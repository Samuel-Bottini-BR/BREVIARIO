"""
Colhe do gerador local, para cada dia e hora, a ORIGEM de cada peca.

O Divinum Officium rotula cada bloco do oficio com a seccao de onde ele
veio — {ex Proprio Sanctorum}, {ex Psalterio secundum diem}, e assim por
diante. E esse rotulo que responde a pergunta que a matriz tenta responder,
e por isso serve de gabarito.

Nao usa o site: usa o gerador em lote do proprio repositorio, que roda aqui.
Assim da para varrer os 365 dias sem fazer milhares de pedidos ao servidor.

uso:
    python colher.py --ano 1961                 # o ano inteiro
    python colher.py --datas 11-10-1961,08-15-1961
"""

import argparse
import csv
import os
import html
import io
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'
GERADOR = REPO / 'standalone/tools/epubgen2/EofficiumXhtml.pl'


def caminho_msys(p):
    """C:\\Users\\x -> /c/Users/x

    O Perl que vem com o Git e um Perl de msys: nao abre caminho com letra
    de unidade, e usa ':' para separar caminhos, como no Unix.
    """
    p = str(p).replace('\\', '/')
    if len(p) > 1 and p[1] == ':':
        p = '/' + p[0].lower() + p[2:]
    return p


PERL5LIB = ':'.join([
    caminho_msys(RAIZ / 'perl5/lib/perl5'),
    caminho_msys(REPO / 'web/cgi-bin'),
])

HORAS = ['Matutinum', 'Laudes', 'Prima', 'Tertia', 'Sexta', 'Nona',
         'Vespera', 'Completorium']

VERSAO = 'Rubrics%201960%20%2D%201960'

# O titulo do bloco vem em <b>...</b>; o rotulo de origem vem logo a
# seguir, dentro de <em>, entre chaves. Exemplo real:
#     <b>Psalmi</b> <em>{ex Psalterio secundum diem}</em>
# O rotulo pode faltar — e entao a peca e do Ordinario.
BLOCO = re.compile(
    r'<b>([^<]{2,60})</b>'          # titulo
    r'(?:\s*<em>\s*\{([^}]*)\}\s*</em>)?'   # rotulo, se houver
)


def gerar(data_mm_dd_yyyy, hora):
    q = (f'date1={data_mm_dd_yyyy}&command=pray{hora}&version={VERSAO}'
         f'&testmode=regular&lang1=Latin&lang2=Portugues'
         f'&votive=&linkmissa=&nofancychars=1')
    r = subprocess.run(
        ['perl', caminho_msys(GERADOR), q],
        capture_output=True, cwd=str(GERADOR.parent),
        env={**os.environ, 'PERL5LIB': PERL5LIB},
    )
    return (r.stdout.decode('utf-8', 'replace'), r.returncode,
            r.stderr.decode('utf-8', 'replace')[:300])


def extrair(texto):
    """Devolve [(titulo, rotulo)] na ordem em que aparecem, so do lado latino.

    O gerador escreve as duas linguas lado a lado. O lado latino vem
    primeiro em cada bloco, e e o que tem os rotulos em latim.
    """
    saida = []
    for m in BLOCO.finditer(texto):
        titulo = html.unescape(m.group(1)).strip()
        rotulo = html.unescape(m.group(2) or '').strip()
        # Descarta capitulares soltas e restos de uma letra
        if len(titulo) < 2 or titulo.isdigit():
            continue
        saida.append((titulo, rotulo))
    return saida


def cabecalho_do_dia(texto):
    """O nome do dia e a sua classe, do topo da pagina.

    Nas festas o gerador marca o cabecalho com class="rd" (vermelho); nas
    ferias, com class="" — por isso nao serve procurar so pelo vermelho.
    """
    m = re.search(r'<p class="cen">\s*<span class="[^"]*">(.*?)</span>',
                  texto, re.S)
    if not m:
        return ''
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1))).split())


def tipo_de_oficio(cabecalho):
    """Qual das cinco colunas da matriz este dia usa.

    Nao e a classe do dia: uma feria de Quaresma e de III classe e mesmo
    assim reza o Oficio FERIAL. Quem manda e a natureza do dia
    (normas 165, 167-170).
    """
    nome = cabecalho.split('~')[0].strip()
    m = re.search(r'~\s*(?:Dies Octavæ\s*)?([IV]+)\.\s*classis', cabecalho)
    classe = m.group(1) if m else ''

    if re.match(r'Dominica\b', nome, re.I):
        return 'DOM'

    # O oficio de N. Senhora ao sabado reza o oficio ORDINARIO, nao o
    # ferial — norma 169. O cabecalho e "Sanctæ Mariæ Sabbato", sem "in":
    # a primeira versao desta funcao exigia o "in" e deixava 504 linhas
    # por classificar.
    if re.search(r'S(anct)?[æ.]?\s*Mari[æa]\s+(in\s+)?Sabbato', nome, re.I):
        return 'III'

    if re.match(r'(Feria|Sabbato|In Vigilia|Vigilia)\b', nome, re.I):
        return 'FER'

    # Os dias de IV classe sao ferias por definicao, mesmo quando o nome
    # nao comeca por "Feria" — por exemplo "Die Secunda Januarii", que
    # sao as ferias do tempo do Natal.
    if classe == 'IV':
        return 'FER'

    return classe if classe in ('I', 'II', 'III') else '?'


def datas_do_ano(ano):
    d, fim = date(ano, 1, 1), date(ano, 12, 31)
    while d <= fim:
        yield f'{d.month:02d}-{d.day:02d}-{d.year}'
        d += timedelta(days=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ano', type=int)
    p.add_argument('--datas')
    p.add_argument('--saida', default='colheita.tsv')
    p.add_argument('--tarefas', type=int, default=6)
    a = p.parse_args()

    if a.datas:
        datas = [d.strip() for d in a.datas.split(',')]
    elif a.ano:
        datas = list(datas_do_ano(a.ano))
    else:
        p.error('indique --ano ou --datas')

    trabalhos = [(d, h) for d in datas for h in HORAS]
    print(f'{len(datas)} dias x {len(HORAS)} horas = {len(trabalhos)} gerações')

    linhas, falhas = [], []

    def uma(t):
        d, h = t
        texto, rc, erro = gerar(d, h)
        if rc != 0 or not texto:
            return ('FALHA', d, h, rc, erro)
        cab = cabecalho_do_dia(texto)
        return ('OK', d, h, cab, tipo_de_oficio(cab), extrair(texto))

    feitos = 0
    with ThreadPoolExecutor(max_workers=a.tarefas) as ex:
        for r in ex.map(uma, trabalhos):
            feitos += 1
            if feitos % 200 == 0:
                print(f'  {feitos}/{len(trabalhos)}', flush=True)
            if r[0] == 'FALHA':
                falhas.append(r[1:])
                continue
            _, d, h, cab, tipo, blocos = r
            for ordem, (titulo, rotulo) in enumerate(blocos):
                linhas.append([d, h, cab, tipo, ordem, titulo, rotulo])

    with io.open(RAIZ / a.saida, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['data', 'hora', 'dia', 'tipo', 'ordem', 'bloco', 'origem'])
        w.writerows(linhas)

    print(f'\nescrito {a.saida}: {len(linhas)} blocos')
    if falhas:
        print(f'FALHAS: {len(falhas)}')
        for f_ in falhas[:5]:
            print('  ', f_)


if __name__ == '__main__':
    main()
