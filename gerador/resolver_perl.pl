#!/usr/bin/perl
# Despeja, para cada ficheiro pedido, TODAS as seccoes ja com as remissoes
# '@' resolvidas — usando o setupstring original do Divinum Officium.
#
# Serve de gabarito para conferir o resolvedor portado em Python.
#
# uso: perl resolver_perl.pl <repo> <idioma> [versao] < lista-de-ficheiros
#
# A lista vem pela entrada padrao, um caminho por linha, relativo a
# web/www/horas/<idioma>. A saida traz, por ficheiro:
#
#   <<<<FICHEIRO <caminho>
#   <<<<SECCAO <nome>
#   ...linhas...
#   <<<<SECCAO <nome>
#   ...
#   >>>>FIM

use strict;
use warnings;
use utf8;
use open ':std', ':encoding(UTF-8)';

BEGIN {
  die "uso: resolver_perl.pl <repo> <idioma> [versao] < lista\n" unless @ARGV >= 2;
  unshift @INC, "$ARGV[0]/web/cgi-bin";
}

my ($repo, $idioma, $versao) = @ARGV;
$versao ||= 'Rubrics 1960 - 1960';

# Estado global de que setupstring e vero() dependem.
our $version      = $versao;
our $hora         = '';
our $missa        = 0;
our $missanumber  = 0;
our $commune      = '';
our $votive       = '';
our $dioecesis    = '';
our $commemoratio = '';
our $rule         = '';
our $winner       = '';
our %winner       = (Rule => '');
our $monthday     = '';
our $chantTone    = '';
our @dayname      = ('', '', '');
our ($day, $month, $year, $dayofweek) = (1, 1, 2026, 4);
our $datafolder   = "$repo/web/www/horas";
our $error        = '';

# A lingua de reserva. O padrao do projeto e o ingles, e e isso que faz
# aparecer ingles no meio do oficio portugues. Aqui fixamos em Latin, que
# e o comportamento que o nosso livro exige: onde falta portugues, sai
# latim, nunca ingles.
our $langfb = 'Latin';

require "$repo/web/cgi-bin/DivinumOfficium/SetupString.pl";

while (my $alvo = <STDIN>) {
  $alvo =~ s/\s+$//;
  next unless length $alvo;

  print "<<<<FICHEIRO $alvo\n";

  my $s = eval { main::setupstring($idioma, $alvo) };
  if ($@) {
    print "<<<<ERRO $@\n";
  } elsif (!$s || !ref $s) {
    print "<<<<ERRO setupstring devolveu vazio\n";
  } else {
    foreach my $sec (sort keys %$s) {
      print "<<<<SECCAO $sec\n";
      my $t = $s->{$sec};
      $t = '' unless defined $t;
      $t =~ s/\n+$//;
      print "$t\n" if length $t;
    }
  }
  print ">>>>FIM\n";
}
