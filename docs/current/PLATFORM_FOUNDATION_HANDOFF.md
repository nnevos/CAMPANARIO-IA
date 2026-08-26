# Campanario — Platform Foundation / Runtime v2 Handoff

> Fase futura. **Nao iniciar enquanto o gate conversacional P2.3 nao estiver congelado.**

## Objetivo

Evoluir o Campanario de uma aplicacao centrada na Web UI para um **runtime persistente, client-independent e orientado a eventos**. Web, Desktop, Mobile, Call e Patrulha devem se tornar superficies diferentes do mesmo sistema, compartilhando Todd, Morgana, memoria, sessoes, tools e estado.

Arquitetura alvo:

```text
Web / Desktop / Mobile / Voice
              |
      Realtime/API Gateway
              |
       CAMPANARIO RUNTIME
       | Conversation Runtime
       | Todd / Morgana
       | AgentRouter
       | ParticipationArbiter
       | Social Protocol
       | Conversation Focus
       | Memory / Experience
       | Event Bus
       | Capability Registry
       | Device Registry
       | Permission / Policy
              |
      Providers / Tools / Devices
```

## Principios nao negociaveis

- Campanario continua sendo sistema/ambiente, nunca uma persona.
- Todd e Morgana continuam participantes persistentes da mesma realidade.
- Nao duplicar memoria, banco de fatos, provider, tools ou knowledge core por agente ou cliente.
- Fechar uma interface nao deve necessariamente desligar o runtime.
- Voz reutiliza Conversation Runtime, Social Protocol, Focus e ParticipationArbiter; nao cria um segundo pipeline cognitivo.
- Mobile e um terminal/dispositivo do mesmo Campanario, nao outra instancia dos agentes.
- Tools sao capacidades do Campanario; agentes nao conhecem provider especifico por personalidade.
- Mudancas devem ser incrementais; a Web UI existente continua funcional durante a migracao.

## PF1 — Runtime boundary

- separar runtime, API e UI;
- criar interfaces claras para RuntimeState, SessionManager, ConversationService, AgentRuntime, ToolRuntime e DeviceRuntime;
- provar runtime funcionando sem navegador aberto;
- decidir somente depois se o processo vira service/tray/desktop shell nativo.

**Gate:** runtime sobe, mantem sessao e responde por API sem depender da Web UI.

## PF2 — Event Bus e contratos versionados

Eventos candidatos:

- USER_TEXT / USER_SPEECH_PARTIAL / USER_SPEECH_FINAL / WAKE_DETECTED;
- SESSION_STARTED / SESSION_ENDED;
- AGENT_SELECTED / AGENT_INTENT_TO_SPEAK / AGENT_RESPONSE_STARTED / CHUNK / FINISHED / INTERRUPTED;
- DEVICE_CONNECTED / DISCONNECTED / STATE_CHANGED;
- TOOL_REQUESTED / STARTED / RESULT / FAILED;
- LOCATION_UPDATED / CONTEXT_UPDATED;
- MEMORY_CANDIDATE / WRITTEN / CORRECTED;
- CALL_STARTED / CALL_ENDED.

Nao espalhar dicts arbitrarios: eventos devem ter schema/versionamento/provenance.

**Gate:** ordem, autoria e replay basico de eventos testados.

## PF3 — Realtime/API Gateway

- `/api/v1/...` para operacoes request/response;
- `/ws/v1/...` para eventos realtime;
- transcript, speaker start/finish, tool activity, device state, presence state e interruption;
- reconexao sem criar nova sessao por acidente.

**Gate:** Web atual migrada para consumir o gateway sem perder funcionalidade.

## PF4 — Device Registry

Representar dispositivos por capacidades, nao por plataforma hardcoded.

Exemplos de capability de dispositivo:

- microphone;
- speaker;
- screen;
- gps;
- camera;
- notifications;
- keyboard;
- files;
- battery;
- network.

**Gate:** um cliente de teste remoto conecta, anuncia capabilities e desconecta/reconecta preservando identidade do device.

## PF5 — Capability / Tool Registry

Capacidades futuras:

- `location.current`;
- `maps.route`;
- `maps.nearby`;
- `weather.current` / `weather.forecast`;
- `web.search`;
- `files.search` / `files.read`;
- `notes.create`;
- `calendar.read` / `calendar.create`;
- `contacts.lookup`;
- `device.status`;
- `camera.inspect`;
- `computer.open` / `computer.read_state`.

Cada capability possui nome, descricao, input/output schema, provider, permissao, disponibilidade, timeout e provenance.

**Gate:** capability mock/remota fornecida por um device e consumida pelo runtime sem o agente conhecer provider.

## PF6 — Permission / Trust Layer

Separar capability **disponivel** de capability **autorizada**.

Exemplos conceituais:

- `location.read`: allow while session;
- `camera.capture`: ask;
- `message.send`: confirm;
- `file.delete`: confirm;
- `computer.execute`: scoped confirm;
- `microphone.listen`: allow while call.

Adicionar pairing, trust, token/session credential, revogacao, audit trail e rede conservadora.

**Gate:** testes provam bloqueio/confirmacao e revogacao.

## PF7 — Client-independent sessions

Definir claramente:

- session_id;
- episode_id;
- client_id;
- device_id;
- speaker provenance.

Dispositivo nao e participante social.

**Gate:** PC inicia uma sessao, cliente remoto entra na mesma sessao, observa o mesmo contexto e reconecta sem duplicar Todd/Morgana/memoria.

## PF8 — Mobile readiness

Nao construir app completo primeiro. Criar cliente minimo capaz de:

- parear/autenticar;
- enviar texto;
- receber eventos;
- acompanhar transcript/presenca;
- fornecer `location.current` mock/test;
- reconectar.

Depois definir shell Android/iOS.

## PF9 — Voice / Call readiness

Preparar contratos para:

- VAD;
- wake word;
- STT streaming;
- TTS streaming por agente;
- barge-in;
- interruption;
- speaker arbitration;
- background call.

Fluxo unico:

```text
Microfone -> Wake/VAD -> STT -> Conversation Runtime -> ParticipationArbiter -> Todd/Morgana -> TTS
```

## PF10 — Patrulha readiness

A Platform Foundation nao implementa Patrulha completa. Ela apenas torna possivel depois conectar:

- localizacao;
- mapa/rotas;
- pesquisa;
- clima/transito;
- bateria/conectividade;
- notas/fotos deliberadas;
- call em background;
- memoria experiencial.

Conceito: `docs/concept/MODO_PATRULHA_V2.md`.

## Latencia como requisito arquitetural

Instrumentar desde o runtime:

- request_received;
- routing_completed;
- context_ready;
- generation_started;
- first_token;
- first_usable_output;
- generation_finished;
- second_agent_started;
- turn_finished;
- tool_started / tool_finished.

Preservar as metricas do Long Call. Em voz, otimizar primeiro o **silencio percebido**, nao apenas tempo total.

## Testes obrigatorios da fase

1. runtime funciona sem UI;
2. cliente conecta/desconecta;
3. duas interfaces nao criam memoria duplicada;
4. sessao continua apos reconexao;
5. Device Registry preserva capabilities;
6. Tool Registry e provider-independent;
7. Permission Layer bloqueia acao sem autorizacao;
8. eventos preservam ordem/provenance;
9. speaker provenance continua correto;
10. Todd/Morgana usam o mesmo estado;
11. Web UI existente continua funcionando;
12. Personality Core permanece intacto;
13. Behavioral/Long Call continuam compativeis.

## Fora de escopo da primeira iteracao

- app Android/iOS completo;
- STT/TTS final;
- wake final;
- Patrulha completa;
- camera always-on;
- localizacao continua real;
- automacao irrestrita do PC;
- dezenas de providers;
- cloud sync;
- proactive layer completo.

## Definicao de pronto

Platform Foundation fica pronta quando:

1. runtime independe da Web UI;
2. Web e um segundo cliente de teste usam o mesmo runtime;
3. ambos observam a mesma sessao/contexto;
4. Todd/Morgana preservam identidade e Social Protocol;
5. eventos realtime usam contratos versionados;
6. um device remoto fornece uma capability;
7. Permission Layer autoriza/bloqueia a capability;
8. reconexao preserva continuidade;
9. testes conversacionais existentes continuam verdes.

## Regra final

Nao otimizar para “ter app”, “ter voz” ou “ter mapa” rapidamente. Otimizar para que Web, Desktop, Mobile, Call, Patrulha e Tools sejam apenas formas diferentes de acessar **o mesmo Campanario, a mesma memoria, o mesmo Todd, a mesma Morgana e a mesma presenca continua**.

## Status de implementacao — 2026-08-25

- PF1 Runtime boundary: concluido (ADRs 0050/0051).
- PF2 Event Bus: concluido (ADR 0052).
- PF3 Realtime/API Gateway: concluido (ADR 0053).
- PF4 Device Registry: concluido (ADR 0054), com identidade persistente, capabilities, `/ws/v1/devices` e provenance de lifecycle.
- PF5 Capability / Tool Registry: concluido (ADR 0055), com contratos semanticos, providers transport-neutral, schemas, timeout, provenance e `TOOL_*`.
- PF6 Permission / Trust Layer: concluido (ADR 0056), com pairing, trust persistente, confirmacao, revogacao e audit.
- PF7 Client-independent sessions: concluido (ADR 0057), com attachments multi-client, client/device provenance e continuidade na mesma sessao/contexto.
- PF8 Mobile Readiness: concluido (ADR 0058), com cliente minimo autenticado, E2E HTTP/WebSocket real em loopback e `location.current` fornecida por device.
- PF9 Voice / Call Readiness: concluido (ADR 0059), com Call semantica, contratos VAD/wake/STT/TTS, mesma Conversation Runtime e interruption signal-only.
- F3 Platform Foundation closure: **concluido e congelado no ADR 0060**, com RuntimeTelemetry e E2Es finais.
- F4 Experience / Learning foi concluida no ADR 0061. Proximo gate: **F5 Realtime Presence / Call / Multi-client**.

`device_id` e capability availability nao representam trust ou autorizacao; PF6 continua responsavel por pairing/permissoes/revogacao.

### PF7 implementation note — 2026-08-25

PF7 foi concluido no ADR 0057. O runtime agora separa `client_id`, `device_id` e `agent_id`; clientes mantem attachments temporarios enquanto a `session_id`/contexto continua pertencendo ao Campanario. A Presence UI usa client id estavel, um segundo cliente de teste continua a mesma conversa, e provenance USER persiste no SQLite. `episode_id` e atualmente alias tecnico de `session_id`. PF8 Mobile Readiness foi concluido no ADR 0058; PF9 no ADR 0059; F3 foi congelada no ADR 0060. F4 foi concluida no ADR 0061; o gate atual e F5 Realtime Presence / Call / Multi-client.


## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.
