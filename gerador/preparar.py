"""
Prepara o repositorio do Divinum Officium: clona se preciso, atualiza, e
reaplica a correcao do Date.pm.

E idempotente: rodar de novo nao estraga nada. E e para ser rodado depois
de todo 'git pull', porque o pull sobrescreve a correcao.

uso: python preparar.py [--atualizar]
"""

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / 'divinum-officium'
URL = 'https://github.com/DivinumOfficium/divinum-officium.git'
DATE_PM = REPO / 'web/cgi-bin/DivinumOfficium/Date.pm'

# As duas funcoes estao na lista de exportacao do Date.pm mas nunca foram
# definidas. Sem elas, qualquer geracao em lote morre com
#   Undefined subroutine &DivinumOfficium::Date::date_to_days
# O bug nao afeta a navegacao do site, so a geracao em lote — por isso
# passou despercebido.
CORRECAO = '''#*** date_to_days($day, $mon, $year)
# Converts a calendar date to a day number. $mon is 0-based, as in gmtime.
# Exported in @EXPORT_OK but never defined; restored here.
sub date_to_days {
  my ($day, $mon, $year) = @_;
  return int(timegm(0, 0, 12, $day, $mon, $year) / 86400);
}

#*** days_to_date($days)
# Inverse of date_to_days: returns the gmtime list for a day number.
# Exported in @EXPORT_OK but never defined; restored here.
sub days_to_date {
  my $days = shift;
  return gmtime($days * 86400 + 43200);
}

'''
ANCORA = '#*** getweek($flag)'

# O gabarito tem de imprimir com a mesma convencao que nos, senao a
# comparacao acusa como divergencia o que e so uma opcao diferente.
#
# Copiamos o site em tudo (decisao 2.18), e o site traz 'noflexa=1'. O
# gerador em lote do repositorio traz '0', e por isso e alinhado aqui a
# cada arranque — inclusive depois de um 'git pull'.
SETUP_LOTE = REPO / 'standalone/tools/epubgen2/Ehoras.setup'
OPCOES_DO_GABARITO = {'noflexa': '1'}


def run(*args, **kw):
    return subprocess.run(args, check=True, **kw)


def clonar():
    if REPO.exists():
        print(f'repositorio ja existe em {REPO}')
        return False
    print(f'clonando {URL}')
    run('git', 'clone', '--depth', '1', URL, str(REPO))
    return True


def atualizar():
    print('git pull')
    run('git', '-C', str(REPO), 'pull', '--ff-only')


def aplicar_correcao():
    texto = DATE_PM.read_text(encoding='utf-8')

    if 'sub date_to_days' in texto and 'sub days_to_date' in texto:
        print('correcao do Date.pm: ja aplicada')
        return False

    if ANCORA not in texto:
        raise SystemExit(
            'nao achei a ancora no Date.pm. O arquivo mudou; conferir a mao.')

    DATE_PM.write_text(texto.replace(ANCORA, CORRECAO + ANCORA, 1),
                       encoding='utf-8')
    print('correcao do Date.pm: aplicada')
    return True


def alinhar_setup_do_lote():
    """Poe o gerador em lote a imprimir com a nossa convencao."""
    if not SETUP_LOTE.exists():
        print('setup do gerador em lote: nao existe, nada a fazer')
        return False

    texto = SETUP_LOTE.read_text(encoding='utf-8')
    mudou = False
    for nome, valor in OPCOES_DO_GABARITO.items():
        novo, n = re.subn(rf"^\${nome}='[^']*';;",
                          f"${nome}='{valor}';;", texto, flags=re.M)
        if n and novo != texto:
            texto, mudou = novo, True
    if mudou:
        SETUP_LOTE.write_text(texto, encoding='utf-8')
        print('setup do gerador em lote: alinhado com o do site')
    else:
        print('setup do gerador em lote: ja alinhado')
    return mudou


def conferir():
    """Prova que a correcao funciona, em vez de supor."""
    script = (
        'use lib "%s/web/cgi-bin";'
        'require DivinumOfficium::Date;'
        'my $d = DivinumOfficium::Date::date_to_days(15, 7, 2026);'
        'my @b = DivinumOfficium::Date::days_to_date($d);'
        'die "ida e volta falhou" unless $b[3]==15 && $b[4]==7 && $b[5]+1900==2026;'
        'print "ok\\n";'
    ) % str(REPO).replace('\\', '/')
    r = subprocess.run(['perl', '-e', script], capture_output=True, text=True)
    if r.returncode != 0 or 'ok' not in r.stdout:
        raise SystemExit(f'a correcao nao funcionou:\n{r.stderr}')
    print('correcao conferida: date_to_days e days_to_date fazem ida e volta')


def main():
    novo = clonar()
    if '--atualizar' in sys.argv and not novo:
        atualizar()
    aplicar_correcao()
    alinhar_setup_do_lote()
    conferir()
    print('\npronto.')


if __name__ == '__main__':
    main()
