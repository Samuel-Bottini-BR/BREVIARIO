"""
Paginacao: o cabecalho corrido e o numero de folio, em duas passagens.

O PROBLEMA
----------
Um livro precisa de tres coisas que so se sabem DEPOIS de paginado:

    o cabecalho corrido   'Feria secunda ad Primam', em cada pagina
    o numero de folio     em cada pagina
    as remissoes          'Psalmi ut in Psalterio [45]'

O WeasyPrint faz as tres sozinho, pelas caixas de margem do '@page'. O
Chrome nao sabe nenhuma delas, e o WeasyPrint neste computador nao corre
por lhe faltar a biblioteca GTK.

A SAIDA
-------
Fazem-se DUAS passagens, e a segunda le a primeira:

  1. compoe-se o corpo do livro, sem cabecalho nem numero;
  2. le-se o PDF pagina a pagina e ve-se em que pagina caiu cada hora;
  3. compoe-se uma folha de CARIMBO — as mesmas paginas, do mesmo
     tamanho, com o cabecalho e o folio e mais nada;
  4. sobrepoem-se as duas.

O passo 2 e o mesmo que as remissoes precisam: saber em que pagina caiu
cada coisa. Feito isto para o cabecalho, esta feito para elas.

uso:
    python gerador/paginar.py prova-natal.pdf
    python gerador/paginar.py breviarium-2026-latina.pdf --saida livro.pdf
"""

import argparse
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
import livro

RAIZ = compor.RAIZ

# A marca invisivel que 'livro.py' poe em cada barra de hora: '§H12§'.
#
# Nao se procura o TEXTO da barra. O texto extraido de um PDF em versalete
# vem partido e com espacos a mais — 'A D  M ATUTINUM' — e ha rubricas do
# oficio que acabam nas mesmas palavras: 'Reliqua omittuntur, nisi Laudes'
# passava por barra de Laudes. Medido em Janeiro: procurando pelo texto,
# encontravam-se 233 barras onde ha 248.
MARCA_DE_BARRA = re.compile(r'§\s*H\s*(\d+)\s*§')


def barras_por_pagina(caminho_pdf):
    """Em que pagina abre cada hora.

    Devolve (total de paginas, [(indice da barra, pagina)]) — pela marca,
    e por isso sem depender de como o texto saiu.
    """
    from pypdf import PdfReader
    leitor = PdfReader(str(caminho_pdf))
    fora = []
    for n, pagina in enumerate(leitor.pages, start=1):
        for achado in MARCA_DE_BARRA.finditer(pagina.extract_text() or ''):
            fora.append((int(achado.group(1)), n))
    return len(leitor.pages), fora


def cabecalhos(total, aberturas, barras):
    """O cabecalho de cada pagina.

    'aberturas' sao pares (indice da barra, pagina); 'barras' sao os
    textos, pelo indice. A pagina que nao abre hora nenhuma herda o
    cabecalho da anterior; a que abre mais do que uma fica com a ultima,
    que e a que continua para a pagina seguinte.
    """
    por_pagina = {}
    for indice, pagina in sorted(aberturas):
        if indice < len(barras):
            por_pagina[pagina] = barras[indice]
    fora = [''] * (total + 1)
    corrente = ''
    for pagina in range(1, total + 1):
        corrente = por_pagina.get(pagina, corrente)
        fora[pagina] = corrente
    return fora


CSS_CARIMBO = """
@page { size: 100mm 160mm; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "EB Garamond","Garamond",Georgia,serif;
       color: #17130f; }
.pag { position: relative; width: 100mm; height: 160mm;
       break-after: page; }
.pag:last-child { break-after: auto; }
.cab { position: absolute; top: 5.4mm; left: 8mm; right: 8mm;
       text-align: center; font-size: 6.5pt; font-variant: small-caps;
       letter-spacing: .05em;
       /* UMA LINHA, sempre. Um nome comprido — 'S. Gregorii Nazianzeni
          Episcopi Confessoris et Ecclesiae Doctoris ad Matutinum' —
          partia-se em tres linhas e caia por cima do texto. Corta-se com
          reticencias, como fazem os livros. */
       white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fol { position: absolute; bottom: 5mm; left: 8mm; right: 8mm;
       text-align: center; font-size: 6.5pt;
       font-variant-numeric: tabular-nums; }
"""


def folha_de_carimbo(cabecas, primeiro_folio=1):
    import html as _h
    o = ['<!doctype html><html lang="la"><head><meta charset="utf-8">',
         '<style>' + CSS_CARIMBO + '</style></head><body>']
    for n in range(1, len(cabecas)):
        folio = n + primeiro_folio - 1
        o.append('<div class="pag">'
                 f'<div class="cab">{_h.escape(cabecas[n])}</div>'
                 f'<div class="fol">{folio}</div></div>')
    o.append('</body></html>')
    return '\n'.join(o)


def sobrepor(corpo_pdf, carimbo_pdf, saida_pdf):
    """Poe o carimbo por cima do corpo, pagina a pagina.

    A sobreposicao descomprime os dois fluxos e junta-os — e escreve-os
    assim, em claro. Medido: um mes passava de 19,6 MB para 69,8. Volta a
    comprimi-los no fim, e ficam em 7 MB. Custa segundos.
    """
    from pypdf import PdfReader, PdfWriter
    corpo = PdfReader(str(corpo_pdf))
    carimbo = PdfReader(str(carimbo_pdf))
    escritor = PdfWriter()
    for n, pagina in enumerate(corpo.pages):
        if n < len(carimbo.pages):
            pagina.merge_page(carimbo.pages[n])
        escritor.add_page(pagina)
    for pagina in escritor.pages:
        pagina.compress_content_streams()
    with io.open(saida_pdf, 'wb') as f:
        escritor.write(f)
    return len(corpo.pages)


def paginar(corpo_pdf, barras, saida_pdf, primeiro_folio=1, minutos=30):
    total, aberturas = barras_por_pagina(corpo_pdf)
    # Nunca deixar passar em silencio: se as barras encontradas no PDF nao
    # forem tantas como as compostas, os cabecalhos saem trocados a partir
    # do primeiro desencontro.
    if len(aberturas) != len(barras):
        raise SystemExit(
            f'{Path(corpo_pdf).name}: encontrei {len(aberturas)} barras no '
            f'PDF e esperava {len(barras)}. Os cabeçalhos sairiam trocados.')
    cabecas = cabecalhos(total, aberturas, barras)
    carimbo_html = Path(corpo_pdf).with_name(
        Path(corpo_pdf).stem + '-carimbo.html')
    io.open(carimbo_html, 'w', encoding='utf-8').write(
        folha_de_carimbo(cabecas, primeiro_folio))
    carimbo_pdf = carimbo_html.with_suffix('.pdf')
    livro.imprimir(carimbo_html, carimbo_pdf, minutos=minutos)
    n = sobrepor(corpo_pdf, carimbo_pdf, saida_pdf)
    return total, len(aberturas), n


def barras_do_periodo(ano, de, ate, bilingue=False):
    """Os textos das barras, na ordem em que foram compostos.

    Nao se leem do PDF: geram-se outra vez pela mesma via que os compos,
    e por isso saem com a grafia e a acentuacao certas.
    """
    from ordo import datas_do_ano
    datas = [d for d in datas_do_ano(ano)
             if (not de or d[:5] >= de) and (not ate or d[:5] <= ate)]
    fora = []
    for data in datas:
        registo = compor.ordo_do_ano(data).dia(data, 'Laudes')
        nome, _ = livro.cabeca_do_dia(data, registo)
        for hora in livro.HORAS:
            fora.append(f'{nome} {livro.NOME_DA_HORA[hora]}')
    return fora


def paginar_partes(base, ano, saida=None, minutos=30):
    """Pagina as doze partes de um ano e cose-as num volume so.

    O folio corre de parte para parte: Fevereiro comeca onde Janeiro
    acabou. E a folha de carimbo faz-se por mes, que uma de treze mil
    paginas poria o navegador a limite.
    """
    partes, folio = [], 1
    for mes in range(1, 13):
        corpo = RAIZ / f'{base}-{mes:02d}.pdf'
        if not corpo.exists():
            raise SystemExit(f'falta {corpo.name}')
        alvo = corpo.with_name(corpo.stem + '-paginado.pdf')
        barras = barras_do_periodo(ano, f'{mes:02d}-01', f'{mes:02d}-31')
        total, aberturas, _ = paginar(corpo, barras, alvo, folio, minutos)
        print(f'  mês {mes:02d}: {total} páginas, folios '
              f'{folio}–{folio + total - 1}, {aberturas} horas', flush=True)
        partes.append(alvo)
        folio += total
    inteiro = Path(saida) if saida else RAIZ / f'{base}.pdf'
    n = livro.juntar(partes, inteiro)
    print(f'escrito {inteiro.name}: {inteiro.stat().st_size / 1e6:.0f} MB, '
          f'{n} páginas')
    return n


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf')
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--de')
    p.add_argument('--ate')
    p.add_argument('--folio', type=int, default=1)
    p.add_argument('--saida')
    p.add_argument('--partes', action='store_true',
                   help='pagina as doze partes de um ano e cose-as')
    a = p.parse_args()

    if a.partes:
        return paginar_partes(a.pdf, a.ano, a.saida)

    corpo = RAIZ / a.pdf if not Path(a.pdf).is_absolute() else Path(a.pdf)
    saida = Path(a.saida) if a.saida else corpo.with_name(
        corpo.stem + '-paginado.pdf')
    barras = barras_do_periodo(a.ano, a.de, a.ate)
    total, aberturas, n = paginar(corpo, barras, saida, a.folio)
    print(f'{corpo.name}: {total} páginas, {aberturas} horas encontradas')
    print(f'escrito {saida.name}: {n} páginas com cabeçalho e folio')


if __name__ == '__main__':
    main()
