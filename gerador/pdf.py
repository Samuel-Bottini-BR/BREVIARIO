"""
O motor de PDF: WeasyPrint.

E a ferramenta que o prompt manda desde o inicio, e a razao e esta: sabe
as caixas de margem do '@page'. Faz sozinho, e numa passagem so, as tres
coisas que um livro precisa e que so se sabem depois de paginar:

    o cabecalho corrido   '@top-center { content: string(cabeca) }'
    o numero de folio     '@bottom-center { content: counter(page) }'
    as remissoes          'content: target-counter(attr(href), page)'

O navegador nao sabe nenhuma delas. Enquanto o WeasyPrint nao correu,
fez-se a manha do carimbo — compor o livro, ler o PDF para saber em que
pagina caiu cada coisa, compor uma folha so com cabecalhos e folios, e
sobrepo-las. Funcionava, mas eram tres passagens e uma marca invisivel em
cada peca. Nada disso e preciso aqui.

A BIBLIOTECA NATIVA
-------------------
No Windows o WeasyPrint precisa do GTK (Pango, Cairo, GObject), que nao
vem com o Python. Esta instalado numa pasta propria — nao no sistema — e
o caminho passa-se pela variavel 'WEASYPRINT_DLL_DIRECTORIES'. Desfaz-se
apagando a pasta.
"""

import os
import sys
from pathlib import Path

# Onde o GTK pode estar. Procura-se em vez de se escrever o caminho: quem
# retomar isto noutra maquina nao tem de mexer no codigo.
LUGARES_DO_GTK = (
    Path(os.environ.get('LOCALAPPDATA', '')) / 'gtk3-runtime' / 'bin',
    Path(r'C:\Program Files\GTK3-Runtime Win64\bin'),
    Path(r'C:\msys64\mingw64\bin'),
)


def preparar():
    """Diz ao WeasyPrint onde estao as bibliotecas nativas."""
    if os.environ.get('WEASYPRINT_DLL_DIRECTORIES'):
        return os.environ['WEASYPRINT_DLL_DIRECTORIES']
    for lugar in LUGARES_DO_GTK:
        if (lugar / 'libgobject-2.0-0.dll').exists():
            os.environ['WEASYPRINT_DLL_DIRECTORIES'] = str(lugar)
            return str(lugar)
    raise SystemExit(
        'nao encontro o GTK. O WeasyPrint precisa dele no Windows.\n'
        'Instalar de:\n'
        '  https://github.com/tschoonj/'
        'GTK-for-Windows-Runtime-Environment-Installer/releases')


def imprimir(caminho_html, caminho_pdf, aviso=None):
    """Compoe o HTML em PDF. Devolve o numero de paginas."""
    preparar()
    from weasyprint import HTML
    documento = HTML(filename=str(Path(caminho_html).resolve())).render()
    if aviso:
        aviso(len(documento.pages))
    documento.write_pdf(str(caminho_pdf))
    return len(documento.pages)


# --------------------------------------------------------------------------
# O CSS que so o WeasyPrint entende
# --------------------------------------------------------------------------

CSS_DE_PAGINA = """
/* As caixas de margem: o cabecalho corrido em cima, o folio em baixo.
   A pagina par leva o cabecalho a esquerda e o folio ao canto de fora,
   como nos livros. */
@page {
  @top-center {
    content: string(cabeca);
    font-family: "EB Garamond","Garamond",Georgia,serif;
    font-size: calc(var(--corpo) * 0.86);
    font-variant: small-caps;
    letter-spacing: .05em;
    color: #17130f;
    vertical-align: bottom;
    padding-bottom: 1.2mm;
    border-bottom: .3pt solid #17130f;
    width: 100%;
  }
}

/* O folio vai ao canto de FORA, em cima, ao lado do cabecalho — e onde
   esta no bilingue de 1962, e e onde o polegar o procura ao folhear.

   AS QUATRO CAIXAS VAO SEPARADAS, uma regra por cada. Agrupa-las —
   '@page :left, @page :right { @top-left, @top-right {...} }' — parecia
   o mesmo e nao era: o WeasyPrint nao aplica o grupo, a regra caia
   inteira, e o folio saia com o tamanho por omissao. Medido: 16pt contra
   9,3pt de corpo, quase o dobro da letra do texto.

   O tamanho vai em PONTOS e nao em var(--corpo): a caixa de margem
   pertence a pagina, nao ao corpo do documento, e nem sempre le as
   variaveis que ali se declaram. */
@page :left {
  @top-left {
    content: counter(page);
    font-family: "EB Garamond","Garamond",Georgia,serif;
    font-size: 8pt;
    color: #17130f;
    vertical-align: bottom;
    padding-bottom: 1.2mm;
    font-variant-numeric: tabular-nums;
  }
}
@page :right {
  @top-right {
    content: counter(page);
    font-family: "EB Garamond","Garamond",Georgia,serif;
    font-size: 8pt;
    color: #17130f;
    vertical-align: bottom;
    padding-bottom: 1.2mm;
    font-variant-numeric: tabular-nums;
  }
}

/* A barra de hora dita o cabecalho das paginas que se seguem. E a
   'string-set': o valor fica guardado e a caixa de margem usa-o ate
   outra barra o mudar. */
.hora-titulo { string-set: cabeca content(); }
.parte-titulo { string-set: cabeca content(); }

/* A remissao. O numero de folio nao se escreve: pede-se a pagina onde a
   ancora esta, e o WeasyPrint resolve-o. */
a.remissao {
  display: block;
  text-indent: 0;
  text-decoration: none;
  color: inherit;
  font-variant: small-caps;
  letter-spacing: .03em;
}
/* O numero da remissao escreve-se NO TEXTO, na composicao, e nao aqui.
   Havia um 'a.remissao::after' com target-counter que lhe acrescentava um
   SEGUNDO numero — 'ut in Psalterio [*23] [7]' — e ainda por cima
   errado: o target-counter conta dentro da parte composta, e cada parte
   e um documento seu, de modo que dava a pagina dentro da parte e nao o
   folio do volume. Quem sabe o folio e o compositor, que o grava no
   indice; aqui nao se adivinha. */
"""
