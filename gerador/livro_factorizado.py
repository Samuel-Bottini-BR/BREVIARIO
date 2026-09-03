"""
O livro factorizado: o que se repete impresso uma vez, e os dias a remeter.

A FORMA DO LIVRO
----------------
    Ordinarium     o que se diz todos os dias. Impresso a cabeca, e os
                   dias nao o repetem nem o apontam.
    Psalterium     os salmos e os canticos, uma vez cada.
    Hymni          os hinos, uma vez cada.
    Commune        as antifonas, os capitulos, os versiculos e as oracoes
                   que servem mais do que um dia.
    Proprium       os 365 dias, com o que e mesmo deles — e com uma linha
                   de remissao no lugar do resto.

DUAS PASSAGENS, E PORQUE BASTAM
-------------------------------
A remissao precisa do numero de folio, que so se sabe depois de paginar.
Compoe-se por isso duas vezes: na primeira o folio sai como '000', le-se
do PDF em que pagina caiu cada peca partilhada, e na segunda escrevem-se
os numeros.

Uma segunda passagem chegaria e sobraria se as seccoes partilhadas
mudassem de sitio — mas nao mudam: estao TODAS antes dos dias, e nenhuma
delas tem remissoes dentro. Trocar '000' por '1234' num dia pode empurrar
esse dia, nunca o Saltério.

uso:
    python gerador/livro_factorizado.py --ano 2026
    python gerador/livro_factorizado.py --ano 2026 --de 12-24 --ate 12-26
"""

import argparse
import html as _html
import io
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
import factorizar
import livro
import paginar
from ordo import datas_do_ano

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ

PARTES = (('ordinario', 'Ordinarium'), ('salterio', 'Psalterium'),
          ('hinos', 'Hymni'), ('comum', 'Commune'))

# A ancora invisivel de uma peca partilhada, e o lugar onde o folio entra.
MARCA_DE_ANCORA = re.compile(r'§A([0-9a-f]+)§')
FOLIO_POR_SABER = '000'


def ancora(chave):
    return f'§A{chave}§'


CSS_FACTORIZADO = """
/* A remissao: uma linha so, em versalete, com o folio a seguir. */
.remissao {
  text-indent: 0;
  font-variant: small-caps;
  letter-spacing: .03em;
  color: var(--tinta);
}
.remissao .folio { color: var(--vermelho); font-variant-numeric: tabular-nums; }
.parte { break-before: page; }
.parte-titulo {
  column-span: all;
  text-align: center;
  font-size: calc(var(--corpo) * 1.8);
  font-variant: small-caps;
  letter-spacing: .08em;
  color: var(--vermelho);
  font-weight: normal;
  margin: 0 0 3mm;
  break-after: avoid;
}
.peca-partilhada { break-inside: avoid; margin-bottom: .8mm; }
"""


# --------------------------------------------------------------------------
# As seccoes partilhadas
# --------------------------------------------------------------------------

def ordem_das_pecas(pecas, reparticao, seccao):
    """As pecas de uma seccao, pela ordem em que aparecem no ano.

    Guardou-se, ao colher, a hora em que cada peca apareceu primeiro; a
    ordem das horas e a do oficio, e dentro dela fica a ordem de encontro.
    """
    ordem_hora = {h: i for i, h in enumerate(livro.HORAS)}
    escolhidas = [(k, p) for k, p in pecas.items()
                  if reparticao.get(k) == seccao]
    escolhidas.sort(key=lambda x: (ordem_hora.get(x[1]['hora'], 99),
                                   x[1]['genero'], -x[1]['vezes']))
    return escolhidas


def html_das_partilhadas(pecas, reparticao, bilingue, marcas):
    o = []
    for seccao, titulo in PARTES:
        escolhidas = ordem_das_pecas(pecas, reparticao, seccao)
        if not escolhidas:
            continue
        o.append('<section class="parte">')
        o.append(f'<h1 class="parte-titulo">{titulo}</h1>')
        # A parte leva barra como as horas, para ter cabecalho corrido.
        o.append(f'<p class="hora-titulo">'
                 f'<span class="marca">{livro.marca(len(marcas))}</span>'
                 f'{titulo}</p>')
        marcas.append(titulo)
        for k, p in escolhidas:
            capitular = p['genero'] in compor.COM_CAPITULAR
            lat = compor.para_html(p['texto'], capitular, 'Latin')
            if not lat.strip():
                continue
            # A ancora vai INVISIVEL, como a marca das horas: fica no PDF
            # para quem o le por dentro, e nao aparece na pagina.
            marca = f'<span class="marca">{ancora(k)}</span>'
            if bilingue:
                ver = compor.para_html(p['vernaculo'], capitular, 'Portugues')
                o.append('<div class="duplo peca-partilhada">'
                         f'<div class="lat">{marca}{lat}</div>'
                         f'<div class="ver">{ver}</div></div>')
            else:
                o.append(f'<div class="par peca-partilhada">{marca}{lat}</div>')
        o.append('</section>')
    return '\n'.join(o)


# --------------------------------------------------------------------------
# Os dias
# --------------------------------------------------------------------------

def html_do_dia(data, registo, horas, bilingue, reparticao, indice,
                folios, marcas):
    nome, data_latina = livro.cabeca_do_dia(data, registo)
    o = ['<section class="dia">',
         f'<h1 class="dia-titulo">{_html.escape(nome)}</h1>',
         f'<p class="dia-data">{_html.escape(data_latina)}</p>']
    for hora, pecas in horas:
        o.append('<section class="hora">')
        o.append(f'<p class="hora-titulo">'
                 f'<span class="marca">{livro.marca(len(marcas))}</span>'
                 f'{_html.escape(nome)} {livro.NOME_DA_HORA[hora]}</p>')
        marcas.append(f'{nome} {livro.NOME_DA_HORA[hora]}')
        for p in pecas:
            t = p.latim or ''
            if not t.strip():
                continue
            k = factorizar.chave(t)
            seccao = reparticao.get(k)

            # O Ordinario nao se aponta: quem reza sabe-o de cor.
            if seccao == 'ordinario':
                continue

            # Sem folio nao ha remissao que se leia: imprime-se a peca
            # por extenso. Vale mais repeti-la do que mandar o leitor a
            # uma pagina que nao existe.
            if seccao and (k in folios or not folios):
                folio = folios.get(k, FOLIO_POR_SABER)
                rot = indice.get(k, {}).get('rotulo') or p.rotulo or ''
                o.append('<p class="remissao">'
                         f'{_html.escape(rot)}'
                         f' <span class="folio">{folio}</span></p>')
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
    o = ['<!doctype html><html lang="la"><head><meta charset="utf-8">',
         f'<title>Breviarium Romanum {ano} — edição {edicao}</title>',
         '<style>' + (compor.CSS % {'corpo': corpo}) + livro.CSS_DO_LIVRO
         + CSS_FACTORIZADO + '</style></head><body>',
         '<div class="corpo %s">' % ('bilingue' if bilingue else 'latina'),
         partilhadas]
    o.extend(dias)
    o.append('</div></body></html>')
    return '\n'.join(o)


# --------------------------------------------------------------------------

def folios_das_ancoras(caminho_pdf):
    """Em que folio caiu cada peca partilhada. Le-se do PDF."""
    from pypdf import PdfReader
    leitor = PdfReader(str(caminho_pdf))
    fora = {}
    for n, pagina in enumerate(leitor.pages, start=1):
        for achado in MARCA_DE_ANCORA.finditer(pagina.extract_text() or ''):
            fora.setdefault(achado.group(1), n)
    return fora, len(leitor.pages)


def html_dos_dias(datas, bilingue, reparticao, indice, folios, marcas,
                  tarefas=8):
    resultados = [None] * len(datas)
    with ThreadPoolExecutor(max_workers=tarefas) as ex:
        for i, r in ex.map(lambda i: (i, livro.um_dia(datas[i], bilingue)),
                           range(len(datas))):
            resultados[i] = r
    return [html_do_dia(d, reg, horas, bilingue, reparticao, indice,
                        folios, marcas)
            for d, reg, horas in resultados]


def escrever_e_imprimir(html, nome, minutos):
    caminho_html = RAIZ / f'{nome}.html'
    io.open(caminho_html, 'w', encoding='utf-8').write(html)
    caminho_pdf = RAIZ / f'{nome}.pdf'
    livro.imprimir(caminho_html, caminho_pdf, minutos=minutos)
    return caminho_pdf


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--edicao', default='latina',
                   choices=('latina', 'bilingue'))
    p.add_argument('--corpo', default='7')
    p.add_argument('--tarefas', type=int, default=8)
    p.add_argument('--minutos', type=int, default=30)
    p.add_argument('--saida')
    a = p.parse_args()

    bilingue = a.edicao == 'bilingue'
    base = a.saida or f'breviarium-factorizado-{a.ano}-{a.edicao}'
    t0 = time.time()

    print('a compor o ano e a repartir as peças...', flush=True)
    pecas, ocorrencias = factorizar.colher(a.ano, bilingue, a.tarefas)
    reparticao = factorizar.repartir(pecas)
    indice = {k: {'rotulo': factorizar.rotulo_curto(pecas[k])}
              for k in reparticao}
    print(f'  {ocorrencias:,} peças, {len(pecas):,} distintas, '
          f'{len(reparticao):,} partilhadas', flush=True)

    # --- 1. as seccoes partilhadas, que vao a cabeca do livro
    marcas_part = []
    html = folha(html_das_partilhadas(pecas, reparticao, bilingue,
                                      marcas_part),
                 [], bilingue, a.corpo, a.ano)
    pdf_part = escrever_e_imprimir(html, f'{base}-partilhadas', a.minutos)
    folios, paginas_part = folios_das_ancoras(pdf_part)
    print(f'  partilhadas: {paginas_part} páginas, '
          f'{len(folios):,} de {len(reparticao):,} âncoras', flush=True)
    if len(folios) < len(reparticao):
        print(f'  ATENÇÃO: {len(reparticao) - len(folios)} peças sem fólio; '
              f'as remissões delas sairão como {FOLIO_POR_SABER}')

    # --- 2. os dias, mes a mes, ja com os folios
    #
    # Os folios das partilhadas nao mudam por os dias mudarem: estao TODAS
    # antes deles. Por isso basta uma passagem nos dias.
    partes = [(pdf_part, marcas_part)]
    for mes in range(1, 13):
        datas = [d for d in datas_do_ano(a.ano)
                 if d[:2] == f'{mes:02d}']
        marcas = []
        html = folha('', html_dos_dias(datas, bilingue, reparticao, indice,
                                       folios, marcas, a.tarefas),
                     bilingue, a.corpo, a.ano)
        pdf = escrever_e_imprimir(html, f'{base}-{mes:02d}', a.minutos)
        n = livro.paginas_do_pdf(pdf)
        print(f'  mês {mes:02d}: {n} páginas', flush=True)
        partes.append((pdf, marcas))

    # --- 3. cabecalho, folio e costura
    print('a pôr o cabeçalho e o folio...', flush=True)
    folio = 1
    paginados = []
    for pdf, marcas in partes:
        alvo = Path(pdf).with_name(Path(pdf).stem + '-paginado.pdf')
        total, _, _ = paginar.paginar(pdf, marcas, alvo, folio, a.minutos)
        print(f'  {Path(pdf).stem}: fólios {folio}–{folio + total - 1}',
              flush=True)
        folio += total
        paginados.append(alvo)

    final = RAIZ / f'{base}.pdf'
    n = livro.juntar(paginados, final)
    print(f'\nescrito {final.name}: {final.stat().st_size / 1e6:.0f} MB, '
          f'{n} páginas, {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
