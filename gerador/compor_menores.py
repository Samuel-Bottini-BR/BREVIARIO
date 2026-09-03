"""
Compoe as horas menores — Terca, Sexta e Noa — de um dia qualquer.

As tres tem o mesmo esqueleto, 'Ordinarium/Minor.txt', e so mudam nos
salmos, no capitulo e no responsorio. A Prima tem esqueleto proprio e vem
depois.

Reaproveita tudo o que ja esta feito: o Ordo, o resolvedor, as funcoes
'&', a salmodia, o alleluia do tempo e a composicao da pagina. So a
escolha das pecas e nova.

uso:
    python compor_menores.py --hora Sexta --data 08-04-2026
    python compor_menores.py --hora Tertia --data 12-25-2026 --edicao latina
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
from salmodia import salmodia_menor, antifona_repetida
from ordo import Ordo
import alleluia
import compor

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ
REPO = compor.REPO
VERSAO = compor.VERSAO

HORAS = ('Tertia', 'Sexta', 'Nona')
ESPECIAL = 'Psalterium/Special/Minor Special.txt'

# O nome de cada hora, para o cabecalho corrido.
HORA_EM_LATIM = {'Tertia': 'ad Tertiam', 'Sexta': 'ad Sextam',
                 'Nona': 'ad Nonam', 'Prima': 'ad Primam',
                 'Matutinum': 'ad Matutinum', 'Laudes': 'ad Laudes',
                 'Vespera': 'ad Vesperas', 'Completorium': 'ad Completorium'}
HORA_EM_PORTUGUES = {'Tertia': 'Terça', 'Sexta': 'Sexta', 'Nona': 'Noa',
                     'Prima': 'Prima', 'Matutinum': 'Matinas',
                     'Laudes': 'Laudes', 'Vespera': 'Vésperas',
                     'Completorium': 'Completas'}

# O versiculo de cada hora menor, quando vem do Comum: nos ficheiros do
# Comum ele nao tem o nome da hora, tem o do nocturno correspondente.
# E a tabela de equivalencias do original, que ja esta em proprio.py.
VERSICULO_DA_HORA = {'Tertia': 'Versum Tertia', 'Sexta': 'Versum Sexta',
                     'Nona': 'Versum Nona'}


def montar(hora, data, com_vernaculo=True):
    if hora not in HORAS:
        raise SystemExit(f'hora desconhecida: {hora}. Uma de {HORAS}')

    ordo = compor.ordo_do_ano(data)
    registo = ordo.dia(data, hora)
    if registo is None:
        raise SystemExit(f'o Ordo nao tem {data} — gerar com '
                         f'"python gerador/ordo.py --ano {data[-4:]}"')

    dow = int(registo.dayofweek or 0) if registo.dayofweek else \
        compor.DIAS.index(compor.dia_da_semana(data))
    ctx = compor.contexto_do_dia(hora, dow, registo, data)
    r = Resolvedor(REPO, ctx)

    dia = Dia(r, registo.vencedor, VERSAO, registo=registo)
    dia_ver = (Dia(r, registo.vencedor, VERSAO, lang='Portugues',
                   registo=registo) if com_vernaculo else None)
    f = Funcoes(r, compor.estado_do_dia(hora, dow, registo, dia))

    pascal = alleluia.e_tempo_pascal(registo.tempo)
    # Da Septuagesima ao sabado santo apaga-se todo o alleluia que o
    # texto traga escrito — mesmo o que vem do Comum.
    suprime = alleluia.suprime_se(registo.tempo, hora, dow,
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

    # O proprio pode trazer a hora inteira escrita.
    especial = dia.secoes.get(f'Special {hora}') or ''
    if especial.strip():
        esqueleto = compor.esqueleto_especial(especial)
    else:
        esqueleto = ler_arquivo(REPO / 'web/www/horas/Ordinarium/Minor.txt',
                                ctx).get('__preambulo', [])

    pecas = []
    bloco_aberto = ['']
    a_calar = [False]
    # O '#Prelude' do original: a rubrica que o oficio do dia poe antes
    # de tudo o resto.
    abertura = compor.prelude(dia, hora)
    if abertura:
        pecas.append(compor.Peca(
            'rubrica', 'Prelude', texto('Latin', abertura),
            texto('Portugues', compor.prelude(dia_ver, hora))
            if com_vernaculo and dia_ver is not None else ''))


    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            a_calar[0] = compor.omitir_bloco(dia.rule, nome, hora)
            if a_calar[0]:
                # A regra 'Capitulum Versum 2' nao cala o capitulo: poe um
                # versiculo no lugar dele. E o que acontece na oitava da
                # Pascoa, em que nao ha capitulo em hora nenhuma.
                if ('Capitulum' in nome
                        and compor.versiculo_no_lugar(dia.rule, hora)):
                    p = _versiculo_em_lugar_do_capitulo(
                        r, texto, dia, dia_ver, com_vernaculo)
                    if p:
                        pecas.append(p)
                continue

            if nome == 'Hymnus':
                p = _hino(r, texto, hora, registo, com_vernaculo)
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
                pecas.extend(_capitulo(r, texto, al, hora, registo, dia,
                                       dia_ver, nome, com_vernaculo, pascal))
            elif nome == 'Oratio':
                p = _oracao(r, texto, dia, dia_ver, com_vernaculo, registo,
                           hora=hora)
                if p:
                    pecas.append(p)
            elif nome in compor.SO_TITULO:
                bloco_aberto[0] = nome
            elif nome not in ('Capitulum Versus', 'Preces Feriales',
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
                tl = r.titulo(bloco_aberto[0], 'Latin')
                tv = (r.titulo(bloco_aberto[0], 'Portugues')
                      if com_vernaculo else '')
                bloco_aberto[0] = ''
            pecas.append(compor.Peca(gen, '', lat, ver, tl, tv))

    return pecas, r, registo


# --------------------------------------------------------------------------

def _hino(r, texto, hora, registo, com_vernaculo):
    """O hino da hora, do Saltério.

    Na oitava de Pentecostes a Terca tem hino proprio — e a unica
    excepcao, e esta escrita assim no original.
    """
    nome = f'Hymnus {hora}'
    if hora == 'Tertia' and re.search(r'Pasc7', registo.tempo or ''):
        nome = 'Hymnus Pasc7 Tertia'
    bl = r.setupstring('Latin', ESPECIAL).get(nome, '')
    bv = (r.setupstring('Portugues', ESPECIAL).get(nome, '')
          if com_vernaculo else '')
    lat = texto('Latin', bl)
    if not lat.strip():
        return None
    return compor.Peca('hino', nome, lat,
                       texto('Portugues', bv) if com_vernaculo else '',
                       r.titulo('Hymnus', 'Latin'),
                       r.titulo('Hymnus', 'Portugues') if com_vernaculo else '')


def _capitulo(r, texto, al, hora, registo, dia, dia_ver, nome_do_bloco,
              com_vernaculo, pascal):
    """O capitulo, o responsorio breve e o versiculo.

    Porta de capitulum_minor e minor_reponsory. A ordem e sempre a mesma:
    primeiro o proprio do dia, depois o Comum, e so em ultimo o Saltério.
    O capitulo da Terca vai buscar-se ao de Laudes, que e o mesmo.
    """
    variante = registo.variante('Capitulum minor')

    def do_salterio(seccao, lang):
        return (r.setupstring(lang, ESPECIAL).get(seccao) or '').strip()

    def escolher(nome_proprio, nome_salterio, d, lang):
        """Primeiro o proprio (e o Comum, que a remissao alcanca), depois
        o Saltério."""
        if d is not None:
            t, _ = d.proprium(nome_proprio, flag=True)
            if t and t.strip():
                return t.strip()
        return do_salterio(nome_salterio, lang)

    fora = []

    # --- o capitulo
    nome_cap = 'Capitulum Laudes' if hora == 'Tertia' else f'Capitulum {hora}'
    cap_lat = escolher(nome_cap, f'{variante} {hora}', dia, 'Latin')
    cap_ver = (escolher(nome_cap, f'{variante} {hora}', dia_ver, 'Portugues')
               if com_vernaculo else '')
    if cap_lat:
        fora.append(compor.Peca(
            'texto', 'Capitulum', texto('Latin', _formatar_capitulo(cap_lat)),
            texto('Portugues', _formatar_capitulo(cap_ver))
            if com_vernaculo else '',
            r.titulo(nome_do_bloco, 'Latin'),
            r.titulo(nome_do_bloco, 'Portugues') if com_vernaculo else ''))

    # --- o responsorio breve
    resp_lat = _responsorio(r, al, hora, variante, dia, 'Latin', pascal)
    resp_ver = (_responsorio(r, al, hora, variante, dia_ver, 'Portugues',
                             pascal) if com_vernaculo else '')
    if resp_lat:
        fora.append(compor.Peca('texto', 'Responsorium',
                                texto('Latin', resp_lat),
                                texto('Portugues', resp_ver)
                                if com_vernaculo else ''))
    return fora


def _formatar_capitulo(capit):
    """Porta de _format_capitulum: a segunda linha abre com 'v.' e o
    capitulo fecha com o 'Deo gratias'."""
    if not capit:
        return capit
    linhas = capit.split('\n')
    if len(linhas) > 1:
        linhas[1] = 'v. ' + re.sub(r'^[vV]\.\s*', '', linhas[1])
    if not linhas[-1].startswith('$Deo gratias'):
        linhas.append('$Deo gratias')
    return '\n'.join(linhas)


def _responsorio(r, al, hora, variante, dia, lang, pascal):
    """Porta de minor_reponsory."""
    secoes = r.setupstring(lang, ESPECIAL)
    resp = (secoes.get(f'Responsory {variante} {hora}') or '').strip()
    if not resp:
        breve = (secoes.get(f'Responsory breve {variante} {hora}') or '').strip()
        vers = (secoes.get(f'Versum {variante} {hora}') or '').strip()
        if breve and vers:
            resp = f'{breve}\n_\n{vers}'

    if dia is not None:
        proprio, _ = dia.proprium(f'Responsory {hora}', flag=True)
        if not (proprio and proprio.strip()):
            breve, _ = dia.proprium(f'Responsory Breve {hora}', flag=True)
            proprio = f'{breve.rstrip()}\n_\n' if breve else ''
            vers, _ = dia.proprium(VERSICULO_DA_HORA[hora], flag=True)
            proprio += vers or ''
        if proprio and proprio.strip():
            resp = proprio.strip()

    return al.responsorio_breve(resp, lang, pascal,
                                dia.rule if dia else '', hora)


def _versiculo_em_lugar_do_capitulo(r, texto, dia, dia_ver, com_vernaculo):
    """O 'Versus in loco Capituli'."""
    def buscar(d):
        if d is None:
            return ''
        t = d.secoes.get('Versum 2') or d.secoes_comum.get('Versum 2') or ''
        return t.strip()

    bl = buscar(dia)
    if not bl:
        return None
    bv = buscar(dia_ver) if com_vernaculo else ''
    return compor.Peca('texto', 'Versus in loco', texto('Latin', bl),
                       texto('Portugues', bv) if com_vernaculo else '',
                       r.traduzir('Versus in loco', 'Latin'),
                       r.traduzir('Versus in loco', 'Portugues')
                       if com_vernaculo else '')


def _oracao_do_domingo(r, dia, lang, tempo):
    """A oracao do domingo da semana corrente.

    Numa feria comum nao ha oracao propria: reza-se a do domingo que a
    precede. E a regra 'Oratio Dominica', e e o caso mais comum do ano —
    a maior parte dos dias sao ferias.

    Os ficheiros do Tempo chamam-se pela posicao: 'Pent12-0' e o domingo
    XII depois de Pentecostes. Basta trocar o dia por '-0'.
    """
    if not tempo:
        return ''
    nome = f'{tempo}-0'
    # Nos dias do Natal e da oitava da Epifania, o domingo que serve e
    # sempre o mesmo — o original tem esta excepcao escrita.
    if re.search(r'(?:Epi1|Nat)', nome, re.I):
        nome = 'Epi1-0a'
    try:
        secoes = r.setupstring(lang, f'Tempora/{nome}.txt')
    except FileNotFoundError:
        return ''
    return (secoes.get('Oratio') or secoes.get('Oratio 2') or '').strip()


def _secoes_do_domingo(r, lang, tempo):
    """As seccoes do ficheiro do domingo da semana corrente."""
    if not tempo:
        return {}
    nome = f'{tempo}-0'
    if re.search(r'(?:Epi1|Nat)', nome, re.I):
        nome = 'Epi1-0a'
    try:
        return r.setupstring(lang, f'Tempora/{nome}.txt')
    except (FileNotFoundError, OSError):
        return {}


def _oracao(r, texto, dia, dia_ver, com_vernaculo, registo=None, hora='',
            vespera=0):
    """A oracao do dia. Porta da escolha que 'oratio' faz.

    A ordem em que se procura E a regra, e o numero da hora manda nela:
    as Vesperas pedem '[Oratio 3]', as Laudes e as horas menores
    '[Oratio 2]'. Sem isso, as ferias da Quaresma diziam a Vesperas a
    oracao das Laudes — sao mais de trinta dias do ano.
    """
    ind = vespera if hora == 'Vespera' else 2
    if ind not in (1, 2, 3):
        ind = 2
    dayofweek = int(registo.dayofweek or 0) if registo is not None else 0
    rank = registo.rank if registo is not None else 0
    tempo = (registo.tempo if registo is not None else '') or ''

    # A regra 'Oratio Dominica' MANDA rezar a do domingo, mesmo que o
    # proprio tenha uma sua — e o caso dos dias dentro da oitava da
    # Epifania.
    manda_domingo = bool(re.search(r'Oratio Dominica', dia.rule, re.I))
    if (registo is not None
            and re.search(r'Epi1', tempo, re.I)
            and re.search(r'Infra octavam Epiphaniæ Domini', dia.rule, re.I)):
        manda_domingo = True

    def escolher(d, lang):
        if d is None:
            return ''
        w = _secoes_do_domingo(r, lang, tempo) if manda_domingo else d.secoes

        # As ferias da primeira semana depois de Pentecostes tem oracao
        # so delas, marcada '[OratioW]'.
        if dayofweek > 0 and 'OratioW' in d.secoes and rank < 5:
            saida = w.get('OratioW') or ''
        else:
            saida = w.get('Oratio') or ''

        # As Matinas podem ter oracao propria; as outras horas pedem a
        # oracao do seu numero, e essa MANDA sobre a geral.
        if hora == 'Matutinum' and (d.secoes.get('Oratio Matutinum') or ''
                                    ).strip():
            saida = (w.get('Oratio Matutinum')
                     or d.secoes.get('Oratio Matutinum') or '')
        elif not saida.strip() or f'Oratio {ind}' in d.secoes:
            saida = w.get(f'Oratio {ind}') or ''

        if not saida.strip():
            c = d.secoes_comum
            saida = (c.get(f'Oratio {ind}') or c.get(f'Oratio {4 - ind}')
                     or c.get('Oratio') or '')

        if not saida.strip():
            # Sem oracao para esta hora, serve a da outra hora maior.
            i = 3 if ind == 2 else 2
            saida = w.get(f'Oratio {i}') or ''
            if not saida.strip():
                saida = w.get(f'Oratio {4 - i}') or ''

        if not saida.strip() and d.comum:
            saida = (d.secoes_comum.get('Oratio')
                     or d.secoes_comum.get(f'Oratio {ind}') or '')

        # Numa feria do Tempo sem oracao propria reza-se a do domingo.
        if not saida.strip() and re.search(r'Tempora', d.proprio, re.I):
            s = _secoes_do_domingo(r, lang, tempo)
            saida = s.get('Oratio') or s.get('Oratio 2') or ''
        return saida

    bl = escolher(dia, 'Latin')
    bv = escolher(dia_ver, 'Portugues') if com_vernaculo else ''
    if not (bl and bl.strip()):
        return None

    # 'Sub unica conclusione': quando duas oracoes se dizem sob uma so
    # conclusao, a primeira perde a sua. Nas rubricas de 1960 a linha do
    # '$Per' ou do '$Qui' sai fora.
    if (hora in ('Laudes', 'Vespera')
            and re.search(r'Sub unica conc', dia.secoes.get('Rule') or '',
                          re.I)):
        bl = re.sub(r'\$(Per|Qui) .*?\n', '', bl, count=1)
        if bv:
            bv = re.sub(r'\$(Per|Qui) .*?\n', '', bv, count=1)

    bl = _cortar_comemoracao(r, bl, hora, 'Latin')
    if bv:
        bv = _cortar_comemoracao(r, bv, hora, 'Portugues')

    # O 'N.' dos ficheiros do Comum troca-se pelo nome do santo, venha a
    # oracao de onde vier. Sem isto saía 'intercedénte beáto N.' impresso.
    bl = dia.substituir_nome(bl)
    if bv and dia_ver is not None:
        bv = dia_ver.substituir_nome(bv)
    # No Triduo Sacro a oracao diz-se sem o 'Orémus' — e a regra
    # 'Limit ... Oratio'.
    sem_oremus = bool(re.search(r'Limit.*?Oratio', dia.rule, re.I))
    if '$Oremus' not in bl and not sem_oremus:
        bl = '$Oremus\n' + bl
        if bv:
            bv = '$Oremus\n' + bv
    return compor.Peca('oracao', 'Oratio', texto('Latin', bl),
                       texto('Portugues', bv) if com_vernaculo else '',
                       r.titulo('Oratio', 'Latin'),
                       r.titulo('Oratio', 'Portugues') if com_vernaculo else '')


def _cortar_comemoracao(r, w, hora, lang):
    """A comemoracao escrita a seguir a oracao so se diz nas horas
    maiores.

    Varios ficheiros trazem, depois da oracao do dia e separada por uma
    linha de '_', uma seccao '!Commemoratio ...'. Nas horas menores e a
    Matinas ela cala-se; nas Laudes diz-se, mas so ate a palavra que
    remete para o dia anterior ou seguinte.
    """
    marca = rf"!({re.escape(r.traduzir('Commemoratio', lang))}|Commemoratio)"
    if not re.search(r'laudes|vespera', hora, re.I):
        m = re.search(rf'(?s)(.*?){marca}', w)
        if m:
            return re.sub(r'\s*_\s*', '', m.group(1), count=1)
        return w
    if hora == 'Laudes' and re.search(marca, w, re.I):
        m = re.search(r'(?s)(.*?)(precedenti|sequenti)', w)
        if m:
            return re.sub(r'\s*_\s*', '', m.group(1), count=1)
    return w


# --------------------------------------------------------------------------

def folha(pecas, hora, registo, bilingue, corpo=7):
    import html as _h
    o = []
    A = o.append
    nome_lat = registo.nome or ''
    A('<!doctype html><html lang="la"><head><meta charset="utf-8">')
    A(f'<title>{HORA_EM_LATIM[hora]} — {_h.escape(nome_lat)}</title>')
    A('<style>' + (compor.CSS % {'corpo': corpo}) + '</style></head><body>')

    cab = f'{_h.escape(nome_lat)} {HORA_EM_LATIM[hora]}'
    if bilingue:
        cab += f' &nbsp;·&nbsp; {HORA_EM_PORTUGUES[hora]}'
    A(f'<div class="cabecalho">{cab}</div>')
    A('<div class="corpo %s">' % ('bilingue' if bilingue else 'latina'))
    A(f'<h2 class="titulo">{HORA_EM_LATIM[hora].capitalize()}</h2>')

    for p in pecas:
        cap = p.genero in compor.COM_CAPITULAR
        lat = compor.para_html(p.latim, cap, 'Latin')
        if not lat.strip():
            continue
        tl = (f'<p class="bloco">{_h.escape(p.titulo_lat)}</p>'
              if p.titulo_lat else '')
        tv = (f'<p class="bloco">{_h.escape(p.titulo_ver)}</p>'
              if p.titulo_ver else '')
        if bilingue:
            ver = compor.para_html(p.vernaculo, cap, 'Portugues')
            A('<div class="duplo">'
              f'<div class="lat">{tl}{lat}</div>'
              f'<div class="ver">{tv}{ver}</div></div>')
        else:
            A(f'<div class="par">{tl}{lat}</div>')

    A('</div><div class="assinatura">A</div></body></html>')
    return '\n'.join(o)


def main():
    hora = 'Sexta'
    data = None
    bilingue = True
    if '--hora' in sys.argv:
        hora = sys.argv[sys.argv.index('--hora') + 1]
    if '--data' in sys.argv:
        data = sys.argv[sys.argv.index('--data') + 1]
    if '--edicao' in sys.argv:
        bilingue = sys.argv[sys.argv.index('--edicao') + 1] != 'latina'
    if not data:
        raise SystemExit('indique --data MM-DD-AAAA')

    pecas, r, registo = montar(hora, data, com_vernaculo=bilingue)
    nome = (f"{hora.lower()}-{data}-"
            f"{'bilingue' if bilingue else 'latina'}.html")
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(
        folha(pecas, hora, registo, bilingue))

    print(f'escrito {nome}')
    print(f'  {registo.nome} [{registo.vencedor}]'
          + (f'  Comum: {registo.comum}' if registo.comum else ''))
    print(f'  {len(pecas)} peças')


if __name__ == '__main__':
    main()
