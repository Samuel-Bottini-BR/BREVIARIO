# Breviário Romano 1960

Gerador da edição impressa do Breviário Romano nas rubricas de 1960, a
partir do corpus do Divinum Officium. Projeto do Pe. Rosenei, para o Padre
rezar. Ver `PROMPT-BREVIARIO.md` para a especificação completa e
`decisoes.md` para tudo que já foi decidido — ler os dois antes de
perguntar algo que talvez já tenha resposta.

**Handoff:** `ESTADO.md` é o estado atual do projeto — leia primeiro em
qualquer sessão nova. Só atualize esse arquivo quando o Samuel pedir
explicitamente ("atualiza o handoff" / "atualiza o ESTADO.md").

## Commit e push regulares

Este repositório tem GitHub remoto (`origin`). Faça commit do progresso
relevante regularmente (fim de sessão, ou depois de fechar uma etapa) e dê
`git push` — não é preciso perguntar cada vez, mas sempre revise o que está
sendo commitado antes (nunca commitar segredo; `divinum-officium/`,
`perl5/`, `*.pdf`, `*.html` e `*.tsv` já ficam fora pelo `.gitignore` por
serem dependência externa ou saída regenerável).

## As 6 regras de metodologia

Ver a memória `breviario-metodologia` (se disponível nesta máquina) ou o
histórico de `decisoes.md` — nunca inferir do PDF o que o gerador já sabia,
nunca escrever um teste que anda pelo mesmo caminho do gerador, medir
exatamente o que se quer saber, nunca deixar um caminho falhar em silêncio,
funil único para limpeza repetida, cuidado com fallback de idioma ao medir
cobertura de tradução.
