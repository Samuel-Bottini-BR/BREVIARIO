"""
A matriz de resolucao, montada a partir das NORMAS OFICIAIS de 1960.

Fonte: Help/Rubrics/Breviary 1960.html do proprio repositorio — o texto
oficial, em paragrafos numerados. Cada linha desta matriz cita o numero da
norma de onde veio, para que a conferencia seja contra a lei e nao contra a
leitura de uma tabela.

O Hausmann e o site sao os conferidores, nao a fonte.

DIFERENCA PARA A VERSAO ANTERIOR: uma celula pode agora depender do TEMPO
LITURGICO. Onde a tabela do Hausmann dava um valor so, a lei muitas vezes
da um valor com excecoes. Era o defeito da versao anterior.

--------------------------------------------------------------------------
AS CINCO CLASSES (nao sao classes de dia, sao tipos de oficio)
--------------------------------------------------------------------------
  I    Officium festivum      festas de I classe                 (norma 167)
  II   Officium semifestivum  festas de II classe                (norma 168)
  III  Officium ordinarium    festas de III classe E o oficio
                              de N. Senhora ao sabado            (norma 169)
  DOM  Officium dominicale    domingos, de qualquer classe       (norma 165)
  FER  Officium feriale       ferias e vigilias, salvo o Triduo
                              Sacro e a vigilia do Natal         (norma 170)

--------------------------------------------------------------------------
AS FONTES
--------------------------------------------------------------------------
  Ord     Ordinarium
  Ps.dom  Salterio, do domingo
  Ps.dia  Salterio, do dia da semana corrente
  Ord+Ps  "o Ordinario e o Salterio", que a lei trata como um corpo so
  Pr>Com  o Proprio; onde ele nao der, o Comum. NAO sao alternativas:
          o Comum e queda, e nesta ordem (normas 167 a, 169 b, 241).

          ATENCAO: "o Proprio" nao quer dizer sempre Proprio dos Santos.
          Numa festa de santo e o Proprio dos Santos; numa festa do
          SENHOR e o Proprio do TEMPO. Levantado ao comparar 2026: a
          oracao das Vesperas em festas de I classe vem do Proprio do
          Tempo na oitava da Pascoa, na Ascensao, na oitava de
          Pentecostes, no Corpus Christi e no Sagrado Coracao.
  PdT     Proprio do Tempo
  L1..L5  a antifona n de Laudes
"""

# --------------------------------------------------------------------------
# Vocabulario
# --------------------------------------------------------------------------

ORD = 'Ord'
PSDOM = 'Ps.dom'
PSDIA = 'Ps.dia'
PSTEMPO = 'Ps.tempo'   # Salterio do TEMPO liturgico, distinto do dia da
                       # semana. O gerador chama-lhe 'ex Psalterio secundum
                       # tempora'. A primeira versao desta matriz nao tinha
                       # esta fonte; apareceu ao comparar os 365 dias.
ORDPS = 'Ord+Ps'
PRCOM = 'Pr>Com'
PDT = 'PdT'

# Os tempos em que o Proprio do Tempo toma o lugar do Ordinario/Salterio
# em varias pecas. Levantado do confronto com os 365 dias de 2026.
TEMPOS_PROPRIOS = ('Advento, Natal, Septuagesima, Quaresma, Paixao e Pascoa')

CLASSES = ['I', 'II', 'III', 'DOM', 'FER']


class Conforme:
    """Uma celula cujo valor depende do tempo liturgico.

    'padrao' vale onde nenhuma excecao se aplica.
    'excecoes' e uma lista de (condicao_em_portugues, valor).
    """

    def __init__(self, padrao, *excecoes):
        self.padrao = padrao
        self.excecoes = list(excecoes)

    def __repr__(self):
        e = '; '.join(f'{c} -> {v}' for c, v in self.excecoes)
        return f'{self.padrao} (salvo: {e})'


def L(peca, I, II, III, DOM, FER, normas):
    return {'peca': peca, 'I': I, 'II': II, 'III': III, 'DOM': DOM,
            'FER': FER, 'normas': normas}


# --------------------------------------------------------------------------
# MATINAS
# --------------------------------------------------------------------------

# Quantos nocturnos e quantas licoes — normas 161, 162, 163
FORMA_DAS_MATINAS = {
    'I':   'tres nocturnos, nove salmos, nove licoes (norma 161 a)',
    'II':  'tres nocturnos, nove salmos, nove licoes (norma 161 a)',
    'III': 'um nocturno, nove salmos, tres licoes (norma 162 d)',
    'DOM': 'um nocturno, nove salmos, tres licoes (norma 162 a); '
           'salvo Pascoa e Pentecostes, que tem um nocturno de tres '
           'salmos e tres licoes (norma 163)',
    'FER': 'um nocturno, nove salmos, tres licoes (norma 162 b)',
}

MATINAS = [
    L('Invitatorio',
      PRCOM, PRCOM, PRCOM, ORDPS, ORDPS,
      '167 c; 168 a; 169 a; 166 c; 171 a'),

    L('Hino',
      PRCOM, PRCOM, PRCOM, ORDPS, ORDPS,
      '167 c; 168 a; 169 a; 166 c; 171 a'),

    L('Antifonas e salmos do nocturno',
      PRCOM, PRCOM,
      Conforme(PSDIA, ('se a festa tiver proprias ou do Comum (norma 177)', PRCOM)),
      PSDOM, PSDIA,
      '167 c; 168 a; 169 a + 177; 166 c; 171 a'),

    L('Versiculo do nocturno',
      PRCOM, PRCOM, PSDIA, PSDOM, PSDIA,
      '167 c; 168 a; 169 a; 166 c; 171 a'),

    L('Absolvicao e bencaos',
      ORD, ORD, ORD, ORD, ORD,
      '166 c da os nomes para o domingo: absolvicao Exaudi, '
      'bencaos Ille nos, Divinum auxilium, Per evangelica dicta'),

    L('Licoes 1 e 2, com responsorios',
      PRCOM, PRCOM, PDT, PDT, PDT,
      '167 c; 168 a; 169 a + 221 a; 166 c + 220 a; 171 a'),

    L('Licao 3',
      PRCOM, PRCOM, PRCOM, PDT, PDT,
      '169 a + 221 b (a licao do santo); 166 c + 220 b (a homilia); 171 a'),

    L('Te Deum, ou o responsorio em seu lugar',
      'Te Deum', 'Te Deum', 'Te Deum',
      Conforme('Te Deum',
               ('do I domingo do Advento a vigilia do Natal', 'responsorio'),
               ('da Septuagesima ao Sabado Santo', 'responsorio')),
      Conforme('responsorio',
               ('ferias do tempo do Natal', 'Te Deum'),
               ('ferias do tempo pascal', 'Te Deum')),
      '237; 238; 239'),
]

# --------------------------------------------------------------------------
# LAUDES
# --------------------------------------------------------------------------

# O esquema de salmos de Laudes — norma 197
ESQUEMA_2 = ('domingos da Septuagesima, Quaresma e Paixao; '
             'ferias do Advento, Septuagesima, Quaresma e Paixao; '
             'Temporas de setembro; vigilias de II e III classe fora '
             'do tempo pascal')

LAUDES = [
    L('Antifonas',
      PRCOM, PRCOM,
      Conforme(PSDIA, ('se a festa tiver proprias ou do Comum (norma 177)', PRCOM)),
      Conforme(PSDOM, ('se houver antifona propria', PDT)),
      PSDIA,
      '167 d; 168 a; 169 b + 177; 166 d; 171 b'),

    L('Salmos',
      'Ps.dom, 1o esquema', 'Ps.dom, 1o esquema',
      PSDIA,
      Conforme('Ps.dom, 1o esquema', (ESQUEMA_2, 'Ps.dom, 2o esquema')),
      Conforme('Ps.dia, 1o esquema', (ESQUEMA_2, 'Ps.dia, 2o esquema')),
      '167 d (diz "first scheme" expressamente); 168 a; 169 b; 166 d + 197; 171 b + 197'),

    L('Capitulo, hino e versiculo',
      PRCOM, PRCOM, PRCOM,
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      '167 d; 168 a; 169 b; 166 d ("como no Ordinario OU no Salterio OU no '
      'Proprio do Tempo" — a norma ja previa as tres, sem dizer quando). '
      'CORRIGIDO: nos 365 dias de 2026, ao domingo, vem do Proprio do Tempo '
      'em todo o Advento, Natal, Septuagesima, Quaresma, Paixao e Pascoa; '
      'e do Salterio depois da Epifania e depois de Pentecostes.'),

    L('Antifona do Benedictus',
      PRCOM, PRCOM, PRCOM, PDT, PDT,
      '167 d; 168 a; 169 b; 166 d ("o resto do Proprio do Tempo"); '
      '171 b. CORRIGIDO: eu tinha escrito Ps.dia na coluna FER, ignorando '
      'a ressalva "salvo o que for dado como proprio" da norma 171 b. '
      'A antifona ferial do Benedictus e dada como propria: o gerador da '
      'PdT em 112 dos 115 dias de 2026.'),

    L('Benedictus',
      ORD, ORD, ORD, ORD, ORD,
      'norma 160: o modo de dizer cada hora esta no Ordinario'),

    L('Oracao',
      PRCOM, PRCOM, PRCOM, PDT,
      Conforme('oracao do domingo anterior',
               ('se a feria tiver oracao propria', PDT),
               ('nas vigilias', 'a oracao propria da vigilia')),
      '167 d; 168 a; 169 b; 166 d; 171 b'),
]

# --------------------------------------------------------------------------
# PRIMA
# --------------------------------------------------------------------------

PRIMA = [
    L('Antifona',
      Conforme('L1', ('tempo pascal', PSTEMPO)),
      PSDIA, PSDIA,
      Conforme(PSDOM,
               ('se houver antifona propria', PRCOM),
               ('Advento, Septuagesima, Quaresma e Paixao', PDT)),
      Conforme(PSDIA, ('se houver antifona propria', PRCOM)),
      '167 e; 168 b; 169 c; 166 e; 171 c. CORRIGIDO: no tempo pascal a '
      'festa nao usa a primeira antifona de Laudes, mas o salterio do '
      'tempo — os cinco dias da oitava da Pascoa em 2026.'),

    L('Salmos',
      'Ps.dom (53, 118.1, 118.2)', PSDIA, PSDIA, PSDOM, PSDIA,
      '167 e (nomeia os salmos); 168 b; 169 c; 166 e; 171 c'),

    L('Capitulo',
      ORD, ORD, ORD, ORD, ORD,
      '241: em Prima e SEMPRE Regi saeculorum. '
      'ATENCAO A PRATELEIRA: o texto e invariavel, mas o Divinum Officium '
      'guarda-o dentro do Salterio, e rotula-o "ex Psalterio secundum diem". '
      'Mesmo texto, estante diferente — conferido em 289 dias de 2026.'),

    L('Licao breve',
      ORDPS, ORDPS, ORDPS, ORDPS, ORDPS,
      '242: "a licao breve de Prima e sempre do Tempo, COMO NO ORDINARIO". '
      'CORRIGIDO: eu tinha escrito PdT, lendo "do Tempo" como Proprio do '
      'Tempo. A norma diz "como no Ordinario": muda com o tempo liturgico, '
      'mas mora no Ordinario/Salterio. O gerador da Ord+Ps ou Ps.tempo em '
      '291 dias de 2026.'),

    L('O resto de Prima',
      ORD, ORD, ORD, ORD, ORD,
      '167 e; 168 b; 169 c; 166 e; 171 c — todas dizem "o resto como no Ordinario"'),
]

# --------------------------------------------------------------------------
# TERCA, SEXTA E NOA
# --------------------------------------------------------------------------

MENORES = [
    L('Antifona',
      Conforme('L2 / L3 / L5', ('tempo pascal', PSTEMPO)),
      PSDIA, PSDIA,
      Conforme(ORDPS,
               ('Advento, Septuagesima, Quaresma e Paixao', PDT),
               ('tempo pascal', PSTEMPO)),
      Conforme(PSDIA, ('se houver antifona propria', PRCOM)),
      '167 f (2a, 3a e 5a de Laudes); 168 c; 169 d; 166 f; 171 d. '
      'CORRIGIDO em dois pontos, pelo confronto com 2026: '
      '(1) no tempo pascal as festas nao usam as antifonas de Laudes, mas '
      'o triplice Alleluia do salterio do tempo — os cinco dias da oitava '
      'da Pascoa; (2) ao domingo a antifona vem do Proprio do Tempo no '
      'Advento (12 dias), Septuagesima (9), Quaresma (12) e Paixao (6), '
      'mas NAO na Pascoa, onde vem do salterio do tempo.'),

    L('Salmos',
      PSDOM, PSDIA, PSDIA, ORDPS, PSDIA,
      '167 f; 168 c; 169 d; 166 f; 171 d'),

    L('Capitulo e responsorio breve',
      PRCOM, PRCOM, PRCOM,
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      '241 (nas outras horas, do Ordinario ou Salterio, ou do Proprio ou '
      'Comum, conforme o tipo de oficio); 166 f; 171 d. '
      'CORRIGIDO: a celula era Ord+Ps fixo. Nos 365 dias de 2026, ao '
      'domingo, o capitulo vem do Proprio do Tempo em todo o Advento, '
      'Septuagesima, Quaresma, Paixao e Pascoa (54 dias), e do '
      'Ordinario/Salterio no resto do ano (75 dias). A norma 241 remete '
      'para "conforme os diferentes tipos de Oficio", sem detalhar o tempo.'),

    L('Oracao',
      PRCOM, PRCOM, PRCOM, PDT,
      Conforme('oracao do domingo anterior',
               ('se a feria tiver oracao propria', PDT),
               ('nas vigilias', 'a oracao propria da vigilia')),
      '167 f; 168 c; 169 d; 166 f; 171 d ("colecta como em Laudes")'),

    L('O resto',
      ORD, ORD, ORD, ORD, ORD,
      '160'),
]

# --------------------------------------------------------------------------
# VESPERAS
# --------------------------------------------------------------------------
# Ao contrario da versao anterior, esta NAO e deduzida da tabela de Laudes:
# vem das mesmas normas 166 g, 167 g, 168 a, 169 b, 171 b.

VESPERAS = [
    L('Antifonas',
      PRCOM, PRCOM,
      Conforme(PSDIA, ('se a festa tiver proprias ou do Comum (norma 177)', PRCOM)),
      ORDPS, PSDIA,
      '167 g; 168 a; 169 b + 177; 166 g; 171 b'),

    L('Salmos',
      PRCOM, PRCOM, PSDIA, ORDPS, PSDIA,
      '167 g; 168 a; 169 b; 166 g; 171 b'),

    L('Capitulo, hino e versiculo',
      PRCOM, PRCOM, PRCOM,
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      Conforme(ORDPS, (TEMPOS_PROPRIOS, PDT)),
      '167 g; 168 a; 169 b; 166 g; 171 b. CORRIGIDO pelo mesmo levantamento '
      'que a linha equivalente de Laudes.'),

    L('Antifona do Magnificat',
      PRCOM, PRCOM, PRCOM, PDT, PDT,
      '167 g; 168 a; 169 b; 166 g; 171 b. CORRIGIDO pelo mesmo motivo da '
      'antifona do Benedictus: o gerador da PdT nos 95 dias feriais de 2026.'),

    L('Magnificat',
      ORD, ORD, ORD, ORD, ORD, '160'),

    L('Oracao',
      PRCOM, PRCOM, PRCOM, PDT,
      Conforme('oracao do domingo anterior',
               ('se a feria tiver oracao propria', PDT),
               ('nas vigilias', 'a oracao propria da vigilia')),
      '167 g; 168 a; 169 b; 166 g; 171 b'),
]

# As I Vesperas, quando existem, sao caso a parte — norma 164.
PRIMEIRAS_VESPERAS = (
    'Norma 164: a festa que nao tem I Vesperas proprias e que, por rubrica, '
    'venha a te-las, toma tudo das II Vesperas, salvo o que for dado como '
    'proprio das I Vesperas.\n'
    'Norma 166 a: no domingo, as I Vesperas sao "do Ordinario e do '
    'Salterio, do sabado precedente".'
)

# --------------------------------------------------------------------------
# COMPLETAS
# --------------------------------------------------------------------------
# A lei nao descreve peca a peca: diz de que DIA sao as Completas, e o
# resto e invariavel, do Ordinario.

COMPLETAS_DE_QUE_DIA = {
    'I':   'de domingo (norma 167 h); e as que seguem as I Vesperas, '
           'tambem de domingo (167 b)',
    'II':  'de domingo (norma 168 d)',
    'III': 'do dia da semana corrente (norma 169 e)',
    'DOM': 'de domingo (norma 166 h); mas as que seguem as I Vesperas '
           'do domingo sao DO SABADO (norma 166 b)',
    'FER': 'do dia da semana corrente (norma 171 e)',
}

COMPLETAS = [
    L('Antifona e salmos',
      PSDOM, PSDOM, PSDIA, PSDOM, PSDIA,
      '167 h; 168 d; 169 e; 166 h; 171 e — ver COMPLETAS_DE_QUE_DIA'),

    L('Capitulo',
      ORD, ORD, ORD, ORD, ORD,
      '241: em Completas e SEMPRE Tu autem in nobis'),

    L('Hino, responsorio breve, Nunc dimittis, oracao, conclusao',
      ORD, ORD, ORD, ORD, ORD, '160'),

    L('Antifona final de N. Senhora',
      ORD, ORD, ORD, ORD, ORD,
      '181 (manda dize-la, e isenta o Triduo Sacro e o oficio de defuntos). '
      'RESOLVIDO: estava marcada "por confirmar", porque a norma nao diz '
      'QUAL antifona em cada tempo. Os 365 dias de 2026 responderam: o '
      'gerador da-a como do Ordinario em 356 dias. Ou seja, a peca mora no '
      'Ordinario/Salterio e a escolha por tempo faz-se la dentro — em '
      'Psalterium/Mariaant.txt, com as seccoes Advent, Nativiti, '
      'Quadragesimae, Paschalis e Postpentecost. Nao e uma celula sazonal '
      'da matriz: e uma peca do Ordinario com variantes internas.'),
]

# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# A clausula que atravessa toda a matriz
# --------------------------------------------------------------------------
#
# Quase todas as normas de 165 a 177 terminam a mesma frase:
#
#   "salvo o que for dado como proprio"          (166 a, f, g)
#   "se nao houver proprias"                     (166 d, e; 171 c, d)
#   "salvo se forem dados como proprios ou do Comum (n. 177)"  (169 a, b)
#   "salvo o que for dado como proprio"          (171 b)
#
# Ou seja: TODA celula desta matriz da o caso NORMAL. Se o dia trouxer a
# peca como propria, e a propria que vale, venha ela do Proprio dos
# Santos, do Proprio do Tempo ou do Comum.
#
# Isto nao e detalhe: no confronto com os 365 dias de 2026, a maioria das
# discordancias que sobraram sao exatamente esta clausula a funcionar —
# um invitatorio proprio numa feria de Quaresma, uma antifona propria num
# sabado de Nossa Senhora, e assim por diante.
#
# O resolvedor tem de a implementar como regra geral: primeiro procurar a
# peca no proprio do dia; so depois cair na celula da matriz.
CLAUSULA_DO_PROPRIO = (
    'Toda celula da o caso normal. Se o dia trouxer a peca como propria, '
    'e a propria que vale. Normas 166 a/d/e/f/g, 169 a/b, 171 b/c/d, 177.'
)

HORAS = [
    ('Matinas', MATINAS),
    ('Laudes', LAUDES),
    ('Prima', PRIMA),
    ('Terca, Sexta e Noa', MENORES),
    ('Vesperas', VESPERAS),
    ('Completas', COMPLETAS),
]

# Arranjos inteiros que fogem da matriz e precisam de regra propria.
CASOS_A_PARTE = [
    ('Triduo Sacro e vigilia do Natal', 'norma 173: rubricas proprias, '
     'impressas no lugar respectivo do Breviario'),
    ('Oficio de defuntos', 'norma 173'),
    ('Pascoa e Pentecostes e os dias das suas oitavas',
     'norma 163 (Matinas de tres salmos e tres licoes) e norma 172 '
     '(nas horas menores, salmos de domingo; em Prima, como nas festas)'),
    ('Festas de II classe do Senhor na Septuagesima, Sexagesima e '
     'Quinquagesima', 'norma 174'),
    ('Dias dentro da oitava do Natal', 'norma 175'),
    ('Domingo dentro da oitava do Natal', 'norma 176'),
]
