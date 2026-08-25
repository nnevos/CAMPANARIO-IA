# ADR-0033 — Pre-agent freeze, model boundary refactor and bakeoff gate

## Status
Accepted.

## Context
O ciclo v1.4-v1.6 provou invariantes uteis, mas acumulou complexidade e o `llama3:latest` continuou variando em naturalidade/factualidade. Projetos de referencia mostram prompts menores, separacao de provider/contexto/tools e uso frequente de Qwen/Gemma/modelos maiores.

## Decision
Congelar tuning comportamental, separar `model` de `response`, centralizar composition e comparar modelos sobre o mesmo Campanario antes de novos patches. Preservar `llm.*` apenas como compatibility shim temporario. Agentes permanecem bloqueados ate bakeoff + mega + refatoracao final.

## Consequences
Trocar modelo deixa de ser recomeço arquitetural. Falhas podem ser comparadas empiricamente. Historico permanece auditavel, enquanto docs ativos ficam menores.
