"""
Monta a pagina de conferencia da matriz.

Gera CONFERIR-matriz.html — uma pagina que abre com dois cliques, sem
depender de nada instalado.

Para cada norma citada, poe em sequencia:
  1. o texto oficial, tal como esta no documento
  2. a traducao portuguesa (minha, so para conferencia)
  3. o que eu tirei dessa norma, linha por linha da matriz

Se a 3 nao se seguir da 1, o erro e meu. E o que se procura.
"""

import html
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import matriz_normas as M

RAIZ = Path(__file__).resolve().parent.parent

# Traducao das normas citadas. E minha, feita do ingles, e serve APENAS
# para conferir a matriz. Nao entra no livro: a traducao do Codigo de
# Rubricas para o livro tem de ser feita do latim.
TRADUCAO = {
160: 'O modo de dizer cada Hora está exposto no Ordinário do Ofício Divino.',

166: '''A ordem do Ofício dominical é esta:
a) Nas I Vésperas: tudo como no Ordinário e no Saltério, do sábado precedente, salvo o que for dado como próprio.
b) Completas que seguem as I Vésperas: do sábado.
c) Nas Matinas: invitatório e hino como no Ordinário ou no Saltério; antífonas, salmos e versículo do único nocturno como no Saltério do domingo; absolvição «Exaudi», bênçãos «Ille nos», «Divinum auxilium», «Per evangelica dicta»; primeira e segunda lições, com os seus responsórios, da Escritura ocorrente (n. 220 a); terceira lição da homilia sobre o evangelho do dia (n. 220 b); hino Te Deum, que se omite nos domingos do Advento e do domingo da Septuagésima ao II domingo da Paixão, dizendo-se então um terceiro responsório.
d) Em Laudes: antífonas, se não houver próprias, do Saltério; salmos do Saltério do domingo, do 1.º ou do 2.º esquema conforme os tempos (n. 197); capítulo, hino e versículo como no Ordinário ou no Saltério ou no Próprio do Tempo; o resto como no Próprio do Tempo.
e) Em Prima: antífona, se não houver própria, e salmos do Saltério do domingo; capítulo e o restante como no Ordinário; lição breve do Tempo.
f) Em Terça, Sexta e Noa: tudo como no Ordinário e no Saltério, salvo o que for dado como próprio.
g) Nas II Vésperas: tudo como no Ordinário e no Saltério, salvo o que for dado como próprio.
h) Completas: do domingo.''',

167: '''O Ofício festivo pertence às festas de I classe. A sua ordem é esta:
a) Nas I Vésperas: tudo do Próprio ou do Comum.
b) Completas que seguem as I Vésperas: de domingo.
c) Nas Matinas: tudo do Próprio ou do Comum; e diz-se o hino Te Deum.
d) Em Laudes: tudo do Próprio ou do Comum, com os salmos de domingo, do primeiro esquema.
e) Em Prima: a primeira antífona de Laudes; salmos 53, 118.1 e 118.2; capítulo e o restante como no Ordinário; lição breve do Tempo.
f) Em Terça, Sexta e Noa: a segunda, a terceira e a quinta antífonas de Laudes, respectivamente; salmos de domingo; o resto do Próprio ou do Comum.
g) Nas II Vésperas: tudo do Próprio ou do Comum.
h) Completas: de domingo.''',

168: '''O Ofício semifestivo pertence às festas de II classe. A sua ordem é esta:
a) Nas Matinas, em Laudes e nas Vésperas: tudo como no Ofício festivo.
b) Em Prima: antífona e salmos do Saltério, do dia da semana corrente; capítulo e o restante como no Ordinário; lição breve do Tempo.
c) Em Terça, Sexta e Noa: antífona e salmos do Saltério do dia da semana corrente; o resto da festa, como no Próprio ou no Comum.
d) Completas: de domingo.''',

169: '''O Ofício ordinário pertence às festas de III classe e ao Ofício de Nossa Senhora ao sábado. A sua ordem é esta:
a) Nas Matinas: invitatório e hino do Próprio ou do Comum; antífonas, salmos e versículo do único nocturno do Saltério do dia da semana corrente, salvo se forem dados como próprios ou do Comum (n. 177); primeira e segunda lições com os seus responsórios da Escritura, como se indica no n. 221 a; terceira lição da festa (n. 221 b); e diz-se o hino Te Deum.
b) Em Laudes e nas Vésperas: antífonas e salmos como no Saltério do dia da semana corrente, salvo se forem dados como próprios ou do Comum (n. 177); o resto como no Próprio ou no Comum.
c) Em Prima: antífona e salmos do Saltério do dia da semana corrente; capítulo e o restante como no Ordinário; lição breve do Tempo.
d) Em Terça, Sexta e Noa: antífonas e salmos como no Saltério do dia da semana corrente; o resto da festa, como no Próprio ou no Comum.
e) Completas: do dia da semana corrente.''',

171: '''A ordem do Ofício ferial é esta:
a) Nas Matinas: invitatório e hino do Saltério ou do Ordinário, conforme as ocasiões; antífonas, salmos e versículo do único nocturno do Saltério, do dia da semana corrente; nas férias, três lições da Escritura ocorrente ou da homilia sobre o evangelho do dia, com os seus responsórios; nas vigílias, três lições próprias da homilia com os responsórios da féria corrente. O hino Te Deum diz-se somente nas férias do tempo do Natal e do tempo pascal; nos outros tempos diz-se um terceiro responsório.
b) Em Laudes e nas Vésperas: tudo como no Saltério, do dia da semana corrente, e no Ordinário, conforme os tempos, salvo o que for dado como próprio. Nas férias toma-se a oração própria, se a féria a tiver; senão, a oração do domingo precedente, a não ser que outra seja designada; nas vigílias diz-se a oração própria.
c) Em Prima: antífona, se não houver própria, e salmos do Saltério, do dia da semana corrente; capítulo e o restante como no Ordinário; lição breve do Tempo.
d) Em Terça, Sexta e Noa: antífona, se não houver própria, e salmos do Saltério, do dia da semana corrente; capítulo e o restante como no Ordinário, conforme os tempos; oração como em Laudes.
e) Completas: do dia da semana corrente.''',

177: '''Nas festas de III classe, universais ou particulares, que em certas Horas tenham antífonas próprias e salmos do Comum, ou antífonas próprias e salmos especialmente designados, observam-se as rubricas especiais dadas nos lugares respectivos do Breviário.''',

181: '''O curso diário do Ofício Divino conclui-se, depois das Completas, com a antífona de Nossa Senhora com o seu versículo e oração, e com o versículo «Divinum auxilium», excepto nos Ofícios do Tríduo Sacro e de defuntos.''',

197: '''O Saltério tem dois esquemas de salmos para as Matinas de quarta-feira e para Laudes de todos os dias. Usa-se o segundo esquema:
a) nos domingos dos tempos da Septuagésima, da Quaresma e da Paixão;
b) em todas as férias dos tempos do Advento, da Septuagésima, da Quaresma e da Paixão, no Ofício ferial das Têmporas de setembro, e nas vigílias de II e III classe fora do tempo pascal.
Nos demais dias usa-se o primeiro esquema.''',

220: '''No Ofício dominical, a ordem das três lições é esta:
a) Dizem-se a primeira e a segunda lições da Escritura ocorrente, como no Próprio. A primeira lição da Sagrada Escritura é a que hoje vem em primeiro lugar no Breviário. A segunda forma-se juntando numa só as actuais segunda e terceira lições, omitindo-se o responsório intermédio.
b) A terceira lição é a leitura da homilia sobre o evangelho do dia. A lição tomada é a que hoje vem no Breviário como primeira do terceiro nocturno.''',

221: '''No Ofício ordinário, a ordem das três lições é esta:
a) A primeira e a segunda lições dizem-se da Escritura; e esta é, ordinariamente, a Escritura ocorrente, salvo se houver lições próprias ou especialmente designadas. A primeira lição da Sagrada Escritura é a que hoje vem em primeiro lugar no Breviário. A segunda forma-se juntando numa só as actuais segunda e terceira lições, omitindo-se o responsório intermédio.
b) A terceira lição é da festa, isto é, a lição própria a que no passado se chamava comummente lição «contracta». Se não houver lição contracta, juntam-se numa só as lições próprias que antes eram do segundo nocturno. Mas se a festa não tiver lições próprias, toma-se como terceira lição a quarta lição do Comum.''',

237: '''O hino Te Deum diz-se nas Matinas, depois da última lição, em lugar do nono ou do terceiro responsório:
a) no domingo da Oitava da Páscoa, no domingo de Pentecostes, e nas Matinas do domingo de Páscoa, rezadas por quem não participou da Vigília Pascal;
b) nos domingos de II classe, excepto a Septuagésima, a Sexagésima e a Quinquagésima;
c) em todas as festas;
d) por todas as oitavas do Natal, da Páscoa e de Pentecostes;
e) no Ofício ferial do tempo do Natal e do tempo pascal;
f) nas vigílias da Ascensão e de Pentecostes;
g) no Ofício de Nossa Senhora ao sábado.''',

238: '''O hino Te Deum omite-se:
a) nos Ofícios do Tempo, do I domingo do Advento à vigília do Natal inclusive, e do domingo da Septuagésima ao Sábado Santo inclusive;
b) nas vigílias de II e III classe, excepto a vigília da Ascensão do Senhor;
c) em todas as férias do tempo chamado «durante o ano»;
d) no Ofício de defuntos.''',

239: 'Quando o hino Te Deum se omite, diz-se em seu lugar um nono ou terceiro responsório.',

241: '''O capítulo que se diz em Prima é sempre «Regi sæculorum», e em Completas «Tu autem in nobis». Nas outras Horas toma-se do Ordinário ou do Saltério, do Próprio ou do Comum, conforme os diferentes tipos de Ofício (n. 165-177).''',

242: 'A lição breve que se diz em Prima é sempre do Tempo, como no Ordinário.',
}

TITULO_HORA = {
    'Matinas': 'Matinas', 'Laudes': 'Laudes', 'Prima': 'Prima',
    'Terca, Sexta e Noa': 'Terça, Sexta e Noa',
    'Vesperas': 'Vésperas', 'Completas': 'Completas',
}


def carregar_normas():
    t = (RAIZ / 'normas-1960.txt').read_text(encoding='utf-8')
    blocos = {}
    for m in re.finditer(r'=== NORMA (\d+) ===\n(.*?)(?=\n\n=== NORMA |\Z)', t, re.S):
        blocos[int(m.group(1))] = ' '.join(m.group(2).split())
    return blocos


def em_alineas(texto):
    """Quebra 'a) ... b) ...' em paragrafos."""
    t = re.sub(r'\s([a-h])\)\s', r'\n\1) ', texto)
    return [p.strip() for p in t.split('\n') if p.strip()]


def celula(v):
    if isinstance(v, M.Conforme):
        if not v.excecoes:
            return f'<em>{html.escape(v.padrao)}</em>'
        partes = [html.escape(v.padrao)]
        for c, x in v.excecoes:
            partes.append(f'<span class="exc">salvo {html.escape(c)}: '
                          f'<b>{html.escape(str(x))}</b></span>')
        return '<br>'.join(partes)
    return html.escape(str(v))


CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1.6; margin: 0; padding: 2rem 1rem 6rem;
  max-width: 60rem; margin-inline: auto;
  background: #fbfaf7; color: #201c17;
}
@media (prefers-color-scheme: dark) {
  body { background: #16150f; color: #e8e3d8; }
}
h1 { font-size: 1.9rem; line-height: 1.2; margin: 0 0 .4rem; }
h2 { font-size: 1.35rem; margin: 3rem 0 .2rem;
     border-top: 2px solid currentColor; padding-top: 1.2rem; }
.sub { opacity: .75; margin: 0 0 2rem; }
.passos { background: #f0ece2; border-radius: .5rem; padding: 1rem 1.4rem;
          margin: 1.5rem 0; }
@media (prefers-color-scheme: dark) { .passos { background: #24221a; } }
.passos ol { margin: .4rem 0 0; padding-left: 1.2rem; }
.passos li { margin: .5rem 0; }
h3 { font-size: .8rem; letter-spacing: .1em; text-transform: uppercase;
     opacity: .7; margin: 1.6rem 0 .4rem; font-weight: 700; }
blockquote {
  margin: 0; padding: .8rem 1.1rem; border-left: 4px solid #b0a68c;
  background: #f4f1e8; border-radius: 0 .4rem .4rem 0;
}
blockquote.trad { border-left-color: #8a6a3b; background: #f7f2e4; }
@media (prefers-color-scheme: dark) {
  blockquote { background: #21201a; border-left-color: #6b6350; }
  blockquote.trad { background: #262218; border-left-color: #a8834a; }
}
blockquote p { margin: .35rem 0; }
.oficial { font-style: italic; opacity: .85; font-size: .95rem; }
.tabela-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .88rem;
        font-family: system-ui, sans-serif; margin-top: .4rem; }
th, td { border: 1px solid #cfc7b3; padding: .4rem .55rem;
         text-align: left; vertical-align: top; }
th { background: #ece7da; font-weight: 700; }
@media (prefers-color-scheme: dark) {
  th, td { border-color: #423d31; } th { background: #2a2820; }
}
.exc { display: inline-block; font-size: .85em; opacity: .9;
       padding-top: .15rem; }
nav { font-family: system-ui, sans-serif; font-size: .9rem;
      margin: 1.5rem 0 0; }
nav a { display: inline-block; padding: .3rem .6rem; margin: .15rem .15rem 0 0;
        border: 1px solid #c3b99f; border-radius: .3rem;
        text-decoration: none; color: inherit; }
@media (prefers-color-scheme: dark) { nav a { border-color: #4a4536; } }
.aviso { font-size: .9rem; opacity: .8; margin-top: .3rem; }
"""


def main():
    blocos = carregar_normas()

    uso = {}
    for hora, tab in M.HORAS:
        for r in tab:
            for n in set(re.findall(r'\b(1[5-9]\d|2[0-4]\d)\b', r['normas'])):
                uso.setdefault(int(n), []).append((hora, r))

    o = []
    A = o.append
    A('<!doctype html><html lang="pt"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width, initial-scale=1">')
    A('<title>Conferir a matriz — normas de 1960</title>')
    A(f'<style>{CSS}</style></head><body>')

    A('<h1>Onde conferir a matriz</h1>')
    A('<p class="sub">Normas gerais do Breviário Romano, 1960 — '
      'as que dizem de onde vem cada peça do Ofício.</p>')

    A('<div class="passos"><b>Como conferir</b><ol>'
      '<li><b>O texto oficial</b> — copiado do documento, não é paráfrase minha.</li>'
      '<li><b>A tradução</b> — minha, feita do inglês, só para esta conferência. '
      'Não serve para o livro: a tradução do Código de Rubricas para o livro '
      'tem de ser feita do latim.</li>'
      '<li><b>O que eu tirei dali</b> — as linhas da matriz que citam a norma.</li>'
      '</ol><p class="aviso">Leia as três de cima para baixo. Se a terceira não '
      'se seguir da primeira, o erro é meu. É isso que se procura.</p></div>')

    A('<nav>' + ''.join(f'<a href="#n{n}">Norma {n}</a>' for n in sorted(uso))
      + '</nav>')

    for n in sorted(uso):
        A(f'<h2 id="n{n}">Norma {n}</h2>')

        A('<h3>Texto oficial</h3><blockquote class="oficial">')
        for p in em_alineas(blocos[n]):
            A(f'<p>{html.escape(p)}</p>')
        A('</blockquote>')

        A('<h3>Tradução</h3><blockquote class="trad">')
        for linha in TRADUCAO.get(n, '(falta traduzir)').split('\n'):
            A(f'<p>{html.escape(linha)}</p>')
        A('</blockquote>')

        A('<h3>O que eu tirei daqui</h3><div class="tabela-wrap"><table>')
        A('<tr><th>Hora</th><th>Peça</th><th>I</th><th>II</th><th>III</th>'
          '<th>DOM</th><th>FER</th></tr>')
        for hora, r in uso[n]:
            cs = ''.join(f'<td>{celula(r[c])}</td>' for c in M.CLASSES)
            A(f'<tr><td>{html.escape(TITULO_HORA.get(hora, hora))}</td>'
              f'<td>{html.escape(r["peca"])}</td>{cs}</tr>')
        A('</table></div>')

    A('</body></html>')

    caminho = RAIZ / 'CONFERIR-matriz.html'
    io.open(caminho, 'w', encoding='utf-8').write('\n'.join(o))
    print('escrito:', caminho)
    print(len(uso), 'normas,', sum(len(v) for v in uso.values()),
          'linhas de matriz cobertas')


if __name__ == '__main__':
    main()
