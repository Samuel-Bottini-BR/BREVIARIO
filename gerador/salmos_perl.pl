#!/usr/bin/perl
# Despeja o resultado da funcao 'psalm' ORIGINAL do Divinum Officium, caso
# a caso, para servir de gabarito ao port em Python.
#
# uso: perl salmos_perl.pl <repo> < lista-de-casos
#
# Cada linha da entrada e um caso, com os campos separados por tabulacao:
#
#     <idioma> <TAB> <argumentos> [<TAB> <antifona>]
#
# onde <argumentos> e exactamente o que vai dentro dos parenteses de
# '&psalm(...)' nos ficheiros do corpus: '4', '118,1,8', '129,1'.
#
# A saida traz, por caso:
#
#     <<<<CASO <numero de ordem>
#     ...o texto...
#     >>>>FIM

use utf8;
use POSIX;
use File::Basename;
use Time::Local;

package main;

# Varios ficheiros do projeto — dialogcommon.pl, horascommon.pl — procuram
# os seus vizinhos a partir de $Bin, que o FindBin poe na pasta do
# programa que corre. Como este programa nao esta na pasta deles, o $Bin
# tem de ser corrigido ANTES de o primeiro 'require' compilar: dai o BEGIN.
use FindBin qw($Bin);

BEGIN {
  die "uso: salmos_perl.pl <repo> < lista\n" unless @ARGV >= 1;
  $Bin = "$ARGV[0]/web/cgi-bin/horas";
}

our $repo = $ARGV[0];

# O estado global de que a funcao depende. Sao os mesmos nomes que o
# EofficiumXhtml.pl declara antes de mandar montar a hora.
our $version = 'Rubrics 1960 - 1960';
our $hora = 'Completorium';
our $missa = 0;
our $missanumber = 0;
our $commune = '';
our $votive = '';
our $dioecesis = '';
our $commemoratio = '';
our $rule = '';
our $winner = '';
our %winner = (Rank => '');
our %winner2 = ();
our $monthday = '';
our $chantTone = '';
our @dayname = ('', '', '');
our ($day, $month, $year, $dayofweek, $vespera) = (1, 1, 2026, 4, 0);
our $datafolder = "$repo/web/www/horas";
our $error = '';
our $debug = '';
our $Tk = 0;
our $Hk = 0;
our $Ck = 0;
our $only = 0;
our $expand = 'all';
our $column = 1;
our $psalmnum1 = 0;
our $psalmnum2 = 0;
our $priest = 0;
our $lang1 = 'Latin';
our $lang2 = 'Portugues';

# A lingua de reserva. O padrao do projeto e o ingles; aqui e o latim,
# pela mesma razao de sempre: nenhum ingles pode entrar no livro.
our $langfb = 'Latin';

# As opcoes de apresentacao dos versiculos. Vem de fora, do lado Python,
# para que os dois lados do confronto nao possam divergir por descuido: se
# a flexa mudar de ideia num sitio, muda nos dois.
#     perl salmos_perl.pl <repo> <nonumbers> <noinnumbers> <noflexa>
our $psalmvar = 0;
our $nonumbers = defined($ARGV[1]) ? $ARGV[1] : 0;
our $noinnumbers = defined($ARGV[2]) ? $ARGV[2] : 1;
our $noflexa = defined($ARGV[3]) ? $ARGV[3] : 0;

require "$repo/web/cgi-bin/DivinumOfficium/SetupString.pl";
require "$Bin/horascommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/dialogcommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/setup.pl";
require "$Bin/horas.pl";
require "$Bin/horasscripts.pl";

use DivinumOfficium::LanguageTextTools qw(load_languages_data);
use DivinumOfficium::Scripting qw(dispatch_script_function parse_script_arguments);

binmode(STDIN, ':encoding(utf-8)');
binmode(STDOUT, ':encoding(utf-8)');

load_languages_data($lang1, $lang2, $langfb, $version, $missa);

my $n = 0;
while (my $linha = <STDIN>) {
  $linha =~ s/[\r\n]+$//;
  next unless length $linha;
  $n++;
  my ($idioma, $argumentos, $antifona) = split(/\t/, $linha, 3);

  print "<<<<CASO $n\n";
  # O contador de salmos reinicia-se a cada caso, senao o '[3]' do titulo
  # dependeria da ordem em que os casos foram pedidos.
  $psalmnum1 = 0;
  $psalmnum2 = 0;

  my @args = (parse_script_arguments($argumentos), $idioma);
  push(@args, $antifona) if defined($antifona) && length($antifona);

  my $t = eval { dispatch_script_function('psalm', @args) };
  if ($@) {
    my $e = $@;
    $e =~ s/[\r\n]+/ /g;
    print "<<<<ERRO $e\n";
  } else {
    $t = '' unless defined $t;
    $t =~ s/\n+$//;
    print "$t\n" if length $t;
  }
  print ">>>>FIM\n";
}
