"""
As funcoes de script do Divinum Officium — as remissoes que comecam por '&'.

Ao contrario do '@' e do '$', estas nao apontam para texto: sao CODIGO.
Decidem, por exemplo, se se diz 'Dominus vobiscum' ou 'Domine exaudi'
conforme haja sacerdote, ou se o Gloria se omite no Triduo Sacro.

Porta de web/cgi-bin/horas/horasscripts.pl.

DUAS SIMPLIFICACOES DELIBERADAS, e a razao de cada uma:

1. O canto (gabc). Varias funcoes tem ramos so para o idioma 'Latin-gabc',
   que serve a notacao musical. O nosso livro e texto, nao partitura, e
   nunca pede esse idioma. Esses ramos ficam de fora, e o codigo diz onde.

2. As familias monastica, cisterciense e dominicana. O nosso breviario e
   romano. Onde o original ramifica para elas, seguimos so o ramo romano.

Nenhuma das duas altera o resultado para o nosso caso. Estao aqui escritas
para que se saiba o que falta, se um dia o projeto mudar de ambito.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class EstadoDoDia:
    """O que as funcoes precisam de saber sobre o dia a rezar.

    Enquanto nao houver o calculo do calendario, isto e preenchido a mao.
    """

    def __init__(self, dayname='', hora='', version='Rubrics 1960 - 1960',
                 dayofweek=0, vespera=0, rule='', winner='', rank=0,
                 priest=False, cwinner='', commune='', secoes_vencedor=None):
        self.dayname = dayname     # 'Quad6-5', 'Pasc0-1', 'Pent16-0'...
        self.hora = hora
        self.version = version
        self.dayofweek = dayofweek  # 0 = domingo, como no original
        self.vespera = vespera      # 1 = I Vesperas, 3 = II Vesperas
        self.rule = rule
        self.winner = winner
        self.rank = rank
        self.priest = priest
        self.cwinner = cwinner
        self.commune = commune
        # As seccoes do oficio vencedor do dia, ja resolvidas. E o %winner
        # do original, e e daqui que o '&special' tira o texto.
        self.secoes_vencedor = secoes_vencedor or {}
        self.precesferiales = False
        self.litaniaflag = False
        # O contador de salmos da hora — o '[3]' que sai a seguir ao titulo
        # 'Psalmus 62'. No original e global e nunca se reinicia dentro de
        # uma pagina; aqui reinicia-se por hora, chamando reiniciar_salmos.
        self.psalmnum = 0
        # Fica verdadeiro quando a antifona cobriu o primeiro versiculo
        # todo: quem monta a pagina poe entao o sinal tambem na antifona.
        self.sinal_na_antifona = False
        # O que nao soubemos calcular, para nao falhar em silencio.
        self.avisos = []

    def reiniciar_salmos(self):
        self.psalmnum = 0


# --------------------------------------------------------------------------
# Como se apresentam os versiculos.
#
# Sao os mesmos valores de horas.setup, que e o que o site usa por omissao,
# e portanto o que a decisao 2.12 — 'quero que esteja como esta no divinum
# officium' — manda seguir. Ficam aqui como parametro, nao escondidos no
# meio do codigo, porque a edicao impressa pode vir a querer outra coisa.
# --------------------------------------------------------------------------

NONUMBERS = False     # 0: os numeros de versiculo saem
NOINNUMBERS = True    # 1: sai a letra de subversiculo e a numeracao interna

# Como no site: 'noflexa=1', estilo Breviarium Romanum. O '‡' passa a
# marcar a divisao do versiculo, o asterisco muda para o lugar dele e o
# '†' desaparece.
#
# Regra permanente (decisao 2.18): copia-se o site em tudo — texto,
# sinais, pontuacao, o que aparece e o que nao aparece. A aparencia do
# livro decide-se no fim, sobre provas impressas, e e so mudar aqui.
NOFLEXA = True

# O '[3]' que o site poe a seguir a 'Psalmus 62'. E o contador dos salmos
# da hora, e serve para navegar no ecra — nenhum breviario impresso o traz.
# Fica ligado por omissao, que e o comportamento do original e o que o
# confronto contra o Perl exige; a composicao da pagina desliga-o.
CONTADOR_DE_SALMO = True


def depunct(item):
    """Porta de depunct, em horas.pl. Tira pontuacao e acentos para poder
    comparar uma palavra do salmo com a mesma palavra da antifona."""
    item = re.sub(r'[.,:?!"\';*()]', '', item)
    for de, para in (('áÁ', 'a'), ('éÉ', 'e'), ('íÍ', 'i'),
                     ('óöõÓÖÔ', 'o'), ('úüûÚÜÛ', 'u')):
        item = re.sub(f'[{de}]', para, item)
    item = item.replace('J', 'I').replace('j', 'i')
    return item.replace('æ', 'ae').replace('œ', 'oe')


def getantcross(psalmline, antline):
    """Porta de getantcross, em horas.pl.

    Poe o sinal '‡' no ponto do primeiro versiculo do salmo onde acaba a
    antifona — para quem reza saber ate onde vai o que ja disse. Se a
    antifona nao for o comeco do versiculo, devolve o versiculo intacto.
    """
    palavras_salmo = psalmline.split()
    palavras_ant = antline.split()
    original = psalmline
    saida = ''
    pind = aind = 0

    while aind < len(palavras_ant) and pind < len(palavras_salmo):
        item1 = depunct(palavras_salmo[pind])
        pind += 1
        if not item1:
            continue
        item2 = depunct(palavras_ant[aind])
        aind += 1
        if not item2:
            pind -= 1
            continue
        try:
            if not re.search(item2, item1, re.I):
                return original
        except re.error:
            return original
        saida += ' ' + palavras_salmo[pind - 1]

    # Se a antifona for mais comprida que o versiculo, nao se poe sinal.
    if aind < len(palavras_ant) and pind == len(palavras_salmo):
        return original

    while pind < len(palavras_salmo) and not depunct(palavras_salmo[pind]):
        saida += ' ' + palavras_salmo[pind]
        pind += 1

    saida += ' /:‡:/'
    if pind < len(palavras_salmo):
        saida += ' ' + ' '.join(palavras_salmo[pind:])
    # Devolve-se com o espaco a frente, como no original. O espaco a mais
    # que isso produz na linha nao se ve: o HTML e o PDF juntam espacos.
    return saida


def tratar_versiculos(linhas):
    """Porta de handleverses, so o ramo do texto.

    Os ramos do canto (gabc) ficam de fora — ver a nota de cabecalho deste
    ficheiro. Sao mais de cento e cinquenta linhas de ajuste de neumas que
    nunca se aplicam a texto: todos os padroes exigem parenteses de notacao
    do genero '(gh gr)', que num salmo nao aparecem.

    O que sobra e o que da a pagina o seu aspecto:
      - a letra de subversiculo e a numeracao interna saem
      - o numero de versiculo passa a rubrica, entre '/:' e ':/'
      - o que estiver entre parenteses passa a rubrica
      - a flexa desaparece, no estilo do Breviarium Romanum
    """
    fora = []
    for l in linhas:
        if NONUMBERS:
            l = re.sub(r'^(?:\d+:)?\d+[a-z]?\s*', '', l)
            l = re.sub(r'\s*\(\d+[a-z]?\)', '', l)
        elif NOINNUMBERS:
            l = re.sub(r'(\d)[a-z]', r'\1', l, count=1)
            l = re.sub(r'\(\d+[a-z]?\)', '', l, count=1)

        if not NONUMBERS:
            l = re.sub(r'^(?:\d+:)?\d+[a-z]?', lambda m: f'/:{m.group(0)}:/',
                       l, count=1)
            l = re.sub(r'\(\d+[a-z]?\)', lambda m: f'/:{m.group(0)}:/',
                       l, count=1)

        # Tudo o que venha entre parenteses e rubrica: '(fit reverentia)'.
        l = re.sub(r'(\(.*?\))', lambda m: f'/:{m.group(1)}:/', l, count=1)

        if NOFLEXA:
            l = re.sub(r'‡\s+(.*?)\*\s*', r'* \1', l)
            l = re.sub(r'†\s*', '', l)
        else:
            l = re.sub(r'\s‡\s', ' † ', l)
        fora.append(l)
    return fora


def septuagesima_vesp(e):
    """As II Vesperas do sabado antes da Septuagesima, em que o Alleluia
    se despede ate a Pascoa."""
    return (e.dayofweek == 6 and re.search(r'Vespera', e.hora, re.I)
            and ((e.vespera == 1 and re.search(r'Quadp1', e.dayname))
                 or (e.vespera == 3 and re.search(r'Quadp1-0', e.cwinner))))


def gloria_omitida_no_triduo(e):
    """Nos tres ultimos dias da Semana Santa o Gloria Patri omite-se ao
    fim dos salmos, em todas as horas."""
    return (bool(re.search(r'Quad6', e.dayname, re.I))
            and e.dayofweek > 3 and e.vespera != 1)


class Funcoes:
    """As funcoes '&'. Recebe o resolvedor, para poder chamar formula()."""

    def __init__(self, resolvedor, estado=None):
        self.r = resolvedor
        self.e = estado or EstadoDoDia()

    def _f(self, nome, lang):
        texto, _ = self.r.formula(nome, lang)
        return texto

    # ------------------------------------------------------------------ #

    def Alleluia(self, lang, *_):
        """Alleluia fora da Quaresma; 'Laus tibi' dentro dela.

        A formula traz as duas linhas; escolhe-se uma.
        """
        texto = self._f('Alleluia', lang)
        linhas = texto.split('\n')
        na_quaresma = (re.search(r'Quad', self.e.dayname, re.I)
                       and not septuagesima_vesp(self.e))
        i = 1 if na_quaresma else 0
        return linhas[i] if i < len(linhas) else (linhas[0] if linhas else '')

    def _gloria_omitida(self, lang):
        """Onde o Gloria se cala, o breviario NAO deixa um buraco: imprime
        a rubrica 'Gloria omittitur', para quem reza saber que a omissao e
        querida. Porta de adjust_refs, em horas.pl."""
        return f'/:{self.r.traduzir("Gloria omittitur", lang)}:/'

    def _cala_o_gloria_do_responsorio(self):
        """A condicao de adjust_refs para o '&Gloria1' e o '&Gloria2'."""
        return (bool(re.search(r'(Quad[56])', self.e.dayname, re.I))
                and not re.search(r'Sancti', self.e.winner, re.I)
                and not re.search(r'Gloria responsory', self.e.rule, re.I))

    def Gloria(self, lang, *_):
        if gloria_omitida_no_triduo(self.e):
            return self._gloria_omitida(lang)
        if re.search(r'Requiem gloria', self.e.rule, re.I):
            return self._f('Requiem', lang)
        return self._f('Gloria', lang)

    def Gloria1(self, lang, *_):
        """O Gloria dos responsorios. Omite-se no tempo da Paixao, salvo
        em festa de santo ou quando a regra do dia o mandar dizer."""
        if self._cala_o_gloria_do_responsorio():
            return self._gloria_omitida(lang)
        return self._f('Gloria1', lang)

    def Gloria2(self, lang, *_):
        """O Gloria do invitatorio."""
        if self._cala_o_gloria_do_responsorio():
            return self._gloria_omitida(lang)
        if re.search(r'Quad[56]', self.e.dayname, re.I):
            return ''
        if re.search(r'Requiem gloria', self.e.rule, re.I):
            return self._f('Requiem', lang)
        return self._f('Gloria', lang)

    def Dominus_vobiscum(self, lang, *_):
        """'Dominus vobiscum' se ha sacerdote; 'Domine exaudi' se nao.

        A formula 'Dominus' traz cinco linhas: as duas primeiras para o
        sacerdote, as duas seguintes para quem nao o e, e a quinta para
        depois das preces feriais.
        """
        linhas = self._f('Dominus', lang).split('\n')
        if self.e.priest:
            return '\n'.join(linhas[0:2])
        if not self.e.precesferiales:
            saida = '\n'.join(linhas[2:4])
        else:
            saida = linhas[4] if len(linhas) > 4 else ''
        self.e.precesferiales = False
        return saida

    def Dominus_vobiscum1(self, lang, *_):
        """Em Prima, depois das preces."""
        if (self.e.litaniaflag or self._preces('Dominicales et Feriales')) \
                and not self.e.priest:
            self.e.precesferiales = True
        return self.Dominus_vobiscum(lang)

    def Dominus_vobiscum2(self, lang, *_):
        """No oficio de defuntos."""
        if not self.e.priest:
            self.e.precesferiales = True
        return self.Dominus_vobiscum(lang)

    def Deus_in_adjutorium(self, lang, *_):
        """No original ha tres tons — ferial, festivo e solene — mas todos
        os ramos que nao o ferial exigem o idioma do canto. Em texto e
        sempre o ferial."""
        return self._f('Deus in adjutorium', lang)

    def Domine_labia(self, lang, *_):
        """No rito monastico diz-se tres vezes; no romano, uma."""
        return self._f('Domine labia', lang)

    def Divinum_auxilium(self, lang, *_):
        """Marca o versiculo e a resposta, e encurta a resposta para
        'Amen.' — no rito monastico ela e mais longa."""
        linhas = self._f('Divinum auxilium', lang).split('\n')
        if len(linhas) < 2:
            return '\n'.join(linhas)
        linhas[-2] = f'V. {linhas[-2]}'
        if not re.search(r'Monastic', self.e.version, re.I):
            linhas[-1] = re.sub(r'.*\. ', '', linhas[-1])
        linhas[-1] = f'R. {linhas[-1]}'
        return '\n'.join(linhas)

    def teDeum(self, lang, *_):
        return '\n!Te Deum\n' + self._f('Te Deum', lang)

    def mLitany(self, lang, *_):
        if self._preces('Dominicales'):
            return ''
        return '$Kyrie\n$pater secreto'

    def Benedicamus_Domino(self, lang, *_):
        """Na oitava da Pascoa acrescenta-se 'Alleluia, alleluia' em
        Laudes e Vesperas."""
        texto = self._f('Benedicamus Domino', lang)
        na_oitava = (re.search(r'(Laudes|Vespera)', self.e.hora, re.I)
                     and (re.search(r'Pasc0', self.e.dayname, re.I)
                          or septuagesima_vesp(self.e)))
        if not na_oitava:
            return texto
        # O alleluia entra em minusculas: vem a seguir a virgula, no meio
        # da frase, e nao a abre. E o 'lc()' do original.
        alleluia = self._f('Alleluia Duplex', lang).strip().lower()
        linhas = [l for l in texto.split('\n') if l.strip()]
        return '\n'.join(f'{l.rstrip(".")}, {alleluia}' if i < 2 else l
                         for i, l in enumerate(linhas))

    # ------------------------------------------------------------- special

    def special(self, nome, lang, *_):
        """Vai buscar uma peca ao oficio vencedor do dia.

        So o oficio de 2 de Novembro — Comemoracao dos Fieis Defuntos — a
        usa, e usa-a quinze vezes: sao tres oficios completos dentro do
        mesmo ficheiro, e cada um vai buscar ao proprio ficheiro a sua
        oracao e a sua conclusao.
        """
        texto = self.e.secoes_vencedor.get(nome)
        if texto is not None:
            return texto.rstrip() + '\n'
        if nome.startswith('#'):
            # O original manda isto a maquina que monta a hora inteira —
            # o Martirologio, que e um bloco proprio. Fora do ambito de
            # uma funcao de script.
            self.e.avisos.append(f'&special({nome}) e um bloco de hora, '
                                 f'nao uma peca')
            return f'&special({nome})'
        self.e.avisos.append(f'&special({nome}): o oficio do dia nao tem '
                             f'essa seccao')
        return f'{nome} is missing'

    # --------------------------------------------------------------- salmos

    # Os canticos evangelicos e o Quicumque nao levam contador.
    SEM_CONTADOR = range(231, 234)

    def psalm(self, *a):
        """O texto de um salmo, com titulo, recorte de versiculos e Gloria.

        Porta de 'sub psalm', em horasscripts.pl. A funcao mais usada de
        todas: e ela que poe salmo na pagina.

        As formas de chamada, como no original:
            &psalm(4)             o salmo inteiro
            &psalm(118,1,8)       so os versiculos 1 a 8
            &psalm(129,1)         inteiro, mas sem o Gloria no fim
        e o idioma — e a antifona, quando ha — vem por acrescimo, postos
        pelo despacho.

        Fica de fora o ramo do canto e o saltério de Pio XII: o primeiro
        porque o livro e de texto, o segundo por decisao registada.
        """
        a = list(a)
        psnum = str(a.pop(0)).strip()

        v1, v2, c1, c2 = 0, 1000, '', ''
        nogloria = False
        antline = None

        if len(a) < 3:
            if a and re.match(r'^1$', str(a[0])):
                nogloria = True
                a.pop(0)
            lang = a[0] if a else 'Latin'
            antline = a[1] if len(a) > 1 else None
        else:
            m = re.match(r'^(\d+)([a-z])?', str(a[0]))
            if m:
                v1, c1 = int(m.group(1)), m.group(2) or ''
            m = re.match(r'^(\d+)([a-z])?', str(a[1]))
            if m:
                v2, c2 = int(m.group(1)), m.group(2) or ''
            lang = a[2]
            antline = a[3] if len(a) > 3 else None

        # O '-' a frente do numero junta dois salmos sob um so Gloria. E
        # coisa do rito tridentino e do monastico; no romano de 1960 o
        # sinal existe nos ficheiros mas nao produz efeito.
        if psnum.startswith('-'):
            psnum = psnum[1:]

        num = self._numero(psnum)
        linhas = self._ler_salmo(psnum, lang)
        if not linhas:
            return f'Psalm{psnum} not found'

        titulo = f'{self.r.traduzir("Psalmus", lang)} {psnum}'
        if v1:
            titulo += f'({v1}{c1}-{v2}{c2})'
        fonte = ''

        # Os canticos — Benedictus, Magnificat, Nunc dimittis, os do
        # Antigo Testamento — trazem na primeira linha o proprio nome e a
        # passagem biblica: '(Canticum Simeonis * Luc. 2:29-32)'. Essa
        # linha e cabecalho, nao texto a rezar.
        if 150 < num < 300:
            m = re.match(r'\(?(.*?) \* (.*?)\)?\s*$', linhas.pop(0))
            if m:
                titulo, fonte = m.group(1), m.group(2)
                if v1:
                    fonte = re.sub(r'(?<=:).*', f'{v1}-{v2}', fonte)
            else:
                titulo, fonte = '', ''

        if v1:
            linhas = self._recortar(linhas, v1, c1, v2, c2)

        if antline and num != 232:
            linhas, coube_inteira = self._por_sinal_da_antifona(linhas, antline)
            # Quando a antifona cobre o primeiro versiculo por inteiro, o
            # sinal passa para o versiculo seguinte — e a propria antifona
            # leva um, a dizer que vai ate ao fim.
            if coube_inteira:
                self.e.sinal_na_antifona = True

        linhas = tratar_versiculos(linhas)

        if NONUMBERS or num == 234:
            linhas[0] = re.sub(r'^(?=[^\W\d_])', 'v. ', linhas[0])

        saida = f'!{titulo}'
        if num not in self.SEM_CONTADOR:
            self.e.psalmnum += 1
            if CONTADOR_DE_SALMO:
                saida += f' [{self.e.psalmnum}]'
        if fonte:
            saida += f'\n!{fonte}'
        saida += '\n' + '\n'.join(linhas) + '\n'

        # O salmo 210 e o 'Pater noster' — nao leva Gloria.
        if num != 210 and not nogloria:
            saida += '&Gloria\n'

        # No invitatorio o salmo 94 traz '$ant' nos pontos em que a
        # antifona se repete — sao cinco ao longo do salmo.
        if num == 94:
            saida = saida.replace('$ant', f'Ant. {antline or ""}'.rstrip())
        if psnum == '94C':
            saida = saida.replace('94C', '94')
        return saida

    @staticmethod
    def _numero(psnum):
        """O numero, para as comparacoes. '94C' vale 94, como no Perl."""
        m = re.match(r'^\s*(\d+)', str(psnum))
        return int(m.group(1)) if m else 0

    def _ler_salmo(self, psnum, lang):
        """O ficheiro do salmo, em linhas.

        Como em toda a parte, a cadeia e vernaculo -> latim, nunca o
        ingles, e a falta fica registada como lacuna.
        """
        rel = f'Psalterium/Psalmorum/Psalm{psnum}.txt'
        bruto = self.r.preambulo(lang, rel)
        if bruto is None and lang != 'Latin':
            bruto = self.r.preambulo('Latin', rel)
            if bruto is not None:
                self.r.lacunas.add((lang, rel, '__preamble'))
        if not bruto:
            return []
        linhas = bruto.replace('\r\n', '\n').split('\n')
        while linhas and not linhas[-1]:
            linhas.pop()          # o split do Perl deita fora os do fim
        return linhas

    @staticmethod
    def _recortar(linhas, v1, c1, v2, c2):
        """So os versiculos pedidos.

        A condicao e a do original, incluindo a sua parte estranha: uma
        linha sem numeracao e julgada pelo numero da linha ANTERIOR. E o
        que faz um titulo no meio do salmo — os que o salmo 118 tem —
        acompanhar o trecho a que pertence, em vez de sair sempre.
        """
        fora = []
        v, c = 0, ''
        for l in linhas:
            m = re.match(r'^(?:\d+:)?(\d+)([a-z])?', l)
            se_bate = False
            if m:
                v, c = int(m.group(1)), m.group(2) or ''
                se_bate = (v == v1 and (not c1 or c >= c1))
            if (se_bate
                    or (v == v2 and (not c2 or c <= c2))
                    or (v1 < v < v2)):
                fora.append(l)
        return fora

    @staticmethod
    def _por_sinal_da_antifona(linhas, antline):
        """O '‡' que marca, dentro do primeiro versiculo, onde acaba a
        antifona.

        Devolve (linhas, houve_sinal). Quando o sinal foi posto, a
        antifona leva um tambem, no fim — para quem reza ver de um lado ao
        outro ate onde vai o que ja disse.
        """
        if not linhas:
            return linhas, False
        linhas = list(linhas)
        m = re.match(r'^(\d+:\d+[a-z]? )(.*)', linhas[0])
        if not m:
            return linhas, False
        linhas[0] = m.group(1) + getantcross(m.group(2), antline)
        houve_sinal = '/:‡:/' in linhas[0]

        # Se o sinal calhou no fim da linha, passa para o comeco da
        # seguinte: no fim de linha nao se veria.
        if linhas[0].endswith('/:‡:/') and len(linhas) > 1:
            linhas[0] = linhas[0][:-len('/:‡:/')]
            linhas[1] = re.sub(r'^(\d+:\d+[a-z]? )', r'\1/:‡:/ ', linhas[1])
        return linhas, houve_sinal

    # --------------------------------------------------------- ainda nao

    def _preces(self, tipo):
        """Depende do calculo do dia, que ainda nao existe. Devolve falso e
        regista, para nao decidir em silencio."""
        self.e.avisos.append(f'preces({tipo}) ainda nao calculado')
        return False

    # ------------------------------------------------------------ despacho

    CHAMADA = re.compile(r'^\s*&([A-Za-z_][A-Za-z_0-9]*)'
                         r'(?:\((.*)\))?\s*$')

    @staticmethod
    def argumentos(s):
        """Porta de parse_script_arguments.

        A sintaxe e pobre de proposito: numeros e cadeias entre plicas,
        separados por virgulas que nao estejam dentro de plicas.
        """
        if s is None:
            return []
        fora = []
        for parte in re.split(r",(?=(?:[^']|'[^']*')*$)", s):
            m = re.search(r"'(.*)'|(-?\d+)", parte)
            fora.append((m.group(1) or m.group(2) or '') if m else '')
        return fora

    def expandir(self, texto, lang, antline=None, fundo=0):
        """Troca as linhas '&Nome' pelo que a funcao devolver.

        Como no original, o idioma junta-se sempre aos argumentos escritos
        no ficheiro, e a antifona a seguir, quando a hora a tiver — e dela
        que o salmo tira o sinal '‡'.
        """
        if fundo > 6 or '&' not in texto:
            return texto

        if antline:
            antline = re.sub(r'^\s*Ant\.\s*', '', antline, flags=re.I)

        saida, mudou = [], False
        for linha in texto.split('\n'):
            m = self.CHAMADA.match(linha)
            if not m:
                saida.append(linha)
                continue
            nome = m.group(1)
            fn = getattr(self, nome, None)
            if fn is None:
                self.e.avisos.append(f'&{nome} nao existe')
                saida.append(linha)
                continue
            args = self.argumentos(m.group(2)) + [lang]
            if antline:
                args.append(antline)
            try:
                saida.append(fn(*args))
                mudou = True
            except TypeError as erro:
                self.e.avisos.append(f'&{nome}: {erro}')
                saida.append(linha)

        resultado = '\n'.join(saida)
        return (self.expandir(resultado, lang, antline, fundo + 1) if mudou
                else resultado)
