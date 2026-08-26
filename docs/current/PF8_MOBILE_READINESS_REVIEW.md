# PF8 — Mobile Readiness review

## Objetivo

Provar que um cliente com formato de celular pode acessar **o mesmo Campanario** sem criar runtime, Todd, Morgana, memoria ou sessao paralelos.

## Implementado

- `MobileReadinessClient`: cliente minimo sem UI/platform SDK;
- pairing PF6 em primeiro contato e autenticacao posterior por credential;
- `/ws/v1/devices` exige credential quando o device ja esta pareado;
- cliente envia texto autenticado usando `client_id` + `device_id` no mesmo `/api/v1/.../turn`;
- cliente observa e reconecta ao mesmo `/ws/v1/events` / `session_id`;
- snapshot autenticado de GPS `location_update`;
- snapshot vira `location.current` no PF5, com provider/device provenance e `location.read`;
- `LOCATION_UPDATED` trafega pelo Event Bus PF2;
- snapshot e invalidado no disconnect e nao vira memoria persistente;
- scripts `TESTAR_RUNTIME_PF8.bat` e `RODAR_CLIENTE_MOBILE_PF8.bat`.

## Evidencia automatica

`tests/test_mobile_readiness.py` cobre:

1. primeiro contato registra device sem confiar nele;
2. pairing produz credential e reconnect autenticado;
3. device nao pareado nao consegue publicar location;
4. GPS autenticado fornece `location.current` consumida pelo Campanario;
5. provenance da location aponta para o device correto;
6. disconnect torna a capability indisponivel;
7. PC e mobile continuam a mesma `session_id`/historico;
8. mensagem mobile persiste `client_id` e `device_id` sem afetar `agent_id`;
9. reconnect cria novo attachment, nao nova conversa;
10. um E2E sobe Uvicorn em loopback e usa HTTP/WebSocket reais com o `MobileReadinessClient`.

## Limites preservados

- gateway continua `127.0.0.1`; nenhum suporte LAN/WAN de producao e alegado;
- o cliente de prova nao e um app Android/iOS;
- nao existe GPS continuo/background, push, camera, microfone ou notificacoes;
- credencial continua separada de `device_id`;
- multi-device capability arbitration fica para politica futura;
- Personality / Social / Long-Call Baseline v1 permanece intacta.

## Shell mobile futuro

Um shell Android/iOS deve apenas implementar os mesmos contratos:

- secure storage para device credential;
- lifecycle/reconnect/background permitido pela plataforma;
- UI/transcript/presence;
- adapters deliberados para GPS/microphone/speaker/notifications;
- transporte remoto somente depois de pairing/network security apropriados (TLS, limite de interfaces, revogacao).

Ele nao deve conter outro ChatService, memoria ou agentes.

## Validacao

- focados PF3-PF8: **29/29 PASS**;
- regressao completa: **377/377 PASS**;
- Alembic `0001 -> 0008`: PASS;
- `compileall`: PASS.

## Gate seguinte

PF9 — Voice / Call Readiness **de contratos**: VAD/wake/STT/TTS/barge-in/interruption devem entrar como adapters/eventos do mesmo runtime. Isso nao libera implementar audio continuo final antes dos gates de Experience/Learning definidos no roadmap.
