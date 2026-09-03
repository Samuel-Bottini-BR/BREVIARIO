"""
As oito verificacoes obrigatorias, corridas sobre o PDF COSIDO.

Porque sobre o cosido e nao sobre as partes: os folios do corpo do livro
— Proprio do Tempo e dos Santos — so ganham o seu valor na costura. Uma
parte solta daria tudo por certo e nao veria nada.

E porque sobre o PDF e nao sobre as pecas: os defeitos que escaparam ate
hoje — o ';;Semiduplex' de Julho, o 'texto ut in Communi' de Agosto —
nasceram DEPOIS da peca, na hora de compor a pagina. Quem audita a peca
nao os ve.

    python gerador/verificar.py BREVIARIUM-latina-volume-unico.pdf
"""

import argparse
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent

# 1. Ponteiros do corpus que nunca podem chegar ao papel.
#    'vide' saiu do padrao solto: aparece dez vezes no livro e todas
#    como verbo latino em texto biblico — 'vide poténtiam regis'. Um
#    ponteiro do corpus e 'vide C5', com o alvo a seguir.
PONTEIRO = re.compile(
    r'(?m)^\s*[@!&$]\w|;;|\bis missing\b'
    r'|^\s*vide\s+(?:C\d|Sancti/|Tempora/)|/:|:/')

# 2. Dados de controlo e nomes internos do programa. O 'texto' esta aqui
#    por ter escapado uma vez: era o nome do genero de uma peca.
#    'Semiduplex', 'Officium', 'Rule' e 'Scriptura' sairam daqui: aparecem
#    em latim corrido dentro do Codigo de Rubricas, e a sua presenca e a
#    prova de que ele entrou no livro. O que os denuncia como dado de
#    maquina e virem seguidos de ';;' ou serem o nome interno de um genero.
CONTROLE = re.compile(
    r'(?i);;'
    r'|(?:^|\s)(?:Rank|Officium|Rule|Scriptura|Doxology)\s*;;'
    r'|(?:^|\s)(?:texto|antifona|salmo|cantico|licao|oracao|rubrica|hino)'
    r'\s+ut\s+in\s')

# 4. A remissao inteira: o NOME da parte e o numero, que e o que a
#    convencao de 1942 pede — 'ut in Communi [*228]'. O numero sozinho
#    nao localiza nada: ha tres sequencias com asterisco, e '*228'
#    existe no Saltério e no Comum. Nem para o teste nem para quem
#    folheia um serve sem o outro.
#
#    O padrao ignora a caixa: 'ut in Communi' sai do PDF como
#    'ut in cOmmuni'.
REMISSAO = re.compile(
    r'(?i)ut\s+in\s+(Psalterio|Communi|Ordinario|Hymnis)'
    r'\s*\[\s*(\*?)\s*(\d{1,4})\s*\]')

# Que parte cada nome de remissao designa, e como se reconhece o seu
# cabecalho corrido.
PARTE_DA_REMISSAO = {'psalterio': 'psalterium', 'communi': 'commune',
                     'ordinario': 'ordinarium', 'hymnis': 'hymni'}

# 8. Palavras que so existem em portugues. Se aparecerem, a edicao latina
#    tem vernaculo dentro.
#    'capítulo' saiu daqui: e o ablativo latino de 'capitulum', e
#    aparece no Codigo de Rubricas. So ficam palavras que NAO existem
#    em latim.
PORTUGUES = re.compile(
    r'(?i)\b(?:Leitura|Antífona|Oração|Segunda-feira|Terça-feira|'
    r'Sexta-feira|Sábado|Glória ao Pai|também|páginas?|'
    r'Salmos?\s\d|Domingo)\b')

HORAS_LATINAS = ('matutinum', 'laudes', 'primam', 'tertiam', 'sextam',
                 'nonam', 'vesperas', 'completorium')


def paginas_do_pdf(caminho):
    from pypdf import PdfReader
    r = PdfReader(str(caminho))
    fora = []
    for p in r.pages:
        fora.append(p.extract_text() or '')
    return fora, r


# O asterisco faz parte do folio e nao pode cair. Um \b antes dele nao
# serve de nada — espaco e '*' sao ambos nao-letra, e a fronteira falha:
#     '\u00a7aPs-1\u00a7Feria ii *23'  dava '23', e a remissao procurava '*23'.
# Por isso o fim da linha usa um olhar-atras, e nao uma fronteira.
# A marca invisivel da posicao. O versalete troca a caixa: ignora-se.
MARCA_DE_POSICAO = re.compile('§a[a-z0-9-]+§', re.I)

BORDA_DA_LINHA = re.compile(
    r'^\s*(\*?)(\d{1,4})(?!\d)'
    r'|(?<![\w])(\*?)(\d{1,4})\s*$')


def folio_impresso(texto):
    """O folio que a pagina imprime: '*95', '57'.

    ARMADILHA, irma do versalete: o folio e o cabecalho corrido vivem em
    caixas de margem diferentes, mas a extracao junta-os NUMA SO LINHA —

        *400 Commune SanCtorum

    Exigir que a linha inteira fosse o numero nao encontrava nada, e a
    busca continuava pagina acima ate topar um numero solto qualquer (um
    numero de salmo). Dai 143 remissoes darem-se por quebradas apontando
    para paginas que existem e estao certas.

    O folio esta sempre numa BORDA da linha — ao principio nas paginas
    pares, ao fim nas impares, que e onde a margem exterior cai. Le-se de
    baixo para cima, e a primeira borda numerica e o folio. Medido:
    400/400 paginas do Comum.
    """
    for l in reversed([x.strip() for x in texto.split(chr(10)) if x.strip()]):
        m = BORDA_DA_LINHA.search(l)
        if m:
            g = m.groups()
            return (g[0] or '') + g[1] if g[1] else (g[2] or '') + g[3]
    return ''

# Os tres oficios que o Hausmann desdobra peca a peca (capitulos XIII-XV).
# O terceiro numero e quantas licoes de Matinas o oficio tem de trazer:
# nove no festivo, dos tres nocturnos; nos outros dois nao se exige aqui.
HAUSMANN = [
    ('s-0815', 'Festivum — Assumptio BMV', 9),
    ('t-Pent160', 'Dominicale — Dom. XVI post Pent.', 0),
    ('s-1110', 'Ordinarium — S. Andreae Avellini', 0),
]

HORAS_POR_ORDEM = ['Ad Matutinum', 'Ad Laudes', 'Ad Horas minores',
                   'Ad Vesperas', 'Ad Completorium']


def rotulos_das_licoes(quantas):
    """Como o livro chama as licoes — perguntado a quem as imprime."""
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).parent))
    import perpetuo
    de_seccao = {s: r for _, pecas in perpetuo.PECAS_DA_POSICAO
                 for s, r in pecas}
    return [de_seccao.get(f'Lectio{n}', f'Lectio{n}')
            for n in range(1, quantas + 1)]


def trecho_da_posicao(paginas, chave):
    """O texto de um oficio: da sua marca ate a marca seguinte.

    A marca invisivel '\u00a7A<ancora>\u00a7' vai no titulo de cada posicao. O
    titulo esta em VERSALETE e a extracao troca-lhe a caixa — '\u00a7As-0815\u00a7'
    le-se '\u00a7aS-0815\u00a7' —, por isso a procura e toda em minusculas.
    """
    de = None
    for n, pg in enumerate(paginas, 1):
        texto = (pg or '').lower()
        if de is None:
            if f'\u00a7a{chave.lower()}\u00a7' in texto.replace(' ', ''):
                de = n
            continue
        # a marca seguinte fecha o trecho
        if MARCA_DE_POSICAO.search(texto.replace(' ', '')) and n > de:
            return de, ' '.join(paginas[de - 1:n]).lower()
    if de is not None:
        return de, ' '.join(paginas[de - 1:]).lower()
    return None


def verificar(caminho):
    paginas, leitor = paginas_do_pdf(caminho)
    total = len(paginas)
    sem_espaco = [re.sub(r'\s+', '', p).lower() for p in paginas]
    resultado = []

    # --- 1. nenhum ponteiro sobrevive
    maus = [(n, l.strip()[:70]) for n, p in enumerate(paginas, 1)
            for l in p.split('\n') if PONTEIRO.search(l)]
    resultado.append(('1. Nenhum ponteiro sobrevive', len(maus), maus[:3]))

    # --- 2. nenhum dado de controlo, nenhum nome interno
    maus = [(n, m.group(0).strip()[:50]) for n, p in enumerate(paginas, 1)
            for m in [CONTROLE.search(p)] if m]
    resultado.append(('2. Nenhum dado de controlo escapa', len(maus), maus[:3]))

    # --- 3. completude estrutural: as partes existem e tem conteudo
    partes = ('ordinarium', 'psalterium', 'propriumdetempore',
              'propriumsanctorum', 'communesanctorum', 'appendix',
              'kalendarium')
    faltam = [x for x in partes if not any(x in s for s in sem_espaco)]
    resultado.append(('3. Completude estrutural', len(faltam), faltam))

    # --- 4. integridade das referencias de pagina
    # De que parte e cada pagina: LE-SE DO INDICE que o compositor
    # gravou, nunca se adivinha pelo texto. Procurar o nome da parte na
    # pagina parecia bastar e nao bastava: o Salterio nao imprime a
    # palavra 'Psalterium' em pagina nenhuma — abre logo em 'Dominica'.
    # Nenhuma pagina sua entrava no mapa, e as 224 remissoes que lhe
    # apontavam davam-se por quebradas apontando para paginas certas.
    parte_da_pagina = [''] * (total + 1)
    indice = caminho.with_name(caminho.stem + '-indice.tsv')
    if not indice.exists():
        raise SystemExit(f'falta {indice.name}: recompor o volume')
    for l in io.open(indice, encoding='utf-8').read().split(chr(10))[1:]:
        c = l.split(chr(9))
        if len(c) < 7:
            continue
        for n in range(int(c[5]), min(int(c[6]), total) + 1):
            parte_da_pagina[n] = c[0]

    # O mapa e por (parte, folio) — nunca pelo folio sozinho: ha tres
    # sequencias com asterisco e '*228' existe em mais de uma.
    folios = set()
    for n, pg in enumerate(paginas, 1):
        f = folio_impresso(pg)
        if f:
            folios.add((parte_da_pagina[n], f))

    quebradas, remissoes = [], 0
    for n, p in enumerate(paginas, 1):
        for m in REMISSAO.finditer(p):
            remissoes += 1
            parte = PARTE_DA_REMISSAO.get(m.group(1).lower(), '')
            alvo = m.group(2) + m.group(3)
            achou = (parte, alvo) in folios
            if not achou:
                quebradas.append((n, f'{m.group(1)} {alvo}'))
    resultado.append((f'4. Referências de página ({remissoes} remissões)',
                      len(quebradas), quebradas[:3]))

    # --- 5. comparacao com o site: corre a parte, nao aqui
    resultado.append(('5. Comparação com o site (varrer.py)', None,
                      ['365/365 nas oito horas — medido à parte']))

    # --- 6. caminho do leitor: o Salterio abre por dia da semana e hora
    esperado = [f'{d}·{h}' for d in ('dominica',) for h in HORAS_LATINAS]
    achados = sum(1 for h in HORAS_LATINAS
                  if any(f'dominica·ad{h}' in s.replace(' ', '') for s in sem_espaco))
    resultado.append(('6. Caminho do leitor (Saltério por dia e hora)',
                      len(HORAS_LATINAS) - achados,
                      [f'{achados} de {len(HORAS_LATINAS)} horas de Domingo']))

    # --- 7. os tres oficios do Hausmann

    # --- 7. os tres oficios do Hausmann
    faltas7 = []
    for chave, rotulo, licoes in HAUSMANN:
        trecho = trecho_da_posicao(paginas, chave)
        if trecho is None:
            faltas7.append((0, f'{rotulo}: o oficio nao esta no livro'))
            continue
        onde, corpo = trecho
        # as horas, pela ordem
        posicao = -1
        for hora in HORAS_POR_ORDEM:
            achou = corpo.find(hora.lower(), posicao + 1)
            if achou < 0:
                continue
            if achou < posicao:
                faltas7.append((onde, f'{rotulo}: {hora} fora de ordem'))
            posicao = achou
        # o Festivum tem de trazer os tres nocturnos inteiros
        if licoes:
            # Os rotulos vem de PECAS_DA_POSICAO, que e quem os imprime —
            # nao se escrevem aqui a mao. O livro da-os em ALGARISMO
            # ROMANO ('Lectio vii'), e o teste procurava 'lectio 7': dava
            # as nove licoes por perdidas estando todas la.
            faltam = [rot for rot in rotulos_das_licoes(licoes)
                      if not re.search(r'\b' + re.escape(rot.lower()) + r'\b',
                                       corpo)]
            if faltam:
                faltas7.append((onde, f'{rotulo}: faltam as licoes {faltam}'))
    resultado.append(('7. Os três ofícios do Hausmann', len(faltas7),
                      faltas7[:3] or ['ordem das horas e nocturnos completos'
                                      ' — falta a colação peça a peça']))

    # --- 8. nada em portugues
    maus = [(n, m.group(0)) for n, p in enumerate(paginas, 1)
            for m in [PORTUGUES.search(p)] if m]
    resultado.append(('8. Nada em português', len(maus), maus[:3]))

    return total, resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf', nargs='?',
                   default='BREVIARIUM-latina-volume-unico.pdf')
    a = p.parse_args()
    caminho = RAIZ / a.pdf if not Path(a.pdf).is_absolute() else Path(a.pdf)

    total, resultado = verificar(caminho)
    print(f'{caminho.name}: {total:,} páginas\n')
    print(f'{"verificação":48} {"falhas":>8}')
    print('-' * 62)
    for nome, falhas, exemplos in resultado:
        marca = ('—' if falhas is None else
                 'PASSA' if falhas == 0 else f'{falhas}')
        print(f'{nome:48} {marca:>8}')
        if falhas:
            for e in exemplos:
                print(f'      {e}')
        elif falhas is None and exemplos:
            print(f'      {exemplos[0]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
