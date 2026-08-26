# Arquitetura atual — Runtime v2 / PF9 Voice-Call Contracts + Persistent Participants

```text
Clients (Web atual; futuros Desktop/Mobile/Voice)
    |
    v
Realtime/API Gateway (`/api/v1`, `/ws/v1`; legado `/api`/SSE durante migracao)
    |
    v
Hosts (FastAPI lifespan / processo headless; futuros Desktop/Service)
    |
    v
RuntimeHost (um runtime ativo por processo)
    |
    v
CampanarioRuntime (boundary client-independent)
    |- RuntimeState
    |- RuntimeEventBus -> eventos 1.0 / sequence / provenance / replay process-local
    |- SessionManager
    |- DeviceRegistry -> SQLite / hardware capabilities / connection state
    |- CapabilityRegistry -> semantic capabilities / providers / schemas / timeout / provenance
    `- ConversationService / Campanario (sistema)
    |- Chat/Context/Pragmatics
    |- DialogueStateCompiler -> objeto/foco/referente/pedido antes da geracao
    |- Conversation Focus Stack -> estrutura temporaria de topicos
    |- Shared memory/evidence boundary
    |- AgentRouter -> prioridade de fala
    |- ParticipationArbiter -> entrada secundaria opcional
    |    |- Morgana (default primary)
    |    `- Todd
    |- Response Contract Pipeline
    |- Model Runtime (Gemma 3 12B recomendado; substituivel)
    `- SQLite persistence
```

## Separacoes obrigatorias

- sistema != agente;
- prioridade != exclusividade;
- persona != verdade;
- participant decision != conteudo da resposta;
- modelo != comportamento do Campanario;
- UI web != core (desktop futuro pode reutilizar ambos).

## Multi-speaker

Uma mensagem do usuario pode gerar uma ou duas falas. Cada fala passa pela mesma pipeline, e `messages.agent_id` registra o speaker real. O segundo agente entra apenas quando ha convite explicito ou valor conversacional distinto identificado de forma conservadora.

## Platform Foundation / Runtime v2 — estado atual

F2 foi congelada no ADR 0049. PF1a/PF1b estabeleceram runtime, lifecycle e hosting (ADRs 0050/0051). PF2 adicionou `RuntimeEventBus` (ADR 0052). PF3 adicionou o gateway versionado (ADR 0053): `/api/v1` para operacoes e `/ws/v1/events` para observar os mesmos `RuntimeEvent` com replay por `after_sequence`. PF4 adicionou `DeviceRegistry` persistente (ADR 0054), `/ws/v1/devices`, discovery por hardware capability e eventos de lifecycle com provenance. PF5 adiciona `CapabilityRegistry` provider-independent (ADR 0055), schemas, timeout, provenance e eventos `TOOL_*`; `DeviceCapabilityProvider` prova uma capability semantica fornecida por device sem expor provider ao caller. A Presence UI continua no mesmo gateway; `/api` + SSE ficam como compatibilidade de migracao. PF6 adicionou Permission/Trust Layer (ADR 0056). PF7 adicionou client-independent sessions e provenance de client/device (ADR 0057). PF8 adicionou um cliente mobile minimo autenticado (ADR 0058): usa os mesmos `/api/v1` + `/ws/v1`, continua a mesma `session_id`, fornece `location.current` por snapshot de GPS autenticado e reconecta sem criar outro Campanario. PF9 adicionou Call semantica e contratos VAD/wake/STT/TTS/interruption sobre o mesmo Conversation Runtime (ADR 0059), sem audio final.

Importante: PF5 ainda e localhost/process-local. `device_id` e identidade de registro, nao credencial. O gateway nao autoriza expor Campanario em LAN/WAN antes do modelo de pairing/trust/permissoes.


## Dialogue State Compiler — P2.4

Antes de cada geracao de Todd/Morgana, `ChatService` deriva um `DialogueState` deterministico a partir do episodio. Ele separa **interpretacao da conversa** de **geracao da resposta**: objeto raiz, assunto ativo, pedido resolvido, referente imediato, escolhas do usuario, troca anterior relevante, assuntos suspensos, assumptions proibidas e fechamento/ack. Nao e memoria persistente e nao adiciona outra chamada de modelo.

## PF6 — Permission / Trust Layer

PF6 adiciona `TrustManager` e `PermissionPolicy` entre discovery e execucao. Trust de device e persistido separadamente do contrato PF4 de Device; pairing entrega uma credencial uma vez e armazena somente hash. Capabilities continuam provider-independent, mas agora cada permission requirement e avaliado antes do provider e antes de `TOOL_REQUESTED`. Politicas suportam allow/deny, sessao/call e confirmacao one-shot/scoped. Revogacao e security audit sao persistentes. O gateway permanece localhost-only. PF7 foi concluido no ADR 0057, PF8 no ADR 0058, PF9 no ADR 0059 e F3 foi congelada no ADR 0060. F4 foi concluida no ADR 0061; o gate atual e F5 Realtime Presence / Call / Multi-client.


## PF7 — Client-independent sessions

PF7 adiciona `ClientIdentity` e `ClientSessionRegistry`. Sessao/contexto pertencem ao runtime; clientes apenas mantem attachments vivos. A origem de mensagens USER persiste `client_id` e opcional `device_id`, enquanto respostas de Todd/Morgana continuam com `agent_id`. `/ws/v1/events` aceita identidade de client e a Presence UI reutiliza um `client_id` local estavel. `episode_id` e atualmente alias do `session_id` tecnico, sem inventar um segundo container de memoria. PF8 foi concluido no ADR 0058, PF9 no ADR 0059 e F3 foi congelada no ADR 0060. F4 foi concluida no ADR 0061; o gate atual e F5 Realtime Presence / Call / Multi-client.


## PF8 — Mobile Readiness

`MobileReadinessClient` e apenas uma superficie de cliente: pairing/auth vem do PF6, device/capabilities do PF4/PF5, conversa do PF7 e realtime do PF3. Um snapshot GPS autenticado entra no runtime como `location.current`; nao existe ChatService mobile, memoria mobile ou personalidade mobile. O gateway continua localhost-only e o E2E de PF8 usa sockets reais em loopback.


## PF9 — Voice / Call Readiness de contratos

`VoiceCallRegistry` guarda somente lifecycle vivo de Call; a conversa duravel continua na `session_id`. `VoiceCallCoordinator` recebe wake/STT semantico e encaminha apenas `speech_final` para o mesmo `ChatService.stream_turn()`. VAD/wake/STT/TTS sao protocolos de adapter, nao engines acoplados. `/ws/v1/call` prova o contrato e emite `tts_text` com `agent_id`. Interruption/barge-in publica `AGENT_INTERRUPTED`, mas PF9 nao afirma cancelamento real de model/TTS.

## F3 closure — Runtime Telemetry

ADR 0060 congela Runtime v2. `RuntimeTelemetry` pertence ao runtime e registra milestones provider-independent com correlation/session e provenance opcional de agent/client/device. Conversation Runtime marca request/routing/context/generation/first-token/first-usable/turn-finished; o Event Bus alimenta tool-started/tool-finished. O journal e bounded/process-local e possui leitura diagnostica em `/api/v1/runtime/telemetry`. Exportadores duraveis futuros sao adapters, nao parte da semantica conversacional.


## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.


## F5b checkpoint — ADR 0063
Binary PCM media now crosses the existing Call gateway through provider-independent VAD/STT/TTS boundaries and reuses the same conversation/session. F5 remains active until target-host microphone/speaker, real engines, barge-in and latency are proven. Next: F5c host voice integration; F6 remains blocked.

## F5c checkpoint — ADR 0064

Host voice is an edge adapter, not a new cognitive runtime. The Windows baseline is whisper.cpp STT + Windows SAPI TTS + sounddevice physical I/O. The host remains a trusted Device and streams PCM through `/ws/v1/call`; finalized text reuses the shared Conversation Runtime. Per-agent audio provenance survives through `agent_id`. Physical playback can be aborted before the existing cooperative interrupt signal. F5 remains open until target-PC acceptance.
