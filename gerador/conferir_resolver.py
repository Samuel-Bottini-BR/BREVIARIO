"""
Confere o resolvedor de remissoes contra o setupstring original do
Divinum Officium, ficheiro a ficheiro e seccao a seccao.

Uma diferenca aqui nao da erro: da texto errado numa pagina impressa, em
latim correto e bem diagramado, e ninguem repara. Por isso o confronto e
sobre o corpus inteiro, e nao sobre uma amostra.

uso: python conferir_resolver.py <repo> [--idioma Latin] [--limite N]
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto
from resolver import Resolvedor
from colher import caminho_msys

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VERSAO = 'Rubrics 1960 - 1960'

PASTAS_DE_OUTRAS_FAMILIAS = {
    'CommuneCist', 'CommuneM', 'CommuneOP',
    'SanctiCist', 'SanctiM', 'SanctiOP',
    'TemporaCist', 'TemporaM', 'TemporaOP',
    'Martyrologium1570', 'Martyrologium1955R',
    'Regula', 'Necrologium',
}


def rodar_perl(repo, idioma, alvos):
    entrada = '\n'.join(alvos) + '\n'
    r = subprocess.run(
        ['perl', caminho_msys(Path(__file__).parent / 'resolver_perl.pl'),
         caminho_msys(repo), idioma, VERSAO],
        input=entrada, capture_output=True, text=True, encoding='utf-8',
        errors='replace',
    )
    if r.returncode != 0:
        raise RuntimeError(f'perl falhou:\n{r.stderr[:2000]}')

    saida, ficheiro, seccao, linhas = {}, None, None, []

    def fechar_seccao():
        if ficheiro is not None and seccao is not None:
            saida.setdefault(ficheiro, {})[seccao] = '\n'.join(linhas).rstrip('\n')

    for linha in r.stdout.replace('\r\n', '\n').split('\n'):
        if linha.startswith('<<<<FICHEIRO '):
            fechar_seccao()
            ficheiro, seccao, linhas = linha[13:], None, []
            saida.setdefault(ficheiro, {})
        elif linha.startswith('<<<<SECCAO '):
            fechar_seccao()
            seccao, linhas = linha[11:], []
        elif linha.startswith('<<<<ERRO'):
            fechar_seccao()
            saida.setdefault(ficheiro, {})['__erro'] = linha
            seccao, linhas = None, []
        elif linha == '>>>>FIM':
            fechar_seccao()
            seccao, linhas = None, []
        elif seccao is not None:
            linhas.append(linha)
    fechar_seccao()
    return saida


def normalizar(t):
    """O Perl e o Python diferem em espaco no fim de linha; isso nao e
    divergencia de conteudo."""
    t = (t or '').replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(l.rstrip() for l in t.split('\n')).strip('\n')


def main():
    # Absoluto: o Perl corre noutra pasta e um caminho relativo nao o
    # levaria a lado nenhum.
    repo = Path(sys.argv[1]).resolve()
    idioma = 'Latin'
    if '--idioma' in sys.argv:
        idioma = sys.argv[sys.argv.index('--idioma') + 1]
    limite = None
    if '--limite' in sys.argv:
        limite = int(sys.argv[sys.argv.index('--limite') + 1])

    base = repo / 'web/www/horas' / idioma
    alvos = sorted(
        str(p.relative_to(base)).replace('\\', '/')
        for p in base.rglob('*.txt')
        if not any(x in PASTAS_DE_OUTRAS_FAMILIAS for x in p.parts)
    )
    if limite:
        alvos = alvos[:limite]
    print(f'{len(alvos)} ficheiros em {idioma}')

    esperado = rodar_perl(repo, idioma, alvos)

    # O mesmo estado que resolver_perl.pl fixa. Varios ficheiros trazem
    # condicionais sobre o dia da semana — '(feria 2) @:Feria2 Ant 2' —
    # e comparar em dias diferentes daria divergencias que nao existem.
    ctx = Contexto(version=VERSAO, dayofweek=4, month=1)
    r = Resolvedor(repo, ctx)

    iguais = divergentes = erros = 0
    exemplos = []

    for alvo in alvos:
        esp = esperado.get(alvo)
        if esp is None or '__erro' in esp:
            erros += 1
            if len(exemplos) < 8:
                exemplos.append((alvo, '', 'o perl nao devolveu', ''))
            continue
        try:
            obtido = r.setupstring(idioma, alvo)
        except Exception as e:
            erros += 1
            if len(exemplos) < 8:
                exemplos.append((alvo, '', f'python: {e!r}', ''))
            continue

        chaves = set(esp) | {k for k in obtido if k != '__preamble'}
        for k in sorted(chaves):
            a, b = normalizar(esp.get(k)), normalizar(obtido.get(k))
            if a == b:
                iguais += 1
            else:
                divergentes += 1
                if len(exemplos) < 8:
                    exemplos.append((alvo, k, a, b))

    for alvo, k, a, b in exemplos:
        print(f'\nDIVERGE  {alvo}  [{k}]')
        print(f'   perl  : {a[:220]!r}')
        print(f'   python: {b[:220]!r}')

    print()
    print(f'seccoes iguais      {iguais}')
    print(f'seccoes divergentes {divergentes}')
    print(f'ficheiros com erro  {erros}')
    return 1 if divergentes or erros else 0


if __name__ == '__main__':
    sys.exit(main())
