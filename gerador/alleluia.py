"""
O alleluia do tempo pascal.

Da Pascoa a Pentecostes acrescenta-se 'allelúja' ao fim das antifonas, dos
versiculos e dos responsorios breves — e ao responsorio breve acrescentam-se
DOIS, com o asterisco a mudar de sitio. Os ficheiros nao trazem esses
alleluias escritos: sao postos na hora de montar a hora.

Ha ainda os que os ficheiros trazem ENTRE PARENTESES, e esses dizem-se no
tempo pascal e cortam-se fora dele.

Porta de process_inline_alleluias, ensure_single_alleluia e
ensure_double_alleluia (LanguageTextTools.pm) e das tres pos-processadoras
postprocess_ant, postprocess_vr e postprocess_short_resp (horas.pl).

Nao se aplica ao Oficio de Defuntos nem ao Parvo de Nossa Senhora — e a
regra 'alleluia_required'.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Como o original o constroi: as traducoes da palavra nas linguas
# carregadas, mais a grafia alternativa do latim.
# Latim 'Allelúja', portugues 'Aleluia'.
PADRAO = r'(?:allel[uú]ja|aleluia|allel[uú][ij]a)'
ENTRE_PARENTESES = re.compile(rf'\(({PADRAO}.*?)\)', re.I | re.S)
NO_FIM = re.compile(rf'{PADRAO}[^\w\s]?\)?\s*$', re.I)
DUPLO_NO_FIM = re.compile(rf'{PADRAO}[,.] {PADRAO}[^\w\s]?\s*$', re.I)
PONTUACAO_FINAL = re.compile(r'[^\w\s]?\s*$')


def e_tempo_pascal(dayname, votive=''):
    """Porta de alleluia_required. Nao vale no Oficio de Defuntos (C9)
    nem no Parvo de Nossa Senhora (C12)."""
    return (bool(re.search(r'Pasc', dayname or '', re.I))
            and not re.search(r'C(?:9|12)', votive or ''))


def suprime_se(dayname, hora='', dayofweek=0, vespera=0, cwinner=''):
    """Se hoje se APAGA todo o alleluia que o texto traga escrito.

    Da Septuagesima ao sabado santo o alleluia despede-se. Nao basta nao
    o acrescentar: ha antifonas que o trazem escrito no ficheiro, e essas
    ficariam com ele. E o que faz a festa de S. Matias, que cai na
    Quaresma e toma as antifonas do Comum dos Apostolos, dize-las sem o
    alleluia que o Comum lhes da.

    Porta da chamada a 'suppress_alleluia' em webdia.pl, que o original
    faz ao texto de TODAS as horas, mesmo antes de o mostrar.
    """
    if not re.search(r'Quadp|Quad[1-5]|Quad6-[0-5]', dayname or '', re.I):
        return False
    # Salvo nas II Vesperas do sabado antes da Septuagesima, em que o
    # alleluia ainda se canta — e a despedida.
    septuagesima = (dayofweek == 6 and re.search(r'Vespera', hora or '', re.I)
                    and ((vespera == 1 and re.search(r'Quadp1', dayname or ''))
                         or (vespera == 3
                             and re.search(r'Quadp1-0', cwinner or ''))))
    return not septuagesima


SO_O_ALLELUIA = re.compile(rf'[,.]?\s*{PADRAO}', re.I)


def suprimir(texto):
    """Porta de suppress_alleluia."""
    return SO_O_ALLELUIA.sub('', texto or '')


def tempo(texto, pascal, suprime=False):
    """As duas passagens que o original da ao texto antes de o mostrar:
    os alleluias entre parenteses, e a supressao da Quaresma."""
    texto = do_tempo(texto, pascal)
    return suprimir(texto) if suprime else texto


def do_tempo(texto, pascal):
    """Porta de process_inline_alleluias.

        R.br. In manus tuas, Dómine. (Allelúja, allelúja.)

    Na Pascoa tiram-se os parenteses e o alleluia diz-se; fora dela,
    corta-se o parentese inteiro. Sem isto o parentese saía impresso, e o
    leitor via um alleluia entre parenteses o ano todo.
    """
    if pascal:
        return ENTRE_PARENTESES.sub(lambda m: f' {m.group(1)} ', texto)
    return ENTRE_PARENTESES.sub('', texto)


class Alleluia:
    """As pos-processadoras. Guarda a palavra traduzida, que vem do
    corpus e nao daqui."""

    def __init__(self, resolvedor):
        self.r = resolvedor
        self._cache = {}

    def palavra(self, lang):
        """'Allelúja' — sem o 'v. ' nem o ponto final, como no original."""
        if lang not in self._cache:
            texto, _ = self.r.formula('Alleluia', lang)
            self._cache[lang] = re.sub(r'^v\. (.*?)\..*', r'\1', texto,
                                       flags=re.S)
        return self._cache[lang]

    def duplo(self, lang):
        texto, _ = self.r.formula('Alleluia Duplex', lang)
        return texto.rstrip()

    # ------------------------------------------------------------------ #

    def um(self, texto, lang):
        """Porta de ensure_single_alleluia: um alleluia no fim, se ainda
        nao houver nenhum."""
        if not texto or NO_FIM.search(texto):
            return texto
        return PONTUACAO_FINAL.sub(f', {self.palavra(lang).lower()}.', texto,
                                   count=1)

    def dois(self, texto, lang):
        """Porta de ensure_double_alleluia: dois alleluias no fim, e o
        asterisco muda para o lugar deles."""
        if not texto or DUPLO_NO_FIM.search(texto):
            return texto
        # O asterisco sai de onde estava, e a letra que o seguia passa a
        # minuscula: era ela que abria a segunda metade do versiculo.
        texto = re.sub(r'\s*\*\s*(.)', lambda m: f' {m.group(1).lower()}',
                       texto, count=1)
        p = self.palavra(lang)
        return PONTUACAO_FINAL.sub(f', * {p}, {p.lower()}.', texto, count=1)

    # ------------------------------------------------------------------ #

    def antifona(self, ant, lang, pascal):
        """Porta de postprocess_ant."""
        return self.um(ant, lang) if pascal and ant else ant

    def versiculo(self, vr, lang, pascal):
        """Porta de postprocess_vr: o V. e o R. levam cada um o seu."""
        if not pascal or not vr:
            return vr
        partes = re.split(r'(?m)(?=^\s*R\.)', vr, maxsplit=1)
        if len(partes) < 2:
            return self.um(vr, lang)
        return self.um(partes[0].rstrip(), lang) + '\n' + \
            self.um(partes[1].strip(), lang)

    def responsorio_breve(self, texto, lang, pascal, regra='', hora=''):
        """Porta de postprocess_short_resp.

        O responsorio breve tem quatro linhas com a mesma resposta a
        repetir-se. No tempo pascal a primeira e a ultima levam dois
        alleluias; a do meio, que responde ao versiculo, e substituida
        pelo 'Alleluia Duplex' inteiro.
        """
        if not texto:
            return texto

        # Isto vale SEMPRE, alleluia ou nao: o Gloria de um responsorio
        # breve e o '&Gloria1', que se cala no tempo da Paixao. Escrito
        # '&Gloria', nao se calaria — e sairia Gloria onde a rubrica manda
        # silencio, em dez dias do ano.
        texto = re.sub(r'&Gloria1?', '&Gloria1', texto)

        aplicar = pascal or (re.search(r'Responsory Breve cum Alleluja', regra)
                             and hora in ('Tertia', 'Sexta', 'Nona'))
        if not aplicar:
            return texto

        # ISTO CORRE SOBRE O TEXTO POR EXPANDIR. E preciso que assim seja:
        # a linha do Gloria e ainda '&Gloria1', e nao 'V. Glória Patri'.
        # Se ja estivesse expandida, o 'V.' dela abriria um versiculo que
        # nao existe, e a ultima resposta sairia trocada.
        fora = []
        dentro = False       # dentro do responsorio breve propriamente
        respostas = 0        # as respostas, sem contar a primeira linha
        depois_do_versiculo = False
        so_no_responsorio = bool(
            re.search(r'Responsory Breve cum Alleluja', regra))

        for l in texto.split('\n'):
            if not dentro:
                if re.match(r'^R\.\s?br\.', l):
                    dentro = True
                    fora.append(self.dois(l, lang))
                    continue
                # O versiculo que vem DEPOIS do responsorio breve leva um
                # alleluia so.
                if l[:2] in ('V.', 'R.') and not so_no_responsorio:
                    l = self.um(l, lang)
                fora.append(l)
                continue

            if l.startswith('V.'):
                depois_do_versiculo = True
            if l.startswith('R.'):
                respostas += 1
                if depois_do_versiculo:
                    # A resposta ao versiculo do responsorio nao se repete
                    # inteira: e so o alleluia duplo.
                    l = 'R. ' + self.duplo(lang)
                    depois_do_versiculo = False
                else:
                    l = self.dois(l, lang)
                if respostas >= 3:
                    dentro = False
            fora.append(l)
        return '\n'.join(fora)
