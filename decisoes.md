# Registro de decisões

Criado em 4 de agosto de 2026, retroagindo por toda a conversa desde o
início. **Nada que já esteja aqui pode ser perguntado de novo.**

Regra de uso: antes de perguntar qualquer coisa, ler este arquivo e o
`PROMPT-BREVIARIO.md`. Se a resposta estiver num dos dois, seguir. Se
estiver parcialmente, seguir o que der e registrar a lacuna.

Atualizar **no instante** em que uma resposta é dada, não no fim da sessão.

---

# 1. Decidido no PROMPT-BREVIARIO.md

O que veio combinado desde o início. Não repetir estas perguntas.

| Assunto | Decisão |
|---|---|
| Rubricas | **1960**. Não é a Liturgia das Horas de 1970 |
| Edições | Duas: **latina** (tudo em latim) e **bilíngue** (latim + português) |
| Ordem de produção | **Volume único primeiro**, nas duas edições. Os quatro tomos por estação são **parâmetro**, não projeto novo |
| Fonte do texto | `github.com/DivinumOfficium/divinum-officium`, licença MIT |
| Formato | **in-18°**, cerca de 10 × 16 cm |
| Colunas | **Duas**, medida de cerca de 40 caracteres |
| Corpo | **7 base**, e toda a escala derivada dele **por proporção**. Nada de tamanhos fixos |
| Cores | **Vermelho e preto**. Rubricas em vermelho |
| Capitulares | Abrindo cada salmo, hino e oração |
| Cabeçalho corrido | Preciso: "Feria secunda ad Primam", não "Saltério" |
| Marcas de assinatura | No pé, para o encadernador |
| Margem interna | Com folga para a costura |
| Fitas marcadoras | Prever 4 a 6 |
| Ferramenta de PDF | **WeasyPrint**. Nunca conversão de EPUB pelo Calibre |
| Fonte de letra | Serifada com acentuação completa. EB Garamond ou TeX Gyre Pagella |
| Disposição bilíngue | **Duas colunas paralelas**, latim à esquerda, vernáculo à direita, como no bilíngue de 1962 |
| Nível de remissão | **Alto**, como o de 1942. E deixado como **parâmetro** |
| Convenção de remissão | Frase em latim nomeando a fonte + número de página entre colchetes. Nunca só um dos dois |
| Numeração | Saltério, Comum e Ordinário com **numeração própria**, separada |
| Hinos | **Ficam em latim**, mesmo na edição bilíngue |
| Onde falta português | Imprime-se o **latim, sem marca especial** |
| Idioma de reserva | **Nunca cair para o inglês.** Onde falta português, latim, e registra-se a lacuna |
| Tradução do Código de Rubricas | **Do latim**, não do inglês. Murphy e Hausmann só para entender |
| Ordo | Caderno anual **à parte**, não dentro do livro. Começar por 2026 |
| Matinas | No volume único, **entram junto** |
| Famílias litúrgicas | Não usar `Cist`, `M`, `OP` |
| Liturgia das Horas | `000LH_Abrev.pdf` e `LDH-04.pdf` em `NAO-USAR\`. Nada deles serve |
| Estilo | Português com acento; caminhos de disco sem acento; **nenhum emoji** |
| Números | **Nunca estimar sem medir** |

---

# 2. Decidido por você durante o trabalho

Cada pergunta feita e a resposta dada, em ordem.

### 2.1 Quanto do Hausmann ler
**Pergunta:** o Hausmann só se lê como imagem (escaneamento sem OCR
utilizável). Ler a especificação inteira, só a Parte II, ou adiar?
**Resposta:** **a especificação inteira** — páginas 4 a 61 do PDF.
*Feito. Registrado em `spec-hausmann.md`.*

### 2.2 Como rodar o Divinum Officium
**Pergunta:** sem WSL nem Docker instalados, qual caminho?
**Resposta:** **instalar o WSL**.
*Situação: recurso habilitado por DISM, aguardando reinício. Mas deixou de
ser necessário — ver 3.9.*

### 2.3 O reinício e as outras sessões
**Instruções, em três mensagens:**
- Há mais duas sessões do Claude Code a correr; o reinício mataria-as.
- Ao reiniciar, reabrir as três sessões automaticamente, de onde pararam.
- **Não pausar agora** — só na hora de reiniciar.
*Registrado em `RETOMAR-APOS-REINICIO.md`, com os comandos `--resume`.*

### 2.4 Divisão de papéis entre as fontes
**Instrução sua:**
- **O Hausmann é o método.** A matriz do capítulo IX e as seções *Where the
  various parts are found* dizem de onde vem cada peça. Implementar a partir
  dela, não por engenharia reversa.
- **O site é o gabarito.** Serve para conferir, não para deduzir a regra.
- **O Perl é o desempate**, quando os dois discordarem. E avisar, em vez de
  escolher sozinho.

### 2.5 A matriz do capítulo IX
**Instrução sua:** transcrever antes de escrever a lógica, e mostrar para
conferência célula a célula. "Se a matriz estiver errada, todo o resolvedor
sai errado."
*Feito. Depois reconstruída a partir das normas oficiais — ver 2.7.*

### 2.6 A tabela: regra ou cópia
**Pergunta sua:** "você usou a regra, ou só copiou o livro?"
*Resposta apurada: 35% das células lidas na página, 48% expandidas de aspas
por mim, 9% derivadas. Levou à marcação de procedência.*

### 2.7 Reconstruir a matriz a partir da lei
**Pergunta:** reconstruir a matriz a partir das normas oficiais 165-177, em
vez do resumo do Hausmann?
**Resposta:** **sim**.
*Feito. Matriz em `gerador/matriz_normas.py`, conferência em
`CONFERIR-matriz.html`.*

### 2.8 Formato dos arquivos para você ler
**Instrução sua:** "eu não consigo abrir arquivo md".
**Decisão permanente: tudo o que for para você ler sai em HTML**, que abre
com dois cliques no navegador. Nunca mais entregar Markdown para leitura.

### 2.9 Corrigir os erros da matriz
**Instrução sua:** "corrija os erros e confira tudo e continue a rodar".
*Feito: de 70 células em desacordo para 19, sobre 12.982 blocos dos 365 dias
de 2026.*

### 2.10 Construir o resolvedor
**Pergunta:** seguir para o resolvedor de remissões?
**Resposta:** **pode começar**. Depois: **seguir pelo `$`**, depois **pelas
funções `&`**.
*Feito. `@` e `$` conferidos contra o Perl em 30.674 seções, zero
divergências.*

### 2.11 Criar a página composta
**Instrução sua:** "pode criar a pagina".
*Feito: `pagina-completas-bilingue.pdf`, 99,8 × 160,2 mm.*

### 2.12 Versículos numerados e grafia
**Pergunta:** o site numera os versículos; o breviário impresso de 1962 não.
E a grafia: o Divinum Officium escreve `Iesus` nas rubricas de 1960, mas o
impresso de 1962 escreve `Jesus`.
**Resposta:** **"quero esteja como está no divinum officium"**.
**Decisão: seguir o Divinum Officium em ambos.**
- Versículos **numerados**
- Grafia de 1960: `j` passa a `i` — `Iesus`, `adiutorium`
- **Só no latim.** Nunca no português (`S. João`, não `S. Ioão`)

### 2.13 O site tcheco
**Instrução sua:** olhar `breviarium.srubarovi.cz`; os ficheiros são EPUB e
você não os abre.
*Investigado. Gerado do mesmo texto e com o mesmo programa que nós. Não tem
PDF nem português. **Deixa de ser dependência; fica como gabarito.** Baixado
agosto de 2026 da coleção bilíngue para `referencia/`.*

### 2.14 Comparar com o site tcheco
**Instrução sua:** "você tambem faça a comparação".
*Feito. Encontrou quatro peças em falta na nossa página, todas corrigidas.*

### 2.15 PDF de hoje e link para comparar
**Instrução sua:** gerar com o nosso programa o PDF de Sexta de hoje, e dar o
link do mesmo no site.
*Feito: `sexta-04-08-2026-bilingue.pdf` e `sexta-04-08-2026-latina.pdf`.*

### 2.16 Como trabalhar — correção do método
**Instrução sua, 4 de agosto:** a instrução de "mostrar cada etapa e
perguntar quando houver escolha" causava interrupção excessiva.
**Substituída pelo Apêndice A do `PROMPT-BREVIARIO.md`:**
- **Decidir e seguir, por padrão**, registrando aqui
- **Parar só em três casos:** caro de desfazer, contradiz o prompt, ou exige
  juízo litúrgico
- **Juntar as dúvidas** — três ou quatro de uma vez, no fim de uma etapa
- **Trabalhar em trechos longos**, mostrar marco concluído
- **Escopo: uma hora inteira de ponta a ponta**, não camada por camada

### 2.18 REGRA PERMANENTE — copiar o site em tudo
**Instrução sua, 4 de agosto, e substitui tudo o que se lhe oponha:**

> Copie o site em tudo. Texto, sinais, pontuação, o que aparece e o que
> não aparece. Se o site imprime, imprime. Se o site omite, omita. Sem
> exceção, sem me consultar.

**A aparência do livro é a última etapa**, quando os 365 dias estiverem a
sair. Aí decide-se sobre provas impressas. Todas essas escolhas são
parâmetro e mudam-se em minutos.

**Nunca mais perguntar sobre:** sinais de canto, grafia (Iesus/Jesus),
abreviações bíblicas, tamanho de letra, capitulares, cor, alinhamento
entre colunas, buracos brancos, numeração. Igual ao site; e se o site não
disser, o mais simples. Anotar aqui e seguir.

**Parar só por três motivos:** (1) o programa não roda e não consigo
resolver; (2) contradição dentro do `PROMPT-BREVIARIO.md`; (3) uma decisão
é caríssima de desfazer — e aí explicar em duas frases porquê.

**Consequência imediata:** a decisão 2.17 fica revogada. `noflexa = 1`,
como no site.

### 2.17 A flexa — REVOGADA por 2.18
*Tinha ficado, a seu pedido, a pontuação de canto completa (`noflexa=0`).
A regra 2.18 manda copiar o site sem excepção, e o site imprime sem
flexa. Revertido: `noflexa = 1`. Fica aqui só como memória de que a
questão existe, para a hora das provas impressas.*

Texto original da decisão:
**Pergunta minha:** o sinal `‡` tem dois usos contrários. No *Antiphonale*
é flexa — a inflexão a meio do versículo. No *Breviarium Romanum* marca a
divisão do versículo, e então o asterisco muda de sítio e o `†`
desaparece. O site vem sem flexa; eu tinha seguido o site.

**Resposta sua:** *"vou querer o sinal para quem reza cantando, que é o
tradicional"*.

**Decisão: `noflexa = 0`.** O `†` fica, o `‡` dos ficheiros passa a `†`, e
o asterisco **não muda de sítio**. O versículo sai com a pontuação de
canto completa: flexa, mediante e final. Os dois sinais saem a vermelho,
como as rubricas.

**É o único ponto em que não seguimos o site**, e a razão fica escrita
aqui: o site é gabarito do TEXTO, não do rito. Onde houver juízo
litúrgico, o site não decide.

*Feito. O gerador em lote do repositório já vem assim; o `preparar.py`
confere-o a cada arranque. As opções de apresentação passaram a ir do
Python para o Perl na conferência, para os dois lados não poderem
divergir por descuido.*

---

# 3. Decidido por mim

Escolhas técnicas que tomei sozinho, com o motivo. Reverta o que não gostar.

### 3.1 Portar o motor de condicionais para Python
**Motivo:** os arquivos-fonte não são texto simples — cada linha pode trazer
uma condição de rubrica. Esse motor processa **todo** o corpus. Depender do
Perl para isso amarraria o projeto ao site.
**Garantia:** conferido contra o Perl original em 3.010 arquivos × 5 versões
de rubricas = 15.050 comparações, zero divergências.

### 3.2 Verificar por confronto, não por inspeção
**Motivo:** cada port meu tem defeitos que não dão erro — dão texto errado
numa página bem diagramada. O confronto contra o original no corpus inteiro é
o único método que os apanha. Já apanhou onze.

### 3.3 Trava dura contra o inglês
**Motivo:** o prompt manda nunca cair para o inglês. Implementei como recusa:
o leitor **levanta erro** se lhe pedirem outro idioma que não latim ou
português. Promessa não basta.

### 3.4 Não corrigir os ficheiros do repositório
**Motivo:** há 143 referências quebradas no calendário geral, quase todas por
um ponto final a mais ou um acento. Em vez de editar o repositório — que o
`git pull` desfaria — a busca é **tolerante**: procura outra vez sem ponto,
sem acentos, e tratando `i`/`j` e `u`/`v` como a mesma letra. E **registra**
cada vez que a tolerância foi usada.

### 3.5 Nunca pular peça em silêncio
**Motivo:** o erro que mata este projeto é a peça que some sem aviso. Todo
gerador imprime `VAZIO: não encontrei texto para esta peça`. Já apanhou a
antífona final de Nossa Senhora.

### 3.6 As duas colunas da edição bilíngue são as duas línguas
**Motivo:** não cabe outra coisa. A página útil tem 79 mm; partida em duas dá
37 mm; partida outra vez para pôr duas línguas dentro de cada coluna daria
18 mm, cerca de doze caracteres por linha. É também o que faz o bilíngue de
1962. Na edição **latina**, as duas colunas são de latim.

### 3.7 Emparelhar as duas línguas peça a peça
**Motivo:** impede os buracos brancos.
**Pendente de revisão:** o bilíngue de 1962 e o dos checos emparelham **linha
a linha**, que alinha melhor num salmo longo. A mudar.

### 3.8 Chrome em vez de WeasyPrint, por enquanto
**Motivo:** o WeasyPrint no Windows exige a biblioteca GTK, que não está
instalada. O Chrome respeita `@page` e imprime em PDF. **O CSS é o mesmo nos
dois** — o trabalho não se perde. Passar a WeasyPrint quando o WSL estiver.

### 3.9 Usar o gerador em lote local, não o site
**Motivo:** o repositório traz `standalone/tools/epubgen2/EofficiumXhtml.pl`,
que produz o ofício sem servidor. Faltava-lhe um módulo Perl, o `CGI`,
instalado em `perl5/` sem tocar na instalação do Git. Um segundo por hora: os
365 dias × 8 horas em menos de dez minutos, **sem fazer 2.920 pedidos ao
servidor deles**. Tornou o reinício não urgente.

### 3.10 Não correr o motor de condicionais nos ficheiros de salmo
**Motivo:** eles abrem com um título entre parênteses —
`(Canticum Simeonis * Luc. 2:29-32)` — e o motor leria esse parêntese como
condição de rubrica, engolindo a linha seguinte. Era o que fazia o Nunc
dimittis perder o primeiro versículo.

### 3.11 Ler o preâmbulo do vernáculo sem a camada latina
**Motivo:** o `setupstring` empilha o preâmbulo do português com o do latim.
É fiel ao original — que deita o preâmbulo fora antes de o usar — mas nos
salmos, cujo texto **está** no preâmbulo, isso fazia sair o salmo em
português e a seguir em latim, na mesma coluna.

### 3.12 "O Próprio" não é sempre o Proprium Sanctorum
**Motivo:** numa festa do Senhor — oitava da Páscoa, Ascensão, Corpus
Christi, Sagrado Coração — o Próprio é o **do Tempo**. Descoberto ao comparar
os 365 dias; explicava 35 discordâncias sozinho.

### 3.13 A cláusula do próprio, como regra geral
**Motivo:** quase todas as normas 165-177 terminam com "salvo o que for dado
como próprio". Toda célula da matriz dá o **caso normal**. O resolvedor tem
de procurar primeiro no próprio do dia, e só depois consultar a matriz.

### 3.14 A função `&psalm` portada por inteiro, menos o canto
**Motivo:** é a função que põe salmo na página, e era a maior peça que
faltava. Sem ela os salmos saíam sem título, sem o *Glória Patri* no fim e
sem o sinal `‡` que marca onde acaba a antífona. Ficaram de fora os ramos
do canto — mais de cento e cinquenta linhas de ajuste de neumas que nunca
se aplicam a texto — e o saltério de Pio XII, que o prompt proíbe.
**Garantia:** conferida contra o Perl em **684 casos** — cada ficheiro de
salmo nas duas línguas, todas as formas de chamada escritas no corpus, e
os recortes com antífona. Zero divergências.

### 3.15 O contador de salmos do site não entra no livro
**Motivo:** o site escreve `Psalmus 62 [3]`. O `[3]` é o número do salmo
dentro da hora, e serve para navegar no ecrã: nenhum breviário impresso o
traz. Fica ligado no gerador, porque é o que o confronto contra o Perl
exige, e desligado na composição da página. Reverter é mudar uma linha.

### 3.16 A flexa — REVERTIDA no mesmo dia, ver 2.17
**O que eu tinha decidido:** seguir o site, que vem com `noflexa=1` e
portanto sem flexa. **Foi revertido por si**, e com razão: o site não é
gabarito em matéria de juízo litúrgico. Fica aqui o registo do erro para
não se repetir — o gabarito manda no que é texto, não no que é rito.

### 3.17 A comparação usa o compositor da página, não uma cópia dele
**Motivo:** o `comparar_texto.py` montava o ofício por conta própria — com
o *Glória Patri* escrito à mão no código. Media a distância entre duas
coisas nossas. Agora chama o mesmo compositor que produz o PDF: o que se
compara é o livro, não um ensaio do livro.

### 3.19 O Ordo colhe-se, não se calcula
**Motivo:** a secção 12 do prompt manda pegar o Ordo pronto. As regras de
precedência — que festa vence, o que se comemora, de que Comum se toma —
são chamadas **uma vez** pela função `precedence` do próprio Divinum
Officium, e o resultado fica em `ordo-2026.tsv`: 365 dias × 8 horas =
2.920 linhas. Depois disso o gerador nunca mais toca no Perl para saber
que dia é.

Colhem-se também três cascatas de condição que seria loucura reescrever —
mais de cinquenta ramos cada, sobre datas móveis:

| Colhido | Para que serve |
|---|---|
| `get_tempus_id` | responde a `(tempore Nativitatis)`, `(tempore Quadragesimæ)` |
| `get_dayname_for_condition` | responde a `(die Epiphaniæ)`, `(die Nativitatis)` |
| `gettempora('Psalmi minor')` | que antífona do tempo entra nas horas menores |

**O que isto consertou de uma vez:** a antífona final de Nossa Senhora
saía sempre *Salve Regina* (agora sai *Alma Redemptoris* no Natal, *Ave
Regina* na Quaresma, *Regina cæli* na Páscoa); e o `&Alleluia` saía
sempre *Allelúia* (agora sai *Laus tibi, Dómine* da Septuagésima à
Páscoa).

### 3.20 A regra `Omit` do dia
**Motivo:** o `[Rule]` de cada ofício pode calar um bloco inteiro —
`Omit Hymnus Preces Suffragium Commemoratio`, na oitava da Páscoa. Sem
isso o hino saía onde não devia. Porta de `specials.pl`, com a segunda
regra que a acompanha: `Capitulum Versum 2`, que põe um versículo no
lugar do capítulo.

### 3.21 Os rótulos de procedência não entram
**Motivo:** o site escreve, ao lado do título de cada bloco,
`{ex Psalterio secundum diem}` ou `{Psalmi et Antiphona de Dominica}`. É
ajuda de ecrã para quem navega — sai em itálico cinzento — e nenhum
breviário impresso o traz. Portá-la exigiria toda a máquina do `setbuild`
e não daria nada ao livro. Fica de fora, e a comparação ignora-a dos dois
lados.

### 3.22 O que se colhe do Perl, e o que se porta
**Motivo:** a regra passou a ser esta, e vale para o que falta. **Colhe-se**
o que é cascata de decisão sobre datas móveis — dezenas de ramos que só
respondem "qual variante" e nunca mudam texto: `precedence`, `get_tempus_id`,
`get_dayname_for_condition`, `gettempora`, o dia da semana do ofício. **Porta-se**
o que produz ou transforma TEXTO: o resolvedor, as funções `&`, a salmodia,
o alleluia do tempo, a regra `Omit`, o alleluia dos responsórios.

Porquê a linha aí: o texto tem de sair do nosso gerador para poder ser
paginado, e por isso portou-se e conferiu-se peça a peça. As cascatas de
data não produzem texto nenhum — reescrevê-las seria só arriscar erro.

O Ordo de 2026 tem hoje **20 colunas × 2.920 linhas**, e o gerador nunca
mais toca no Perl depois de o ter.

### 3.23 O `[Special <Hora>]` é um esqueleto, não texto
**Motivo:** quando o ofício do dia traz `[Special Completorium]`, essa
secção substitui o esqueleto do Ordinário — e volta a passar pela mesma
máquina, com os seus `#`, `$` e `&`. Tratá-la como texto fazia sair
`$Pater noster` impresso à letra no dia de Finados. É o que dá as
Completas do Tríduo Sacro e as de 2 de Novembro.

### 3.34 Um dia pode ter mais do que uma comemoração
**Motivo:** o campo `comemorado` do Ordo traz **uma**; a lista completa
está noutro sítio (`@commemoentries`) e é essa que vale. Num sábado de
Novembro comemoram-se a féria e Nossa Senhora; num domingo, o santo que
cedeu o lugar. As entradas que aparecem sem pasta são do Tempo.

### 3.33 A regra do Comum só vale se as antífonas vierem do Comum
**Motivo:** o Comum pode mandar trocar o quinto salmo das Vésperas —
`Psalm5 Vespera=113`. Mas essa ordem só se cumpre **quando foi do Comum
que vieram as antífonas do dia**. Se as antífonas são do Saltério, o
Comum não manda no salmo.

No original é uma condição de três caracteres — `$c eq 4`, o código de
procedência das antífonas — encostada ao fim de uma expressão de dez
linhas. Foi o que me escapou em setenta dias do ano.

**Como a encontrei:** sondando o Perl e o nosso lado no mesmo dia, e
comparando os cinco pares antífona/salmo lado a lado. Quatro batiam e o
quinto não. Quando a diferença é assim tão estreita, o erro está numa
condição, não na estrutura.

### 3.32 Duas regras de Comum, e não são a mesma
**Motivo:** o `Psalmi Dominica` pode vir de dois sítios que se parecem e
não são iguais:

| | |
|---|---|
| a regra de Comum que a **precedência** guardou | é a que as horas menores consultam |
| o `[Rule]` do **ficheiro** do Comum | é o que Laudes e Vésperas consultam |

O original usa uma em `psalmi_minor` e a outra em `psalmi_major`. Ler a
errada fazia Santa Inês rezar os salmos da féria em Laudes quando devia
rezar os de domingo. Estão as duas em `proprio.py`: `regra_do_comum` (a
primeira) e `secoes_comum['Rule']` (a segunda).

**Tentativa que não deu — fica registada para não se repetir:** restringir
a segunda aos Comuns a sério (`Commune/C6-1`), excluindo os ofícios de
santo que servem de Comum (`vide Sancti/01-01`). Ganhou cinco dias nas
Vésperas e perdeu cinco nas Laudes. Troca nula: **o discriminador é
outro**, e o problema das Vésperas não está aqui.

### 3.31 O nome do dia lê-se do Ordo, não do ficheiro
**Motivo:** o hino de domingo tem forma de inverno em Outubro e Novembro,
e o original conhece-os pelo NOME do dia — *Dominica XIX Post Pentecosten
**I. Octobris***. Esse nome não está no ficheiro do vencedor
(`Tempora/Pent19-0.txt` diz só *Dominica XIX Post Pentecosten*): está no
do mês litúrgico. Lê-se do Ordo, onde foi colhido do próprio Perl.

É a mesma lição da decisão 3.25, noutra roupagem: **onde o original
compõe um valor a partir de várias fontes, não o recompor — colhê-lo.**

### 3.29 No tempo pascal, Laudes diz-se sob uma só antífona
**Motivo:** da Páscoa a Pentecostes os cinco salmos de Laudes rezam-se sob
*Allelúia, allelúia, allelúia* — uma antífona para todos, e as do dia da
semana calam-se. Só quando o dia não tem antífonas próprias: uma festa com
as suas mantém-nas. São 38 dias do ano.

### 3.30 O til junta a linha com a seguinte
**Motivo:** os ficheiros escrevem

    V. Orémus pro beatíssimo Papa nostro ~
    r. N.

e isso é **uma** linha, não duas: o `~` diz que a seguinte lhe pertence, e
a marca de coluna `r.` da continuação desaparece na junção. Sem isto o
nome do Papa saía numa linha sozinha, nas Preces feriais.

### 3.28 O sinal `‡` vai à antífona sempre que foi posto
**Motivo:** o `‡` marca, dentro do primeiro versículo do salmo, onde acaba
a antífona — e a antífona leva um também, no fim, para o olho ir de um
lado ao outro. Eu tinha lido a regra pela metade: julguei que a antífona
só o levava quando cobria o versículo **inteiro**, porque foi assim no
primeiro caso que examinei. Em Laudes isso não explicava nada, e eram 140
dias.

A regra verdadeira é mais simples: **se o sinal foi posto, a antífona
leva-o**. Vi-a olhando o HTML do gerador, não deduzindo:

    Ant. Dómine, * refúgium factus es nobis. ‡
    89:1 Dómine, refúgium factus es nobis: * ‡ a generatióne in generatiónem.

As Laudes passaram de 155 para 260 dias com esta linha só, e as horas
menores não se mexeram.

### 3.26 O Martirológio colhe-se pela lua, monta-se pelo texto
**Motivo:** a Prima lê o Martirológio do dia **seguinte**, e abre pela
idade da lua — *"Nonis Augústi Luna vicésima prima. Anno Dómini 2026"*. A
lua sai de uma tabela de ouro áureo com trinta e uma letras; o ficheiro
depende do dia seguinte; a entrada móvel depende da semana. As três são
contas de calendário, e vão para o Ordo. O que se portou foi só a
montagem: ler o ficheiro e marcar as linhas.

### 3.27 O `&special('#Bloco')` é uma chamada ao bloco
**Motivo:** dentro de um `[Special <Hora>]` pode vir
`&special('#Martyrologium', 'Latin')`. Não é texto: é a máquina a chamar-se
a si própria pelo nome do bloco. Reescreve-se como `#Martyrologium` antes
de processar, que é o que o original faz por outro caminho. Sem isso, a
Prima de 2 de Novembro saía sem Martirológio nenhum.

### 3.25 O ficheiro do dia pergunta-se ao resultado, não se adivinha
**Motivo:** depois de Agosto, cada dia do Tempo tem **dois** ficheiros — um
pela semana (`Pent17-5`) e outro pelo mês litúrgico (`093-5`) — e a
precedência escolhe entre eles. O nome do vencedor fica sempre o primeiro,
mesmo quando o texto veio do segundo.

Tentei adivinhar a escolha por regra e errei duas vezes: uma fez as
Têmporas de Setembro rezarem a oração do domingo, outra fez dez sábados
rezarem Completas de domingo. A solução é não adivinhar: o arnês compara o
nome do ofício que ficou em `%winner` com o de cada candidato, e devolve
o que bate. Fica no Ordo, na coluna `ficheiro`.

**A regra geral que isto ensina:** onde o original escolhe entre fontes,
não reproduzir a escolha — perguntar qual foi.

### 3.24 A oração da féria é a do domingo
**Motivo:** na maior parte dos dias do ano não há oração própria — reza-se
a do domingo que precede. Os ficheiros do Tempo chamam-se pela posição
(`Pent12-0` é o domingo XII depois de Pentecostes), e basta trocar o dia
por `-0`. Sem isto faltava a oração em cerca de 120 dias.

### 3.18 O Comum deixa de ser escrito à mão
**Motivo:** estava escrito `'comum': 'Commune/C5.txt'` no ficheiro da
Sexta. Agora lê-se da linha `[Rank]` do próprio, pelo mesmo caminho do
original (`extract_common`), conferido em **660 casos** — todos os campos
de Comum que existem no corpus, dentro e fora do tempo pascal, zero
divergências.

### 3.35 A tabela de incipit transferidos está vazia em 1960

**Medido:** `initiarule` lê a tabela `Stransfer` do ano e diz que ficheiro
do Tempo empresta hoje as lições do I Nocturno. As entradas dessa tabela
vêm marcadas por versão — `DA`, `1570`, `Newcal`, `M1617` — e **nenhuma
casa com o padrão `1960`**. A versão de 1960 também não herda tabela
nenhuma: a coluna `transferbase` do `data.txt` deles está em branco para
ela. Colhida sobre os 365 dias de 2026: **zero entradas**.

**Consequência:** com `initiarule` vazia, `resolveitable`, `tferifile` e
`StJamesRule` nunca correm. Não estão portadas, e a razão está escrita em
`matinas.py`.

### 3.36 `officestring` lê DOIS ficheiros, e a `[Rank]` vem do segundo

Depois de Agosto — e depois da Epifania — os dias do Tempo têm um segundo
ficheiro, chamado pelo **mês litúrgico**: `Tempora/093-3.txt` é a
quarta-feira da 3.ª semana de Setembro. A função deles que lê um ofício
não lê só o ficheiro pedido: lê os dois e sobrepõe-lhe as secções.

O original **parece** proteger a `[Rank]` da sobreposição:

    if (($version =~ //i && $key =~ /Rank/i)) { ; } else { $s{$key} = $m{$key}; }

Mas `//` em Perl é o **padrão vazio**: reaproveita o último padrão que
tenha casado, e na prática a condição não se cumpre. Medido: pedida a
Quarta-feira das Têmporas de Setembro, a função deles devolve
`Feria Quarta Quattuor Temporum Septembris;;Feria major;;4.9` — a `[Rank]`
do ficheiro do mês. **Sem isto, as bênçãos das Têmporas saíam as da féria
comum**, em três dias do ano.

### 3.37 O mês litúrgico não se recalcula: colhe-se

A conta do mês litúrgico não depende só da data. Nas Completas e nas
Vésperas o ofício já é o do dia seguinte, e o mês que sai é outro:
no sábado das Têmporas de Setembro, as Completas pedem o mês de **amanhã**.
Recalculado por conta própria dava o de hoje, e as Completas saíam com os
salmos de domingo.

Colhem-se por isso **três** números por dia: o `$monthday` que a
precedência deixou, o do dia (marca a zero) e o de amanhã (marca a um). O
ofício comemorado usa o do dia; nas **primeiras** Vésperas usa o de amanhã.

### 3.38 A supressão do alleluia é de TODAS as horas

Da Septuagésima ao sábado santo apaga-se **todo** o alleluia que o texto
traga escrito. Não basta não o acrescentar: há antífonas que o trazem no
ficheiro, e essas ficavam com ele. É o que faz a festa de S. Matias, que
cai na Quaresma e toma as antífonas do Comum dos Apóstolos, dizê-las sem
o alleluia que o Comum lhes dá.

O original fá-lo em `webdia.pl`, ao texto de todas as horas, mesmo antes
de o mostrar. Aqui está em `alleluia.suprime_se` e `alleluia.tempo`, e
passa por todos os cinco compositores.

### 3.39 O `#Prelude` é um bloco que não está em ficheiro nenhum

O original põe, à cabeça do esqueleto de **todas** as horas, um bloco que
o Ordinário não traz: `#Prelude`. Se o ofício do dia tiver uma secção
`[Prelude <Hora>]`, ela sai ali; se não, o bloco desaparece.

É o que faz o domingo de Páscoa avisar, antes de Matinas, que quem esteve
na Vigília não as reza — e o que avisa, na Quinta-feira Santa, que quem
foi à Missa vespertina não reza Vésperas.

### 3.40 A oração pede-se pelo NÚMERO da hora

A ordem por que se procura a oração **é** a regra, e o número da hora
manda nela: as Vésperas pedem `[Oratio 3]`, as Laudes e as horas menores
`[Oratio 2]`, e Matinas têm ainda uma porta antes de todas,
`[Oratio Matutinum]`. Sem isso, as férias da Quaresma diziam a Vésperas a
oração das Laudes — **mais de trinta dias do ano**.

### 3.41 `Psalmi Dominica` e `Psalmi minores Dominica` não são a mesma regra

Nas horas **menores** o original aceita as duas grafias; nas **maiores**
exige `Psalmi Dominica` por extenso. No Tríduo Sacro está escrita a outra
— `Psalmi minores Dominica` — e sem a distinção as Laudes do Tríduo
começavam pelo salmo 92 em vez do 50.

### 3.42 As comemorações têm ordem, limite e conclusão comum

Três regras, todas medidas contra o gerador:

| | |
|---|---|
| **ordem** | cada comemoração recebe uma chave pela sua classe, e sai por essa ordem — a de classe mais alta primeiro |
| **limite** | nas rubricas de 1960, um dia de II classe ou uma féria maior admitem **uma** comemoração só |
| **conclusão** | duas orações seguidas dizem-se sob uma só conclusão: a primeira perde a sua, e a última fecha as duas |

E há **quatro** origens, não uma: o ofício concorrente (o dia que cede a
hora), as comemorações de amanhã, as de hoje, e a que o próprio ofício
traz escrita numa secção `[Commemoratio]`. Esta última pode nem trazer o
texto: traz uma remissão — `@Tempora/Quad5-5:Oratio` — e o que se reza é a
antífona, o versículo e a oração **desse** ofício.

### 3.43 As Têmporas dizem as Preces, mesmo ao sábado

A reforma de 1960 reduziu as Preces feriais às quartas e sextas-feiras —
mas **as Têmporas contam sempre**, e as terceiras caem ao sábado. Sem
isso, os três sábados das Têmporas ficavam sem as suas quarenta linhas de
Preces. O dia de Têmporas colhe-se do Perl: é outra cascata de datas
móveis.

### 3.44 O sinal `;mtv` só vale se o próprio tiver essa variante

Nas Vésperas de um Confessor ou Doutor o hino leva última estrofe
própria — o `Hymnus1`. Mas há ofícios marcados assim que dão um hino
inteiro seu, sob o nome simples. Sem a ressalva, o hino próprio dos Anjos
da Guarda cedia o lugar ao `Iste Conféssor` do Comum.

### 3.45 A regra bate a antífona, no quinto salmo das Vésperas

Uma antífona própria pode trazer os seus próprios salmos, escritos a
seguir a `;;`. Mas quando a **regra** já trocou o quinto salmo das
Vésperas, é a regra que manda: é o `aflag` do original. No domingo da
Santíssima Trindade a antífona traz `;;116` e a regra manda 113.


### 3.46 O livro por expandir tem catorze mil páginas — medido

**Medido em 5 de Agosto**, com o ano inteiro composto e impresso:

| | |
|---|---|
| Janeiro, edição latina | **1.176 páginas** em 31 dias — **37,9 páginas por dia** |
| Latim no ano, expandido | **26.086.810** caracteres |
| Peças com texto | **73.706** |
| Peças **distintas** | **6.471** |
| Repetição média | **11,4 ×** |
| O que sobra sem repetições | **3.921.713** caracteres — **15%** |

**Oitenta e cinco por cento do livro é a mesma coisa impressa outra vez.**
Os salmos sozinhos são 54% do total, e passam de 14,1 milhões de
caracteres para 460 mil quando se imprimem uma vez só — trinta vezes
menos.

O que fica no núcleo diz que a conta fecha: **as lições de Matinas são
metade dele** (1,91 milhões de caracteres), e essas são mesmo diferentes
todos os dias. É por isso que um breviário completo com Matinas é grosso,
e é só por isso.

À densidade medida — cerca de 1.900 caracteres por página no in-18 de
corpo 7 —, o núcleo dá **cerca de dois mil páginas**. Isso é um breviário.

**Consequência:** a estrutura que o prompt já decidiu — «Saltério, Comum e
Ordinário com numeração própria, separada», «nível de remissão alto, como
o de 1942» — não é um requinte. É a única maneira de o livro caber num
volume. Fica assim o caminho:

1. **Marcar a procedência de cada peça.** Os compositores já sabem de onde
   cada peça veio (`proprium` devolve-o); falta guardá-lo na `Peca`.
2. **Imprimir uma vez o que se repete:** Ordinário, Saltério da semana,
   Comum — cada um com a sua numeração.
3. **Nos dias, imprimir só o próprio**, e no lugar do resto uma linha de
   remissão.
4. **Paginar em duas passagens:** compor sem números, medir onde caiu cada
   âncora, recompor com os números.

### 3.47 O Chrome não compõe o ano inteiro num ficheiro só

**Medido:** o ano em HTML dá **46,2 MB**. O Chrome sem janela aceita-o,
mas não escreve PDF nenhum e sai sem erro. Partido por mês, cada parte
compõe-se em segundos.

Por isso `livro.py` tem a opção `--por-mes`, e as doze partes juntam-se
depois com o `pypdf`, que está instalado.

**A causa da falta de cabeçalho corrido e de número de página é outra, e
mais funda:** o Chrome não sabe as caixas de margem do `@page` — nem
`@top-center`, nem `counter(page)`, nem `string-set`. Isso é do
WeasyPrint, e o WeasyPrint precisa da biblioteca GTK, que no Windows se
instala à parte. **Sem ela não há como paginar**, e sem paginação não há
remissões com número de página. É o único bloqueio real do projecto.


### 3.48 A paginação faz-se em duas passagens, e dispensa o WeasyPrint

**O problema:** um livro precisa de três coisas que só se sabem DEPOIS de
paginado — o cabeçalho corrido, o número de folio, e as remissões com
número de página. O WeasyPrint faz as três sozinho, pelas caixas de
margem do `@page`; o Chrome não sabe nenhuma delas.

**A saída, medida e a funcionar:** lê-se do próprio PDF.

1. Compõe-se o corpo do livro, sem cabeçalho nem número.
2. Lê-se o PDF página a página e vê-se em que página caiu cada hora.
3. Compõe-se uma folha de **carimbo** — as mesmas páginas, do mesmo
   tamanho, só com o cabeçalho e o folio.
4. Sobrepõem-se as duas, com o `pypdf`.

Provado na prova de três dias: **125 páginas, 24 barras de hora
encontradas** — as 24 que lá estão (3 dias × 8 horas). Conferido por
amostragem: página 2 «In Vigilia Nativitatis Domini ad Matutinum»,
página 40 «In Nativitate Domini ad Matutinum», página 100 «S. Stephani
Protomartyris ad Laudes», página 125 «S. Stephani Protomartyris ad
Completorium». O folio bate em todas.

**Consequência:** o WeasyPrint sai do caminho crítico. Fica como
melhoria, para quando a biblioteca GTK estiver — o CSS é o mesmo.

**E o passo 2 é o que as remissões precisam:** saber em que página caiu
cada coisa. Feito para o cabeçalho, está feito para elas.

Duas cautelas que custaram tempo, e ficam escritas:

- O processo do Chrome que se lança é só o **arranque**: sai logo, e quem
  compõe fica a trabalhar por trás. Não basta esperar que ele termine —
  espera-se que o PDF apareça E deixe de crescer.
- Sem um `--user-data-dir` só nosso, o Chrome que já está aberto apanha o
  pedido, entrega-o à janela do utilizador e sai sem escrever nada.

### 3.49 O ano latino, medido: 13.710 páginas

Composto, paginado e cosido — `BREVIARIUM-ROMANUM-2026-latina.pdf`,
**13.710 páginas, 78 MB**, in-18 de 100 × 160 mm, corpo 7, duas colunas.
Por mês, e com os fólios a correr de um para o outro:

| Mês | Páginas | Fólios | Horas |
|---|---|---|---|
| Janeiro | 1.179 | 1–1.179 | 248 |
| Fevereiro | 1.065 | 1.180–2.244 | 224 |
| Março | 1.192 | 2.245–3.436 | 248 |
| Abril | 1.054 | 3.437–4.490 | 240 |
| Maio | 1.165 | 4.491–5.655 | 248 |
| Junho | 1.133 | 5.656–6.788 | 240 |
| Julho | 1.160 | 6.789–7.948 | 248 |
| Agosto | 1.166 | 7.949–9.114 | 248 |
| Setembro | 1.130 | 9.115–10.244 | 240 |
| Outubro | 1.161 | 10.245–11.405 | 248 |
| Novembro | 1.125 | 11.406–12.530 | 240 |
| Dezembro | 1.180 | 12.531–13.710 | 248 |

As horas encontradas são exactamente as compostas em todos os meses —
248 nos de 31 dias, 240 nos de 30, 224 em Fevereiro.

É o livro **por expandir** — ver 3.46 para o que a factorização lhe faz.

### 3.50 A sobreposição do carimbo tem de voltar a comprimir

**Medido:** `merge_page` descomprime os dois fluxos de conteúdo, junta-os
e escreve-os **em claro**. Um mês passava de 19,6 MB para 69,8, e o
volume inteiro dava **822 MB**.

`compress_identical_objects` não serve — as fontes não estão duplicadas
(seis objectos de fonte em duzentas páginas). O que serve é
`compress_content_streams` em cada página depois da sobreposição: o
volume passa de **822 para 78 MB**, e custa trinta segundos.


### 3.51 A factorização: 13.710 páginas passam a 3.265

Medido, composto e impresso — `breviarium-factorizado-2026-latina.pdf`,
**3.265 páginas, 18 MB**, contra as 13.710 do livro por expandir.

| Secção | Fólios | Páginas |
|---|---|---|
| Ordinarium, Psalterium, Hymni, Commune | 1–358 | 358 |
| Os 365 dias | 359–3.265 | 2.907 |

Das 6.471 peças distintas do ano, **1.115 são partilhadas** e ocupam 358
páginas. Verificado: **21.397 remissões, nenhuma sem fólio.**

Três regras, e a razão de cada uma:

| | |
|---|---|
| **Ordinário** | o que se diz todos os dias imprime-se uma vez e os dias **não o repetem nem o apontam** — nem sequer um ponteiro. Quem reza sabe-o. |
| **Salmos e hinos** | uma vez cada, e o dia diz `Psalmus 68(2-13) 42`. |
| **Antífonas** | **ficam no dia.** É a antífona que dá cara ao ofício; trocá-la por um ponteiro deixava a página cega, e são só 1,2 milhões de caracteres em vinte e seis. |

Não se remete peça a peça em tudo: 74.000 ponteiros a quarenta e cinco
caracteres seriam 3,3 milhões de caracteres — mais do que se poupa em
metade dos géneros.

**O chão desta conta são as lições de Matinas:** 1,93 milhões de
caracteres que se repetem **1,0 vezes**. Não há como as encolher, e são
dois quintos do livro final. É por isso que um breviário completo com
Matinas é grosso — e é só por isso.

Dois defeitos apanhados por olhar, e corrigidos:

- Uma peça que era só um `_` — separador de estrofe — foi parar às
  partilhadas, não imprimia nada, e **seis remissões apontavam para o
  fólio 000**. Agora uma peça sem letras nunca é partilhada, e sem fólio
  a peça sai por extenso: vale mais repetir do que mandar o leitor a uma
  página que não existe.
- O cabeçalho corrido partia-se em três linhas nos nomes compridos e caía
  por cima do texto. Passa a uma linha, cortada com reticências.

### 3.52 O navegador que imprime escolhe-se por prova, não por nome

**Medido, à terceira vez que falhou:** o Chrome, quando o utilizador tem
uma janela aberta, entrega-lhe o pedido — *«Abrindo em uma sessão de
navegador existente»* — e sai **sem escrever nada e sem erro**, mesmo com
um `--user-data-dir` só nosso. E o Edge não mora onde se espera: está em
`Microsoft\EdgeCore\<versão>\msedge.exe`, com o número da versão no
caminho.

Por isso `livro.py` não escolhe pelo nome: **imprime uma página de prova
e fica com o primeiro que a produzir**; e se o que servia deixar de
servir a meio, risca-o e passa ao seguinte.

**Fica em aberto:** com a janela do utilizador aberta, pode não haver
navegador nenhum disponível. É a razão de peso para instalar a
biblioteca GTK e passar ao WeasyPrint, que não depende de navegador
nenhum.


### 3.53 O WeasyPrint entrou, e três passagens passam a uma

**Instalado em 6 de Agosto**, com autorização sua. A biblioteca GTK que
lhe faltava no Windows está numa **pasta própria** —
`%LOCALAPPDATA%\gtk3-runtime` —, não no sistema: desfaz-se apagando a
pasta. Nem o PATH nem nada partilhado foi tocado. O caminho passa-se pela
variável `WEASYPRINT_DLL_DIRECTORIES`, e `pdf.py` procura-o sozinho.

**O que ele resolve, e o navegador não sabia fazer:** as caixas de margem
do `@page`.

| | |
|---|---|
| Cabeçalho corrido | `@top-center { content: string(cabeca) }` |
| Fólio | `@bottom-center { content: counter(page) }` |
| Remissão | `content: target-counter(attr(href), page)` |

A remissão deixa de ser um número calculado por nós e escrito no texto:
passa a ser uma **ligação** para a peça, e o compositor põe lá a página
onde ela caiu. Some tudo o que se tinha inventado para contornar a falta:
a folha de carimbo, a sobreposição com o `pypdf`, as duas passagens, e as
marcas invisíveis em cada peça e em cada barra de hora.

**Medido — `BREVIARIUM-2026-latina.pdf`:**

| | |
|---|---|
| Páginas | **2.991** |
| Tamanho | 15 MB |
| Páginas sem cabeçalho | **0** |
| Ligações internas | **48.032**, nenhuma quebrada |
| Destinos nomeados | 1.115 — as peças partilhadas todas |

Contra as 13.710 do livro por expandir, e contra as 3.265 da mesma
factorização feita pelo navegador — as 274 páginas de diferença são o
desperdício que a manha do carimbo obrigava.

**Cautela para quem retomar:** a verificação das ligações tem de seguir os
**destinos nomeados**. Com poucas ligações o WeasyPrint escreve a
referência directa à página; com quarenta e oito mil escreve um nome, e
um teste que só leia `dest[0]` dá as 48.032 por quebradas — foi o que me
aconteceu à primeira.


---

# 4. Perguntas em aberto, para quando houver ocasião

Não bloqueiam nada. Trazer juntas, no fim de uma etapa.

1. **Juízo litúrgico, para o Padre:** o breviário impresso de 1962 escreve
   `Jesus`; o Divinum Officium, nas rubricas de 1960, escreve `Iesus`. Está a
   seguir o Divinum Officium (decisão 2.12), mas as editoras da época
   divergiram. Confirmar com o Padre antes de imprimir.
2. **Abreviações bíblicas:** a coluna portuguesa mostra `1 Pet 5:8-9`, à
   latina. Em português seria `1 Pe 5,8-9`. Faz parte do glossário de ~70
   termos da seção 11 do prompt, ainda por fazer.
3. **Emparelhamento linha a linha** em vez de peça a peça — ver 3.7.

*A quarta — a flexa — foi respondida no mesmo dia: ver 2.17.*

---

# 5. O que está feito, medido

| | |
|---|---|
| Repositório clonado e corrigido | por um comando, idempotente: `python gerador/preparar.py` |
| Motor de condicionais | portado e conferido: **15.050 comparações, zero divergências** |
| Resolvedor de `@` | **5.379 → 30** ponteiros; os 30 estão quebrados na fonte |
| Resolvedor de `$` | **2.283 → 0** fórmulas por expandir |
| Funções `&` | **todas portadas**, incluindo `&psalm` e `&special` |
| Conferência total do resolvedor | **30.674 seções**, latim e português, zero divergências |
| Conferência da função `&psalm` | **684 casos**, zero divergências |
| Conferência do extractor do Comum | **660 casos**, zero divergências |
| Matriz de regras | 170 células, 23 dependentes do tempo litúrgico, conferida nos 365 dias |
| Página composta | Completas e Sexta, 99,8 × 160,2 mm, bilíngue e latina |
| Ordo de 2026 | colhido: 2.920 linhas, 20 colunas, zero erros |

## AS OITO HORAS, O ANO INTEIRO

Conferidas contra o gerador oficial do próprio Divinum Officium, dia a
dia, linha a linha:

| Hora | Dias iguais | Ponteiros sobreviventes | Dias que não geraram |
|---|---|---|---|
| **Matinas** | **365 / 365** | 0 | 0 |
| **Laudes** | **365 / 365** | 0 | 0 |
| **Prima** | **365 / 365** | 0 | 0 |
| **Terça** | **365 / 365** | 0 | 0 |
| **Sexta** | **365 / 365** | 0 | 0 |
| **Noa** | **365 / 365** | 0 | 0 |
| **Vésperas** | **365 / 365** | 0 | 0 |
| **Completas** | **365 / 365** | 0 | 0 |

**2.920 de 2.920 dias-hora.** Nem uma palavra de diferença, e nenhum
ponteiro de remissão sobreviveu a página nenhuma.

A varredura corre com um comando por hora:

    python gerador/varrer.py --hora Matutinum

e junta numa passagem as verificações 1, 2, 3, 6 e 7 do prompt: nenhum
ponteiro sobrevive, nenhum dado de controlo escapa, todos os dias geram,
os 365 dias estão cobertos, e o texto é o mesmo do gerador oficial.

## O que Matinas trouxe

É a hora que muda de tamanho conforme o dia:

    festa de I ou II classe   três nocturnos, nove salmos, nove lições
    tudo o resto              um nocturno, nove salmos, três lições

Quem decide é `gettype1960`, e dessa decisão sai tudo: quantas lições se
dizem, para onde a terceira se desvia — para a homilia num domingo, para
a legenda do santo numa festa — e se há Te Deum no fim.

O invitatório não é um salmo com antífona antes e depois: a antífona
repete-se entre cada estrofe, e a segunda metade alterna com a inteira.

## O que falta, por ordem

As oito horas estão feitas. O que resta já não é liturgia — é livro.

1. **A prova impressa.** As 365 páginas saem; falta olhá-las em papel e
   mandar mudar o que for para mudar. Todas as escolhas de aparência são
   parâmetro e mudam-se em minutos (decisão 2.18).
2. **Paginação e remissões.** O número de página só se sabe depois de
   paginar; as remissões (`%Laudes%` e as outras) esperam por ele.
3. **O glossário de ~70 termos** da secção 11 do prompt, e as abreviações
   bíblicas em português.
4. **As lacunas de português**, registadas peça a peça: onde falta, sai o
   latim, sem marca (decisão do prompt).

O instrumento do marco está feito: `python gerador/varrer.py --hora X`
gera o ano inteiro, confere linha a linha contra o gerador oficial e
audita os ponteiros sobreviventes numa passagem só.

## Os programas, e o que cada um faz

| | |
|---|---|
| `preparar.py` | clona, corrige o `Date.pm`, alinha o gerador em lote |
| `resolver.py` | segue as remissões `@`, `$`, `vide` |
| `funcoes.py` | as funções `&`, incluindo o salmo |
| `comum.py` | de que Comum vem o ofício |
| `proprio.py` | de onde vem cada peça: do próprio ou do Comum |
| `salmodia.py` | que antífona e que salmos, em cada dia da semana |
| `compor.py` / `compor_sexta.py` | a página |
| `imprimir.py` | a página em PDF |
| `conferir_*.py` | os confrontos contra o Perl original |
| `comparar_texto.py` | a verificação 7: o nosso texto contra o deles |
