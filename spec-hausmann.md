# A especificação do Hausmann

Levantado lendo `hausmann-1961.pdf` inteiro — *Learning the New Breviary*,
Hausmann, 1961. 62 páginas de PDF em paisagem, duas páginas de livro em cada;
o livro tem 117 páginas numeradas mais o índice.

O PDF é escaneado e a camada de OCR é inutilizável. Foi lido como imagem.
Mapeamento: **página N do PDF traz as páginas 2N-6 (esquerda) e 2N-5 (direita)
do livro**. Conferido em três pontos independentes.

Este arquivo registra o que o livro especifica. Não substitui o livro: é o
resumo do que interessa ao gerador.

---

## 1. As cinco classes de Ofício

Toda a máquina de resolução gira em torno disto. Um dia do ano cai
necessariamente numa destas cinco classes, e a classe determina de onde vem
cada peça.

| Classe | Quando |
|---|---|
| **Festivum** | festa de I ou II classe |
| **Semifestivum** | festa de III classe com material próprio abundante |
| **Ordinarium** | festa de III classe com pouco próprio |
| **Dominicale** | domingo |
| **Feriale** | féria de IV classe |

O Ordo diz, para cada dia, qual é. As abreviações aparecem como
`Off. festivum`, `Off. dominicale`, `Off. ordinarium`, `Off. feriale`.

---

## 2. As seis fontes de onde uma peça pode vir

| Sigla usada aqui | Seção do breviário |
|---|---|
| **Ord** | Ordinarium — o esqueleto invariável |
| **PS** | Proprium Sanctorum — o próprio do santo, por data fixa |
| **CS** | Commune Sanctorum — o comum, por categoria de santo |
| **PdT** | Proprium de Tempore — o próprio do tempo |
| **PsD** | Psalterium, do domingo |
| **PsF** | Psalterium, da féria do dia |

**Regra de precedência entre PS e CS:** onde o Proprium Sanctorum dá a peça,
usa-se ela; onde não dá, cai-se no Commune da categoria correspondente. Nunca
o contrário. Isto vale peça a peça, não ofício a ofício — é normal um mesmo
nocturno ter antífonas do Próprio e salmos do Comum.

---

## 3. Onde cada peça é encontrada

Cada capítulo da Parte I traz uma seção *Where the various parts are found*.
O que segue é a regra, hora por hora.

### Matinas de três nocturnos

1. Introdução — **Ord**, exceto o **invitatório e seu hino**, que vêm do
   **PS**, ou do **CS** se o Próprio não der
2. As três antífonas e os três salmos de cada nocturno, mais o versículo e
   resposta ao fim de cada terno — **PS**, senão **CS**
3. Absolvição de cada terno de lições e as bênçãos, uma por lição — **Ord**
4. As lições de cada nocturno, com o responsório e versículo de cada uma —
   **PS**
5. Te Deum, que substitui o responsório da nona lição — **Ord**
6. Conclusão, quando usada — **Ord**, exceto a oração, que vem do **PS**

### Matinas de um nocturno

Mesma lógica, com um nocturno só. No Ofício ordinário e no ferial as lições
são as **Scripturae occurrentis**, do Proprium de Tempore.

### As demais horas

Laudes, Prima, Terça, Sexta, Noa, Vésperas e Completas seguem o mesmo padrão:
esqueleto do Ordinarium, salmos do Psalterium ou do Comum conforme a classe,
antífonas e capítulo e oração do Próprio.

**A tabela completa, célula por célula, está no capítulo IX (páginas 55 a 59
do livro).** É a forma matricial da mesma regra: linhas são as peças, colunas
são as cinco classes. **Transcrever essa matriz para um arquivo de dados é a
primeira tarefa do resolvedor de remissões** — e cada célula deve ser conferida
contra a página, não deduzida.

### Duas advertências do próprio autor

- **Nota 1:** as peças são citadas da seção onde *propriamente* pertencem. Uma
  edição impressa pode reimprimir a mesma peça em lugar mais cômodo — muitos
  breviários reimprimem quase todo o Ordinarium dentro do Psalterium. Isso é
  decisão de diagramação, não de conteúdo.
- **Nota 2:** as exceções por tempo litúrgico estão todas reunidas no
  capítulo XI, não espalhadas pelos capítulos das horas.

---

## 4. Convenções tipográficas — importam para a composição

- **Asterisco** no meio do salmo e da antífona: marca a divisão do versículo.
- **Adaga (†)**: marca onde a antífona termina quando é dita só até ali.
- **Palavras entre parênteses** no início de um salmo: são omitidas na
  recitação, porque repetem a antífona que acabou de ser dita. O gerador
  precisa reproduzir esse parêntese, não apagá-lo.
- `R.br.` é o responsório breve; distingue-se do responsório de lição.

---

## 5. Mudanças por tempo litúrgico — capítulo XI

Os casos especiais, que sem esta fonte se descobrem um a um. Cada um destes é
uma exceção a codificar:

- Advento, e os dias 17 a 23 de dezembro
- Natal e sua oitava
- Septuagésima
- Quaresma
- Tempo da Paixão
- **Os três últimos dias da Semana Santa** — o caso mais divergente:
  - Matinas: toda a introdução é omitida; começa direto pelas antífonas e
    salmos, que são próprios e estão no Proprium de Tempore
  - O **Gloria Patri é omitido ao fim dos salmos em todas as horas**
  - Absolvição, bênçãos e o *Tu autem* são omitidos
  - Laudes não tem introdução; capítulo e hino omitidos, versículo mantido;
    após o Benedictus, conclusão especial com *Christus factus est*, Pater
    noster e a oração *Réspice*, sem *Orémus*
  - Prima, Terça, Sexta e Noa: sem introdução, salmos de domingo **sem
    antífona**
  - Completas de Sábado Santo: sem antífona nos salmos; *Christus factus est*
    é omitido da conclusão
- **Páscoa e sua oitava**: hinos, capítulos e responsórios breves omitidos em
  todas as horas, substituídos pela antífona *Haec dies*; Matinas com três
  salmos e três lições
- **Tempo pascal**: acrescenta-se *Alleluia* ao invitatório, às antífonas e a
  todos os versículos e respostas, exceto ao versículo do responsório das
  lições de Matinas e aos que o Ordinarium já imprime sem ele; duplo
  *Alleluia* nos responsórios breves; as antífonas do Psalterium não são
  usadas, sendo substituídas por tríplice *Alleluia*; Te Deum dito mesmo nos
  ofícios feriais; Comum especial para Apóstolos e Evangelistas, e outro para
  um ou muitos Mártires
- **Pentecostes e sua oitava**: Matinas com três salmos e três lições; o mesmo
  ofício todo dia da oitava, mudando só as lições; sem comemorações

---

## 6. Os três casos de teste — Parte II

O livro desdobra três ofícios inteiros, peça por peça, com a origem de cada
uma marcada. **São gabarito independente do Divinum Officium** — a verificação
número 10 do prompt.

| Capítulo | Classe | Dia | Páginas do livro | Páginas do PDF |
|---|---|---|---|---|
| XIII | **Festivum** | Assunção de Nossa Senhora, 15 de agosto (com I Vésperas e Completas em 14 de agosto) | 79 a 93 | 42 a 49 |
| XIV | **Dominicale** | Domingo XVI depois de Pentecostes, 10 de setembro de 1961 | 94 a 105 | 50 a 55 |
| XV | **Ordinarium** | Santo André Avelino, Confessor, III classe, sexta-feira, 10 de novembro de 1961 | 106 a 115 | 56 a 61 |

O Festivum é o mais completo: traz I Vésperas, Completas, Matinas com os três
nocturnos, Laudes, Prima, Terça, Sexta, Noa, II Vésperas e Completas.

Nos três arquivos correspondentes do Divinum Officium:
`Sancti/08-15`, `Tempora/Pent16-0`, `Sancti/11-10`.

**Como usar:** gerar o dia pelo nosso corpus e conferir peça a peça contra o
desdobramento do Hausmann — mesma peça, mesma ordem, mesma origem.

---

## 7. Como ler o Ordo — capítulo XII

O capítulo decodifica três linhas reais do Ordo Romano de 1961, do formato
comprimido para prosa. Serve à leitura do nosso Ordo de 2026.

Exemplo, 19 de fevereiro:

```
19. Viol. DOM. I QUADRAGESIMAE, De ea, I cl. — Off. dominicale
  + temp. Quadr. — Ad Mat. 9 ant. et 9 pss. de dom. cum versu
  Ipse liberavit (e 1 Nocturno), abs. Exaudi, ben. Ille nos,
  Divinum auxilium, Per evangelica dicta. — L.1 (cum suo R.)
  et 2 (= 2 et 3 cum 3 R.) de Scr. occ., 3 de homilia (= L 7
  cum 9 R.), sine Te Deum. ...
```

Quer dizer: cor violeta; Domingo I da Quaresma, I classe; ofício dominical do
tempo da Quaresma; o `+` na margem é dia de preceito; nas Matinas, 9 antífonas
e 9 salmos do domingo, com o versículo *Ipse liberavit* do primeiro nocturno;
absolvição *Exaudi*; bênçãos *Ille nos*, *Divinum auxilium*, *Per evangelica
dicta*; primeira lição com seu responsório e segunda lição — que é a antiga 2
combinada com a 3, levando o responsório da 3 — das Escrituras ocorrentes;
terceira lição da homilia, que é a antiga lição 7 com o responsório da 9; sem
Te Deum.

Marcas de margem: `+` dia de preceito; `V` missas votivas de IV classe
permitidas; `D` missas cotidianas de defuntos permitidas; `O.C.` *omittitur
collecta*, a oração imperada é omitida.

---

## 8. O que fazer com isto

1. **Transcrever a matriz do capítulo IX** para um arquivo de dados, célula por
   célula, conferindo contra a página. É a espinha do resolvedor.
2. **Transcrever os três ofícios da Parte II** para arquivos de teste, peça a
   peça com a origem marcada.
3. Codificar as exceções do capítulo XI como regras por tempo litúrgico.
4. Só então escrever o resolvedor, e testá-lo contra 2 antes de confiar nele.
