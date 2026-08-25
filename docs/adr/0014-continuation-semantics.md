# ADR-0014 — Continuation Semantics

## Status
Accepted — 2026-08-24

## Context
O teste manual da Conversational v1.3 mostrou que o isolamento entre modos melhorou, mas mensagens curtas de continuidade ainda eram tratadas de forma uniforme. `aham`, `ok`, `pois entao`, `mas posso estar errado` e `deixa isso pra la` produziram repeticao integral da resposta anterior, continuidade artificial ou incapacidade de encerrar um tema.

## Decisao
Manter `TurnMode.CONTINUATION` como modo unico, mas adicionar uma semantica interna deterministica por turno:

- `acknowledgement`: confirmacao curta (`ok`, `aham`, `entendi`, etc.); nao recapitular automaticamente;
- `reflection`: reacao/reflexao curta (`pois e`, `e complicado`, etc.); reconhecer sem fabricar tarefa;
- `revision`: hesitacao/revisao (`posso estar errado`, `nao tenho certeza`); responder ao ponto de incerteza sem repetir a explicacao inteira;
- `topic_drop`: abandono/pausa de tema (`deixa isso pra la`, `esquece isso`); encerrar o tema sem perguntar automaticamente o proximo assunto.

A semantica e exposta no boundary do turno e no trace de auditoria. A auditoria tambem recebe um sinal mecanico quando uma resposta repete integralmente a anterior.

## Consequencias
- melhora a naturalidade sem multiplicar modos de alto nivel;
- evita tratar toda continuacao curta como pedido de recapitulacao;
- preserva o isolamento de modos do v1.3;
- nao altera memoria, RAG, personas, temperatura ou provider;
- novos exemplos de linguagem podem ser adicionados por categoria sem criar respostas hardcoded para perguntas especificas.
