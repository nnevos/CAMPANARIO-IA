# ADR-0036 — System/Agent Separation and Browser-first UI

## Status
Accepted.

## Context
Agent Architecture v1 representava Campanario como uma terceira persona selecionavel. Isso contradizia o conceito canonico: Campanario e o sistema e agentes sao pontes.

## Decision
- remover `campanario` do registry de agentes;
- tornar Morgana o agente default;
- tratar `Campanario` como wake/endereco do sistema;
- manter Todd/Morgana como unicas personas atuais;
- migrar sessoes antigas `campanario -> morgana`;
- manter mensagens historicas `campanario` sem atribuicao de agente;
- manter UI browser-first e preparar fronteira para futura shell desktop;
- wake/voice futuro reutiliza o mesmo AgentRouter.

## Consequences
O sistema e as personas ficam semanticamente separados, e uma futura interface desktop pode envolver a UI/API existentes sem reescrever o core.
