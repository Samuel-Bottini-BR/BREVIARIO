"""
A factorizacao: imprimir uma vez o que se repete.

O PORQUE, MEDIDO
----------------
O ano por expandir tem 26,1 milhoes de caracteres e 13.710 paginas. Mas
73.706 pecas sao so 6.471 distintas: **85% do livro e a mesma coisa
impressa outra vez.**

Nao basta, porem, trocar cada repeticao por um ponteiro: 74.000 ponteiros
a quarenta e cinco caracteres sao 3,3 milhoes de caracteres — mais do que
se poupa em metade dos generos. E por isso que os breviarios impressos
nao remetem peca a peca. Fazem tres coisas diferentes:

    ORDINARIO   o que se diz TODOS os dias — o Incipit, a Conclusao, o
                Pater, o Dominus vobiscum — imprime-se uma vez a cabeca
                do livro, e nos dias NAO SE IMPRIME DE TODO, nem sequer
                um ponteiro. Quem reza sabe-o de cor.
    SALTERIO    os salmos imprimem-se uma vez, pela ordem da semana, e o
                dia diz so 'Psalmus 26, 51' — a antifona, essa, fica no
                dia, porque muda com a festa.
    HINOS       o mesmo: uma vez cada, e o dia remete.

O que sobra no dia e o que e mesmo do dia: as antifonas, o capitulo, a
oracao, e as licoes de Matinas — que sao metade do que resta e nao ha
como encolher, porque sao diferentes todos os dias.

uso:
    python gerador/factorizar.py --ano 2026            # so medir
    python gerador/factorizar.py --ano 2026 --guardar  # escrever o indice
"""

import argparse
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
import livro
from ordo import datas_do_ano

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ

# Quantas vezes uma peca tem de aparecer para ir ao Ordinario. O que se
# diz todos os dias em todas as horas aparece 2.920 vezes; o que se diz
# todos os dias numa hora so, 365. Abaixo de duzentas, ja nao e 'de todos
# os dias' e fica no dia.
VEZES_PARA_ORDINARIO = 200

# Os generos que vao para cada secao.
DO_SALTERIO = ('salmo', 'cantico')
DOS_HINOS = ('hino',)
DO_ORDINARIO = ('texto', 'rubrica')

# A ANTIFONA NAO SE REMETE. E ela que diz de que dia e o oficio — troca-la
# por 'Ant., 1234' tirava ao dia a sua cara, e sao so 1,2 milhoes de
# caracteres em vinte e seis. Um breviario impresso remete o salmo e
# imprime a antifona; aqui faz-se o mesmo.
FICAM_NO_DIA = ('antifona', 'licao')


def chave(texto):
    return hashlib.md5(texto.encode('utf-8')).hexdigest()[:16]


def colher(ano, bilingue=False, tarefas=8):
    """Todas as pecas do ano, agrupadas pelo seu texto."""
    pecas = {}            # chave -> {texto, vernaculo, genero, rotulo, vezes}
    ocorrencias = 0
    with ThreadPoolExecutor(max_workers=tarefas) as ex:
        for data, registo, horas in ex.map(
                lambda d: livro.um_dia(d, bilingue), datas_do_ano(ano)):
            for hora, lista in horas:
                for p in lista:
                    t = p.latim or ''
                    if not t.strip():
                        continue
                    ocorrencias += 1
                    k = chave(t)
                    if k in pecas:
                        pecas[k]['vezes'] += 1
                    else:
                        pecas[k] = {'texto': t, 'vernaculo': p.vernaculo or '',
                                    'genero': p.genero, 'rotulo': p.rotulo,
                                    'titulo': p.titulo_lat, 'vezes': 1,
                                    'hora': hora}
    return pecas, ocorrencias


def repartir(pecas):
    """Que peca vai para que secao. Devolve {chave: secao}.

    Tudo o que se repete sai do dia; o que nao se repete fica nele. As
    licoes de Matinas repetem-se 1,0 vezes — sao 1,93 milhoes de
    caracteres que nao ha como encolher, e serao dois quintos do livro.
    """
    fora = {}
    for k, p in pecas.items():
        g, vezes = p['genero'], p['vezes']
        if vezes < 2 or g in FICAM_NO_DIA:
            continue
        # Uma peca sem letras — o '_' que separa estrofes — nao imprime
        # nada, e por isso nao ha para onde remeter. Fica onde esta.
        if not re.search(r'[^\W\d_]', p['texto']):
            continue
        if g in DO_ORDINARIO and vezes >= VEZES_PARA_ORDINARIO:
            fora[k] = 'ordinario'
        elif g in DO_SALTERIO:
            fora[k] = 'salterio'
        elif g in DOS_HINOS:
            fora[k] = 'hinos'
        else:
            # Antifonas, oracoes, capitulos, versiculos: repetem-se de
            # seis a oito vezes cada, e e do Comum que vem a maior parte.
            fora[k] = 'comum'
    return fora


TITULO_NO_TEXTO = re.compile(r'^!(.+)$', re.M)


def rotulo_curto(p):
    """Como a remissao nomeia a peca: 'Psalmus 68(2-13)', 'Hymnus'.

    O nome sai do TEXTO da peca, nao do rotulo interno: o rotulo diz so
    'Salmo 68', e tres pedacos do salmo 68 sairiam com o mesmo nome. A
    primeira linha do texto traz 'Psalmus 68(2-13)', que os distingue.
    """
    achado = TITULO_NO_TEXTO.search(p['texto'])
    if achado and p['genero'] in ('salmo', 'cantico'):
        return achado.group(1).strip()
    if p['genero'] == 'hino':
        return 'Hymnus'
    if p['genero'] == 'oracao':
        return 'Oratio'
    return (p['titulo'] or p['rotulo'] or p['genero']).strip()


def medir(pecas, ocorrencias, reparticao):
    """Quanto pesa o livro, antes e depois. Sem estimar nada que se possa
    contar."""
    REMISSAO = 26          # 'Psalmus 26, 51' com folga
    antes = sum(p['texto'].__len__() * p['vezes'] for p in pecas.values())
    depois = 0
    por_secao = defaultdict(lambda: [0, 0])     # secao -> [caracteres, pecas]
    for k, p in pecas.items():
        n, vezes = len(p['texto']), p['vezes']
        secao = reparticao.get(k)
        if secao == 'ordinario':
            depois += n                      # uma vez, e o dia nao o diz
            por_secao['ordinario'][0] += n
            por_secao['ordinario'][1] += 1
        elif secao:
            depois += n + vezes * REMISSAO   # uma vez, e o dia remete
            por_secao[secao][0] += n
            por_secao[secao][1] += 1
        else:
            depois += n * vezes              # fica no dia, tal e qual
            por_secao['dias'][0] += n * vezes
            por_secao['dias'][1] += 1
    return antes, depois, por_secao


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--guardar', action='store_true')
    a = p.parse_args()

    print(f'a compor o ano de {a.ano}...', flush=True)
    pecas, ocorrencias = colher(a.ano)
    reparticao = repartir(pecas)
    antes, depois, por_secao = medir(pecas, ocorrencias, reparticao)

    print(f'\npeças no ano: {ocorrencias:,}   distintas: {len(pecas):,}')
    print(f'caracteres antes: {antes:,}')
    print(f'caracteres depois: {depois:,}  ({100 * depois / antes:.1f}%)')
    print()
    print(f'{"secção":12} {"peças":>8} {"caracteres":>12}')
    for nome in ('ordinario', 'salterio', 'hinos', 'comum', 'dias'):
        ch, n = por_secao[nome]
        print(f'{nome:12} {n:8,} {ch:12,}')

    # A densidade vem do livro ja impresso, nao de um palpite: 13.710
    # paginas para 26.086.810 caracteres.
    densidade = 26086810 / 13710
    print(f'\ndensidade medida: {densidade:.0f} caracteres por página')
    print(f'páginas previstas: {round(depois / densidade):,}')

    if a.guardar:
        indice = {k: {'secao': s, 'rotulo': rotulo_curto(pecas[k]),
                      'genero': pecas[k]['genero'],
                      'vezes': pecas[k]['vezes']}
                  for k, s in reparticao.items()}
        caminho = RAIZ / f'indice-{a.ano}.json'
        io.open(caminho, 'w', encoding='utf-8').write(
            json.dumps(indice, ensure_ascii=False))
        print(f'\nescrito {caminho.name}: {len(indice):,} peças partilhadas')


if __name__ == '__main__':
    main()
