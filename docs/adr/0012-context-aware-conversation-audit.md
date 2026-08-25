# ADR-0012 — Context-aware conversation audit

## Status
Accepted

## Context
O teste manual da Conversational v1.1 mostrou que a auditoria conseguia detectar sinais mecanicos, mas julgava respostas isoladas. Isso fez uma ficcao explicitamente solicitada ser marcada como problema e permitiu continuidade social forcada.

## Decision
A auditoria comportamental deve avaliar pares pedido/resposta. Ficcao, humor e hipoteses explicitamente solicitados sao invencao autorizada e nao alucinacao factual. Continuacoes curtas devem preservar o fluxo sem eco ou obrigacao de manter a conversa andando. Discordancia pode ser explicita e respeitosa sem concordancia de cortesia contraditoria.

## Consequences
A camada continua deterministica e sem nova chamada ao LLM. Ela orienta comportamento, nao decide verdade. Memoria, RAG, tools e personas permanecem fora deste gate.
