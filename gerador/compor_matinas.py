"""
Compoe Matinas — a ultima hora, e a maior.

O esqueleto do Ordinario e curto (Incipit, Invitatorio, Hino, Salmos com
licoes, Oracao, Conclusao), mas o bloco do meio vale por toda a hora: um
ou tres nocturnos, nove salmos, tres ou nove licoes, cada uma com a sua
bencao e o seu responsorio, e o Te Deum quando o dia o pede.

O miolo esta em matinas.py; aqui so se monta a pagina.

uso:
    python compor_matinas.py --data 08-04-2026
    python compor_matinas.py --data 12-25-2026 --edicao latina
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
import matinas

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = compor.RAIZ
REPO = compor.REPO
VERSAO = compor.VERSAO
HORA = 'Matutinum'

CHAMADA_DE_LICAO = re.compile(r'^@@LECTIO (\d+)@@$')


def montar(data, com_vernaculo=True):
    ordo = compor.ordo_do_ano(data)
    registo = ordo.dia(data, HORA)
    if registo is None:
        raise SystemExit(f'o Ordo nao tem {data}')

    dow = (int(registo.dayofweek) if registo.dayofweek
           else compor.DIAS.index(compor.dia_da_semana(data)))

    ctx = compor.contexto_do_dia(HORA, dow, registo, data)
    r = Resolvedor(REPO, ctx)
    dia = Dia(r, registo.vencedor, VERSAO, registo=registo)
    dia_ver = (Dia(r, registo.vencedor, VERSAO, lang='Portugues',
                   registo=registo) if com_vernaculo else None)
    f = Funcoes(r, compor.estado_do_dia(HORA, dow, registo, dia))

    pascal = alleluia.e_tempo_pascal(registo.tempo)
    # Da Septuagesima ao sabado santo apaga-se todo o alleluia que o
    # texto traga escrito — mesmo o que vem do Comum.
    suprime = alleluia.suprime_se(registo.tempo, HORA, dow,
                                 int(registo.vespera or 0))

    m_lat = matinas.Matinas(r, registo, dia, 'Latin')
    m_ver = (matinas.Matinas(r, registo, dia_ver, 'Portugues')
             if com_vernaculo else None)

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

    def par(bruto_lat, bruto_ver=None):
        lat = texto('Latin', bruto_lat)
        ver = ''
        if com_vernaculo:
            ver = texto('Portugues',
                        bruto_lat if bruto_ver is None else bruto_ver)
        return lat, ver

    especial = dia.secoes.get(f'Special {HORA}') or ''
    if especial.strip():
        esqueleto = compor.esqueleto_especial(especial)
    else:
        esqueleto = ler_arquivo(
            REPO / f'web/www/horas/Ordinarium/{HORA}.txt',
            ctx).get('__preambulo', [])

    pecas = []
    bloco_aberto = ['']
    a_calar = [False]
    # O '#Prelude' do original: a rubrica que o oficio do dia poe antes
    # de tudo o resto.
    abertura = compor.prelude(dia, HORA)
    if abertura:
        pecas.append(compor.Peca(
            'rubrica', 'Prelude', texto('Latin', abertura),
            texto('Portugues', compor.prelude(dia_ver, HORA))
            if com_vernaculo and dia_ver is not None else ''))


    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            a_calar[0] = compor.omitir_bloco(dia.rule, nome, HORA)
            if a_calar[0]:
                continue

            especial_da_conclusao = (compor.conclusao_especial(dia)
                                     if nome == 'Conclusio' else '')
            if especial_da_conclusao:
                lat, ver = par(especial_da_conclusao,
                               compor.conclusao_especial(dia_ver)
                               if com_vernaculo and dia_ver else None)
                if lat.strip():
                    pecas.append(compor.Peca(
                        'texto', nome, lat, ver,
                        r.titulo(nome, 'Latin'),
                        r.titulo(nome, 'Portugues') if com_vernaculo else ''))
                a_calar[0] = True
                continue

            if nome == 'Invitatorium':
                lat, ver = par(matinas.invitatorium(m_lat),
                               matinas.invitatorium(m_ver)
                               if m_ver else None)
                if lat.strip():
                    pecas.append(compor.Peca(
                        'texto', nome, lat, ver,
                        r.titulo(nome, 'Latin'),
                        r.titulo(nome, 'Portugues') if com_vernaculo else ''))
            elif nome == 'Hymnus':
                lat, ver = par(matinas.hymnus(m_lat),
                               matinas.hymnus(m_ver) if m_ver else None)
                if lat.strip():
                    pecas.append(compor.Peca(
                        'hino', nome, lat, ver,
                        r.titulo('Hymnus', 'Latin'),
                        r.titulo('Hymnus', 'Portugues')
                        if com_vernaculo else ''))
            elif nome.startswith('Psalmi'):
                bloco = _salmos_e_licoes(f, m_lat, m_ver, com_vernaculo,
                                         texto)
                if bloco:
                    bloco[0].titulo_lat = r.titulo(nome, 'Latin')
                    if com_vernaculo:
                        bloco[0].titulo_ver = r.titulo(nome, 'Portugues')
                pecas.extend(bloco)
            elif nome == 'Oratio':
                p = compor_menores._oracao(r, texto, dia, dia_ver,
                                           com_vernaculo, registo,
                                           hora=HORA)
                if p:
                    pecas.append(p)
            elif nome in compor.SO_TITULO:
                bloco_aberto[0] = nome
            elif nome not in ('Commemoratio officii parvi B.M.V.',):
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


def _salmos_e_licoes(f, m_lat, m_ver, com_vernaculo, texto):
    """O bloco central: os nocturnos, e dentro deles as licoes.

    'psalmi_matutinum' devolve uma lista de linhas com as chamadas de
    salmo e, no lugar de cada licao, uma marca '@@LECTIO n@@'. Aqui a
    marca troca-se pelo texto da licao — que so entao se vai buscar,
    porque a licao pode depender do nocturno em que caiu.
    """
    def linhas_de(m):
        saida = []
        matinas.psalmi_matutinum(m, saida)
        return saida

    lat = linhas_de(m_lat)
    ver = linhas_de(m_ver) if com_vernaculo else []

    pecas = []
    acumulado_lat, acumulado_ver = [], []

    def despejar(genero='texto', rotulo=''):
        if not acumulado_lat:
            return
        bruto_lat = '\n'.join(acumulado_lat)
        bruto_ver = '\n'.join(acumulado_ver)
        acumulado_lat.clear()
        acumulado_ver.clear()
        t_lat = texto('Latin', bruto_lat)
        if not t_lat.strip():
            return
        t_ver = texto('Portugues', bruto_ver) if com_vernaculo else ''
        pecas.append(compor.Peca(genero, rotulo, t_lat, t_ver))

    # A antifona corrente. E dela que o salmo tira o sinal '‡', que marca
    # que a antifona cobre o primeiro versiculo inteiro — e o sinal vai
    # para a PECA da antifona, que por isso tem de ficar a mao.
    antifona = [None]

    for i, l in enumerate(lat):
        lv = ver[i] if i < len(ver) else ''
        chamada = CHAMADA_DE_LICAO.match(l.strip())
        if chamada:
            despejar()
            antifona[0] = None
            num = int(chamada.group(1))
            bruto_lat = matinas.lectio(m_lat, num)
            bruto_ver = (matinas.lectio(m_ver, num) if com_vernaculo else '')
            t_lat = texto('Latin', bruto_lat)
            t_ver = texto('Portugues', bruto_ver) if com_vernaculo else ''
            pecas.append(compor.Peca('licao', f'Lectio {num}', t_lat, t_ver))
            continue

        if re.match(r'^Ant\.\s', l.strip()):
            despejar()
            p = compor.Peca('antifona', 'Ant.', texto('Latin', l),
                            texto('Portugues', lv) if com_vernaculo else '')
            pecas.append(p)
            antifona[0] = p
            continue

        if l.strip().startswith('&psalm('):
            despejar()
            args = f.argumentos(l.strip())
            ant_lat = _so_antifona(antifona[0].latim if antifona[0] else '')
            ant_ver = _so_antifona(antifona[0].vernaculo
                                   if antifona[0] else '')
            f.e.psalmnum = 0
            f.e.sinal_na_antifona = False
            t_lat = f.expandir(f.psalm(*(args + ['Latin', ant_lat])), 'Latin')
            if f.e.sinal_na_antifona and antifona[0] and antifona[0].latim:
                antifona[0].latim += ' /:‡:/'
            t_ver = ''
            if com_vernaculo:
                f.e.psalmnum = 0
                f.e.sinal_na_antifona = False
                t_ver = f.expandir(f.psalm(*(args + ['Portugues', ant_ver])),
                                   'Portugues')
                if (f.e.sinal_na_antifona and antifona[0]
                        and antifona[0].vernaculo):
                    antifona[0].vernaculo += ' /:‡:/'
            pecas.append(compor.Peca(
                'salmo', f'Salmo {args[0] if args else ""}', t_lat, t_ver))
            continue

        acumulado_lat.append(l)
        acumulado_ver.append(lv)
    despejar()
    return pecas


def _so_antifona(linha):
    return re.sub(r'^\s*Ant\.\s*', '', (linha or '').split('\n')[0])


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
    nome = f"matinas-{data}-{'bilingue' if bilingue else 'latina'}.html"
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(
        compor_menores.folha(pecas, HORA, registo, bilingue))
    print(f'escrito {nome}')
    print(f'  {registo.nome} [{registo.vencedor}]')
    print(f'  {len(pecas)} peças')


if __name__ == '__main__':
    main()
