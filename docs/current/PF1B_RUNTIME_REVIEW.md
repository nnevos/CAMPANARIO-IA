# PF1b — Runtime Lifecycle / Hosting Review

## Resultado

PF1b conclui o gate PF1 da Platform Foundation sem introduzir service nativo, Event Bus ou rede remota.

## Implementado

- `CampanarioRuntime.start()/stop()` com estado explicito e idempotente;
- `RuntimeHost` process-local, thread-safe, com um unico runtime ativo por vez;
- restart do host cria novo `runtime_id` mantendo sessoes persistidas no SQLite;
- FastAPI lifespan inicia/encerra o host;
- API usa `get_runtime()` como boundary principal;
- `get_chat_service()` permanece somente como compatibilidade legada;
- entrypoint headless `campanario-runtime` prova hosting sem Web/FastAPI;
- launchers Windows de teste/headless adicionados;
- `/api/system` expoe `runtime_id` e `runtime_status` para diagnostico local.

## Nao implementado de proposito

- Windows service/tray;
- comunicacao entre processos;
- Realtime Gateway/WebSocket v1;
- Event Bus;
- Device/Tool Registry;
- Permission Layer.

Ate o Realtime Gateway existir, host Web e host headless sao alternativas de hospedagem, nao clientes simultaneos do mesmo runtime em memoria.

## Evidencia

- testes focados PF1/API/lifecycle: 19 PASS;
- regressao completa: **343/343 PASS**;
- `compileall` sem erros;
- Personality Core nao alterado.

## Proximo gate

**PF2 — Event Bus interno com contratos versionados, ordem e provenance.**
