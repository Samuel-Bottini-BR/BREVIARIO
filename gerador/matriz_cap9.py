"""
A matriz do capitulo IX do Hausmann, com a PROCEDENCIA de cada celula.

Isto e dado, nao logica. Nenhum resolvedor foi escrito ainda.

O ponto deste arquivo e distinguir quatro coisas que na pagina impressa
se confundem, e que na tabela que apresentei estavam todas com a mesma
aparencia de autoridade:

  'lido'     — o valor esta impresso na pagina, em letras. Confere-se
               olhando o livro.
  'aspas'    — a pagina traz " ("igual a celula de cima"). O valor aqui
               foi expandido por mim. Se eu errei para qual linha a aspa
               aponta, o valor sai errado e PARECE transcrito. Nao se
               pega comparando com a pagina: so relendo a coluna inteira
               de cima para baixo.
  'branco'   — a celula esta vazia na pagina. O valor None e leitura
               direta; o que significa esse vazio e inferencia minha.
  'derivado' — nao esta na pagina de forma nenhuma. Deduzi de uma regra
               em prosa. E onde eu posso ter errado sem que o livro me
               contradiga.

Colunas: I, II, III, DOM, FER
Fontes:  Ord, PS, CS, PdT, PsD, PsF, L1, L235, TeDeum, Resp, OfSun
"""

COLUNAS = ['I', 'II', 'III', 'DOM', 'FER']

# Cada linha: (peca, [(valor, procedencia) x 5])
# Escrito assim, e nao como tabela solta, para que a procedencia nao possa
# ser perdida ao copiar.

L = 'lido'
A = 'aspas'
B = 'branco'
D = 'derivado'


def linha(peca, valores, procs):
    return (peca, list(zip(valores, procs)))


MATINAS_INTRODUCAO = [
    linha('Domine, labia + mea',            ['Ord']*5,                      [L]*5),
    linha('+ Deus, in adiutorium',          ['Ord']*5,                      [A]*5),
    linha('Gloria Patri. Alleluia',         ['Ord']*5,                      [A]*5),
    linha('Invitatorio (duas vezes)',       ['PS','PS','CS','PsD','PsF'],   [L]*5),
    linha('Venite',                         ['Ord']*5,                      [L]*5),
    linha('Hino',                           ['PS','PS','CS','PsD','PsF'],   [L]*5),
]

# O primeiro e o segundo nocturnos sao identicos na pagina.
MATINAS_NOCTURNO_1_E_2 = [
    linha('Antifona, salmo, Gl.P., antifona - 3x',
          ['PS','PS','PsF','PsD','PsF'],   [L]*5),
    linha('Versiculo e resposta',   ['PS','PS',None,None,None],  [A,A,B,B,B]),
    linha('Pater noster (sem Amen)',['Ord','Ord',None,None,None],[L,L,B,B,B]),
    linha('Absolvicao',             ['Ord','Ord',None,None,None],[A,A,B,B,B]),
    linha('Iube, Domine. Bencao - 3x',
                                    ['Ord','Ord',None,None,None],[A,A,B,B,B]),
    linha('Licao. Tu autem - 3x',   ['PS','PS',None,None,None],  [L,L,B,B,B]),
    linha('Responsorio e versiculo - 3x',
                                    ['PS','PS',None,None,None],  [A,A,B,B,B]),
]

MATINAS_NOCTURNO_3 = [
    linha('Antifona, salmo, Gl.P., antifona - 3x',
          ['PS','PS','PsF','PsD','PsF'],   [A,A,L,L,L]),
    linha('Versiculo e resposta',
          ['PS','PS','PsF','PsD','PsF'],   [A]*5),
    linha('Pater noster. Absolvicao',      ['Ord']*5,            [L]*5),
    linha('Iube, Domine. Bencao - 2x',     ['Ord']*5,            [A]*5),
    linha('Licao. Tu autem - 2x',
          ['PS','PS','PdT','PdT','PdT'],   [L]*5),
    linha('Responsorio e versiculo - 2x',
          ['PS','PS','PdT','PdT','PdT'],   [A]*5),
    linha('Iube, Domine. Bencao (a terceira)', ['Ord']*5,        [L]*5),
    linha('Licao. Tu autem (a terceira)',
          ['PS','PS','PS','PdT','PdT'],    [L]*5),
    linha('Te Deum ou responsorio',
          ['TeDeum','TeDeum','TeDeum','TeDeum','Resp'], [L]*5),
]

MATINAS_CONCLUSAO = [
    linha('Domine, exaudi',                ['Ord']*5,            [L]*5),
    linha('Oremus. Oracao',
          ['PS','PS','PS','PdT','OfSun'],  [L]*5),
    linha('Domine, exaudi',                ['Ord']*5,            [L]*5),
    linha('Benedicamus Domino',            ['Ord']*5,            [A]*5),
    linha('Fidelium animae',               ['Ord']*5,            [A]*5),
]

LAUDES = [
    linha('+ Deus in adiutorium',          ['Ord']*5,            [L]*5),
    linha('Gloria Patri. Alleluia',        ['Ord']*5,            [A]*5),
    linha('Antifona - 5x',
          ['PS','PS','PsF','PsD','PsF'],   [L]*5),
    linha('Salmo. Gl.P. - 5x',
          ['PsD','PsD','PsF','PsD','PsF'], [L,L,A,A,A]),
    linha('Antifona repetida - 5x',
          ['PS','PS','PsF','PsD','PsF'],   [L,L,A,A,A]),
    linha('Capitulo, hino, versiculo, resposta',
          ['PS','PS','CS','PsD','PsF'],    [A,A,L,A,A]),
    linha('Antifona do Benedictus',
          ['PS','PS','CS','PdT','PsF'],    [A,A,A,L,A]),
    linha('+ Benedictus. Gl.P.',           ['Ord']*5,            [L]*5),
    linha('Antifona do Benedictus repetida',
          ['PS','PS','CS','PdT','PsF'],    [L]*5),
]

LAUDES_CONCLUSAO = [
    linha('Preces, se exigidas',   [None,None,None,None,'Ord'],  [B,B,B,B,L]),
    linha('Domine, exaudi',                ['Ord']*5,            [L,L,L,L,A]),
    linha('Oremus. Oracao',
          ['PS','PS','PS','PdT','OfSun'],  [L]*5),
]

LAUDES_COMEMORACOES = [
    linha('Antifona, versiculo, Oremus, oracao',
          [None,'PS','PS','PS','PS'],      [B,L,L,L,L]),
    linha('Domine, exaudi. Benedicamus Domino', ['Ord']*5,       [L]*5),
    linha('Fidelium animae',               ['Ord']*5,            [A]*5),
]

PRIMA = [
    linha('+ Deus, in adiutorium',         ['Ord']*5,            [L]*5),
    linha('Gl.P. Alleluia. Hino',          ['Ord']*5,            [A]*5),
    linha('Antifona',
          ['L1','PsF','PsF','PsD','PsF'],  [L]*5),
    linha('3 salmos, Gl.P. apos cada',
          ['PsD','PsF','PsF','PsD','PsF'], [L,A,A,A,A]),
    linha('Antifona repetida',
          ['L1','PsF','PsF','PsD','PsF'],  [L,A,A,A,A]),
    linha('Capitulo. Deo gratias',         ['Ord']*5,            [L]*5),
    linha('Responsorio breve',             ['Ord']*5,            [A]*5),
    linha('Domine, exaudi. Preces de Prima', ['Ord']*5,          [A]*5),
    linha('Lectio brevis. Tu autem',       ['Ord']*5,            [A]*5),
    linha('+ Adiutorium nostrum',          ['Ord']*5,            [A]*5),
    linha('Benedicite. Deus',              ['Ord']*5,            [A]*5),
    linha('+ Dominus nos benedicat',       ['Ord']*5,            [A]*5),
]

TERCA_SEXTA_NOA = [
    linha('+ Deus, in adiutorium',         ['Ord']*5,            [L]*5),
    linha('Gloria Patri. Alleluia. Hino',  ['Ord']*5,            [A]*5),
    linha('Antifona',
          ['L235','PsF','PsF','PsD','PsF'],[L]*5),
    linha('Salmos, Gloria Patri - 3x',
          ['PsD','PsF','PsF','PsD','PsF'], [L,A,A,A,A]),
    linha('Antifona repetida',
          ['L235','PsF','PsF','PsD','PsF'],[L,A,A,A,A]),
    linha('Capitulo. Deo gratias',
          ['PS','PS','CS','Ord','Ord'],    [L]*5),
    linha('Responsorio breve',
          ['PS','PS','CS','Ord','Ord'],    [A]*5),
    linha('Domine, exaudi',
          ['Ord','Ord','PS','Ord','Ord'],  [L]*5),
    linha('Oremus. Oracao',
          ['PS','PS','Ord','PdT','OfSun'], [L]*5),
    linha('Domine, exaudi',                ['Ord']*5,            [L,L,A,L,L]),
    linha('Benedicamus Domino',            ['Ord']*5,            [A]*5),
    linha('Fidelium animae',               ['Ord']*5,            [A]*5),
]

# O livro NAO imprime tabela de Vesperas. Da a regra em prosa:
#   "Vespers is just like Lauds except that the Benedictus is to be changed
#    to the Magnificat; that the psalms for the Officium festivum and the
#    Officium semifestivum are to be taken from the feast and not from
#    Sunday Lauds."
# Tudo abaixo e deducao minha a partir dessa frase e da tabela de Laudes.
VESPERAS = [
    linha('+ Deus in adiutorium',          ['Ord']*5,            [D]*5),
    linha('Gloria Patri. Alleluia',        ['Ord']*5,            [D]*5),
    linha('Antifona - 5x',
          ['PS','PS','PsF','PsD','PsF'],   [D]*5),
    linha('Salmo. Gl.P. - 5x',
          ['PS','PS','PsF','PsD','PsF'],   [D]*5),
    linha('Antifona repetida - 5x',
          ['PS','PS','PsF','PsD','PsF'],   [D]*5),
    linha('Capitulo, hino, versiculo, resposta',
          ['PS','PS','CS','PsD','PsF'],    [D]*5),
    linha('Antifona do Magnificat',
          ['PS','PS','CS','PdT','PsF'],    [D]*5),
    linha('+ Magnificat. Gl.P.',           ['Ord']*5,            [D]*5),
    linha('Antifona do Magnificat repetida',
          ['PS','PS','CS','PdT','PsF'],    [D]*5),
    linha('Oremus. Oracao',
          ['PS','PS','PS','PdT','OfSun'],  [D]*5),
]

COMPLETAS = [
    linha('Iube, Domine. Noctem quietam',  ['Ord']*5,            [L]*5),
    linha('Fratres: Sobrii',               ['Ord']*5,            [A]*5),
    linha('+ Adiutorium nostrum',          ['Ord']*5,            [A]*5),
    linha('Pater noster. Amen',            ['Ord']*5,            [A]*5),
    linha('Confiteor. Misereatur',         ['Ord']*5,            [A]*5),
    linha('+ Indulgentiam',                ['Ord']*5,            [A]*5),
    linha('Converte nos + (ao peito)',     ['Ord']*5,            [A]*5),
    linha('+ Deus, in adiutorium',         ['Ord']*5,            [A]*5),
    linha('Gloria Patri. Alleluia',        ['Ord']*5,            [A]*5),
    linha('Antifona (por inteiro)',
          ['PsD','PsD','PsF','PsD','PsF'], [L]*5),
    linha('Salmos. Gl.P. - 3x',
          ['PsD','PsD','PsF','PsD','PsF'], [A]*5),
    linha('Antifona repetida',
          ['PsD','PsD','PsF','PsD','PsF'], [A]*5),
    linha('Hino. Capitulo. Deo gratias',   ['Ord']*5,            [L]*5),
    linha('Responsorio breve',             ['Ord']*5,            [A]*5),
    linha('Ant. Salva nos (por inteiro)',  ['Ord']*5,            [A]*5),
    linha('+ Nunc dimittis',               ['Ord']*5,            [A]*5),
    linha('Ant. Salva nos repetida',       ['Ord']*5,            [A]*5),
    linha('Domine, exaudi',                ['Ord']*5,            [A]*5),
    linha('Oremus. Visita',                ['Ord']*5,            [A]*5),
    linha('Domine, exaudi',                ['Ord']*5,            [A]*5),
    linha('Benedicamus Domino',            ['Ord']*5,            [A]*5),
    linha('+ Benedicat et custodiat',      ['Ord']*5,            [A]*5),
    linha('Antiphona finalis B.M.V.',      ['Ord']*5,            [A]*5),
    linha('+ Divinum auxilium',            ['Ord']*5,            [A]*5),
]

TABELAS = [
    ('Matinas - introducao',                MATINAS_INTRODUCAO),
    ('Matinas - primeiro nocturno',         MATINAS_NOCTURNO_1_E_2),
    ('Matinas - segundo nocturno',          MATINAS_NOCTURNO_1_E_2),
    ('Matinas - terceiro nocturno',         MATINAS_NOCTURNO_3),
    ('Matinas - conclusao se parar aqui',   MATINAS_CONCLUSAO),
    ('Laudes',                              LAUDES),
    ('Laudes - conclusao',                  LAUDES_CONCLUSAO),
    ('Laudes - comemoracoes',               LAUDES_COMEMORACOES),
    ('Prima',                               PRIMA),
    ('Terca, Sexta e Noa',                  TERCA_SEXTA_NOA),
    ('Vesperas (DERIVADA, nao impressa)',   VESPERAS),
    ('Completas',                           COMPLETAS),
]

# Os dois pontos em que o livro parece discordar de si mesmo. Nao foram
# corrigidos aqui: a matriz guarda o que a pagina diz. A decisao e do
# Padre, com desempate no Perl do Divinum Officium.
DISCREPANCIAS = [
    {
        'onde': 'Terca, Sexta e Noa — coluna III',
        'o_que_a_pagina_diz': "Domine exaudi = PS ; Oremus. Oracao = Ord",
        'por_que_estranha': (
            'Em todas as outras colunas e o inverso. O Domine exaudi e '
            'versiculo invariavel; a oracao e a peca mais propria que existe.'),
        'o_que_o_proprio_livro_diz_noutro_lugar': (
            'O oficio-modelo do capitulo XV, que e um III classe, traz em '
            'Terca: "From the Ord. but the prayer from the Proprium".'),
    },
    {
        'onde': 'Terca, Sexta e Noa — colunas DOM e FER',
        'o_que_a_pagina_diz': 'Capitulo e responsorio breve = Ord',
        'por_que_estranha': (
            'O oficio-modelo do capitulo XIV imprime esses capitulos sob '
            '"From the Psalterium", e no Divinum Officium eles moram em '
            'Psalterium/Special/Minor Special.txt.'),
        'o_que_o_proprio_livro_diz_noutro_lugar': (
            'A nota 1 do capitulo II avisa que o autor cita cada peca da '
            'secao a que ela propriamente pertence, e que as edicoes '
            'reimprimem pecas do Ordinarium dentro do Salterio. Pode ser '
            'diferenca de arrumacao, nao de conteudo.'),
    },
]
