# Capability / Tool Registry

PF5 separa **o que o Campanario pode pedir** de **como isso e executado**.

Exemplo:

```text
Morgana/Todd/runtime -> location.current -> Capability Registry -> provider/device
```

Todd e Morgana nao precisam saber se a localizacao veio de um celular, de um adapter local ou de outro provider. Eles usam o mesmo nome semantico da capability.

## Consultar capabilities

```text
GET /api/v1/capabilities
GET /api/v1/capabilities?available_only=true
GET /api/v1/capabilities/location.current
```

O catalogo mostra nome, descricao, schemas, provider, timeout, requirements de permissao, provenance e disponibilidade.

## Device x capability semantica

PF4 registra que um device possui algo fisico como `gps`.

PF5 permite um provider oferecer algo semantico como `location.current` usando esse device. Se o device desconectar, a capability pode continuar registrada, mas aparece indisponivel.

## Importante sobre seguranca

PF5 **nao autoriza** uma capability apenas porque ela existe. O campo `permissions` e apenas requisito declarado. PF6 implementara pairing, trust, confirmacao, revogacao e policy decisions.

Por isso nao existe neste gate um endpoint publico generico para executar qualquer capability.
