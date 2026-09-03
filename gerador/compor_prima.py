"""
Compoe a Prima de um dia qualquer.

A Prima tem esqueleto proprio — 'Ordinarium/Prima.txt' — e duas pecas que
mais nenhuma hora tem:

  o Martirologio    a lista dos santos do dia SEGUINTE, que se le hoje.
                    Abre pela idade da lua: 'Nonis Augústi Luna vicésima
                    prima. Anno Dómini 2026'.
  o Capitulo        'De Officio Capituli', que nas rubricas de 1960 se diz
                    a seguir ao Martirologio.

Tudo o resto — o hino, os salmos, o capitulo breve, a oracao — vem da
mesma maquina das outras horas menores.

uso:
    python compor_prima.py --data 08-04-2026
    python compor_prima.py --data 12-25-2026 --edicao latina
"""

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import ler_arquivo
from resolver import Resolvedor
from funcoes import Funcoes
from proprio import Dia
import alleluia
import compor
import compor_menores

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ
REPO = compor.REPO
VERSAO = compor.VERSAO

ESPECIAL_PRIMA = 'Psalterium/Special/Prima Special.txt'


def montar(data, com_vernaculo=True):
    hora = 'Prima'
    ordo = compor.ordo_do_ano(data)
    registo = ordo.dia(data, hora)
    if registo is None:
        raise SystemExit(f'o Ordo nao tem {data} — gerar com '
                         f'"python gerador/ordo.py --ano {data[-4:]}"')

    dow = (int(registo.dayofweek) if registo.dayofweek
           else compor.DIAS.index(compor.dia_da_semana(data)))
    ctx = compor.contexto_do_dia(hora, dow, registo, data)
    r = Resolvedor(REPO, ctx)

    dia = Dia(r, registo.vencedor, VERSAO, registo=registo)
    dia_ver = (Dia(r, registo.vencedor, VERSAO, lang='Portugues',
                   registo=registo) if com_vernaculo else None)
    f = Funcoes(r, compor.estado_do_dia(hora, dow, registo, dia))

    pascal = alleluia.e_tempo_pascal(registo.tempo)
    # Da Septuagesima ao sabado santo apaga-se todo o alleluia que o
    # texto traga escrito — mesmo o que vem do Comum.
    suprime = alleluia.suprime_se(registo.tempo, 'Prima', dow,
                                 int(registo.vespera or 0))
    al = alleluia.Alleluia(r)

    def texto(lang, bruto):
        saida = bruto
        for _ in range(6):
            novo = f.expandir(r.expandir_formulas(saida, lang), lang)
            if novo == saida:
                break
            saida = novo
        saida = '\n'.join(l for l in saida.split('\n')
                          if not l.startswith('#'))
        return alleluia.tempo(saida, pascal, suprime)

    def par(bruto):
        return (texto('Latin', bruto),
                texto('Portugues', bruto) if com_vernaculo else '')

    especial = dia.secoes.get(f'Special {hora}') or ''
    if especial.strip():
        esqueleto = compor.esqueleto_especial(especial)
    else:
        esqueleto = ler_arquivo(REPO / 'web/www/horas/Ordinarium/Prima.txt',
                                ctx).get('__preambulo', [])

    pecas = []
    bloco_aberto = ['']
    a_calar = [False]
    # O '#Prelude' do original: a rubrica que o oficio do dia poe antes
    # de tudo o resto.
    abertura = compor.prelude(dia, 'Prima')
    if abertura:
        pecas.append(compor.Peca(
            'rubrica', 'Prelude', texto('Latin', abertura),
            texto('Portugues', compor.prelude(dia_ver, 'Prima'))
            if com_vernaculo and dia_ver is not None else ''))

    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            a_calar[0] = compor.omitir_bloco(dia.rule, nome, hora)
            if a_calar[0]:
                # Na oitava da Pascoa nao ha capitulo em hora nenhuma: no
                # lugar dele diz-se o versiculo 'Hæc dies'.
                if ('Capitulum' in nome
                        and compor.versiculo_no_lugar(dia.rule, hora)):
                    p = compor_menores._versiculo_em_lugar_do_capitulo(
                        r, texto, dia, dia_ver, com_vernaculo)
                    if p:
                        pecas.append(p)
                continue

            if nome == 'Hymnus':
                p = _hino(r, texto, com_vernaculo)
                if p:
                    pecas.append(p)
            elif nome == 'Psalmi':
                bloco = compor._salmos(r, f, hora, dow, com_vernaculo,
                                       dia, al, pascal)
                if bloco:
                    bloco[0].titulo_lat = r.titulo('Psalmi', 'Latin')
                    if com_vernaculo:
                        bloco[0].titulo_ver = r.titulo('Psalmi', 'Portugues')
                pecas.extend(bloco)
            elif nome == 'Capitulum Responsorium Versus':
                p = _capitulo(r, texto, al, dia, registo, nome,
                              com_vernaculo, pascal)
                if p:
                    pecas.append(p)
            elif nome == 'Martyrologium':
                p = _martirologio(r, texto, registo, nome, com_vernaculo,
                                  dia.rule)
                if p:
                    pecas.append(p)
            elif nome == 'Lectio brevis':
                p = _licao_breve(r, texto, registo, nome, com_vernaculo)
                if p:
                    pecas.append(p)
            elif nome == 'Oratio' and re.search(r'Limit.*?Oratio', dia.rule,
                                               re.I):
                # No Triduo Sacro a Prima nao reza a oracao do costume: o
                # proprio do dia traz a sua, com o 'Christus factus est' e
                # o Pater noster dito em silencio.
                p = _oracao_do_triduo(r, texto, dia, dia_ver, com_vernaculo)
                if p:
                    pecas.append(p)
                a_calar[0] = True
            elif nome in compor.SO_TITULO or nome == 'De Officio Capituli':
                bloco_aberto[0] = nome
            elif nome not in ('Capitulum Versus', 'Preces Dominicales',
                              'Preces Feriales',
                              'Preces Dominicales et Feriales',
                              'Regula vel Lectio brevis',
                              'Regula vel Evangelium',
                              'Commemoratio defunctorum',
                              'Commemoratio officii parvi B.M.V.'):
                print(f'  BLOCO SEM TRATAMENTO: {nome}', file=sys.stderr)
            continue

        if not a_calar[0]:
            lat, ver = par(l)
            if not lat.strip():
                continue
            gen = 'rubrica' if l.startswith('$rubrica ') else 'texto'
            tl = tv = ''
            if bloco_aberto[0]:
                tl = r.traduzir(bloco_aberto[0], 'Latin')
                tv = (r.traduzir(bloco_aberto[0], 'Portugues')
                      if com_vernaculo else '')
                bloco_aberto[0] = ''
            pecas.append(compor.Peca(gen, '', lat, ver, tl, tv))

    return pecas, r, registo


# --------------------------------------------------------------------------

def _hino(r, texto, com_vernaculo):
    """O 'Iam lucis orto sídere', que abre o dia."""
    def buscar(lang):
        return (r.setupstring(lang, ESPECIAL_PRIMA).get('Hymnus Prima')
                or '').strip()

    lat = texto('Latin', buscar('Latin'))
    if not lat.strip():
        return None
    return compor.Peca('hino', 'Hymnus Prima', lat,
                       texto('Portugues', buscar('Portugues'))
                       if com_vernaculo else '',
                       r.titulo('Hymnus', 'Latin'),
                       r.titulo('Hymnus', 'Portugues') if com_vernaculo else '')


def _capitulo(r, texto, al, dia, registo, nome_do_bloco, com_vernaculo,
              pascal):
    """Porta de capitulum_prima.

    Nas rubricas de 1960 o capitulo breve da Prima e sempre o de domingo —
    a variante ferial so existe nas rubricas antigas.
    """
    variante_resp = _variante_do_responsorio(dia, registo)

    def montar_um(lang):
        secoes = r.setupstring(lang, ESPECIAL_PRIMA)
        capit = (secoes.get('Dominica') or '').rstrip()
        if not capit:
            return ''
        capit += '\n$Deo gratias\n_\n'

        resp = (secoes.get('Responsory') or '').split('\n')
        proprio = (secoes.get(f'Responsory {variante_resp}') or '').strip() \
            if variante_resp else ''
        do_dia, _ = dia.proprium('Versum Prima')
        if do_dia and do_dia.strip():
            proprio = do_dia.strip()
        if proprio and len(resp) > 2:
            resp[2] = f'V. {proprio}'
        resp.append('_')
        resp.extend((secoes.get('Versum') or '').split('\n'))
        return capit + al.responsorio_breve(
            '\n'.join(resp), lang, pascal, dia.rule, 'Prima')

    lat = texto('Latin', montar_um('Latin'))
    if not lat.strip():
        return None
    return compor.Peca('texto', 'Capitulum', lat,
                       texto('Portugues', montar_um('Portugues'))
                       if com_vernaculo else '',
                       r.titulo(nome_do_bloco, 'Latin'),
                       r.titulo(nome_do_bloco, 'Portugues')
                       if com_vernaculo else '')


def _oracao_do_triduo(r, texto, dia, dia_ver, com_vernaculo):
    """A oracao da Prima nos tres ultimos dias da Semana Santa."""
    # No Sabado Santo nao ha '[Oratio]': ha '[Oratio 2]', a de Laudes.
    def buscar(d):
        if d is None:
            return ''
        for nome in ('Oratio', 'Oratio 2', 'Oratio 3'):
            t, _ = d.proprium(nome, flag=True)
            if t and t.strip():
                return t
        return ''

    bl = buscar(dia)
    if not (bl and bl.strip()):
        return None
    bv = buscar(dia_ver) if com_vernaculo else ''
    return compor.Peca('oracao', 'Oratio', texto('Latin', bl),
                       texto('Portugues', bv or '') if com_vernaculo else '',
                       r.titulo('Oratio', 'Latin'),
                       r.titulo('Oratio', 'Portugues') if com_vernaculo else '')


def _variante_do_responsorio(dia, registo):
    """Porta de get_prima_responsory.

    O versiculo do responsorio da Prima muda com o tempo — 'Qui natus es
    de María Vírgine' no Natal, 'Qui surrexísti a mórtuis' na Pascoa. Nao
    basta o tempo litúrgico: a regra do dia pode dize-lo, pela linha
    'Doxology=', e e ela que manda.
    """
    chave = registo.variante('Prima responsory')

    # A regra pode estar no oficio COMEMORADO — e o caso da Maternidade de
    # Nossa Senhora, comemorada num domingo depois de Pentecostes.
    regra_comemorado = ''
    if registo.comemorado:
        try:
            regra_comemorado = (dia.r.setupstring('Latin', registo.comemorado)
                                .get('Rule') or '')
        except (FileNotFoundError, OSError):
            regra_comemorado = ''

    m = (re.search(r'Doxology=(Nat|Epi|Pasch|Asc|Corp|Heart)', dia.rule, re.I)
         or re.search(r'Doxology=(Nat|Epi|Pasch|Asc|Corp|Heart)',
                      dia.regra_do_comum, re.I)
         or re.search(r'Doxology=(Nat|Epi|Pasch|Asc|Corp|Heart)',
                      regra_comemorado, re.I))
    if m:
        chave = m.group(1)

    # Na primeira metade de Dezembro diz-se o do Advento — menos no dia 12.
    mes, dia_do_mes, _ = (int(x) for x in registo.data.split('-'))
    if mes == 12 and 8 < dia_do_mes < 16 and dia_do_mes != 12:
        chave = 'Adv'

    # Corpus Christi e o Sagrado Coracao nao tem responsorio proprio nas
    # rubricas de 1960.
    if re.search(r'Corp|Heart', chave or ''):
        chave = ''
    return chave


def _licao_breve(r, texto, registo, nome_do_bloco, com_vernaculo):
    """A licao breve da Prima, que muda com o tempo liturgico."""
    variante = registo.variante('Lectio brevis Prima') or 'Per Annum'

    def buscar(lang):
        corpo = (r.setupstring(lang, ESPECIAL_PRIMA).get(variante)
                 or '').strip()
        if not corpo:
            return ''
        # A licao breve da Prima le-se com bencao antes e o 'Tu autem'
        # depois, como todas as licoes do Oficio.
        return f'$benedictio Prima\n{corpo}\n$Tu autem'

    lat = texto('Latin', buscar('Latin'))
    if not lat.strip():
        return None
    return compor.Peca('texto', 'Lectio brevis', lat,
                       texto('Portugues', buscar('Portugues'))
                       if com_vernaculo else '',
                       r.titulo(nome_do_bloco, 'Latin'),
                       r.titulo(nome_do_bloco, 'Portugues')
                       if com_vernaculo else '')


def _martirologio(r, texto, registo, nome_do_bloco, com_vernaculo,
                  regra=''):
    """O Martirologio do dia seguinte, que se le hoje.

    O ficheiro, a linha da lua e a chave da entrada movel vem colhidos no
    Ordo — sao contas de calendario. Aqui so se le o ficheiro e se marca
    cada linha como versiculo, que e o que o original faz.
    """
    if not registo.martir_ficheiro:
        return None

    def montar_um(lang):
        try:
            bruto = r.preambulo(lang, registo.martir_ficheiro)
        except (FileNotFoundError, OSError):
            bruto = None
        if bruto is None and lang != 'Latin':
            bruto = r.preambulo('Latin', registo.martir_ficheiro)
        if not bruto:
            return ''
        linhas = [l for l in bruto.split('\n')]
        while linhas and not linhas[-1].strip():
            linhas.pop()
        if not linhas:
            return ''
        # A primeira linha e a data romana, e leva a lua a seguir.
        if registo.martir_luna:
            linhas[0] = f'{linhas[0].rstrip()} {registo.martir_luna}'
        # A entrada movel entra no lugar do '_'.
        movel = _entrada_movel(r, lang, registo)
        fora = []
        for l in linhas:
            if l.strip() == '_':
                if movel:
                    fora.append(f'r. {movel}')
                continue
            fora.append(f'r. {l}' if len(l) > 4 and not l.startswith('/:')
                        else l)
        if fora:
            fora[0] = re.sub(r'^r', 'v', fora[0])
        saida = '\n'.join(fora) + '\n$Conclmart'
        # A 'Pretiosa' fecha o Martirologio — salvo no Oficio de Defuntos.
        if not re.search(r'ex C9', regra, re.I):
            saida += '\n$Pretiosa'
        return saida

    lat = texto('Latin', montar_um('Latin'))
    if not lat.strip():
        return None
    return compor.Peca('texto', 'Martyrologium', lat,
                       texto('Portugues', montar_um('Portugues'))
                       if com_vernaculo else '',
                       r.traduzir(nome_do_bloco, 'Latin'),
                       r.traduzir(nome_do_bloco, 'Portugues')
                       if com_vernaculo else '')


def _entrada_movel(r, lang, registo):
    """A linha do Martirologio que depende da semana — a festa movel que
    se anuncia. A chave vem do Ordo."""
    if not registo.martir_movel:
        return ''
    pasta = str(Path(registo.martir_ficheiro).parent)
    try:
        secoes = r.setupstring(lang, f'{pasta}/Mobile.txt')
    except FileNotFoundError:
        return ''
    return (secoes.get(registo.martir_movel) or '').strip()


# --------------------------------------------------------------------------

def main():
    data = None
    bilingue = True
    if '--data' in sys.argv:
        data = sys.argv[sys.argv.index('--data') + 1]
    if '--edicao' in sys.argv:
        bilingue = sys.argv[sys.argv.index('--edicao') + 1] != 'latina'
    if not data:
        raise SystemExit('indique --data MM-DD-AAAA')

    pecas, r, registo = montar(data, com_vernaculo=bilingue)
    nome = f"prima-{data}-{'bilingue' if bilingue else 'latina'}.html"
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(
        compor_menores.folha(pecas, 'Prima', registo, bilingue))

    print(f'escrito {nome}')
    print(f'  {registo.nome} [{registo.vencedor}]')
    print(f'  {len(pecas)} peças')


if __name__ == '__main__':
    main()
