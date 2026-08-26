# PF2 — Internal Event Bus Review

## Resultado

PF2 introduz o primeiro event model interno do Runtime v2 sem iniciar PF3/Realtime Gateway.

### Implementado

- `RuntimeEventBus` process-local pertencente ao mesmo `CampanarioRuntime`;
- envelope `RuntimeEvent` versionado (`schema_version=1.0`);
- `event_id`, ordem monotônica por `sequence`, `runtime_id`, `session_id`, `correlation_id` e `causation_id`;
- `EventProvenance` explícita para runtime/system/user/agent/client/device/tool;
- payloads Pydantic tipados e `extra=forbid`, evitando dictionaries arbitrários fora de contrato;
- catálogo de eventos preparado para conversation, voice/wake, sessions, agents, devices, tools, location/context, memory e call;
- journal bounded em memória e `replay()` básico por sequence/session/type;
- subscriptions internas filtráveis;
- fluxo real de conversa publica SESSION_STARTED, USER_TEXT, AGENT_SELECTED, AGENT_INTENT_TO_SPEAK, RESPONSE_STARTED/CHUNK/FINISHED;
- `ChatService` usa `EventPublisher`, sem depender de transporte.

### Deliberadamente não implementado

- WebSocket / `/ws/v1`;
- `/api/v1` novo;
- broker externo ou replay durável entre processos;
- Device Registry;
- Tool/Capability Registry;
- Permission Layer;
- mobile/voice/call final.

Esses itens permanecem em gates posteriores.

## Testes

Os testes PF2 cobrem:

- versionamento e validação do envelope/payload;
- ordem monotônica;
- correlation/causation ids;
- provenance de usuário/runtime/agente;
- subscribe/filter/unsubscribe;
- replay básico;
- integração do bus com um turno real do `ChatService`;
- identidade única do bus dentro do runtime.

Regressão completa após PF2: **348/348 PASS**.

## Gate

PF2 concluído. Próximo gate: **PF3 — Realtime/API Gateway**, migrando incrementalmente a Web atual para consumir contratos versionados sem big-bang rewrite.
