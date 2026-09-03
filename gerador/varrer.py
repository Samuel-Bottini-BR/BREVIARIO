"""
A varredura: gera o ano inteiro e confere cada dia contra o gerador oficial.

E o marco do projeto — os 365 dias a sair, o texto conferido, e nenhum
ponteiro de remissao a sobreviver. Junta as verificacoes 1, 2, 3, 6 e 7 do
prompt numa passagem so:

  1. nenhum ponteiro sobrevive   ('@', '!', '&', '$', 'vide')
  2. nenhum dado de controle escapa   (';;', seccoes de controle)
  3. completude — todos os dias geram
  6. cobertura — os 365 dias
  7. comparacao com o gerador oficial, linha a linha

uso:
    python varrer.py --hora Completorium
    python varrer.py --hora Completorium --ano 2026 --tarefas 6
    python varrer.py --hora Completorium --limite 30
"""

import argparse
import csv
import io
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import html as _html
import comparar_texto as C
import compor
import compor_maiores
import compor_menores
import compor_prima
import compor_matinas
from ordo import datas_do_ano

RAIZ = Path(__file__).resolve().parent.parent

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# O que nunca pode chegar a uma pagina impressa. Sao as verificacoes 1 e 2
# do prompt, e a razao de existirem esta na seccao 14: ja saiu impresso
# ';;Semiduplex;;6.9' numa pagina bem diagramada, e ninguem reparou.
PONTEIRO = re.compile(r'(?m)^\s*[@!&$]\w|;;|\bis missing\b|^\s*vide\s'
                      r'|/:|:/|\{:')


def auditar(pecas):
    """Os ponteiros que sobreviveram ATE A PAGINA.

    Nao se audita o texto intermedio: la ainda ha '!Psalmus 4' e
    '/:4:2:/', que sao marcas de composicao — a primeira vira titulo de
    salmo, a segunda vira numero de versiculo a vermelho. O que conta e o
    que chega ao papel, e por isso audita-se a pagina ja composta.
    """
    fora = []
    for p in pecas:
        for lado, bruto in (('LA', p.latim), ('PT', p.vernaculo)):
            if not bruto:
                continue
            corpo = compor.para_html(bruto, False,
                                     'Latin' if lado == 'LA' else 'Portugues')
            texto = _html.unescape(re.sub(r'<[^>]+>', '', corpo))
            for l in texto.split('\n'):
                if PONTEIRO.search(l):
                    fora.append(f'{lado} {l.strip()[:110]}')
    return fora


def um_dia(data, hora):
    try:
        deles = C.normalizar(C.texto_do_gerador(data, hora))
    except Exception as e:
        return {'data': data, 'estado': 'FALHA-GERADOR', 'detalhe': repr(e)[:200]}

    try:
        if hora == 'Matutinum':
            pecas, _, _ = compor_matinas.montar(data, com_vernaculo=True)
        elif hora == 'Completorium':
            pecas, _ = compor.montar(None, com_vernaculo=True, data=data)
        elif hora in compor_maiores.HORAS:
            pecas, _, _ = compor_maiores.montar(hora, data, com_vernaculo=True)
        elif hora == 'Prima':
            pecas, _, _ = compor_prima.montar(data, com_vernaculo=True)
        elif hora in compor_menores.HORAS:
            pecas, _, _ = compor_menores.montar(hora, data,
                                                com_vernaculo=True)
        else:
            raise NotImplementedError(f'a hora {hora} ainda nao se compoe')
    except Exception as e:
        return {'data': data, 'estado': 'FALHA-NOSSA',
                'detalhe': f'{e!r} {traceback.format_exc()[-300:]}'}

    nossas = []
    for p in pecas:
        nossas.extend((p.latim or '').split('\n'))
    nosso = C.normalizar(nossas)
    so_deles = [l for l in deles if l not in nosso]
    so_nosso = [l for l in nosso if l not in deles]
    ponteiros = auditar(pecas)

    return {
        'data': data,
        'estado': ('OK' if not so_deles and not so_nosso and not ponteiros
                   else 'DIVERGE'),
        'linhas_deles': len(deles),
        'linhas_nossas': len(nosso),
        'so_deles': len(so_deles),
        'so_nosso': len(so_nosso),
        'ponteiros': len(ponteiros),
        'detalhe': ' | '.join(([f'-{l[:70]}' for l in so_deles[:2]]
                               + [f'+{l[:70]}' for l in so_nosso[:2]]
                               + [f'PONTEIRO {l[:70]}' for l in ponteiros[:2]])),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--hora', default='Completorium')
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--tarefas', type=int, default=6)
    p.add_argument('--limite', type=int)
    p.add_argument('--saida')
    a = p.parse_args()

    datas = list(datas_do_ano(a.ano))
    if a.limite:
        datas = datas[:a.limite]
    saida = Path(a.saida) if a.saida else RAIZ / f'varredura-{a.hora}-{a.ano}.tsv'

    print(f'{a.hora}, {len(datas)} dias')
    resultados = []
    feitos = 0
    with ThreadPoolExecutor(max_workers=a.tarefas) as ex:
        for r in ex.map(lambda d: um_dia(d, a.hora), datas):
            resultados.append(r)
            feitos += 1
            if feitos % 25 == 0:
                maus = sum(1 for x in resultados if x['estado'] != 'OK')
                print(f'  {feitos}/{len(datas)}  ({maus} por bater)', flush=True)

    campos = ['data', 'estado', 'linhas_deles', 'linhas_nossas', 'so_deles',
              'so_nosso', 'ponteiros', 'detalhe']
    with io.open(saida, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter='\t',
                           extrasaction='ignore')
        w.writeheader()
        w.writerows(resultados)

    ok = [r for r in resultados if r['estado'] == 'OK']
    diverge = [r for r in resultados if r['estado'] == 'DIVERGE']
    falhas = [r for r in resultados if r['estado'].startswith('FALHA')]
    com_ponteiro = [r for r in resultados if r.get('ponteiros')]

    print()
    print('=' * 62)
    print(f'  {a.hora} — {a.ano}')
    print('=' * 62)
    print(f'  dias iguais ao gerador oficial : {len(ok)} / {len(datas)}')
    print(f'  dias com divergencia           : {len(diverge)}')
    print(f'  dias que nao geraram           : {len(falhas)}')
    print(f'  dias com ponteiro sobrevivente : {len(com_ponteiro)}')
    print(f'  escrito {saida.name}')

    for r in (falhas + diverge)[:12]:
        print(f'\n  {r["data"]}  {r["estado"]}')
        print(f'     {r.get("detalhe", "")[:300]}')

    return 0 if not diverge and not falhas else 1


if __name__ == '__main__':
    sys.exit(main())
