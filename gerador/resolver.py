"""
O resolvedor de remissoes.

Os ficheiros-fonte do Divinum Officium nao contem o oficio: contem setas
para outros lugares. Este modulo segue essas setas e devolve o texto.

Exemplo real, o ficheiro de Santa Ines (Sancti/01-21.txt):

    [Ant Vespera]
    @:Ant Laudes

Depois de resolvido, a seccao 'Ant Vespera' traz as cinco antifonas de
Laudes por extenso.

Porta o setupstring de web/cgi-bin/DivinumOfficium/SetupString.pl. Como no
motor de condicionais, a fidelidade e conferida contra o Perl original
sobre o corpus inteiro — ver conferir_resolver.py.

DIFERENCA DELIBERADA EM RELACAO AO ORIGINAL: a lingua de reserva. O
Divinum Officium empilha portugues sobre INGLES sobre latim, e por isso
aparece ingles no meio do oficio portugues. Aqui a pilha e portugues sobre
latim, e as seccoes que so existem em latim ficam registadas como lacuna.
"""

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import (Contexto, process_conditional_lines, vero,
                    SECTION_RE, CONDITIONAL_RE)

RESOLVE_NONE = 0
RESOLVE_WHOLEFILE = 1
RESOLVE_ALL = 2

# @Ficheiro:Seccao:substituicoes — todos os tres pedacos sao opcionais.
# Sem ficheiro, e remissao para o proprio ficheiro; sem seccao, para a
# seccao onde a linha esta.
INCLUSAO = re.compile(
    # '\s*' e nao '[^\S\n]*': no original e \s, que inclui a quebra de
    # linha, e portanto engole tambem a linha em branco que venha antes.
    # Escrever '[^\S\n]*' deixava uma linha em branco a mais na saida.
    r'^\s*@'
    r'([^\n:]+)?'                 # 1 ficheiro
    r'(?::([^\n:]+?))?'           # 2 seccao
    r'[^\S\n\r]*'
    r'(?::(.*))?'                 # 3 substituicoes
    r'$\n?',
    re.M,
)

# As substituicoes vem em duas formas: 's/x/y/flags' ou faixas de linhas
# como '2-5', com '!' a inverter a selecao.
SUBST = re.compile(r'(?:s/(?P<s>[^/]*)/(?P<r>[^/]*)/(?P<f>[gism]*))'
                   r'|(?:(?P<n>!?)(?P<b>\d+)(?:-(?P<e>\d+))?)')


def _perl_para_python(padrao):
    """Converte o pouco de sintaxe Perl que aparece nas substituicoes."""
    return padrao.replace(r'\z', r'\Z')


def _expandir_troca(m, modelo):
    """Constroi o lado direito de uma substituicao a maneira do Perl.

    Tres coisas que o Python nao faz sozinho:
      $1        retrovisor (no Python seria \\1)
      \\l  \\u    passa a proxima letra a minuscula / maiuscula
      \\,        barra antes de pontuacao e so o caractere literal

    Sem a segunda, um '\\lEt' saia impresso como 'lEt' no meio de um
    responsorio.
    """
    def grupo(g):
        try:
            return m.group(int(g.group(1))) or ''
        except (IndexError, error_grupo):
            return ''

    saida = re.sub(r'\$(\d)', grupo, modelo)
    saida = re.sub(r'\\(\d)', grupo, saida)
    saida = saida.replace('\\n', '\n')
    saida = re.sub(r'\\l(.)', lambda g: g.group(1).lower(), saida)
    saida = re.sub(r'\\u(.)', lambda g: g.group(1).upper(), saida)
    saida = re.sub(r'\\L(.*?)(?:\\E|$)', lambda g: g.group(1).lower(), saida)
    saida = re.sub(r'\\U(.*?)(?:\\E|$)', lambda g: g.group(1).upper(), saida)
    return re.sub(r'\\(.)', r'\1', saida)


error_grupo = re.error


def aplicar_substituicoes(texto, subs):
    """Porta de do_inclusion_substitutions."""
    if not subs:
        return texto
    for m in SUBST.finditer(subs):
        if m.group('b'):
            ini = int(m.group('b')) - 1
            fim = int(m.group('e')) - ini if m.group('e') else 1
            # O split do Perl descarta os campos vazios do fim; o do
            # Python guarda-os. Sem isto, recortar 'linhas 2 a 6' trazia
            # junto uma linha em branco que no original nao existe.
            linhas = texto.split('\n')
            while linhas and linhas[-1] == '':
                linhas.pop()
            escolhidas = linhas[ini:ini + fim]
            restantes = linhas[:ini] + linhas[ini + fim:]
            texto = '\n'.join(restantes if m.group('n') else escolhidas) + '\n'
        else:
            bandeiras = 0
            f = m.group('f') or ''
            if 'i' in f:
                bandeiras |= re.I
            if 's' in f:
                bandeiras |= re.S
            if 'm' in f:
                bandeiras |= re.M
            try:
                modelo = m.group('r')
                texto = re.sub(_perl_para_python(m.group('s')),
                               lambda mm: _expandir_troca(mm, modelo),
                               texto,
                               count=0 if 'g' in f else 1,
                               flags=bandeiras)
            except re.error:
                pass          # substituicao que o Python nao entende: deixa
    return texto


class Resolvedor:
    """Le e resolve ficheiros do corpus, com cache por versao de rubricas."""

    def __init__(self, repo, ctx=None, vernaculo='Portugues'):
        self.base = Path(repo) / 'web/www/horas'
        self.ctx = ctx or Contexto()
        self.vernaculo = vernaculo
        self._cache = {}
        self.lacunas = set()       # (idioma, ficheiro, seccao) so em latim
        self.nao_resolvidas = []   # remissoes que ficaram por resolver
        self.formulas_toleradas = set()  # nomes que so bateram sem
                                         # ponto final ou sem acento

    # ---------------------------------------------------------------- leitura

    def _parse(self, caminho, titulo, chave_lang):
        """setupstring_parse_file: seccoes, condicionais, e o preenchimento
        do nome de ficheiro e da seccao nas linhas '@'."""
        texto = caminho.read_text(encoding='utf-8-sig')
        linhas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')

        secoes = {}
        chave = '__preamble'
        usar = True

        for linha in linhas:
            m = SECTION_RE.match(linha) if linha.startswith('[') else None
            if m:
                nome, resto = m.group(1), m.group(2).strip()
                cond = None
                if resto:
                    mc = CONDITIONAL_RE.match(resto)
                    if mc:
                        cond = mc.group(2)
                if cond is None or vero(cond, self.ctx):
                    usar, chave = True, nome
                    secoes[chave] = []
                else:
                    usar = False
            elif usar:
                # Preenche o que a remissao deixou implicito
                if linha.startswith('@') and chave != '__preamble':
                    def preencher(mm):
                        f = mm.group(1) or titulo
                        s = mm.group(2) or chave
                        t = f':{mm.group(3)}' if mm.group(3) else ''
                        return f'@{f}:{s}{t}\n'
                    linha = INCLUSAO.sub(preencher, linha + '\n').rstrip('\n')
                secoes.setdefault(chave, []).append(linha)

        return {k: '\n'.join(process_conditional_lines(v, self.ctx) + [''])
                for k, v in secoes.items()}

    def setupstring(self, lang, fname, resolver=RESOLVE_ALL):
        chave = (lang, fname)
        if chave not in self._cache:
            self._cache[chave] = self._carregar(lang, fname)
        secoes = dict(self._cache[chave])

        if resolver != RESOLVE_NONE:
            self._inclusoes_de_ficheiro(secoes, lang, fname)
            secoes.pop('__preamble', None)

        if resolver == RESOLVE_ALL:
            self._inclusoes_de_seccao(secoes, lang, fname)

        if 'Officium' in secoes:
            of = secoes['Officium'].rstrip()
            if 'Rank' in secoes:
                secoes['Rank'] = re.sub(r'^.*?;;', of + ';;', secoes['Rank'],
                                        count=1)
        return secoes

    # ------------------------------------------------- formulas fixas ($)

    # O sigilo pode trazer um qualificador: '$rubrica Examen',
    # '$Preces Dominicales'. Cada um vem de um ficheiro diferente.
    FICHEIRO_DA_FORMULA = {
        'rubrica': 'Psalterium/Common/Rubricae.txt',
        'Preces': 'Psalterium/Special/Preces.txt',
        '': 'Psalterium/Common/Prayers.txt',
    }

    CIFRAO = re.compile(r'^\s*\$((?:rubrica |Preces )?)(.+?)\s*$')

    def formula(self, nome, lang, qualificador=''):
        """Devolve (texto, veio_do_latim).

        A cadeia do original e idioma -> lingua de reserva -> latim -> o
        proprio nome. Aqui saltamos a lingua de reserva: e ela que poe
        ingles no meio do oficio portugues.
        """
        qual = qualificador.strip()
        ficheiro = self.FICHEIRO_DA_FORMULA[qual]

        # Nas preces o original repoe o prefixo antes de procurar: a linha
        # '$Preces dominicales Completorium' vai buscar a seccao chamada
        # 'Preces dominicales Completorium', com a palavra 'Preces'
        # incluida. Cortar o prefixo fazia falhar as catorze preces.
        if qual == 'Preces':
            nome = f'Preces {nome}'

        for tentativa, do_latim in ((lang, False), ('Latin', True)):
            if tentativa == lang and do_latim:
                continue
            try:
                secoes = self.setupstring(tentativa, ficheiro)
            except FileNotFoundError:
                continue

            texto = secoes.get(nome)
            if texto and texto.strip():
                if do_latim and lang != 'Latin':
                    self.lacunas.add((lang, ficheiro, nome))
                return texto.rstrip('\n'), do_latim

            # Busca tolerante. Nos ficheiros do repositorio ha 143
            # referencias no calendario geral que nao batem com nenhuma
            # seccao — quase todas por um ponto final a mais ('$Per
            # Dominum.') ou por um acento ('$Deo grátias'). O original
            # devolve o proprio nome quando nao encontra, o que numa
            # pagina impressa sairia como 'Per Dominum.' no lugar da
            # formula de encerramento. Aqui procura-se de novo sem o
            # ponto e sem acentos, e regista-se o caso.
            alt = self._nome_tolerante(nome, secoes)
            if alt:
                self.formulas_toleradas.add((ficheiro, nome, alt))
                if do_latim and lang != 'Latin':
                    self.lacunas.add((lang, ficheiro, alt))
                return secoes[alt].rstrip('\n'), do_latim

        self.nao_resolvidas.append((lang, ficheiro, nome, 'formula inexistente'))
        return nome, False

    @staticmethod
    def _sem_acento(s):
        s = (unicodedata.normalize('NFKD', s)
             .encode('ascii', 'ignore').decode('ascii').lower())
        # No latim, i e j sao a mesma letra, e u e v tambem. Os ficheiros
        # escrevem ora 'adjutorium' ora 'adiutorium'. Sem esta equivalencia
        # a formula do 'Deus in adiutorium' nao seria encontrada.
        return s.replace('j', 'i').replace('v', 'u')

    def _nome_tolerante(self, nome, secoes):
        candidato = nome.rstrip('. ').strip()
        if candidato != nome and secoes.get(candidato):
            return candidato
        alvo = self._sem_acento(candidato)
        for chave in secoes:
            if self._sem_acento(chave) == alvo and secoes[chave].strip():
                return chave
        return None

    def expandir_formulas(self, texto, lang, fundo=0):
        """Troca as linhas '$Nome' pelo texto da formula.

        E recursivo: uma formula pode conter outra. A licao breve das
        Completas, por exemplo, acaba em '$Tu autem'.
        """
        texto = self.remissoes(texto, lang)
        if fundo > 6 or '$' not in texto:
            return texto

        saida, mudou = [], False
        for linha in texto.split('\n'):
            m = self.CIFRAO.match(linha)
            if not m:
                saida.append(linha)
                continue
            corpo, _ = self.formula(m.group(2), lang, m.group(1))
            saida.append(corpo)
            mudou = True

        resultado = '\n'.join(saida)
        return self.expandir_formulas(resultado, lang, fundo + 1) if mudou else resultado

    # A remissao para outra hora, escrita dentro da linha:
    #     Reliqua omittuntur, nisi %Laudes% separandæ sint.
    REMISSAO = re.compile(r'%(.*?)%')

    def remissoes(self, texto, lang):
        """'%Laudes%' e uma remissao para outra hora do oficio.

        No site vira um link; num livro impresso vira o nome da hora e o
        numero da pagina. O numero so se sabe depois de paginar, e por
        isso aqui fica so o nome — traduzido, como no original.
        """
        if '%' not in texto:
            return texto
        return self.REMISSAO.sub(
            lambda m: self.traduzir(m.group(1), lang), texto)

    # ------------------------------------------------ titulos de bloco

    FICHEIRO_DOS_TITULOS = 'Psalterium/Common/Translate.txt'

    def traduzir(self, nome, lang):
        """Porta de translate(): o glossario de estrutura do repositorio.

        E daqui que sai a palavra 'Psalmus' — 'Salmo' em portugues — a
        abrir cada salmo. A cadeia e a do costume: vernaculo, depois latim,
        e se nem isso, o proprio nome.
        """
        for tentativa, do_latim in ((lang, False), ('Latin', True)):
            if tentativa == lang and do_latim:
                continue
            try:
                secoes = self.setupstring(tentativa, self.FICHEIRO_DOS_TITULOS)
            except FileNotFoundError:
                continue
            v = (secoes.get(nome) or '').strip()
            if v:
                if do_latim and lang != 'Latin':
                    self.lacunas.add((lang, self.FICHEIRO_DOS_TITULOS, nome))
                return v
        return nome

    def titulo(self, nome, lang):
        """O titulo de um bloco do oficio, traduzido.

        No esqueleto os blocos vem como '#Incipit', '#Hymnus'. O
        repositorio guarda a traducao com a mesma chave, incluindo o '#':
        a seccao chama-se '[#Incipit]' e o valor '#Início'.

        E o glossario de estrutura da seccao 11 do prompt, ja feito e a
        espera de ser usado.
        """
        chave = nome if nome.startswith('#') else f'#{nome}'
        for tentativa, do_latim in ((lang, False), ('Latin', True)):
            if tentativa == lang and do_latim:
                continue
            try:
                secoes = self.setupstring(tentativa, self.FICHEIRO_DOS_TITULOS)
            except FileNotFoundError:
                continue
            v = (secoes.get(chave) or '').strip()
            if v:
                if do_latim and lang != 'Latin':
                    self.lacunas.add((lang, self.FICHEIRO_DOS_TITULOS, chave))
                return v.lstrip('#').strip()
        return chave.lstrip('#').strip()

    def preambulo(self, lang, fname):
        """O preambulo de um ficheiro, SEM a camada latina por baixo.

        Os salmos guardam o texto no preambulo, e nao em seccoes. O
        setupstring empilha o preambulo do vernaculo com o do latim — o
        que e fiel ao original, porque la o preambulo e deitado fora antes
        de servir para alguma coisa. Aqui nao: se se usasse esse
        empilhamento, o salmo sairia em portugues E A SEGUIR em latim, um
        atras do outro, na mesma coluna.
        """
        caminho = self.base / lang / self._nome_latino(fname)
        if not caminho.exists():
            return None

        # Nao se corre aqui o motor de condicionais. Os ficheiros de salmo
        # abrem muitas vezes com um titulo entre parenteses —
        #     (Canticum Simeonis * Luc. 2:29-32)
        # — e o motor leria esse parentese como condicao de rubrica,
        # engolindo a linha seguinte. Era o que fazia o Nunc dimittis
        # perder o seu primeiro versiculo.
        texto = caminho.read_text(encoding='utf-8-sig')
        texto = texto.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
        fora = []
        for linha in texto.split(chr(10)):
            if linha.startswith('['):
                break          # comecou uma seccao: o preambulo acabou
            fora.append(linha)
        return chr(10).join(fora)

    def _nome_latino(self, fname):
        """Porta de checklatinfile.

        As familias cisterciense, monastica e dominicana nao tem ficheiro
        proprio para tudo. Quando falta, cai-se na hierarquia:
            cisterciense -> monastica -> romana
        Sem isto, uma remissao a 'TemporaM/Pent01-3' devolvia 'is
        missing!' em vez do texto romano correspondente.
        """
        base = fname[:-4] if fname.endswith('.txt') else fname
        sufixo = '.txt' if fname.endswith('.txt') else ''

        if (self.base / 'Latin' / f'{base}.txt').exists():
            return fname

        cist = re.sub(r'(Sancti|Tempora|Commune)Cist(.*)', r'\1M\2', base)
        if cist != base and (self.base / 'Latin' / f'{cist}.txt').exists():
            return cist + sufixo

        romano = re.sub(r'(Sancti|Tempora|Commune)(?:M|OP)(.*)', r'\1\2', base)
        if romano != base and (self.base / 'Latin' / f'{romano}.txt').exists():
            return romano + sufixo

        return fname

    def _carregar(self, lang, fname):
        """Empilha o vernaculo sobre o latim. NUNCA sobre o ingles."""
        fname = self._nome_latino(fname)
        caminho = self.base / lang / fname
        titulo = fname[:-4] if fname.endswith('.txt') else fname

        base = {}
        if lang != 'Latin':
            base = self.setupstring('Latin', fname, RESOLVE_NONE)

        novo = self._parse(caminho, titulo, lang) if caminho.exists() else {}

        if novo:
            # Os hinos anteriores a revisao de Urbano VIII estao em seccoes
            # 'HymnusM ...'. Uma traducao costuma ter so o hino, sem a
            # variante antiga — e entao a traducao serve para as duas.
            # Isto tem de acontecer ANTES de o latim preencher, senao a
            # variante antiga sairia em latim tendo traducao disponivel.
            if lang != 'Latin':
                for chave in list(novo):
                    m = re.match(r'^Hymnus (.*)', chave)
                    if m and f'HymnusM {m.group(1)}' not in novo:
                        novo[f'HymnusM {m.group(1)}'] = novo[chave]

            pre_novo = novo.get('__preamble', '')
            pre_base = base.get('__preamble', '')
            if pre_novo != pre_base:
                novo['__preamble'] = pre_novo + '\n' + pre_base
            for k, v in base.items():
                if not novo.get(k):
                    novo[k] = v
                    if lang != 'Latin':
                        self.lacunas.add((lang, fname, k))
            # O grau do oficio ('Rank') herda sempre o nome do oficio
            # ('Officium'), para que uma inclusao de seccao possa mudar o
            # grau sem perder o nome.
            base_rank = (base.get('Rank') or '').split(';;')
            if base.get('Rank'):
                novo_rank = (novo.get('Rank') or '').split(';;')
                oficio = (novo.get('Officium') or '').rstrip()
                base_rank[0] = oficio or (novo_rank[0] if novo_rank else '')
                novo['Rank'] = ';;'.join(base_rank)
            elif 'Officium' in novo:
                novo_rank = (novo.get('Rank') or '').split(';;')
                novo_rank[0] = (novo.get('Officium') or '').rstrip()
                novo['Rank'] = ';;'.join(novo_rank)
        else:
            novo = dict(base)
            if lang != 'Latin':
                for k in base:
                    self.lacunas.add((lang, fname, k))
        return novo

    # ------------------------------------------------------------- inclusoes

    def _inclusoes_de_ficheiro(self, secoes, lang, fname):
        """Remissoes soltas no preambulo: trazem o ficheiro inteiro."""
        vistos = set()
        while True:
            pre = secoes.get('__preamble', '')
            if '@' not in pre:
                return
            m = INCLUSAO.search(pre)
            if not m or not m.group(1):
                return
            incl = f'{m.group(1)}.txt'
            if incl in vistos or incl in fname:
                return
            vistos.add(incl)
            outras = self.setupstring(lang, incl, RESOLVE_WHOLEFILE)
            for k, v in outras.items():
                if not secoes.get(k):
                    secoes[k] = v
            secoes['__preamble'] = pre[:m.start()] + pre[m.end():]

    def _salta(self, chave, conteudo):
        """As mesmas excepcoes do original: comemoracoes e evangelhos nao se
        resolvem, para nao entrar em ciclo."""
        if 'Commemoratio' in chave:
            return True
        if ('LectioE' in chave or 'Evangelium' in chave) and 'Commune' not in conteudo:
            return True
        return False

    def _inclusoes_de_seccao(self, secoes, lang, fname):
        ordem = (['Rule'] if 'Rule' in secoes else []) + list(secoes)
        for chave in ordem:
            if chave not in secoes or self._salta(chave, secoes[chave]):
                continue
            voltas = 0
            while '@' in secoes[chave]:
                if voltas > 6:
                    self.nao_resolvidas.append((lang, fname, chave, 'fundo demais'))
                    break
                novo = INCLUSAO.sub(
                    lambda m: self._trazer(secoes, lang, m.group(1),
                                           m.group(2) or chave, m.group(3),
                                           fname, chave),
                    secoes[chave])
                if novo == secoes[chave]:
                    break
                secoes[chave] = novo
                voltas += 1

    def _trazer(self, secoes_proprias, lang, ficheiro, seccao, subs,
                chamador, chave):
        """get_loadtime_inclusion."""
        # No tempo pascal, os Comuns de Apostolos e Martires trocam para a
        # variante propria — C1 passa a C1p, e assim por diante.
        if (ficheiro and 'Pasc' in (self.ctx.tempore or '')
                and not re.search(r'C[123]', chamador or '')
                and not re.search(r'Hymnus|Oratio|Lectio|Secreta|Postcommunio|Versum',
                                  seccao, re.I)):
            ficheiro = re.sub(r'(C[123][abcd]*)(?![p\d])', r'\1p', ficheiro)

        if ficheiro:
            fonte = self.setupstring(lang, f'{ficheiro}.txt', RESOLVE_WHOLEFILE)
        else:
            fonte = secoes_proprias

        texto = fonte.get(seccao)
        if not texto:
            self.nao_resolvidas.append((lang, chamador, chave,
                                        f'{ficheiro}:{seccao}'))
            return f'{ficheiro}:{seccao} is missing!'

        texto = re.sub(r'\n+$', '\n', texto)
        return aplicar_substituicoes(texto, subs)
