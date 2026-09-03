"""
De que Comum vem o oficio do dia.

O quarto campo da linha [Rank] de cada santo diz onde ir buscar o que o
proprio nao traz:

    ;;Duplex majus;;4;;vide C5          S. Domingos, Confessor
    ;;Duplex;;3;;vide C6-1              Santa Ines, Virgem e Martir

'C5' e o Comum dos Confessores nao Pontifices; 'C6-1' e o das Virgens
Martires. A palavra a frente diz como se usa:

    vide   o Comum serve de fonte, e as remissoes vao la buscar as pecas
    ex     o oficio E o do Comum, e o proprio so acrescenta

Sao 1.388 remissoes 'vide' no corpus — a terceira familia mais numerosa,
depois das '@' e das '!'.

Porta de extract_common, em horascommon.pl.
"""

import re
from pathlib import Path

# Um Comum de verdade: 'C5', 'C6-1', 'C4a', e o que venha depois de uma
# barra. A recusa do 'Sancti' e do original: 'vide Sancti/01-06' nao e um
# Comum, e um oficio de santo a servir de Comum, e trata-se abaixo.
COMUM_PROPRIO = re.compile(
    r'^(ex|vide)\s*(?!Sancti)((?:[a-z\s]*/)?C[0-9]+[a-z]*-*[123]*)', re.I)
COMO_COMUM = re.compile(r'(ex|vide)\s*Sancti(?:M|OP|Cist)?/(.*)\s*$', re.I)
QUALQUER = re.compile(r'(ex|vide)\s*(.*)\s*$', re.I)


def subpasta(nome, version=''):
    """Porta de subdirname. O nosso rito e o romano; as outras familias
    ficam aqui so para o codigo dizer o que faz."""
    if re.search(r'Cisterciensis', version):
        return f'{nome}Cist/'
    if re.match(r'^Monastic', version):
        return f'{nome}M/'
    if re.match(r'^Ordo Praedicatorum', version):
        return f'{nome}OP/'
    return f'{nome}/'


def extrair_comum(campo, rank=0, version='Rubrics 1960 - 1960',
                  tempo_pascal=False, base=None):
    """Devolve (tipo, ficheiro) — ('vide', 'Commune/C5.txt') — ou (None, None).

    'tempo_pascal' faz procurar a variante propria do tempo pascal: no
    tempo da Pascoa os Comuns dos Apostolos e dos Martires trocam para
    'C1p', 'C3p', que trazem o Alleluia. So se troca se o ficheiro existir,
    e por isso e precisa a raiz do corpus em 'base'.
    """
    campo = (campo or '').strip()
    if not campo:
        return None, None

    m = COMUM_PROPRIO.match(campo)
    if m:
        tipo, comum = m.group(1), m.group(2)
        if re.search(r'Trident', version, re.I) and rank >= 2:
            tipo = 'ex'
        if tempo_pascal and base is not None:
            if re.search(r'C\d(?![3-9])[a-z]?', comum):
                caminho = (Path(base) / 'Latin'
                           / f'{subpasta("Commune", version)}{comum}p.txt')
                if caminho.exists():
                    comum += 'p'
        return tipo, f'{subpasta("Commune", version)}{comum}.txt'

    m = COMO_COMUM.match(campo)
    if m:
        tipo = 'ex' if re.search(r'Trident', version, re.I) else m.group(1)
        return tipo, f'{subpasta("Sancti", version)}{m.group(2).strip()}.txt'

    m = QUALQUER.match(campo)
    if m:
        tipo = 'ex' if re.search(r'Trident', version, re.I) else m.group(1)
        nome = re.sub(r'Tempora(?:M|OP|Cist)?/', '', m.group(2), flags=re.I)
        nome = nome.strip()
        if not re.search(r'Sancti|Commune', nome, re.I):
            return tipo, f'{subpasta("Tempora", version)}{nome}.txt'
        return tipo, f'{nome}.txt'

    return None, None


def comum_do_oficio(resolvedor, ficheiro, version='Rubrics 1960 - 1960',
                    tempo_pascal=False):
    """O Comum de um oficio, lido da sua propria linha [Rank].

    Devolve (tipo, ficheiro, rank). O rank e o terceiro campo, e serve
    para saber a classe da festa.
    """
    secoes = resolvedor.setupstring('Latin', ficheiro)
    campos = (secoes.get('Rank') or '').strip().split(';;')
    rank = 0.0
    if len(campos) > 2:
        try:
            rank = float(campos[2])
        except ValueError:
            rank = 0.0
    campo = campos[3] if len(campos) > 3 else ''
    tipo, comum = extrair_comum(campo, rank, version, tempo_pascal,
                                resolvedor.base)
    return tipo, comum, rank
