"""
Compoe uma hora do oficio como pagina de livro.

Produz um ficheiro HTML que abre no navegador e se imprime em PDF. O
mesmo CSS servira ao WeasyPrint quando ele estiver disponivel: o trabalho
nao se perde.

DECISOES QUE ESTAO AQUI, E DE ONDE VEM
--------------------------------------
formato        10 x 16 cm, o in-18 tradicional e o do breviario de 1942
duas colunas   medida de cerca de 40 caracteres; em corpo 7 uma linha da
               largura da pagina faz o olho perder-se ao voltar
corpo 7        e TODA a escala derivada dele por proporcao, em CSS. Mudar
               '--corpo' muda o livro inteiro sem desmanchar nada
vermelho       so nas rubricas — e o que da nome a coisa
capitulares    a abrir cada salmo, hino e oracao
cabecalho      preciso: 'Feria secunda ad Completorium', nao 'Salterio'
margem interna com folga para a costura de um volume grosso
assinatura     marca no pe, para o encadernador ordenar os cadernos
sem numero de versiculo — o breviario de 1962 nao os imprime

uso:
  python compor.py                          # bilingue, segunda-feira
  python compor.py --edicao latina
  python compor.py --semana "Dominica"
  python compor.py --corpo 8
"""

import html
import io
import re
import sys
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto, ler_arquivo
from resolver import Resolvedor, RESOLVE_NONE
import funcoes
from funcoes import Funcoes, EstadoDoDia
from salmodia import salmodia_menor, antifona_repetida
from proprio import Dia
from ordo import Ordo
import alleluia

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'
VERSAO = 'Rubrics 1960 - 1960'

DIAS = ['Dominica', 'Feria II', 'Feria III', 'Feria IV',
        'Feria V', 'Feria VI', 'Sabbato']

DIA_EM_LATIM = {
    'Dominica': 'Dominica', 'Feria II': 'Feria secunda',
    'Feria III': 'Feria tertia', 'Feria IV': 'Feria quarta',
    'Feria V': 'Feria quinta', 'Feria VI': 'Feria sexta',
    'Sabbato': 'Sabbato',
}
DIA_EM_PORTUGUES = {
    'Dominica': 'Domingo', 'Feria II': 'Segunda-feira',
    'Feria III': 'Terça-feira', 'Feria IV': 'Quarta-feira',
    'Feria V': 'Quinta-feira', 'Feria VI': 'Sexta-feira',
    'Sabbato': 'Sábado',
}

# Um bloco do esqueleto pode juntar varias seccoes do corpus. O nome
# 'Capitulum Responsorium Versus' diz isso mesmo: sao tres pecas. Mapea-lo
# so para o capitulo fazia desaparecer o responsorio breve e o versiculo —
# apanhado ao comparar com o breviario publicado em breviarium.srubarovi.cz.
BLOCOS = {
    'Lectio brevis': [('Psalterium/Special/Minor Special.txt', 'Lectio Completorium')],
    'Hymnus': [('Psalterium/Special/Minor Special.txt', 'Hymnus Completorium')],
    'Capitulum Responsorium Versus': [
        ('Psalterium/Special/Minor Special.txt', 'Completorium'),
        ('Psalterium/Special/Minor Special.txt', 'Responsory Completorium'),
        ('Psalterium/Special/Minor Special.txt', 'Versum 4'),
    ],
    # O cantico de Simeao nao entra aqui: e um salmo, e vai pela funcao
    # '&psalm(233)', que lhe da o titulo e a passagem biblica.
}

# A antifona do Nunc dimittis, que o envolve antes e depois.
ANT_NUNC_DIMITTIS = ('Psalterium/Special/Minor Special.txt', 'Ant 4')

# Blocos que sao so um titulo: o texto vem das linhas '$' e '&' seguintes.
SO_TITULO = {'Incipit', 'Oratio', 'Conclusio'}

# As pecas que abrem com capitular
COM_CAPITULAR = {'salmo', 'hino', 'oracao', 'cantico'}


def dia_da_semana(data):
    """'08-22-2026' -> 'Sabbato'. E aritmetica de calendario civil, nao
    regra liturgica: o dia da semana de uma data nao se pega pronto."""
    mes, dia, ano = (int(x) for x in data.split('-'))
    # O Divinum Officium conta o domingo como 0; o Python conta a
    # segunda-feira como 0.
    return DIAS[(_date(ano, mes, dia).weekday() + 1) % 7]


_ORDO = {}


def ordo_do_ano(data):
    """A tabela do ano dessa data, lida uma vez e guardada.

    Nao se calcula nada aqui: a tabela vem da funcao de precedencia do
    proprio Divinum Officium, colhida por 'ordo.py'. Seccao 12 do prompt.
    """
    ano = data.split('-')[-1]
    if ano not in _ORDO:
        caminho = RAIZ / f'ordo-{ano}.tsv'
        if not caminho.exists():
            raise SystemExit(
                f'falta {caminho.name}. Gerar com: '
                f'python gerador/ordo.py --ano {ano}')
        _ORDO[ano] = Ordo(caminho)
    return _ORDO[ano]


def pascal_na_peca(al, txt, seccao, lang, pascal, dia=None, hora=''):
    """O alleluia do tempo pascal, conforme o genero da peca.

    Cada genero leva o seu: o responsorio breve leva dois alleluias e o
    asterisco muda de sitio; o versiculo leva um em cada linha; a antifona
    leva um no fim.
    """
    if not pascal and not (dia and re.search(
            r'Responsory Breve cum Alleluja', dia.rule or '')):
        return txt
    regra = dia.rule if dia else ''
    if seccao.startswith('Responsory'):
        return al.responsorio_breve(txt, lang, pascal, regra, hora)
    if seccao.startswith('Versum'):
        return al.versiculo(txt, lang, pascal)
    return txt


CHAMADA_DE_BLOCO = re.compile(r"^\s*&special\(\s*'#([^']+)'.*\)\s*$")


def esqueleto_especial(bruto):
    """As linhas de um '[Special <Hora>]', prontas a passar pela maquina.

    Dentro delas pode vir '&special('#Martyrologium', 'Latin')' — que nao
    e uma peca de texto, e sim uma chamada ao BLOCO com esse nome. O
    original devolve-a a maquina dos blocos; aqui reescreve-se como
    '#Martyrologium', que da no mesmo e e mais facil de ler.
    """
    fora = []
    for l in bruto.split('\n'):
        m = CHAMADA_DE_BLOCO.match(l)
        fora.append(f'#{m.group(1)}' if m else l)
    return fora


def omitir_bloco(regra, nome, hora):
    """O '[Rule]' do dia pode mandar calar um bloco inteiro.

        Omit Hymnus Preces Suffragium Commemoratio

    e o que faz a oitava da Pascoa nao ter hino em hora nenhuma. A regra
    olha so a PRIMEIRA palavra do nome do bloco — '#Lectio brevis' e
    'Lectio' — como no original.

    E ha uma segunda regra, a do capitulo: 'Capitulum Versum 2' manda pôr
    um versiculo no lugar do capitulo. Nas Completas isso quer dizer
    calar o capitulo, porque o versiculo ja vem mais abaixo.
    """
    regra = regra or ''
    primeira = (nome or '').split(' ')[0]
    if primeira and re.search(rf'Omit.*? {re.escape(primeira)}', regra, re.I):
        if not re.search(r'Omit ad Matutinum', regra) or hora == 'Matutinum':
            return True

    if 'Capitulum' in (nome or '') and versiculo_no_lugar(regra, hora):
        return True
    return False


def versiculo_no_lugar(regra, hora):
    """Se a regra 'Capitulum Versum 2' se aplica a ESTA hora.

    A clausula pode limitar-se a Laudes, ou a Laudes e Vesperas. Onde nao
    se aplica, o capitulo diz-se como sempre — e nao ha versiculo nenhum
    a por no lugar dele. E o que distingue a Quinta-feira Santa, em que a
    clausula e 'ad Laudes tantum', da oitava da Pascoa, em que vale para
    todas as horas.
    """
    m = re.search(r'Capitulum Versum 2(.*?);?$', regra or '', re.I | re.M)
    if not m:
        return False
    resto = m.group(1)
    if re.search(r'nisi ad Laudes', resto, re.I) and hora == 'Laudes':
        return True
    so_laudes = (re.search(r'ad Laudes tantum', resto, re.I)
                 and hora != 'Laudes')
    laudes_e_vesperas = (re.search(r'ad Laudes et Vesperas', resto, re.I)
                         and hora not in ('Laudes', 'Vespera'))
    return not (so_laudes or laudes_e_vesperas)


def prelude(dia, hora):
    """A rubrica que abre a hora, antes do Incipit.

    O original poe, a cabeca do esqueleto de TODAS as horas, um bloco que
    nao esta em ficheiro nenhum: '#Prelude'. Se o oficio do dia tiver uma
    seccao '[Prelude <Hora>]', ela sai ali; se nao, o bloco desaparece.

    E o que faz o domingo de Pascoa avisar, antes de Matinas, que quem
    esteve na Vigilia nao as reza — e o que avisa, na Quinta-feira Santa,
    que quem foi a Missa vespertina nao reza Vesperas.
    """
    if dia is None:
        return ''
    return (dia.secoes.get(f'Prelude {hora}') or '').strip()


def conclusao_especial(dia):
    """A conclusao propria de um oficio, quando a regra a manda.

    So o dia de Finados a tem: em vez do 'Benedicamus Domino' e do
    'Fidelium animae', diz-se 'Requiescant in pace'. A regra assinala-o
    com 'Special Conclusio', e entao as linhas do Ordinario calam-se
    todas — e o 'skipflag' do original.
    """
    if dia is None or not re.search(r'Special Conclusio', dia.rule or '',
                                    re.I):
        return ''
    return (dia.secoes.get('Conclusio') or '').strip()


def contexto_do_dia(hora, dayofweek, registo=None, data=None):
    """O contexto em que as condicoes dos ficheiros se avaliam.

    Uma linha como

        (tempore Nativitatis aut tempore Epiphaniæ) @Psalterium/Mariaant:Nativiti

    so se decide sabendo em que tempo litúrgico se esta. Esses dois
    valores — 'tempus' e 'die' — vem prontos do Ordo, calculados pelas
    funcoes do proprio Divinum Officium.

    Sem eles, tudo caía no tempo depois de Pentecostes: a antifona final
    de Nossa Senhora saía sempre a Salve Regina, e o 'Laus tibi' da
    Quaresma saía sempre 'Allelúia'.
    """
    mes = int(data.split('-')[0]) if data else 0
    return Contexto(
        version=VERSAO,
        hora=hora,
        tempore=(registo.tempus if registo else '') or 'post Pentecosten',
        die=(registo.die if registo else ''),
        commune=(registo.comum if registo else ''),
        officio=(registo.vencedor if registo else ''),
        dayofweek=dayofweek,
        month=mes,
    )


def estado_do_dia(hora, dayofweek, registo=None, dia=None, proprio=None):
    """O que as funcoes '&' precisam de saber sobre o dia.

    O 'dayname' e o que faz o '&Alleluia' dizer 'Laus tibi, Dómine' em vez
    de 'Allelúia' no tempo da Septuagesima e da Quaresma, e o que cala o
    Gloria no Triduo.
    """
    return EstadoDoDia(
        dayname=(registo.tempo if registo else ''),
        hora=hora,
        version=VERSAO,
        dayofweek=dayofweek,
        vespera=int(registo.vespera or 0) if registo else 0,
        rule=(dia.rule if dia else ''),
        winner=proprio or (registo.vencedor if registo else ''),
        rank=(registo.rank if registo else 0),
        commune=(registo.comum if registo else ''),
        secoes_vencedor=(dia.secoes if dia else {}),
    )


def antifona_final(mes=8, dia_do_mes=17, dayname='', hora='Completorium'):
    """Qual das quatro antifonas finais de Nossa Senhora se diz.

    Nao sao quatro tempos iguais aos do calendario: a Alma Redemptoris vai
    do Advento ate a Purificacao, e por isso a regra e por MES, e nao por
    tempo liturgico. E do original, tal e qual.

    Sem o calculo do calendario, o mes e o dia sao dados de fora; o valor
    por omissao cai no tempo depois de Pentecostes, que e o do dia ja
    composto.
    """
    if (re.search(r'Adv|Nat', dayname, re.I)
            or mes == 1
            or (mes == 2 and dia_do_mes < 2)
            or (mes == 2 and dia_do_mes == 2
                and not re.search(r'Completorium', hora, re.I))):
        return '$ant Alma Redemptoris Mater'
    if ((mes in (2, 3) or re.search(r'Quad', dayname, re.I))
            and not re.search(r'Pasc', dayname, re.I)):
        return '$ant Ave Regina caelorum'
    if re.search(r'Pasc', dayname, re.I):
        return '$ant Regina caeli'
    return '$ant Salve Regina'


# --------------------------------------------------------------------------
# Montagem do texto
# --------------------------------------------------------------------------

class Peca:
    def __init__(self, gen, rotulo, latim, vernaculo,
                 titulo_lat='', titulo_ver=''):
        self.genero = gen           # 'salmo', 'hino', 'oracao', 'rubrica'...
        self.rotulo = rotulo
        self.latim = latim
        self.vernaculo = vernaculo
        # O titulo do bloco, como no Divinum Officium: 'Incipit', 'Hino',
        # 'Salmos'. Sai em vermelho, a abrir o bloco.
        self.titulo_lat = titulo_lat
        self.titulo_ver = titulo_ver


def montar(dia_semana=None, com_vernaculo=True, proprio=None, data=None):
    """Compoe as Completas de um dia.

    Ha duas maneiras de dizer que dia e:

      data='08-22-2026'   o Ordo do ano diz o resto — que oficio vence,
                          de que Comum se toma, que classe tem
      dia_semana='Sabbato'  so o dia da semana: rezam-se as Completas
                          feriais do Saltério, sem festa nenhuma

    Com o Ordo, as regras do proprio e do Comum entram — e sao elas que
    mandam, numa festa de Nossa Senhora, rezar os salmos de domingo em vez
    dos do dia da semana.
    """
    registo = None
    if data:
        # A data manda sobre tudo. Se vier tambem um dia da semana, e
        # porque quem chamou o trazia por omissao — e uma data com um dia
        # da semana que nao e o dela nao existe.
        dia_semana = dia_da_semana(data)
        registo = ordo_do_ano(data).dia(data, 'Completorium')
        if registo is None:
            raise SystemExit(f'o Ordo nao tem {data} — gerar com '
                             f'"python gerador/ordo.py --ano {data[-4:]}"')
        proprio = proprio or registo.vencedor

    if not dia_semana:
        raise SystemExit('indique --data ou --semana')

    idx = DIAS.index(dia_semana)
    ctx = contexto_do_dia('Completorium', idx, registo, data)
    r = Resolvedor(REPO, ctx)
    dia = (Dia(r, proprio, VERSAO, registo=registo) if proprio else None)
    dia_ver = (Dia(r, proprio, VERSAO, lang='Portugues', registo=registo)
               if proprio and com_vernaculo else None)
    f = Funcoes(r, estado_do_dia('Completorium', idx, registo, dia, proprio))

    # No tempo pascal acrescenta-se alleluia as antifonas, aos versiculos
    # e aos responsorios — e dizem-se os que os ficheiros trazem entre
    # parenteses.
    pascal = alleluia.e_tempo_pascal(registo.tempo if registo else '')
    # Da Septuagesima ao sabado santo apaga-se todo o alleluia que o
    # texto traga escrito — mesmo o que vem do Comum.
    suprime = alleluia.suprime_se(
        registo.tempo if registo else '', 'Completorium', idx,
        int(registo.vespera or 0) if registo else 0)
    al = alleluia.Alleluia(r)

    def texto(lang, bruto):
        # As duas expansoes alternam-se ate estabilizar: uma funcao '&'
        # pode devolver formulas '$', e uma formula pode devolver funcoes.
        # E o que acontece no dia de Finados, em que '&special' devolve um
        # pedaco de esqueleto com '$Pater noster' dentro.
        saida = bruto
        for _ in range(6):
            novo = f.expandir(r.expandir_formulas(saida, lang), lang)
            if novo == saida:
                break
            saida = novo
        # Um titulo de bloco vindo de dentro de uma peca nao e texto: o
        # titulo do bloco ja e impresso a parte.
        saida = '\n'.join(l for l in saida.split('\n')
                          if not l.startswith('#'))
        return alleluia.tempo(saida, pascal, suprime)

    def par(bruto_lat):
        lat = texto('Latin', bruto_lat)
        ver = texto('Portugues', bruto_lat) if com_vernaculo else ''
        return lat, ver

    # Ha dias em que a hora nao segue o esqueleto do Ordinario: o proprio
    # traz um esqueleto seu, numa seccao '[Special <Hora>]'. E o caso das
    # Completas do Triduo Sacro e das do dia de Finados.
    #
    # Note-se: e um ESQUELETO, nao texto. O original volta a passa-lo pela
    # mesma maquina, e por isso os '#', os '$' e os '&' que ele traga sao
    # tratados como quaisquer outros.
    especial = (dia.secoes.get('Special Completorium') or '') if dia else ''
    if especial.strip():
        esqueleto = esqueleto_especial(especial)
    else:
        esqueleto = ler_arquivo(
            REPO / 'web/www/horas/Ordinarium/Completorium.txt',
            ctx).get('__preambulo', [])

    pecas = []
    bloco_aberto = ['']    # o titulo do bloco que ainda nao foi impresso
    # O '#Prelude' do original: a rubrica que o oficio do dia poe antes
    # de tudo o resto.
    abertura = prelude(dia, 'Completorium')
    if abertura:
        pecas.append(Peca(
            'rubrica', 'Prelude', texto('Latin', abertura),
            texto('Portugues', prelude(dia_ver, 'Completorium'))
            if com_vernaculo and dia_ver is not None else ''))

    a_calar = [False]      # dentro de um bloco que a regra do dia omite
    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            # Um bloco omitido leva consigo as linhas que o enchem: elas
            # vem a seguir ao '#', e sem isto sairiam soltas na pagina.
            a_calar[0] = omitir_bloco(dia.rule if dia else '', nome,
                                      'Completorium')
            if a_calar[0]:
                continue
            if nome in BLOCOS:
                gen = ('hino' if nome == 'Hymnus'
                       else 'cantico' if nome.startswith('Canticum')
                       else 'texto')
                for k, (rel, sec) in enumerate(BLOCOS[nome]):
                    if sec == '__preamble':
                        bl = r.preambulo('Latin', rel) or ''
                        bv = (r.preambulo('Portugues', rel) or ''
                              ) if com_vernaculo else ''
                    else:
                        bl = r.setupstring('Latin', rel).get(sec, '')
                        bv = (r.setupstring('Portugues', rel).get(sec, '')
                              if com_vernaculo else '')
                    # O alleluia do tempo entra ANTES da expansao — ver a
                    # nota em alleluia.py.
                    lat = texto('Latin', pascal_na_peca(
                        al, bl, sec, 'Latin', pascal, dia))
                    ver = (texto('Portugues', pascal_na_peca(
                        al, bv, sec, 'Portugues', pascal, dia))
                        if com_vernaculo else '')
                    if not lat.strip():
                        continue
                    # so a primeira parte do bloco leva capitular e titulo
                    pecas.append(Peca(
                        gen if k == 0 else 'texto', nome, lat, ver,
                        r.titulo(nome, 'Latin') if k == 0 else '',
                        (r.titulo(nome, 'Portugues')
                         if k == 0 and com_vernaculo else '')))
            elif nome == 'Psalmi':
                bloco = _salmos(r, f, 'Completorium', idx, com_vernaculo,
                                dia, al, pascal, suprime)
                if bloco:
                    bloco[0].titulo_lat = r.titulo('Psalmi', 'Latin')
                    if com_vernaculo:
                        bloco[0].titulo_ver = r.titulo('Psalmi', 'Portugues')
                pecas.extend(bloco)
            elif nome == 'Canticum: Nunc dimittis':
                pecas.extend(_nunc_dimittis(
                    r, f, nome, com_vernaculo, dia, dia_ver,
                    int(registo.vespera or 0) if registo else 0, al, pascal,
                    suprime))
            elif nome == 'Antiphona finalis':
                # Qual das quatro antifonas de Nossa Senhora depende do mes
                # e do tempo liturgico. Sem data, cai no tempo depois de
                # Pentecostes — a Salve Regina.
                if data:
                    m, d, _ = (int(x) for x in data.split('-'))
                    escolha = antifona_final(
                        m, d, registo.tempo if registo else '',
                        'Completorium')
                else:
                    escolha = antifona_final()
                # Qual das quatro se diz e escolha nossa; QUAL O TEXTO de
                # cada uma depende do tempo, e isso esta nas condicoes do
                # ficheiro, que o contexto ja sabe avaliar.
                lat, ver = par(escolha)
                if lat.strip():
                    pecas.append(Peca(
                        'oracao', nome, lat, ver,
                        r.titulo('Antiphona finalis BMV', 'Latin'),
                        (r.titulo('Antiphona finalis BMV', 'Portugues')
                         if com_vernaculo else '')))
                # O 'Divínum auxílium' fecha o dia, e vem a seguir a
                # antifona final — nao esta no esqueleto, e a maquina do
                # original que o acrescenta aqui.
                lat, ver = par('&Divinum_auxilium')
                if lat.strip():
                    pecas.append(Peca('texto', nome, lat, ver))
            elif nome in SO_TITULO:
                # Estes blocos nao tem texto proprio: o que os enche sao as
                # linhas '$' e '&' que vem a seguir. Guarda-se o titulo
                # para a primeira delas.
                bloco_aberto[0] = nome
            elif nome not in ('Capitulum Versus', 'Preces Dominicales',
                              'Commemoratio officii parvi B.M.V.'):
                # Nunca pular peca em silencio — decisao 3.5. Os tres
                # nomes acima sao alternativas de outra familia liturgica
                # ou de outra rubrica, e nao entram no oficio de 1960.
                print(f'  BLOCO SEM TRATAMENTO: {nome}', file=sys.stderr)
            continue

        # Tudo o que nao seja bloco e texto a rezar: as formulas '$', as
        # funcoes '&' e as linhas escritas por extenso, que aparecem nos
        # esqueletos proprios — 'v. Christus factus est pro nobis...'.
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
            pecas.append(Peca(gen, '', lat, ver, tl, tv))

    return pecas, r


def _nunc_dimittis(r, f, nome, com_vernaculo, dia=None, dia_ver=None,
                   vespera=0, al=None, pascal=False, suprime=False):
    """O cantico de Simeao, com a sua antifona antes e depois.

    A antifona e quase sempre a mesma — 'Salva nos, Dómine, vigilántes' —
    mas o oficio do dia pode ter a sua, e entao traz DUAS: uma para antes
    do cantico e outra para a repeticao. E o que acontece na oitava da
    Pascoa, em que se diz 'Allelúia' antes e 'Hæc dies' depois.
    """
    rel, sec = ANT_NUNC_DIMITTIS

    def antifona(lang, d):
        if d is not None:
            texto, _ = d.proprium(f'Ant 4{vespera}')
            if texto and texto.strip():
                return texto.strip()
        return (r.setupstring(lang, rel).get(sec) or '').strip()

    def partir(texto, lang):
        """(antes, depois).

        Quando o oficio do dia da DUAS antifonas, a segunda vai como
        esta: o original nao lhe acrescenta o alleluia do tempo, porque
        ela ja e a do tempo. Quando ha uma so, a repeticao deriva dela —
        e ai o alleluia entra nas duas.
        """
        if al is not None:
            texto = alleluia.tempo(texto, pascal, suprime)
        linhas = [l for l in texto.split('\n') if l.strip()]
        if len(linhas) > 1:
            primeira = (al.antifona(linhas[0], lang, pascal) if al
                        else linhas[0])
            return primeira, linhas[1]
        if al is not None:
            texto = al.antifona(texto, lang, pascal)
        return texto, antifona_repetida(texto)

    ant_lat, repete_lat = partir(antifona('Latin', dia), 'Latin')
    ant_ver = repete_ver = ''
    if com_vernaculo:
        ant_ver, repete_ver = partir(antifona('Portugues', dia_ver or dia),
                                     'Portugues')

    f.e.psalmnum = 0
    lat = f.expandir(f.psalm('233', 'Latin', ant_lat), 'Latin')
    ver = ''
    if com_vernaculo:
        f.e.psalmnum = 0
        ver = f.expandir(f.psalm('233', 'Portugues', ant_ver), 'Portugues')

    return [
        Peca('antifona', 'Ant.',
             f'Ant. {ant_lat}' if ant_lat else '',
             f'Ant. {ant_ver}' if ant_ver else '',
             r.titulo(nome, 'Latin'),
             r.titulo(nome, 'Portugues') if com_vernaculo else ''),
        Peca('cantico', nome, lat, ver),
        Peca('antifona', 'Ant.',
             f'Ant. {repete_lat}' if repete_lat else '',
             f'Ant. {repete_ver}' if repete_ver else ''),
    ]


def _salmos(r, f, hora, dayofweek, com_vernaculo, dia=None, al=None,
            pascal=False, suprime=False):
    """A salmodia de uma hora menor, pela mesma via do original.

    A antifona e a lista de salmos vem de salmodia.py; o texto de cada
    salmo vem da funcao '&psalm', ja conferida contra o Perl. Antes disto
    os salmos eram lidos a mao e saiam sem titulo e sem Gloria.
    """
    ant_lat, chamadas = salmodia_menor(r, hora, dayofweek, 'Latin', dia)
    ant_ver = ''
    if com_vernaculo:
        ant_ver, _ = salmodia_menor(r, hora, dayofweek, 'Portugues', dia)

    if al is not None:
        # As antifonas nao passam pelo 'texto()' da composicao — sao
        # construidas aqui — e por isso o alleluia entre parenteses tem de
        # ser tratado neste sitio. Sem isto saia '(Allelúia.)' impresso.
        ant_lat = alleluia.tempo(ant_lat, pascal, suprime)
        ant_ver = alleluia.tempo(ant_ver, pascal, suprime)
        ant_lat = al.antifona(ant_lat, 'Latin', pascal)
        ant_ver = al.antifona(ant_ver, 'Portugues', pascal)

    saida = [Peca('antifona', 'Ant.',
                  f'Ant. {ant_lat}' if ant_lat else '',
                  f'Ant. {ant_ver}' if ant_ver else '')]

    for k, chamada in enumerate(chamadas):
        args = f.argumentos(chamada)
        # O contador anda por hora, e as duas colunas da pagina tem de dar
        # o mesmo numero ao mesmo salmo.
        f.e.psalmnum = k
        f.e.sinal_na_antifona = False
        lat = f.expandir(f.psalm(*(args + ['Latin', ant_lat])), 'Latin')
        # So o primeiro salmo leva o sinal da antifona.
        if k == 0 and f.e.sinal_na_antifona and saida[0].latim:
            saida[0].latim += ' /:‡:/'
        ver = ''
        if com_vernaculo:
            f.e.psalmnum = k
            f.e.sinal_na_antifona = False
            ver = f.expandir(f.psalm(*(args + ['Portugues', ant_ver])),
                             'Portugues')
            if k == 0 and f.e.sinal_na_antifona and saida[0].vernaculo:
                saida[0].vernaculo += ' /:‡:/'
        saida.append(Peca('salmo', f'Salmo {args[0] if args else ""}',
                          lat, ver))

    saida.append(Peca(
        'antifona', 'Ant.',
        f'Ant. {antifona_repetida(ant_lat)}' if ant_lat else '',
        f'Ant. {antifona_repetida(ant_ver)}' if ant_ver else ''))
    return saida


# --------------------------------------------------------------------------
# Do texto do corpus para HTML
# --------------------------------------------------------------------------

RUBRICA = re.compile(r'/:(.*?):/')
# O numero de versiculo chega de duas maneiras: cru, quando a linha vem
# direita do ficheiro, e ja marcado como rubrica — '/:4:2:/' — quando
# passou pela funcao '&psalm', que e o caminho normal.
NUMERO_DE_VERSICULO = re.compile(r'^\s*(?:/:)?(\d+:\d+)[a-z]?(?::/)?\s*')
MARCA_INTERNA = re.compile(r'(?:/:)?\((\d+[a-z]?)\)(?::/)?\s*')
MARCA_DE_CANTO = re.compile(r'\{:[^}]*:\}')

# Como o Divinum Officium apresenta o texto. Sao opcoes, nao lei — mas o
# padrao segue o site, que foi o pedido.
NUMERAR_VERSICULOS = True      # o site numera; o impresso de 1962 nao
GRAFIA_DE_1960 = True          # nas rubricas de 1960 o 'j' passa a 'i'

# O contador de salmos do site nao entra em livro impresso — ver a nota em
# funcoes.py. Desliga-se aqui, e nao la, para o confronto contra o Perl
# continuar a comparar o que o Perl produz.
funcoes.CONTADOR_DE_SALMO = False


def grafia(texto, lang='Latin'):
    """Nas rubricas de 1960 restaura-se a grafia classica: Iesus, adiutorium.

    SO NO LATIM. E regra de ortografia latina; aplicada ao portugues
    transformava 'S. Joao Baptista' em 'S. Ioao Baptista'.

    E o que o Divinum Officium faz — 'tr/Jj/Ii/' em horascommon.pl — com
    duas excepcoes que ele mesmo repoe.
    """
    if not GRAFIA_DE_1960 or lang != 'Latin':
        return texto
    t = texto.replace('J', 'I').replace('j', 'i')
    t = t.replace('H-Iesu', 'H-Jesu').replace('er eúmdem', 'er eúndem')
    return t


def para_html(bruto, com_capitular=False, lang='Latin'):
    """Transforma o texto do corpus em paragrafos.

    O que sai fora, e porque:
      numero de versiculo  o breviario de 1962 nao os imprime
      marcas de canto      {:H-Nome:} sao para partitura
      '_' sozinho          e separador de estrofe, vira quebra
      'v.' e 'r.'          sao marcas de coluna do site, nao texto
    """
    # O til no fim da linha e uma marca de juncao: o que vem a seguir
    # pertence a mesma linha. E o que faz 'Orémus pro beatíssimo Papa
    # nostro ~ / N.' sair numa linha so.
    # A continuacao pode trazer a marca de coluna 'v.'/'r.' a frente; ela
    # nao sobrevive a juncao.
    bruto = re.sub(r'~[^\S\n]*\n[^\S\n]*(?:[vr]\.\s*)?', ' ', bruto or '')

    paragrafos, atual = [], []
    for linha in bruto.split('\n'):
        l = MARCA_DE_CANTO.sub('', linha)
        numero = ''
        mnum = NUMERO_DE_VERSICULO.match(l)
        if mnum:
            if NUMERAR_VERSICULOS:
                numero = mnum.group(1)
            l = NUMERO_DE_VERSICULO.sub('', l)
        l = MARCA_INTERNA.sub('', l)
        l = re.sub(r'^\s*[vr]\.\s+', '', l)
        if l.startswith('#'):
            # Titulo de bloco vindo de dentro de uma peca — acontece
            # quando uma funcao devolve um pedaco de esqueleto. Sai como
            # titulo, nunca como texto com cardinal.
            paragrafos.append([('', f'@@REF@@{l[1:].strip()}')])
            continue
        if l.startswith('!'):
            # referencia biblica: e titulo, nao texto a rezar
            paragrafos.append([('', f'@@REF@@{l[1:].strip()}')])
            continue
        l = l.rstrip()
        if not l.strip() or l.strip() == '_':
            if atual:
                paragrafos.append(atual)
                atual = []
            continue
        atual.append((numero, l.strip()))
    if atual:
        paragrafos.append(atual)

    fora = []
    for i, p in enumerate(paragrafos):
        if len(p) == 1 and str(p[0][1]).startswith('@@REF@@'):
            fora.append('<p class="referencia">'
                        + html.escape(p[0][1][7:]) + '</p>')
            continue
        corpo = '<br>'.join(_linha_html(x[1], x[0], lang) for x in p)
        if com_capitular and i == 0:
            # A capitular e a primeira LETRA, e o numero de versiculo vem
            # antes dela. Sem esta ressalva, o salmo abria sem capitular.
            corpo = re.sub(
                r'^((?:<span class="versiculo">[^<]*</span>\s*)?)([A-ZÁÉÍÓÚÆŒ])',
                r'\1<span class="capitular">\2</span>', corpo, count=1)
        fora.append(f'<p>{corpo}</p>')
    return '\n'.join(fora)


def _linha_html(l, numero='', lang='Latin'):
    # O sublinhado e um espaco que o Divinum Officium marca para nao se
    # quebrar ali a linha: 'Cântico de_Simeão'. O original troca-o por
    # espaco na hora de mostrar, e sem isso o sublinhado saia impresso.
    l = l.replace('_', ' ')
    # A rubrica dentro da linha vai a vermelho
    # (nota: as linhas '#Titulo' sao retiradas antes, em para_html)
    def rub(m):
        return f'<span class="rubrica">{html.escape(m.group(1))}</span>'
    partes = []
    pos = 0
    for m in RUBRICA.finditer(l):
        partes.append(html.escape(l[pos:m.start()]))
        partes.append(rub(m))
        pos = m.end()
    partes.append(html.escape(l[pos:]))
    saida = ''.join(partes)
    # As letras de versiculo e resposta em vermelho
    saida = re.sub(r'^(V\.|R\.|R\.br\.)', r'<span class="vr">\1</span>', saida)
    # O asterisco da divisao do versiculo
    saida = re.sub(r'\+{3}', '<span class="cruz">&#10009;</span>', saida)
    saida = re.sub(r'(?<![+>])\+(?!\+)', '<span class="cruz">&#10016;</span>', saida)
    # Um asterisco NO INICIO da linha nao e o asterisco do meio do
    # versiculo: e a marca de estrofe nova de um hino. O original nao o
    # imprime — poe inicial na letra seguinte. Sem esta ressalva saia um
    # asterisco vermelho a frente da doxologia de cada hino.
    saida = re.sub(r'^\*\s+([^\s<])',
                   r'<span class="inicial">\1</span>', saida, count=1)
    saida = saida.replace('*', '<span class="asterisco">*</span>')
    # A flexa. E marca de canto como o asterisco, e vai a vermelho como
    # ele — os dois juntos dao a pontuacao do versiculo: flexa, mediante,
    # final.
    saida = saida.replace('†', '<span class="flexa">&#8224;</span>')
    # A vogal muda de um hino: 'Ill[e] amor'. Elide-se ao cantar, e o
    # original imprime-a em italico.
    saida = re.sub(r'\[([æaeiou]m?)\]', r'<i>\1</i>', saida)
    saida = grafia(saida, lang)
    if numero:
        saida = f'<span class="versiculo">{numero}</span> ' + saida
    return saida


# --------------------------------------------------------------------------
# A folha
# --------------------------------------------------------------------------

CSS = """
/* Toda a escala sai de --corpo por proporcao. Mudar --corpo muda o livro
   inteiro; nao ha um so tamanho escrito a mao noutro sitio. */
:root {
  --corpo: %(corpo)spt;
  --entrelinha: 1.22;
  --rubrica: calc(var(--corpo) * 0.93);
  --cabecalho: calc(var(--corpo) * 0.93);
  --titulo-seccao: calc(var(--corpo) * 1.07);
  --titulo-festa: calc(var(--corpo) * 1.35);
  --capitular: calc(var(--corpo) * 2.4);
  --assinatura: calc(var(--corpo) * 0.8);
  --vermelho: #9c1c14;
  --tinta: #17130f;
}

@page {
  size: 100mm 160mm;
  margin: 10mm 8mm 12mm 13mm;   /* a margem interna leva folga p/ costura */
  @bottom-center { content: none; }
}
@page :left  { margin: 10mm 13mm 12mm 8mm; }
@page :right { margin: 10mm 8mm 12mm 13mm; }

* { box-sizing: border-box; }

body {
  font-family: "EB Garamond", "Garamond", "TeX Gyre Pagella", Palatino,
               "Palatino Linotype", Georgia, serif;
  font-size: var(--corpo);
  line-height: var(--entrelinha);
  color: var(--tinta);
  margin: 0;
  text-align: justify;
  hyphens: auto;
  -webkit-hyphens: auto;
}

.cabecalho {
  position: fixed;      /* o Chrome repete o que e fixed em cada pagina */
  top: 0; left: 0; right: 0;
  font-size: var(--cabecalho);
  font-variant: small-caps;
  letter-spacing: .04em;
  text-align: center;
  border-bottom: .3pt solid currentColor;
  padding-bottom: .6mm;
  margin-bottom: 0;
  background: white;
  color: var(--tinta);
}

/* Na edicao LATINA, a pagina leva duas colunas de latim.
   Na BILINGUE, as duas colunas SAO as duas linguas — e a solucao do
   breviario bilingue de 1962, e a unica que cabe: a pagina util tem
   79 mm; partida em duas da 37 mm por coluna, cerca de 40 caracteres em
   corpo 7. Parti-la outra vez para por duas linguas dentro de cada
   coluna daria 18 mm, ou seja doze caracteres por linha. Nao existe. */
.corpo { padding-top: 4.2mm; padding-bottom: 1mm; }   /* espaco para o cabecalho corrido, que
                                    e fixo e por isso sai do fluxo */
.corpo.latina {
  column-count: 2;
  column-gap: 4mm;
  column-fill: auto;
  orphans: 2;
  widows: 2;
}

h2.titulo {
  column-span: all;
  font-size: var(--titulo-seccao);
  font-variant: small-caps;
  letter-spacing: .05em;
  text-align: center;
  color: var(--vermelho);
  margin: 1.6mm 0 .8mm;
  break-after: avoid;      /* nunca um titulo separado do que encabeca */
  font-weight: normal;
}

p { margin: 0 0 .6mm; text-indent: 1.1em; orphans: 2; widows: 2; }
p:first-of-type { text-indent: 0; }

/* A PECA PARTE-SE. Tinha 'break-inside: avoid-column', e uma peca alta
   que nao coubesse no resto da coluna saltava inteira para a pagina
   seguinte, deixando o pe vazio. Medido: 32 paginas com mais de 30 mm a
   sobrar, a pior com 119 mm — quase um quinto da mancha. O breviario
   impresso parte salmos e hinos a vontade; quem segura a qualidade da
   partida sao as orfas e as viuvas, nao a proibicao de partir. */
.par { break-inside: auto; orphans: 2; widows: 2; margin-bottom: .9mm; }

.capitular {
  float: left;
  font-size: var(--capitular);
  line-height: .84;
  padding: .3mm .5mm 0 0;
  color: var(--vermelho);
}

.versiculo {
  font-size: calc(var(--corpo) * 0.78);
  color: var(--vermelho);
  vertical-align: .12em;
  letter-spacing: 0;
}
.bloco {
  color: var(--vermelho);
  font-style: italic;
  font-size: var(--titulo-seccao);
  text-indent: 0;
  margin: 1.4mm 0 .3mm;
  break-after: avoid;
}
.referencia {
  color: var(--vermelho);
  font-size: var(--rubrica);
  font-variant: small-caps;
  letter-spacing: .05em;
  text-indent: 0;
  margin-top: .8mm;
  break-after: avoid;
}
/* A letra que abre uma estrofe de hino. Nao e capitular: e so uma
   inicial, como no bilingue de 1962. */
.inicial { font-variant: small-caps; font-weight: 600; }
.rubrica { color: var(--vermelho); font-size: var(--rubrica); font-style: italic; }
.cruz    { color: var(--vermelho); }
.vr      { color: var(--vermelho); }
.asterisco { color: var(--vermelho); }
.flexa     { color: var(--vermelho); }

.lat, .ver { }
.ver { }
.ver p { }

.assinatura {
  position: fixed;
  bottom: -7mm; left: 0; right: 0;   /* dentro da margem inferior, fora
                                        da mancha de texto */
  pointer-events: none;
  text-align: center;
  font-size: var(--assinatura);
  letter-spacing: .1em;
  color: var(--tinta);
  opacity: .75;
}

/* Na edicao bilingue as duas linguas andam emparelhadas peca a peca:
   e o que impede os buracos brancos quando uma e mais curta que a outra. */
.duplo { display: table; width: 100%%; table-layout: fixed;
         break-inside: avoid; margin-bottom: 1mm; }
.duplo > div { display: table-cell; vertical-align: top; }
.duplo > .lat { padding-right: 2mm; width: 47%%; }
.duplo > .ver { padding-left: 2mm; width: 53%%; }  /* o portugues e mais
                                                      comprido que o latim */
"""


def folha(pecas, dia_semana, bilingue, corpo, registo=None):
    o = []
    A = o.append
    # O cabecalho corrido nomeia o dia como ele se reza: numa festa, o
    # nome da festa; num dia ferial, o dia da semana.
    nome_lat = ((registo.nome if registo and registo.nome else '')
                or DIA_EM_LATIM[dia_semana])
    A('<!doctype html><html lang="la"><head><meta charset="utf-8">')
    A(f'<title>Completorium — {html.escape(nome_lat)}</title>')
    A('<style>' + (CSS % {'corpo': corpo}) + '</style></head><body>')

    cab = (f'{html.escape(nome_lat)} ad Completorium' if not bilingue
           else f'{html.escape(nome_lat)} ad Completorium'
                f' &nbsp;·&nbsp; {DIA_EM_PORTUGUES[dia_semana]}, Completas')
    A(f'<div class="cabecalho">{cab}</div>')
    A('<div class="corpo %s">' % ('bilingue' if bilingue else 'latina'))
    A('<h2 class="titulo">Ad Completorium</h2>')

    for p in pecas:
        cap = p.genero in COM_CAPITULAR
        lat = para_html(p.latim, cap, 'Latin')
        if not lat.strip():
            continue
        tl = (f'<p class="bloco">{html.escape(p.titulo_lat)}</p>'
              if p.titulo_lat else '')
        tv = (f'<p class="bloco">{html.escape(p.titulo_ver)}</p>'
              if p.titulo_ver else '')
        if bilingue:
            ver = para_html(p.vernaculo, cap, 'Portugues')
            A('<div class="duplo">'
              f'<div class="lat">{tl}{lat}</div>'
              f'<div class="ver">{tv}{ver}</div></div>')
        else:
            A(f'<div class="par">{tl}{lat}</div>')

    A('</div>')
    A('<div class="assinatura">A</div>')
    A('</body></html>')
    return '\n'.join(o)


def main():
    dia = None
    data = None
    corpo = 7
    bilingue = True
    if '--data' in sys.argv:
        data = sys.argv[sys.argv.index('--data') + 1]
    if '--semana' in sys.argv:
        dia = sys.argv[sys.argv.index('--semana') + 1]
    if '--corpo' in sys.argv:
        corpo = sys.argv[sys.argv.index('--corpo') + 1]
    if '--edicao' in sys.argv:
        bilingue = sys.argv[sys.argv.index('--edicao') + 1] != 'latina'
    if not data and not dia:
        dia = 'Feria II'

    registo = None
    if data:
        dia = dia or dia_da_semana(data)
        registo = ordo_do_ano(data).dia(data, 'Completorium')

    pecas, r = montar(dia, com_vernaculo=bilingue, data=data)
    sufixo = f'-{data}' if data else ''
    nome = (f"pagina-completas{sufixo}-"
            f"{'bilingue' if bilingue else 'latina'}.html")
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(
        folha(pecas, dia, bilingue, corpo, registo))

    print(f'escrito {nome}')
    if registo:
        print(f'  {registo.nome} [{registo.vencedor}]'
              + (f'  Comum: {registo.comum}' if registo.comum else ''))
    print(f'  {len(pecas)} peças, corpo {corpo}pt, '
          f"edição {'bilíngue' if bilingue else 'latina'}, {dia}")
    if r.lacunas:
        print(f'  {len(r.lacunas)} peças sem português (saem em latim)')


if __name__ == '__main__':
    main()
