# Breviário Romano de 1960 — prompt de entrada para o Claude Code

Pasta do projeto: `C:\Users\fotog\Desktop\BREVIARIO`

---

## 0. Como quero trabalhar

**Esta seção foi substituída em 4 de agosto de 2026. Ver o Apêndice A, no
fim deste arquivo. O texto original fica abaixo, riscado, para memória.**

~~Mostre cada etapa antes de seguir para a próxima. Não construa tudo e me
entregue no fim. Termine uma etapa, mostre o resultado, espere eu dizer se
está bom.~~

~~Pergunte quando houver escolha real. Não escolha sozinho e me avise
depois.~~

O que continua valendo desta seção:

- **Explique em linguagem simples** as decisões e os custos antes de
  tomá-las. Se ficar técnico demais, eu peço para simplificar.
- **Não reconstrua do zero nada que já funcione.** Corrija, adapte, integre.
- **Não invente número.** Se disser "cerca de X páginas", meça antes. Vários
  erros graves neste projeto vieram de estimativa não verificada (seção 14).
- Textos e relatórios **em português com acento**. Caminhos de disco **sem
  acento**. **Nenhum emoji.**

---

## 1. O que é e para quem

Um instituto católico fundado pelo Padre Rosenei preserva livros esgotados e
retoma métodos tradicionais de impressão. O objetivo é produzir uma **edição
impressa do Breviário Romano nas rubricas de 1960**, para o Padre rezar.

A editora tem prensas modernas, capazes de impressão em duas cores, e há um
encadernador artesão experiente. Papel, lombada e fitas não são obstáculo.

**Não é a Liturgia das Horas de 1970.** É o Breviário Romano tradicional:
saltério de uma semana, com Prima, Matinas com nocturnos e nove lições,
calendário de 1960. São livros diferentes — saltério, calendário, hinos e
leituras não coincidem. Nunca misture material de um com o outro.

---

## 2. As duas edições

**Latina** — inteiramente em latim. Cabeçalhos, calendário, rótulos de peça,
sumário, rubricas do corpo, material introdutório: tudo em latim, como no
original de 1960. Nenhum português em lugar nenhum.

**Bilíngue** — latim e português. Onde não houver tradução portuguesa,
imprime-se o latim, **sem marca especial** (latim se reconhece sozinho; marca
seria redundante). Em português: toda a estrutura do livro (seção 11), as
rubricas do corpo, e o Código de Rubricas traduzido.

As duas **não diferem só numa coluna** — diferem em cabeçalho, calendário,
sumário e índice. São duas composições distintas saindo do mesmo corpus.

**Volume único primeiro, nas duas edições.** Os quatro tomos por estação vêm
depois e devem ser um **parâmetro**, não um projeto novo.

---

## 3. As fontes

### Repositório do texto

`github.com/DivinumOfficium/divinum-officium` — licença MIT. Pode copiar,
publicar, distribuir e vender, bastando que o aviso de licença acompanhe. Os
textos latinos são antigos e de domínio público. **É a fonte de todo o texto
litúrgico.**

Leia o `handoff-divinum-officium.md`, que está nesta pasta: traz a estrutura do
site, as versões de rubricas, a organização dos arquivos e as armadilhas.

### Referências impressas, no Archive

- **`archive.org/details/breviarium-romanum-bilingual`** — breviário bilíngue de
  1962. **É a referência de diagramação mais importante**: mesma edição que
  estamos recriando, e bilíngue. Baixe primeiro o EPUB e o texto completo, que
  são leves e permitem analisar as remissões por dentro. O PDF só depois, e só
  um volume, para ver a página com os próprios olhos.
- `archive.org/details/breviarium-romanum-1942` — de onde a convenção de
  remissão já foi levantada (seção 8).
- Para comparação, se for útil: `breviariumromanu0002cath` (1.816 páginas),
  `breviariumromanu04turo` (1.348), `breviariumromanu21898cath` (1898).

### Os arquivos já reunidos na pasta

**Não baixe de novo o que já está aqui.**

| Nome | O que é | Para que serve |
|---|---|---|
| `hausmann-1961.pdf` | *Learning the New Breviary*, Hausmann, 1961 | **especificação das remissões e casos de teste** — seção 7 |
| `murphy-1960.pdf` | *The New Rubrics*, Murphy, 1960 | rubricas traduzidas e comentadas; conferência do Ordo |
| `bilingue-1962.pdf` e `.txt` | breviário bilíngue latim-inglês, 759 pág., 10,8 × 17,8 cm | modelo de diagramação bilíngue em duas colunas paralelas |
| `br-1942-aestiva.epub` | Breviário de 1942, Pars Aestiva | convenção de remissão |
| `br-outro-tomo.epub` | outro tomo do Breviário Romano | confirma a convenção; remissão com localização interna |
| `comba-hinos-1963.pdf` | Comba, 1963 | apoio a quem for traduzir os hinos |

### Dois arquivos que NÃO devem ser usados

`000LH_Abrev.pdf` e `LDH-04.pdf` são **Liturgia das Horas**, a reforma de 1970.
Nada deles serve, **nem os salmos**, porque a distribuição é outra. Estão em
`NAO-USAR\`.

### Direitos

Divinum Officium: MIT, livre. Textos latinos: antigos, domínio público.

Hausmann, Murphy e Comba: **obras protegidas**. Servem integralmente para
consulta, estudo e como gabarito de teste — **não para reimprimir trechos**.

O Código de Rubricas em si é documento oficial da Igreja. Ver o método de
tradução na seção 11.

Antes de traduzir o Código, **procure se já existe tradução portuguesa
publicada** das rubricas de 1960, livre ou cedível.

---

## 4. Um defeito conhecido, com a correção

O gerador em lote do Divinum Officium **está quebrado**. Chama duas funções
removidas de `web/cgi-bin/DivinumOfficium/Date.pm` e nunca reescritas:

```
Undefined subroutine &DivinumOfficium::Date::date_to_days
```

Inserir em `Date.pm`, antes de `sub getweek {`:

```perl
sub date_to_days {
  my ($day, $mon, $year) = @_;
  return int(timegm(0, 0, 12, $day, $mon, $year) / 86400);
}

sub days_to_date {
  my $days = shift;
  return gmtime($days * 86400 + 43200);
}
```

`Time::Local` já está importado no topo do arquivo.

O projeto recomenda `git pull` periódico, que pode sobrescrever a
correção: **verifique e reaplique automaticamente**.

Vale abrir um pull request com essa correção. Deixe para o fim.

---

## 5. A arquitetura, e por que ela é assim

### Componha a partir dos arquivos-fonte, não do Perl

Os arquivos em `web/www/horas/<Idioma>/` são organizados por **posição
litúrgica**, não por data: `Adv1-0.txt` é o Domingo I do Advento, não uma data.
É isso que faz o livro servir qualquer ano. O Perl aplica a data; nós não
queremos isso.

### O breviário impresso é perpétuo

Serve 2026, 2050, sem mudar uma vírgula. O que muda todo ano é só **qual peça
combinar em cada dia** — e isso vai no **Ordo**, caderno fino anual, não no
livro (seção 12).

### As partes do livro, nesta ordem

1. **Material introdutório** — rosto, Kalendarium, tábuas de precedência,
   Código de Rubricas
2. **Ordinarium** — o esqueleto invariável de cada hora
3. **Psalterium** — os 150 salmos distribuídos de domingo a sábado
4. **Proprium de Tempore** — Advento a Pentecostes
5. **Proprium Sanctorum** — por data fixa, 1º de janeiro a 31 de dezembro
6. **Commune Sanctorum** — ofícios genéricos por categoria
7. **Ofício Parvo de Nossa Senhora** e **Ofício de Defuntos**
8. **Apêndice** — salmos penitenciais, graduais, ladainhas, Itinerário,
   bênçãos da mesa. Estão em `Latin/Appendix/`

Não use as variantes `...Cist`, `...M`, `...OP` — são cisterciense, monástica e
dominicana, outras famílias litúrgicas.

No volume único, **as Matinas de nove lições entram junto**.

---

## 6. O corpus limpo — o entregável central

Antes de qualquer diagramação, extraia todo o breviário de 1960 para arquivos
estruturados e limpos, independentes do Perl e do site.

Cada peça identificada (antífona, salmo, hino, lição, oração, capítulo,
responsório, versículo, invitatório, comemoração), cada lacuna de tradução
marcada, sem código de controle, sem lixo.

**Por que vem primeiro:** o repositório muda e quebra — já vimos. Com o corpus,
gerar outro formato, outra rubrica ou outro idioma é trabalho de horas. E o
corpus com as lacunas marcadas **é a lista de trabalho do tradutor**.

### Três tipos de linha convivem nos arquivos-fonte

- **Texto litúrgico** — o que se imprime.
- **Controle** — seções `[Officium]`, `[Rank]`, `[Rule]`, `[Name]`, e qualquer
  linha contendo `;;`. **Nunca sai impresso.**
- **Remissões** — linhas começando com `@`, `!`, `&`, `$`, e a palavra `vide`.

---

## 7. O interpretador de remissões — o coração técnico

São cerca de **12.800 remissões** no corpus: 5.344 do tipo `@`, 3.453 `!`,
1.382 `$`, 1.264 `&`, 1.388 `vide`.

### Exemplo real — `Sancti/01-21.txt`, Santa Inês

```
[Rule]
vide C6-1;
9 lectiones
Psalm5 Vespera=116

[Ant Vespera]
@:Ant Laudes

[Oratio]
Omnípotens sempitérne Deus...
$Per Dominum
```

### Casos difíceis já identificados

- **Remissão com localização interna** — "no terceiro nocturno".
- **Remissão com exceção** — "tudo do Comum, exceto a segunda lição".
- **Substituição de salmo**, como o `Psalm5 Vespera=116`.
- **Remissão em cadeia** — um alvo que por sua vez remete a outro.

Se um ponteiro não resolver, a página sai com buraco ou, pior, **com texto
errado sem ninguém perceber**.

### O Hausmann é a especificação

`hausmann-1961.pdf` traz, em cada capítulo de hora, uma seção *Where the
various parts are found*. **É a regra de resolução das remissões, escrita em
prosa por quem sabia.**

A Parte II traz **três ofícios completos resolvidos** — festivo, dominical e
ordinário. São casos de teste prontos, **independentes do Divinum Officium**.

---

## 8. A convenção de remissão — copiada do de 1942

**Frase em latim nomeando a fonte, seguida do número de página entre
colchetes.** Nunca só o número, nunca só o nome.

Os números são pequenos porque **o Saltério, o Comum e o Ordinário têm
numeração própria, separada**, marcada com asterisco.

**Adote isso.** É o que permite gerar o volume único e os quatro tomos sem
recalcular as remissões dessas seções.

Existem remissões curtas sem número — *ut supra*, *ut infra*, *ut in
Psalterio*. O gerador decide isso sozinho, olhando a distância entre as
páginas depois de paginar.

### Nível de remissão

**Alto, como o de 1942.** Deixe o nível como **parâmetro**. Medido no dia de
Santa Inês: remissão alta dá ~4 páginas; expandindo o Comum, ~13; expandindo
também os salmos, ~28 — este último passa de 25 mil páginas no ano.

### Números de página nunca são texto fixo

São **calculados depois de paginar**, uma vez por edição. Serão cinco
conjuntos: volume único e quatro tomos.

---

## 9. A composição

- **Formato in-18°**, cerca de 10 × 16 cm.
- **Duas colunas**, medida de cerca de 40 caracteres.
- **Corpo 7 base**, e **toda a escala derivada dele por proporção**: rubricas
  ~6,5; numeração de versículo ~5,5; cabeçalho corrido ~6,5; títulos de seção
  ~7,5; título de festa ~9-10; capitulares ~15-20. **Nada de tamanhos fixos.**
- **Vermelho e preto.** Rubricas em vermelho.
- **Capitulares** abrindo cada salmo, hino e oração.
- **Cabeçalho corrido preciso** — "Feria secunda ad Primam".
- **Aberturas de parte** com folha de rosto própria.
- **Marcas de assinatura** no pé.
- **Margem interna com folga** para a costura.
- **Papel bíblia** — considerar na opacidade e no peso de tinta.
- **Fitas marcadoras**: prever 4 a 6.

### A disposição bilíngue

O português ocupa mais espaço que o latim.

**Como as duas línguas se dispõem é decisão a tomar olhando o bilíngue de
1961-62.** Aquele volume usa **duas colunas paralelas na mesma página**, latim
à esquerda, vernáculo à direita, em 10,8 × 17,8 cm.

Uma tentativa anterior montou cada bloco isolado e produziu buracos brancos
enormes. Não repita.

### Ferramenta

**WeasyPrint** para o PDF. **Não use conversão de EPUB pelo Calibre.**

Fonte serifada com acentuação completa e itálico decente. EB Garamond é
gratuita e adequada; TeX Gyre Pagella também serve.

---

## 10. Cobertura da tradução portuguesa — medido

| Parte | Latim | Português | |
|---|---|---|---|
| Psalterium | 511 KB | 399 KB | 78% |
| Commune | 431 KB | 102 KB | 24% |
| **Tempora** | **1.745 KB** | **2,9 KB** | **0,2%** |
| **Sancti** | **2.662 KB** | **67 KB** | **3%** |

**Hinos:** 205 arquivos latinos contêm hino, 5 em português.

**Rubricas do corpo:** 4.317 no latim, 280 em português.

**Meça de novo por conta própria e produza o relatório de lacunas.**

**Consequência:** o breviário latino completo é viável agora. O bilíngue sai
com as lacunas em latim e vai sendo preenchido.

---

## 11. O que traduzir na edição bilíngue

### O glossário de estrutura — cerca de 450 termos

| | Itens |
|---|---|
| Horas, seções, dias, tempos, classes de festa | ~60 |
| Rótulos de peça | ~30 |
| Fórmulas de título de santo | ~40 |
| Nomes próprios de santos | 246 |
| Abreviações de livros bíblicos | ~70 |
| Palavras de remissão | ~6 |

### As rubricas do corpo

**Prioridade alta** — rende mais que traduzir hinos.

### O Código de Rubricas

Traduzir por inteiro, **do latim original**, **com o Murphy e o Hausmann em
paralelo**. **Marque os trechos onde as leituras divergirem**: vão para revisão
do Padre.

### Nota de método sobre o inglês

Murphy e Hausmann servem para **entender**. **Mas a palavra vem do latim, não
do inglês.**

### Os hinos

**Ficam em latim**, mesmo na bilíngue.

### Índice de lacunas

Ao fim do volume bilíngue, lista do que ficou em latim, com página e peça.

---

## 12. O Ordo

O breviário é perpétuo; o Ordo é anual. Caderno fino que se joga fora em
dezembro — **não vai dentro do livro**.

O site calcula o ano inteiro (botão **Totus**, `kmonth=14`) e mantém cache
pré-gerado. **Não calcule nada — pegue pronto.**

Comece por 2026.

---

## 13. A armadilha do idioma de reserva

O site tem **Fallback language**, cujo padrão é o inglês: onde falta tradução,
preenche com o idioma de reserva **sem avisar**.

**O gerador nunca deve cair para o inglês.** Onde faltar português, imprime o
latim e registra a lacuna.

Outras opções que interessam: `Don't use fancy characters`, `Hide verse
numbers`. **Não** usar `Pius XII Psalter`.

---

## 14. Erros já cometidos — não repita

1. **Expandir tudo em cada dia.** 146 páginas para um único dia.
2. **Buracos brancos.** Cada trecho montado como bloco isolado.
3. **Dados de controle impressos.** Saiu `;;Semiduplex;;6.9`.
4. **Inglês na coluna portuguesa.**
5. **Medição feita só numa semana ferial** e generalizada para o ano.

E um erro de aritmética: **volume único ≈ 2.000 páginas; quatro volumes ≈
4.000 no total; dois volumes ≈ 2.300.**

---

## 15. Verificação — oito obrigatórias antes de imprimir

### Automáticos

1. **Nenhum ponteiro sobrevive** — nenhum `@`, `!`, `&`, `$`, `;;` ou `vide`.
2. **Nenhum dado de controle escapa.**
3. **Completude estrutural** nos 365 dias.
4. **Integridade das referências de página.**
5. **Órfãos** — material que nenhum dia referencia.
6. **Cobertura** — os 365 dias geram.

### Contra fontes externas

7. **Comparação com o site.**
8. **Volta pelo caminho do leitor** — seguir as remissões como um leitor.
9. **Cruzamento com o breviário de 1942.**
10. **Os três ofícios resolvidos do Hausmann.**
11. **Ordo contra Ordo publicado** para 2026.
12. **As duas edições têm texto idêntico**; só a paginação muda.

### Tipográficos

13. Nada transbordando, nenhuma página em branco não intencional, nenhuma
    viúva ou órfã, vermelho só em rubrica, nenhum título separado.

### Humanos

14. **Revisão litúrgica por amostra desenhada.**
15. **Prova de mesa** — cinquenta páginas soltas, dobradas, e rezar um dia.

**Obrigatórias antes de qualquer impressão: 1, 2, 3, 4, 7, 8, 10 e 14.**

---

## 16. Ambiente

- Windows. Python 3.11+, WeasyPrint, PyMuPDF, poppler-utils.
- Cache obrigatório.

---

## 17. Critérios de aceitação

1. Repositório clonado e corrigido por um comando.
2. O corpus limpo existe, com cada peça identificada e cada lacuna marcada.
3. As 12.800 remissões resolvem; nenhum ponteiro sobra no PDF.
4. Saltério, Comum e Ordinário têm numeração própria.
5. As oito verificações obrigatórias passam nos 365 dias.
6. Sai a edição latina em volume único, **inteiramente em latim**.
7. Sai a edição bilíngue em volume único.
8. Relatório de lacunas em português, com dia, hora, peça e página.
9. O Ordo de 2026 sai como caderno à parte.
10. Trocar formato, corpo, nível de remissão ou rubrica é **parâmetro**.
11. Os quatro tomos por estação saem do mesmo gerador.
12. Nada de controle e **nada em inglês** aparece em página impressa.

---

## 18. Investigações pendentes

- `breviarium.srubarovi.cz` — **já investigado, ver `decisoes.md`**.
- Um Ordo de 2026 publicado, para o teste 11.
- Edições impressas recentes do breviário de 1962.
- Tradução portuguesa publicada das rubricas de 1960.
- **Cobertura do Missal em português — nunca medida.**
- Se o instituto quiser reimprimir trechos do Comba, falar com os salesianos.

---

# APÊNDICE A — Como trabalhar

*Acrescentado em 4 de agosto de 2026, substituindo a seção 0.*

## Registro de decisões

**Mantenha `decisoes.md` e consulte antes de perguntar.**

**Antes de perguntar qualquer coisa, releia este arquivo e o `decisoes.md`.**
Se a resposta estiver em algum dos dois, siga e não pergunte. Se estiver
parcialmente, siga o que der e registre a lacuna em vez de parar.

**No começo de toda sessão nova** — depois de `/clear`, de reiniciar ou de
perder contexto — a primeira coisa a fazer é ler, nesta ordem:

1. `PROMPT-BREVIARIO.md` (este arquivo)
2. `decisoes.md`
3. `RETOMAR-APOS-REINICIO.md`

Antes de qualquer código, antes de qualquer pergunta.

**Atualize o `decisoes.md` no mesmo instante em que uma resposta é dada**, não
no fim da sessão.

## Quando decidir sozinho e quando parar

**Decida e siga, por padrão.** Escolha a mais simples que funcione, anote a
decisão e o motivo em `decisoes.md`, e continue.

**Pare só nestes três casos:**

1. Algo **caro de desfazer** — estrutura de dados do corpus, esquema de
   numeração de página, formato de arquivo.
2. Algo que **contradiga este arquivo**, ou que ele não cubra e mude o
   resultado impresso.
3. Algo que exija **juízo litúrgico** — se uma regra se aplica, se uma peça
   está no lugar certo. Isso é do Padre.

**Junte as dúvidas.** Se acumularem três ou quatro, traga todas de uma vez no
fim de uma etapa, em lista curta.

**Trabalhe em trechos longos.** Mostre resultado em marco concluído, não a
cada passo interno.

## Escopo: uma hora inteira, de ponta a ponta

**Em vez de construir camada por camada, leve uma hora só até o fim.**
Completas, que já saem, até o PDF diagramado, com remissão resolvida,
numeração e as verificações obrigatórias rodando.

Uma coisa inteira funcionando ensina mais do que quatro camadas meio prontas.
