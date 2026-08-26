# PF5 — Capability / Tool Registry Review

## Resultado

PF5 adiciona uma camada de capacidades semanticas provider-independent ao `CampanarioRuntime`.

### Contrato

Cada capability possui:

- nome (`location.current`, `web.search`, etc.);
- descricao;
- input/output schema;
- provider id;
- requirements de permissao como metadata;
- timeout;
- availability;
- provenance de provider/device.

O caller pede uma capability pelo nome. Ele nao importa nem seleciona provider concreto.

### Providers

`CallbackCapabilityProvider` e um adapter transport-neutral para providers locais/mock/futuros bridges. `DeviceCapabilityProvider` liga uma capability semantica a um device PF4; availability acompanha estado conectado/desconectado e uma capability fisica opcional, como `gps`.

O teste de gate registra um device com `gps`, fornece `location.current` por um provider de device mock/remoto e executa pelo registry sem o caller conhecer o provider. Ao desconectar o device, `location.current` passa a indisponivel automaticamente.

### Eventos

Execucao publica os contratos PF2 existentes:

- `TOOL_REQUESTED`;
- `TOOL_STARTED`;
- `TOOL_RESULT`;
- `TOOL_FAILED`.

Correlation/causation e provenance continuam no mesmo Event Bus.

### API

PF5 adiciona somente discovery:

- `GET /api/v1/capabilities`;
- `GET /api/v1/capabilities/{name}`;
- filtro `available_only` na listagem.

Nao existe endpoint generico de execucao remota em PF5. Autorizar/confirmar actions e responsabilidade do PF6.

## Limites

- permission strings sao metadata, nao decisao de seguranca;
- `device_id` continua sem representar trust;
- nenhum provider final de mapa/clima/web/files foi integrado em massa;
- nenhum detalhe de provider foi adicionado ao Personality Core;
- gateway continua localhost-only.

## Evidencia

Testes focados PF4/PF5/Event Bus/Gateway/Runtime: **22/22 PASS**.

Regressao completa antes da documentacao: **362/362 PASS**.

## Proximo gate

**PF6 — Permission / Trust Layer.**
