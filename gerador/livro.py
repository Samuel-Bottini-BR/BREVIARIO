"""
O livro: todas as horas de todos os dias, num so PDF.

Monta a folha inteira — dia a dia, e dentro de cada dia as oito horas pela
ordem em que se rezam — e manda-a imprimir.

    python gerador/livro.py --ano 2026 --edicao latina
    python gerador/livro.py --ano 2026 --edicao bilingue --de 12-24 --ate 12-26
    python gerador/livro.py --ano 2026 --so-html          (nao imprime)

A FERRAMENTA DE PDF
-------------------
O prompt manda WeasyPrint, e e ele que da o que um livro precisa:
cabecalho corrido em cada pagina, numero de pagina, e as caixas de margem
do '@page'. Neste computador o WeasyPrint esta instalado mas faltam-lhe as
bibliotecas nativas (GTK/Pango), e por isso a prova sai pelo Chrome, que
compoe o mesmo CSS mas nao sabe cabecalho corrido nem numero de pagina.
E prova, nao e o livro. Ver a nota em decisoes.md.
"""

import argparse
import html as _html
import io
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
import compor_maiores
import compor_matinas
import compor_menores
import compor_prima
import imprimir as _imprimir
from ordo import datas_do_ano

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ

# A ordem em que as horas se rezam, que e a ordem em que vao no livro.
HORAS = ('Matutinum', 'Laudes', 'Prima', 'Tertia', 'Sexta', 'Nona',
         'Vespera', 'Completorium')

NOME_DA_HORA = {
    'Matutinum': 'ad Matutinum', 'Laudes': 'ad Laudes',
    'Prima': 'ad Primam', 'Tertia': 'ad Tertiam', 'Sexta': 'ad Sextam',
    'Nona': 'ad Nonam', 'Vespera': 'ad Vesperas',
    'Completorium': 'ad Completorium',
}

MES_EM_LATIM = ('Ianuarii', 'Februarii', 'Martii', 'Aprilis', 'Maii',
                'Iunii', 'Iulii', 'Augusti', 'Septembris', 'Octobris',
                'Novembris', 'Decembris')


def montar_hora(data, hora, bilingue):
    if hora == 'Matutinum':
        return compor_matinas.montar(data, com_vernaculo=bilingue)[0]
    if hora == 'Completorium':
        return compor.montar(None, com_vernaculo=bilingue, data=data)[0]
    if hora in compor_maiores.HORAS:
        return compor_maiores.montar(hora, data, com_vernaculo=bilingue)[0]
    if hora == 'Prima':
        return compor_prima.montar(data, com_vernaculo=bilingue)[0]
    return compor_menores.montar(hora, data, com_vernaculo=bilingue)[0]


def um_dia(data, bilingue):
    """(data, nome do dia, [(hora, pecas)]) — a materia de um dia."""
    ordo = compor.ordo_do_ano(data)
    registo = ordo.dia(data, 'Laudes')
    horas = []
    for hora in HORAS:
        try:
            horas.append((hora, montar_hora(data, hora, bilingue)))
        except Exception as erro:            # nunca calar um dia inteiro
            horas.append((hora, [compor.Peca(
                'texto', '', f'/:falhou: {erro!r}:/', '')]))
    return data, registo, horas


# --------------------------------------------------------------------------
# A folha
# --------------------------------------------------------------------------

CSS_DO_LIVRO = """
/* O livro nao leva o cabecalho fixo da pagina solta: em vez dele, cada
   hora abre com a sua barra. Recupera-se o espaco que ficava reservado
   para ele. */
.corpo { padding-top: 0; }

/* A marca que a paginacao le. Fica no PDF para quem o le por dentro, e
   nao aparece a quem le a pagina. */
.marca { font-size: 1px; color: transparent; letter-spacing: 0; }

/* A abertura de cada dia. Comeca em pagina nova: e o que faz o livro
   abrir-se no dia certo. */
.dia { break-before: page; }
.dia-titulo {
  column-span: all;
  text-align: center;
  font-size: var(--titulo-festa);
  font-variant: small-caps;
  letter-spacing: .04em;
  color: var(--vermelho);
  margin: 0 0 1.2mm;
  font-weight: normal;
  line-height: 1.15;
  break-after: avoid;
}
.dia-data {
  column-span: all;
  text-align: center;
  font-size: var(--rubrica);
  color: var(--tinta);
  letter-spacing: .06em;
  font-variant: small-caps;
  margin: 0 0 1.8mm;
  break-after: avoid;
}
/* A barra de hora faz as vezes do cabecalho corrido enquanto a prova sai
   pelo Chrome, que nao sabe repetir cabecalho por pagina. */
.hora-titulo {
  column-span: all;
  text-align: center;
  font-size: var(--cabecalho);
  font-variant: small-caps;
  letter-spacing: .08em;
  border-top: .4pt solid currentColor;
  border-bottom: .4pt solid currentColor;
  padding: .5mm 0;
  margin: 2.4mm 0 1.2mm;
  break-after: avoid;
  break-inside: avoid;
}
.hora:first-of-type .hora-titulo { margin-top: .6mm; }
"""


def cabeca_do_dia(data, registo):
    mes, dia_do_mes, ano = (int(x) for x in data.split('-'))
    dia_da_semana = compor.dia_da_semana(data)
    nome = (registo.nome if registo and registo.nome else
            compor.DIA_EM_LATIM[dia_da_semana])
    return nome, (f'{compor.DIA_EM_LATIM[dia_da_semana]} · '
                  f'{dia_do_mes} {MES_EM_LATIM[mes - 1]}')


MARCA = '§H'


def marca(indice):
    """A marca invisivel de uma barra de hora: '§H0§', '§H1§'..."""
    return f'{MARCA}{indice}§'


def html_do_dia(data, registo, horas, bilingue, marcas=None):
    marcas = marcas if marcas is not None else []
    nome, data_latina = cabeca_do_dia(data, registo)
    o = ['<section class="dia">',
         f'<h1 class="dia-titulo">{_html.escape(nome)}</h1>',
         f'<p class="dia-data">{_html.escape(data_latina)}</p>']
    for hora, pecas in horas:
        o.append('<section class="hora">')
        # A marca invisivel. O texto extraido de um PDF em versalete vem
        # partido e com espacos a mais, e por isso nao serve para achar a
        # barra; uma marca posta por nos serve sempre, e diz ALEM DISSO
        # qual barra e. A mesma manha servira as remissoes.
        o.append(f'<p class="hora-titulo">'
                 f'<span class="marca">{marca(len(marcas))}</span>'
                 f'{_html.escape(nome)} {NOME_DA_HORA[hora]}</p>')
        marcas.append(f'{nome} {NOME_DA_HORA[hora]}')
        for p in pecas:
            capitular = p.genero in compor.COM_CAPITULAR
            lat = compor.para_html(p.latim, capitular, 'Latin')
            if not lat.strip():
                continue
            tl = (f'<p class="bloco">{_html.escape(p.titulo_lat)}</p>'
                  if p.titulo_lat else '')
            if bilingue:
                tv = (f'<p class="bloco">{_html.escape(p.titulo_ver)}</p>'
                      if p.titulo_ver else '')
                ver = compor.para_html(p.vernaculo, capitular, 'Portugues')
                o.append('<div class="duplo">'
                         f'<div class="lat">{tl}{lat}</div>'
                         f'<div class="ver">{tv}{ver}</div></div>')
            else:
                o.append(f'<div class="par">{tl}{lat}</div>')
        o.append('</section>')
    o.append('</section>')
    return '\n'.join(o)


def folha(dias, bilingue, corpo, ano):
    edicao = 'bilíngue' if bilingue else 'latina'
    o = ['<!doctype html><html lang="la"><head><meta charset="utf-8">',
         f'<title>Breviarium Romanum {ano} — edição {edicao}</title>',
         '<style>' + (compor.CSS % {'corpo': corpo}) + CSS_DO_LIVRO
         + '</style></head><body>',
         '<div class="corpo %s">' % ('bilingue' if bilingue else 'latina')]
    o.extend(dias)
    o.append('</div></body></html>')
    return '\n'.join(o)


# --------------------------------------------------------------------------
# A impressao
# --------------------------------------------------------------------------

_NAVEGADOR = []
_RISCADOS = set()


def navegador_que_imprime():
    """Qual dos navegadores instalados imprime mesmo.

    O Chrome, quando o utilizador ja o tem aberto, entrega o pedido a
    janela dele — 'Abrindo em uma sessao de navegador existente' — e sai
    sem escrever nada, mesmo com um '--user-data-dir' so nosso. O Edge,
    que e o mesmo motor, nao faz isso se nao estiver aberto.

    Por isso nao se escolhe pelo nome: prova-se. Uma pagina minima, e
    fica o primeiro que a imprimir.
    """
    if _NAVEGADOR:
        return _NAVEGADOR[0]
    pasta = Path(os.environ.get('TEMP', '.'))
    fonte = pasta / 'prova-de-navegador.html'
    io.open(fonte, 'w', encoding='utf-8').write(
        '<!doctype html><meta charset="utf-8"><body>prova</body>')
    for candidato in _imprimir.CHROME:
        if not candidato.exists() or candidato in _RISCADOS:
            continue
        alvo = pasta / f'prova-{candidato.stem}.pdf'
        if alvo.exists():
            alvo.unlink()
        try:
            subprocess.run(
                [str(candidato), '--headless', '--disable-gpu',
                 '--no-first-run', '--no-default-browser-check',
                 f'--user-data-dir={pasta / ("perfil-" + candidato.stem)}',
                 f'--print-to-pdf={alvo}', fonte.resolve().as_uri()],
                capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            continue
        for _ in range(20):
            if alvo.exists() and alvo.stat().st_size > 500:
                _NAVEGADOR.append(candidato)
                return candidato
            time.sleep(0.5)
    raise SystemExit('nenhum navegador instalado imprimiu a página de prova')


def imprimir(caminho_html, caminho_pdf, minutos=30):
    """Manda o navegador compor a folha em PDF."""
    caminho_pdf = Path(caminho_pdf)
    if caminho_pdf.exists():
        caminho_pdf.unlink()
    navegador = navegador_que_imprime()
    perfil = Path(os.environ.get('TEMP', '.')) / f'perfil-{navegador.stem}'
    r = subprocess.run(
        [str(navegador), '--headless', '--disable-gpu',
         '--no-first-run', '--no-default-browser-check',
         f'--user-data-dir={perfil}',
         '--no-pdf-header-footer', '--no-margins',
         f'--print-to-pdf={caminho_pdf}',
         Path(caminho_html).resolve().as_uri()],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=minutos * 60)
    # ATENCAO: o processo que se lanca e so o arranque — sai logo, e quem
    # compoe fica a trabalhar por tras. Nao basta esperar que ele termine:
    # espera-se que o PDF apareca E deixe de crescer.
    limite = time.time() + minutos * 60
    tamanho, parado = -1, 0
    while time.time() < limite:
        actual = caminho_pdf.stat().st_size if caminho_pdf.exists() else -1
        if actual > 1000 and actual == tamanho:
            parado += 1
            if parado >= 3:                 # tres leituras seguidas iguais
                return r
        else:
            parado = 0
        tamanho = actual
        time.sleep(1)
    # O navegador que servia deixou de servir — o utilizador abriu a
    # janela dele, e o pedido passou a ser entregue la em vez de imprimir.
    # Risca-se este e tenta-se o seguinte.
    if navegador in _NAVEGADOR:
        _NAVEGADOR.remove(navegador)
    _RISCADOS.add(navegador)
    if any(c.exists() and c not in _RISCADOS for c in _imprimir.CHROME):
        return imprimir(caminho_html, caminho_pdf, minutos)
    raise SystemExit(f'nenhum navegador produziu PDF em {minutos} min:\n'
                     f'{r.stderr[-2000:]}')


CONTA_PAGINAS = re.compile(rb'/Type\s*/Page(?![s/\w])')


def paginas_do_pdf(caminho):
    """Quantas paginas tem o PDF — lido do proprio ficheiro, sem
    biblioteca nenhuma.

    Cuidado com o '/Type /Pages', que e o NO da arvore de paginas e nao
    uma pagina: dai o travao a seguir ao 'Page'.
    """
    return len(CONTA_PAGINAS.findall(Path(caminho).read_bytes()))


# --------------------------------------------------------------------------

def juntar(partes, caminho_pdf):
    """Cose as partes num volume so.

    O 'pypdf' faz isto sem tocar no conteudo: as paginas passam tal e
    qual de um ficheiro para o outro.
    """
    from pypdf import PdfWriter
    escritor = PdfWriter()
    for parte in partes:
        escritor.append(str(parte))
    with io.open(caminho_pdf, 'wb') as f:
        escritor.write(f)
    return paginas_do_pdf(caminho_pdf)


def por_mes(a):
    """Um ficheiro por mes.

    Um ano inteiro por expandir sao milhares de paginas, e um so ficheiro
    de HTML dessa dimensao poe o navegador a limite. Partido por mes, cada
    parte compoe-se em segundos e ve-se logo.
    """
    base = a.saida or f'breviarium-{a.ano}-{a.edicao}'
    total_paginas, partes = 0, []
    for mes in range(1, 13):
        argumentos = argparse.Namespace(**vars(a))
        argumentos.por_mes = False
        argumentos.de = f'{mes:02d}-01'
        argumentos.ate = f'{mes:02d}-31'
        argumentos.saida = f'{base}-{mes:02d}'
        print(f'\n===== mes {mes:02d} =====')
        total_paginas += (uma_parte(argumentos) or 0)
        partes.append(RAIZ / f'{base}-{mes:02d}.pdf')
    print(f'\nTOTAL DO ANO: {total_paginas} páginas')

    if (not a.so_html and not getattr(a, 'sem_coser', False)
            and all(p.exists() for p in partes)):
        inteiro = RAIZ / f'{base}.pdf'
        print('a coser as doze partes num volume só...', flush=True)
        n = juntar(partes, inteiro)
        print(f'escrito {inteiro.name}: '
              f'{inteiro.stat().st_size / 1e6:.0f} MB, {n} páginas')
    return total_paginas


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--edicao', default='latina',
                   choices=('latina', 'bilingue'))
    p.add_argument('--corpo', default='7')
    p.add_argument('--de', help='MM-DD')
    p.add_argument('--ate', help='MM-DD')
    p.add_argument('--tarefas', type=int, default=8)
    p.add_argument('--saida')
    p.add_argument('--so-html', action='store_true')
    p.add_argument('--por-mes', action='store_true',
                   help='um ficheiro por mes, em vez de um so')
    p.add_argument('--minutos', type=int, default=60,
                   help='quanto tempo dar ao navegador')
    p.add_argument('--sem-coser', action='store_true',
                   help='deixa as partes soltas, para as paginar antes')
    a = p.parse_args()

    if a.por_mes:
        return por_mes(a)
    return uma_parte(a)


def uma_parte(a):
    """Compoe um troco do ano — um mes, uma semana, o ano inteiro."""
    bilingue = a.edicao == 'bilingue'
    datas = list(datas_do_ano(a.ano))
    if a.de:
        datas = [d for d in datas if d[:5] >= a.de]
    if a.ate:
        datas = [d for d in datas if d[:5] <= a.ate]

    print(f'{len(datas)} dias x {len(HORAS)} horas, edição {a.edicao}, '
          f'corpo {a.corpo}pt')
    t0 = time.time()
    resultados = [None] * len(datas)
    feitos = [0]

    def trabalho(i):
        r = um_dia(datas[i], bilingue)
        feitos[0] += 1
        if feitos[0] % 25 == 0:
            print(f'  {feitos[0]}/{len(datas)} dias', flush=True)
        return i, r

    with ThreadPoolExecutor(max_workers=a.tarefas) as ex:
        for i, r in ex.map(trabalho, range(len(datas))):
            resultados[i] = r

    marcas = []
    corpo_html = [html_do_dia(d, reg, horas, bilingue, marcas)
                  for d, reg, horas in resultados]
    nome = a.saida or f'breviarium-{a.ano}-{a.edicao}'
    caminho_html = RAIZ / f'{nome}.html'
    io.open(caminho_html, 'w', encoding='utf-8').write(
        folha(corpo_html, bilingue, a.corpo, a.ano))
    print(f'escrito {caminho_html.name}: '
          f'{caminho_html.stat().st_size / 1e6:.1f} MB, '
          f'{time.time() - t0:.0f}s')

    if a.so_html:
        return 0
    caminho_pdf = RAIZ / f'{nome}.pdf'
    print('a compor o PDF...', flush=True)
    imprimir(caminho_html, caminho_pdf, minutos=getattr(a, 'minutos', 60))
    paginas = paginas_do_pdf(caminho_pdf)
    print(f'escrito {caminho_pdf.name}: '
          f'{caminho_pdf.stat().st_size / 1e6:.1f} MB, '
          f'{paginas} páginas, '
          f'{time.time() - t0:.0f}s no total')
    return paginas


if __name__ == '__main__':
    main()
