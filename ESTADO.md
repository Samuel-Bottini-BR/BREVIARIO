# Onde estamos

Actualizado em 8 de Agosto de 2026.

## A EDIÇÃO LATINA ESTÁ FECHADA

`BREVIARIUM-latina-volume-unico.pdf` — **2.216 páginas.**
**As oito verificações passam.**

O pé vazio, remedido depois de a peça passar a partir-se: **2.113 de
2.117 páginas abaixo de 5 mm**. Sobram duas com mais de 30 mm, e são as
duas **fins de parte** — a última do Próprio do Tempo e a última do
Próprio dos Santos, antes de a parte seguinte abrir em página ímpar.
Essas têm de ficar assim. Poupou **524 páginas**: eram 2.740.

| | Verificação | |
|---|---|---|
| 1 | Nenhum ponteiro sobrevive | passa |
| 2 | Nenhum dado de controlo escapa | passa |
| 3 | Completude estrutural | passa |
| 4 | Referências de página (1.168) | passa |
| — | Pé vazio, por coluna e até à margem | 2.113/2.117 abaixo de 5 mm |
| 5 | Comparação com o sítio | 365/365 nas oito horas |
| 6 | Caminho do leitor | passa |
| 7 | Os três ofícios do Hausmann | passa |
| 8 | Nada em português | passa |

**1.253 remissões numeradas** — 387 ao Comum, 781 ao Saltério, 85 ao
corpo do livro. Corre com `python gerador/remissoes.py`, que fecha os
dois ciclos: primeiro as partes de numeração própria, depois o corpo do
livro sobre o volume cosido, até o mapa não mexer. Estabilizou em **2
passagens** e **2 voltas**.

Fica a dever **uma coisa só**: a colação peça a peça dos três ofícios do
Hausmann, que precisa da transcrição do livro escaneado. Ver abaixo.

## O que está feito e conferido

**O texto do ofício está completo e certo.** As oito horas, os 365 dias,
conferidas linha a linha contra o gerador do próprio Divinum Officium:

| Matinas | Laudes | Prima | Terça | Sexta | Noa | Vésperas | Completas |
|---|---|---|---|---|---|---|---|
| 365/365 | 365/365 | 365/365 | 365/365 | 365/365 | 365/365 | 365/365 | 365/365 |

Corre com `python gerador/varrer.py --hora <Hora>`. **Rodar depois de cada
etapa**, não só no fim: se um dia deixar de bater, foi a última mudança
que o quebrou.

**O livro está reorganizado nas partes clássicas.** Deixou de ser uma fila
de calendário de 2026 e passou a ser perpétuo — serve 2027, 2050, sempre.
Cada parte é uma secção onde se abre e se reza.

| Parte | Numeração |
|---|---|
| Ordinarium | própria, com asterisco |
| Psalterium — Domingo a Sábado × 8 horas | própria, com asterisco |
| Proprium de Tempore — Advento I a Pent 24 | corrida |
| Proprium Sanctorum — 1 Jan a 31 Dez | corrida |
| Commune Sanctorum — C1 a C11 | própria, com asterisco |

2.285 páginas na primeira composição, contra 3.092 da fila de calendário.

## O que ficou pendente — 7 de Agosto, fim da sessão

**`BREVIARIUM-latina-volume-unico.pdf` — 2.424 páginas, 12 MB.**

Resolvido nesta sessão:
- Os `;;`: **1.123 → 4**. A causa era o número do salmo colado ao fim da
  antífona (`génui te.;;109`). Sai agora como marca a vermelho —
  `Ps. 109` — que é como o breviário impresso o dá.
- Os três `@` não resolvidos: passam pela mesma via das horas.
- Verificação 8: **passa**. Os padrões estavam a acusar latim por
  português.

Falta, por ordem:

1. **As remissões numeradas.** O livro emite `Psalmi ut in Psalterio` e
   `Cetera ut in Communi`, mas **sem número** — o ciclo de recálculo sobre
   o volume cosido nunca chegou a correr. É a primeira coisa a fazer, e a
   máquina está toda escrita: âncoras nas posições, `folio_impresso()` em
   `verificar.py` para ler o fólio, `livro.juntar` para coser. Falta o
   ciclo: compor → coser → ler → reescrever → compor, até o mapa de
   âncoras estabilizar.
2. **Quatro `;;` que sobram.** Dois no Código de Rubricas (páginas 18 e
   26) e um no Próprio dos Santos (página 1493, `Ecclésiam meam.;;138`).
   Este último é `;;` **no meio da linha**, e a limpeza está presa ao fim
   da linha — alargar o padrão. Os do Código de Rubricas: limpar o texto
   cru antes de o imprimir.
3. **Os seis defeitos de aparência.** Nenhum tocado.
4. **A verificação 7**, os três ofícios do Hausmann.

## As oito verificações — medidas em 7 de Agosto sobre o PDF cosido

Corre com `python gerador/verificar.py`.

| | Verificação | Resultado |
|---|---|---|
| 1 | Nenhum ponteiro sobrevive | **4 falhas** — eram 1.123 |
| 2 | Nenhum dado de controlo escapa | **3 falhas** — eram 163 |
| 3 | Completude estrutural | **passa** |
| 4 | Integridade das referências de página | **passa** — 0 falhas em 356 remissões |
| 5 | Comparação com o site | **365/365** nas oito horas (`varrer.py`) |
| 6 | Volta pelo caminho do leitor | **passa** |
| 7 | Os três ofícios do Hausmann | **por escrever** |
| 8 | Nada em português | **passa** |

As quatro falhas da 1 e as três da 2 são o mesmo `;;`: dois no Código de
Rubricas (páginas 18 e 26) e um no Próprio dos Santos (página 1493,
`Ecclésiam meam.;;138`). Este último é `;;` **no meio da linha**, e a
limpeza está presa ao fim — alargar o padrão.

A **5** foi medida por inteiro em 8 de Agosto, incluindo Vésperas e
Completas, que numa passagem anterior tinham ficado com o registo
cortado: `365/365` nas oito, sem um dia por gerar e sem um ponteiro
sobrevivente.

## As remissões numeradas — FEITAS em 8 de Agosto

**356 remissões ao Comum, com número.** O ciclo estabilizou em **2
passagens**. Corre com `python gerador/remissoes.py`.

**Como funciona, e porque é barato:** o alvo é o **Comum**, que tem
numeração própria — o seu fólio é o mesmo esteja ele sozinho ou cosido no
volume. Por isso basta compor o Comum, ler as âncoras, e compor o resto
com os números. O Próprio do Tempo e o dos Santos é que partilham a
sequência corrida e só sabem o seu número na costura; as remissões PARA
eles ainda não existem.

## DUAS REGRAS QUE VALEM PARA TODO O PROJECTO

Custaram duas sessões e quatro defeitos. Ler antes de escrever qualquer
teste novo.

### 1. Nunca inferir do PDF o que o programa já sabe

Quatro defeitos, uma só causa — adivinhar, a partir do PDF, coisa que o
compositor já tinha na mão:

| O que se inferiu | O que o PDF devolveu | Custo |
|---|---|---|
| a caixa das letras num título | versalete: pôs-se `§Ac-C1§`, leu-se `§aC-C1§` | uma sessão |
| que posição de página é fólio | numas partes é, no leitor de fólios não era | 143 remissões falsas |
| que `\b` separa espaço de asterisco | não separa: ambos são não-letra, e `*23` lia-se `23` | leitura de fólio errada |
| que a página diz a que parte pertence | **o Saltério não imprime «Psalterium» em página nenhuma** — abre em «Dominica» | 224 remissões falsas |

**A regra: onde o compositor conhece o dado, ele grava-o e a verificação
lê-o. Só se extrai do PDF aquilo que existe apenas lá.**

Em obra: `perpetuo.construir()` escreve `<saida>-indice.tsv` com a parte,
os fólios e as páginas físicas de cada secção; a verificação 4 lê esse
ficheiro em vez de procurar nomes de parte no texto.

### 2. Um teste que anda pelo mesmo caminho do gerador não vê o buraco

**A verificação 5 dava 365/365 nas oito horas enquanto faltavam 74
posições no livro — entre elas a Assunção e a Epifania.** Não foi
descuido dela: ela não podia ver.

| | Por onde anda |
|---|---|
| **verificação 5** (`varrer.py`) | pelas **datas**: gera o dia 1 de Janeiro, o dia 2, … e compara com o gerador Perl do próprio Divinum Officium |
| **o livro perpétuo** (`perpetuo.py`) | pelas **posições**: lê `ordo-uniao.tsv` e compõe `Sancti/08-15`, `Tempora/Adv1-0`, … |

São dois caminhos diferentes para o mesmo corpus. A 5 confere que o
**texto** de um dia está certo; nunca chega a olhar para a lista de
posições, e por isso uma posição que o livro deixe cair passa-lhe ao lado
sem uma falha sequer. Pior: a 5 compara-se contra o **mesmo corpus** que
alimenta o gerador — concorda com ele por construção naquilo que ambos
lêem igual.

Quem apanhou o buraco foi a **verificação 7**, e apanhou-o porque é a
única que se mede contra fonte **de fora** — o Hausmann, livro impresso
em 1961, que não sabe nada do Divinum Officium.

**A regra: um teste só prova alguma coisa onde não partilha caminho nem
fonte com o que está a testar.** Ao escrever uma verificação nova,
perguntar primeiro: por onde é que ela anda, e contra que fonte se mede?
Se a resposta for «a mesma do gerador» nos dois casos, ela vai passar
sempre — e não vale nada.

**Corolário, e é o que se fez a seguir:** quando um teste não pode ver
uma coisa, não se aperta esse teste — escreve-se o que anda pelo caminho
que falta. As 73 posições recuperadas foram conferidas **posição a
posição** sobre o PDF (`scratchpad/conferir_74.py`): todas presentes,
todas com texto, nenhuma com ponteiro ou `;;` por limpar.

### 3. A régua mede o que se quer saber, não o que é fácil de medir

**Eu dei o vazio de página por resolvido com «669 de 669 páginas abaixo
de 10%», e havia páginas com 119 mm de pé vazio.** A régua estava errada
de duas maneiras, ambas por comodidade:

- **Media a linha na largura inteira.** O livro é a duas colunas: uma
  coluna cheia de um lado escondia a coluna vazia do outro.
- **Excluía o pé.** Media entre o primeiro e o último pingo de tinta, que
  é o que a extração dá de graça — e o que interessa é a distância do
  último pingo **até à margem**.

A régua certa mede **por coluna e até à margem**. Medido assim:

| | Páginas |
|---|---|
| até 5 mm de pé vazio | 2.293 |
| 5 a 15 mm | 96 |
| 15 a 30 mm | 80 |
| **mais de 30 mm** | **32** — a pior com 119 mm |

**A regra: antes de medir, dizer em voz alta o que se quer saber, e só
depois escolher a medida.** Se a medida for a que a ferramenta dá sem
esforço, desconfiar — foi ela que escolheu a pergunta.

Comparação com o modelo, medida com a mesma régua: o bilíngue de 1962 tem
as colunas entre **32% e 41%** de preenchimento e o pé em **0, 0 e 13
mm**. O nosso tem as colunas equivalentes — 24% a 44% — e era só o pé que
estava mal.

**A causa:** `.par { break-inside: avoid-column }`. Uma peça alta que não
coubesse no resto da coluna saltava **inteira** para a página seguinte.
Confirmado pelas piores páginas: a seguinte abria a meio de um Te Deum,
isto é, com o bloco empurrado. Passou a `break-inside: auto`, com órfãs e
viúvas a segurar a qualidade da partida — que é como o breviário impresso
faz: salmos e hinos partem-se à vontade.

### 4. Funil único para toda a limpeza

Quando a mesma limpeza é chamada de vários sítios, **um vai ficar
esquecido** — foi o que deixou passar `Ecclésiam meam.;;116`. A limpeza
dos dados de controlo faz-se agora num só ponto, `_peca()`, por onde toda
a peça passa antes de virar HTML, mais `parte_texto_corrido()` para o
texto cru do Código de Rubricas.

**As armadilhas em detalhe** — todas da mesma família: o PDF não devolve
o que se lá pôs.

1. **O versalete troca a caixa das letras no texto extraído do PDF.**
   Põe-se `§Ac-C1§` e lê-se `§aC-C1§`. Qualquer padrão que procure texto
   dentro de um título em versalete tem de ignorar a caixa — e as chaves
   guardam-se em minúsculas dos dois lados.
   **Regra geral: todo teste que procure texto no PDF ignora a caixa.**
2. **O mesmo vale para contar.** O contador dizia «0 com número» quando
   havia 356: procurava `Communi` e no PDF está `cOmmuni`.
3. **Não presumir que posição de página é igual a fólio impresso — mas
   também não presumir o contrário.** O fólio e o cabeçalho corrido vivem
   em caixas de margem diferentes e a extração junta-os numa só linha:

       *400 Commune SanCtorum

   O `folio_impresso()` exigia que a linha inteira fosse o número, não
   achava nada, e continuava página acima até topar um número de salmo
   solto. Daí **143 remissões darem-se por quebradas apontando para
   páginas certas**. O fólio está sempre numa **borda** da linha — ao
   princípio nas pares, ao fim nas ímpares. Lê-se de baixo para cima, e a
   primeira borda numérica é o fólio. Medido: **400/400** páginas do
   Comum, e a página 1 imprime `*1` e a 400 imprime `*400`, o que
   confirma que aí sim o índice é o fólio.

## Os defeitos de aparência — 8 de Agosto

Eram cinco na lista do `COMPARACAO.html`. **Dois já não existiam** e foram
descartados por medida, não por opinião:

- **Metade da página em branco:** medidas 669 páginas do corpo do livro,
  **669 com menos de 10% de branco no fim**. Era defeito da fila de
  calendário, onde cada dia abria em página nova; a reorganização
  perpétua desfê-lo.
- **Remissões ilegíveis:** o rótulo saía do nome interno da peça
  («TEXTO UT IN COMMUNI»). Hoje sai do nome litúrgico — *Cetera ut in
  Communi*, *Psalmi ut in Psalterio*, *Officium ut supra*.

Os que existiam, medidos e corrigidos:

| Defeito | A medida | A causa |
|---|---|---|
| Fólio gigante | **16pt** contra 9,3pt de corpo | as quatro caixas de margem estavam num selector **agrupado** (`@page :left, @page :right { @top-left, @top-right {...} }`) que o WeasyPrint não aplica: a regra caía inteira e ficava o tamanho por omissão. Vão agora separadas, e o tamanho em pontos — a caixa de margem pertence à página e nem sempre lê as variáveis do corpo |
| Segundo colchete | `ut in Psalterio [*23] [7]` | um `a.remissao::after` com `target-counter` acrescentava um número por cima do que se escreve no texto — e **errado**, porque conta dentro da parte composta, não do volume |
| Capitulares ausentes | **nenhuma letra entre 14 e 24pt** em página nenhuma do Próprio | `parte_de_posicoes` chamava `_peca()` sem dizer o género, e é o género que manda pôr capitular. Escrito o `genero_da_seccao()` |

## A verificação 7 — escrita, e o que fica a dever

Os três ofícios que o Hausmann desdobra peça a peça (capítulos XIII–XV):

| Classe | Dia | No corpus |
|---|---|---|
| Festivum | Assunção, 15 de Agosto | `Sancti/08-15` |
| Dominicale | Domingo XVI depois de Pentecostes | `Tempora/Pent16-0` |
| Ordinarium | Santo André Avelino, 10 de Novembro | `Sancti/11-10` |

**O que a verificação confere hoje:** que os três ofícios existem no
livro, que trazem as horas na ordem devida, e que o Festivum traz os três
nocturnos completos — as nove lições, que é o que distingue um ofício
festivo de todos os outros.

**Pagou-se à primeira corrida.** Acusou «*Festivum — Assumptio BMV: o
ofício não está no livro*», e estava certa: o Próprio dos Santos saltava
de 13 para 16 de Agosto. **74 posições eram saltadas em silêncio**, e
entre elas a **Assunção**, a **Epifania** e o **dia da Oitava do Natal**.

A causa: o nome do ofício lia-se só da secção `[Officium]`, e quem não a
tivesse era saltado sem uma palavra. Mas **nenhum ficheiro do corpus tem
`[Officium]` em disco** — é secção montada, e onde não se monta o nome
está no **primeiro campo do `[Rank]`**:

    In Assumptione Beatæ Mariæ Virginis;;Duplex I classis cum Octava...

Há agora recurso ao `[Rank]`, e quem ficar mesmo sem nome vai para a
lista `SEM_NOME` em vez de desaparecer. **Saltar em silêncio foi o que
escondeu a Assunção durante três sessões** — é a terceira regra desta
família: um caminho que desiste sem se queixar não se distingue de um
caminho que funcionou.

E logo a seguir a verificação 7 acusou «faltam as nove lições» estando
todas lá: o livro dá-as em **algarismo romano** (`Lectio vii`) e o teste
procurava `lectio 7`. Mesma regra outra vez — os rótulos vêm agora de
`PECAS_DA_POSICAO`, que é quem os imprime, e não escritos à mão no teste.

### Uma armadilha de ferramenta, não do livro

Ao remendar ficheiros com um script passado por *heredoc*, `\b` escrito
como `\\b` chega ao ficheiro como **carácter de backspace** (`\x08`), e o
padrão deixa de casar sem dar erro. Aconteceu duas vezes. **Para
qualquer remendo com escapes, escrever o script num ficheiro e correr o
ficheiro** — nunca colar pelo heredoc.

**O QUE FICA A DEVER:** a colação **peça a peça** contra o desdobramento
do livro. É o único ponto do plano que continua por fazer, e é o gabarito
**independente do Divinum Officium**, o que lhe dá o valor.

**Como fazê-la sem transcrever o Hausmann:** o que o teste precisa não é
o texto — é a **estrutura**. Para cada hora dos três ofícios, a lista
ordenada de **tipo de peça e secção de onde vem**: antífona do Próprio
dos Santos, salmos do Comum, capítulo do Próprio, e assim por diante.
Isso é informação litúrgica factual, e o capítulo IX já a resume em
matriz. Extrair só a tabela «peça, origem», rasterizando as páginas 79 a
115 e lendo como imagem, uma a uma. Depois confrontar: para cada posição,
cada peça vem da secção que o Hausmann diz?

### O Hausmann NÃO é modelo de diagramação

Corrigido por medida: está digitalizado em folha carta **horizontal**,
duas páginas de livro por quadro, e é um **manual didáctico de coluna
única com margens largas**. Serve para a matriz de peça e origem, e para
mais nada.

**O modelo tipográfico é o bilíngue de 1962 e o de 1942.**

## POR AQUI COMEÇA A PRÓXIMA SESSÃO

Fica **uma coisa só**: a **colação peça a peça dos três ofícios do
Hausmann**. Tudo o resto da edição latina está fechado e medido.

**O passo exacto por onde recomeçar:** montar a matriz «peça, origem» —
não o texto — rasterizando `hausmann-1961.pdf` e lendo como imagem.
Começar pelo **Festivum, capítulo XIII, quadros 42 a 49** do PDF, que traz
o ofício mais completo: I Vésperas, Completas, Matinas com os três
nocturnos, Laudes, Horas menores, II Vésperas e Completas. Mapeamento já
levantado: **o quadro N do PDF traz as páginas 2N-6 e 2N-5 do livro**.
Se a leitura das imagens não for fiável, parar e dizer — não montar uma
matriz em que não se confia. O detalhe está na secção «A verificação 7».

Se sobrar tempo depois disso, por ordem de proveito:

1. **O Ordo de cada ano** — `python gerador/ordo.py --ano 2027`. É
   caderno à parte, obrigatório, e sai pronto do cache do sítio.
2. **A edição bilíngue**, parada pelo motivo abaixo.

### As remissões, todas elas

| Destino | Quantas | Como se resolve |
|---|---|---|
| ao Comum | 357 | numeração própria: compõe-se a parte só, conta-se, e já se sabe |
| ao Saltério | 708 | o mesmo |
| ao corpo do livro | 130 | **caras**: o Tempo e os Santos partilham a sequência corrida, o fólio só se sabe com o volume cosido, e escrever os números desloca a paginação. Ciclo que repete até o mapa não mexer |
| em prosa, sem número | 46 | **e é assim que tem de ser**: é o Código de Rubricas a citar «ut in Psalterio» como latim corrido, não como remissão |

Nota apanhada a medir: o padrão `(?:ex|vide)` **sem fronteira de
palavra** apanhava o `ex` de «Duple**x** II classis» e inventava
remissões. Os dois padrões levam `\b`.

## O que está parado, e porquê

**A edição bilíngue.** Depende de tradução que não existe no corpus:
medido, 26,5% das peças não têm português — 85% das lições de Matinas,
65% das antífonas. O alvo, levantado comparando com o bilíngue de 1962:
antífonas, capítulos, versículos e orações em português; hinos e salmos
ficam como estão. São cerca de 16.840 peças.

## Ferramentas

- **PDF: WeasyPrint.** O GTK está em `%LOCALAPPDATA%\gtk3-runtime`, numa
  pasta só dele — desfaz-se apagando a pasta. `gerador/pdf.py` acha-o.
- **Voz:** `powershell -File gerador\falar.ps1 -Ficheiro recado.txt` lê em
  voz alta, para quando estiver a pintar.
- **O Ordo é obrigatório** e sai pronto do cache do site, nunca se calcula:
  `python gerador/ordo.py --ano 2027`.
