"""
O miolo das Matinas: invitatorio, hino, nocturnos, bencaos e licoes.

Porta do ramo romano de 1960 de 'specmatins.pl' — 1.864 linhas, a maior
peca do projecto. Fica de fora tudo o que e monastico, cisterciense,
dominicano ou tridentino, pelo mesmo motivo de sempre: o nosso breviario
e o romano de 1960.

A HORA, EM RESUMO
-----------------
Matinas e a unica hora que muda de tamanho conforme o dia:

    festa de I ou II classe   tres nocturnos, nove salmos, nove licoes
    tudo o resto              um nocturno, nove salmos, tres licoes

Quem decide e 'gettype1960', que devolve de que familia e o oficio:
feria, domingo, santo, ou dia dentro de uma oitava de II classe. Dessa
familia sai quantas licoes se dizem, para onde a terceira licao se desvia
— para a homilia num domingo, para a legenda do santo numa festa — e se
ha Te Deum no fim.

O QUE NAO SE PORTOU, E PORQUE
-----------------------------
'initiarule' e a tabela dos incipit transferidos ('Stransfer'). Nas
rubricas de 1960 ela esta VAZIA: a tabela do ano tem entradas marcadas
'DA', '1570', 'Newcal' — nenhuma casa com o padrao '1960', e a versao de
1960 nao herda tabela de transferencia nenhuma (a coluna 'transferbase'
do 'data.txt' deles esta em branco para ela). Medido: zero entradas nos
365 dias de 2026. Com 'initiarule' vazia, 'resolveitable' e 'tferifile'
nunca correm — e por isso nao estao aqui.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proprio import Dia, officestring
import alleluia

FICHEIRO_SALMOS = 'Psalterium/Psalmi/Psalmi matutinum.txt'
FICHEIRO_ESPECIAL = 'Psalterium/Special/Matutinum Special.txt'
FICHEIRO_BENCAOS = 'Psalterium/Benedictions.txt'
FICHEIRO_INVITATORIO = 'Psalterium/Invitatorium.txt'

# As familias de oficio que 'gettype1960' distingue.
LT_OUTRO = 0        # nove licoes — festa de I ou II classe
LT_FERIAL = 1
LT_DOMINGO = 2
LT_SANTORAL = 3
LT_OITAVA_II = 4    # dias depois do Natal


class Matinas:
    """O estado de um dia a Matinas.

    Junta num so sitio o que as funcoes do original leem de variaveis
    globais: o oficio vencedor, o Comum, a Escritura corrente, o oficio
    comemorado, e a linha do Ordo com tudo o que a precedencia decidiu.
    """

    def __init__(self, r, registo, dia, lang='Latin'):
        self.r = r
        self.registo = registo
        self.dia = dia
        self.lang = lang

        self.vencedor = registo.vencedor or ''
        self.rule = dia.rule or ''
        self.comum = registo.comum or ''
        self.tipo_comum = registo.tipo_comum or ''
        self.rank = registo.rank
        self.dayofweek = int(registo.dayofweek or 0)
        self.mes, self.dia_do_mes, self.ano = (
            int(x) for x in registo.data.split('-'))
        self.tempo = registo.tempo or ''       # $dayname[0]
        self.titulo = registo.titulo or ''     # $dayname[1]
        self.duplex = _numero(registo.duplex)
        self.comrank = _numero(registo.comrank)
        self.monthday = registo.monthday or ''
        self.laudes = int(registo.laudes or 1)

        self.secoes = dia.secoes
        self.secoes_comum = (
            officestring(r, lang, registo.comum, registo.mes_comum)
            if registo.comum else {})
        self.escritura = (
            officestring(r, lang, registo.escritura, registo.mes_escritura)
            if registo.escritura else {})
        self.comemorado = (
            officestring(r, lang, registo.comemorado, registo.mes_comemorado)
            if registo.comemorado else {})
        self.ficheiro_comemorado = registo.comemorado or ''

        self.pascal = alleluia.e_tempo_pascal(self.tempo)
        self.al = alleluia.Alleluia(r)
        self.ltype = self.tipo1960()

    # ------------------------------------------------------------------ #

    def salmos(self):
        return self.r.setupstring(self.lang, FICHEIRO_SALMOS)

    def especial(self):
        return self.r.setupstring(self.lang, FICHEIRO_ESPECIAL)

    def traduzir(self, nome):
        return self.r.traduzir(nome, self.lang)

    def formula(self, nome):
        texto, _ = self.r.formula(nome, self.lang)
        return texto

    # ------------------------------------------------------------------ #

    def tipo1960(self):
        """De que familia e o oficio de hoje. Porta de gettype1960.

        E a chave de toda a hora: dela sai quantas licoes se dizem, para
        onde a terceira se desvia, e se ha Te Deum.
        """
        tipo = LT_OUTRO
        if re.search(r'post Nativitatem', self.titulo, re.I):
            tipo = LT_OITAVA_II
        elif self.rank < 2 or re.search(r'(feria|vigilia|die)', self.titulo,
                                        re.I):
            tipo = LT_FERIAL
        elif (re.search(r'dominica.*?semiduplex', self.titulo, re.I)
              or re.search(r'Pasc1-0', self.vencedor, re.I)):
            tipo = LT_DOMINGO
        elif self.rank < 5:
            tipo = LT_SANTORAL
        if re.search(r'9 lectiones 1960|12 lectiones', self.rule, re.I):
            tipo = LT_OUTRO
        return tipo

    def nove_licoes(self):
        """Se o dia leva tres nocturnos e nove licoes.

        E a condicao que abre o ramo longo de psalmi_matutinum.
        """
        return (bool(re.search(r'9 lectio', self.rule, re.I))
                and not self.ltype
                and self.rank >= 2)

    def i_do_dia(self):
        """Porta de dayofweek2i: 1 as segundas, quintas e domingos; 2 as
        tercas e sextas; 3 as quartas e sabados."""
        i = self.dayofweek or 1
        return i - 3 if i > 3 else i

    def contrair_escritura(self, num, resp=False):
        """Se as licoes 2 e 3 se juntam numa so. Porta de
        contract_scripture.

        E a reforma de 1960: num domingo ou numa festa de III classe
        dizem-se tres licoes, e a Escritura que dava duas passa a dar uma.
        """
        if num != 2:
            return False
        if re.search(r'C10', self.comum, re.I):
            return True
        if (self.ltype in (LT_SANTORAL, LT_DOMINGO)
                and (not re.search(r'scriptura1960', self.rule, re.I) or resp)
                and (not re.search(r'feria', self.titulo, re.I)
                     or self.ficheiro_comemorado)):
            return True
        return False

    def te_deum(self, num):
        """Se depois desta licao se diz o Te Deum. Porta de
        tedeum_required."""
        ultima = ((num == 9 and re.search(r'9 lectiones', self.rule, re.I))
                  or (num == 3
                      and (not re.search(r'9 lectiones', self.rule, re.I)
                           or self.duplex == 1
                           or self.ltype != LT_OUTRO)))
        if not ultima:
            return False
        if re.search(r'no Te Deum', self.rule):
            return False
        if re.search(r'C9', self.comum):
            return False
        if re.match(r'Tempora.*(?:Adv|Quad)', self.vencedor):
            return False
        return bool(
            (not self.dayofweek and not re.search(r'Vigilia', self.titulo, re.I))
            or (re.search(r'Sancti|Commune', self.vencedor, re.I)
                and not re.search(r'Vigilia', self.titulo, re.I))
            or re.search(r'Feria Te Deum', self.rule, re.I)
            or re.search(r'Pasc|Nat|C10', self.vencedor)
            or (re.match(r'Tempora', self.vencedor) and self.rank > 5
                and self.dayofweek))


def linhas(texto):
    """Porta de split("\n", ...).

    O Perl deita fora os campos vazios do FIM da divisao, e varias
    seccoes do corpus acabam em linhas em branco. Sem isto, o versiculo
    de um nocturno saía com duas linhas vazias atras, e essas empurravam
    as antifonas do nocturno seguinte para o lugar errado.
    """
    fora = (texto or '').split('\n')
    while fora and not fora[-1].strip():
        fora.pop()
    return fora


def _numero(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


# --------------------------------------------------------------------------
# O invitatorio
# --------------------------------------------------------------------------

def invitatorium(m):
    """O salmo 94 com a sua antifona, entrelacados. Porta de invitatorium.

    Nao e um salmo com antifona antes e depois: a antifona repete-se
    entre cada estrofe, e uma delas — a segunda metade, depois do
    asterisco — alterna com a inteira. O ficheiro
    'Psalterium/Invitatorium.txt' e o molde disso, com '$ant' e '$ant2'
    nos lugares.
    """
    invit = m.especial()
    nome = m.registo.variante('Invitatorium')
    nome = f'Invit {nome}' if nome else 'Invit'

    # So a seccao geral [Invit] tem uma antifona por dia da semana; as do
    # tempo tem uma so.
    i = m.dayofweek if nome == 'Invit' else 0
    if (i == 0 and nome == 'Invit'
            and (m.mes < 4 or re.match(r'^1\d\d-', m.monthday or ''))):
        # De Janeiro a Marco, e outra vez nos meses liturgicos de Outubro
        # em diante, o domingo tem invitatorio proprio — a oitava linha.
        i = 7

    linhas_da_seccao = linhas(invit.get(nome))
    ant = (linhas_da_seccao[i].strip()
           if i < len(linhas_da_seccao) else '')

    proprio, _ = m.dia.proprium('Invit', flag=True)
    if proprio and proprio.strip():
        ant = proprio.strip()

    # A linha pode vir rotulada — 'Dominica = Regem magnum'.
    ant = re.sub(r'^.*?=\s*', '', ant).strip()
    ant = f'Ant. {ant}'
    ant = m.al.antifona(ant, m.lang, m.pascal)

    partes = ant.split('*')
    ant2 = f'Ant. {partes[1]}' if len(partes) > 1 else ant

    molde = m.r.preambulo(m.lang, FICHEIRO_INVITATORIO) or ''
    if isinstance(molde, list):
        molde = '\n'.join(molde)

    if re.search(r'Invit2', m.rule, re.I):
        # O invitatorio das Temporas do Advento: a antifona nunca se
        # parte, e por isso a segunda metade some.
        molde = re.sub(r' \*.*?$', ' ', molde, flags=re.M)
    elif (re.search(r'Quad[56]', m.tempo, re.I)
          and re.search(r'tempora', m.vencedor, re.I)
          and not re.search(r'Gloria responsory|Invit6', m.rule, re.I)):
        # No tempo da Paixao o Gloria do invitatorio cala-se, e no lugar
        # dele repete-se a antifona.
        molde = molde.replace('&Gloria', '&Gloria2')
        molde = re.sub(r'^(v\.)\s*.* \^ (.)',
                       lambda x: f'{x.group(1)} {x.group(2).upper()}',
                       molde, flags=re.M)
        molde = re.sub(r'\$ant2\s*(?=\$)', '', molde, flags=re.S)
    elif (not (proprio and proprio.strip())
          and m.dayofweek == 1
          and not (m.secoes.get('Invit') or m.secoes_comum.get('Invit'))
          and re.search(r'(Epi|Pent|Quadp)', m.tempo, re.I)):
        # A segunda-feira do tempo comum encurta o salmo: uma estrofe
        # comeca a meio, na palavra marcada com '+'.
        molde = re.sub(r'^(v\.)\s*.* \+ (.)',
                       lambda x: f'{x.group(1)} {x.group(2).upper()}',
                       molde, flags=re.M)

    # As marcas de divisao — '+', '*', '^', '=', '_' seguidos de espaco —
    # sao para o compositor, nao para a pagina.
    molde = re.sub(r'[+*^=_] ', '', molde)
    molde = molde.replace('$ant2', ant2).replace('$ant', ant)
    return molde


# --------------------------------------------------------------------------
# O hino
# --------------------------------------------------------------------------

def hymnus(m):
    """O hino de Matinas. Porta de hymnusmatutinum.

    Nas rubricas de 1960 nao ha hinos deslocados nem fundidos — isso e do
    tempo em que as primeiras Vesperas cediam a hora as segundas, e a
    reforma acabou com essa concorrencia.
    """
    nome = 'Hymnus'
    if 'Hymnus Matutinum' not in m.secoes:
        nome += _mtv(m)
    h, _ = m.dia.proprium(f'{nome} Matutinum', flag=True)
    if h and h.strip():
        return h

    variante = m.registo.variante('Hymnus matutinum')
    nome = f'Hymnus {variante}' if variante else f'Day{m.dayofweek} Hymnus'
    if (nome == 'Day0 Hymnus'
            and (m.mes < 4 or re.match(r'^1\d\d-', m.monthday or ''))):
        # O domingo de inverno tem hino proprio, como as Laudes.
        nome += '1'
    return (m.especial().get(nome) or '')


def _mtv(m):
    """Porta de checkmtv: um Confessor ou Doutor leva ultima estrofe
    propria."""
    return '1' if re.search(r'C[45]', m.rule or '') else ''


# --------------------------------------------------------------------------
# Os salmos e os nocturnos
# --------------------------------------------------------------------------

def antetpsalm(pares, lang, saida):
    """Porta de antetpsalm, no ramo em que a antifona se diz por inteiro.

    Recebe linhas 'antifona;;salmos' e escreve, por ordem: a antifona, as
    chamadas de salmo, e a antifona outra vez. Uma linha sem antifona
    junta-se a anterior — e o que faz, no tempo pascal, os nove salmos
    correrem sob um 'Allelúja' so.
    """
    ultima = ''
    for linha in pares:
        ant, _, salmos = (linha or '').partition(';;')
        if ant:
            if ultima:
                saida.pop()
                saida.append(f'Ant. {ultima}')
                saida.append('\n')
            ant = re.sub(r'~?\n', ' ', ant)
            saida.append(f'Ant. {ant}')
            ultima = ant.replace('* ', '', 1)
        partes = [p for p in salmos.split(';') if p.strip()]
        for k, p in enumerate(partes):
            p = re.sub(r'[(\-]', ',', p).replace(')', '')
            if k < len(partes) - 1:
                p = '-' + p
            p = p.replace("-'", "'-")
            saida.append(f'&psalm({p})')
            saida.append('\n')
    if ultima and saida:
        saida[-1] = f'Ant. {ultima}'


def nocturn(m, num, pares, indices, saida):
    """Um nocturno: o titulo, os tres salmos e o versiculo. Porta de
    nocturn."""
    if num:
        saida.append(f"!{m.traduzir('Nocturn')} {'I' * num}")
    else:
        saida.append(f"!{m.traduzir('Ad Nocturnum')}")

    escolhidos = [pares[i] for i in indices[:-2]
                  if isinstance(i, int) and i < len(pares)]
    antetpsalm(escolhidos, m.lang, saida)

    # As duas ultimas entradas sao o versiculo: ou um par de indices na
    # lista dos salmos, ou o texto ja por extenso.
    fim = indices[-2:]
    if all(isinstance(x, int) for x in fim):
        versiculo = [pares[x] if x < len(pares) else '' for x in fim]
    else:
        versiculo = [str(x) for x in fim]
    if m.pascal:
        versiculo = [m.al.um(v, m.lang) for v in versiculo]
    saida.append('\n')
    saida.extend(versiculo)
    saida.append('\n')


def getantmatutinum(m):
    """As antifonas proprias de Matinas, com os versiculos intercalados.
    Porta de getantmatutinum.

    Um oficio proprio da nove antifonas seguidas; a lista que a hora
    precisa tem quinze linhas — tres antifonas e dois versiculos por
    nocturno. Aqui intercalam-se.
    """
    proprio, _ = m.dia.proprium('Ant Matutinum', flag=False)
    if not (proprio and proprio.strip()):
        return ''
    partes = linhas(proprio)
    if len(partes) >= 15:
        return proprio

    fora, resto = [], list(partes)
    for noc in (1, 2, 3):
        for _ in range(min(3, len(resto))):
            fora.append(resto.pop(0))
        vers, _c = m.dia.proprium(f'Nocturn {noc} Versum', flag=True)
        if vers:
            fora.extend(linhas(vers))
    return '\n'.join(fora)


def ant_matutinum_paschal(m, pares, tem_proprias):
    """No tempo pascal as antifonas de Matinas calam-se: os salmos correm
    sob um 'Allelúja' so. Porta de ant_matutinum_paschal."""
    unica = f'{m.al.palavra(m.lang)}, * ' \
            f'{m.al.palavra(m.lang).lower()}, {m.al.palavra(m.lang).lower()}.'

    if m.dayofweek or (re.search(r'Pasc6', m.tempo) ):
        if not tem_proprias or re.search(r'/C10', m.vencedor):
            pares = [re.sub(r'.*?(?=;;)', '', p) for p in pares]
            if pares:
                pares[0] = unica + pares[0]
            if (m.dayofweek and re.search(r'9 lectio', m.rule, re.I)
                    and m.rank > 3 and m.rank >= 2):
                for i in (5, 10):
                    if i < len(pares):
                        pares[i] = unica + pares[i]
        elif not re.search(r'tempora', m.vencedor, re.I):
            # Cada nocturno sob uma antifona so.
            for i in range(4):
                for k in (1, 2):
                    j = i * 5 + k
                    if j < len(pares):
                        pares[j] = re.sub(r'.*;;', ';;', pares[j])
    else:
        if (re.search(r'Pasc[1-5]', m.tempo, re.I)
                and re.search(r'Dominica', m.titulo)):
            a = linhas(m.salmos().get('Pasch0'))
            for i in range(len(pares)):
                if i < len(a):
                    pares[i] = re.sub(r'.*;;', a[i], pares[i])
            for i in range(1, len(pares)):
                pares[i] = re.sub(r'.*;;', ';;', pares[i])
    return pares


def psalmi_matutinum(m, saida):
    """Os salmos de Matinas, com os nocturnos e as licoes. Porta do ramo
    romano de psalmi_matutinum."""
    secoes = m.salmos()
    pares = linhas(secoes.get(f'Day{m.dayofweek}'))

    if m.dayofweek == 0 and re.search(r'Adv', m.tempo, re.I):
        pares = linhas(secoes.get('Adv 0 Ant Matutinum'))

    # As quartas-feiras que dizem as Laudes II nao repetem o salmo 50,
    # que ja se disse: no lugar dele parte-se o 49 em tres.
    if (m.laudes == 2 and m.dayofweek == 3
            and not re.search(r'12-24', m.vencedor, re.I)):
        pares = linhas(secoes.get('Day31'))

    nome = m.registo.variante('Psalmi Matutinum')

    if nome and (re.search(r'tempora', m.vencedor, re.I)
                 or nome in ('Nat', 'Epi')):
        if m.dayofweek == 0:
            for i in (1, 2, 3):
                v = (secoes.get(f'{nome} {i} Versum') or '').split('\n', 1)
                if len(v) == 2:
                    pares[(i - 1) * 5 + 3], pares[(i - 1) * 5 + 4] = v
            pares[13], pares[14] = pares[3], pares[4]
        else:
            i = m.i_do_dia()
            v = (secoes.get(f'{nome} {i} Versum') or '').split('\n', 1)
            if len(v) == 2:
                pares[13], pares[14] = v

    proprias = getantmatutinum(m)
    if proprias:
        pares = linhas(proprias)

    if re.search(r'Pasc[1-6]', m.tempo, re.I):
        pares = ant_matutinum_paschal(m, pares, bool(proprias))

    achado = re.search(r'Ant Matutinum ([0-9]+) special', m.rule, re.I)
    if achado:
        ind = int(achado.group(1))
        wa = (m.secoes.get(f'Ant Matutinum {ind}') or '').rstrip()
        if wa:
            alvo = 10 if (ind == 12 and re.search(r'Pasc', m.tempo, re.I)) \
                else ind
            if alvo < len(pares):
                pares[alvo] = re.sub(r'^.*?;;', f'{wa};;', pares[alvo])

    # --- tres nocturnos, nove licoes
    if m.nove_licoes():
        if 'Ant Matutinum' not in m.secoes:
            if (nome in ('Pasch', 'Asc') and m.rank < 5
                    and not re.search(r'(?:in|post).*octava.*Ascensio',
                                      m.titulo, re.I)):
                dnome = ('Dominica' if re.search(r'Dominica', m.titulo, re.I)
                         else 'Feria')
                spec = linhas(secoes.get(f'Pasch Ant {dnome}'))
                for i in (3, 4, 8, 9, 13, 14):
                    if i < len(spec) and i < len(pares):
                        pares[i] = spec[i]
            elif (re.search(r'tempora', m.vencedor, re.I)
                  and nome in ('Adv', 'Quad', 'Pasch')):
                for i in (1, 2, 3):
                    v = (secoes.get(f'{nome} {i} Versum') or '').split('\n', 1)
                    if len(v) == 2:
                        pares[(i - 1) * 5 + 3], pares[(i - 1) * 5 + 4] = v

        for n in (1, 2, 3):
            nocturn(m, n, pares, list(range((n - 1) * 5, n * 5)), saida)
            lectiones(m, n, saida)
        saida.append('\n')
        return

    # --- um nocturno, tres licoes
    vers = ''
    vn = m.i_do_dia()

    if re.search(r'Pasc[1-6]', m.tempo, re.I):
        if nome == 'Asc':
            r = m.r.setupstring(m.lang, 'Tempora/Pasc5-4.txt')
            vers = r.get(f'Nocturn {vn} Versum') or ''
        else:
            vers = secoes.get(f'Pasch {vn} Versum') or ''

    indices = [0, 1, 2]
    if not vers:
        vers = f'{_em(pares, 13)}\n{_em(pares, 14)}'
    if len(pares) > 9:
        indices += [5, 6, 7, 10, 11, 12]
    if m.mes == 12 and m.dia_do_mes == 24:
        vers = secoes.get('Nat24 Versum') or vers
    if re.search(r'Pasc[07]', m.tempo, re.I):
        vers = f'{_em(pares, 3)}\n{_em(pares, 4)}'
    if re.search(r'votive nocturn', m.rule, re.I):
        i = (m.i_do_dia() - 1) * 5
        indices = [i, i + 1, i + 2]

    indices += linhas(vers)
    nocturn(m, 0, pares, indices, saida)
    lectiones(m, 0, saida)


def _em(lista, i):
    return lista[i] if i < len(lista) else ''


# --------------------------------------------------------------------------
# As absolvicoes e as bencaos
# --------------------------------------------------------------------------

def cujus_q(m, rank):
    """Qual das seis formas da bencao 'Cujus festum colimus' se diz.

    A bencao concorda com o santo do dia: 'cujus ... ipse' para um
    homem, 'ipsa' para uma mulher, 'quorum ... ipsi' para varios. Porta
    de cujus_q.
    """
    if re.search(r'Quorum Festum', m.rule):
        return 1
    if re.search(r'C11|08-15|09-08|12-08', m.comum):
        return 4
    if re.search(r'basilic', rank, re.I):
        return -2
    if 'S. P. N. Benedicti Abbatis' in rank:
        return 5
    j = 0
    if re.search(r'(virgin|vidu[aæ]|poenitentis|pœnitentis|C6|C7)', rank, re.I):
        if not re.search(r'C[2-5]', rank):
            j += 2
    if re.search(r'(?:ss\.|bb\.|sanctorum|sociorum)', rank, re.I):
        j += 1
    return j


def absolutio_et_benedictiones(m, num):
    """A absolvicao e as tres bencoas de um nocturno. Porta de
    get_absolutio_et_benedictiones.

    Devolve uma lista: no indice 0 a absolvicao, e a seguir as bencoas,
    uma por licao.
    """
    ben_secoes = m.r.setupstring(m.lang, FICHEIRO_BENCAOS)
    abs_ = linhas(ben_secoes.get('Absolutiones'))
    eva = linhas(ben_secoes.get('Evangelica'))
    rank = m.secoes.get('Rank') or ''

    # --- nove licoes
    if num and re.search(r'9 lectiones', m.rule, re.I):
        rpn = 2
        ben = linhas(ben_secoes.get(f'Nocturn {num}'))

        if num == 3 and re.search(r'Sancti|Quad5-5', m.vencedor):
            if re.search(r'12-25', m.vencedor):
                ben = linhas(ben_secoes.get('Nocturn 3 12-25'))
            elif (re.search(r'(?:\bss?\.|\bbb?\.|sanctorum)', rank, re.I)
                  or re.search(r'C11|08-15|09-08|12-08', m.comum)):
                k = 3 + cujus_q(m, rank)
                if 0 <= k < len(ben):
                    ben[1] = ben[k]

        if num == 3 and not re.search(r'12-25', m.vencedor):
            # A primeira licao do III nocturno e sempre do Evangelho.
            if eva:
                ben[0] = eva[0]
            # E se a NONA tambem o for, a bencao dela muda.
            if re.search(r'!(?:Matt|Marc|Luc|Joannes)', lectio(m, 9) or ''):
                ev9 = linhas(ben_secoes.get('Evangelica9'))
                if ev9 and rpn < len(ben):
                    ben[rpn] = ev9[0]

        return [abs_[num - 1] if num - 1 < len(abs_) else ''] + ben

    # --- o Oficio Parvo de Nossa Senhora e o de Defuntos
    achado = re.search(r'(C1[02])', m.vencedor)
    if achado:
        from comum import subpasta
        mariae = m.r.setupstring(
            m.lang, subpasta('Commune', m.dia.version) + f'{achado.group(1)}.txt')
        return linhas(mariae.get('Benedictio'))

    # --- tres licoes
    ben = linhas(ben_secoes.get('Nocturn 3'))

    if (re.search(r'vigil|quatt|ciner', rank, re.I)
            or re.search(r'Quad[1-5]-[^0]|Quad6-1|Pasc5-1|Pasc[07]',
                         m.vencedor)):
        # Onde a primeira licao e homilia do Evangelho.
        if eva:
            ben[0] = eva[0]
    elif re.search(r'dominica', rank, re.I):
        # Num domingo de 1960 a terceira licao e a homilia.
        ev9 = linhas(ben_secoes.get('Evangelica9'))
        if ev9 and len(ben) > 2:
            ben[2] = ev9[0]
    elif ((re.search(r'Sancti', m.vencedor, re.I)
           and re.search(r'\bss?\.|b\.', rank, re.I))
          or re.search(r'C11', m.comum)):
        k = 3 + cujus_q(m, rank)
        if 0 <= k < len(ben):
            ben[1] = ben[k]
    else:
        i = m.i_do_dia()
        ben = linhas(ben_secoes.get(f'Nocturn {i}'))

    k = m.i_do_dia() - 1
    return [abs_[k] if 0 <= k < len(abs_) else ''] + ben


def lectiones(m, num, saida):
    """A absolvicao, as bencoas e as chamadas das licoes. Porta de
    lectiones."""
    a = absolutio_et_benedictiones(m, num)
    limitada = bool(re.search(r'Limit.*?Benedictio', m.rule, re.I))

    if not limitada:
        if not re.search(r'sine absolutio', m.rule, re.I):
            saida.append('$rubrica Pater secreto')
            saida.append('$Pater noster Et')
            saida.append(f'Absolutio. {a[0] if a else ""}')
            saida.append('$Amen')
    else:
        saida.append('$Pater totum secreto')
    saida.append('\n')

    rpn = 3 if not re.search(r'Lectio brevis', m.rule, re.I) else 1
    n = num or 1

    for i in range(1, rpn + 1):
        l = (n - 1) * rpn + i
        k = 0 if re.search(r'Lectio brevis sine absolutio', m.rule, re.I) else i
        if not limitada:
            saida.append(m.formula('Jube domne'))
            saida.append(f'Benedictio. {a[k] if k < len(a) else ""}')
            saida.append('$Amen')
        saida.append(f'@@LECTIO {l}@@')
        saida.append('\n')


# --------------------------------------------------------------------------
# As licoes
# --------------------------------------------------------------------------

def responsory_gloria(m, texto, num):
    """O Gloria que fecha o responsorio do fim de cada nocturno. Porta de
    responsory_gloria."""
    w = re.sub(r'&Gloria1?', '&Gloria1', texto or '')
    if ((num == 1 and re.search(r'(?:Adv1|Pasc0)-0', m.vencedor, re.I))
            or re.search(r'requiem Gloria', m.rule, re.I)):
        return w
    rpn = 3
    ultimo = (num % rpn == 0)
    penultimo = (num % rpn == rpn - 1 and m.te_deum(num + 1))
    if ultimo or penultimo:
        if not re.search(r'&Gloria', w, re.I):
            w = re.sub(r'[\s_]*$', '', w, flags=re.S)
            w = re.sub(r'(R\..*?)$', r'\1\n&Gloria1\n\1', w, count=1,
                       flags=re.M | re.S)
        return w
    return re.sub(r'.&Gloria.*', '', w, flags=re.S)


def _homilia_comemorada(m):
    """Se ha uma homilia por comemorar: a licao 1 do oficio comemorado
    abre com uma citacao evangelica."""
    l1 = m.comemorado.get('Lectio1') or ''
    return 1 if re.search(
        r'!(Matt|Mark|Marc|Luke|Luc|Joannes|John)\s+[0-9]+:[0-9]+-[0-9]+',
        l1, re.I) else 0


def lectio(m, num):
    """O texto de uma licao, com o responsorio no fim. Porta de 'lectio'.

    E a peca mais longa do original — 650 linhas — e a razao e uma so: a
    licao pode vir de seis sitios diferentes, e a ordem em que se
    procuram e toda a regra. Por ordem: o proprio do dia, a Escritura
    corrente, o Comum, e o oficio comemorado.
    """
    ltype = m.ltype

    # Num domingo a terceira licao desvia para a homilia; numa festa de
    # santo, para a legenda.
    if ltype == LT_DOMINGO and num == 3:
        num = 7
    elif num == 3 and ltype == LT_SANTORAL:
        num = 4

    w = dict(m.secoes)
    nocturno = (num - 1) // 3 + 1
    homilia = _homilia_comemorada(m)

    # --- as licoes do I Nocturno de 29 de Dezembro a 5 de Janeiro
    if nocturno == 1 and re.search(r'Lectio1 (Oct|Temp)Nat', m.rule, re.I):
        if m.mes == 12 and m.dia_do_mes < 29:
            temp = officestring(m.r, m.lang, 'Sancti/12-25.txt')
        else:
            alvo = m.registo.nat_ficheiro or \
                f'Tempora/Nat{m.dia_do_mes:02d}.txt'
            try:
                temp = officestring(m.r, m.lang, alvo)
            except (FileNotFoundError, OSError):
                temp = {}
        if m.contrair_escritura(2):
            temp['Lectio2'] = (temp.get('Lectio2') or '') + \
                (temp.get('Lectio3') or '')
        w[f'Lectio{num}'] = temp.get(f'Lectio{num}')
        w[f'Responsory{num}'] = temp.get(f'Responsory{num}')

    # --- a oitava da Epifania
    if (nocturno == 1 and re.search(r'Lectio1 tempora', m.rule, re.I)
            and 'Lectio1' in m.escritura):
        w[f'Lectio{num}'] = m.escritura.get(f'Lectio{num}')
        w[f'Responsory{num}'] = m.escritura.get(f'Responsory{num}')

    # --- a Escritura corrente das ferias, na reforma de 1960
    if (num < 3 and re.search(r'scriptura1960', m.rule, re.I)
            and f'Lectio{num}' in m.escritura):
        w[f'Lectio{num}'] = m.escritura.get(f'Lectio{num}')
        if num == 2 and (not re.search(r'feria', m.titulo, re.I)
                         or m.ficheiro_comemorado):
            corte = re.match(r'(.*?)_', w.get('Lectio2') or '', re.S)
            if corte:
                w['Lectio2'] = corte.group(1)
            w['Lectio2'] = (w.get('Lectio2') or '') + \
                (m.escritura.get('Lectio3') or '')

    texto = w.get(f'Lectio{num}')

    # Ha santos cujas licoes do I Nocturno so valem na Quaresma; fora
    # dela le-se a Escritura corrente.
    if (nocturno == 1 and re.search(r'Lectio1 Quad', m.rule, re.I)
            and not re.search(r'Quad(\d|p3-[3456])', m.tempo, re.I)):
        texto = ''

    # --- o Comum, quando o oficio E o do Comum
    de_onde = 'proprio'
    if not texto and (
            (re.match(r'ex', m.tipo_comum or '', re.I)
             and re.search(r'Tempora', m.comum, re.I) and m.rank > 3)
            or (nocturno == 1 and homilia == 1
                and f'Lectio{num}' in m.secoes_comum
                and not re.search(r'in 1 Nocturno', m.rule, re.I))):
        w = dict(m.secoes_comum)
        de_onde = 'comum'
        texto = w.get(f'Lectio{num}')

    if (not texto and re.search(r'sancti', m.vencedor, re.I)
            and re.match(r'C', Path(m.comum).name if m.comum else '')
            and (re.match(r'ex', m.tipo_comum or '', re.I) and m.rank > 3
                 or re.search(rf'in {nocturno} Nocturno Lectiones ex',
                              m.rule, re.I))):
        com = dict(m.secoes_comum)
        chave = f'Lectio{num}'
        achado = re.search(
            rf'in {nocturno} Nocturno Lectiones ex (Commune|C\d+[a-z]*) '
            rf'in (\d+) loco', m.rule, re.I)
        if achado:
            from comum import subpasta
            if achado.group(1) != 'Commune':
                com = m.r.setupstring(
                    m.lang, subpasta('Commune', m.dia.version)
                    + f'{achado.group(1)}.txt')
            loco = int(achado.group(2))
            if loco > 1:
                chave += f' in {loco} loco'
            texto = com.get(chave)
        elif chave in com:
            texto = com.get(chave)
        if texto and m.contrair_escritura(num):
            texto += com.get(chave.replace('Lectio2', 'Lectio3')) or ''

    # --- a Escritura corrente, para o I Nocturno
    if not texto and num < 4 and f'Lectio{num}' in m.escritura:
        w = dict(m.escritura)
        de_onde = 'escritura'
        texto = w.get(f'Lectio{num}')
    elif (not texto and num == 4 and f'Lectio{num}' in m.comemorado):
        # A terceira licao desviada para a legenda do santo comemorado.
        w = dict(m.comemorado)
        de_onde = 'comemorado'
        texto = w.get(f'Lectio{num}')

    if m.contrair_escritura(num):
        corte = re.match(r'(.*?)_', texto or '', re.S)
        if corte:
            texto = corte.group(1)
        texto = (texto or '') + (w.get('Lectio3') or '')

    if not texto and f'Lectio{num}' in m.secoes_comum:
        c = dict(m.secoes_comum)
        texto = c.get(f'Lectio{num}')
        if m.contrair_escritura(num):
            texto = (texto or '') + (c.get('Lectio3') or '')

    if re.search(rf'Special Lectio {num}', m.dia.regra_do_comum or ''):
        from comum import subpasta
        mariae = m.r.setupstring(
            m.lang, subpasta('Commune', m.dia.version) + 'C10.txt')
        texto = mariae.get(_nome_da_licao_de_C10(m)) or texto

    texto = _licao_do_comemorado(m, num, texto, w, homilia)

    # A legenda contraida de uma festa de III classe.
    if ltype == LT_SANTORAL and num == 4:
        if 'Lectio94' in m.secoes:
            texto = m.secoes.get('Lectio94')
        else:
            i = 5
            while i < 7:
                seguinte = m.secoes.get(f'Lectio{i}')
                if not seguinte or '!' in seguinte:
                    break
                corte = re.match(r'(.*?)_', texto or '', re.S)
                if corte:
                    texto = corte.group(1)
                texto = (texto or '') + seguinte
                i += 1

    if (ltype or (re.search(r'Sancti', m.vencedor, re.I) and m.rank < 2)) \
            and num > 2:
        num = 3

    texto = (texto or '').replace('¶', '')
    texto = re.sub(r'&teDeum\n*', '', texto)

    if not (re.search(r'Limit.*?Benedictio', m.rule, re.I)
            or 'In Finem Lectio' in m.secoes):
        texto = re.sub(r'~?\s*$', '\n$Tu autem', texto, flags=re.S)

    if not m.te_deum(num):
        texto += '\n_\n' + _responsorio(m, num, w)

    texto = re.sub(r'^_', '', texto)

    # A inicial: o texto de uma licao abre com 'v.', como um salmo.
    if not re.search(r'^!', texto, re.M):
        texto = re.sub(r'^(?=[^\W\d_])', 'v. ', texto)
    elif not re.search(r'^\d', texto, re.M):
        texto = re.sub(r'^!.*?\n(?=[^\W\d_])', lambda x: x.group(0) + 'v. ',
                       texto, flags=re.M)

    rotulo = m.traduzir('Lectio')
    if '%s' not in rotulo:
        rotulo += ' %s'
    cabeca = '' if re.search(r'Limit.*?Benedictio', m.rule, re.I) else '_\n'
    texto = cabeca + (rotulo % num) + '\n' + texto

    texto = _numerar_versiculos(texto)
    if m.te_deum(num):
        texto += '\n_\n&teDeum\n'
    return texto


def _nome_da_licao_de_C10(m):
    """Porta de getC10readingname: a licao do sabado de Nossa Senhora
    muda com o mes."""
    return f'Lectio M{m.mes:02d}'


def _responsorio(m, num, w):
    """O responsorio que fecha a licao. Porta do ramo de 'add responsory'
    dentro de lectio."""
    na = num
    if (re.search(r'tempora', m.vencedor, re.I) and m.dayofweek == 0
            and re.search(r'(Adv|Quad)', m.tempo, re.I) and na == 3):
        na = 9
    if m.contrair_escritura(num, resp=True):
        na = 3

    s = ''
    if f'Responsory{na} 1960' in w:
        s = w.get(f'Responsory{na} 1960')
    elif (re.search(r'Responsory Feria', m.rule, re.I)
          or (re.search(r'scriptura1960', m.rule, re.I)
              and f'Responsory{na}' not in m.secoes)):
        if f'Responsory{na}' in m.escritura:
            s = m.escritura.get(f'Responsory{na}')
        else:
            s = m.escritura.get(f'Lectio{na}') or ''
            corte = re.search(r'\n_(.*)', s, re.S)
            s = f'_{corte.group(1)}' if corte else ''
        if not s and f'Responsory{na} 1960' in m.escritura:
            s = m.escritura.get(f'Responsory{na} 1960')
    else:
        if f'Responsory{na}' in w:
            s = w.get(f'Responsory{na}')
        elif f'Responsory{na}' in m.secoes_comum:
            s = m.secoes_comum.get(f'Responsory{na}')
        if f'Responsory{na}' in m.secoes:
            s = ''

    if not s:
        if f'Responsory{na}' in m.secoes:
            s = m.secoes.get(f'Responsory{na}')
        if not s and f'Responsory{na}' in m.secoes_comum:
            s = m.secoes_comum.get(f'Responsory{na}')

    s = s or ''
    if m.pascal:
        s = _alleluia_no_responsorio(m, s)
    return responsory_gloria(m, s, num)


def _alleluia_no_responsorio(m, s):
    """Porta de matins_lectio_responsory_alleluia."""
    s = re.sub(r'\s*~\s*', ' ', s, flags=re.S)
    partes = s.split('\n')
    for i in (1, 3, len(partes) - 1):
        if 0 <= i < len(partes):
            partes[i] = m.al.um(partes[i], m.lang)
    return '\n'.join(partes)


def _licao_do_comemorado(m, num, texto, w, homilia):
    """A ultima licao pode ser a do oficio comemorado.

    Nas rubricas de 1960 isto so acontece numa festa de III classe cuja
    terceira licao ja se desviou para a legenda. Porta do ramo de 1960 do
    grande bloco 'look for commemoratio 9'.
    """
    if not ((m.ltype == LT_SANTORAL
             or (re.search(r'Sancti', m.vencedor, re.I) and m.rank < 2))
            and re.search(r'Sancti', m.vencedor, re.I) and num == 4):
        return texto

    if 'Lectio94' in m.secoes:
        return m.secoes.get('Lectio94')
    if 'Lectio93' in m.secoes:
        return m.secoes.get('Lectio93')
    return texto


NUMERO_DE_VERSICULO = re.compile(r'^([0-9]+)\s+(.*)', re.S)


def _numerar_versiculos(texto):
    """Porta do ciclo final de lectio: cada versiculo abre com o seu
    numero, e o primeiro com 'v.' no lugar dele."""
    fora = []
    inicial = False
    for l in re.split(r'\n+', texto):
        achado = NUMERO_DE_VERSICULO.match(l)
        if achado:
            # O versiculo abre com maiuscula: no ficheiro ele vem escrito
            # como continuacao da frase anterior, mas na pagina cada
            # versiculo e uma linha por si.
            resto = achado.group(2)
            resto = resto[:1].upper() + resto[1:]
            marca = f'\n{achado.group(1)}'
            if inicial:
                marca = '\nv. '
                inicial = False
            fora.append(f'{marca} {resto}')
        else:
            fora.append(f'\n{l}')
    return ''.join(fora)
