"""
Compoe Laudes e Vesperas — as duas horas maiores do dia.

Diferem das menores em tudo o que importa:

  cinco antifonas   uma para cada salmo, e nao uma para os tres
  o cantico         o Benedictus em Laudes, o Magnificat em Vesperas,
                    cada um com a sua antifona propria
  as comemoracoes   os oficios que o dia venceu mas nao apaga

Porta do ramo romano de psalmi_major, capitulum_major e getantvers.

uso:
    python compor_maiores.py --hora Laudes --data 08-04-2026
    python compor_maiores.py --hora Vespera --data 12-25-2026 --edicao latina
"""

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import ler_arquivo
from resolver import Resolvedor
from funcoes import Funcoes
from proprio import Dia
from salmodia import salmodia_maior, antifona_repetida
import alleluia
import compor
import compor_menores
from comum import subpasta

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ
REPO = compor.REPO
VERSAO = compor.VERSAO

HORAS = ('Laudes', 'Vespera')
ESPECIAL_MAIOR = 'Psalterium/Special/Major Special.txt'

# O cantico de cada hora, e o seu numero de salmo.
CANTICO = {'Laudes': ('Canticum: Benedictus', '231'),
           'Vespera': ('Canticum: Magnificat', '232')}


def montar(hora, data, com_vernaculo=True):
    if hora not in HORAS:
        raise SystemExit(f'hora desconhecida: {hora}. Uma de {HORAS}')

    ordo = compor.ordo_do_ano(data)
    registo = ordo.dia(data, hora)
    if registo is None:
        raise SystemExit(f'o Ordo nao tem {data}')

    dow = (int(registo.dayofweek) if registo.dayofweek
           else compor.DIAS.index(compor.dia_da_semana(data)))
    vespera = int(registo.vespera or 0)
    laudes = int(registo.laudes or 1)

    ctx = compor.contexto_do_dia(hora, dow, registo, data)
    r = Resolvedor(REPO, ctx)
    # Nas PRIMEIRAS Vesperas o oficio ja e o de amanha, e o ficheiro do
    # mes liturgico que se lhe sobrepoe tambem: no sabado 1 de Agosto o
    # domingo que se reza esta na I semana de Agosto, e nao no mes que a
    # data de hoje daria — que em 1 de Agosto ainda nem existe.
    mes_do_vencedor = registo.mes_vencedor
    if vespera == 1:
        mes_do_vencedor = _mes_do_ficheiro(registo, registo.vencedor, 1)
    dia = Dia(r, registo.vencedor, VERSAO, registo=registo,
              ficheiro_do_mes=mes_do_vencedor)
    dia_ver = (Dia(r, registo.vencedor, VERSAO, lang='Portugues',
                   registo=registo, ficheiro_do_mes=mes_do_vencedor)
               if com_vernaculo else None)
    f = Funcoes(r, compor.estado_do_dia(hora, dow, registo, dia))

    pascal = alleluia.e_tempo_pascal(registo.tempo)
    # Da Septuagesima ao sabado santo apaga-se todo o alleluia que o
    # texto traga escrito — mesmo o que vem do Comum.
    suprime = alleluia.suprime_se(registo.tempo, hora, dow, vespera)
    al = alleluia.Alleluia(r)

    def texto(lang, bruto):
        saida = bruto
        for _ in range(6):
            novo = f.expandir(r.expandir_formulas(saida, lang), lang)
            if novo == saida:
                break
            saida = novo
        saida = '\n'.join(l for l in saida.split('\n')
                          if not l.startswith('#'))
        return alleluia.tempo(saida, pascal, suprime)

    def par(bruto):
        return (texto('Latin', bruto),
                texto('Portugues', bruto) if com_vernaculo else '')

    especial = dia.secoes.get(f'Special {hora}') or ''
    if especial.strip():
        esqueleto = compor.esqueleto_especial(especial)
    else:
        esqueleto = ler_arquivo(
            REPO / f'web/www/horas/Ordinarium/{hora}.txt',
            ctx).get('__preambulo', [])

    pecas = []
    bloco_aberto = ['']
    a_calar = [False]
    # O '#Prelude' do original: a rubrica que o oficio do dia poe antes
    # de tudo o resto.
    abertura = compor.prelude(dia, hora)
    if abertura:
        pecas.append(compor.Peca(
            'rubrica', 'Prelude', texto('Latin', abertura),
            texto('Portugues', compor.prelude(dia_ver, hora))
            if com_vernaculo and dia_ver is not None else ''))


    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            a_calar[0] = compor.omitir_bloco(dia.rule, nome, hora)
            if a_calar[0]:
                # Na oitava da Pascoa nao ha capitulo: no lugar dele
                # diz-se o versiculo 'Hæc dies'.
                if ('Capitulum' in nome
                        and compor.versiculo_no_lugar(dia.rule, hora)):
                    p = compor_menores._versiculo_em_lugar_do_capitulo(
                        r, texto, dia, dia_ver, com_vernaculo)
                    if p:
                        pecas.append(p)
                continue

            # A 25 de Abril, nas Ladainhas Maiores, a Conclusao das
            # Laudes cede o lugar a Ladainha de Todos os Santos.
            if (nome == 'Conclusio' and hora == 'Laudes'
                    and _dizem_se_as_ladainhas(registo, dia)):
                p = _litania(r, f, texto, com_vernaculo)
                if p:
                    pecas.append(p)
                a_calar[0] = True
                continue

            especial_da_conclusao = (compor.conclusao_especial(dia)
                                     if nome == 'Conclusio' else '')
            if especial_da_conclusao:
                lat = texto('Latin', especial_da_conclusao)
                ver = (texto('Portugues',
                             compor.conclusao_especial(dia_ver) or '')
                       if com_vernaculo and dia_ver else '')
                if lat.strip():
                    pecas.append(compor.Peca(
                        'texto', nome, lat, ver,
                        r.titulo(nome, 'Latin'),
                        r.titulo(nome, 'Portugues') if com_vernaculo else ''))
                a_calar[0] = True
                continue

            if nome == 'Psalmi':
                bloco = _salmos(r, f, al, hora, dow, dia, laudes, vespera,
                                com_vernaculo, pascal, suprime)
                if bloco:
                    bloco[0].titulo_lat = r.titulo('Psalmi', 'Latin')
                    if com_vernaculo:
                        bloco[0].titulo_ver = r.titulo('Psalmi', 'Portugues')
                pecas.extend(bloco)
            elif nome.startswith('Capitulum'):
                pecas.extend(_capitulo_hino_versiculo(
                    r, texto, al, hora, registo, dia, dia_ver, nome,
                    com_vernaculo, pascal, vespera))
            elif nome.startswith('Canticum'):
                pecas.extend(_cantico(r, f, texto, al, hora, registo, dia,
                                      dia_ver, vespera, com_vernaculo,
                                      pascal, suprime))
            elif nome == 'Oratio':
                p = compor_menores._oracao(r, texto, dia, dia_ver,
                                           com_vernaculo, registo,
                                           hora=hora, vespera=vespera)
                if p:
                    pecas.append(p)
                pecas.extend(_comemoracoes(r, texto, al, hora, registo,
                                           vespera, com_vernaculo, pascal,
                                           dia, dia_ver))
            elif nome == 'Preces Feriales':
                p = _preces(r, texto, hora, dow, dia, registo, nome,
                            com_vernaculo)
                if p:
                    pecas.append(p)
                    # Ditas as Preces, o 'Dómine, exáudi' que vem a seguir
                    # nao se repete: no lugar dele sai a rubrica a dize-lo.
                    f.e.precesferiales = True
            elif nome in compor.SO_TITULO:
                bloco_aberto[0] = nome
            elif nome not in ('Suffragium',
                              'Antiphona finalis',
                              'Commemoratio officii parvi B.M.V.'):
                print(f'  BLOCO SEM TRATAMENTO: {nome}', file=sys.stderr)
            continue

        if not a_calar[0]:
            lat, ver = par(l)
            if not lat.strip():
                continue
            gen = 'rubrica' if l.startswith('$rubrica ') else 'texto'
            tl = tv = ''
            if bloco_aberto[0]:
                tl = r.titulo(bloco_aberto[0], 'Latin')
                tv = (r.titulo(bloco_aberto[0], 'Portugues')
                      if com_vernaculo else '')
                bloco_aberto[0] = ''
            pecas.append(compor.Peca(gen, '', lat, ver, tl, tv))

    return pecas, r, registo


# --------------------------------------------------------------------------

def _salmos(r, f, al, hora, dow, dia, laudes, vespera, com_vernaculo,
            pascal, suprime=False):
    """Os cinco salmos, cada um com a sua antifona."""
    lat = salmodia_maior(r, hora, dow, 'Latin', dia, laudes, vespera)
    ver = (salmodia_maior(r, hora, dow, 'Portugues', dia, laudes, vespera)
           if com_vernaculo else [])

    saida = []
    for k, (ant_lat, chamadas) in enumerate(lat):
        ant_ver = ver[k][0] if k < len(ver) else ''
        if al is not None:
            ant_lat = al.antifona(alleluia.tempo(ant_lat, pascal, suprime),
                                  'Latin', pascal)
            ant_ver = al.antifona(alleluia.tempo(ant_ver, pascal, suprime),
                                  'Portugues', pascal)
        saida.append(compor.Peca(
            'antifona', 'Ant.',
            f'Ant. {ant_lat}' if ant_lat else '',
            f'Ant. {ant_ver}' if ant_ver else ''))

        for chamada in chamadas:
            args = f.argumentos(chamada)
            f.e.psalmnum = len(saida)
            f.e.sinal_na_antifona = False
            t_lat = f.expandir(f.psalm(*(args + ['Latin', ant_lat])), 'Latin')
            if f.e.sinal_na_antifona and saida[-1].latim:
                saida[-1].latim += ' /:‡:/'
            t_ver = ''
            if com_vernaculo:
                f.e.psalmnum = len(saida)
                f.e.sinal_na_antifona = False
                t_ver = f.expandir(f.psalm(*(args + ['Portugues', ant_ver])),
                                   'Portugues')
                if f.e.sinal_na_antifona and saida[-1].vernaculo:
                    saida[-1].vernaculo += ' /:‡:/'
            saida.append(compor.Peca(
                'salmo', f'Salmo {args[0] if args else ""}', t_lat, t_ver))

        saida.append(compor.Peca(
            'antifona', 'Ant.',
            f'Ant. {antifona_repetida(ant_lat)}' if ant_lat else '',
            f'Ant. {antifona_repetida(ant_ver)}' if ant_ver else ''))
    return saida


def dizem_se_preces(dia, registo, hora, dayofweek):
    """Se hoje se dizem as Preces feriais. Porta de 'preces', no ramo de
    1960.

    A reforma reduziu-as muito: so as quartas e sextas-feiras, e nas
    Temporas — e nunca em festa de santo, nem no tempo pascal, nem em
    domingo. As Temporas contam mesmo quando caem ao sabado, que e o dia
    em que sempre caem as terceiras: sem isso, os tres sabados das
    Temporas ficavam sem as suas quarenta linhas de Preces.
    """
    if dia is None or registo is None:
        return False
    rule = dia.rule or ''
    tempo = registo.tempo or ''
    temporas = (registo.temporas or '') == '1'
    duplex = 0.0
    try:
        duplex = float(registo.duplex or 0)
    except ValueError:
        pass

    if (re.search(r'C12', dia.proprio, re.I)
            or re.search(r'Omit.*? Preces', rule, re.I)
            or duplex > 2
            or re.search(r'Pasc[67]', tempo, re.I)):
        return False
    if not dayofweek:
        return False
    if dayofweek == 6 and re.search(r'vespera', hora, re.I):
        return False
    if re.search(r'sancti', dia.proprio, re.I):
        return False
    if not (re.search(r'Preces', rule, re.I)
            or re.search(r'Adv|Quad(?!p)', tempo, re.I)
            or temporas):
        return False
    return dayofweek in (3, 5) or temporas


def _preces(r, texto, hora, dayofweek, dia, registo, nome_do_bloco,
            com_vernaculo):
    """As Preces feriais de Laudes e Vésperas."""
    if not dizem_se_preces(dia, registo, hora, dayofweek):
        return None

    def buscar(lang):
        return (r.setupstring(lang, ESPECIAL_MAIOR)
                .get(f'Preces feriales {hora}') or '').strip()

    lat = texto('Latin', buscar('Latin'))
    if not lat.strip():
        return None
    return compor.Peca('texto', 'Preces', lat,
                       texto('Portugues', buscar('Portugues'))
                       if com_vernaculo else '',
                       r.traduzir('Preces Feriales', 'Latin'),
                       r.traduzir('Preces Feriales', 'Portugues')
                       if com_vernaculo else '')


def _variante_do_tempo(tempo, ind):
    """A secção do Saltério que serve o tempo litúrgico do dia.

    E o miolo do 'gettempora' deles, so para o que a comemoracao precisa:
    o tempo do dia COMEMORADO, que nao e o do vencedor e por isso nao vem
    colhido no Ordo.
    """
    tempo = tempo or ''
    if re.match(r'Adv', tempo, re.I):
        return 'Adv'
    if re.match(r'Quad[56]', tempo, re.I):
        return 'Quad5'
    if re.match(r'Quad(?!p)', tempo, re.I):
        return 'Quad'
    if re.match(r'Pasc[0-5]', tempo, re.I):
        return 'Pasch'
    if re.match(r'Pasc6', tempo, re.I):
        return 'Asc'
    if re.match(r'Pasc7', tempo, re.I):
        return 'Pent'
    return 'Feria'


def _comemoracoes(r, texto, al, hora, registo, vespera, com_vernaculo,
                  pascal, dia=None, dia_ver=None):
    """Os oficios que o dia venceu mas nao apaga.

    Um santo de classe inferior nao desaparece do dia em que cai: reza-se
    dele uma antifona, um versiculo e a oracao, a seguir a oracao do dia.
    E o que faz S. Joaquim aparecer no domingo XII depois de Pentecostes.

    Porta de 'commemoratio' e de 'getcommemoratio', em specials/orationes.pl.

    Tres regras mandam aqui, e as tres foram medidas contra o gerador:

      a ORDEM      cada comemoracao recebe uma chave pela sua classe, e
                   sai por essa ordem — a de classe mais alta primeiro
      o LIMITE     nas rubricas de 1960, um dia de II classe ou uma feria
                   maior admitem UMA comemoracao so
      a CONCLUSAO  duas oracoes seguidas dizem-se sob uma so conclusao: a
                   primeira perde a sua, e a ultima fecha as duas
    """
    # Um dia pode ter mais do que uma comemoracao, e cada uma pede as
    # pecas do SEU numero de hora. As Vesperas tem tres origens:
    #
    #   o oficio concorrente   o dia que cede a hora ao seguinte, e que
    #                          por isso se comemora em primeiro lugar
    #   as de amanha           primeiras Vesperas do dia que comeca (1)
    #   as de hoje             segundas Vesperas do dia que acaba (3)
    #
    # As Laudes tem so uma lista, e o numero e sempre 2.
    def juntar(fonte, indice, chave_base, para):
        for nome in (fonte or '').split('|'):
            nome = nome.strip()
            if not nome:
                continue
            if '/' not in nome:
                nome = f'Tempora/{nome}'
            if not nome.endswith('.txt'):
                nome += '.txt'
            if nome not in [f for f, _, _ in para]:
                para.append((nome, indice, chave_base))

    ficheiros = []
    if hora == 'Vespera':
        if registo.concorrente:
            juntar(registo.concorrente,
                   int(registo.concorrente_vespera or 3), 1000, ficheiros)
        juntar(registo.comemoracoes_amanha, 1, None, ficheiros)
        juntar(registo.comemoracoes, 3, None, ficheiros)
    else:
        juntar(registo.comemoracoes, 2, None, ficheiros)
    if not ficheiros:
        return []

    def montar_uma(lang, ficheiro, ind):
        """Porta de getcommemoratio. Devolve (texto, classe)."""
        try:
            c = Dia(r, ficheiro, VERSAO, lang=lang,
                    ficheiro_do_mes=_mes_do_ficheiro(registo, ficheiro, ind))
        except (FileNotFoundError, OSError):
            return '', 0.0
        campos = (c.secoes.get('Rank') or '').split(';;')
        grau = _numero(campos[2] if len(campos) > 2 else '')
        # Uma feria comum nao se comemora. E a primeira porta do
        # original, e e ela que cala 'Die Decima Januarii' a 10 de
        # Janeiro.
        if (grau < 2.1 and grau != 1.15
                and re.search(r'Feria', campos[1] if len(campos) > 1 else '')):
            return '', grau

        # O Comum a que a comemoracao remete. No tempo pascal os tres
        # primeiros Comuns tem versao propria — 'C2b-1' passa a 'C2b-1p'.
        com = {}
        achado = re.search(r'(?:ex|vide)\s+(.*?)\s*$',
                           campos[3] if len(campos) > 3 else '', re.I)
        if achado:
            nome_do_comum = achado.group(1)
            if re.match(r'C[1-3](?![v\d])', nome_do_comum) and pascal:
                nome_do_comum = re.sub(r'p?$', 'p', nome_do_comum)
            caminho = (nome_do_comum if re.match(r'Sancti', nome_do_comum)
                       else subpasta('Commune', VERSAO) + nome_do_comum)
            try:
                com = r.setupstring(lang, f'{caminho}.txt')
            except (FileNotFoundError, OSError):
                com = {}

        # --- a oracao
        oracao = (c.secoes.get('Oratio') or '').strip()
        if not oracao and re.search(r'Oratio Dominica',
                                    c.secoes.get('Rule') or '', re.I):
            oracao = compor_menores._oracao_do_domingo(r, c, lang,
                                                       registo.tempo)
        if not oracao:
            oracao = ((c.secoes.get(f'Oratio {ind}') or '')
                      or (c.secoes.get(f'Oratio {4 - ind}') or '')
                      or (com.get('Oratio') or '')).strip()
        if not oracao:
            return '', grau
        oracao = c.substituir_nome(oracao.split('\n_\n')[0])

        # --- a antifona
        ant = ((c.secoes.get(f'Ant {ind}') or '')
               or (c.secoes.get(f'Ant {4 - ind}') or '')
               or (com.get(f'Ant {ind}') or ''))
        ant = _primeira_antifona(c.substituir_nome(ant)) if ant else ''
        # De 17 a 23 de Dezembro a feria comemorada leva a grande
        # antifona 'O' do dia, e nao a sua.
        if re.search(r'tempora', ficheiro, re.I):
            especial = _antifona_do_advento_comemorada(r, hora, registo, lang)
            if especial:
                ant = especial
        if not ant:
            return '', grau
        # Na comemoracao a antifona diz-se por inteiro: o asterisco, que
        # marca onde ela se corta, nao faz sentido aqui.
        ant = re.sub(r'\s*\*\s*', ' ', ant)
        ant = al.antifona(alleluia.tempo(ant, pascal, False), lang, pascal)

        # --- o versiculo
        versiculo = ((c.secoes.get(f'Versum {ind}') or '')
                     or (c.secoes.get(f'Versum {4 - ind}') or '')
                     or (com.get(f'Versum {ind}') or '')
                     or (com.get(f'Versum {4 - ind}') or '')).strip()
        if not versiculo:
            versiculo = _do_psalterio(r, registo, 'Versum', ind, lang)

        titulo = r.traduzir('Commemoratio', lang)
        # O nome sai da [Rank], nao do [Officium]: depois de Agosto e
        # depois da Epifania a [Rank] traz a semana e o mes liturgico
        # acrescentados — 'Dominica XII Post Pentecosten III. Augusti' —
        # e e assim que a comemoracao se anuncia.
        nome_do_santo = (campos[0].strip()
                         or (c.secoes.get('Officium') or '').strip())
        partes = [f'!{titulo} {nome_do_santo}', f'Ant. {ant}']
        if versiculo:
            partes += ['_', al.versiculo(versiculo, lang, pascal)]
        partes += ['_', '$Oremus', oracao]
        return '\n'.join(partes), grau

    # --- montar todas, e ordena-las como o original as ordena
    montadas = []
    ordem = 0
    for lat, ver in _do_vencedor(r, dia, dia_ver, registo, vespera,
                                 com_vernaculo, pascal):
        ordem += 1
        base = 3000 if re.search('Dominic[aæ]',
                                 lat.split('\n')[0]) else 0
        montadas.append((base or ordem + 9900, lat, ver))
    for ficheiro, ind, chave_base in ficheiros:
        lat, grau = montar_uma('Latin', ficheiro, ind)
        if not lat.strip():
            continue
        ordem += 1
        if chave_base is not None:
            chave = chave_base
        else:
            base = (7000 if re.search(r'Dominic[aæ]', lat.split('\n')[0])
                    else grau * 1000)
            chave = 10000 - base + ordem
        ver = (montar_uma('Portugues', ficheiro, ind)[0]
               if com_vernaculo else '')
        montadas.append((chave, lat, ver))
    if not montadas:
        return []
    montadas.sort(key=lambda x: x[0])

    # Nas rubricas de 1960 um dia de II classe ou uma feria maior admitem
    # UMA comemoracao so — a de classe mais alta.
    grau_do_dia = registo.rank
    if (len(montadas) > 1
            and (grau_do_dia >= 5
                 or (re.search(r'Feria', registo.titulo or '', re.I)
                     and grau_do_dia >= 4))):
        montadas = montadas[:1]

    # Duas oracoes seguidas dizem-se sob uma so conclusao. Porta de
    # delconclusio: a conclusao sai de dentro de cada oracao e so a
    # ultima se imprime, no fim de todas.
    fora, conclusao_lat, conclusao_ver = [], '', ''
    for _chave, lat, ver in montadas:
        lat, conclusao_lat = _tirar_conclusao(lat, conclusao_lat)
        ver, conclusao_ver = _tirar_conclusao(ver, conclusao_ver)
        p_lat = texto('Latin', lat)
        if not p_lat.strip():
            continue
        fora.append(compor.Peca(
            'texto', 'Commemoratio', p_lat,
            texto('Portugues', ver) if com_vernaculo else ''))
    if conclusao_lat and fora:
        fora.append(compor.Peca(
            'texto', 'Commemoratio', texto('Latin', conclusao_lat),
            texto('Portugues', conclusao_ver) if com_vernaculo else ''))
    return fora


REFERENCIA = re.compile(r'(?is)(.*?)@([a-z0-9/\-]+?):([a-z0-9 ]*)(.*)')


def _resolver_referencia(r, registo, texto_do_bloco, ind, lang, pascal):
    """Porta de getrefs, no ramo '@Ficheiro:Oratio'.

    Uma seccao '[Commemoratio]' pode nao trazer o texto: traz uma
    remissao para outro oficio — '@Tempora/Quad5-5:Oratio' — e o que se
    reza e a antifona, o versiculo e a oracao DESSE oficio. E o que faz a
    Sexta-feira antes do Domingo da Paixao comemorar as Sete Dores com o
    formulario da festa.
    """
    achado = REFERENCIA.match(texto_do_bloco or '')
    if not achado:
        return texto_do_bloco
    antes, ficheiro, item, depois = (achado.group(1), achado.group(2),
                                     achado.group(3).strip(), achado.group(4))
    if not re.search(r'oratio', item, re.I):
        return texto_do_bloco
    # No tempo pascal os Comuns dos Martires tem versao propria.
    if pascal:
        ficheiro = re.sub(r'(C[23])', r'\1p', ficheiro)
    try:
        s = r.setupstring(lang, f'{ficheiro}.txt')
    except (FileNotFoundError, OSError):
        return texto_do_bloco

    com = {}
    achado_comum = re.search(r';;(?:ex|vide)\s+(.*?)\s*$',
                             s.get('Rank') or '', re.I)
    if achado_comum:
        nome = achado_comum.group(1)
        if re.match(r'C[1-3]a?$', nome) and pascal:
            nome += 'p'
        caminho = (nome if re.match(r'Sancti', nome)
                   else subpasta('Commune', VERSAO) + nome)
        try:
            com = r.setupstring(lang, f'{caminho}.txt')
        except (FileNotFoundError, OSError):
            com = {}

    ant = (s.get(f'Ant {ind}') or com.get(f'Ant {ind}') or '').strip()
    if not ant and re.search(r'tempora', ficheiro, re.I):
        ant = _do_psalterio(r, registo, 'Ant', ind, lang)
    versiculo = (s.get(f'Versum {ind}') or com.get(f'Versum {ind}')
                 or '').strip()
    if not versiculo and re.search(r'tempora', ficheiro, re.I):
        versiculo = _do_psalterio(r, registo, 'Versum', ind, lang)
    oracao = (s.get(item) or com.get(item) or '').strip()
    if oracao and '$Oremus' not in oracao:
        oracao = f'$Oremus\n{oracao}'
    if not antes.strip():
        antes = (f"!{r.traduzir('Commemoratio', lang)} "
                 f"{(s.get('Officium') or '').strip()}")
    ant = re.sub(r'\s*\*\s*', ' ', _primeira_antifona(ant))
    return f'{antes.rstrip()}\nAnt. {ant}\n_\n{versiculo}\n_\n{oracao}\n_\n{depois}'



def _do_vencedor(r, dia, dia_ver, registo, vespera, com_vernaculo, pascal):
    """A comemoracao que o proprio oficio do dia traz escrita.

    Nao vem da lista da precedencia: esta dentro do ficheiro, numa seccao
    '[Commemoratio]' ou '[Commemoratio 2]'. E o que faz a Sexta-feira
    antes do Domingo da Paixao comemorar as Sete Dores de Nossa Senhora.

    Porta do bloco 'add commemorated from winner' de 'commemoratio'.
    """
    if dia is None:
        return []
    if (registo.rank >= 6
            and not re.search(r'Pasc[07]|Pent01', registo.tempo or '', re.I)):
        return []
    if re.search(r'nocomm1960', dia.secoes.get('Rule') or '', re.I):
        return []

    def buscar(d):
        if d is None:
            return ''
        t = d.secoes.get(f'Commemoratio {vespera}')
        if t and t.strip():
            return t
        t = d.secoes.get('Commemoratio')
        if t and t.strip() and (vespera != 3
                                or re.search(r'Tempora|C12', d.proprio, re.I)
                                or re.search(r'!.*O[ckt]ta', t)):
            return t
        return ''

    ind = vespera if vespera in (1, 3) else 2
    lat = _resolver_referencia(r, registo, buscar(dia), ind, 'Latin', pascal)
    if not lat.strip():
        return []
    ver = (_resolver_referencia(r, registo, buscar(dia_ver), ind, 'Portugues',
                                pascal) if com_vernaculo else '')
    # Um mesmo bloco pode trazer mais do que uma comemoracao, cada uma a
    # abrir por '!'. O original parte-as ai.
    partes_lat = _partir_comemoracoes(lat)
    partes_ver = _partir_comemoracoes(ver) if ver else []
    return [(pl, partes_ver[k] if k < len(partes_ver) else '')
            for k, pl in enumerate(partes_lat)]


def _partir_comemoracoes(texto):
    partes, atual = [], []
    for linha in (texto or '').split('\n'):
        if linha.startswith('!') and atual:
            partes.append('\n'.join(atual))
            atual = []
        atual.append(linha)
    if atual:
        partes.append('\n'.join(atual))
    return [p for p in partes if p.strip()]



CONCLUSAO = re.compile(r'(?m)^(\$(?!Oremus).*?(?:\n|$))')


def _tirar_conclusao(texto_da_oracao, conclusao):
    """Porta de delconclusio: tira a conclusao de dentro da oracao e
    guarda-a para o fim."""
    if not texto_da_oracao:
        return texto_da_oracao, conclusao
    achado = CONCLUSAO.search(texto_da_oracao)
    if not achado:
        return texto_da_oracao, conclusao
    return (texto_da_oracao[:achado.start()] + texto_da_oracao[achado.end():],
            achado.group(1).strip())


def _do_psalterio(r, registo, item, ind, lang):
    """Porta de getfrompsalterium: a peca do Saltério que serve a hora."""
    variante = registo.variante('getfrompsalterium major') or 'Feria'
    secoes = r.setupstring(lang, ESPECIAL_MAIOR)
    for chave in (f'{variante} {item} {ind}', f'{variante} {item} 1',
                  f'{variante} {item} 3', f'{variante} {item} 2'):
        t = (secoes.get(chave) or '').strip()
        if t:
            return t
    return ''


def _numero(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0



def _dizem_se_as_ladainhas(registo, dia):
    """Se hoje a Ladainha de Todos os Santos fecha as Laudes.

    Nas rubricas de 1960 e uma vez por ano: 25 de Abril, nas Ladainhas
    Maiores. O original prende-a ao mes de Abril — 'month == 4' — e a
    regra 'Laudes Litania' do dia.
    """
    mes, dia_do_mes, _ = (int(x) for x in registo.data.split('-'))
    if mes != 4:
        return False
    regra = (dia.rule or '') if dia is not None else ''
    if re.search(r'Sancti', registo.vencedor or '', re.I) and dia_do_mes != 25:
        return False
    return bool(re.search(r'Laudes Litania', regra, re.I))


def _litania(r, f, texto, com_vernaculo):
    """A Ladainha de Todos os Santos, encurtada como o original a encurta.

    O original parte-a por LINHA EM BRANCO e le cinco desses blocos: o
    primeiro, o ultimo, o segundo, o penultimo e o terceiro. Como o
    ficheiro nao tem linhas em branco — as suas divisoes sao linhas de
    '_' — a divisao da um bloco so, e a Ladainha sai inteira. E a que o
    site imprime, e a que se imprime aqui.
    """
    def montar(lang):
        bruto = (r.setupstring(lang, 'Psalterium/Special/Preces.txt')
                 .get('Litania') or '')
        blocos = bruto.split('\n\n') + ['', '']
        escolhidos = [blocos[0], blocos[-1], blocos[1], blocos[-2], blocos[2]]
        return '\n'.join(['$Domine exaudi', '&Benedicamus_Domino']
                          + [b for b in escolhidos if b.strip()])

    # A Ladainha acaba com o 'Dómine, exáudi' — e depois dela o segundo
    # nao se repete: no lugar dele sai a rubrica a dize-lo. E o
    # 'litaniaflag' do original.
    f.e.litaniaflag = True
    lat = texto('Latin', montar('Latin'))
    f.e.litaniaflag = True
    ver = texto('Portugues', montar('Portugues')) if com_vernaculo else ''
    f.e.litaniaflag = False
    if not lat.strip():
        return None
    return compor.Peca('texto', 'Litania', lat, ver,
                       r.traduzir('Litaniae', 'Latin'),
                       r.traduzir('Litaniae', 'Portugues')
                       if com_vernaculo else '')


def _mtv(dia):
    """Porta de checkmtv.

    Nas rubricas de 1960, o hino das Vésperas de um Confessor ou Doutor
    leva última estrofe própria. A regra do dia assinala-o com ';mtv'.
    """
    if dia is None:
        return ''
    return '1' if re.search(r'C[45]', dia.rule or '') else ''


def _e_inverno(registo, dia=None):
    """Se o hino de domingo se diz na forma de inverno.

    'Ætérne rerum Cónditor' em vez de 'Ecce, iam noctis'. Vale do tempo
    depois da Epifania à Septuagésima, e outra vez em Outubro e Novembro —
    e estes últimos não se conhecem pelo tempo litúrgico, mas pelo nome
    do dia, que nesses meses diz 'Octobris' ou 'Novembris'.
    """
    tempo = registo.tempo or ''
    if re.search(r'Epi[2-6]|Quadp', tempo, re.I):
        return True
    # O nome do dia vem colhido do Ordo, e e o do Perl. Ler o ficheiro por
    # conta propria nao serve: em Outubro e Novembro o nome esta no
    # ficheiro do mes liturgico, e o do vencedor nao o traz.
    return bool(re.search(r'Octobris|Novembris', registo.nome or '', re.I))


def _capitulo_hino_versiculo(r, texto, al, hora, registo, dia, dia_ver,
                             nome_do_bloco, com_vernaculo, pascal, vespera):
    """O capitulo, o hino e o versiculo — por esta ordem."""
    fora = []
    # 'Capitulum major' e 'getfrompsalterium major' percorrem a mesma
    # cascata e dao sempre o mesmo — 'Dominica', 'Feria', 'Adv', 'Quad'.
    variante = registo.variante('getfrompsalterium major') or 'Dominica'

    def capitulo(d, lang):
        nome = 'Capitulum Laudes'
        if re.search(r'12-25', dia.proprio) and vespera == 1:
            nome = 'Capitulum Vespera 1'
        if d is not None:
            t, _ = d.proprium(nome, flag=True)
            if t and t.strip():
                return t.strip()
        return (r.setupstring(lang, ESPECIAL_MAIOR).get(f'{variante} {hora}')
                or '').strip()

    cap_lat = capitulo(dia, 'Latin')
    if cap_lat:
        fora.append(compor.Peca(
            'texto', 'Capitulum',
            texto('Latin', compor_menores._formatar_capitulo(cap_lat)),
            texto('Portugues', compor_menores._formatar_capitulo(
                capitulo(dia_ver, 'Portugues'))) if com_vernaculo else '',
            r.titulo(nome_do_bloco, 'Latin'),
            r.titulo(nome_do_bloco, 'Portugues') if com_vernaculo else ''))

    # --- o hino
    # Nas Vesperas de um Confessor ou Doutor, o hino tem uma ultima
    # estrofe propria — e o 'Hymnus1'. A regra do dia diz quando, pelo
    # sinal ';mtv'. Porta de checkmtv.
    #
    # Mas o sinal so vale se o proprio TIVER essa variante. Ha oficios
    # marcados assim que dao um hino inteiro seu, sob o nome simples; sem
    # esta ressalva, o hino dos Anjos da Guarda cedia o lugar ao 'Iste
    # Conféssor' do Comum.
    raiz = f'Hymnus{_mtv(dia)}' if hora == 'Vespera' else 'Hymnus'
    if (raiz != 'Hymnus'
            and f'{raiz} Vespera' not in dia.secoes
            and not (vespera == 3 and f'{raiz} Vespera 3' in dia.secoes)
            and ((vespera == 3 and 'Hymnus Vespera 3' in dia.secoes)
                 or 'Hymnus Vespera' in dia.secoes)):
        raiz = 'Hymnus'
    nome_do_hino = f'{raiz} {hora}'

    def hino(d, lang):
        if hora == 'Vespera' and vespera == 3 and d is not None:
            t, _ = d.proprium(f'{nome_do_hino} 3', flag=True)
            if t and t.strip():
                return t.strip()
        if d is not None:
            t, _ = d.proprium(nome_do_hino, flag=True)
            if t and t.strip():
                return t.strip()
        # Do Saltério, pela variante do tempo: 'Hymnus Day0 Laudes'.
        variante_h = registo.variante('Hymnus major') or 'Day0'
        secoes = r.setupstring(lang, ESPECIAL_MAIOR)
        for chave in (f'Hymnus {variante_h} {hora} hiemalis',
                      f'Hymnus {variante_h} {hora}'):
            t = (secoes.get(chave) or '').strip()
            if t and chave.endswith("hiemalis") and not _e_inverno(registo, dia):
                continue
            if t:
                return t
        return ''

    h_lat = hino(dia, 'Latin')
    if h_lat:
        fora.append(compor.Peca(
            'hino', 'Hymnus', texto('Latin', h_lat),
            texto('Portugues', hino(dia_ver, 'Portugues'))
            if com_vernaculo else '',
            r.titulo('Hymnus', 'Latin'),
            r.titulo('Hymnus', 'Portugues') if com_vernaculo else ''))

    # --- o versiculo
    ind = 2 if hora == 'Laudes' else vespera

    def versiculo(d, lang):
        if d is None:
            return ''
        for nome in (f'Versum {ind}', f'Versum {4 - ind}'):
            t, _ = d.proprium(nome, flag=True)
            if t and t.strip():
                return t.strip()
        variante_v = registo.variante('getfrompsalterium major') or 'Feria'
        secoes = r.setupstring(lang, ESPECIAL_MAIOR)
        for chave in (f'{variante_v} Versum {ind}', f'{variante_v} Versum 1',
                      f'{variante_v} Versum 3', f'{variante_v} Versum 2'):
            t = (secoes.get(chave) or '').strip()
            if t:
                return t
        return ''

    v_lat = versiculo(dia, 'Latin')
    if v_lat:
        fora.append(compor.Peca(
            'texto', 'Versum',
            texto('Latin', al.versiculo(v_lat, 'Latin', pascal)),
            texto('Portugues', al.versiculo(versiculo(dia_ver, 'Portugues'),
                                            'Portugues', pascal))
            if com_vernaculo else ''))
    return fora


def _primeira_antifona(texto):
    """A antifona escrita no ficheiro, numa linha so.

    O til no fim da linha e marca de juncao: o que vem a seguir pertence
    a mesma antifona. Sem isto, a antifona do Benedictus de 23 de Agosto
    saía cortada em 'Cum transíret' — tres palavras onde deviam ir tres
    linhas.
    """
    texto = re.sub(r'~[^\S\n]*\n[^\S\n]*(?:[vr]\.\s*)?', ' ', texto or '')
    return texto.strip().split('\n')[0]


def _mes_do_ficheiro(registo, ficheiro, ind=0):
    """O ficheiro do mes liturgico que se sobrepoe a um oficio do Tempo.

    A conta do mes ja vem colhida no Ordo; aqui so se ve se este ficheiro
    e dos que a pedem.
    """
    # Nas primeiras Vesperas o oficio comemorado e o de AMANHA, e o mes
    # liturgico que lhe cabe e o do dia seguinte.
    mes = ((registo.monthday_amanha if ind == 1 else registo.monthday_comem)
           or registo.monthday)
    if not mes:
        return ''
    if not re.match(r'Tempora[^/]*/(?:Pent|Epi)', ficheiro or ''):
        return ''
    if re.match(r'Tempora[^/]*/Pent0[1-5]', ficheiro):
        return ''
    return f'Tempora/{mes}.txt'


def _antifona_do_advento_comemorada(r, hora, registo, lang):
    """A antifona 'O' com que se comemora a feria de Advento."""
    mes, dia_do_mes, _ = (int(x) for x in registo.data.split('-'))
    if mes != 12 or not (16 < dia_do_mes < 24):
        return ''
    secoes = r.setupstring(lang, ESPECIAL_MAIOR)
    if hora == 'Vespera':
        return (secoes.get(f'Adv Ant {dia_do_mes}') or '').strip()
    if hora == 'Laudes' and dia_do_mes in (21, 23):
        return (secoes.get(f'Adv Ant {dia_do_mes}L') or '').strip()
    return ''


def _antifona_do_advento(r, hora, registo, lang):
    """A antifona 'O' do cantico, de 17 a 23 de Dezembro. Porta de
    ant123_special."""
    mes, dia_do_mes, _ = (int(x) for x in registo.data.split('-'))
    if mes != 12 or not (16 < dia_do_mes < 24):
        return ''
    if not re.search(r'tempora', registo.vencedor or '', re.I):
        return ''
    secoes = r.setupstring(lang, ESPECIAL_MAIOR)
    if hora == 'Laudes' and dia_do_mes in (21, 23):
        return (secoes.get(f'Adv Ant {dia_do_mes}L') or '').strip()
    if hora == 'Vespera':
        return (secoes.get(f'Adv Ant {dia_do_mes}') or '').strip()
    return ''


def _cantico(r, f, texto, al, hora, registo, dia, dia_ver, vespera,
             com_vernaculo, pascal, suprime=False):
    """O Benedictus ou o Magnificat, com a sua antifona."""
    nome_do_bloco, numero = CANTICO[hora]
    ind = 2 if hora == 'Laudes' else vespera

    variante = registo.variante('getfrompsalterium major') or 'Dominica'

    def antifona(d, lang):
        # De 17 a 23 de Dezembro o cantico das Vesperas leva as grandes
        # antifonas 'O' — 'O Sapiéntia', 'O Adonái' — e as Laudes de 21 e
        # 23 levam a sua. Porta de ant123_special.
        especial = _antifona_do_advento(r, hora, registo, lang)
        if especial:
            return especial
        # Porta de getantvers: o recuo para a antifona da outra hora
        # maior so existe acima do indice 1. Nas PRIMEIRAS Vesperas nao
        # ha recuo — vai-se direito ao Saltério. Sem isto, as primeiras
        # Vesperas de um domingo do tempo comum diziam ao Magnificat a
        # antifona das segundas.
        nomes = (f'Ant {ind}',) if ind <= 1 else (f'Ant {ind}',
                                                  f'Ant {4 - ind}')
        if d is not None:
            for nome in nomes:
                t, _ = d.proprium(nome, flag=True)
                if t and t.strip():
                    return _primeira_antifona(t)
        # Numa feria a antifona do cantico vem do Saltério.
        secoes = r.setupstring(lang, ESPECIAL_MAIOR)
        for chave in (f'{variante} Ant {ind}', f'{variante} Ant 1',
                      f'{variante} Ant 3', f'{variante} Ant 2'):
            t = (secoes.get(chave) or '').strip()
            if t:
                return _primeira_antifona(t)
        return ''

    ant_lat = antifona(dia, 'Latin')
    ant_ver = antifona(dia_ver, 'Portugues') if com_vernaculo else ''
    if al is not None:
        ant_lat = al.antifona(alleluia.tempo(ant_lat, pascal, suprime),
                              'Latin', pascal)
        ant_ver = al.antifona(alleluia.tempo(ant_ver, pascal, suprime),
                              'Portugues', pascal)

    f.e.psalmnum = 0
    lat = f.expandir(f.psalm(numero, 'Latin', ant_lat), 'Latin')
    ver = ''
    if com_vernaculo:
        f.e.psalmnum = 0
        ver = f.expandir(f.psalm(numero, 'Portugues', ant_ver), 'Portugues')

    return [
        compor.Peca('antifona', 'Ant.',
                    f'Ant. {ant_lat}' if ant_lat else '',
                    f'Ant. {ant_ver}' if ant_ver else '',
                    r.titulo(nome_do_bloco, 'Latin'),
                    r.titulo(nome_do_bloco, 'Portugues')
                    if com_vernaculo else ''),
        compor.Peca('cantico', nome_do_bloco, lat, ver),
        compor.Peca('antifona', 'Ant.',
                    f'Ant. {antifona_repetida(ant_lat)}' if ant_lat else '',
                    f'Ant. {antifona_repetida(ant_ver)}' if ant_ver else ''),
    ]


# --------------------------------------------------------------------------

def main():
    hora = 'Laudes'
    data = None
    bilingue = True
    if '--hora' in sys.argv:
        hora = sys.argv[sys.argv.index('--hora') + 1]
    if '--data' in sys.argv:
        data = sys.argv[sys.argv.index('--data') + 1]
    if '--edicao' in sys.argv:
        bilingue = sys.argv[sys.argv.index('--edicao') + 1] != 'latina'
    if not data:
        raise SystemExit('indique --data MM-DD-AAAA')

    pecas, r, registo = montar(hora, data, com_vernaculo=bilingue)
    nome = (f"{hora.lower()}-{data}-"
            f"{'bilingue' if bilingue else 'latina'}.html")
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(
        compor_menores.folha(pecas, hora, registo, bilingue))
    print(f'escrito {nome}')
    print(f'  {registo.nome} [{registo.vencedor}]')
    print(f'  {len(pecas)} peças')


if __name__ == '__main__':
    main()
