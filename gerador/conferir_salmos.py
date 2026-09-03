"""
Confere a funcao '&psalm' portada contra a original do Divinum Officium.

E a funcao que poe salmo na pagina — a mais usada de todas. Um erro aqui
nao levanta excepcao nenhuma: da um versiculo a menos, ou um numero
errado, numa pagina bem composta, e ninguem repara antes de o livro estar
impresso. Por isso o confronto e sobre TODOS os ficheiros de salmo, nas
duas linguas, e sobre todas as formas de chamada que existem no corpus.

Os casos sao tres familias:

  1. cada ficheiro de salmo, inteiro, em latim e em portugues
  2. todas as chamadas '&psalm(...)' escritas nos ficheiros do corpus —
     recortes de versiculos, o sinal de 'sem Gloria', o saltimo 94C
  3. as mesmas, com antifona, que e o que faz nascer o sinal '‡'

uso: python conferir_salmos.py <repo> [--limite N]
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto
from resolver import Resolvedor
import funcoes
from funcoes import Funcoes, EstadoDoDia
from colher import caminho_msys, PERL5LIB

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VERSAO = 'Rubrics 1960 - 1960'
IDIOMAS = ('Latin', 'Portugues')

# Antifonas reais, para o sinal '‡'. A primeira e a das Completas de
# domingo, e casa com o comeco do salmo 4; a segunda nao casa com nada, e
# serve para conferir que nesse caso o versiculo sai intacto.
ANTIFONAS = [
    'Miserére mihi, Dómine, * et exáudi oratiónem meam.',
    'Cum invocárem exaudívit me Deus justítiæ meæ.',
]


def casos(repo, limite=None):
    """A lista de casos a conferir, cada um (idioma, argumentos, antifona)."""
    base = Path(repo) / 'web/www/horas'
    fora = []

    # 1. cada ficheiro de salmo, inteiro
    nums = sorted(
        (p.stem[5:] for p in (base / 'Latin/Psalterium/Psalmorum').glob('Psalm*.txt')),
        key=lambda s: (int(re.match(r'\d+', s).group()) if re.match(r'\d+', s)
                       else 0, s))
    for num in nums:
        for idioma in IDIOMAS:
            fora.append((idioma, num, ''))

    # 2. as chamadas escritas no corpus
    escritas = set()
    for p in base.rglob('*.txt'):
        try:
            texto = p.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r'&psalm\(([^)]*)\)', texto):
            escritas.add(m.group(1).strip())
    for arg in sorted(escritas):
        for idioma in IDIOMAS:
            fora.append((idioma, arg, ''))

    # 3. com antifona
    for arg in ['4', '90', '133', '233', '231', '118,1,8', '94']:
        for idioma in IDIOMAS:
            for ant in ANTIFONAS:
                fora.append((idioma, arg, ant))

    return fora[:limite] if limite else fora


def rodar_perl(repo, lista):
    entrada = ''.join(f'{i}\t{a}\t{ant}\n' for i, a, ant in lista)
    # As opcoes de apresentacao vao daqui para o Perl, para que os dois
    # lados nao possam divergir por descuido.
    opcoes = [str(int(funcoes.NONUMBERS)), str(int(funcoes.NOINNUMBERS)),
              str(int(funcoes.NOFLEXA))]
    r = subprocess.run(
        ['perl', caminho_msys(Path(__file__).parent / 'salmos_perl.pl'),
         caminho_msys(repo)] + opcoes,
        input=entrada, capture_output=True, text=True, encoding='utf-8',
        errors='replace', env={**os.environ, 'PERL5LIB': PERL5LIB},
    )
    if r.returncode != 0:
        raise RuntimeError(f'perl falhou:\n{r.stderr[:3000]}')

    saida, atual, linhas = {}, None, []
    for linha in r.stdout.replace('\r\n', '\n').split('\n'):
        if linha.startswith('<<<<CASO '):
            atual, linhas = int(linha[9:]), []
        elif linha.startswith('<<<<ERRO'):
            if atual:
                saida[atual] = linha
            atual = None
        elif linha == '>>>>FIM':
            if atual:
                saida[atual] = '\n'.join(linhas)
            atual, linhas = None, []
        elif atual:
            linhas.append(linha)
    if r.stderr.strip():
        print(f'  (perl escreveu em stderr: {r.stderr.strip()[:300]})')
    return saida


def normalizar(t):
    """Espaco no fim de linha nao e divergencia de conteudo. Espaco a mais
    dentro da linha e — o '‡' da antifona nasce de um espaco duplicado no
    original, e queremos ver se o reproduzimos."""
    t = (t or '').replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(l.rstrip() for l in t.split('\n')).strip('\n')


def main():
    # Absoluto: o Perl corre noutra pasta e um caminho relativo nao o
    # levaria a lado nenhum.
    repo = Path(sys.argv[1]).resolve()
    limite = None
    if '--limite' in sys.argv:
        limite = int(sys.argv[sys.argv.index('--limite') + 1])

    lista = casos(repo, limite)
    print(f'{len(lista)} casos')

    esperado = rodar_perl(repo, lista)

    ctx = Contexto(version=VERSAO, dayofweek=4, month=1)
    r = Resolvedor(repo, ctx)

    iguais = divergentes = 0
    exemplos = []

    for i, (idioma, arg, ant) in enumerate(lista, start=1):
        f = Funcoes(r, EstadoDoDia(version=VERSAO, hora='Completorium',
                                   dayofweek=4))
        args = Funcoes.argumentos(arg) + [idioma]
        if ant:
            args.append(ant)
        try:
            obtido = f.psalm(*args)
        except Exception as e:
            obtido = f'EXCEPCAO {e!r}'

        a, b = normalizar(esperado.get(i)), normalizar(obtido)
        if a == b:
            iguais += 1
        else:
            divergentes += 1
            if len(exemplos) < 10:
                exemplos.append((idioma, arg, ant, a, b))

    for idioma, arg, ant, a, b in exemplos:
        print(f'\nDIVERGE  &psalm({arg})  {idioma}'
              + (f'  ant: {ant[:40]}' if ant else ''))
        print(f'   perl  : {a[:300]!r}')
        print(f'   python: {b[:300]!r}')

    print()
    print(f'casos iguais      {iguais}')
    print(f'casos divergentes {divergentes}')
    return 1 if divergentes else 0


if __name__ == '__main__':
    sys.exit(main())
