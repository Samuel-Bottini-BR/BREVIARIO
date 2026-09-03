"""
Leitor dos arquivos-fonte do Divinum Officium.

Porta fielmente o motor de condicionais do repositorio
(web/cgi-bin/DivinumOfficium/SetupString.pl) para Python, para que a
composicao do livro nao dependa do Perl nem do site.

Tres coisas que este modulo garante, e que sao os erros ja cometidos
antes neste projeto:

  1. Nenhuma linha de controle sai na saida.
  2. Nunca se cai para o ingles. Onde falta portugues, marca-se a lacuna.
  3. As condicoes de rubrica sao avaliadas, nao ignoradas.
"""

import re
from pathlib import Path

# --------------------------------------------------------------------------
# Escopos, como em SetupString.pl
# --------------------------------------------------------------------------

SCOPE_NULL = 0    # nenhum
SCOPE_LINE = 1    # uma linha
SCOPE_CHUNK = 2   # ate a proxima linha em branco
SCOPE_NEST = 3    # ate uma condicao de forca maior ou igual

COND_NOT_YET_AFFIRMATIVE = 0
COND_AFFIRMATIVE = 1
COND_DUMMY_FRAME = 2

# Palavras de parada e seus pesos. As quatro primeiras trazem escopo
# implicito para tras.
STOPWORD_WEIGHTS = {
    'sed': 1, 'vero': 1, 'atque': 2, 'attamen': 3,
    'si': 0, 'deinde': 1,
}
BACKSCOPED_STOPWORDS = {'sed', 'vero', 'atque', 'attamen'}

_STOPWORDS_RE = '|'.join(STOPWORD_WEIGHTS)

_SCOPE_RE = r"""
    (?:\bloco\s+(?:hu[ij]us\s+versus|horum\s+versuum)\b)?
    \s*
    (?:
      \b
      (?:
        (?:dicitur|dicuntur)(?:\s+semper)?
        |
        (?:(?:hic|hoc)\s+versus\s+)?omittitur
        |
        (?:(?:h(?:æ|ae)c|hi)\s+versus\s+)?omittuntur
      )
      \b
    )?
"""

CONDITIONAL_RE = re.compile(
    r'\(\s*(?:(' + _STOPWORDS_RE + r')\b)*(.*?)(' + _SCOPE_RE + r')?\s*\)',
    re.IGNORECASE | re.VERBOSE,
)

LINE_CONDITIONAL_RE = re.compile(
    r'^\s*' + CONDITIONAL_RE.pattern + r'\s*(.*)$',
    re.IGNORECASE | re.VERBOSE,
)

SECTION_RE = re.compile(r'^\s*\[([^\]\n]+)\]\s*(.*)$')
BLANKLINE_RE = re.compile(r'^\s*_?\s*$')


# --------------------------------------------------------------------------
# Avaliacao de condicoes
# --------------------------------------------------------------------------

class Contexto:
    """O estado do dia contra o qual as condicoes sao avaliadas.

    Para o volume unico e perpetuo, o que importa e a versao das rubricas
    e a hora. Os campos que dependem do dia do ano ficam aqui para quando
    o gerador do Ordo os preencher.
    """

    def __init__(self, version='Rubrics 1960 - 1960', hora='', tempore='',
                 dayofweek=0, commune='', votive='', officio='', die='',
                 month=0, dioecesis=''):
        self.version = version
        self.hora = hora
        self.tempore = tempore
        self.dayofweek = dayofweek
        self.commune = commune
        self.votive = votive
        self.officio = officio
        self.die = die
        self.month = month
        self.dioecesis = dioecesis
        # Condicoes que nao soubemos avaliar, para nao falhar em silencio.
        self.nao_avaliadas = []

    def sujeito(self, nome):
        return {
            'rubricis': self.version, 'rubrica': self.version,
            'communi': self.version,
            'tempore': self.tempore,
            'die': self.die,
            'feria': str(self.dayofweek + 1),
            'commune': self.commune,
            'votiva': self.votive,
            'officio': self.officio,
            'ad': self.hora,
            'mense': str(self.month),
            'dioecesis': self.dioecesis,
        }.get(nome.lower())


PREDICADOS = {
    'tridentina': lambda s: bool(re.search(r'Trident', s)),
    'monastica': lambda s: bool(re.search(r'Monastic', s)),
    'innovata': lambda s: bool(re.search(r'2020 USA|NewCal', s, re.I)),
    'innovatis': lambda s: bool(re.search(r'2020 USA|NewCal', s, re.I)),
    'paschali': lambda s: bool(re.search(r'Pasch[æa]|Ascensionis|Octava Pentecostes', s, re.I)),
    'post septuagesimam': lambda s: bool(re.search(r'Septua|Quadra|Passio', s, re.I)),
    'prima': lambda s: s.strip() == '1',
    'secunda': lambda s: s.strip() == '2',
    'tertia': lambda s: s.strip() == '3',
    'longior': lambda s: s.strip() == '1',
    'brevior': lambda s: s.strip() == '2',
    'summorum pontificum': lambda s: bool(re.search(r'194[2-9]|195[45]|196', s)),
    'feriali': lambda s: bool(re.search(r'feria|vigilia', s, re.I)),
}

SUJEITOS_CONHECIDOS = {
    'rubricis', 'rubrica', 'tempore', 'missa', 'communi', 'die', 'feria',
    'commune', 'votiva', 'officio', 'ad', 'mense', 'dioecesis',
    'tonus', 'toni',
}


def vero(condicao, ctx):
    """Avalia uma condicao. 'aut' liga mais forte que 'et'."""
    condicao = (condicao or '').strip()
    if not condicao:
        return True  # condicao vazia e verdadeira, como no original

    for alternativa in re.split(r'\baut\b', condicao):
        partes = re.split(r'\b(et|nisi)\b', alternativa)
        negacao = False
        satisfeita = True
        for parte in partes:
            if parte in ('et', 'nisi'):
                if parte == 'nisi':
                    negacao = True
                continue
            parte = re.sub(r'\s+', ' ', parte.strip())
            if not parte:
                continue

            campos = parte.split(' ', 1)
            if len(campos) == 2:
                sujeito, predicado = campos
            else:
                sujeito, predicado = '', campos[0]

            # Predicado de varias palavras com sujeito implicito
            if sujeito and sujeito.lower() not in SUJEITOS_CONHECIDOS:
                predicado = f'{sujeito} {predicado}'
                sujeito = ''
            sujeito = sujeito or 'tempore'

            valor = ctx.sujeito(sujeito)
            if valor is None:
                ctx.nao_avaliadas.append(parte)
                satisfeita = False
                break

            fn = PREDICADOS.get(predicado.lower())
            if fn is None:
                # Predicado desconhecido: trata-se como expressao regular
                pred_txt = predicado
                fn = lambda s, p=pred_txt: bool(re.search(p, s, re.I))

            if bool(fn(valor)) == negacao:
                satisfeita = False
                break

        if satisfeita:
            return True
    return False


def parse_conditional(stopwords, condicao, escopo, ctx):
    stopwords = (stopwords or '').lower()
    escopo = escopo or ''

    forca = sum(STOPWORD_WEIGHTS.get(w, 0) for w in stopwords.split())
    resultado = vero(condicao, ctx)

    backscope_implicito = any(w in BACKSCOPED_STOPWORDS for w in stopwords.split())

    if re.search(r'versuum|omittuntur', escopo, re.I):
        backscope = SCOPE_NEST
    elif re.search(r'versus|omittitur', escopo, re.I):
        backscope = SCOPE_CHUNK
    elif not re.search(r'semper', escopo, re.I) and backscope_implicito:
        backscope = SCOPE_LINE
    else:
        backscope = SCOPE_NULL

    if re.search(r'omittitur|omittuntur', escopo, re.I):
        forwardscope = SCOPE_NULL
    elif re.search(r'dicuntur', escopo, re.I):
        forwardscope = SCOPE_CHUNK if backscope == SCOPE_CHUNK else SCOPE_NEST
    else:
        forwardscope = (SCOPE_CHUNK if backscope in (SCOPE_CHUNK, SCOPE_NEST)
                        else SCOPE_LINE)

    return forca, resultado, backscope, forwardscope


def process_conditional_lines(linhas, ctx):
    """Porta de process_conditional_lines de SetupString.pl."""
    saida = []
    pilha = [[COND_AFFIRMATIVE, SCOPE_NEST]]
    deslocamentos = [-1]

    for linha_original in linhas:
        linha = linha_original
        m = LINE_CONDITIONAL_RE.match(linha)
        if m:
            stopwords, condicao, escopo, resto = m.group(1), m.group(2), m.group(3), m.group(4)
            forca, resultado, backscope, forwardscope = parse_conditional(
                stopwords, condicao, escopo, ctx)
            linha = resto

            if pilha[-1][0] == COND_AFFIRMATIVE or forca >= len(deslocamentos) - 1:
                if forca >= len(deslocamentos) - 1:
                    pilha = []
                elif forca >= (len(deslocamentos) - 1) - (len(pilha) - 1):
                    # Perl: $#conditional_stack = $#offsets - $strength - 1
                    # O comprimento resultante pode ser zero; nunca negativo.
                    novo_tam = max((len(deslocamentos) - 1) - forca, 0)
                    del pilha[novo_tam:]

                if resultado:
                    cerca = (deslocamentos[forca]
                             if len(deslocamentos) - 1 >= forca else -1)
                    if backscope == SCOPE_LINE:
                        if len(saida) - 1 > cerca:
                            saida.pop()
                    elif backscope == SCOPE_CHUNK:
                        while len(saida) - 1 > cerca and not BLANKLINE_RE.match(saida[-1]):
                            saida.pop()
                        while len(saida) - 1 > cerca and BLANKLINE_RE.match(saida[-1]):
                            saida.pop()
                    elif backscope == SCOPE_NEST:
                        del saida[cerca + 1:]

                if forwardscope == SCOPE_NULL:
                    forwardscope = SCOPE_NEST
                    resultado = True

                if resultado:
                    for i in range(forca + 1):
                        while len(deslocamentos) <= i:
                            deslocamentos.append(-1)
                        deslocamentos[i] = len(saida) - 1

                while forca < (len(deslocamentos) - 1) - (len(pilha) - 1) - 1:
                    pilha.append([COND_DUMMY_FRAME, forwardscope])

                pilha.append([COND_AFFIRMATIVE if resultado
                              else COND_NOT_YET_AFFIRMATIVE, forwardscope])

            if not linha:
                continue

        if linha.startswith('~'):
            linha = linha[1:]

        if pilha[-1][0] == COND_AFFIRMATIVE:
            saida.append(linha)

        # Fim de escopo depois desta linha. Ao sair de um quadro, saem
        # junto os quadros-fantasma; se a pilha esvaziar, repoe-se um
        # quadro sempre-verdadeiro, para o teste seguir uniforme.
        while pilha and (
            pilha[-1][1] == SCOPE_LINE
            or (pilha[-1][1] == SCOPE_CHUNK and BLANKLINE_RE.match(linha))
        ):
            while True:
                pilha.pop()
                if not (pilha and pilha[-1][0] == COND_DUMMY_FRAME):
                    break
            if not pilha:
                pilha.append([COND_AFFIRMATIVE, SCOPE_NEST])

    return saida


# --------------------------------------------------------------------------
# Leitura de arquivo em secoes
# --------------------------------------------------------------------------

def ler_arquivo(caminho, ctx):
    """Le um arquivo-fonte e devolve {secao: [linhas]}.

    Secoes cuja condicao de rubrica e falsa sao descartadas.
    """
    caminho = Path(caminho)
    texto = caminho.read_text(encoding='utf-8-sig')
    linhas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    secoes = {}
    chave = '__preambulo'
    usar = True

    for linha in linhas:
        m = SECTION_RE.match(linha) if linha.startswith('[') else None
        if m:
            nome, resto = m.group(1), m.group(2).strip()
            condicao = None
            if resto:
                mc = CONDITIONAL_RE.match(resto)
                if mc:
                    condicao = (mc.group(1), mc.group(2), mc.group(3))
            if condicao is None or vero(condicao[1], ctx):
                usar = True
                chave = nome
                secoes[chave] = []
            else:
                usar = False
        elif usar:
            secoes.setdefault(chave, []).append(linha)

    return {k: process_conditional_lines(v, ctx) for k, v in secoes.items()}


# --------------------------------------------------------------------------
# Filtro de linhas de controle
# --------------------------------------------------------------------------

SECOES_DE_CONTROLE = {'Officium', 'Rank', 'Rule', 'Name', 'Comment', 'Numbers'}


def e_linha_de_controle(linha):
    """Verdadeiro para o que nunca pode sair impresso."""
    if ';;' in linha:
        return True
    nu = linha.strip()
    if nu.startswith('[') and nu.endswith(']'):
        return nu[1:-1].split()[0] in SECOES_DE_CONTROLE if nu[1:-1].split() else False
    return False


def limpar(linhas):
    """Remove linhas de controle. Devolve (limpas, descartadas)."""
    limpas, descartadas = [], []
    for l in linhas:
        (descartadas if e_linha_de_controle(l) else limpas).append(l)
    return limpas, descartadas
