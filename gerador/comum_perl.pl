#!/usr/bin/perl
# Despeja o resultado de extract_common ORIGINAL, caso a caso, para servir
# de gabarito ao port em Python.
#
# uso: perl comum_perl.pl <repo> < lista-de-casos
#
# Cada linha da entrada: <campo> <TAB> <rank> <TAB> <tempo_pascal>
# A saida, por caso:     <numero> <TAB> <tipo> <TAB> <ficheiro>

use utf8;
use POSIX;
use File::Basename;
use Time::Local;

package main;

use FindBin qw($Bin);

BEGIN {
  die "uso: comum_perl.pl <repo> < lista\n" unless @ARGV >= 1;
  $Bin = "$ARGV[0]/web/cgi-bin/horas";
}

our $repo = $ARGV[0];
our $version = 'Rubrics 1960 - 1960';
our $datafolder = "$repo/web/www/horas";
our $missa = 0;
our $error = '';
our $debug = '';
our $langfb = 'Latin';
our @dayname = ('', '', '');

require "$repo/web/cgi-bin/DivinumOfficium/SetupString.pl";
require "$Bin/horascommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/dialogcommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/setup.pl";

binmode(STDIN, ':encoding(utf-8)');
binmode(STDOUT, ':encoding(utf-8)');

my $n = 0;
while (my $linha = <STDIN>) {
  $linha =~ s/[\r\n]+$//;
  next unless length $linha;
  $n++;
  my ($campo, $rank, $pascal) = split(/\t/, $linha, 3);
  my ($tipo, $ficheiro) = extract_common($campo, $rank, $version, $pascal);
  $tipo = '' unless defined $tipo;
  $ficheiro = '' unless defined $ficheiro;
  print "$n\t$tipo\t$ficheiro\n";
}
