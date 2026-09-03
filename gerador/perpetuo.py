"""
O livro perpetuo: as seis partes classicas, cada uma uma seccao onde se abre
e se reza.

O QUE MUDA, E PORQUE
--------------------
O gerador anterior percorria DATAS: para cada dia de 2026 perguntava ao Ordo
quem vencia e imprimia o oficio inteiro. Dava um livro que so servia para
2026, com os dias em fila de calendario, sem Proprio do Tempo nem Saltério
onde se pudesse abrir e rezar.

Um breviario organiza-se por POSICAO LITURGICA, e o corpus do Divinum
Officium ja esta assim: 'Tempora/Adv1-0' e o Domingo I do Advento,
'Sancti/08-04' e o 4 de Agosto. Cada posicao imprime SO O QUE LHE E PROPRIO
e remete o resto.

    Ordinarium              o esqueleto das horas                 *1
    Psalterium              Domingo a Sabado, oito horas          *1
    Proprium de Tempore     Advento I ate ao fim do ano            1
    Proprium Sanctorum      1 de Janeiro a 31 de Dezembro          .
    Commune Sanctorum       C1 a C11                              *1
    Anexos e Appendix       Parvo de N. Senhora, Defuntos, etc.    *1

As tres partes marcadas com asterisco tem NUMERACAO PROPRIA, como no
breviario de 1942 — e e isso que permitira, depois, partir o livro em quatro
tomos por estacao sem recalcular remissao nenhuma.

O ano corrente entra pelo ORDO, que e caderno a parte: diz, dia a dia, que
posicao se reza e em que pagina esta.
"""

import io
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compor
from dofile import Contexto
from funcoes import Funcoes
from proprio import Dia
from resolver import Resolvedor

RAIZ = compor.RAIZ
REPO = compor.REPO
VERSAO = compor.VERSAO


class _RegistoVazio:
    """O minimo que 'getrefs' pede quando nao ha dia nenhum."""
    data = '01-01-2026'
    tempo = monthday = monthday_comem = monthday_amanha = ''
    vencedor = nome = titulo = ''
    rank = 0.0

    def variante(self, _):
        return 'Feria'


_REGISTO_VAZIO = _RegistoVazio()

# --------------------------------------------------------------------------
# A ordem do ano liturgico
# --------------------------------------------------------------------------

# Os tempos, pela ordem em que o ano os percorre. O numero e a chave de
# ordenacao; o nome e o titulo da parte no livro.
TEMPOS = (
    ('Adv',   1, 'Tempus Adventus'),
    ('Nat',   2, 'Tempus Nativitatis'),
    ('Epi',   3, 'Tempus Epiphaniae'),
    ('Quadp', 4, 'Tempus Septuagesimae'),
    ('Quad',  5, 'Tempus Quadragesimae'),
    ('Pasc',  6, 'Tempus Paschale'),
    ('Pent',  7, 'Tempus post Pentecosten'),
)

MESES = ('Ianuarius', 'Februarius', 'Martius', 'Aprilis', 'Maius', 'Iunius',
         'Iulius', 'Augustus', 'September', 'October', 'November', 'December')

DIAS_DA_SEMANA = ('Dominica', 'Feria II', 'Feria III', 'Feria IV',
                  'Feria V', 'Feria VI', 'Sabbato')


def ordem_do_tempo(nome):
    """A chave que poe 'Adv1-0' antes de 'Pent24-6'."""
    achado = re.match(r'^([A-Za-z]+)(\d*)-?(\d*)(.*)$', nome)
    if not achado:
        return (99, 0, 0, nome)
    prefixo, semana, dia, resto = achado.groups()
    peso = next((p for t, p, _ in TEMPOS if t == prefixo), 98)
    return (peso, int(semana or 0), int(dia or 0), resto)


# --------------------------------------------------------------------------
# As pecas de uma posicao, pela ordem das horas
# --------------------------------------------------------------------------

# Que seccao do ficheiro sai sob que titulo, e por que ordem. E a ordem do
# oficio: Matinas, Laudes, as horas menores, Vesperas, Completas.
#
# So se imprime o que a posicao TIVER: um santo que nao de antifonas de
# Laudes nao leva rubrica nenhuma a dizer que nao as tem — remete-se para o
# Comum, como faz o breviario impresso.
PECAS_DA_POSICAO = (
    ('Ad Matutinum', (
        ('Invit', 'Invitatorium'),
        ('Hymnus Matutinum', 'Hymnus'),
        ('Ant Matutinum', 'Antiphonae'),
        ('Nocturn 1 Versum', 'Versus I Nocturni'),
        ('Nocturn 2 Versum', 'Versus II Nocturni'),
        ('Nocturn 3 Versum', 'Versus III Nocturni'),
        ('Lectio1', 'Lectio i'), ('Responsory1', 'Responsorium i'),
        ('Lectio2', 'Lectio ii'), ('Responsory2', 'Responsorium ii'),
        ('Lectio3', 'Lectio iii'), ('Responsory3', 'Responsorium iii'),
        ('Lectio4', 'Lectio iv'), ('Responsory4', 'Responsorium iv'),
        ('Lectio5', 'Lectio v'), ('Responsory5', 'Responsorium v'),
        ('Lectio6', 'Lectio vi'), ('Responsory6', 'Responsorium vi'),
        ('Lectio7', 'Lectio vii'), ('Responsory7', 'Responsorium vii'),
        ('Lectio8', 'Lectio viii'), ('Responsory8', 'Responsorium viii'),
        ('Lectio9', 'Lectio ix'), ('Responsory9', 'Responsorium ix'),
        ('Lectio93', 'Lectio ix de Commemoratione'),
        ('Lectio94', 'Lectio ix de Legenda'),
    )),
    ('Ad Laudes', (
        ('Ant Laudes', 'Antiphonae'),
        ('Capitulum Laudes', 'Capitulum'),
        ('Hymnus Laudes', 'Hymnus'),
        ('Versum 2', 'Versus'),
        ('Ant 2', 'Ad Benedictus'),
        ('Oratio 2', 'Oratio'),
    )),
    ('Ad Horas minores', (
        ('Lectio Prima', 'Lectio brevis ad Primam'),
        ('Capitulum Tertia', 'Capitulum ad Tertiam'),
        ('Responsory Tertia', 'Responsorium ad Tertiam'),
        ('Capitulum Sexta', 'Capitulum ad Sextam'),
        ('Responsory Sexta', 'Responsorium ad Sextam'),
        ('Capitulum Nona', 'Capitulum ad Nonam'),
        ('Responsory Nona', 'Responsorium ad Nonam'),
    )),
    ('Ad Vesperas', (
        ('Ant Vespera', 'Antiphonae'),
        ('Capitulum Vespera', 'Capitulum'),
        ('Hymnus Vespera', 'Hymnus'),
        ('Versum 1', 'Versus ad I Vesperas'),
        ('Versum 3', 'Versus ad II Vesperas'),
        ('Ant 1', 'Ad Magnificat, I Vesperis'),
        ('Ant 3', 'Ad Magnificat, II Vesperis'),
        ('Ant Vespera 3', 'Antiphonae ad II Vesperas'),
        ('Oratio 3', 'Oratio ad II Vesperas'),
    )),
    ('Ad Completorium', (
        ('Ant Completorium', 'Antiphona'),
    )),
    ('', (
        ('Oratio', 'Oratio'),
        ('Commemoratio', 'Commemoratio'),
        ('Commemoratio 2', 'Commemoratio ad Laudes'),
        ('Commemoratio 3', 'Commemoratio ad II Vesperas'),
    )),
)

# O que NUNCA se imprime: dados de controlo do programa.
NAO_SAO_TEXTO = {'Rank', 'Rule', 'Officium', 'Name', 'Initial', 'Scriptura',
                 'Doxology', 'Comment'}


def contexto(tempo='', dayofweek=0, comum='', oficio='', mes=0):
    return Contexto(version=VERSAO, hora='', tempore=tempo or 'post Pentecosten',
                    die='', commune=comum, officio=oficio,
                    dayofweek=dayofweek, month=mes)


def texto_expandido(r, f, bruto, lang='Latin', registo=None):
    """Resolve as formulas, as funcoes e as remissoes de um pedaco."""
    saida = sem_dados_de_controlo(bruto)
    # As remissoes do corpus — '@Tempora/Quad5-5:Oratio' — vao buscar a
    # antifona, o versiculo e a oracao a outro oficio. Impressas em cru
    # saíam tres no livro; aqui resolvem-se pela mesma via das horas.
    if '@' in saida:
        try:
            import compor_maiores as _M
            saida = _M._resolver_referencia(r, registo or _REGISTO_VAZIO,
                                            saida, 2, lang, False)
        except Exception:
            pass
    for _ in range(6):
        novo = f.expandir(r.expandir_formulas(saida, lang), lang)
        if novo == saida:
            break
        saida = novo
    return '\n'.join(l for l in saida.split('\n') if not l.startswith('#'))


# --------------------------------------------------------------------------
# Que posicoes existem
# --------------------------------------------------------------------------

def posicoes(caminho='ordo-uniao.tsv'):
    """As posicoes liturgicas que o oficio de 1960 usa mesmo.

    Nao se leem da pasta: um ficheiro pode la estar e ser de outra rubrica.
    Leem-se do Ordo de SEIS ANOS — o que aparece como vencedor, como
    ficheiro efectivo ou como comemorado em algum desses anos existe; o
    resto nao entra.
    """
    import csv
    fora = set()
    with io.open(RAIZ / caminho, encoding='utf-8', newline='') as f:
        for l in csv.DictReader(f, delimiter='\t'):
            for campo in ('vencedor', 'ficheiro', 'comemorado'):
                v = (l.get(campo) or '').strip()
                if v.endswith('.txt'):
                    fora.add(v[:-4])
            for c in (l.get('comemoracoes') or '').split('|'):
                c = c.strip()
                if c:
                    fora.add(c[:-4] if c.endswith('.txt') else c)

    tempo = sorted((p for p in fora if p.startswith('Tempora/')),
                   key=lambda x: ordem_do_tempo(x.split('/')[1]))
    # Os do mes liturgico ('093-3') nao sao posicoes do ano: sao o segundo
    # ficheiro que se sobrepoe aos dias depois de Agosto. Ficam de fora da
    # tabua do Proprio do Tempo, que se percorre pelo ano.
    tempo = [p for p in tempo if not re.match(r'^\d', p.split('/')[1])]

    # O Proprio dos Santos leva TODOS os dias do calendario, mesmo os que
    # em seis anos nunca venceram — o livro e perpetuo, e daqui a dez anos
    # esse santo cai num dia livre.
    pasta = REPO / 'web/www/horas/Latin/Sancti'
    santos = sorted(f'Sancti/{f[:-4]}' for f in os.listdir(pasta)
                    if f.endswith('.txt') and re.match(r'^\d\d-\d\d', f))
    comuns = sorted(f'Commune/{f[:-4]}'
                    for f in os.listdir(REPO / 'web/www/horas/Latin/Commune')
                    if f.endswith('.txt'))
    return tempo, santos, comuns


# --------------------------------------------------------------------------
# As partes do livro
# --------------------------------------------------------------------------

import html as _html

HORAS = ('Matutinum', 'Laudes', 'Prima', 'Tertia', 'Sexta', 'Nona',
         'Vespera', 'Completorium')
HORA_EM_LATIM = {'Matutinum': 'Ad Matutinum', 'Laudes': 'Ad Laudes',
                 'Prima': 'Ad Primam', 'Tertia': 'Ad Tertiam',
                 'Sexta': 'Ad Sextam', 'Nona': 'Ad Nonam',
                 'Vespera': 'Ad Vesperas', 'Completorium': 'Ad Completorium'}


# O numero do salmo colado a antifona, em qualquer sitio da linha.
# 'vide Sancti/01-01', 'ex Tempora/Nat01' — remissao ao corpo do livro.
# O " + B + "b antes de 'ex' e obrigatorio: sem ele apanhava-se o 'ex' de
# 'Duplex II classis' e inventavam-se remissoes.
# 'ex C4', 'vide C10a' — remissao ao Comum.
REMISSAO_AO_COMUM = re.compile(
    r'\b(?:ex|vide)\s+(C[0-9a-z\-]+)', re.I)

REMISSAO_AO_CORPO = re.compile(
    r'\b(?:ex|vide)\s+(Tempora|Sancti)/([A-Za-z0-9\-]+)', re.I)
SALMO_SOLTO = re.compile(r';;(\d[\d;,-]*)')
SALMO_COLADO = re.compile(r";;\s*([-0-9;,()a-zA-Z']*)\s*$", re.M)


def sem_dados_de_controlo(bruto):
    """Tira o ';;' que o corpus usa para colar o numero do salmo a
    antifona.

    Nos ficheiros do corpus uma antifona escreve-se assim:

        Dixit Dóminus * Dómino meo: Sede a dextris meis.;;109

    O ';;109' nao e texto: e a maquina a dizer com que salmo esta antifona
    se canta. Impresso em cru sai 'génui te.;;109' — e era isso, repetido
    1.062 vezes, o grosso dos ponteiros que a verificacao apanhava.

    Aqui o numero sai do texto e volta como marca a vermelho no fim da
    linha, que e como o breviario impresso o da: 'Ant. Dixit Dóminus ...
    Ps. 109'.
    """
    fora = []
    for linha in (bruto or '').split(chr(10)):
        # O numero do salmo, esteja onde estiver na linha. NAO basta
        # ancorar ao fim: o ';;138' de 'Ecclesiam meam.;;138' nao vem do
        # ficheiro — e INSERIDO por uma regra de substituicao do '@'
        # (s/\\_/;;138/), depois de a linha ja estar montada, e podia
        # ficar-lhe texto a seguir.
        linha = SALMO_SOLTO.sub(
            lambda m: ' /:Ps. ' + m.group(1).replace(';', ', ') + ':/', linha)
        # O ';;' que sobre em qualquer outro sitio sai. No corpus e
        # SEMPRE separador de campos, nunca texto, e o Perl do sitio
        # tambem nunca o imprime: 'ejusdem Ecclesia;; et tunc de...'.
        linha = re.sub(r'\s*;;\s*', ' ', linha).rstrip()
        fora.append(linha)
    return chr(10).join(fora)


def genero_da_seccao(seccao):
    """Que genero de peca e esta seccao — e o genero e que manda pôr
    capitular a abrir.

    Sem isto o corpo do livro saia SEM UMA CAPITULAR: parte_de_posicoes
    chamava _peca() sem dizer o genero, ficava o 'texto' por omissao, e
    nenhuma oracao, hino ou licao abria com a letra grande. Medido: nem
    uma letra entre 14 e 24pt em pagina nenhuma do Proprio.
    """
    s = (seccao or '').lower()
    if s.startswith('hymnus'):
        return 'hino'
    if s.startswith('oratio'):
        return 'oracao'
    if s.startswith('lectio'):
        return 'oracao'
    if s.startswith('canticum'):
        return 'cantico'
    if s.startswith('ant') or s.startswith('invit'):
        return 'antifona'
    return 'texto'


def _peca(titulo, corpo, genero='texto', ancora=''):
    if not (corpo or '').strip():
        return ''
    # A limpeza dos dados de controlo faz-se AQUI, no funil por onde toda
    # a peca passa antes de virar HTML, e nao em cada chamador. Era um
    # chamador esquecido que deixava passar o 'Ecclesiam meam.;;116'.
    corpo = sem_dados_de_controlo(corpo)
    cap = genero in compor.COM_CAPITULAR
    html = compor.para_html(corpo, cap, 'Latin')
    if not html.strip():
        return ''
    t = f'<p class="bloco">{_html.escape(titulo)}</p>' if titulo else ''
    a = f' id="{ancora}"' if ancora else ''
    return f'<div class="par"{a}>{t}{html}</div>'


def parte_ordinarium(r, f):
    """O esqueleto das horas, uma vez."""
    from dofile import ler_arquivo
    o = []
    for hora, ficheiro in (('Matutinum', 'Matutinum'), ('Laudes', 'Laudes'),
                           ('Prima', 'Prima'), ('Horae minores', 'Minor'),
                           ('Vespera', 'Vespera'),
                           ('Completorium', 'Completorium')):
        linhas = ler_arquivo(REPO / f'web/www/horas/Ordinarium/{ficheiro}.txt',
                             contexto(hora=hora) if False else contexto()
                             ).get('__preambulo', [])
        corpo = []
        for l in linhas:
            l = l.strip()
            if not l:
                continue
            if l.startswith('#'):
                corpo.append(f'!{l[1:].strip()}')
                continue
            corpo.append(texto_expandido(r, f, l))
        o.append(f'<h2 class="hora-titulo" id="ord-{ficheiro}">'
                 f'{HORA_EM_LATIM.get(hora, hora)}</h2>')
        o.append(_peca('', '\n'.join(corpo)))
    return '\n'.join(o)


def parte_psalterium(r, f):
    """Domingo a Sabado, as oito horas: a salmodia ferial com as suas
    antifonas. E aqui que se abre para rezar o oficio do dia da semana."""
    import salmodia
    o = []
    for dow, nome in enumerate(DIAS_DA_SEMANA):
        o.append(f'<h2 class="parte-titulo" id="ps-{dow}">'
                 f'<span class="marca">§Aps-{dow}§</span>{nome}</h2>')
        for hora in HORAS:
            ancora = f'ps-{dow}-{hora}'
            o.append(f'<h3 class="hora-titulo" id="{ancora}">'
                     f'<span class="marca">§A{ancora}§</span>'
                     f'{nome} · {HORA_EM_LATIM[hora]}</h3>')
            try:
                if hora in ('Laudes', 'Vespera'):
                    pares = salmodia.salmodia_maior(r, hora, dow, 'Latin',
                                                    None, 1, 3)
                elif hora == 'Matutinum':
                    pares = _psalmodia_matutina(r, dow)
                else:
                    ant, chamadas = salmodia.salmodia_menor(r, hora, dow,
                                                            'Latin', None)
                    pares = [(ant, chamadas)]
            except Exception as erro:
                o.append(_peca('', f'/:falhou: {erro!r}:/'))
                continue
            for ant, chamadas in pares:
                if ant:
                    o.append(_peca('', f'Ant. {ant}', 'antifona'))
                for chamada in chamadas:
                    args = f.argumentos(chamada)
                    f.e.psalmnum = 0
                    corpo = f.expandir(f.psalm(*(args + ['Latin', ant])),
                                       'Latin')
                    o.append(_peca('', corpo, 'salmo'))
    return '\n'.join(o)


def _psalmodia_matutina(r, dow):
    """Os nove salmos de Matinas do dia da semana, com as suas antifonas."""
    secoes = r.setupstring('Latin', 'Psalterium/Psalmi/Psalmi matutinum.txt')
    linhas = [l for l in (secoes.get(f'Day{dow}') or '').split('\n') if l.strip()]
    fora = []
    for l in linhas[:15]:
        ant, _, salmos = l.partition(';;')
        if not salmos.strip():
            continue
        chamadas = []
        partes = [p for p in salmos.split(';') if p.strip()]
        for k, p in enumerate(partes):
            p = re.sub(r'[(\-]', ',', p).replace(')', '')
            if k < len(partes) - 1:
                p = '-' + p
            chamadas.append(f'&psalm({p})')
        fora.append((re.sub(r'~?\n', ' ', ant), chamadas))
    return fora


# As posicoes que ficaram mesmo sem nome. Ficam anotadas: saltar em
# silencio foi o que escondeu a Assuncao durante tres sessoes.
SEM_NOME = []


def parte_de_posicoes(r, f, lista, prefixo, titulo_de, folios=None):
    """Uma parte feita de posicoes: o Proprio do Tempo, o dos Santos, o
    Comum. Cada posicao imprime SO o que lhe e proprio."""
    o = []
    for pos in lista:
        try:
            dia = Dia(r, f'{pos}.txt', VERSAO)
        except (FileNotFoundError, OSError):
            continue
        # O nome do oficio. O [Officium] e a primeira escolha, mas NAO
        # existe em disco em ficheiro nenhum: e seccao montada, e onde
        # nao se monta o nome esta no PRIMEIRO CAMPO do [Rank] —
        # 'In Assumptione Beatae Mariae Virginis;;Duplex I classis...'.
        # Sem este recurso o livro saltava 74 posicoes SEM DIZER NADA, e
        # entre elas a Assuncao, a Epifania e o dia da Oitava do Natal.
        nome = (dia.secoes.get('Officium') or '').strip().split('\n')[0]
        if not nome:
            nome = (dia.secoes.get('Rank') or '').split(';;')[0].strip()
            nome = nome.split('\n')[0]
        if not nome:
            SEM_NOME.append(pos)
            continue
        ancora = prefixo + re.sub(r'[^\w]', '', pos.split('/')[1])
        corpo = []
        for grupo, pecas in PECAS_DA_POSICAO:
            bloco = []
            for seccao, rotulo in pecas:
                bruto = dia.secoes.get(seccao)
                if not (bruto and bruto.strip()):
                    continue
                bloco.append(_peca(rotulo, texto_expandido(r, f, bruto),
                                   genero_da_seccao(seccao)))
            bloco = [b for b in bloco if b]
            if bloco:
                if grupo:
                    corpo.append(f'<p class="grupo">{grupo}</p>')
                corpo.extend(bloco)
        # A remissao: o que a posicao nao imprime, diz onde esta. O
        # Saltério vai sem numero — e a excepcao que a regra permite,
        # porque toda a gente sabe onde ele fica. O Comum vai com numero.
        campos = (dia.secoes.get('Rank') or '').split(';;')
        campo = campos[3] if len(campos) > 3 else ''
        # O \b evita apanhar o 'ex' de 'Duplex II classis'.
        achado = REMISSAO_AO_COMUM.search(campo)
        if achado and prefixo != 'c-':
            alvo = 'c-' + re.sub(r'[^A-Za-z0-9]', '', achado.group(1))
            # O numero so entra quando ja se souber em que folio o Comum
            # caiu. Na primeira passagem sai a remissao curta; na segunda,
            # com o numero entre colchetes.
            n = (folios or {}).get(alvo.lower())
            numero = f' [{n}]' if n else ''
            corpo.append(f'<a class="remissao" href="#{alvo}">'
                         f'Cetera ut in Communi{numero}</a>')
        # A remissao ao CORPO DO LIVRO — 'vide Sancti/01-01'. Estas sao
        # as caras: o Proprio do Tempo e o dos Santos partilham a
        # sequencia corrida e so sabem o seu folio depois da costura, ao
        # contrario do Comum e do Salterio, que tem numeracao propria.
        for achado_c in REMISSAO_AO_CORPO.finditer(campo):
            parte_alvo, pos_alvo = achado_c.group(1), achado_c.group(2)
            pre = 't-' if parte_alvo.lower() == 'tempora' else 's-'
            alvo_c = pre + re.sub(r'[^\w]', '', pos_alvo)
            if alvo_c == ancora:
                continue
            n = (folios or {}).get(alvo_c)
            corpo.append(f'<a class="remissao" href="#{alvo_c}">'
                         f'Officium ut supra{f" [{n}]" if n else ""}</a>')

        if prefixo in ('t-', 's-'):
            # O ALVO do «ut in Psalterio» depende do dia da semana, e os
            # dois Proprios nao estao em pe de igualdade:
            #
            #   - no TEMPO o dia esta fixo e vem no proprio nome da
            #     posicao — 'Adv1-0' e o domingo, 'Adv1-3' a quarta —, e
            #     por isso o numero pode escrever-se.
            #   - nos SANTOS o dia varia com o ano. Sao Lourenco cai numa
            #     feria diferente em cada ano, e a salmodia e a da feria
            #     corrente. Num livro perpetuo esse folio NAO EXISTE: a
            #     remissao aponta a abertura do Salterio e quem reza vai
            #     ao seu dia. E o que o breviario impresso faz.
            alvo = 'ps-0'
            if prefixo == 't-':
                dia = re.search(r'-([0-6])$', pos or '')
                if dia:
                    alvo = f'ps-{dia.group(1)}'
            n = (folios or {}).get(alvo)
            numero = f' [{n}]' if n else ''
            corpo.append(f'<a class="remissao" href="#{alvo}">'
                         f'Psalmi ut in Psalterio{numero}</a>')
        if not corpo:
            continue
        o.append(f'<section class="posicao" id="{ancora}">')
        # A marca vai invisivel — corpo de 1 pixel, cor transparente. Fica
        # no texto do PDF, para a passagem seguinte a ler, e nao aparece
        # na pagina impressa.
        o.append(f'<h3 class="posicao-titulo">'
                 f'<span class="marca">\u00a7A{ancora}\u00a7</span>'
                 f'{_html.escape(titulo_de(pos, nome))}</h3>')
        o.extend(corpo)
        o.append('</section>')
    return '\n'.join(o)


# --------------------------------------------------------------------------
# A folha e a numeracao separada
# --------------------------------------------------------------------------

# Cada parte com numeracao propria comeca a contar do um outra vez, e o seu
# folio sai marcado com asterisco — como no breviario de 1942. E o que
# permitira, depois, partir o livro em quatro tomos sem recalcular remissao.
CSS_PERPETUO = """
.parte { break-before: right; }
.parte-titulo { column-span: all; text-align: center;
  font-size: calc(var(--corpo) * 1.7); font-variant: small-caps;
  letter-spacing: .08em; color: var(--vermelho); font-weight: normal;
  margin: 0 0 2.4mm; break-after: avoid; }
.hora-titulo { column-span: all; text-align: center;
  font-size: var(--titulo-seccao); font-variant: small-caps;
  letter-spacing: .06em; border-top: .4pt solid currentColor;
  border-bottom: .4pt solid currentColor; padding: .4mm 0;
  margin: 2mm 0 1mm; break-after: avoid; break-inside: avoid; }
.posicao-titulo { font-size: var(--titulo-seccao); font-variant: small-caps;
  letter-spacing: .04em; color: var(--vermelho); text-indent: 0;
  margin: 1.6mm 0 .6mm; break-after: avoid; font-weight: normal; }
.grupo { font-variant: small-caps; letter-spacing: .05em; text-indent: 0;
  color: var(--tinta); margin: 1mm 0 .3mm; break-after: avoid; }
.posicao { break-inside: auto; }
.remissao-curta { text-indent: 0; font-variant: small-caps;
  letter-spacing: .03em; margin: .4mm 0; }
.kalendarium, .sumario { column-span: none; width: 100%;
  border-collapse: collapse; font-size: calc(var(--corpo) * 0.95); }
.kalendarium td, .sumario td { padding: .1mm .6mm .1mm 0;
  vertical-align: top; }
.kalendarium td:first-child { white-space: nowrap; color: var(--vermelho); }
.sumario td.n { text-align: right; font-variant-numeric: tabular-nums; }
.rosto { column-span: all; text-align: center; padding-top: 26mm; }
.rosto-alto { font-variant: small-caps; letter-spacing: .18em;
  font-size: calc(var(--corpo) * 1.6); text-indent: 0; }
.rosto-grande { font-variant: small-caps; letter-spacing: .12em;
  font-size: calc(var(--corpo) * 3); color: var(--vermelho);
  text-indent: 0; margin: 2mm 0 6mm; }
.rosto-sub { font-style: italic; text-indent: 0; margin: 0 0 1mm; }
.rosto-rubrica { color: var(--vermelho); font-variant: small-caps;
  letter-spacing: .08em; text-indent: 0; margin-top: 6mm; }

/* As partes de numeracao propria: o contador volta a um e o folio leva
   asterisco. */
.numeracao-propria { counter-reset: page 1; }
.com-estrela { string-set: estrela "*"; }
.sem-estrela { string-set: estrela ""; }
"""


def folha(partes, corpo='7', primeiro_folio=1):
    import pdf as _pdf
    import livro
    css = (compor.CSS % {'corpo': corpo}) + livro.CSS_DO_LIVRO \
        + _pdf.CSS_DE_PAGINA + CSS_PERPETUO
    # o folio das partes de numeracao propria leva asterisco
    css = css.replace('content: counter(page);',
                      'content: string(estrela) counter(page);')
    # O contador comeca onde a parte comeca: um 'counter-reset' no corpo
    # e a unica forma que o WeasyPrint aceita para a PRIMEIRA pagina.
    css += ('\nbody { counter-reset: page '
            + str(primeiro_folio - 1) + '; }\n')
    o = ['<!doctype html><html lang="la"><head><meta charset="utf-8">',
         '<title>Breviarium Romanum</title>',
         f'<style>{css}</style></head><body>',
         '<div class="corpo latina">']
    o.extend(partes)
    o.append('</div></body></html>')
    return '\n'.join(o)


def parte(titulo, conteudo, ancora, propria=False):
    classes = 'parte com-estrela' if propria else 'parte sem-estrela'
    return (f'<section class="{classes}" id="{ancora}">'
            f'<h1 class="parte-titulo">{_html.escape(titulo)}</h1>'
            f'{conteudo}</section>')


# --------------------------------------------------------------------------
# A numeracao separada
# --------------------------------------------------------------------------
#
# MEDIDO, e por isso esta assim: o WeasyPrint nao reinicia o contador de
# paginas com 'counter-reset: page' num elemento — ignora-o — e com paginas
# nomeadas reinicia em TODAS as paginas dessa pagina nomeada, o que da a
# mesma pagina 1 vezes sem conta. Prova em tres partes de nove paginas:
#
#   counter-reset no elemento -> *1 *2 ... 10 11 ... +19 +20 ...
#   @page nomeada             -> *1 *1 *1 ... 1 1 1 ... +1 +1 +1
#
# A saida e compor CADA PARTE como documento seu, onde o contador comeca
# naturalmente em um, e cose-las no fim. E o que o breviario de 1942 faz
# de facto: sao cadernos com numeracao propria, encadernados juntos.

def parte_ficheiros(r, f, pasta, lista, prefixo):
    """Uma parte feita de ficheiros soltos — o Appendix, as Tabuas."""
    o = []
    for nome in lista:
        try:
            secoes = r.setupstring('Latin', f'{pasta}/{nome}.txt')
        except (FileNotFoundError, OSError):
            continue
        corpo = []
        for chave, bruto in secoes.items():
            if chave in NAO_SAO_TEXTO or not (bruto or '').strip():
                continue
            # No Apendice o '!' no principio da linha e chave de indice
            # do corpus, nao texto: o titulo ja vem impresso por cima
            # dela, e o sitio nao a mostra. Tira-se AQUI e nao no funil,
            # porque noutras partes o '!' marca referencia biblica, que e
            # para sair.
            bruto = re.sub(r'(?m)^\s*!.*$\n?', '', bruto or '')
            if not bruto.strip():
                continue
            corpo.append(_peca(chave if not chave.startswith('_') else '',
                               texto_expandido(r, f, bruto)))
        corpo = [c for c in corpo if c]
        if not corpo:
            continue
        o.append(f'<section class="posicao" id="{prefixo}{re.sub(r"[^\w]", "", nome)}">')
        o.append(f'<h3 class="posicao-titulo">{_html.escape(nome)}</h3>')
        o.extend(corpo)
        o.append('</section>')
    return '\n'.join(o)


def parte_texto_corrido(caminho, titulo_de_seccao=None):
    """Um ficheiro de texto do repositorio, impresso como esta — o Codigo
    de Rubricas, as Tabuas de precedencia. Sao latim corrido."""
    try:
        bruto = io.open(caminho, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''
    # Tambem aqui: o Codigo de Rubricas traz ';;' no texto cru, e sem
    # isto saiam impressos nas paginas 18 e 26.
    bruto = sem_dados_de_controlo(bruto)
    # As linhas comecadas por '!' sao chave de indice do corpus, nao
    # texto — o titulo ja vem impresso por cima delas. O sitio nao as
    # mostra; aqui tambem nao.
    bruto = re.sub(r'(?m)^\s*!.*$\n?', '', bruto)
    o = []
    for bloco in re.split(r'\n\s*\n', bruto):
        bloco = bloco.strip()
        if not bloco:
            continue
        primeira = bloco.split('\n')[0]
        titulo = (re.match(r'^(Titulus [IVXLC]+.*|[A-Z][A-Z ]{6,})$', primeira)
                  is not None)
        classe = 'grupo' if titulo else 'par'
        corpo = _html.escape(bloco).replace('\n', '<br>')
        o.append(f'<p class="{classe}">{corpo}</p>' if titulo
                 else f'<div class="par"><p>{corpo}</p></div>')
    return '\n'.join(o)


def parte_kalendarium(r, santos):
    """O calendario perpetuo dos Santos: dia, festa, classe."""
    linhas = []
    for pos in santos:
        d = pos.split('/')[1]
        m = re.match(r'^(\d\d)-(\d\d)', d)
        if not m:
            continue
        try:
            secoes = r.setupstring('Latin', f'{pos}.txt')
        except (FileNotFoundError, OSError):
            continue
        campos = (secoes.get('Rank') or '').split(';;')
        nome = (campos[0].strip()
                or (secoes.get('Officium') or '').strip().split('\n')[0])
        classe = campos[1].strip() if len(campos) > 1 else ''
        if not nome:
            continue
        linhas.append(f'<tr><td>{int(m.group(2))} {MESES[int(m.group(1))-1][:3]}'
                      f'</td><td>{_html.escape(nome)}</td>'
                      f'<td>{_html.escape(classe)}</td></tr>')
    return ('<table class="kalendarium">' + ''.join(linhas) + '</table>')


def folha_de_rosto():
    return ('<div class="rosto">'
            '<p class="rosto-alto">Breviarium</p>'
            '<p class="rosto-grande">Romanum</p>'
            '<p class="rosto-sub">ex decreto Sacrosancti Concilii Tridentini '
            'restitutum</p>'
            '<p class="rosto-sub">Summorum Pontificum cura recognitum</p>'
            '<p class="rosto-rubrica">cum Rubricis anni MCMLX</p>'
            '</div>')


def sumario(indice):
    linhas = ''.join(
        f'<tr><td>{_html.escape(t)}</td>'
        f'<td class="n">{e}{a}&ndash;{e}{b}</td></tr>'
        for t, e, a, b, _n in indice)
    return f'<table class="sumario">{linhas}</table>'


def construir_partes(corpo='7', folios=None):
    """Devolve [(nome, titulo, html, numeracao_propria)]."""
    ctx = contexto()
    r = Resolvedor(REPO, ctx)
    f = Funcoes(r, compor.estado_do_dia('', 0, None, None))
    tempo, santos, comuns = posicoes()

    def tit_tempo(pos, nome):
        return nome

    def tit_santo(pos, nome):
        d = pos.split('/')[1]
        m = re.match(r'(\d\d)-(\d\d)', d)
        data = f'{int(m.group(2))} {MESES[int(m.group(1)) - 1]}' if m else d
        return f'{data} — {nome}'

    def tit_comum(pos, nome):
        return nome

    appendix = sorted(x[:-4] for x in os.listdir(
        REPO / 'web/www/horas/Latin/Appendix') if x.endswith('.txt'))
    rubricas = REPO / 'web/www/horas/Help/Rubrics/rubrics.txt'
    tabellae = REPO / 'web/www/horas/Help/Rubrics/Tabellae.txt'

    return [
        ('rosto', '', folha_de_rosto(), True),
        ('rubricae', 'Rubricae Generales', parte_texto_corrido(rubricas), True),
        ('tabellae', 'Tabellae Occurrentiae et Concurrentiae',
         parte_texto_corrido(tabellae), True),
        ('kalendarium', 'Kalendarium', parte_kalendarium(r, santos), True),
        ('ordinarium', 'Ordinarium', parte_ordinarium(r, f), True),
        ('psalterium', 'Psalterium', parte_psalterium(r, f), True),
        ('tempore', 'Proprium de Tempore',
         parte_de_posicoes(r, f, tempo, 't-', tit_tempo, folios), False),
        ('sanctorum', 'Proprium Sanctorum',
         parte_de_posicoes(r, f, santos, 's-', tit_santo, folios), False),
        ('commune', 'Commune Sanctorum',
         parte_de_posicoes(r, f, comuns, 'c-', tit_comum, folios), True),
        ('appendix', 'Appendix',
         parte_ficheiros(r, f, 'Appendix', appendix, 'a-'), True),
    ]


def construir(saida='BREVIARIUM-latina-volume-unico', corpo='7',
              folios=None, so=None):
    """Compoe cada parte como documento seu e cose-as num volume.

    O Proprio do Tempo e o dos Santos partilham a mesma sequencia — sao o
    corpo do livro e correm um atras do outro, como no de 1942. As outras
    tres tem cada uma a sua, marcada com asterisco.
    """
    import pdf as _pdf
    import livro
    partes = construir_partes(corpo, folios)
    if so:
        partes = [x for x in partes if x[0] in so]
    ficheiros, indice = [], []
    folio_corpo, fisica = 1, 1
    for nome, titulo, html, propria in partes:
        # O corpo do livro (Tempore + Sanctorum) continua a contagem;
        # cada parte de numeracao propria comeca do um.
        inicio = 1 if propria else folio_corpo
        pagina_html = folha([parte(titulo, html, f'p-{nome}', propria)],
                            corpo, primeiro_folio=inicio)
        cam = RAIZ / f'{saida}-{nome}.html'
        io.open(cam, 'w', encoding='utf-8').write(pagina_html)
        pdf_da_parte = cam.with_suffix('.pdf')
        n = _pdf.imprimir(cam, pdf_da_parte)
        indice.append((titulo, '*' if propria else '', inicio, inicio + n - 1, n,
                       nome, fisica, fisica + n - 1))
        fisica += n
        if not propria:
            folio_corpo += n
        ficheiros.append(pdf_da_parte)
        print(f'   {titulo:22} {"*" if propria else " "}{inicio}–'
              f'{"*" if propria else ""}{inicio + n - 1}  ({n} páginas)',
              flush=True)
    inteiro = RAIZ / f'{saida}.pdf'
    total = livro.juntar(ficheiros, inteiro)
    # O indice em ficheiro, para quem verifica. Que pagina pertence a que
    # parte NAO SE ADIVINHA lendo a pagina: o Salterio, por exemplo, nunca
    # imprime a palavra 'Psalterium' — abre logo em 'Dominica'. Quem
    # compos e que sabe, e escreve-o aqui.
    with io.open(RAIZ / f'{saida}-indice.tsv', 'w', encoding='utf-8') as fh:
        fh.write('parte\ttitulo\tpropria\tfolio_de\tfolio_ate'
                 '\tfisica_de\tfisica_ate\n')
        for tit, marca, de, ate, n, nome, fde, fate in indice:
            fh.write(f'{nome}\t{tit}\t{1 if marca else 0}'
                     f'\t{de}\t{ate}\t{fde}\t{fate}\n')
    return inteiro, total, indice


if __name__ == '__main__':
    import time
    t0 = time.time()
    caminho, total, indice = construir()
    print(f'escrito {caminho.name}: '
          f'{caminho.stat().st_size / 1e6:.0f} MB, {total} páginas, '
          f'{time.time() - t0:.0f}s')
