# Retomar apos o reinicio

Atualizado em 2026-08-04, ao fim da tarde.

## Por que reiniciar — e por que ja nao urge

O recurso do WSL ja foi habilitado por DISM e aguarda so o reinicio.
Depois dele:

    wsl --install -d Ubuntu

Ganha-se **o WeasyPrint**, que no Windows exige a biblioteca GTK e por
isso nao roda. Enquanto isso o PDF sai pelo Chrome, com o MESMO CSS —
`python gerador/imprimir.py`. O trabalho nao se perde.

O que era o outro motivo — rodar o site localmente para comparar os 365
dias — **deixou de ser preciso**: o gerador em lote do proprio
repositorio roda aqui, sem servidor (decisao 3.9).

## No comeco de toda sessao nova

Ler, nesta ordem, antes de qualquer codigo e de qualquer pergunta:

1. `PROMPT-BREVIARIO.md`
2. `decisoes.md`
3. este ficheiro

## Estado do projeto

Feito e conferido contra o Perl original, sem uma divergencia:

- repositorio clonado e corrigido por um comando (`python gerador/preparar.py`)
- motor de condicionais — 15.050 comparacoes
- resolvedor de remissoes `@` e `$` — 30.674 seccoes
- a funcao `&psalm`, que poe salmo na pagina — 684 casos
- o extractor do Comum, que le o `vide C5` da linha `[Rank]` — 660 casos
- matriz de regras a partir das normas oficiais de 1960

Feito e conferido contra o gerador oficial, linha a linha:

- **Completas nos seis dias de semana e a Sexta de 4 de agosto de 2026**,
  em latim: zero diferencas
  (`python gerador/comparar_texto.py --hora Sexta`)

A pagina composta, nas duas edicoes, sai em PDF de 100 x 160 mm:

    python gerador/compor.py --semana "Feria II"
    python gerador/compor_sexta.py
    python gerador/imprimir.py

## A fazer, por ordem

1. **O calendario.** E o que falta para o programa saber sozinho que dia
   e hoje e qual o oficio. E a unica divergencia que resta na comparacao:
   o sabado 22 de agosto de 2026, festa de II classe, cujas Completas
   tomam os salmos de domingo.
2. As antifonas proprias do tempo — Advento e Pascoa — nas horas menores.
3. A extracao do corpus limpo.
4. Numeracao de pagina, e as remissoes calculadas depois de paginar.
5. As oito verificacoes obrigatorias, nos 365 dias.
