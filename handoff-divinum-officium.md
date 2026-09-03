# Divinum Officium — o que o site é, o que ele tem, e como usar

Documento de referência para o projeto do Breviário do Padre Rosenei.
Levantado lendo o site e o repositório por dentro, não de memória.

---

## 1. O que é o projeto

Site que reproduz o Breviário Romano e o Missal tradicionais em várias
versões históricas das rubricas. Criado por Laszlo Kiss, falecido em 2011,
hoje mantido por uma equipe com um sacerdote diocesano e desenvolvedores.

- Site: `https://www.divinumofficium.com`
- Código: `https://github.com/DivinumOfficium/divinum-officium`
- Licença MIT — pode copiar, publicar, distribuir e vender, bastando que o
  aviso de licença acompanhe. Os textos latinos são antigos e de domínio
  público.

Aviso importante: os downloads independentes antigos morreram junto com o
fundador em 2011 e nunca foram repostos. **Não existe um breviário pronto
para baixar.** O que existe é o texto-fonte e um site que o monta dia a dia.

---

## 2. As três seções do site

| Seção | O que é |
|---|---|
| **Horas** | O Ofício Divino — as oito horas canônicas |
| **Missa** | O Missal Romano |
| **Kalendarium** | O calendário litúrgico, mês a mês ou o ano inteiro |

---

## 3. As versões de rubricas disponíveis

Definidas em `web/www/Tabulae/data.txt`. São onze:

| Versão | Chave |
|---|---|
| Tridentina 1570 | `Tridentine - 1570` |
| Tridentina 1888 | `Tridentine - 1888` |
| Divino Afflatu 1939 | `Divino Afflatu - 1939` |
| Divino Afflatu 1954 | `Divino Afflatu - 1954` |
| Reduzidas 1955 | `Reduced - 1955` |
| **Rubricas de 1960** | **`Rubrics 1960 - 1960`** |
| Rubricas 1960, EUA 2020 | `Rubrics 1960 - 2020 USA` |
| Monástica Tridentina 1617 | `Monastic Tridentinum 1617` |
| Monástica Divino 1930 | `Monastic Divino 1930` |
| Monástica 1963 | `Monastic - 1963` |
| Dominicana 1962 | `Ordo Praedicatorum - 1962` |

**A Liturgia das Horas de 1970 não está aqui.** O projeto cobre apenas as
formas tradicionais. Nosso projeto usa **Rubricas de 1960**.

---

## 4. Como o texto está organizado no disco

Esta é a parte que mais importa para nós. Sob `web/www/horas/<Idioma>/`:

| Pasta | Conteúdo |
|---|---|
| `Ordinarium` | O esqueleto invariável de cada hora |
| `Psalterium` | Os 150 salmos distribuídos pela semana, com antífonas e hinos feriais |
| `Tempora` | Próprio do Tempo — Advento, Natal, Quaresma, Páscoa, domingos depois de Pentecostes |
| `Sancti` | Próprio dos Santos, por data fixa |
| `Commune` | Comum dos Santos — ofícios genéricos por categoria |
| `Appendix` | Peças avulsas |
| `Martyrologium` | O martirológio, leitura de Prima |

Há ainda variantes `...Cist`, `...M`, `...OP` para cistercienses,
monásticos e dominicanos. **Não usar** — são outras famílias litúrgicas.

**Ponto decisivo:** os arquivos são organizados por *posição litúrgica*, não
por data. `Adv1-0.txt` é o Domingo I do Advento, não uma data. É por isso
que o mesmo material serve qualquer ano.

### Formato dos arquivos-fonte

Texto simples, com seções entre colchetes:

```
[Ant Vespera]
[Capitulum Vespera 1]
[Hymnus Vespera]
[Lectio1]
[Responsory1]
[Oratio]
```

Três tipos de linha convivem no mesmo arquivo:

- **Texto litúrgico** — o que se imprime
- **Controle** — seções `[Officium]`, `[Rank]`, `[Rule]`, `[Name]`, e linhas
  com `;;`. É dado interno do programa. **Nunca sai impresso.**
- **Remissões** — linhas começando com `@`, `!`, `&` ou `$`, que apontam
  para outro lugar do corpus

Exemplos reais de remissão:

```
@Psalterium/Special/Major Special:Adv Versum 3
@:Ant Laudes
!Isa 1:1-3
&Gloria
$Qui vivis
```

Separar essas três coisas com segurança é o coração técnico do projeto.

---

## 5. Cobertura da tradução portuguesa — medido

Comparando o volume de texto em cada parte:

| Parte | Latim | Português | Cobertura |
|---|---|---|---|
| Psalterium | 511 KB | 399 KB | **78%** |
| Commune | 431 KB | 102 KB | **24%** |
| Tempora | 1.745 KB | 2,9 KB | **0,2%** |
| Sancti | 2.662 KB | 67 KB | **3%** |

Dentro do Saltério, o detalhe:

| | Latim | Português | |
|---|---|---|---|
| Psalmorum (os salmos) | 287 KB | 325 KB | completo |
| Psalmi | 57 KB | 25 KB | 44% |
| Special (antífonas próprias) | 119 KB | 27 KB | 23% |
| Common | 30 KB | 17 KB | 58% |
| Doxologies, Benedictions, Invitatorium, Chant | — | 0 | **nada** |

**Hinos:** 205 arquivos latinos contêm seção de hino. Em português, 5.
Praticamente nenhum hino está traduzido — é o que se vê ao abrir qualquer
hora no site com idioma português.

**Conclusão:** os salmos estão traduzidos. Quase todo o resto não. O
breviário completo em português **não existe** e depende de trabalho de
tradução medido em anos, não de programação.

---

## 6. A opção "Fallback language" — a explicação do inglês

No menu de configuração do site (`Divinum Officium setup`) existe o campo
**Fallback language**, cujo padrão é o inglês.

O comportamento é este: quando falta a tradução de um trecho no idioma
escolhido, o site preenche o buraco com o idioma de reserva. Com o padrão de
fábrica, isso significa **texto inglês aparecendo no meio do ofício
português** — sem aviso nenhum.

Mudando o fallback para Português, o inglês desaparece; e onde o português
não existe, sobra o latim. **O latim que continua aparecendo é a medida
honesta do que falta traduzir.**

Isso importa para nós de duas formas:

1. Explica por que uma medição ingênua superestima a cobertura portuguesa.
   Contar "linhas diferentes do latim" conta o inglês como se fosse tradução.
2. No nosso gerador, o comportamento correto é **nunca cair para o inglês**.
   Onde falta português, ou se imprime o latim, ou se marca a lacuna.

Outras opções do mesmo menu que interessam:

| Opção | Efeito |
|---|---|
| `Don't use fancy characters` | Evita ℟ ℣ ✠, que nem toda fonte de impressão tem |
| `Hide verse numbers` | Tira a numeração dos versículos dos salmos |
| `Hide flexa mark` | Tira a marca de flexa do canto |
| `Compare in single cell` | Junta os dois idiomas numa coluna só |
| `Priest` | Inclui as partes reservadas ao sacerdote |
| `Pius XII Psalter` | Troca o saltério pelo de Pio XII — **não usar** |
| `Use antique hymns` | Hinos na forma anterior à revisão de Urbano VIII |

---

## 7. O Kalendarium e o Ordo — como o ano é resolvido

O repositório traz a maquinaria completa de calendário:

- `web/cgi-bin/horas/kalendar.pl` — o script do calendário
- `web/www/Tabulae/Kalendaria/1960.txt` — as regras do calendário de 1960
- `web/www/Tabulae/Tempora/`, `Transfer/`, `Stransfer/` — tabelas de tempo e
  de transferência de festas

Clicando **Totus** na página do calendário, o site calcula **o ano inteiro de
uma vez** — o parâmetro é `kmonth=14`, um valor sentinela que significa "ano
completo". O cálculo dos 365 dias é pesado, então o projeto mantém um cache
pré-gerado por versão de rubrica e por ano, com nomes como
`2026-rubrics-1960-1960.html`, atualizado toda madrugada.

**Ou seja: o Ordo de 2026 nas rubricas de 1960 já existe pronto no site.**
Não precisamos calcular nada — basta pedir o ano completo e ficar com a
tabela.

---

## 8. A biblioteca de rubricas — material para o livro

A página `Help/rubrics.html` é um acervo de documentos que serve
diretamente ao material introdutório do nosso breviário:

**Rubricas de 1960:**
- Rubricarum Instructum
- Rubricas Gerais
- Rubricas do Breviarium Romanum
- Tábuas de festas (`Tables 1960.txt`)
- Calendário Romano de 1960 em PDF
- Variationes in Breviario et Missali Romano
- De Anno et Eius Partibus — o tratado do cômputo do ano

**Rubricas tridentinas e Divino Afflatu:** trinta e sete capítulos em
arquivos separados (`R01.txt` a `R37.txt`), cobrindo ofício duplo,
semiduplo, simples, domingos, férias, vigílias, oitavas, comemorações,
translação de festas, concorrência, e depois cada hora e cada peça —
matinas, laudes, prima, horas menores, vésperas, completas, invitatório,
hinos, antífonas, salmos, cânticos, versículos, bênçãos, lições,
responsórios, capítulos, orações, Te Deum, preces, sufrágios, antífonas
finais de Nossa Senhora.

Mais nove arquivos de adições Divino Afflatu (`N1.txt` a `N9.txt`) e as
`Tabellae.txt` — as tábuas de ocorrência e concorrência.

**Manuais didáticos em PDF:**
- *Learning The New Breviary*, Hausmann, 1961 — manual das rubricas de 1960
- *A Brief Introduction to the Divine Office*, Ayd, 1918
- *The Divine Office*, Quigley, 1920 — estudo histórico

Esses três últimos são leitura para quem for definir o conteúdo do livro.

---

## 9. Como rodar localmente

O site é software web em Perl. Três caminhos, do mais fácil ao mais
trabalhoso:

**Docker** — recomendado pelo próprio projeto:
```
docker run --rm -p 8080:80 ghcr.io/divinumofficium/divinum-officium:master
```
Depois abrir `http://localhost:8080`.

**Python, sem Docker:**
```
cd divinum-officium/web
python -m http.server --cgi
```
Abrir `http://0.0.0.0:8000`. Exige Perl e o módulo CGI instalados.

**Apache** — exige configurar execução de CGI em `web/cgi-bin/`.

Só a pasta `/web` deve ser servida. As demais, não.

---

## 10. Um defeito conhecido, com a correção

O gerador de arquivos em lote (`standalone/tools/epubgen2`) **está quebrado**.
Chama duas funções de data que foram removidas de
`web/cgi-bin/DivinumOfficium/Date.pm` e nunca reescritas:

```
Undefined subroutine &DivinumOfficium::Date::date_to_days
```

Correção testada — inserir em `Date.pm`, antes de `sub getweek {`:

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

O bug não afeta a navegação do site, só a geração em lote — foi por isso que
passou despercebido. Vale mandar a correção ao projeto como pull request.

O projeto recomenda `git pull` periódico, o que pode sobrescrever a
correção. Nosso script deve verificar e reaplicar.

---

## 11. Resumo do que serve ao projeto

| Precisamos de | Está onde |
|---|---|
| Texto do ofício, latim | `web/www/horas/Latin/` |
| Texto do ofício, português | `web/www/horas/Portugues/` — incompleto |
| Regras do ano de 2026 | Ordo Totus do site, já em cache |
| Rubricas para o material introdutório | `Help/Rubrics/` |
| Calendário de 1960 | `Help/Rubrics/1960calendarium.pdf` |
| Tábuas de precedência | `Help/Rubrics/Tabellae.txt` |

O que **não** existe e teremos de fazer: a composição tipográfica, a
resolução das remissões, e a tradução portuguesa que falta.
