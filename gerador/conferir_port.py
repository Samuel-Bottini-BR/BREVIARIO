"""
Confere o port em Python do motor de condicionais contra o Perl original,
sobre TODO o corpus.

Roda os dois sobre os mesmos arquivos e compara linha a linha. Qualquer
divergencia e reportada com o contexto, porque uma diferenca aqui vira
texto errado na pagina impressa sem ninguem perceber.

uso: python conferir_port.py <caminho-do-repo> [limite]
"""

import subprocess
import sys
from pathlib import Path

# O console do Windows vem em cp1252 e engasga com o latim acentuado.
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto, process_conditional_lines

VERSAO = 'Rubrics 1960 - 1960'
if '--versao' in sys.argv:
    VERSAO = sys.argv[sys.argv.index('--versao') + 1]

# So o que entra no nosso breviario: o esqueleto comum, o latim e o
# portugues. Ficam de fora os outros idiomas e as familias cisterciense,
# monastica e dominicana.
RAIZES = ('Ordinarium/', 'Latin/', 'Portugues/')
PASTAS_DE_OUTRAS_FAMILIAS = {
    'CommuneCist', 'CommuneM', 'CommuneOP',
    'SanctiCist', 'SanctiM', 'SanctiOP',
    'TemporaCist', 'TemporaM', 'TemporaOP',
    'Martyrologium1570', 'Martyrologium1955R',
    'Regula', 'Necrologium',
}


def interessa(rel):
    if not rel.startswith(RAIZES):
        return False
    return not any(p in PASTAS_DE_OUTRAS_FAMILIAS for p in rel.split('/'))


def caminho_msys(p):
    """C:\\Users\\x  ->  /c/Users/x

    O Perl que vem com o Git para Windows e um Perl de msys: ele nao abre
    caminho com letra de unidade. Sem esta conversao todos os arquivos
    falham em silencio com 'No such file or directory'.
    """
    p = str(p).replace('\\', '/')
    if len(p) > 1 and p[1] == ':':
        p = '/' + p[0].lower() + p[2:]
    return p


def rodar_perl(repo, alvos):
    entrada = '\n'.join(alvos) + '\n'
    r = subprocess.run(
        ['perl',
         caminho_msys(Path(__file__).parent / 'conferir_perl.pl'),
         caminho_msys(repo),
         VERSAO],
        input=entrada, capture_output=True, text=True, encoding='utf-8',
    )
    if r.returncode != 0:
        raise RuntimeError(f'perl falhou:\n{r.stderr[:2000]}')

    resultados, atual, linhas = {}, None, []
    for linha in r.stdout.replace('\r\n', '\n').split('\n'):
        if linha.startswith('<<<<ARQUIVO '):
            atual, linhas = linha[len('<<<<ARQUIVO '):], []
        elif linha == '>>>>FIM':
            if atual is not None:
                resultados[atual] = linhas
            atual, linhas = None, []
        elif atual is not None:
            linhas.append(linha)
    return resultados


def rodar_python(repo, alvo):
    texto = (Path(repo) / 'web/www/horas' / alvo).read_text(encoding='utf-8-sig')
    linhas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if linhas and linhas[-1] == '':
        linhas.pop()
    ctx = Contexto(version=VERSAO, hora='Completorium',
                   tempore='post Pentecosten', dayofweek=0)
    return process_conditional_lines(linhas, ctx)


def aparar(xs):
    xs = list(xs)
    while xs and xs[-1] == '':
        xs.pop()
    return xs


def main():
    repo = Path(sys.argv[1])
    posicionais = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--versao' in sys.argv:
        posicionais = [a for a in posicionais if a != VERSAO]
    limite = int(posicionais[1]) if len(posicionais) > 1 else None
    base = repo / 'web/www/horas'

    alvos = sorted(
        r for r in (
            str(p.relative_to(base)).replace('\\', '/')
            for p in base.rglob('*.txt')
        ) if interessa(r)
    )
    if limite:
        alvos = alvos[:limite]

    print(f'{len(alvos)} arquivos a conferir')
    resultados_perl = rodar_perl(repo, alvos)

    iguais = divergentes = erros = 0
    exemplos = []

    for alvo in alvos:
        a = resultados_perl.get(alvo)
        if a is None:
            erros += 1
            if len(exemplos) < 10:
                exemplos.append((alvo, 'o perl nao devolveu nada para este arquivo', None, None))
            continue
        if a and a[0].startswith('<<<<ERRO'):
            erros += 1
            if len(exemplos) < 10:
                exemplos.append((alvo, a[0], None, None))
            continue
        try:
            b = rodar_python(repo, alvo)
        except Exception as e:
            erros += 1
            exemplos.append((alvo, f'python levantou {e!r}', None, None))
            continue

        a, b = aparar(a), aparar(b)
        if a == b:
            iguais += 1
        else:
            divergentes += 1
            if len(exemplos) < 10:
                for i in range(max(len(a), len(b))):
                    la = a[i] if i < len(a) else '<fim>'
                    lb = b[i] if i < len(b) else '<fim>'
                    if la != lb:
                        exemplos.append((alvo, f'linha {i + 1}', la, lb))
                        break

    for alvo, onde, la, lb in exemplos:
        print(f'\nDIVERGE  {alvo}  {onde}')
        if la is not None:
            print(f'   perl  : {la!r}')
            print(f'   python: {lb!r}')

    print()
    print(f'iguais      {iguais}')
    print(f'divergentes {divergentes}')
    print(f'erros       {erros}')
    return 1 if divergentes or erros else 0


if __name__ == '__main__':
    sys.exit(main())
