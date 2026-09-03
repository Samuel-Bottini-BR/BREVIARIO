# Achados técnicos — etapa 3

Levantados construindo o primeiro gerador. Tudo aqui foi medido, não estimado.

---

## 1. O motor de condicionais é o alicerce, e está portado e conferido

Os arquivos-fonte não são texto simples. Cada linha pode vir com uma
condição entre parênteses que a liga ou desliga conforme a versão de
rubricas, o tempo litúrgico, o dia da semana e mais. Exemplos reais:

    (rubrica 196) $rubrica examen
    (sed rubrica Ordo Praedicatorum aut rubrica cisterciensis omittitur)
    (sed rubrica 196 hæc versus omittuntur)
    (deinde dicuntur)

O motor tem níveis de força, escopo para trás e para frente, cercas e
aninhamento. Ele processa **todos** os arquivos do corpus, não só o
esqueleto das horas. Errar aqui é errar o livro inteiro em silêncio.

Portado para Python em `gerador/dofile.py` e conferido contra o Perl
original com `gerador/conferir_port.py`:

| | |
|---|---|
| arquivos conferidos | 3.010 (Ordinarium, Latim, Português) |
| versões de rubricas | 5 |
| comparações totais | 15.050 |
| divergentes | 0 |

O confronto achou dois defeitos meus antes de eu confiar no port. Um
deles vale registrar: escrevi `h[aæ]ec` numa expressão regular, o que
exige quatro caracteres, mas `hæc` tem três, porque o `æ` é um caractere
só. A palavra nunca casava, a condição virava falsa, e duas comemorações
saíam com texto a mais. Sem o confronto, isso teria ido para a página.

**Rodar `conferir_port.py` depois de todo `git pull`.**

---

## 2. Parte da lógica do ofício está em código Perl, não em dados

As remissões que começam com `&` não apontam para texto: são **chamadas de
função Perl**. São 21 no total, das quais 10 aparecem nos esqueletos das
horas:

    &Dominus_vobiscum (8x)   &Benedicamus_Domino (6x)   &Alleluia (6x)
    &Deus_in_adjutorium (3x) &psalm (2x)  &mLitany (2x)
    &Dominus_vobiscum1 (2x)  &Gloria  &Domine_labia  &Divinum_auxilium

Elas decidem, por exemplo, se se diz *Dominus vobiscum* ou *Domine exaudi*
conforme haja sacerdote, ou se acrescenta *Alleluia* conforme o tempo.

**Consequência:** o corpus limpo não sai só lendo arquivos. Estas 21
funções precisam ser portadas também. São poucas e curtas — é trabalho de
dias, não de semanas — mas não dá para ignorá-las.

---

## 3. A armadilha do idioma de reserva, confirmada no código

Em `web/cgi-bin/DivinumOfficium/LanguageTextTools.pm`, a função `prayer`:

```perl
$_prayers{"$lang$version"}{$name}
  || $_prayers{"$fb_lang$version"}{$name}   # <- idioma de reserva, inglês
  || $_prayers{"Latin$version"}{$name}
  || $name;
```

O degrau do meio é o que põe inglês na coluna portuguesa. O nosso gerador
pula esse degrau: vai de português direto ao latim, e registra a lacuna.

Não ficou como promessa. O `Corpus` **recusa-se a abrir** qualquer pasta
que não seja `Latin` ou `Portugues`, levantando erro. E ao fim de cada
geração imprime-se quais idiomas foram lidos.

---

## 4. O saltério latino e o português numeram os versículos diferente

Medido nos 202 arquivos de salmo:

| | |
|---|---|
| arquivos de salmo no latim | 202 |
| sem correspondente em português | 2 |
| mesmo número de linhas | 194 |
| **número de linhas diferente** | **6** |

Entre os 194 que casam, o deslocamento da numeração:

| Deslocamento | Salmos |
|---|---|
| nenhum | 150 |
| **latim um a mais** | **41** |
| **latim dois a mais** | **3** |

O latim segue a Vulgata e costuma começar no versículo 2, contando o
título como versículo 1; o português começa no 1. O texto corresponde
linha a linha, mas o rótulo não.

**Por que isto é grave.** O saltério manda recortar trechos de salmo, como
`33(2-11)` nas Completas de quarta-feira. Recortar "versículos 2 a 11"
pelo número em cada idioma pega **trechos diferentes**: no latim começa na
primeira linha, no português na segunda. As duas colunas da página
passariam a dizer coisas diferentes, ambas plausíveis, e ninguém notaria.

Foi exatamente o que aconteceu na primeira geração das Completas de
quarta-feira, e só apareceu porque conferi o alinhamento a olho.

**Correção adotada:** o recorte é decidido pela numeração latina, e as
mesmas posições são tomadas no português.

**Fica pendente:** os 6 salmos com contagem de linhas diferente não podem
ser casados por posição. Hoje o gerador se recusa a imprimir português
neles e registra o desalinhamento, o que é seguro mas não é solução. São:

    Psalm87, Psalm250, Psalm251, Psalm266, Psalm267, Psalm268

---

## 5. Detalhes menores, mas que quebram script

- Os arquivos de salmo **não têm cabeçalho de seção**: o texto todo fica
  no preâmbulo. Procurar uma seção `[Psalm4]` devolve nada, e o salmo
  some da página sem aviso.
- O Perl que vem com o Git para Windows é um Perl de msys: só abre
  caminhos no estilo `/c/Users/...`, nunca `C:\Users\...` nem
  `C:/Users/...`. Sem converter, todo arquivo falha em silêncio.
- O Python no Windows converte `\n` em `\r\n` ao passar dados a outro
  processo. O `chomp` do Perl não tira o retorno de carro, e o nome do
  arquivo fica com um caractere invisível no fim. Derrubou 3.010 arquivos
  de uma vez, sem mensagem de erro útil.

Os três erraram **em silêncio**. Daí a regra que ficou no gerador:
nenhuma peça é pulada sem avisar, e toda condição que não soube avaliar
é listada ao fim.
