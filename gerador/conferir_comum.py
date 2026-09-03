"""
Confere o extractor do Comum contra o original do Divinum Officium.

Os casos nao sao inventados: sao TODOS os campos de Comum que existem nas
linhas [Rank] do corpus, cada um com a sua classe verdadeira e fora e
dentro do tempo pascal.

uso: python conferir_comum.py <repo>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from comum import extrair_comum
from colher import caminho_msys, PERL5LIB

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VERSAO = 'Rubrics 1960 - 1960'
PASTAS = ('Sancti', 'Tempora', 'Commune')


def casos(repo):
    base = Path(repo) / 'web/www/horas/Latin'
    vistos = set()
    for pasta in PASTAS:
        for p in (base / pasta).rglob('*.txt'):
            try:
                texto = p.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeDecodeError):
                continue
            dentro = False
            for linha in texto.split('\n'):
                if linha.startswith('['):
                    dentro = linha.strip().lower() == '[rank]'
                    continue
                if not dentro or ';;' not in linha:
                    continue
                campos = linha.strip().split(';;')
                if len(campos) < 4 or not campos[3].strip():
                    continue
                rank = campos[2].strip()
                try:
                    float(rank)
                except ValueError:
                    rank = '0'
                vistos.add((campos[3].strip(), rank))

    fora = []
    for campo, rank in sorted(vistos):
        for pascal in ('0', '1'):
            fora.append((campo, rank, pascal))
    return fora


def rodar_perl(repo, lista):
    entrada = ''.join(f'{c}\t{r}\t{p}\n' for c, r, p in lista)
    proc = subprocess.run(
        ['perl', caminho_msys(Path(__file__).parent / 'comum_perl.pl'),
         caminho_msys(repo)],
        input=entrada, capture_output=True, text=True, encoding='utf-8',
        errors='replace', env={**os.environ, 'PERL5LIB': PERL5LIB},
    )
    if proc.returncode != 0:
        raise RuntimeError(f'perl falhou:\n{proc.stderr[:3000]}')
    saida = {}
    for linha in proc.stdout.replace('\r\n', '\n').split('\n'):
        if not linha.strip():
            continue
        partes = linha.split('\t')
        if len(partes) == 3 and partes[0].isdigit():
            saida[int(partes[0])] = (partes[1], partes[2])
    return saida


def main():
    repo = Path(sys.argv[1]).resolve()
    lista = casos(repo)
    print(f'{len(lista)} casos')

    esperado = rodar_perl(repo, lista)
    base = repo / 'web/www/horas'

    iguais = divergentes = 0
    exemplos = []
    for i, (campo, rank, pascal) in enumerate(lista, start=1):
        tipo, ficheiro = extrair_comum(campo, float(rank), VERSAO,
                                       pascal == '1', base)
        obtido = (tipo or '', ficheiro or '')
        esp = esperado.get(i, ('?', '?'))
        if obtido == esp:
            iguais += 1
        else:
            divergentes += 1
            if len(exemplos) < 12:
                exemplos.append((campo, rank, pascal, esp, obtido))

    for campo, rank, pascal, esp, obt in exemplos:
        print(f'\nDIVERGE  {campo!r}  classe {rank}  pascal {pascal}')
        print(f'   perl  : {esp}')
        print(f'   python: {obt}')

    print()
    print(f'casos iguais      {iguais}')
    print(f'casos divergentes {divergentes}')
    return 1 if divergentes else 0


if __name__ == '__main__':
    sys.exit(main())
