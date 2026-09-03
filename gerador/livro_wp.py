"""
O livro, pelo WeasyPrint: uma passagem, e nada de manhas.

E o mesmo livro factorizado de 'livro_factorizado.py' — o Ordinario, o
Saltério, os Hinos e o Comum impressos uma vez, e os dias a remeter — mas
sem as tres passagens, sem a folha de carimbo e sem as marcas invisiveis
em cada peca. O WeasyPrint faz o cabecalho corrido, o folio e as
remissoes sozinho.

uso:
    python gerador/livro_wp.py --ano 2026
    python gerador/livro_wp.py --ano 2026 --de 12-24 --ate 12-26
"""

import argparse
import html as _html
import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
import factorizar
import livro
import livro_factorizado as LF
import pdf as _pdf
from ordo import datas_do_ano

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ


# A frase latina que nomeia a fonte de cada seccao.
ONDE_ESTA = {
    'salterio': ' ut in Psalterio',
    'hinos': ' ut in Hymnis',
    'comum': ' ut in Communi',
}


def id_da_peca(chave):
    """O identificador HTML de uma peca partilhada. Comeca por letra,
    que um id nao pode comecar por algarismo."""
    return f'p{chave}'


# --------------------------------------------------------------------------

def html_das_partilhadas(pecas, reparticao, bilingue):
    o = []
    for seccao, titulo in LF.PARTES:
        escolhidas = LF.ordem_das_pecas(pecas, reparticao, seccao)
        if not escolhidas:
            continue
        o.append('<section class="parte">')
        o.append(f'<h1 class="parte-titulo">{titulo}</h1>')
        for k, p in escolhidas:
            capitular = p['genero'] in compor.COM_CAPITULAR
            lat = compor.para_html(p['texto'], capitular, 'Latin')
            if not lat.strip():
                continue
            marca = f' id="{id_da_peca(k)}"'
            if bilingue:
                ver = compor.para_html(p['vernaculo'], capitular, 'Portugues')
                o.append(f'<div class="duplo peca-partilhada"{marca}>'
                         f'<div class="lat">{lat}</div>'
                         f'<div class="ver">{ver}</div></div>')
            else:
                o.append(f'<div class="par peca-partilhada"{marca}>{lat}</div>')
        o.append('</section>')
    return '\n'.join(o)


def html_do_dia(data, registo, horas, bilingue, reparticao, indice,
                partilhadas_impressas):
    nome, data_latina = livro.cabeca_do_dia(data, registo)
    o = ['<section class="dia">',
         f'<h1 class="dia-titulo">{_html.escape(nome)}</h1>',
         f'<p class="dia-data">{_html.escape(data_latina)}</p>']
    for hora, pecas in horas:
        o.append('<section class="hora">')
        o.append(f'<p class="hora-titulo">{_html.escape(nome)} '
                 f'{livro.NOME_DA_HORA[hora]}</p>')
        for p in pecas:
            t = p.latim or ''
            if not t.strip():
                continue
            k = factorizar.chave(t)
            seccao = reparticao.get(k)

            # O Ordinario nao se aponta: quem reza sabe-o de cor.
            if seccao == 'ordinario':
                continue

            # Sem ancora impressa nao ha para onde remeter: imprime-se a
            # peca por extenso. Vale mais repetir do que mandar o leitor a
            # uma pagina que nao existe.
            if seccao and k in partilhadas_impressas:
                rot = indice.get(k, {}).get('rotulo') or p.rotulo or ''
                onde = ONDE_ESTA.get(seccao, '')
                o.append(f'<a class="remissao" href="#{id_da_peca(k)}">'
                         f'{_html.escape(rot)}{onde}</a>')
                continue

            capitular = p.genero in compor.COM_CAPITULAR
            lat = compor.para_html(t, capitular, 'Latin')
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


def folha(partilhadas, dias, bilingue, corpo, ano):
    edicao = 'bilíngue' if bilingue else 'latina'
    css = (compor.CSS % {'corpo': corpo}) + livro.CSS_DO_LIVRO \
        + LF.CSS_FACTORIZADO + _pdf.CSS_DE_PAGINA
    o = ['<!doctype html><html lang="la"><head><meta charset="utf-8">',
         f'<title>Breviarium Romanum {ano} — edição {edicao}</title>',
         f'<style>{css}</style></head><body>',
         '<div class="corpo %s">' % ('bilingue' if bilingue else 'latina'),
         partilhadas]
    o.extend(dias)
    o.append('</div></body></html>')
    return '\n'.join(o)


# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--edicao', default='latina',
                   choices=('latina', 'bilingue'))
    p.add_argument('--corpo', default='7')
    p.add_argument('--de')
    p.add_argument('--ate')
    p.add_argument('--tarefas', type=int, default=8)
    p.add_argument('--saida')
    p.add_argument('--so-html', action='store_true')
    a = p.parse_args()

    bilingue = a.edicao == 'bilingue'
    nome = a.saida or f'BREVIARIUM-{a.ano}-{a.edicao}'
    t0 = time.time()

    print('a compor o ano e a repartir as peças...', flush=True)
    pecas, ocorrencias = factorizar.colher(a.ano, bilingue, a.tarefas)
    reparticao = factorizar.repartir(pecas)
    indice = {k: {'rotulo': factorizar.rotulo_curto(pecas[k])}
              for k in reparticao}
    print(f'  {ocorrencias:,} peças, {len(pecas):,} distintas, '
          f'{len(reparticao):,} partilhadas', flush=True)

    partilhadas = html_das_partilhadas(pecas, reparticao, bilingue)
    # Quais delas ficaram MESMO impressas: uma peca que nao imprime nada
    # nao tem ancora, e por isso nao se pode remeter para ela.
    impressas = {k for k in reparticao
                 if f'id="{id_da_peca(k)}"' in partilhadas}
    if len(impressas) < len(reparticao):
        print(f'  {len(reparticao) - len(impressas)} peças partilhadas não '
              f'imprimem nada; sairão por extenso nos dias', flush=True)

    datas = [d for d in datas_do_ano(a.ano)
             if (not a.de or d[:5] >= a.de) and (not a.ate or d[:5] <= a.ate)]
    resultados = [None] * len(datas)
    with ThreadPoolExecutor(max_workers=a.tarefas) as ex:
        for i, r in ex.map(lambda i: (i, livro.um_dia(datas[i], bilingue)),
                           range(len(datas))):
            resultados[i] = r
    dias = [html_do_dia(d, reg, horas, bilingue, reparticao, indice, impressas)
            for d, reg, horas in resultados]

    caminho_html = RAIZ / f'{nome}.html'
    io.open(caminho_html, 'w', encoding='utf-8').write(
        folha(partilhadas, dias, bilingue, a.corpo, a.ano))
    print(f'escrito {caminho_html.name}: '
          f'{caminho_html.stat().st_size / 1e6:.1f} MB, '
          f'{time.time() - t0:.0f}s', flush=True)
    if a.so_html:
        return

    print('a compor o PDF (WeasyPrint)...', flush=True)
    caminho_pdf = RAIZ / f'{nome}.pdf'
    n = _pdf.imprimir(caminho_html, caminho_pdf,
                      aviso=lambda p: print(f'  {p} páginas paginadas, '
                                            f'{time.time() - t0:.0f}s',
                                            flush=True))
    print(f'escrito {caminho_pdf.name}: '
          f'{caminho_pdf.stat().st_size / 1e6:.0f} MB, {n} páginas, '
          f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
