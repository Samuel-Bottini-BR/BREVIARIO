# Conferência da matriz contra o site — resultado

Feita no site ao vivo (`divinumofficium.com`), pelo navegador. O acesso
automático por programa é bloqueado com 403; pelo navegador funciona.

O site faz uma coisa que os arquivos do repositório não fazem: **rotula a
origem de cada bloco do ofício**. É isso que o torna gabarito.

---

## Os três dias conferidos

| Dia | Classe | Hora | Por que este |
|---|---|---|---|
| 10 nov 1961, S. André Avelino | III classe | Terça | é o ofício-modelo do capítulo XV, e a hora da célula suspeita |
| 10 set 1961, Domingo XVI depois de Pentecostes | II classe | Terça | é o ofício-modelo do capítulo XIV |
| 15 ago 1961, Assunção | I classe | Completas | é o ofício-modelo do capítulo XIII, e a única hora que já geramos |

---

## ⚠A — resolvido: erro de impressão no Hausmann

O site, em Terça de 10 de novembro:

```
Salmos {do Saltério do dia correspondente}      -> PsF
Capítulo Responsório Verso {do Comum ou Festa}  -> CS
Oração {do Próprio dos Santos}                  -> PS
```

A oração vem do **Proprium Sanctorum**. O `Dómine, exáudi` vem do
Ordinário. É o inverso do que a tabela do capítulo IX imprime.

Confirmam a mesma coisa, independentemente:

- a norma oficial 169 d): *"At Terce, Sext and None: antiphons and psalms
  as in the Psalter for the current weekday; the rest from the feast, as in
  the Proper or the Common"*
- o próprio ofício-modelo do Hausmann, capítulo XV: *"From the Ord. but the
  prayer from the Proprium"*
- o esqueleto do Divinum Officium, onde `#Oratio` é bloco preenchido pelo
  próprio do dia

E as peças que o site produziu são exatamente as do desdobramento do
Hausmann para esse dia: antífona *Éxcita, Dómine*, salmos 79(2-8), 79(9-20)
e 81, capítulo *Beátus vir* (Sir 31:8-9), responsório *Amávit eum Dóminus*,
versículo *Os justi*, oração *Deus, qui in corde beáti Andréæ*. Até a
comemoração dos Santos Trifão e companheiros confere.

**Correção a fazer na matriz:** Terça, Sexta e Noa, coluna III —
`Domine exaudi` passa a **Ord**, `Oremus. Oração` passa a **PS**.

---

## ⚠B — o site dá uma terceira resposta, e é a certa

No domingo, o site rotula:

```
Capítulo Responsório Verso {Durante o Ano}
Capitulum Responsorium Versus {Per Annum}
```

Nem `Ord` (como diz a tabela) nem `Psalterium` (como diz o ofício-modelo):
**pelo tempo litúrgico**. O capítulo das horas menores no domingo muda
conforme a estação.

A célula única do Hausmann esconde uma dependência de tempo.

---

## O que já geramos confere

As Completas da Assunção, no site:

```
Salmos {Salmos & Antífonas de Domingo}
Psalmi {Psalmi et Antiphona de Dominica}
Ant. Miserére * mihi, Dómine, et exáudi oratiónem meam.
Psalmus 4 ... Psalmus 90 ... Psalmus 133
```

Numa festa de I classe, as Completas usam salmos e antífona **do domingo** —
o site diz isso com todas as letras no rótulo. Confere com a linha da
matriz (I = PsD) e com o capítulo XIII.

E é **exatamente** o que o nosso gerador produziu para as Completas de
domingo: mesma antífona, mesmos salmos 4, 90 e 133. Gerador, site e
Hausmann dizem a mesma coisa.

---

## Duas coisas que a conferência pegou de graça

### 1. O inglês vazando, ao vivo

Na coluna portuguesa do domingo, no site oficial, com o idioma português
escolhido:

```
Ant. Alleluia, * Lead me into the path of thy commandments, alleluia, alleluia.
```

É a armadilha do idioma de reserva da seção 13, acontecendo na tela. Não é
hipótese.

### 2. Um defeito real no nosso gerador, apanhado pelo aviso de vazio

O nosso gerador imprimiu:

```
--- Antiphona finalis ---   (Psalterium/Mariaant.txt [Ant Maria4])
    VAZIO: nao encontrei texto para esta peca
```

E tinha razão: a seção `[Ant Maria4]` não existe. O arquivo tem
`[Advent]`, `[Nativiti]`, `[Quadragesimae]`, `[Paschalis]` e
`[Postpentecost]` — **a antífona final de Nossa Senhora é escolhida pelo
tempo litúrgico**. O site, em 15 de agosto, deu *Salve Regina*, que é a de
depois de Pentecostes.

Mais uma célula que a matriz tem como `Ord` fixo e que na verdade depende
da estação.

Vale registrar que o defeito só apareceu porque o gerador se recusa a pular
peça em silêncio. Sem esse aviso, a antífona final simplesmente não sairia
no livro, e ninguém notaria até rezar.

---

## Uma correção na legenda das colunas

Eu rotulei as colunas como "festa de I classe", "de II classe" e assim por
diante. Está errado, e o dia 10 de setembro mostra por quê: o site o dá
como **II classe**, e mesmo assim ele reza o ofício **dominical**, não o
semifestivo.

As colunas não são classes de dia; são **tipos de ofício**. A norma oficial
define assim:

| Coluna | A quem pertence | Norma |
|---|---|---|
| I | festas de I classe | 167 |
| II | festas de II classe | 168 |
| III | festas de III classe **e o ofício de Nossa Senhora ao sábado** | 169 |
| DOM | domingos, de qualquer classe | 165 |
| FER | todas as férias e vigílias, salvo o Tríduo Sacro e a vigília do Natal | 170 |

---

## O padrão que emergiu

Três achados independentes dizem a mesma coisa:

1. o capítulo das horas menores muda por tempo;
2. o Te Deum muda por tempo;
3. a antífona final de Nossa Senhora muda por tempo.

**A matriz de valor único não é a regra — é um resumo dela.** Serve para
entender; não serve para gerar 365 dias.
