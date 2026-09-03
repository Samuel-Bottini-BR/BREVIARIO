"""
Gera uma hora de um dia a partir dos arquivos-fonte do Divinum Officium.

Prova de conceito das Completas nas rubricas de 1960. Nao usa o Perl nem
o site: le os arquivos-fonte, avalia as condicoes de rubrica pelo motor
portado em dofile.py, e monta a hora.

Tres regras que valem para todo o projeto e estao implementadas aqui:

  1. NUNCA cair para o ingles. A cadeia de reserva do Divinum Officium e
     portugues -> ingles -> latim. A nossa e portugues -> latim, e a
     lacuna fica registrada.
  2. Nenhuma linha de controle sai impressa.
  3. As condicoes de rubrica sao avaliadas, nao ignoradas.

uso: python gerar_hora.py <repo> [--dia Dominica]
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dofile import Contexto, ler_arquivo, e_linha_de_controle

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VERSAO = 'Rubrics 1960 - 1960'
LATIM = 'Latin'
VERNACULO = 'Portugues'


# --------------------------------------------------------------------------
# Acesso aos arquivos, com registro de lacunas
# --------------------------------------------------------------------------

class Corpus:
    def __init__(self, repo, ctx):
        self.base = Path(repo) / 'web/www/horas'
        self.ctx = ctx
        self._cache = {}
        self.lacunas = []       # (arquivo, secao) que faltam no vernaculo
        self.desalinhados = []  # arquivos cujas colunas nao casam por posicao

    def arquivo(self, lang, rel):
        # Trava dura contra o erro numero 4 da secao 14 do prompt. Nao e
        # promessa: e o gerador recusando-se a abrir o arquivo.
        if lang is not None and lang not in (LATIM, VERNACULO):
            raise RuntimeError(
                f'tentou ler o idioma {lang!r}; so o latim e o portugues '
                f'podem entrar no livro')

        chave = (lang, rel)
        if chave not in self._cache:
            caminho = self.base / (rel if lang is None else f'{lang}/{rel}')
            self._cache[chave] = (ler_arquivo(caminho, self.ctx)
                                  if caminho.exists() else {})
        return self._cache[chave]

    def secao(self, rel, nome, lang):
        """Devolve as linhas de uma secao no idioma pedido, ou None."""
        return self.arquivo(lang, rel).get(nome)

    def par(self, rel, nome):
        """Devolve (latim, vernaculo, houve_lacuna).

        Se o vernaculo nao tiver a secao, devolve o latim nos dois lados e
        marca a lacuna. Nunca consulta o ingles.
        """
        lat = self.secao(rel, nome, LATIM)
        ver = self.secao(rel, nome, VERNACULO)
        if lat is None:
            return None, None, False
        if ver is None:
            self.lacunas.append((rel, nome))
            return lat, None, True
        return lat, ver, False


# --------------------------------------------------------------------------
# Resolucao de $Nome e $rubrica Nome
# --------------------------------------------------------------------------

ARQ_ORACOES = 'Psalterium/Common/Prayers.txt'
ARQ_RUBRICAS = 'Psalterium/Common/Rubricae.txt'


def resolver_cifrao(corpus, nome):
    """$Nome -> (latim, vernaculo, lacuna). Sem passar pelo ingles."""
    if nome.startswith('rubrica '):
        return corpus.par(ARQ_RUBRICAS, nome[len('rubrica '):])
    return corpus.par(ARQ_ORACOES, nome)


# --------------------------------------------------------------------------
# As pecas das Completas
# --------------------------------------------------------------------------

ARQ_ESPECIAL = 'Psalterium/Special/Minor Special.txt'
ARQ_SALMOS_MENORES = 'Psalterium/Psalmi/Psalmi minor.txt'
ARQ_MARIA = 'Psalterium/Mariaant.txt'

# O que preenche cada bloco '#' das Completas. Fora daqui o bloco e so
# um titulo, sem conteudo proprio.
BLOCOS = {
    'Lectio brevis': (ARQ_ESPECIAL, 'Lectio Completorium'),
    'Hymnus': (ARQ_ESPECIAL, 'Hymnus Completorium'),
    'Capitulum Responsorium Versus': (ARQ_ESPECIAL, 'Completorium'),
    # Os arquivos de salmo nao tem cabecalho de secao: o texto todo fica
    # no preambulo.
    'Canticum: Nunc dimittis': ('Psalterium/Psalmorum/Psalm233.txt', '__preambulo'),
}

DIAS = ['Dominica', 'Feria II', 'Feria III', 'Feria IV',
        'Feria V', 'Feria VI', 'Sabbato']


def salmos_do_dia(corpus, dia):
    """Devolve (antifona_lat, antifona_ver, [numeros de salmo])."""
    lat, ver, _ = corpus.par(ARQ_SALMOS_MENORES, 'Completorium')
    if not lat:
        return None, None, []

    def extrair(linhas):
        if not linhas:
            return None, None
        for i, l in enumerate(linhas):
            m = re.match(rf'^{re.escape(dia)}\s*=\s*(.*)$', l)
            if m:
                seguinte = linhas[i + 1] if i + 1 < len(linhas) else ''
                return m.group(1).strip(), seguinte.strip()
        return None, None

    ant_lat, lista = extrair(lat)
    ant_ver, _ = extrair(ver) if ver else (None, None)
    numeros = [n.strip() for n in lista.split(',')] if lista else []
    return ant_lat, ant_ver, numeros


def texto_do_salmo(corpus, ref):
    """ref pode ser '90' ou '7(2-10)'. Devolve (latim, vernaculo, lacuna)."""
    m = re.match(r'^(\d+)(?:\((\d+)-(\d+)\))?$', ref)
    if not m:
        return None, None, False
    num = m.group(1)
    rel = f'Psalterium/Psalmorum/Psalm{num}.txt'
    lat, ver, lacuna = corpus.par(rel, '__preambulo')

    if m.group(2):  # recorte de versiculos, como em '33(2-11)'
        ini, fim = int(m.group(2)), int(m.group(3))

        # O recorte e decidido pela numeracao LATINA, e as mesmas posicoes
        # sao tomadas no portugues.
        #
        # E preciso ser assim porque os dois arquivos numeram diferente: o
        # latim segue a Vulgata e comeca no versiculo 2, o portugues comeca
        # no 1. O texto corresponde linha a linha, mas o rotulo nao. Cortar
        # pelo numero em cada idioma pegaria trechos distintos, e as duas
        # colunas da pagina diriam coisas diferentes sem ninguem notar.
        posicoes = [
            i for i, l in enumerate(lat or [])
            if (mv := re.match(r'^\s*(\d+):(\d+)', l))
            and ini <= int(mv.group(2)) <= fim
        ]
        lat = [lat[i] for i in posicoes] if lat else lat
        if ver is not None:
            if len(ver) == len(corpus.secao(rel, '__preambulo', LATIM) or []):
                ver = [ver[i] for i in posicoes]
            else:
                # Contagem de linhas diferente: nao da para casar por
                # posicao. Melhor nao imprimir portugues errado.
                corpus.desalinhados.append(rel)
                ver = None
    return lat, ver, lacuna


# --------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------

class Peca:
    def __init__(self, rotulo, latim, vernaculo, origem, lacuna=False):
        self.rotulo = rotulo
        self.latim = [l for l in (latim or []) if not e_linha_de_controle(l)]
        self.vernaculo = ([l for l in vernaculo if not e_linha_de_controle(l)]
                          if vernaculo is not None else None)
        self.origem = origem
        self.lacuna = lacuna


def montar_completas(corpus, dia='Dominica'):
    pecas = []
    esqueleto = corpus.arquivo(None, 'Ordinarium/Completorium.txt')
    linhas = esqueleto.get('__preambulo', [])

    for linha in linhas:
        l = linha.strip()
        if not l:
            continue

        if l.startswith('#'):
            nome = l[1:].strip()
            if nome in BLOCOS:
                rel, secao = BLOCOS[nome]
                lat, ver, lac = corpus.par(rel, secao)
                pecas.append(Peca(nome, lat, ver, f'{rel} [{secao}]', lac))
            elif nome == 'Psalmi':
                ant_lat, ant_ver, numeros = salmos_do_dia(corpus, dia)
                pecas.append(Peca(
                    f'Antifona ({dia})', [f'Ant. {ant_lat}'] if ant_lat else [],
                    [f'Ant. {ant_ver}'] if ant_ver else None,
                    f'{ARQ_SALMOS_MENORES} [Completorium]',
                    ant_ver is None))
                for ref in numeros:
                    lat, ver, lac = texto_do_salmo(corpus, ref)
                    pecas.append(Peca(f'Salmo {ref}', lat, ver,
                                      f'Psalterium/Psalmorum/Psalm{ref}', lac))
                pecas.append(Peca(f'Antifona repetida',
                                  [f'Ant. {ant_lat}'] if ant_lat else [],
                                  [f'Ant. {ant_ver}'] if ant_ver else None,
                                  ARQ_SALMOS_MENORES, ant_ver is None))
            elif nome == 'Antiphona finalis':
                lat, ver, lac = corpus.par(ARQ_MARIA, 'Ant Maria4')
                pecas.append(Peca(nome, lat, ver, f'{ARQ_MARIA} [Ant Maria4]', lac))
            else:
                pecas.append(Peca(f'-- {nome} --', [], [], 'titulo de secao'))

        elif l.startswith('$'):
            nome = l[1:]
            lat, ver, lac = resolver_cifrao(corpus, nome)
            arq = ARQ_RUBRICAS if nome.startswith('rubrica ') else ARQ_ORACOES
            pecas.append(Peca(nome, lat, ver, f'{arq} [{nome}]', lac))

        elif l.startswith('&'):
            pecas.append(Peca(l, None, None, 'funcao de script do Perl'))

    return pecas


# --------------------------------------------------------------------------
# Saida
# --------------------------------------------------------------------------

def imprimir(pecas, dia):
    print('=' * 78)
    print(f'  COMPLETAS — {dia} — Rubricas de 1960')
    print('=' * 78)
    for p in pecas:
        if p.origem == 'titulo de secao':
            print(f'\n{p.rotulo}')
            continue
        if p.origem == 'funcao de script do Perl':
            print(f'\n  [{p.rotulo}]  <- calculado por funcao Perl, ainda nao portada')
            continue
        if not p.latim:
            # Nunca pular em silencio: e assim que uma peca some do livro
            # sem ninguem perceber.
            print(f'\n--- {p.rotulo} ---   ({p.origem})')
            print('    VAZIO: nao encontrei texto para esta peca')
            continue

        print(f'\n--- {p.rotulo} ---   ({p.origem})')
        lat = [l for l in p.latim if l.strip()]
        ver = [l for l in (p.vernaculo or []) if l.strip()]

        if p.vernaculo is None:
            print('    LACUNA: nao ha portugues; imprime-se o latim')
            for l in lat:
                print(f'    LA  {l}')
        else:
            for i in range(max(len(lat), len(ver))):
                if i < len(lat):
                    print(f'    LA  {lat[i]}')
                if i < len(ver):
                    print(f'    PT  {ver[i]}')


PONTEIRO = re.compile(r'(^\s*[@!&$]|;;)')


def auditar(pecas):
    """As verificacoes 1 e 2 do prompt, sobre o que acabou de ser gerado."""
    ponteiros, controle = [], []
    for p in pecas:
        for lado, linhas in (('LA', p.latim), ('PT', p.vernaculo or [])):
            for l in linhas:
                if e_linha_de_controle(l):
                    controle.append((p.rotulo, lado, l))
                elif PONTEIRO.search(l):
                    ponteiros.append((p.rotulo, lado, l.strip()))
    return ponteiros, controle


def main():
    repo = sys.argv[1]
    dia = 'Dominica'
    if '--dia' in sys.argv:
        dia = sys.argv[sys.argv.index('--dia') + 1]

    ctx = Contexto(version=VERSAO, hora='Completorium',
                   tempore='post Pentecosten', dayofweek=DIAS.index(dia))
    corpus = Corpus(repo, ctx)
    pecas = montar_completas(corpus, dia)
    imprimir(pecas, dia)

    print()
    print('=' * 78)
    print('  LACUNAS DE TRADUCAO NESTA HORA')
    print('=' * 78)
    vistas = []
    for rel, secao in corpus.lacunas:
        if (rel, secao) not in vistas:
            vistas.append((rel, secao))
            print(f'  falta portugues: {rel} [{secao}]')
    print(f'  total: {len(vistas)} pecas sem traducao')

    if ctx.nao_avaliadas:
        print()
        print('  CONDICOES QUE NAO SOUBE AVALIAR (nao falhar em silencio):')
        for c in sorted(set(ctx.nao_avaliadas)):
            print(f'    {c}')

    ponteiros, controle = auditar(pecas)
    print()
    print('=' * 78)
    print('  AUDITORIA — verificacoes 1 e 2 do prompt')
    print('=' * 78)
    print(f'  dados de controle escapados : {len(controle)}')
    for rotulo, lado, l in controle:
        print(f'      {lado} em {rotulo}: {l!r}')
    print(f'  ponteiros nao resolvidos    : {len(ponteiros)}')
    for rotulo, lado, l in ponteiros:
        print(f'      {lado} em {rotulo}: {l}')

    idiomas = sorted({lang for lang, _ in corpus._cache if lang})
    arquivos = len(corpus._cache)
    print(f'  idiomas lidos               : {", ".join(idiomas)}')
    print(f'  arquivos abertos            : {arquivos}')
    assert 'English' not in idiomas
    if ponteiros:
        print()
        print('  Esperado nesta etapa: o resolvedor de remissoes ainda nao existe.')
        print('  Nenhum destes pode sobreviver ate o PDF.')


if __name__ == '__main__':
    main()
