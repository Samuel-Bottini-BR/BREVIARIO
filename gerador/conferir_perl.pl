#!/usr/bin/perl
# Roda o motor de condicionais ORIGINAL do Divinum Officium sobre uma
# lista de arquivos e imprime os resultados delimitados. Serve de
# gabarito para conferir o port em Python (dofile.py).
#
# uso: perl conferir_perl.pl <repo> <versao> < lista-de-arquivos-na-entrada
#
# A lista vem pela entrada padrao, um caminho por linha, relativo a
# web/www/horas. A saida traz, para cada arquivo:
#
#   <<<<ARQUIVO <caminho>
#   ...linhas processadas...
#   >>>>FIM

use strict;
use warnings;
use utf8;
use open ':std', ':encoding(UTF-8)';

BEGIN {
  die "uso: conferir_perl.pl <repo> [versao] < lista\n" unless @ARGV >= 1;
  unshift @INC, "$ARGV[0]/web/cgi-bin";
}

my ($repo, $versao) = @ARGV;
$versao ||= 'Rubrics 1960 - 1960';

# Estado global de que vero() depende.
our $version      = $versao;
our $hora         = 'Completorium';
our $missa        = 0;
our $missanumber  = 0;
our $commune      = '';
our $votive       = '';
our $dioecesis    = '';
our $commemoratio = '';
our $rule         = '';
our $winner       = 'Pent16-0';
our %winner       = (Rule => '');
our $monthday     = '';
our $chantTone    = '';
our @dayname      = ('Pent16-0', '', '');
our ($day, $month, $year, $dayofweek) = (10, 9, 1961, 0);
our $datafolder   = "$repo/web/www/horas";

require "$repo/web/cgi-bin/DivinumOfficium/SetupString.pl";

while (my $alvo = <STDIN>) {
  # Nao basta chomp: se a lista vier de um processo Windows, sobra um
  # retorno de carro no fim do nome e todo arquivo "some".
  $alvo =~ s/\s+$//;
  next unless length $alvo;

  my $caminho = "$repo/web/www/horas/$alvo";
  print "<<<<ARQUIVO $alvo\n";

  if (open(my $fh, '<:encoding(UTF-8)', $caminho)) {
    my @linhas = <$fh>;
    close $fh;
    chomp @linhas;
    my @saida = eval { main::process_conditional_lines(@linhas) };
    if ($@) { print "<<<<ERRO $@\n"; }
    else    { print "$_\n" for @saida; }
  } else {
    print "<<<<ERRO nao abriu: $!\n";
  }
  print ">>>>FIM\n";
}
