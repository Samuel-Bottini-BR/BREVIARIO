"""
Compoe a hora de Sexta de um dia, como pagina de livro.

Reaproveita tudo o que ja esta feito: o motor de condicionais, o
resolvedor de remissoes, as formulas '$' e as funcoes '&'. So a montagem
e nova, porque as horas menores tem um esqueleto diferente das Completas.

O QUE E NOSSO E O QUE NAO E
---------------------------
O calendario ainda nao esta feito. Ou seja: o programa nao sabe sozinho
que dia 4 de agosto de 2026 e S. Domingos, nem que o oficio dele segue o
Comum C5. Isso e dado a mao, aqui em baixo, e esta assinalado.

Tudo o resto — seguir as remissoes, escolher os salmos do dia da semana,
juntar as pecas, compor a pagina — e do nosso programa.

uso: python compor_sexta.py
"""

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto, ler_arquivo
from resolver import Resolvedor
from funcoes import Funcoes, EstadoDoDia
from proprio import Dia
from salmodia import salmodia_menor, antifona_repetida
import compor

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'
VERSAO = 'Rubrics 1960 - 1960'


# --------------------------------------------------------------------------
# O DIA, dado a mao enquanto o calendario nao existe
# --------------------------------------------------------------------------

DIA = {
    'data': '04-08-2026',
    'data_us': '08-04-2026',          # como o Divinum Officium a escreve
    'dia_da_semana': 'Feria III',     # 4 de agosto de 2026 e terca-feira
    'nome_latino': 'S. Dominici Confessoris',
    'nome_portugues': 'S. Domingos, Confessor',
    'classe': 'III. classis',
    'proprio': 'Sancti/08-04.txt',
    # O Comum ja NAO se escreve aqui: le-se da linha [Rank] do proprio,
    # pelo mesmo caminho do original — ver comum.py.
}


# --------------------------------------------------------------------------

def montar(com_vernaculo=True):
    idx = compor.DIAS.index(DIA['dia_da_semana'])
    ctx = Contexto(version=VERSAO, hora='Sexta',
                   tempore='post Pentecosten', dayofweek=idx)
    r = Resolvedor(REPO, ctx)
    dia = Dia(r, DIA['proprio'], VERSAO)
    f = Funcoes(r, EstadoDoDia(hora='Sexta', dayofweek=idx,
                               winner=DIA['proprio'],
                               commune=dia.comum or '',
                               secoes_vencedor=dia.secoes))

    def texto(lang, bruto, antifona=None):
        return f.expandir(r.expandir_formulas(bruto, lang), lang, antifona)

    dia_ver = (Dia(r, DIA['proprio'], VERSAO, lang='Portugues')
               if com_vernaculo else None)

    def peca(genero, rel, seccao, bloco=''):
        bl = r.setupstring('Latin', rel).get(seccao, '')
        bv = (r.setupstring('Portugues', rel).get(seccao, '')
              if com_vernaculo else '')
        return _peca(genero, seccao, bl, bv, bloco)

    def peca_do_dia(genero, seccao, bloco='', flag=True):
        """A peca pela via do original: primeiro o proprio, depois o
        Comum — e com a tabela de equivalencias, que e o que faz o
        versiculo da Sexta ser encontrado em '[Nocturn 3 Versum]'."""
        bl, _ = dia.proprium(seccao, flag)
        bv = ''
        if com_vernaculo:
            bv, _ = dia_ver.proprium(seccao, flag)
        return _peca(genero, seccao, bl or '', bv or '', bloco)

    def _peca(genero, seccao, bl, bv, bloco):
        lat = texto('Latin', bl)
        ver = texto('Portugues', bv) if com_vernaculo else ''
        if not lat.strip():
            return None
        tl = r.titulo(bloco, 'Latin') if bloco else ''
        tv = (r.titulo(bloco, 'Portugues')
              if bloco and com_vernaculo else '')
        return compor.Peca(genero, seccao, lat, ver, tl, tv)

    ESPECIAL = 'Psalterium/Special/Minor Special.txt'

    pecas = []
    bloco_aberto = ['']    # o titulo do bloco que ainda nao foi impresso
    esqueleto = ler_arquivo(REPO / 'web/www/horas/Ordinarium/Minor.txt',
                            ctx).get('__preambulo', [])

    for linha in esqueleto:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()

            if nome in ('Incipit', 'Conclusio'):
                bloco_aberto[0] = nome
            elif nome == 'Hymnus':
                p = peca('hino', ESPECIAL, 'Hymnus Sexta', 'Hymnus')
                if p:
                    pecas.append(p)

            elif nome == 'Psalmi':
                bloco = _salmos(r, f, dia, idx, com_vernaculo)
                if bloco:
                    bloco[0].titulo_lat = r.titulo('Psalmi', 'Latin')
                    if com_vernaculo:
                        bloco[0].titulo_ver = r.titulo('Psalmi', 'Portugues')
                pecas.extend(bloco)

            elif nome == 'Capitulum Responsorium Versus':
                # Numa festa de III classe estas tres pecas vem do Comum.
                # Nao se leem do ficheiro a mao: vao pela mesma via do
                # original, que sabe que o versiculo da Sexta se chama
                # 'Nocturn 3 Versum' nos ficheiros do Comum.
                primeiro = True
                em_falta = []
                for sec in ('Capitulum Sexta', 'Responsory Breve Sexta',
                            'Versum Sexta'):
                    p = peca_do_dia('texto', sec, nome if primeiro else '')
                    if p:
                        pecas.append(p)
                        primeiro = False
                    else:
                        em_falta.append(sec)
                if em_falta:
                    # Nunca pular peca em silencio — decisao 3.5.
                    print(f'  VAZIO: {", ".join(em_falta)}', file=sys.stderr)

            elif nome == 'Oratio':
                # A oracao abre com 'Orémus', que os ficheiros nao trazem:
                # o original acrescenta-o quando a peca nao o tem.
                p = peca_do_dia('oracao', 'Oratio', 'Oratio')
                if p:
                    if '$Oremus' not in (p.latim or ''):
                        p.latim = texto('Latin', '$Oremus') + '\n' + p.latim
                        if com_vernaculo:
                            p.vernaculo = (texto('Portugues', '$Oremus')
                                           + '\n' + p.vernaculo)
                    pecas.append(p)
            continue

        if l.startswith(('$', '&')):
            lat = texto('Latin', l)
            ver = texto('Portugues', l) if com_vernaculo else ''
            if lat.strip():
                tl = tv = ''
                if bloco_aberto[0]:
                    tl = r.titulo(bloco_aberto[0], 'Latin')
                    tv = (r.titulo(bloco_aberto[0], 'Portugues')
                          if com_vernaculo else '')
                    bloco_aberto[0] = ''
                pecas.append(compor.Peca('texto', '', lat, ver, tl, tv))

    return pecas, r


def _salmos(r, f, dia, dayofweek, com_vernaculo):
    """Os salmos da hora, pela salmodia do Saltério e pela funcao '&psalm'.

    Ate aqui os salmos eram lidos a mao do ficheiro, e por isso saiam sem
    titulo, sem o Gloria e sem o sinal '‡' que marca o fim da antifona.
    Agora passam pela mesma funcao do original, ja conferida contra ele.
    """
    return _bloco_de_salmos(r, f, dia, 'Sexta', dayofweek, com_vernaculo)


def _bloco_de_salmos(r, f, dia, hora, dayofweek, com_vernaculo):
    ant_lat, chamadas = salmodia_menor(r, hora, dayofweek, 'Latin', dia)
    ant_ver = ''
    if com_vernaculo:
        ant_ver, _ = salmodia_menor(r, hora, dayofweek, 'Portugues', dia)

    fora = [compor.Peca('antifona', 'Ant.',
                        f'Ant. {ant_lat}' if ant_lat else '',
                        f'Ant. {ant_ver}' if ant_ver else '')]

    for k, chamada in enumerate(chamadas):
        args = f.argumentos(chamada)
        # O contador de salmos anda por hora e por COLUNA: as duas linguas
        # da mesma pagina tem de dar o mesmo numero ao mesmo salmo.
        f.e.psalmnum = k
        lat = f.expandir(f.psalm(*(args + ['Latin', ant_lat])), 'Latin')
        ver = ''
        if com_vernaculo:
            f.e.psalmnum = k
            ver = f.expandir(f.psalm(*(args + ['Portugues', ant_ver])),
                             'Portugues')
        rotulo = args[0] if args else ''
        fora.append(compor.Peca('salmo', f'Salmo {rotulo}', lat, ver))

    fora.append(compor.Peca(
        'antifona', 'Ant.',
        f'Ant. {antifona_repetida(ant_lat)}' if ant_lat else '',
        f'Ant. {antifona_repetida(ant_ver)}' if ant_ver else ''))
    return fora


# --------------------------------------------------------------------------

def folha(pecas, bilingue, corpo=7):
    o = []
    A = o.append
    A('<!doctype html><html lang="la"><head><meta charset="utf-8">')
    A(f"<title>Ad Sextam — {DIA['data']}</title>")
    A('<style>' + (compor.CSS % {'corpo': corpo}) + '</style></head><body>')

    cab = (f"{DIA['nome_latino']} ad Sextam"
           + (f" &nbsp;·&nbsp; {DIA['nome_portugues']}, Sexta" if bilingue else ''))
    A(f'<div class="cabecalho">{cab}</div>')
    A('<div class="corpo %s">' % ('bilingue' if bilingue else 'latina'))
    A('<h2 class="titulo">Ad Sextam</h2>')

    import html as _h
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
    bilingue = '--edicao' not in sys.argv or \
        sys.argv[sys.argv.index('--edicao') + 1] != 'latina'
    pecas, r = montar(com_vernaculo=bilingue)
    nome = f"sexta-{DIA['data']}-{'bilingue' if bilingue else 'latina'}.html"
    io.open(RAIZ / nome, 'w', encoding='utf-8').write(folha(pecas, bilingue))
    print(f'escrito {nome}')
    print(f"  {DIA['nome_latino']} ~ {DIA['classe']}, {DIA['dia_da_semana']}")
    print(f'  {len(pecas)} peças')
    if r.nao_resolvidas:
        print(f'  {len(r.nao_resolvidas)} remissões por resolver')


if __name__ == '__main__':
    main()
