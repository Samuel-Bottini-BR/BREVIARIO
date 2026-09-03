"""
De onde vem cada peca do dia: do proprio, ou do Comum.

E a pergunta central do livro. A matriz de regras (matriz_normas.py) diz
qual a resposta NORMAL para cada casa; esta funcao diz a resposta REAL,
porque quase todas as normas 165-177 acabam com 'salvo o que for dado como
proprio'. Por isso se procura sempre primeiro no proprio do dia, e so
depois no Comum — a decisao 3.13 do registo.

E ha uma condicao a mais, que e a razao de 'vide' e 'ex' serem palavras
diferentes:

    ex     o oficio E o do Comum: o Comum consulta-se sempre
    vide   o Comum e so uma fonte: consulta-se apenas quando a peca o
           pedir de forma explicita

Porta de getproprium e replaceNdot, em specials.pl.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from comum import subpasta, extrair_comum

# Nos ficheiros do Comum ha peças cujo nome nao coincide com o que a hora
# pede. O original tem esta tabela de equivalencias.
EQUIVALENTES = {
    'Nocturn 1 Versum': 'Versum 1',
    'Responsory TertiaM': 'Nocturn 1 Versum',
    'Versum Tertia': 'Nocturn 2 Versum',
    'Responsory SextaM': 'Nocturn 2 Versum',
    'Versum Sexta': 'Nocturn 3 Versum',
    'Responsory NonaM': 'Nocturn 3 Versum',
    'Versum Nona': 'Versum 2',
}

# De onde a peca veio. Sao os mesmos numeros do original, e servem para o
# rotulo que sai na pagina: '{ex Proprio Sanctorum}', '{ex Communi}'.
DO_PROPRIO_TEMPORE = 2
DO_PROPRIO_SANCTORUM = 3
DO_COMUM = 4

SEMANAS = ('I.', 'II.', 'III.', 'IV.', 'V.')


def officestring(resolvedor, lang, ficheiro, ficheiro_do_mes=''):
    """Ler um oficio como o original o le. Porta de officestring.

    Nao e so abrir o ficheiro. Depois de Agosto, e depois da Epifania, os
    dias do Tempo tem um SEGUNDO ficheiro, chamado pelo mes liturgico
    ('Tempora/093-0.txt' = domingo da 3a semana de Setembro). O original
    le os dois e sobrepoe as seccoes do segundo ao primeiro — todas menos
    a [Rank], que fica a do primeiro, so com a semana e o mes acrescentados
    ao nome.

    E dai que vem, por exemplo, 'Dominica ... I. Octobris', que o hino de
    inverno das Laudes pede, e sao de la que vem as licoes de Matinas
    nesses dias.

    Qual e o segundo ficheiro vem colhido no Ordo: e uma conta de datas
    moveis, e por isso colhe-se (decisao 3.22).
    """
    s = dict(resolvedor.setupstring(lang, ficheiro))
    if not ficheiro_do_mes:
        return s
    try:
        m = resolvedor.setupstring(lang, ficheiro_do_mes)
    except (FileNotFoundError, OSError):
        return s

    # '093-0' -> mes 09, semana 3. O nome do mes esta no Comment.txt, e a
    # lista comeca em Agosto — dai o '- 8'.
    nome_mes = semana = ''
    achado = re.match(r'.*?(\d\d)(\d)-\d', ficheiro_do_mes)
    if achado:
        i_mes, i_semana = int(achado.group(1)), int(achado.group(2))
        if i_mes:
            meses = (resolvedor.setupstring(lang, 'Psalterium/Comment.txt')
                     .get('Menses') or '').split('\n')
            if 0 <= i_mes - 8 < len(meses):
                nome_mes = meses[i_mes - 8].strip()
        if i_semana:
            semana = SEMANAS[i_semana - 1] if i_semana <= len(SEMANAS) else ''
        campos = (s.get('Rank') or '').split(';;')
        if campos:
            campos[0] = f'{campos[0]} {semana} {nome_mes}'
            s['Rank'] = ';;'.join(campos)

    # A [Rank] tambem se sobrepoe. O original tem aqui uma condicao que
    # PARECE proteger a [Rank] — 'if ($version =~ //i && $key =~ /Rank/i)' —
    # mas '//' em Perl e o padrao vazio: reaproveita o ultimo padrao que
    # tenha casado, e na pratica a condicao nao se cumpre. Medido: pedida
    # a Quarta-feira das Temporas de Setembro, a funcao deles devolve
    # 'Feria Quarta Quattuor Temporum Septembris;;Feria major;;4.9', que e
    # a [Rank] do ficheiro do mes, e nao a do ficheiro da semana. Sem
    # isto, as bencaos das Temporas saíam as da feria comum.
    for chave, valor in m.items():
        s[chave] = valor
    return s


class Dia:
    """O oficio de um dia, ja resolvido: o proprio, o Comum e a sua regra.

    Enquanto o calculo do calendario nao existir, o ficheiro do proprio e
    dado de fora. O Comum, esse, ja se deduz sozinho da linha [Rank].
    """

    def __init__(self, resolvedor, proprio, version='Rubrics 1960 - 1960',
                 tempo_pascal=False, lang='Latin', registo=None,
                 ficheiro_do_mes=None):
        """'registo' e a linha do Ordo desse dia, quando ela existe.

        Com ela, o Comum e a classe vem prontos da funcao de precedencia
        do proprio Divinum Officium — que e quem sabe as regras — em vez
        de serem deduzidos aqui. Sem ela, deduzem-se da linha [Rank], que
        e o caminho ja conferido em 660 casos e acerta no caso simples.
        """
        self.r = resolvedor
        self.version = version
        self.proprio = proprio
        self.lang = lang
        self.registo = registo
        self.avisos = []

        # Depois de Agosto o texto do dia do Tempo vem de um ficheiro com
        # outro nome — o do mes liturgico. O nome do vencedor nao muda,
        # mas o texto e o de la.
        # O nome do vencedor nem sempre e o ficheiro de onde o texto vem:
        # depois de Agosto, os dias do Tempo tem um segundo ficheiro,
        # chamado pelo mes liturgico. Qual dos dois serviu vem colhido no
        # Ordo — perguntado ao proprio resultado, nao adivinhado.
        self.ficheiro = (registo.ficheiro if registo is not None
                         and registo.ficheiro else proprio)
        # ATENCAO: 'ficheiro_efectivo' escolhe UM dos dois ficheiros; o
        # original le OS DOIS e sobrepoe-os. Para as sete horas ja fechadas
        # a escolha bastava — nenhuma peca delas vinha das seccoes que so
        # existem no primeiro. Nas Matinas nao basta: as licoes e os
        # responsorios vem misturados dos dois.
        if ficheiro_do_mes is None and registo is not None:
            ficheiro_do_mes = registo.mes_vencedor
        if ficheiro_do_mes:
            self.ficheiro = proprio
            self.secoes = officestring(resolvedor, lang, proprio,
                                       ficheiro_do_mes)
        else:
            self.secoes = resolvedor.setupstring(lang, self.ficheiro)
        campos = (self.secoes.get('Rank') or '').strip().split(';;')
        self.rank = self._numero(campos[2] if len(campos) > 2 else '')
        self.tipo_comum, self.comum = extrair_comum(
            campos[3] if len(campos) > 3 else '', self.rank, version,
            tempo_pascal, resolvedor.base)
        self.rule = (self.secoes.get('Rule') or '').strip()
        self.nome = (self.secoes.get('Name') or '').strip()

        if registo is not None:
            # O Ordo manda. Guarda-se o que nos tinhamos deduzido, para se
            # poder confrontar os dois sobre o ano inteiro.
            self.comum_deduzido = (self.tipo_comum, self.comum)
            self.rank = registo.rank or self.rank
            if registo.comum:
                self.tipo_comum, self.comum = registo.tipo_comum, registo.comum
            if registo.regra:
                self.rule = registo.regra

        self.secoes_comum = {}
        if self.comum:
            try:
                self.secoes_comum = resolvedor.setupstring(lang, self.comum)
            except FileNotFoundError:
                self.avisos.append(f'o Comum {self.comum} nao existe')
        # A regra do Comum vale por si, a par da regra do proprio: e nela
        # que esta, por exemplo, o 'Psalmi Dominica' do Comum de Nossa
        # Senhora.
        self.regra_do_comum = (self.secoes_comum.get('Rule') or '').strip()
        if registo is not None:
            # Quando ha Ordo, o Ordo manda — inclusive quando diz que NAO
            # ha regra de Comum. A funcao de precedencia deles so a poe em
            # certos casos, e ler o ficheiro por conta propria fazia rezar
            # os salmos de domingo em 2 de Janeiro, que e feria.
            self.regra_do_comum = registo.regra_comum

    @staticmethod
    def _numero(s):
        try:
            return float(s)
        except ValueError:
            return 0.0

    # ------------------------------------------------------------------ #

    def proprium(self, nome, flag=False):
        """Devolve (texto, procedencia) — ou (None, 0) se nao houver.

        'flag' e o que forca a consulta do Comum mesmo quando a remissao e
        'vide'. O original passa-o quando a peca so pode vir do Comum, por
        exemplo o capitulo e o hino das horas menores.
        """
        texto = self.secoes.get(nome)
        if texto and texto.strip():
            proc = (DO_PROPRIO_SANCTORUM if 'Sancti' in self.proprio
                    else DO_PROPRIO_TEMPORE)
            return texto, proc

        if not self.tipo_comum:
            return None, 0
        if not (self.tipo_comum.lower().startswith('ex') or flag):
            return None, 0

        com = dict(self.secoes_comum)
        cn = self.comum or ''
        equivalente = EQUIVALENTES.get(nome, '')
        procurado = nome

        for _ in range(5):
            texto = com.get(procurado)
            if texto and texto.strip():
                return self.substituir_nome(texto), DO_COMUM

            if re.match(r'^C', Path(cn).name, re.I) and equivalente:
                texto = com.get(equivalente)
                if texto and texto.strip():
                    return self.substituir_nome(texto), DO_COMUM
                return None, 0

            # Um Comum que por sua vez remete para outro. Acontece nos
            # 'pseudo-Comuns' — um oficio de santo a servir de Comum.
            if not re.match(r'^C', Path(cn).name, re.I):
                m = re.search(r';;(ex|vide)\s*(C[0-9a-z]+)', com.get('Rank') or '',
                              re.I) or re.search(
                    r';;(ex|vide)\s*(SanctiM?/.*?)\s', com.get('Rank') or '', re.I)
                if not m:
                    return None, 0
                if m.group(1).lower() == 'vide' and not flag:
                    return None, 0
                alvo = m.group(2)
                cn = (alvo if re.match(r'^Sancti', alvo, re.I)
                      else subpasta('Commune', self.version) + alvo)
                try:
                    com = self.r.setupstring(self.lang, f'{cn}.txt')
                except FileNotFoundError:
                    return None, 0
                continue
            return None, 0
        return None, 0

    # ------------------------------------------------------------------ #

    NOME_ABREVIADO = re.compile(r'N\.')

    def substituir_nome(self, texto):
        """Porta de replaceNdot.

        Os ficheiros do Comum escrevem 'N.' onde vai o nome do santo:
        'ut, intercedénte beáto N.'. Sem isto, a pagina impressa sairia
        com o 'N.' — que e a marca inconfundivel de um livro mal feito.
        """
        if 'N.' not in texto:
            return texto
        nome = self.nome
        if not nome:
            return texto

        linhas = [l for l in nome.split('\n') if l.strip()]
        if re.match(r'^[OÓ],?\s|O Doctor optime', texto) and 'Ant=' in nome:
            escolhidas = [l for l in linhas if 'Ant=' in l]
        else:
            escolhidas = ([l for l in linhas if 'Oratio=' in l]
                          if 'Oratio=' in nome else linhas)
        if not escolhidas:
            return texto

        valor = re.sub(r'^.*?=', '', escolhidas[0]).strip()
        if not valor:
            return texto
        texto = re.sub(r'N\. .*? N\.', valor, texto, count=1)
        return texto.replace('N.', valor)
