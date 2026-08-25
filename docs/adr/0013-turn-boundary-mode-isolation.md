# ADR-0013 — Turn boundary and mode isolation

## Status
Accepted

## Context
O teste manual da Conversational v1.2 mostrou vazamento de comportamento entre turnos: uma ficcao explicitamente pedida contaminou uma pergunta factual posterior. Embora o interpretador classificasse o turno atual corretamente, o historico recente continuava exercendo forte influencia de estilo/tarefa no modelo-base.

## Decision
Cada resposta recebe um **limite de turno** como mensagem `system` imediatamente antes do USER atual. Esse boundary declara que o pedido atual define o modo da resposta e que estilo, ficcao, humor, formato ou objetivo de turnos anteriores nao sao permissao persistente.

A personalidade pode permanecer continua; o modo da tarefa nao. O interpretador continua deterministico, sem nova chamada ao LLM. O trace de auditoria passa a registrar o modo esperado de cada pedido.

## Consequences
- reduz contaminacao `creative -> factual` e outras transicoes;
- adiciona uma mensagem system por request, proxima ao turno atual;
- nao altera memoria, resumo, temperatura, provider, RAG, tools ou personas;
- requer validacao manual no modelo local, pois obediencia ao boundary depende tambem do LLM-base.
