# PF7 — Client-independent sessions review

## Objetivo

Provar que interfaces diferentes sao apenas clientes do mesmo Campanario: PC/Web e um segundo cliente entram na mesma `session_id`, observam o mesmo historico/contexto e podem se substituir sem criar outra sessao, outro Todd ou outra Morgana.

## Implementado

- `ClientIdentity`: `client_id` separado de `device_id` e `agent_id`;
- `ClientSessionRegistry`: attachments vivos process-local, sem ownership da sessao;
- `/ws/v1/events?...&client_id=...` registra/desregistra attachments na mesma sessao;
- `GET /api/v1/sessions/{session_id}/clients` permite inspecionar attachments ativos;
- `POST /api/v1/sessions/{session_id}/turn` aceita `X-Campanario-Client-Id` e opcional device autenticado;
- mensagens USER persistem `client_id` / `device_id` via migration `0008`;
- `USER_TEXT` usa provenance `client`; respostas continuam provenance `agent`;
- Presence UI usa `client_id` persistente no `localStorage`;
- `episode_id` e explicitado como alias do atual `session_id` tecnico; nao foi inventado um segundo container de contexto.

## Evidencia automatica

`tests/test_client_independent_sessions.py` prova:

1. PC cria uma sessao e envia o primeiro turno;
2. segundo cliente le exatamente o mesmo historico;
3. segundo cliente continua o turno e o model context inclui a fala iniciada no PC;
4. ambos observam a mesma sessao por WebSocket;
5. `client_id` de origem aparece no `USER_TEXT`, enquanto `agent_id` continua separado;
6. reconnect do mesmo cliente cria apenas novo attachment, nao nova sessao;
7. provenance de client/device sobrevive roundtrip SQLite.

## Limites preservados

- gateway continua localhost-only;
- `client_id` sozinho nao e credencial;
- `device_id` associado a cliente exige PF6 quando usado na API/WS;
- mobile completo, background transport, voz e call nao fazem parte de PF7;
- Personality / Social / Long-Call Baseline v1 nao foi alterada.

## Gate seguinte

PF8 — Mobile Readiness: cliente remoto minimo deve parear/autenticar, conectar ao mesmo runtime, enviar texto, acompanhar transcript/eventos, oferecer uma capability mock de localizacao e reconectar sem criar outra personalidade/sessao.
