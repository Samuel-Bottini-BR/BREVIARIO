#!/usr/bin/perl
# Colhe do Divinum Officium, para cada dia e hora, QUAL E O OFICIO DO DIA.
#
# Nao calcula nada: chama a funcao 'precedence' do proprio projeto, que e
# quem sabe as regras de precedencia, e escreve o que ela devolve. E o que
# a seccao 12 do prompt manda — 'nao calcule nada, pegue pronto'.
#
# uso: perl ordo_perl.pl <repo> < lista-de-casos
#
# Cada linha da entrada: <data MM-DD-AAAA> <TAB> <hora>
# A saida e uma linha por caso, com os campos separados por tabulacao:
#
#   data  hora  vencedor  classe  comum  tipo_comum  regra  regra_comum
#   tempo  nome  vespera  laudes  comemorado  tempus  die  titulo  comentario
#
# 'vencedor' e o ficheiro: 'Sancti/08-22.txt', 'Tempora/Pent12-0.txt'.
#
# 'tempus' e 'die' sao o que as CONDICOES dos ficheiros perguntam:
#     (tempore Nativitatis) ...
#     (die Epiphaniæ) ...
# Sao calculados por get_tempus_id e get_dayname_for_condition, que estao
# no SetupString.pl deles. Colhem-se em vez de se portarem: sao duas
# cascatas de mais de cinquenta ramos cada, sobre datas moveis, e nao ha
# nada a ganhar em reescreve-las.

use utf8;
use POSIX;
use File::Basename;
use Time::Local;

package main;

use FindBin qw($Bin);

BEGIN {
  die "uso: ordo_perl.pl <repo> < lista\n" unless @ARGV >= 1;
  $Bin = "$ARGV[0]/web/cgi-bin/horas";
}

our $repo = $ARGV[0];
our $version = 'Rubrics 1960 - 1960';
our $datafolder = "$repo/web/www/horas";
our $missa = 0;
our $missanumber = 0;
our $votive = '';
our $dioecesis = 'Generale';
our $error = '';
our $debug = '';
our $lang1 = 'Latin';
our $lang2 = 'Latin';
our $langfb = 'Latin';
our $only = 1;
our $column = 1;
our $Tk = 0;
our $Hk = 0;
our $Ck = 0;
our $expand = 'all';
our $priest = 0;
our $testmode = 'regular';
our $caller = '';

require "$repo/web/cgi-bin/DivinumOfficium/SetupString.pl";
require "$Bin/horascommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/dialogcommon.pl";
require "$repo/web/cgi-bin/DivinumOfficium/setup.pl";
require "$Bin/horas.pl";
require "$Bin/horasscripts.pl";
require "$Bin/specials.pl";
require "$Bin/specmatins.pl";

use DivinumOfficium::LanguageTextTools qw(load_languages_data);

binmode(STDIN, ':encoding(utf-8)');
binmode(STDOUT, ':encoding(utf-8)');

load_languages_data($lang1, $lang2, $langfb, $version, $missa);

sub limpo {
  my $v = shift;
  $v = '' unless defined $v;
  $v =~ s/[\r\n\t]+/ /g;
  $v =~ s/^\s+|\s+$//g;
  return $v;
}

# As regras sao de VARIAS LINHAS, e isso importa: '$rule =~ /Omit.*? Hymnus/'
# so encontra o Hymnus se ele estiver na MESMA linha do 'Omit'. Achatar a
# regra numa linha so faria o 'Omit' apanhar tudo o que viesse depois.
# Guarda-se a mudanca de linha como '\n' de dois caracteres, que o lado
# Python volta a desdobrar.
sub limpo_multilinha {
  my $v = shift;
  $v = '' unless defined $v;
  $v =~ s/\t/ /g;
  $v =~ s/\r//g;
  $v =~ s/^\s+|\s+$//g;
  $v =~ s/\n/\\n/g;
  return $v;
}

# Qual ficheiro deu o TEXTO do dia. Nem sempre e o que o nome do vencedor
# diz: depois de Agosto, os dias do Tempo tem um segundo ficheiro, chamado
# pelo mes liturgico, e a precedencia escolhe entre os dois. Em vez de
# adivinhar a escolha, pergunta-se ao resultado: compara-se o nome do
# oficio que ficou em %winner com o de cada candidato.
sub ficheiro_efectivo {
  our (%winner, $winner, $monthday, $datafolder);
  my $nome = $winner{Officium};
  return $winner unless defined $nome && length $nome;
  $nome =~ s/\s+$//;

  my @candidatos = ();
  push(@candidatos, "Tempora/$monthday.txt")
    if $monthday && $winner =~ /Tempora/;
  push(@candidatos, $winner);

  foreach my $cand (@candidatos) {
    next unless -e "$datafolder/Latin/$cand";
    my $s = eval { setupstring('Latin', $cand) };
    next unless $s && ref $s;
    my $of = $s->{Officium};
    next unless defined $of;
    $of =~ s/\s+$//;
    return $cand if $of eq $nome;
  }
  return $winner;
}

# O ficheiro do MES LITURGICO que se sobrepoe a um ficheiro do Tempo.
#
# 'officestring' — a funcao deles que le um oficio — nao le so o ficheiro
# pedido: para os dias depois de Agosto (Pent) e depois da Epifania (Epi)
# le TAMBEM o ficheiro do mes liturgico e sobrepoe-lhe as seccoes, menos a
# [Rank]. E dai que venham as licoes de Matinas e o nome do dia — o
# 'Dominica ... I. Octobris' que o hino de inverno pede.
#
# Aqui colhe-se so o NOME do segundo ficheiro; a sobreposicao faz-se do
# lado Python. A conta do mes liturgico e uma cascata de datas moveis, e
# por isso colhe-se em vez de se portar (decisao 3.22).
#
# Nao se recalcula o mes liturgico: usa-se o '$monthday' que a propria
# precedencia deixou. A conta nao depende so da data — nas Completas e
# nas Vesperas o oficio ja e o do dia seguinte, e o mes que sai e outro.
# Recalcular por conta propria dava, no sabado das Temporas de Setembro,
# o mes de hoje em vez do de amanha, e as Completas saíam com os salmos
# de domingo.
sub ficheiro_do_mes {
  our ($monthday);
  my ($fname) = @_;
  return '' unless defined $fname && length $fname;
  return ''
    unless $fname =~ m{^Tempora[^/]*/(?:Pent|Epi)}
    && $fname !~ m{^Tempora[^/]*/Pent0[1-5]};
  return $monthday ? "Tempora/$monthday.txt" : '';
}

# (ficheiro, linha da lua, chave da entrada movel) do Martirologio de
# amanha — que e o que se le hoje a Prima.
sub martirologio_do_dia {
  our ($version, $year, $month, $day, $dayofweek, $datafolder, %winner);
  my $dir = 'Martyrologium';
  $dir .= '1960' if $version =~ /1960|Newcal/;
  $dir = substr($dir, 0, 13) unless -e "$datafolder/Latin/$dir";

  my $chave = eval {
    my $a = getweek($day, $month, $year, 1) . '-' . (($dayofweek + 1) % 7);
    $a = '10-DU'
      if ($month == 10 && $dayofweek == 6 && $day > 23 && $day < 31);
    $a = 'Defuncti' if $winner{Rank} =~ /ex C9/i;
    $a;
  } || '';

  my ($m, $d) = split('-', nextday($month, $day, $year));
  my $ficheiro = "$dir/$m-$d.txt";
  $ficheiro = "Martyrologium/$m-$d.txt"
    unless -e "$datafolder/Latin/$ficheiro";

  my $luna = eval {
    _luna($m, $d, ($m == 1 && $d == 1) ? $year + 1 : $year, 'Latin');
  } || '';

  return ($ficheiro, $luna, $chave);
}

while (my $linha = <STDIN>) {
  $linha =~ s/[\r\n]+$//;
  next unless length $linha;
  my ($data, $hora_pedida) = split(/\t/, $linha, 2);

  our $hora = $hora_pedida;
  our $vespera = ($hora =~ /Vespera/i) ? 3 : 0;

  our ($winner, $commune, $communetype, $rule, $communerule, $rank);
  our ($commemoratio, $laudes);
  our (@dayname, %winner, %commune);
  # O que so as Matinas pedem: a Escritura corrente, a classe do oficio
  # comemorado, a vigilia transferida, o sinal de 'incipit' e o grau.
  our ($scriptura, $comrank, $transfervigil, $initia, $duplex, $tvesp);
  # As Vesperas tem duas listas de comemoracoes: a de HOJE (as segundas
  # Vesperas do dia que acaba) e a de AMANHA (as primeiras Vesperas do dia
  # que comeca). E ha ainda o 'oficio concorrente' — o dia que cede a hora.
  our ($cwinner, $cvespera, @ccommemoentries);
  $cwinner = '';
  $cvespera = 2;
  @ccommemoentries = ();
  $scriptura = $transfervigil = '';
  $comrank = $initia = $duplex = 0;

  my $erro = '';
  eval { precedence($data); 1 } or $erro = $@;

  if ($erro) {
    $erro =~ s/[\r\n\t]+/ /g;
    print join("\t", $data, $hora_pedida, 'ERRO', limpo($erro)), "\n";
    next;
  }

  my @rank = split(';;', limpo($winner{Rank}));

  # As duas cascatas de condicao, avaliadas com o estado deste dia e
  # desta hora.
  my $tempus = eval { get_tempus_id() } || '';
  my $die = eval { get_dayname_for_condition() } || '';
  # As cascatas do 'gettempora'. Cada uma responde 'que variante do tempo
  # se usa nesta peca': 'Adv3', 'Quad', 'Pasch', 'Dominica', 'Feria'. Sao
  # sessenta ramos sobre datas moveis; colhem-se em vez de se portarem.
  my %tempora;
  foreach my $chamador ('Psalmi minor', 'Capitulum minor', 'Hymnus major',
    'Invitatorium', 'Nunc dimittis', 'Lectio brevis Prima', 'Doxology',
    'Hymnus matutinum', 'getfrompsalterium major', 'Prima responsory',
    'Psalmi Matutinum')
  {
    $tempora{$chamador} = eval { gettempora($chamador) } || '';
  }
  my $tempora_salmos = $tempora{'Psalmi minor'};
  # Os restantes vao juntos num campo so, como 'chave=valor', para nao
  # crescer a tabela em dez colunas.
  my @martirologio = martirologio_do_dia();

  my $monthday_do_dia = $main::monthday;
  # O mes liturgico do oficio COMEMORADO. Nao e o do vencedor: a
  # comemoracao le-se com 'officestring($lang, $ficheiro, 0)', e essa
  # recalcula o mes com a marca a zero. Sao dois numeros diferentes no
  # mesmo dia — nas Vesperas da Assuncao, o vencedor esta na II semana de
  # Agosto e o domingo comemorado na III.
  my $monthday_comem = eval {
    monthday($day, $month, $year, ($version =~ /196/) + 0, 0)
  } || '';
  # E o mes de AMANHA, para o oficio que se comemora nas primeiras
  # Vesperas: nesse caso a funcao deles pede o dia seguinte.
  my $monthday_amanha = eval {
    monthday($day, $month, $year, ($version =~ /196/) + 0, 1)
  } || '';
  my $mes_vencedor = ficheiro_do_mes($winner);
  my $mes_comum = ficheiro_do_mes($commune);
  my $mes_escritura = ficheiro_do_mes($scriptura);
  my $mes_comemorado = ficheiro_do_mes($commemoratio);
  my $tempora_todos = join(';;',
    map { "$_=$tempora{$_}" } sort keys %tempora);

  print join("\t",
    $data,
    $hora_pedida,
    limpo($winner),
    limpo($rank),
    limpo($commune),
    limpo($communetype),
    limpo_multilinha($rule),
    limpo_multilinha($communerule),
    limpo($dayname[0]),
    limpo($rank[0]),
    limpo($vespera),
    limpo($laudes),
    limpo($commemoratio),
    limpo($tempus),
    limpo($die),
    limpo($dayname[1]),
    limpo($dayname[2]),
    limpo($tempora_salmos),
    limpo($tempora_todos),
    # O dia da semana COMO O OFICIO O CONTA. Nem sempre e o do calendario
    # civil: nas primeiras Vesperas e Completas de uma festa, o oficio ja
    # e o do dia seguinte.
    limpo($dayofweek),
    # Depois de Agosto os ficheiros do Tempo deixam de se chamar pela
    # semana ('Pent17-5') e passam a chamar-se pelo MES LITURGICO
    # ('093-5' = sexta da 3a semana de Setembro). O nome do vencedor fica
    # o antigo, mas o texto vem do novo — e sem isto a oracao das Temporas
    # de Setembro saía a do domingo.
    limpo($monthday_do_dia),
    limpo($monthday_comem),
    limpo($monthday_amanha),
    # Se hoje e dia de Temporas. E outra cascata de datas moveis: as
    # Temporas caem nas quatro estacoes, e a data de cada uma depende da
    # Pascoa, do Pentecostes e do Advento.
    limpo(eval { emberday() ? 1 : 0 } || 0),
    # O ficheiro de onde o TEXTO do dia veio. Nem sempre e o que o nome do
    # vencedor diz: depois de Agosto, os dias do Tempo tem um segundo
    # ficheiro, chamado pelo mes liturgico, e a precedencia escolhe entre
    # os dois. Aqui pergunta-se ao proprio resultado qual foi.
    limpo(ficheiro_efectivo()),
    # O Martirologio, que se le a Prima, e o do dia SEGUINTE, e abre com a
    # idade da lua — 'Luna vicésima prima'. Sao contas de calendario: o
    # ficheiro, a linha da lua e a chave da entrada movel colhem-se; o
    # resto e ler o ficheiro e por 'r.' a frente de cada linha.
    limpo($martirologio[0]),
    limpo($martirologio[1]),
    limpo($martirologio[2]),
    # Um dia pode ter MAIS DO QUE UMA comemoracao: o santo que cedeu o
    # lugar e a feria, por exemplo. Vem todas, separadas por '|'.
    limpo(join('|', grep { defined && length } @main::commemoentries)),
    # O oficio concorrente, e as comemoracoes do dia que comeca.
    limpo($cwinner),
    limpo($cvespera),
    limpo(join('|', grep { defined && length } @main::ccommemoentries)),
    # --- daqui para baixo, o que so as Matinas pedem ---
    # A Escritura corrente: o ficheiro de onde vem a licao do I Nocturno
    # numa feria.
    limpo($scriptura),
    # A classe do oficio comemorado, e a vigilia que se transferiu.
    limpo($comrank),
    limpo($transfervigil),
    # '$initia' diz se a licao de hoje ABRE um livro da Escritura — e o
    # que decide onde entram os incipit transferidos.
    limpo($initia),
    # O grau do oficio: 1 simples, 2 semiduplex, 3 duplex... Nao e a
    # classe; entra na conta de quantos nocturnos se dizem.
    limpo($duplex),
    # A tabela dos incipit transferidos (Str1960<ano>): que ficheiro do
    # Tempo empresta hoje as licoes do I Nocturno.
    limpo(eval { initiarule($month, $day, $year) } || ''),
    # De 29 de Dezembro a 5 de Janeiro as licoes do I Nocturno vem de um
    # ficheiro do Tempo escolhido pelo directorio do ano.
    limpo(eval {
      my $t = sprintf('Tempora/Nat%02i.txt', $day);
      get_from_directorium('tempora', $version, $t) || '';
    } || ''),
    # Os ficheiros do mes liturgico que 'officestring' sobrepoe a cada um
    # dos quatro oficios do dia.
    limpo($mes_vencedor),
    limpo($mes_comum),
    limpo($mes_escritura),
    limpo($mes_comemorado),
  ), "\n";
}
