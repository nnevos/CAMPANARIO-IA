# PF3 — Realtime/API Gateway Review

## Resultado

PF3 adiciona a primeira porta client-independent formal do Runtime v2.

### API versionada

- `GET /api/v1/runtime` (alias também disponível como `/api/v1/system`);
- `GET /api/v1/agents`;
- `GET/POST /api/v1/sessions`;
- `GET /api/v1/sessions/{session_id}/messages`;
- `PATCH /api/v1/sessions/{session_id}/primary-speaker`;
- `POST /api/v1/sessions/{session_id}/turn`.

Os endpoints `/api/...` antigos continuam ativos para compatibilidade, incluindo o SSE legado.

### Realtime

`/ws/v1/events` entrega frames versionados `1.0` contendo os `RuntimeEvent` PF2 originais. O cliente pode filtrar por `session_id` e reconectar com `after_sequence=N` para receber replay do journal process-local antes de voltar ao live stream.

A subscription acontece antes do replay e o gateway descarta sequências já reenviadas, evitando um buraco entre replay e eventos live sem duplicar sequência observada.

### Web UI

A Presence UI atual foi migrada para:

1. criar/consultar sessão via `/api/v1`;
2. conectar ao `/ws/v1/events` da sessão;
3. renderizar `AGENT_RESPONSE_STARTED`, `AGENT_RESPONSE_CHUNK` e `AGENT_RESPONSE_FINISHED`;
4. submeter o turno por `POST /api/v1/sessions/{id}/turn`.

Ela não depende mais do endpoint SSE para o fluxo principal.

## Segurança

PF3 não abre Campanario na rede. O launcher continua usando `127.0.0.1`. Pairing, tokens, trust, revogação e exposição remota pertencem ao PF6; não devem ser contornados antecipadamente.

## Testes

- v1 API e WebSocket observam o mesmo `runtime_id`;
- eventos do turno chegam na ordem PF2 e preservam provenance;
- reconexão por `after_sequence` reutiliza a mesma sessão e faz replay;
- API/SSE legado continua disponível;
- Web UI referencia `/api/v1` e `/ws/v1/events`, não `/chat/stream`;
- regressão completa após PF3: **352/352 PASS** antes da atualização documental final.

## Próximo gate

**PF4 — Device Registry**, ainda sem implementar Tool Registry ou Permission Layer.
