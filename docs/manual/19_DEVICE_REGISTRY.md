# 19 - Device Registry

PF4 permite ao Campanario manter um registro de dispositivos conectados sem acoplar o runtime a Android, Windows ou outro sistema especifico.

## O que um dispositivo anuncia

Exemplo conceitual:

```text
id: phone-main
name: Meu celular
type: mobile
capabilities:
- gps
- microphone
- speaker
- battery
```

O `type` serve para descricao. Para escolher de onde obter uma funcao fisica, o runtime consulta a capability: por exemplo, "qual device conectado possui `gps`?".

## Persistencia

O registro fica no mesmo SQLite do runtime. Fechar a conexao muda o device para `disconnected`, mas nao apaga sua identidade ou capabilities. Reconectar com o mesmo `device_id` reutiliza o registro existente.

## API local

- `GET /api/v1/devices`
- `GET /api/v1/devices?capability=gps&connected_only=true`
- `GET /api/v1/devices/{device_id}`

## Canal realtime de device

`/ws/v1/devices` recebe um `device_hello` versionado e responde `device_ready`. Um `ping` pode atualizar `last_seen`.

## Importante: ainda nao e pairing seguro

PF4 identifica devices, mas nao os autoriza. `device_id` nao e senha, token ou prova de identidade. Trust, pairing, revogacao e permissoes entram somente em PF6. Por isso o Campanario continua restrito a localhost nesta fase.
