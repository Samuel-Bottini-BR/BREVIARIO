"""
Confronta a matriz contra o que o gerador do Divinum Officium faz de facto,
em todos os dias do ano.

A matriz diz, para cada tipo de oficio e cada peca, de que seccao do
Breviario a peca vem. O gerador rotula cada bloco com essa mesma
informacao. Este programa poe os dois lado a lado e lista onde discordam.

Nao "corrige" a matriz sozinho: so aponta. A decisao e do Padre.

uso: python comparar.py colheita-2026.tsv
"""

import csv
import io
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import matriz_normas as M
from colher import tipo_de_oficio

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Do rotulo do gerador para as fontes da matriz
# --------------------------------------------------------------------------

# Nucleo do rotulo -> fonte, no vocabulario da matriz
NUCLEO = {
    '': 'Ord',
    'ex Proprio Sanctorum': 'PS',
    'ex Commune aut Festo': 'CS',
    'ex Proprio de Tempore': 'PdT',
    'ex Psalterio secundum diem': 'Ps.dia',
    'ex Psalterio secundum tempora': 'Ps.tempo',
    'Psalmi et Antiphona de Dominica': 'Ps.dom',
    'Per Annum': 'Ord+Ps',
    'anticipatur': '(antecipado)',
    'habentur': '(especial)',
    'specialis': '(especial)',
}

# Que rotulos do gerador sao aceitaveis para cada celula da matriz.
# 'Pr>Com' quer dizer "o Proprio; onde ele nao der, o Comum" — por isso
# aceita tanto PS como CS: sao os dois lados da mesma regra.
#
# Duas notas que custaram discordancias falsas ate serem percebidas:
#
# 1. PRATELEIRA. Varias pecas que a lei chama "do Ordinario" — porque sao
#    invariaveis — estao guardadas dentro do Salterio no Divinum Officium,
#    e por isso vem rotuladas 'ex Psalterio...'. Mesmo texto, estante
#    diferente. Por isso 'Ord' aceita tambem os rotulos de Salterio.
#
# 2. O SALTERIO DO DIA, AO DOMINGO, E O DO DOMINGO. Quando o dia da semana
#    e domingo, 'secundum diem' e 'de Dominica' dizem a mesma coisa. Ver
#    resolver_dia_da_semana() mais abaixo.
#
ACEITA = {
    'Ord':     {'Ord', 'Ord+Ps', 'Ps.dia', 'Ps.tempo'},
    'Ord+Ps':  {'Ord', 'Ord+Ps', 'Ps.dia', 'Ps.tempo', 'Ps.dom'},
    # 'o Proprio' e o dos Santos numa festa de santo, e o do TEMPO numa
    # festa do Senhor (oitava da Pascoa, Ascensao, Corpus Christi...).
    # Por isso PdT tambem satisfaz esta celula.
    'Pr>Com':  {'PS', 'CS', 'PdT'},
    'PdT':     {'PdT'},
    'Ps.dia':  {'Ps.dia', 'Ps.tempo'},
    'Ps.tempo': {'Ps.tempo', 'Ps.dia'},
    'Ps.dom':  {'Ps.dom', 'Ps.dia', 'Ps.tempo'},
    'Ps.dom, 1o esquema': {'Ps.dom'},
    'Ps.dom, 2o esquema': {'Ps.dom'},
    'Ps.dia, 1o esquema': {'Ps.dia', 'Ps.tempo'},
    'Ps.dia, 2o esquema': {'Ps.dia', 'Ps.tempo'},
    'Ps.dom (53, 118.1, 118.2)': {'Ps.dom'},
    'L1': {'PS', 'CS', 'PdT', 'Ps.dom'},
    'L2 / L3 / L5': {'PS', 'CS', 'PdT', 'Ps.dom'},
}

PREFIXOS = [
    (re.compile(r'^Laudes:(\d)\s+'), 'esquema'),
    (re.compile(r'^Psalmi Dominica & antiphonæ\s+'), 'salmos_domingo'),
    (re.compile(r'^Psalmi & antiphonæ\s+'), 'salmos_e_antifonas'),
    (re.compile(r'^Antiphonæ et Psalmi\s+'), 'salmos_e_antifonas'),
    # 'Antiphona' (singular) e 'Antiphonæ' (plural). Escrever 'Antiphonæ?'
    # nao apanha o singular, porque o 'æ' e um caractere so.
    (re.compile(r'^Antiphon(?:a|æ)\s+'), 'so_antifona'),
]


def decompor(rotulo):
    """Devolve (nucleo, modificador, esquema).

    O gerador combina informacoes num rotulo so, por exemplo
    'Laudes:2 Psalmi & antiphonæ ex Proprio de Tempore'. Aqui separam-se.
    """
    r = ' '.join((rotulo or '').split())
    esquema = modificador = None
    mudou = True
    while mudou:
        mudou = False
        for rx, nome in PREFIXOS:
            m = rx.match(r)
            if m:
                if nome == 'esquema':
                    esquema = m.group(1)
                else:
                    modificador = nome
                r = r[m.end():]
                mudou = True
                break
    return NUCLEO.get(r, f'?{r}'), modificador, esquema


# --------------------------------------------------------------------------
# Do bloco do gerador para a linha da matriz
# --------------------------------------------------------------------------

# (hora do gerador, titulo do bloco) -> (hora da matriz, nome da peca)
BLOCOS = {
    ('Matutinum', 'Invitatorium'): ('Matinas', 'Invitatorio'),
    ('Matutinum', 'Hymnus'): ('Matinas', 'Hino'),
    ('Matutinum', 'Psalmi cum lectionibus'):
        ('Matinas', 'Antifonas e salmos do nocturno'),
    ('Matutinum', 'Lectio 1'): ('Matinas', 'Licoes 1 e 2, com responsorios'),
    ('Matutinum', 'Lectio 2'): ('Matinas', 'Licoes 1 e 2, com responsorios'),
    ('Matutinum', 'Lectio 3'): ('Matinas', 'Licao 3'),
    ('Matutinum', 'Oratio'): ('Matinas', None),   # a matriz nao tem a
                                                  # conclusao de Matinas
    ('Prima', 'Hymnus'): ('Prima', 'O resto de Prima'),
    ('Prima', 'Oratio'): ('Prima', 'O resto de Prima'),
    ('Prima', 'Incipit'): ('Prima', 'O resto de Prima'),
    ('Prima', 'Conclusio'): ('Prima', 'O resto de Prima'),

    ('Completorium', 'Hymnus'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),
    ('Completorium', 'Canticum: Nunc dimittis'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),
    ('Completorium', 'Oratio'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),
    ('Completorium', 'Lectio brevis'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),
    ('Completorium', 'Incipit'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),
    ('Completorium', 'Conclusio'):
        ('Completas', 'Hino, responsorio breve, Nunc dimittis, oracao, conclusao'),

    ('Laudes', 'Psalmi'): ('Laudes', 'Antifonas'),
    ('Laudes', 'Capitulum Hymnus Versus'): ('Laudes', 'Capitulo, hino e versiculo'),
    ('Laudes', 'Canticum: Benedictus'): ('Laudes', 'Antifona do Benedictus'),
    ('Laudes', 'Oratio'): ('Laudes', 'Oracao'),

    ('Prima', 'Psalmi'): ('Prima', 'Antifona'),
    ('Prima', 'Capitulum Responsorium Versus'): ('Prima', 'Capitulo'),
    ('Prima', 'Lectio brevis'): ('Prima', 'Licao breve'),

    ('Vespera', 'Psalmi'): ('Vesperas', 'Antifonas'),
    ('Vespera', 'Capitulum Hymnus Versus'): ('Vesperas', 'Capitulo, hino e versiculo'),
    ('Vespera', 'Canticum: Magnificat'): ('Vesperas', 'Antifona do Magnificat'),
    ('Vespera', 'Oratio'): ('Vesperas', 'Oracao'),

    ('Completorium', 'Psalmi'): ('Completas', 'Antifona e salmos'),
    ('Completorium', 'Capitulum Responsorium Versus'): ('Completas', 'Capitulo'),
    ('Completorium', 'Antiphona finalis B.M.V.'):
        ('Completas', 'Antifona final de N. Senhora'),
}
for h in ('Tertia', 'Sexta', 'Nona'):
    BLOCOS[(h, 'Psalmi')] = ('Terca, Sexta e Noa', 'Antifona')
    BLOCOS[(h, 'Capitulum Responsorium Versus')] = \
        ('Terca, Sexta e Noa', 'Capitulo e responsorio breve')
    BLOCOS[(h, 'Oratio')] = ('Terca, Sexta e Noa', 'Oracao')


# Blocos em que a ausencia de rotulo quer dizer "o gerador nao informa",
# e nao "vem do Ordinario". As licoes de Matinas sao o caso: o gerador
# imprime <b>Lectio 1</b> sem qualquer <em>{...}</em>. Tratar isso como
# Ordinario produzia cerca de mil discordancias falsas.
SEM_ROTULO_E_DESCONHECIDO = {
    ('Matutinum', 'Lectio 1'), ('Matutinum', 'Lectio 2'),
    ('Matutinum', 'Lectio 3'), ('Matutinum', 'Lectio 4'),
    ('Matutinum', 'Lectio 5'), ('Matutinum', 'Lectio 6'),
    ('Matutinum', 'Lectio 7'), ('Matutinum', 'Lectio 8'),
    ('Matutinum', 'Lectio 9'),
}


def indexar_matriz():
    idx = {}
    for hora, tab in M.HORAS:
        for r in tab:
            idx[(hora, r['peca'])] = r
    return idx


def valores_esperados(celula):
    """A celula pode ser um valor ou depender do tempo. Devolve o conjunto
    de rotulos aceitaveis, juntando o padrao e todas as excecoes — porque
    aqui ainda nao sabemos em que tempo do ano estamos."""
    if isinstance(celula, M.Conforme):
        vals = [celula.padrao] + [v for _, v in celula.excecoes]
    else:
        vals = [celula]
    aceitos = set()
    for v in vals:
        aceitos |= ACEITA.get(v, {v})
    return aceitos, vals


def main():
    caminho = RAIZ / (sys.argv[1] if len(sys.argv) > 1 else 'colheita-2026.tsv')
    linhas = [x for x in csv.DictReader(io.open(caminho, encoding='utf-8'),
                                        delimiter='\t')
              if int(x['ordem']) % 2 == 0]      # so o lado latino

    idx = indexar_matriz()

    conferidos = 0
    discordancias = defaultdict(list)
    sem_regra = Counter()
    nucleos_novos = Counter()
    nao_informado = Counter()

    for x in linhas:
        # Reclassifica a partir do cabecalho guardado, em vez de confiar na
        # coluna 'tipo' da colheita: assim uma correccao no classificador
        # vale imediatamente, sem ter de recolher o ano outra vez.
        tipo = tipo_de_oficio(x['dia'])
        if tipo not in M.CLASSES:
            continue
        chave = BLOCOS.get((x['hora'], x['bloco']))
        if not chave or chave[1] is None:
            sem_regra[(x['hora'], x['bloco'])] += 1
            continue
        linha = idx.get(chave)
        if linha is None:
            sem_regra[chave] += 1
            continue

        if (not x['origem'].strip()
                and (x['hora'], x['bloco']) in SEM_ROTULO_E_DESCONHECIDO):
            nao_informado[(x['hora'], x['bloco'])] += 1
            continue

        nucleo, modif, esquema = decompor(x['origem'])
        if nucleo.startswith('?'):
            nucleos_novos[nucleo] += 1
            continue
        if nucleo.startswith('('):        # antecipado, especial
            continue

        aceitos, esperado = valores_esperados(linha[tipo])
        conferidos += 1
        if nucleo not in aceitos:
            discordancias[(chave[0], chave[1], tipo)].append(
                (x['data'], x['dia'], nucleo, ' ou '.join(map(str, esperado))))

    print(f'blocos conferidos: {conferidos}')
    print(f'celulas da matriz com discordancia: {len(discordancias)}')
    print()

    if discordancias:
        print('=' * 78)
        print('  ONDE A MATRIZ DISCORDA DO GERADOR')
        print('=' * 78)
        for (hora, peca, tipo), casos in sorted(
                discordancias.items(), key=lambda kv: -len(kv[1])):
            obs = Counter(c[2] for c in casos)
            print(f'\n{hora} — {peca} — coluna {tipo}   ({len(casos)} dias)')
            print(f'   a matriz diz : {casos[0][3]}')
            print(f'   o gerador dá : ' +
                  ', '.join(f'{k} ({v} dias)' for k, v in obs.most_common()))
            for d, dia, nuc, _ in casos[:3]:
                print(f'      {d}  {dia[:58]}  ->  {nuc}')
            if len(casos) > 3:
                print(f'      ... e mais {len(casos) - 3} dias')

    if sem_regra:
        print()
        print('=' * 78)
        print('  BLOCOS QUE A MATRIZ NÃO COBRE')
        print('=' * 78)
        for k, v in sem_regra.most_common(20):
            print(f'  {v:5d}  {k}')

    if nao_informado:
        print()
        print('  BLOCOS EM QUE O GERADOR NÃO INFORMA A ORIGEM:')
        for k, v in nao_informado.most_common(10):
            print(f'  {v:5d}  {k}')

    if nucleos_novos:
        print()
        print('  RÓTULOS QUE NÃO SOUBE LER:')
        for k, v in nucleos_novos.most_common(10):
            print(f'  {v:5d}  {k}')


if __name__ == '__main__':
    main()
