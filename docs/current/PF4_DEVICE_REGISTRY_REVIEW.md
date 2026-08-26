# PF4 — Device Registry Review

## Resultado

PF4 adiciona identidade persistente de dispositivos e discovery por capability sem transformar dispositivo em participante social nem em credencial de seguranca.

### Registro persistente

`DeviceRegistry` pertence ao `CampanarioRuntime` e persiste no SQLite via migration `0006`.

Cada device possui:

- `id` estavel;
- `name`;
- `type` descritivo;
- `capabilities` normalizadas;
- `connection_state`;
- `created_at`, `updated_at`, `last_seen`.

Reconnect com o mesmo `device_id` atualiza o mesmo registro; nao cria outro Todd, Morgana, sessao ou memoria.

### Discovery por capability

O runtime consulta `find_capable("gps")`, `find_capable("microphone")`, etc. O campo `type` e apenas descritivo: nao existe logica `se Android use GPS X`.

### Gateway de device

`/ws/v1/devices` recebe primeiro um frame versionado `device_hello` e responde `device_ready`. Disconnect marca o device offline. `ping` atualiza `last_seen`.

A API oferece leitura:

- `GET /api/v1/devices`;
- filtro `capability` + `connected_only`;
- `GET /api/v1/devices/{device_id}`.

### Eventos

Connect/touch/disconnect usam os eventos PF2 existentes:

- `DEVICE_CONNECTED`;
- `DEVICE_STATE_CHANGED`;
- `DEVICE_DISCONNECTED`.

Todos carregam provenance com `source_kind=device`, `source_id` e `device_id`.

## Limite de seguranca

PF4 nao implementa trust. Um client que diz `device_id=phone-main` apenas identifica um registro local; isso nao prova identidade nem autoriza camera, GPS ou qualquer acao. Pairing, tokens, trust, revogacao e Permission Layer continuam PF6. O host segue restrito a `127.0.0.1`.

## Evidencia

Testes focados de Device Registry + gateway + Event Bus + runtime: **22/22 PASS** antes da regressao completa.

A regressao completa inicial encontrou somente a expectativa de release PF3 em `test_api_chat.py`; o codigo funcional permaneceu verde. A expectativa foi atualizada para PF4 antes da regressao final.

## Proximo gate

**PF5 — Capability / Tool Registry provider-independent.**
