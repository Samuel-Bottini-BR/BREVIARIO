"""
O ciclo das remissoes numeradas.

O QUE FAZ, E PORQUE ASSIM
-------------------------
Uma remissao precisa do numero de folio do alvo, e esse numero so existe
depois de o alvo estar composto. Faz-se por isso em duas passagens:

    1. compoe-se o Comum e le-se, do PDF, em que folio caiu cada posicao
    2. compoem-se as outras partes com esses numeros ja escritos

O ALVO E O COMUM, e nao o corpo do livro, por uma razao que poupa metade
do trabalho: **o Comum tem numeracao propria**. O folio de uma posicao do
Comum e o mesmo esteja o Comum sozinho ou cosido no volume — comeca em
*1 e nao depende de nada. O Proprio do Tempo e o dos Santos e que
partilham a sequencia corrida, e esses so sabem o seu numero na costura.

Por isso o ciclo estabiliza depressa: as remissoes escrevem-se no Tempo e
nos Santos, e apontam para o Comum, que nao se mexe. Uma passagem de
leitura chega — e confirma-se com uma segunda.

    python gerador/remissoes.py
"""

import argparse
import io
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import livro
import pdf as _pdf
import perpetuo

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

RAIZ = perpetuo.RAIZ
# ATENCAO a caixa das letras: a marca vai dentro de um titulo em
# VERSALETE, e o texto extraido do PDF vem com a caixa trocada — pos-se
# '§Ac-C1§' e le-se '§aC-C1§'. Por isso o padrao ignora a caixa e a chave
# guarda-se toda em minusculas, dos dois lados.
MARCA = re.compile(r'§\s*A\s*([A-Za-z0-9\-]+?)\s*§', re.I)


def folios_do_comum(caminho_pdf):
    """Em que folio caiu cada posicao do Comum.

    O Comum comeca em *1, e por isso o indice da pagina dentro do seu
    proprio PDF E o folio impresso. Nao ha que ler o numero da pagina:
    contar chega.
    """
    from pypdf import PdfReader
    leitor = PdfReader(str(caminho_pdf))
    fora = {}
    for n, pagina in enumerate(leitor.pages, start=1):
        for achado in MARCA.finditer(pagina.extract_text() or ''):
            # O valor e o FOLIO IMPRESSO, nao o numero da pagina: as
            # partes de numeracao propria levam asterisco e o corpo do
            # livro nao, e quem emite a remissao nao tem de o saber.
            fora.setdefault(achado.group(1).lower(), f'*{n}')
    return fora, len(leitor.pages)


def folios_do_corpo(caminho_pdf):
    """Em que folio caiu cada posicao do Tempo e dos Santos.

    Aqui NAO se pode contar paginas: o corpo do livro nao comeca no um do
    volume — vem depois do Salterio — e o folio impresso e o unico que
    serve. Le-se da propria pagina.
    """
    import verificar
    from pypdf import PdfReader
    leitor = PdfReader(str(caminho_pdf))
    fora = {}
    for pagina in leitor.pages:
        texto = pagina.extract_text() or ''
        marcas = [m.group(1).lower() for m in MARCA.finditer(texto)]
        if not marcas:
            continue
        folio = verificar.folio_impresso(texto)
        if not folio:
            continue
        for chave in marcas:
            if chave[:2] in ('t-', 's-'):
                fora.setdefault(chave, folio)
    return fora


def contar_remissoes(caminho_pdf):
    from pypdf import PdfReader
    leitor = PdfReader(str(caminho_pdf))
    com, sem = 0, 0
    for pagina in leitor.pages:
        texto = pagina.extract_text() or ''
        # (?i) obrigatorio: o versalete devolve 'cOmmuni' do PDF.
        com += len(re.findall(r'(?i)(?:Communi|Psalterio)\s*\[\s*\*\s*\d+\s*\]', texto))
        sem += len(re.findall(r'(?i)(?:Communi|Psalterio)(?!\s*\[)', texto))
    return com, sem


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida', default='BREVIARIUM-latina-volume-unico')
    p.add_argument('--max-passagens', type=int, default=3)
    a = p.parse_args()
    t0 = time.time()

    folios, passagens = {}, 0
    anterior = None
    while passagens < a.max_passagens:
        passagens += 1
        print(f'\n===== passagem {passagens} =====', flush=True)
        # Os dois alvos possiveis, e sao alvo pela mesma razao: ambos
        # tem NUMERACAO PROPRIA, e por isso o folio de uma posicao e o
        # mesmo esteja a parte sozinha ou cosida no volume. Compoe-se
        # cada uma a parte, contam-se as paginas, e ja se sabe o numero.
        perpetuo.construir(a.saida, folios=folios,
                           so=('commune', 'psalterium'))
        novos = {}
        for parte, rotulo in (('commune', 'Comum'),
                              ('psalterium', 'Saltério')):
            m, n = folios_do_comum(RAIZ / f'{a.saida}-{parte}.pdf')
            novos.update(m)
            print(f'   {rotulo}: {n} páginas, {len(m)} âncoras', flush=True)
        if novos == anterior:
            print('   o mapa de âncoras estabilizou', flush=True)
            folios = novos
            break
        anterior, folios = novos, novos

    print(f'\nâncoras estáveis ao fim de {passagens} passagens', flush=True)

    # SEGUNDO CICLO — o corpo do livro. O Tempo e os Santos partilham a
    # sequencia corrida: o folio de uma posicao so se sabe com o volume
    # cosido, e escrever os numeros muda o comprimento do texto e pode
    # deslocar a paginacao. Por isso repete-se ate o mapa nao mexer.
    caminho = total = indice = None
    for volta in range(1, a.max_passagens + 1):
        print(f'\n===== volume, volta {volta} =====', flush=True)
        caminho, total, indice = perpetuo.construir(a.saida, folios=folios)
        do_corpo = folios_do_corpo(caminho)
        juntos = dict(folios)
        juntos.update(do_corpo)
        print(f'   corpo do livro: {len(do_corpo)} âncoras', flush=True)
        if juntos == folios:
            print('   o mapa do corpo estabilizou', flush=True)
            break
        folios = juntos
    else:
        print('   AVISO: o mapa do corpo não estabilizou', flush=True)

    com, sem = contar_remissoes(caminho)
    print(f'\nescrito {caminho.name}: {total} páginas, '
          f'{time.time() - t0:.0f}s')
    print(f'remissões ao Comum: {com} com número, {sem} sem')
    return passagens


if __name__ == '__main__':
    main()
