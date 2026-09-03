"""
Passa as paginas de HTML a PDF.

Usa o Chrome sem janela. E uma solucao de espera, e esta registada como
tal na decisao 3.8: o WeasyPrint, que e a ferramenta escolhida, exige no
Windows a biblioteca GTK, que nao esta instalada. O CSS e o mesmo nos
dois — quando o WeasyPrint estiver, troca-se o motor e nada mais.

O Chrome respeita a regra '@page' do CSS, e por isso o formato de 100 x
160 mm e as margens saem certos. Manda-se '--no-margins' para ele nao
acrescentar margem propria por cima da nossa.

uso:
    python imprimir.py                     # todas as paginas da pasta
    python imprimir.py sexta-04-08-2026-latina.html
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Onde procurar. O Edge nao esta onde se espera: mora numa pasta com o
# numero da versao — 'Microsoft\EdgeCore\148.0.3967.54\msedge.exe' — e
# por isso procura-se por padrao em vez de se escrever o caminho.
LUGARES = (
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files (x86)\Microsoft\EdgeCore\*\msedge.exe',
    r'C:\Program Files\Microsoft\EdgeCore\*\msedge.exe',
)


def navegadores():
    """Todos os navegadores instalados que sabem imprimir em PDF."""
    import glob
    fora = []
    for lugar in LUGARES:
        for achado in sorted(glob.glob(lugar), reverse=True):
            caminho = Path(achado)
            if caminho.exists() and caminho not in fora:
                fora.append(caminho)
    return fora


CHROME = navegadores()


def navegador():
    if CHROME:
        return CHROME[0]
    raise RuntimeError('nao encontrei o Chrome nem o Edge para imprimir')


def imprimir(html, pdf=None):
    html = Path(html)
    pdf = Path(pdf) if pdf else html.with_suffix('.pdf')
    r = subprocess.run(
        [str(navegador()), '--headless', '--disable-gpu', '--no-pdf-header-footer',
         '--no-margins', f'--print-to-pdf={pdf}', html.resolve().as_uri()],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=180,
    )
    if not pdf.exists():
        raise RuntimeError(f'o navegador nao escreveu {pdf.name}:\n'
                           f'{r.stderr[:800]}')
    return pdf


def main():
    alvos = [Path(a) for a in sys.argv[1:] if a.endswith('.html')]
    if not alvos:
        # So as paginas do oficio. Os relatorios e as folhas de
        # conferencia sao para ler no navegador, nao para imprimir.
        alvos = sorted(p for p in RAIZ.glob('*.html')
                       if not p.name.startswith(('CONFERIR', 'RELATORIO')))
    for html in alvos:
        pdf = imprimir(RAIZ / html.name if not html.is_absolute() else html)
        print(f'{pdf.name}  {pdf.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
