"""
A salmodia das horas menores: que antifona e que salmos, em que dia.

Prima, Terca, Sexta, Noa e Completas tomam os salmos do Saltério, pelo dia
da semana. O ficheiro 'Psalterium/Psalmi/Psalmi minor.txt' guarda-os assim:

    [Sexta]
    Feria III = Suscepísti me, Dómine: * et confirmásti me in conspéctu tuo.
    40, 41(2-6), 41(7-12)

Duas linhas por dia: a antifona e a lista. '41(2-6)' quer dizer o salmo 41
do versiculo 2 ao 6; '18(2-'7b')' vai ate a primeira metade do versiculo 7.

Porta do ramo romano de psalmi_minor e de antetpsalm, em
specials/psalmi.pl. Os ramos tridentino e monastico ficam de fora, pelo
mesmo motivo de sempre: o nosso breviario e o romano de 1960.

O QUE AINDA DEPENDE DO CALENDARIO, e esta assinalado no codigo:
  - a troca de antifona no tempo do Advento e da Pascoa (gettempora)
  - as antifonas proprias das horas nas festas de I classe (getanthoras)
Nenhuma das duas se aplica a uma festa de III classe fora desses tempos,
que e o caso ja composto.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proprio import DO_COMUM

sys.path.insert(0, str(Path(__file__).parent))

FICHEIRO = 'Psalterium/Psalmi/Psalmi minor.txt'

DIAS = ['Dominica', 'Feria II', 'Feria III', 'Feria IV',
        'Feria V', 'Feria VI', 'Sabbato']

PSALMI_DOMINICA = re.compile(r'Psalmi\s*(?:minores)*\s*Dominica', re.I)
# Nas horas MAIORES a regra tem de dizer 'Psalmi Dominica' por extenso:
# 'Psalmi minores Dominica' fala so das horas menores, e no Triduo Sacro e
# essa que esta escrita. Sem a distincao, as Laudes do Triduo comecavam
# pelo salmo 92 em vez do 50.
PSALMI_DOMINICA_MAIOR = re.compile(r'Psalmi Dominica', re.I)
PSALMI_EX_PSALTERIO = re.compile(r'Psalmi\s*(?:minores)*\s*ex Psalterio', re.I)


def indice_do_dia(hora, dayofweek, dia=None):
    """Que par de linhas da seccao da hora se usa.

    Duas linhas por dia da semana, e por isso o indice e o dobro. As
    excepcoes sao as do original.
    """
    i = 2 * dayofweek
    rule = dia.rule if dia else ''
    # A regra do COMUM, e nao a do proprio. E dela que vem, por exemplo,
    # 'Psalmi Dominica' no Comum de Nossa Senhora, que manda rezar as
    # Completas com os salmos de domingo em qualquer dia da semana.
    communerule = dia.regra_do_comum if dia else ''
    rank = dia.rank if dia else 0
    vencedor = dia.proprio if dia else ''

    # Completas de sabado quando o dia seguinte manda oficio de domingo.
    def sabado_de_domingo():
        return (hora == 'Completorium' and dayofweek == 6
                and dia is not None
                and re.search(r'Dominica', dia.secoes.get('Rank') or '', re.I))

    if sabado_de_domingo():
        i = 12

    if (PSALMI_DOMINICA.search(rule)
            or (PSALMI_DOMINICA.search(communerule)
                and not PSALMI_EX_PSALTERIO.search(rule))):
        i = 0

    # A regra de 1960: numa festa abaixo de I classe as horas menores
    # voltam ao saltério do dia da semana. E a 'Cum nostra hac aetate'.
    if (re.search(r'horas1960 feria', rule, re.I)
            or (re.search(r'Sancti', vencedor, re.I) and rank < 5)
            or (re.search(r'Sancti|Nat[23]', vencedor, re.I) and rank < 6
                and hora != 'Completorium')):
        i = 2 * dayofweek

    if sabado_de_domingo():
        i = 12
    return i


def salmodia_menor(r, hora, dayofweek, lang, dia=None, laudes=1,
                   vespera=0, avisos=None):
    """Devolve (antifona, [argumentos de &psalm]).

    Os argumentos vem na forma que a funcao '&psalm' espera — '41,2,6' —
    ja com o sinal '-' que junta salmos sob um so Gloria.
    """
    avisos = avisos if avisos is not None else []
    secoes = r.setupstring(lang, FICHEIRO)
    linhas = (secoes.get(hora) or '').split('\n')
    if not linhas:
        avisos.append(f'{FICHEIRO} nao tem seccao [{hora}]')
        return '', []

    i = indice_do_dia(hora, dayofweek, dia)
    if i + 1 >= len(linhas):
        avisos.append(f'[{hora}] nao tem linha {i} — dia da semana {dayofweek}')
        return '', []

    ant = linhas[i].strip()
    salmos = linhas[i + 1].strip()

    # Nas Laudes II o salmo 117 da Prima cede o lugar ao 53. Quais Laudes
    # se rezam e coisa do dia, e vem do Ordo.
    rule = dia.rule if dia else ''
    if dia is not None and dia.registo is not None and dia.registo.laudes:
        try:
            laudes = int(dia.registo.laudes)
        except ValueError:
            pass
    if (('117' in salmos and laudes == 2) or re.search(r'Prima=53', rule, re.I)):
        salmos = salmos.replace('117', '53')

    if hora == 'Completorium' and dia is not None:
        rank_do_vencedor = (dia.secoes.get('Rank') or '')
        e_do_tempo = bool(re.search(r'tempora', dia.proprio, re.I))
        communerule = dia.regra_do_comum

        if (e_do_tempo and dayofweek > 0
                and re.search(r'Dominica', rank_do_vencedor, re.I)
                and dia.rank < 6):
            # Feria com oficio de domingo abaixo de I classe: fica o
            # saltério do dia da semana.
            pass
        elif ((PSALMI_DOMINICA.search(rule)
               or PSALMI_DOMINICA.search(communerule))
              and dia.rank >= 6):
            # As Completas de uma festa de I classe rezam-se com os
            # salmos de domingo, seja que dia for. E o que faz as
            # Completas do sabado antes de Pentecostes serem as de
            # domingo, e nao as de sabado.
            ant, salmos = linhas[0].strip(), linhas[1].strip()

        proprio = (dia.secoes.get(f'Ant Completorium{vespera}')
                   or dia.secoes.get('Ant Completorium'))
        if proprio and proprio.strip():
            ant = proprio.strip()

    ant = antifona_do_tempo(secoes, hora, dayofweek, dia, ant, avisos)

    # A linha traz 'Feria III = <antifona>'; o rotulo do dia sai fora.
    ant = re.sub(r'^.*?=\s*', '', ant)

    if hora != 'Completorium' and dia is not None:
        texto, _ = dia.proprium(f'Ant {hora}')
        if not (texto and texto.strip()):
            if (not PSALMI_EX_PSALTERIO.search(rule)
                    and not (dia.rank < 6 and dayofweek > 0)):
                texto = antifonas_das_horas(dia, hora)
        if texto and texto.strip():
            ant = texto.strip()

    if dia is not None and re.search(r'Minores sine Antiphona', dia.rule, re.I):
        ant = ''

    if ';;' in ant:
        ant = ant.split(';;')[0]

    # Na Prima ha um salmo a mais, entre colchetes, que as rubricas de
    # 1960 mandam omitir sempre.
    if hora == 'Prima':
        salmos = re.sub(r',?\[\d+\]', '', salmos)
        # E numa festa, o primeiro salmo da Prima e o 53, nao o do dia.
        if e_festa(dia, dayofweek):
            salmos = re.sub(r'^\s*[^,]+', '53', salmos, count=1)
        # O 'Quicumque' — o Símbolo de Santo Atanásio. Nas rubricas de
        # 1960 diz-se uma vez por ano, no domingo da Santíssima Trindade.
        if diz_se_o_quicumque(dia, dayofweek):
            salmos += ',234'

    return ant.strip(), chamadas_de_salmo(salmos)


def diz_se_o_quicumque(dia, dayofweek):
    """Se a Prima leva o Símbolo de Santo Atanásio.

    Nas rubricas antigas dizia-se em muitos domingos. A reforma de 1960
    reduziu-o a **um** por ano: o domingo da Santíssima Trindade. O
    original guarda essa redução na condicao que exige 'Pent01' quando a
    versao e de 1960.
    """
    if dia is None or dia.registo is None:
        return False
    tempo = dia.registo.tempo or ''
    return (dayofweek == 0
            and bool(re.search(r'Pent01', tempo, re.I))
            and not re.search(r'Non dicitur Quicumque', dia.rule, re.I))


def e_festa(dia, dayofweek):
    """Porta do 'feastflag' de psalmi_minor.

    Diz se o dia se reza como festa para efeito da salmodia. Nas rubricas
    de 1960 so as festas de I classe contam — abaixo disso volta-se ao
    Saltério do dia da semana.
    """
    if dia is None:
        return False
    rule, communerule = dia.rule, dia.regra_do_comum
    festa = ((PSALMI_DOMINICA.search(rule)
              or PSALMI_DOMINICA.search(communerule))
             and not PSALMI_EX_PSALTERIO.search(rule)
             and not (dia.rank < 6 and dayofweek > 0))
    if dia.rank < 6:
        festa = False
    # Um domingo nao e festa para este efeito — salvo no Natal e na
    # oitava da Ascensao.
    if (re.search(r'Dominica', dia.secoes.get('Rank') or '', re.I)
            and not re.search(r'Nat|Pasc6',
                              (dia.registo.tempo if dia.registo else ''), re.I)):
        festa = False
    return bool(festa)


# Que antifona de Laudes serve cada hora menor. Prima toma a primeira,
# Terca a segunda, Sexta a terceira, Noa a quinta — a quarta nao se usa.
ANTIFONA_DE_LAUDES = {'Prima': 0, 'Tertia': 1, 'Sexta': 2, 'Nona': 4}


def antifonas_das_horas(dia, hora):
    """Porta de getanthoras.

    Nas festas de I classe, as horas menores nao dizem a antifona do
    Saltério: dizem as de Laudes, uma para cada hora. E o que a regra
    'Antiphonas horas' manda, e e o que faz o dia de Natal ter, a Sexta,
    'Angelus ad pastóres ait' em vez do 'Allelúia' do Saltério.

    Nas rubricas de 1960 isto so vale para as festas de I classe: abaixo
    disso, volta-se ao Saltério.
    """
    if not (re.search(r'Antiphonas horas', dia.rule, re.I)
            or re.search(r'Antiphonas horas', dia.regra_do_comum, re.I)):
        return ''
    if dia.rank < 6:
        return ''

    laudes = dia.secoes.get('Ant Laudes') or ''
    if not laudes.strip() and re.match(r'ex', dia.tipo_comum or '', re.I):
        laudes = dia.secoes_comum.get('Ant Laudes') or ''

    linhas = [l for l in laudes.split('\n') if l.strip()]
    i = ANTIFONA_DE_LAUDES.get(hora, 4)
    # Menos de quatro antifonas quer dizer que nao sao as cinco de Laudes.
    return linhas[i] if len(linhas) > 3 and i < len(linhas) else ''


# Em que linha da seccao do tempo esta a antifona de cada hora. Sao os
# indices do original, e o das Completas nao existe — so o tempo pascal
# lhe da uma, e essa e a primeira da lista.
LINHA_DA_HORA = {'Prima': 0, 'Tertia': 1, 'Sexta': 2, 'Nona': 4}


def antifona_do_tempo(secoes, hora, dayofweek, dia, ant, avisos):
    """No Advento e na Pascoa a antifona das horas menores nao e a do
    Saltério: e a do tempo.

    Na oitava da Pascoa, por exemplo, todas as horas se dizem sob uma so
    antifona — 'Allelúia, allelúia, allelúia' — e ate as Completas, que
    fora dela nunca trocam de antifona.
    """
    if dia is None or dia.registo is None:
        return ant
    reg = dia.registo
    if not (re.search(r'tempora', dia.proprio, re.I)
            or re.search(r'pasc', reg.tempo or '', re.I)):
        return ant

    nome = reg.tempora_salmos or ''
    linha = LINHA_DA_HORA.get(hora, -1)

    if nome == 'Adv':
        # No Advento cada semana tem a sua antifona, e a partir de 17 de
        # Dezembro cada dia tem a sua.
        nome = reg.tempo or ''
        dia_do_mes = int(reg.data.split('-')[1])
        if 16 < dia_do_mes < 24 and dayofweek:
            nome = f'Adv4{dayofweek + 1}'
    elif nome == 'Pasch' and (not re.search(r'Pasc7', reg.tempo or '', re.I)
                              or hora == 'Completorium'):
        linha = 0

    if not nome or linha < 0:
        return ant

    linhas = (secoes.get(nome) or '').split('\n')
    if linha >= len(linhas) or not linhas[linha].strip():
        avisos.append(f'[{nome}] nao tem antifona na linha {linha}')
        return ant
    return linhas[linha].strip()


FICHEIRO_MAIOR = 'Psalterium/Psalmi/Psalmi major.txt'


def salmodia_maior(r, hora, dayofweek, lang, dia, laudes=1, vespera=0,
                   avisos=None):
    """A salmodia de Laudes e Vésperas: cinco antífonas, cinco salmos.

    Ao contrário das horas menores, aqui cada salmo tem a sua antífona. O
    Saltério guarda-as emparelhadas:

        [Day0 Laudes1]
        Allelúja, * Dóminus regnávit...;;92
        Jubiláte * Deo omnis terra, allelúja.;;99

    Antes do ';;' a antífona, depois o número do salmo. Numa festa as
    antífonas vêm do próprio ou do Comum, e então os salmos ficam os do
    Saltério — salvo quando a própria antífona traz os seus.

    Porta do ramo romano de psalmi_major, em specials/psalmi.pl.

    Devolve [(antifona, [argumentos de &psalm])], uma entrada por salmo.
    """
    avisos = avisos if avisos is not None else []
    secoes = r.setupstring(lang, FICHEIRO_MAIOR)

    nome = f'{hora}{laudes}' if hora == 'Laudes' else hora
    do_salterio = [l for l in (secoes.get(f'Day{dayofweek} {nome}') or ''
                               ).split('\n') if l.strip()]

    antifonas, do_comum = _antifonas_maiores(r, hora, vespera, dia, lang)
    if not antifonas:
        antifonas = _antifonas_do_advento(secoes, hora, dayofweek, dia)

    # A regra 'Psalmi Dominica' manda rezar os salmos de domingo — e nas
    # Laudes sempre os do primeiro esquema.
    rule = dia.rule if dia else ''
    # ATENCAO: nas horas maiores o original le a regra do FICHEIRO do
    # Comum, e nao a regra que a precedencia guardou. Sao coisas
    # diferentes, e nas horas menores usa-se a outra. E o que faz Santa
    # Ines rezar os salmos de domingo em Laudes.
    #
    # NOTA para quem retomar: tentei restringir isto aos Comuns a serio
    # ('Commune/C6-1'), excluindo os oficios de santo que servem de Comum
    # ('vide Sancti/01-01'). Ganhou cinco dias nas Vesperas e perdeu cinco
    # nas Laudes — troca nula. Nao e por aqui: o problema das Vesperas e
    # outro. Ver a nota em decisoes.md.
    communerule = (dia.secoes_comum.get('Rule') or '') if dia else ''
    de_domingo = ((PSALMI_DOMINICA_MAIOR.search(rule)
                   or PSALMI_DOMINICA_MAIOR.search(communerule))
                  and not re.search(r'Psalmi Feria', rule, re.I)
                  and not (antifonas and re.search(r';;\s*\d+', antifonas[0])))
    # ATENÇÃO: os salmos de domingo só entram quando o dia TEM antífonas
    # próprias. Sem elas fica o par do Saltério — antífona e salmo do dia
    # da semana — tal e qual. No original isto sai de o Day0 só ser usado
    # dentro do ciclo que casa antífona com salmo, e esse ciclo não corre
    # quando não há antífonas.
    if de_domingo and antifonas:
        h = 'Laudes1' if hora == 'Laudes' else hora
        pares = [l for l in (secoes.get(f'Day0 {h}') or '').split('\n')
                 if l.strip()]
    else:
        pares = do_salterio

    if not pares:
        avisos.append(f'{FICHEIRO_MAIOR} nao tem [Day{dayofweek} {nome}]')
        return []

    fora = []
    for i in range(5):
        salmo = ''
        trocado_por_regra = False
        if i < len(pares) and ';;' in pares[i]:
            salmo = pares[i].split(';;', 1)[1].strip()

        # O quinto salmo das Vésperas pode ser trocado por regra.
        if i == 4 and hora == 'Vespera' and not re.search(r'no Psalm5', rule,
                                                          re.I):
            # A regra do COMUM so vale se as antifonas tambem vierem de
            # la. E o '$c eq 4' do original: sem esta condicao, o quinto
            # salmo das Vesperas saía trocado em setenta dias do ano.
            do_c = communerule if do_comum else ''
            m = None
            if vespera == 3:
                m = (re.search(r'Psalm5 Vespera3=(\d+)', rule, re.I)
                     or re.search(r'Psalm5 Vespera3=(\d+)', do_c, re.I))
            if not m:
                m = (re.search(r'Psalm5 Vespera=(\d+)', rule, re.I)
                     or re.search(r'Psalm5 Vespera=(\d+)', do_c, re.I))
            if m:
                salmo = m.group(1)
                trocado_por_regra = True

        if antifonas:
            if i >= len(antifonas):
                break
            ant = antifonas[i]
            # Uma antifona propria pode trazer os seus proprios salmos —
            # mas nao quando a REGRA ja trocou o salmo. E o 'aflag' do
            # original: no domingo da Santissima Trindade a antifona traz
            # ';;116' e a regra manda 113, e quem manda e a regra.
            if ';;' in ant:
                cabeca, cauda = ant.split(';;', 1)
                if (re.match(r'\s*[\d;]+\s*$', cauda)
                        and not trocado_por_regra):
                    salmo = cauda.strip()
                ant = cabeca
        else:
            ant = pares[i].split(';;', 1)[0] if i < len(pares) else ''

        if not salmo:
            continue
        fora.append((ant.strip(), chamadas_de_salmo(salmo.replace(';', ','))))

    fora = _uma_so_antifona_pascal(fora, hora, dia, antifonas)
    return fora


def _antifonas_do_advento(secoes, hora, dayofweek, dia):
    """De 17 a 23 de Dezembro as Laudes tem antifonas suas.

    Sao os sete dias que preparam o Natal, e o Saltério guarda-lhes uma
    terceira serie — '[Day4 Laudes3]' — a par das duas de sempre. So nas
    ferias: o domingo tem as suas.

    Porta do bloco de Advento de psalmi_major.
    """
    if hora != 'Laudes' or not dayofweek:
        return []
    if dia is None or dia.registo is None:
        return []
    mes, dia_do_mes, _ = (int(x) for x in dia.registo.data.split('-'))
    if mes != 12 or not (16 < dia_do_mes < 24):
        return []
    return [l for l in (secoes.get(f'Day{dayofweek} Laudes3') or ''
                        ).split('\n') if l.strip()]


def _uma_so_antifona_pascal(fora, hora, dia, antifonas):
    """No tempo pascal os cinco salmos dizem-se sob UMA antifona.

    'Allelúia, * allelúia, allelúia' cobre a salmodia inteira, e as
    antifonas do dia da semana calam-se. So se o dia nao tiver antifonas
    proprias: uma festa com antifonas suas mantem-nas.

    Porta do ramo 'alleluia_required' de psalmi_major.
    """
    if not fora or dia is None or dia.registo is None:
        return fora
    if not re.search(r'Pasc', dia.registo.tempo or '', re.I):
        return fora
    if antifonas:
        return fora
    if re.match(r'ex', dia.tipo_comum or '', re.I):
        return fora

    unica = 'Allelúja, * allelúja, allelúja.'
    return [(unica if i == 0 else '', chamadas)
            for i, (_, chamadas) in enumerate(fora)]


def _antifonas_maiores(r, hora, vespera, dia, lang):
    """As cinco antifonas de Laudes ou Vesperas, quando o dia tem as suas.

    Devolve (lista, veio_do_comum). A segunda importa: certas regras do
    Comum — a troca do quinto salmo das Vesperas — so valem quando foi de
    la que as antifonas vieram.
    """
    if dia is None:
        return [], False
    do_comum = False
    texto = ''
    if hora == 'Vespera' and vespera == 3:
        texto = dia.secoes.get('Ant Vespera 3') or ''
        # So se vai buscar ao Comum quando ele e 'ex' — quando o oficio E
        # o do Comum. Com 'vide' o Comum e so uma fonte, e as antifonas
        # ficam as do Saltério. Sem esta condicao, a Sexta-feira depois do
        # Natal ia buscar as antifonas do dia 1 de Janeiro.
        if (not texto and not dia.secoes.get('Ant Vespera')
                and re.match(r'ex', dia.tipo_comum or '', re.I)):
            t, proc = dia.proprium('Ant Vespera 3', flag=True)
            texto = t or ''
            do_comum = bool(texto) and proc == DO_COMUM
    if not texto:
        texto = dia.secoes.get(f'Ant {hora}') or ''
        do_comum = False
    if not texto and re.match(r'ex', dia.tipo_comum or '', re.I):
        t, proc = dia.proprium(f'Ant {hora}', flag=True)
        texto = t or ''
        do_comum = bool(texto) and proc == DO_COMUM
    return [l for l in texto.split('\n') if l.strip()], do_comum


def chamadas_de_salmo(salmos):
    """'40, 41(2-6), 41(7-12)' -> ['-40', '-41,2,6', '41,7,12'].

    Porta do miolo de antetpsalm. O '-' a frente diz 'este salmo junta-se
    ao seguinte sob um so Gloria'; no rito romano nao produz efeito, mas
    escreve-se na mesma, porque e o que o original escreve e e o que
    permitira gerar o monastico sem mexer aqui.
    """
    lista = [p.strip() for p in salmos.split(',') if p.strip()]

    fora = []
    for k, p in enumerate(lista):
        p = re.sub(r'[(\-]', ',', p)
        p = p.replace(')', '')
        if k < len(lista) - 1:
            p = '-' + p
        p = p.replace("-'", "'-")
        fora.append(p)
    return fora


def antifona_repetida(ant):
    """A antifona repete-se no fim, e ai sem o asterisco.

    O asterisco marca onde ela se corta quando so se entoa. Na repeticao
    diz-se por inteiro, e por isso o sinal nao faz falta.
    """
    return ant.replace('* ', '', 1)
