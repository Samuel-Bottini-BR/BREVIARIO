"""
Compara o TEXTO que nos produzimos com o texto do gerador do Divinum
Officium, para o mesmo dia e a mesma hora.

E a verificacao 7 do prompt — 'comparacao com o site' — feita contra o
gerador em lote do proprio repositorio, que corre aqui e da o mesmo
resultado sem fazer pedidos ao servidor deles.

O nosso lado NAO e montado aqui: vem do compositor da pagina, o mesmo que
produz o PDF. Se fosse montado aqui outra vez, a comparacao mediria a
distancia entre duas coisas nossas, e nao entre o nosso livro e o deles.

uso:
    python comparar_texto.py                         # Completas, Feria II
    python comparar_texto.py --hora Sexta            # a Sexta ja composta
    python comparar_texto.py --dia 08-17-2026 --semana "Feria II"
"""

import html
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from colher import caminho_msys, PERL5LIB
import compor
import compor_maiores
import compor_menores
import compor_prima
import compor_sexta

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'
GERADOR = REPO / 'standalone/tools/epubgen2/EofficiumXhtml.pl'


# --------------------------------------------------------------------------
# O lado deles
# --------------------------------------------------------------------------

def texto_do_gerador(data, hora):
    q = (f'date1={data}&command=pray{hora}'
         f'&version=Rubrics%201960%20%2D%201960&testmode=regular'
         f'&lang1=Latin&lang2=Latin&votive=&linkmissa=&nofancychars=1')
    r = subprocess.run(
        ['perl', caminho_msys(GERADOR), q],
        capture_output=True, cwd=str(GERADOR.parent),
        env={**os.environ, 'PERL5LIB': PERL5LIB},
    )
    bruto = r.stdout.decode('utf-8', 'replace')

    # Pedido com uma lingua so, o gerador emite uma coluna unica, em
    # celulas com identificador '<Hora>1', '<Hora>2'... Fora delas fica so
    # o menu de navegacao, que nao e oficio.
    celulas = re.findall(
        rf"<TD[^>]*ID='{hora}\d+'[^>]*>(.*?)</TD>", bruto, re.S)
    if not celulas:
        celulas = re.findall(r"<TD[^>]*WIDTH='50%'[^>]*>(.*?)</TD>",
                             bruto, re.S)[::2]
    corpo = '\n'.join(celulas)

    corpo = re.sub(r'<br\s*/?>', '\n', corpo, flags=re.I)
    corpo = re.sub(r'</p>', '\n', corpo, flags=re.I)
    corpo = re.sub(r'<[^>]+>', '', corpo)
    return [l for l in (html.unescape(corpo)).split('\n') if l.strip()]


# --------------------------------------------------------------------------
# O nosso lado — o compositor da pagina, tal e qual
# --------------------------------------------------------------------------

def nosso_texto(hora, dia_semana, proprio=None, data=None):
    if hora == 'Completorium':
        pecas, _ = compor.montar(dia_semana, com_vernaculo=False,
                                 proprio=proprio, data=data)
    elif hora in compor_maiores.HORAS:
        pecas, _, _ = compor_maiores.montar(hora, data, com_vernaculo=False)
    elif hora == 'Prima':
        pecas, _, _ = compor_prima.montar(data, com_vernaculo=False)
    elif hora in compor_menores.HORAS:
        pecas, _, _ = compor_menores.montar(hora, data, com_vernaculo=False)
    else:
        pecas, _ = compor_sexta.montar(com_vernaculo=False)
    fora = []
    for p in pecas:
        fora.extend((p.latim or '').split('\n'))
    return [l for l in fora if l.strip()]


# --------------------------------------------------------------------------

# Os titulos dos blocos. O nosso compositor guarda-os a parte da peca —
# saem em vermelho, a abrir o bloco — e por isso nao entram nesta
# comparacao, que e de texto.
TITULOS = {'Incipit', 'Lectio brevis', 'Hymnus', 'Psalmi',
           'Capitulum Responsorium Versus', 'Canticum: Nunc dimittis',
           'Oratio', 'Conclusio', 'Antiphona finalis B.M.V.', 'Te Deum',
           'Versus (In loco Capituli)', 'Capitulum', 'Responsorium',
           'De Officio Capituli', 'Martyrologium', 'Martyrológio',
           'Litaniæ', 'Litania', 'Ladainhas'}


def normalizar(linhas):
    # O til no fim da linha junta-a com a seguinte — e o que o compositor
    # faz ao montar a pagina; aqui faz-se o mesmo, para comparar linhas
    # com linhas.
    juntas, pendente = [], ''
    for l in linhas:
        if pendente:
            l = pendente + ' ' + re.sub(r'^\s*[vr]\.\s*', '', l)
        pendente = ''
        if l.rstrip().endswith('~'):
            pendente = l.rstrip()[:-1]
            continue
        juntas.append(l)
    if pendente:
        juntas.append(pendente)
    linhas = juntas
    return _normalizar(linhas)


def _normalizar(linhas):
    """Tira o que e so apresentacao, para comparar palavras com palavras.

    O gerador aplica, depois de resolver, uma camada de apresentacao:
      - troca 'j' por 'i' quando a versao e de 1960 (grafia classica)
      - troca '+' pelos sinais de cruz
      - poe as barras dos versiculos no lugar de 'V.' e 'R.'
      - imprime o titulo de cada bloco
    Aqui essas diferencas sao anuladas: sao decisoes de tipografia, e a
    pagina impressa toma-as por conta propria.
    """
    fora = []
    for l in linhas:
        l = re.sub(r'\{:[^}]*:\}', '', l)            # marcas de canto
        l = re.sub(r'/:(.*?):/', r'\1', l)           # rubricas entre /: :/
        # O numero de versiculo e o contador de salmos da hora sao
        # apresentacao: um sai em vermelho pequeno, o outro nao entra em
        # livro impresso. Fora dos dois lados, para comparar palavras.
        l = re.sub(r'^\s*\d+:\d+[a-z]?\s*', '', l)
        # O contador de salmos da hora sai no fim do titulo — 'Psalmus 62
        # [3]', 'Canticum Quicumque [4]'. E ajuda de ecra, e nao entra em
        # livro impresso (decisao 3.15).
        l = re.sub(r'\s*\[\d+\]\s*$', '', l)
        l = l.replace('℣', 'V').replace('℟', 'R')
        l = re.sub(r'^\s*([VR])\.\s*', r'\1. ', l)
        l = re.sub(r'^\s*[vr]\.\s*', '', l)          # marcas de coluna
        l = l.replace('✙︎', '+').replace('✠', '+').replace('✙', '+')
        # Os seletores de variacao (U+FE0E/U+FE0F) dizem ao tipo se o
        # sinal sai como texto ou como emoji. Sao invisiveis, e o gerador
        # poe-nos a volta da cruz.
        l = l.replace('︎', '').replace('️', '')
        l = re.sub(r'\++', '+', l)
        # A grafia de 1960 — porta de spell_var. E aplicada aos dois lados
        # porque no nosso ela so entra na hora de compor a pagina.
        l = l.replace('J', 'I').replace('j', 'i')
        l = l.replace('er eúmdem', 'er eúndem')
        l = re.sub(r'^!', '', l)                     # marca de referencia
        # A vogal muda de um hino vem entre parenteses rectos —
        # 'Ill[e] amor'. E marca de canto: a vogal elide-se, e o original
        # imprime-a em italico. A letra esta la nos dois lados; so o
        # parentese e apresentacao.
        l = re.sub(r'\[([æaeiou]m?)\]', r'\1', l)
        # A flexa NAO se normaliza: os dois lados imprimem-na (decisao
        # 2.17), e por isso um '†' fora do sitio tem de aparecer aqui como
        # divergencia. E o que garante que a pontuacao de canto esta certa.
        #
        # As aspas. O gerador foi chamado com 'nofancychars=1', que lhe
        # tira as aspas angulares; a pagina impressa quere-las.
        l = l.replace('«', '').replace('»', '')
        l = l.replace('_', ' ')
        # A marca de estrofe do hino: o original poe inicial na letra
        # seguinte, nos imprimimos a inicial. Nenhum dos dois imprime o
        # asterisco.
        l = re.sub(r'^\*\s+', '', l)
        l = re.sub(r'\s+', ' ', l).strip(' ')
        # O rotulo de procedencia — '{ex Psalterio secundum diem}',
        # '{Psalmi et Antiphona de Dominica}' — e uma ajuda de ecra do
        # site: sai em italico a seguir ao titulo do bloco, para quem
        # navega saber de onde veio a peca. Nao e texto do oficio, e
        # nenhum breviario impresso o traz. Ficaria de fora na composicao
        # mesmo que o portassemos, e portar exigia toda a maquina do
        # 'setbuild' — sem proveito nenhum para o livro.
        if re.match(r'^[^{}]*\{[^}]*\}\s*$', l):
            continue
        if l and l not in TITULOS:
            fora.append(l)
    return fora


def main():
    hora = 'Completorium'
    if '--hora' in sys.argv:
        hora = sys.argv[sys.argv.index('--hora') + 1]

    dia_semana = 'Feria II'
    data = '08-17-2026'
    if hora != 'Completorium':
        dia_semana = compor_sexta.DIA['dia_da_semana']
        data = compor_sexta.DIA['data_us']
    if '--dia' in sys.argv:
        data = sys.argv[sys.argv.index('--dia') + 1]
    if '--semana' in sys.argv:
        dia_semana = sys.argv[sys.argv.index('--semana') + 1]
    # O oficio que vence nesse dia, enquanto o calendario nao existir.
    proprio = None
    if '--proprio' in sys.argv:
        proprio = sys.argv[sys.argv.index('--proprio') + 1]

    deles = normalizar(texto_do_gerador(data, hora))
    # A data manda: e por ela que o Ordo diz qual o oficio do dia. O
    # '--proprio' so serve para forcar um dia que o Ordo nao tenha.
    nosso = normalizar(nosso_texto(hora, dia_semana, proprio, data))

    print(f'{hora}, {data} ({dia_semana})')
    print(f'gerador oficial : {len(deles)} linhas')
    print(f'nosso           : {len(nosso)} linhas')
    print()

    so_deles = [l for l in deles if l not in nosso]
    so_nosso = [l for l in nosso if l not in deles]

    print(f'linhas que so o gerador tem : {len(so_deles)}')
    for l in so_deles[:15]:
        print(f'   - {l[:100]}')
    print()
    print(f'linhas que so nos temos     : {len(so_nosso)}')
    for l in so_nosso[:15]:
        print(f'   + {l[:100]}')
    return 1 if so_deles or so_nosso else 0


if __name__ == '__main__':
    sys.exit(main())
