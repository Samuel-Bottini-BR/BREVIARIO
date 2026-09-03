"""
O Ordo: que oficio se reza em cada dia do ano.

O breviario e perpetuo — a mesma pagina serve 2026 e 2050. O que muda todo
o ano e so QUAL peca combinar em cada dia, e isso e o Ordo (seccao 12 do
prompt).

**Nada aqui e calculado por nos.** As regras de precedencia — qual festa
vence, o que se comemora, de que Comum se toma — sao as do Divinum
Officium, chamadas uma vez pela sua propria funcao 'precedence', e o
resultado fica guardado numa tabela. E o que a seccao 12 manda: 'nao
calcule nada, pegue pronto'.

A tabela e um ficheiro de texto com uma linha por dia e por hora. Gera-se
uma vez por ano:

    python ordo.py --ano 2026

e depois le-se sem tocar no Perl:

    from ordo import Ordo
    o = Ordo(RAIZ / 'ordo-2026.tsv')
    r = o.dia('08-22-2026', 'Completorium')
    r.vencedor   -> 'Sancti/08-22.txt'
    r.comum      -> 'Commune/C11.txt'
"""

import argparse
import csv
import io
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from colher import caminho_msys, PERL5LIB, HORAS

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'

CAMPOS = ['data', 'hora', 'vencedor', 'classe', 'comum', 'tipo_comum',
          'regra', 'regra_comum', 'tempo', 'nome', 'vespera', 'laudes',
          'comemorado', 'tempus', 'die', 'titulo', 'comentario',
          'tempora_salmos', 'tempora', 'dayofweek', 'monthday', 'monthday_comem', 'monthday_amanha', 'temporas',
          'ficheiro', 'martir_ficheiro', 'martir_luna', 'martir_movel',
          'comemoracoes', 'concorrente', 'concorrente_vespera',
          'comemoracoes_amanha',
          # so as Matinas usam o que vem daqui para baixo
          'escritura', 'comrank', 'vigilia_transferida', 'initia', 'duplex',
          'initia_ficheiro', 'nat_ficheiro', 'mes_vencedor', 'mes_comum', 'mes_escritura',
          'mes_comemorado']


class DiaDoOrdo:
    """Uma linha da tabela: o oficio de um dia, numa hora."""

    __slots__ = CAMPOS

    # As regras vem com as mudancas de linha guardadas como '\n' de dois
    # caracteres — ver a nota em ordo_perl.pl. Aqui desdobram-se, porque
    # varias regras so valem dentro da sua propria linha.
    MULTILINHA = ('regra', 'regra_comum')

    def __init__(self, valores):
        for campo in CAMPOS:
            v = valores.get(campo, '') or ''
            if campo in self.MULTILINHA:
                v = v.replace('\\n', '\n')
            setattr(self, campo, v)

    @property
    def rank(self):
        try:
            return float(self.classe)
        except ValueError:
            return 0.0

    def variante(self, chamador):
        """A variante do tempo para uma peca: 'Dominica', 'Feria', 'Adv',
        'Quad', 'Pasch'. Vem do 'gettempora' deles, ja calculado."""
        for par in (self.tempora or '').split(';;'):
            chave, _, valor = par.partition('=')
            if chave == chamador:
                return valor
        return ''

    def __repr__(self):
        return (f'<{self.data} {self.hora}: {self.nome} '
                f'[{self.vencedor}] ~ {self.classe}>')


class Ordo:
    """A tabela do ano, lida do disco."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self._por_dia = {}
        with io.open(self.caminho, encoding='utf-8', newline='') as f:
            for linha in csv.DictReader(f, delimiter='\t'):
                self._por_dia[(linha['data'], linha['hora'])] = \
                    DiaDoOrdo(linha)

    def dia(self, data, hora):
        """data no formato do Divinum Officium: 'MM-DD-AAAA'."""
        return self._por_dia.get((data, hora))

    def __len__(self):
        return len(self._por_dia)

    @property
    def datas(self):
        return sorted({d for d, _ in self._por_dia})


# --------------------------------------------------------------------------
# A colheita — a unica parte que toca no Perl
# --------------------------------------------------------------------------

def datas_do_ano(ano):
    d, fim = date(ano, 1, 1), date(ano, 12, 31)
    while d <= fim:
        yield f'{d.month:02d}-{d.day:02d}-{d.year}'
        d += timedelta(days=1)


def colher(repo, datas, horas=None):
    """Corre a funcao de precedencia deles, uma vez por dia e por hora."""
    horas = horas or HORAS
    entrada = ''.join(f'{d}\t{h}\n' for d in datas for h in horas)

    r = subprocess.run(
        ['perl', caminho_msys(Path(__file__).parent / 'ordo_perl.pl'),
         caminho_msys(Path(repo).resolve())],
        input=entrada, capture_output=True, text=True, encoding='utf-8',
        errors='replace', env={**os.environ, 'PERL5LIB': PERL5LIB},
    )
    if r.returncode != 0:
        raise RuntimeError(f'perl falhou:\n{r.stderr[:3000]}')

    linhas, erros = [], []
    for l in r.stdout.replace('\r\n', '\n').split('\n'):
        if not l.strip():
            continue
        partes = l.split('\t')
        if len(partes) > 2 and partes[2] == 'ERRO':
            erros.append(partes)
            continue
        partes += [''] * (len(CAMPOS) - len(partes))
        linhas.append(dict(zip(CAMPOS, partes[:len(CAMPOS)])))
    return linhas, erros


def guardar(linhas, caminho):
    with io.open(caminho, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter='\t')
        w.writeheader()
        w.writerows(linhas)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ano', type=int, default=2026)
    p.add_argument('--saida')
    a = p.parse_args()

    saida = Path(a.saida) if a.saida else RAIZ / f'ordo-{a.ano}.tsv'
    datas = list(datas_do_ano(a.ano))
    print(f'{len(datas)} dias x {len(HORAS)} horas = '
          f'{len(datas) * len(HORAS)} consultas')

    linhas, erros = colher(REPO, datas)
    guardar(linhas, saida)

    print(f'escrito {saida.name}: {len(linhas)} linhas')
    if erros:
        print(f'ERROS: {len(erros)}')
        for e in erros[:5]:
            print('  ', e[:3])

    # Nunca dar por bom o que nao se olhou.
    o = Ordo(saida)
    print(f'relido: {len(o)} registos, {len(o.datas)} dias')
    for d in ('01-01-2026', '04-05-2026', '08-04-2026', '08-22-2026',
              '12-25-2026'):
        r = o.dia(d, 'Laudes')
        print(f'   {d}  {r.nome}  [{r.vencedor}]'
              + (f'  Comum: {r.comum} ({r.tipo_comum})' if r.comum else ''))


if __name__ == '__main__':
    main()
