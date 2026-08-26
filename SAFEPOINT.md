# SAFEPOINT — F4 Experience / Learning Baseline v1

Data do checkpoint: 2026-08-24/25 (sessao atual).

## Motivo

Este checkpoint existe para permitir retomar o projeto em outro chat ou apos falha sem depender da memoria da conversa.


## F2 Freeze / entrada em F3 — 2026-08-25

- Long Call P2.4.4 seed `1787683779`: **253 PASS / 2 WARN / 0 FAIL**, 2 cenarios PASS / 1 WARN / 0 FAIL.
- Revisao humana aceitou os dois WARNs como contextuais: convite a discordar era condicional e nao justificava fabricar coro.
- **Personality / Social / Long-Call Baseline v1 congelada** no ADR 0049.
- F3 Platform Foundation / Runtime v2 liberada como proximo gate.
- PF1a implementado no ADR 0050: `CampanarioRuntime`, `RuntimeState`, `ChatSessionManager`, contratos client-independent e `build_runtime()`.
- PF1b implementado no ADR 0051: lifecycle explicito, `RuntimeHost`, FastAPI lifespan, host headless e API dependente diretamente do runtime.
- `get_chat_service()` permanece apenas para compatibilidade; novos hosts/client adapters usam `get_runtime()`.
- Host pode reiniciar com novo `runtime_id` preservando sessoes persistidas no SQLite.
- PF2 implementado no ADR 0052: `RuntimeEventBus`, contratos de payload/envelope versionados, sequence monotônica, provenance, correlation/causation, subscriptions e replay basico process-local.
- PF3 implementado no ADR 0053: `/api/v1` para request/response e `/ws/v1/events` para eventos PF2 em realtime/replay.
- Presence UI migrada para API v1 + WebSocket; `/api` + SSE legado permanecem durante a migracao.
- Reconexao por `after_sequence` reusa a mesma sessao e replay process-local; speaker provenance/ordem continuam contratos PF2.
- Gateway permanece localhost; nenhuma exposicao LAN/WAN foi liberada.
- Testes locais apos PF3 antes da documentacao final: **352/352**.
- PF4 implementado no ADR 0054: `DeviceRegistry` persistente, migration `0006`, `/ws/v1/devices`, API de discovery e lookup por capability.
- Disconnect/reconnect com o mesmo `device_id` preserva um unico registro e capabilities; restart do runtime preserva o registro no SQLite.
- `DEVICE_CONNECTED/STATE_CHANGED/DISCONNECTED` usam o Event Bus PF2 e provenance de device.
- PF4 nao implementa trust: `device_id` nao e credencial; host continua localhost-only.
- Testes focados PF4: **22/22**.
- Migration `0006` validada com `alembic upgrade head`; `compileall` sem erros.
- Regressao completa PF4: **357/357 PASS**.
- PF5 implementado no ADR 0055: `CapabilityRegistry`, `CapabilityDefinition`, providers transport-neutral, input/output schema, timeout, permission requirements como metadata, availability e provenance.
- `DeviceCapabilityProvider` prova que uma capability semantica pode ser fornecida por um device PF4 e consumida pelo runtime por nome, sem provider hardcoded no caller.
- Execucao publica `TOOL_REQUESTED/STARTED/RESULT/FAILED` no Event Bus PF2.
- API PF5 e somente discovery (`/api/v1/capabilities`); execucao remota generica continua bloqueada ate PF6.
- Testes focados PF5: **22/22 PASS**.
- Regressao completa PF5 antes da documentacao final: **362/362 PASS**.
- PF6 concluido no ADR 0056: Permission / Trust Layer.
- PF7 concluido no ADR 0057: Client-independent sessions, attachments multi-client e provenance persistente de client/device.
- PF8 concluido no ADR 0058: cliente mobile minimo autenticado, mesma sessao/reconnect, sockets reais em loopback e `location.current` de teste.
- PF9 concluido no ADR 0059: Call semantica, contratos VAD/wake/STT/TTS, speech final no mesmo ChatService e interruption signal-only.
- Proximo passo unico: fechar F3 com telemetria runtime + E2Es/ADRs finais; nao implementar audio final antes de Experience/Learning.

## Baseline que nao deve ser perdido

- Campanario = sistema/ambiente;
- Morgana/Todd = IAs/agentes que habitam o sistema e fazem a ponte com o usuario;
- Morgana = primary/default speaker, nao "modo ativo" exclusivo;
- ambos podem participar, complementar, discordar e falar um com o outro;
- Presence UI deve transmitir "entrar numa call com o Campanario";
- usuario expressa intencao; Campanario coordena;
- Gemma 3 12B e baseline recomendado;
- foundation conversacional nao deve ser reaberta sem evidencia de regressao.

## Progresso deste checkpoint

- Personality Core P1 concluido em `src/campanario/agents/profiles.py`;
- Todd/Morgana possuem contrato imutavel com traits, anti-traits, tendencies, boundaries e comportamento por contexto;
- prompt ativo e renderizado do contrato, sem respostas hardcoded de benchmark;
- bateria P2 foi ampliada para 8 eixos pareados (16 quick / 128 mega), com analise heuristica BATE/REVISAR por agente;
- gabarito conceitual registrado em `docs/current/AGENT_PERSONALITY_CONCEPT.md`;
- 263/263 testes locais sem modelo passaram;
- Quick e Mega reais foram executados pelo usuario fora do runtime de recuperacao; o Mega seed `1787660853` teve 128 cenarios, 63 PASS / 65 WARN / 0 FAIL.

## Proximo trabalho

1. fechar F3 Platform Foundation: telemetria runtime e E2Es/ADRs finais;
2. definir eventos/contratos para VAD, wake, STT streaming, TTS, barge-in e interruption sobre o mesmo runtime;
3. preservar AgentRouter, ParticipationArbiter, Social Protocol e Conversation Focus existentes;
4. nao criar segundo ChatService/pipeline cognitivo para voz;
5. manter STT/TTS final, audio background e Patrulha completa bloqueados ate os gates apropriados de Experience/Learning e Call.

## Emergencia / rollback

Se uma nova mudanca quebrar a foundation:

- nao tente corrigir apagando historico;
- compare com este safepoint;
- rode standard E2E com Gemma 3 12B;
- preserve banco do usuario separadamente do codigo;
- prefira rollback do codigo a migration destrutiva;
- leia `RECOVER_FIRST.md` e `PROJECT_STATE.md` antes de qualquer patch.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.

## P2.1 — safepoint da regua pareada contextual

Apos o Mega real, decidiu-se nao maximizar artificialmente a distancia entre Todd e Morgana. A personalidade deve divergir apenas quando a situacao oferece espaco real para perspectiva.

Implementado no harness:
- `CONVERGENCIA_OK`: simplicity, urgency;
- `DIVERGENCIA_ESPERADA`: decision, disagreement, creative;
- `ASSINATURA_LEVE`: uncertainty, technical, social;
- nova secao de relatorio `Comparacao pareada Todd x Morgana`;
- sobreposicao lexical remove tokens do prompt e permanece apenas heuristica de revisao;
- nenhum trait/tendency/persona foi alterado nesta etapa.

Proximo gate exato: rodar Quick real com Gemma 3 12B, revisar pares sob a nova regua e decidir se ha calibracao minima. Depois disso, iniciar teste integrado em um unico episodio com usuario + Todd + Morgana, cobrindo complemento, discordancia util, referencia cruzada e ausencia de overtalk.


## Safepoint — P2.2 Behavioral E2E multiagente integrado

- A régua pareada contextual foi considerada suficiente para avançar sem tuning amplo de `profiles.py`.
- Nova suite real: `agent_integrated`.
- Launcher Windows: `tools/windows/TESTAR_CONVERSA_MULTIAGENTE.bat`.
- A suite usa `ChatService.stream_turn()` e portanto exercita `AgentRouter`, `ParticipationArbiter`, histórico compartilhado e `agent_id` real.
- Bateria: 4 cenários / 7 turnos, cobrindo decisão compartilhada, referência Todd↔Morgana, criatividade, discordância útil e silêncio seletivo.
- Relatórios preservam cada speaker separadamente e incluem resumo de participação.
- Regressão local após implementação: 273/273.
- Próximo gate único: executar `TESTAR_CONVERSA_MULTIAGENTE.bat` com Gemma 3 12B e revisar o transcript. Não iniciar Experience/Learning nem voz antes desse gate.

## Social Protocol v1 — pós Behavioral E2E seed 1787664681

- teste real integrado: 3 PASS / 1 WARN / 0 FAIL; 51 PASS / 2 WARN / 0 FAIL;
- análise: `docs/current/INTEGRATED_E2E_REVIEW_1787664681.md`;
- problemas reais: referência ao outro era confundida com convite de grupo; modelo simulava labels de speakers dentro da própria bubble;
- implementado `src/campanario/agents/social.py`, compartilhado por Todd/Morgana e separado de Personality Core;
- `ParticipationArbiter` agora distingue endereçamento direto de mera menção;
- E2E integrado ampliado para 6 cenários / 10 turnos;
- regressão local: 275/275;
- próximo gate: reexecutar `TESTAR_CONVERSA_MULTIAGENTE.bat` com Gemma 3 12B e validar Social Protocol v1 antes de congelar baseline.

## P2.2c — correções pós Behavioral E2E seed 1787665381

- execução real recebida: 1 PASS / 0 WARN / 5 FAIL; 71 PASS / 0 WARN / 9 FAIL;
- a maioria dos FAILs veio de simulação de labels de speaker (`Todd:`, `Morgana:`) dentro da saída do modelo;
- `ParticipationArbiter` agora bloqueia estruturalmente participação secundária quando há endereçamento direto a um agente, salvo convite explícito de grupo; o semantic arbiter não pode reabrir esse turno;
- Social Protocol v1 exige fidelidade literal a números/nomes/unidades/negações ao corrigir ponto atribuído ao outro agente;
- contexto de cada agente ganhou `CONTRATO DE SAIDA DO SPEAKER`: uma única próxima fala, sem nome próprio como cabeçalho, transcript ou fala em nome de outro participante;
- Personality Core não foi alterado;
- regressão local: 278/278;
- próximo passo: reexecutar `tools/windows/TESTAR_CONVERSA_MULTIAGENTE.bat` com Gemma 3 12B. Se speaker boundaries, reference-vs-invitation e correction fidelity passarem, avançar para Long Call E2E com instrumentação de latência.

## P2.3 Long Call Behavioral E2E

- ultimo integrado real revisado: seed `1787666272`, 5 PASS / 1 FAIL; 53/53 checks avaliados PASS;
- FAIL isolado: Speaker Output Guard abortou Morgana apos repair ainda contaminado;
- recovery adicional: pode extrair apenas segmento explicitamente rotulado como o proprio speaker, nunca fala estrangeira;
- nova suite `agent_long_call`: 3 x 12 turnos;
- latencia de call instrumentada;
- regressao: 288/288;
- gate atual: executar `tools/windows/TESTAR_LONG_CALL.bat`.


## P2.3b Long Context Grounding

- evidencia real: Long Call seed `1787669291`;
- 36 turnos, 222 PASS / 2 WARN / 2 FAIL;
- corrigido vocativo no fim da frase;
- adicionado Working Conversation State temporario para binding de tema/referencia/retomada;
- adicionados checks de grounding no Long Call;
- nenhuma mudanca de Personality Core;
- regressao local 292/292;
- proximo gate: nova execucao de `TESTAR_LONG_CALL.bat`.

## P2.3c — Conversation Focus Stack

Seed real `1787670418`: 230 PASS / 5 WARN / 0 FAIL. O runtime agora deriva frames temporarios de foco dirigidos pelo usuario, preserva tangentes sem promove-las, entende mudanca/retomada/guardado e injeta answer binding. Social Protocol impede autoridade unilateral Todd<->Morgana para silenciar. Personality Core intacto. Regressao: 295/295. Proximo gate: novo `TESTAR_LONG_CALL.bat`.


## P2.3d — Long Call Grounding Hardening / Platform Foundation planejada

- evidencia real: Long Call seed `1787671154`, 36 turnos, 230 PASS / 7 WARN / 2 FAIL;
- falhas reais separadas de personalidade: leak de metadados (`IDENT/frame`), referente imediato fraco, correction arithmetic cross-turn e componentes tecnicos inventados;
- `working_context.py` continua com Focus Stack interno, mas renderiza somente briefing temporario de continuidade sem vocabulario de implementacao;
- follow-ups `isso / mesma pergunta / aterrissa / sequencia curta` recebem pedido anterior e fala anterior quando pertinentes;
- Arithmetic Correction Anchor busca a expressao nos turnos recentes do usuario quando o claim incorreto aparece apenas no turno de correcao;
- Social Protocol nao deve explicar routing/frames/arbiter/logs espontaneamente;
- Long Call E2E endurecido para placeholders tecnicos, sintese de produto e elipses;
- Personality Core nao foi alterado;
- regressao local: 300/300;
- gate unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B;
- **nao iniciar Platform Foundation ainda**;
- apos congelar F2, roadmap canonico segue para **F3 Platform Foundation / Runtime v2**, documentada em `docs/current/PLATFORM_FOUNDATION_HANDOFF.md`;
- F3 deve tornar Web apenas um cliente e criar runtime persistente, Event Bus, Realtime/API Gateway, Device Registry, Capability Registry e Permission/Trust Layer antes de Mobile/Voice/Patrulha em massa;
- `docs/concept/MODO_PATRULHA_V2.md` registra Patrulha como Call persistente em campo, nao nova personalidade.

## P2.3e — Reference Binding + Ambient Call Semantics

- evidencia real: Long Call seed `1787678674`, 36 turnos, 233 PASS / 8 WARN / 0 FAIL;
- problemas remanescentes eram binding pragmatico e semantica de call ambiente, nao Personality Core;
- follow-ups elipticos agora recebem referente concreto derivado do usuario/fala imediatamente anterior;
- sintese/decisao e escolhas de produto recebem ancora funcional explicita;
- contexto proibe inventar subsistemas quando detalhes nao foram fornecidos;
- Social Protocol formaliza presenca continua sem wake/nome obrigatorio por turno e silencio natural durante pensamento em voz alta;
- analise: `docs/current/LONG_CALL_REVIEW_1787678674.md`;
- ADR: `docs/adr/0043-reference-binding-ambient-call-semantics.md`;
- regressao: 305/305;
- gate atual: repetir `tools/windows/TESTAR_LONG_CALL.bat`;
- F3 Platform Foundation continua imediatamente depois do congelamento de F2, nao antes.


## P2.4 — Dialogue State Compiler safepoint

Seed real `1787679961` mostrou 237 PASS / 11 WARN / 1 FAIL: Social Protocol, speaker provenance, arithmetic correction e presence semantics estao maduros, mas a continuidade longa ainda falhava ao reconstruir referencia/função do turno dentro da propria geracao.

Implementado `DialogueStateCompiler` deterministico e tipado. `ChatService` agora compila estado antes de chamar Gemma. O estado inclui objeto raiz, assunto ativo, pedido resolvido, referente imediato, escolhas do usuario, troca anterior, assuntos suspensos, assumptions proibidas e fechamento/ack. Nao existe chamada adicional de LLM nem memoria persistente. Personality Core permanece intacto.

Regressao local: **317/317**.

Proximo gate unico: `tools/windows/TESTAR_LONG_CALL.bat`. Nao iniciar F3 antes da revalidacao/congelamento de F2.

## P2.4.1 — Answer Contract safepoint

Seed de entrada `1787680836`: 244 PASS / 12 WARN / 0 FAIL. O `DialogueStateCompiler` permanece como interpretador deterministico, mas agora `AnswerContract` transforma o estado resolvido em obrigacao final do turno e e anexado por ultimo ao system prompt. Bindings criticos possuem validacao local e um retry maximo; nao ha segunda chamada de LLM para interpretar ou julgar o dialogo. Personality Core nao foi alterado.

Regressao: **323/323**.

Proximo gate unico: `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B. Nao iniciar F3 antes da revalidacao/congelamento F2.


## P2.4.2 — Commitment / Contribution / Embodiment safepoint

Evidencia de entrada: Long Call P2.4.1 seed `1787681697`, 36 turnos, 254 PASS / 2 WARN / 0 FAIL. A revisao humana confirmou que o Answer Contract resolveu coreferencia/binding, mas detectou tres lacunas finais: reabertura de decisao aceita em acknowledgement, repeticao quase literal quando o usuario pediu outra perspectiva e embodiment factual espontaneo em exploracao criativa.

Implementado em `src/campanario/chat/dialogue_state.py`: `CommitmentState`, contrato de acknowledgement curto, `distinct_from` com validacao de sobreposicao somente sob pedido explicito de nao repeticao e Embodiment Boundary conservadora. `ChatService` possui fallback `Entendido.` somente para decisao explicitamente fechada se o retry ainda violar. O arithmetic anchor rejeita linguagem interna de guard. Personality Core permanece intacto e nao ha inferencia adicional.

Regressao local: **329/329**.

Proximo gate unico: `tools/windows/TESTAR_LONG_CALL.bat`. F3 Platform Foundation permanece bloqueada ate decisao de freeze F2.


## P2.4.3 — Freeze Candidate Polish safepoint

Evidencia de entrada: Long Call P2.4.2 seed `1787682411`, 36 turnos, 256 PASS / 3 WARN / 0 FAIL. A revisao humana considerou Dialogue State, Answer Contract, Commitment State, correction fidelity, fechamento e embodiment estaveis. Os pontos restantes sao polish de naturalidade, nao nova arquitetura.

Implementado: limite de sobreposicao mais estrito apenas sob pedido explicito `nao repete`; micro-turno aritmetico dirigido limitado a resposta curta; semantica social de silencio/presenca bloqueia jargon interno de runtime; `valeu/obrigado` nao abrem pergunta; checker Long Call reconhece `prefiro observar / nao e necessario / sem solicitacao`. O WARN de participacao em `discordem ... se precisarem` continua contextual e nao forca overtalk. Personality Core/Participation Arbiter intactos.

Regressao local: **333/333**.

Proximo gate unico: `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B. Se os bindings objetivos permanecerem verdes e so houver WARN contextuais, decidir freeze de F2; nao iniciar F3 antes dessa decisao.


## P2.4.4 — Freeze Gate Fixes safepoint

Evidencia de entrada: Long Call P2.4.3 seed `1787683144`, 36 turnos, 255 PASS / 2 WARN / 2 FAIL. O core permaneceu estavel. Um FAIL veio de check aritmetico lexical apesar de resposta correta por extenso; o segundo veio de repeticao semantica no turno `mesma pergunta ... nao repete`. O fechamento social tambem reciclou a frase anterior.

Implementado: criterio social novo deterministico para contribuicao distinta, arithmetic check por valor equivalente e fechamento `vou trabalhar agora` curto/nao-commitment. Personality Core, Participation Arbiter e Platform Foundation nao foram alterados. Regressao: **335/335**.

Proximo gate unico: `tools/windows/TESTAR_LONG_CALL.bat`. Somente depois decidir freeze F2 e liberar F3 Platform Foundation.


## PF6 Permission / Trust Layer — 2026-08-25

- ADR 0056 aceito; migration 0007 adiciona trust persistente e security audit.
- Pairing gera credencial one-time e persiste somente hash; revogacao invalida imediatamente.
- PermissionPolicy separa availability de authorization com ALLOW/DENY/session/call/confirm/scoped-confirm.
- CapabilityRegistry autoriza antes de iniciar provider/TOOL_REQUESTED.
- Confirmacoes sao one-shot e vinculadas a principal/device/scope.
- API continua localhost-only; PF6 nao autoriza exposicao irrestrita em LAN/WAN.
- Testes focados PF4/PF5/PF6/gateway: 19/19 PASS; regressao completa: 367/367 PASS; migration 0001->0007 PASS.
- Proximo gate unico: PF7 Client-independent sessions.

## PF7 Client-independent sessions — 2026-08-25

- ADR 0057 define sessao como recurso do Campanario e client como attachment temporario.
- `client_id`, `device_id` e `agent_id` sao identidades separadas.
- Presence UI e segundo cliente podem compartilhar a mesma `session_id`; reconnect nao duplica contexto.
- provenance USER persiste no SQLite pela migration `0008`; speaker provenance de Todd/Morgana permanece agent-owned.
- testes focados PF7 e regressao completa devem estar verdes antes de PF8.
- Proximo gate unico: PF8 Mobile Readiness.

## Validacao PF7 — 2026-08-25

PF7 esta fechado no ADR 0057. PC/Web e segundo cliente compartilham a mesma sessao/contexto, realtime e provenance sem duplicar Todd/Morgana ou memoria. Testes focados: **36/36 PASS**; regressao completa: **373/373 PASS**; migration `0001 -> 0008`: PASS; `compileall`: PASS. Proximo gate unico: **PF8 Mobile Readiness**.


## Validacao PF8 — 2026-08-25

PF8 prova um cliente mobile minimo autenticado reutilizando o mesmo runtime, sessao, Todd/Morgana, Event Bus, Device Registry, Capability Registry e Permission Layer. O E2E inclui transporte HTTP/WebSocket real em loopback e `location.current` fornecida pelo device. Testes focados PF3-PF8: **29/29 PASS**; regressao completa: **377/377 PASS**; Alembic `0001 -> 0008`: PASS; `compileall`: PASS. Nenhum app Android/iOS final ou exposicao LAN/WAN foi implementado. Proximo gate: **PF9 Voice / Call Readiness de contratos**.


## Validacao PF9 — 2026-08-25

PF9 fecha os contratos de voz/call sem engine de audio final. Wake e speech parcial sao eventos operacionais; speech final causa o mesmo `USER_TEXT` e a mesma pipeline de Todd/Morgana. Device precisa de trust + microphone + `microphone.listen` em call. TTS fica como diretiva textual por agent_id e interruption e signal-only. ADR 0059. Testes PF9 focados: **5/5 PASS**; regressao completa: **382/382 PASS**; Alembic `0001 -> 0008`: PASS; `compileall`: PASS. Proximo gate unico: **F3 Platform Foundation closure — telemetria + E2Es/ADRs finais**.

## Safepoint F3 CLOSED — 2026-08-25

Platform Foundation / Runtime v2 foi congelada no ADR 0060. Telemetria arquitetural e E2Es finais estao incorporados. F4 foi concluida no ADR 0061. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**. Nao saltar para Patrulha completa ou F6.


## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.

## F5 checkpoint — ADR 0062
Do not call F5 frozen yet. Orchestration-level presence/call/handoff is green; real media VAD/STT/TTS/background audio E2E remains the next gate inside F5.

## F5b Voice Media Runtime checkpoint

ADR 0063 accepted. Binary PCM -> VAD/STT adapter -> shared Conversation Runtime -> agent-provenanced TTS audio is implemented and regression is 399 PASS. F5 remains OPEN because physical microphone/speaker plus production STT/TTS engines and measured host/mobile E2E are not yet proven. Next gate: F5c host voice integration; do not advance to F6.

## F5c Host Voice Integration checkpoint — ADR 0064

F5c implementation is complete: local whisper.cpp STT, Windows SAPI TTS, sounddevice host microphone/speaker client, authenticated Device presence, physical playback abort before barge-in, and voice latency telemetry are wired to the existing Call/Conversation Runtime. Automated focused gate: 14 PASS; full regression: 403 PASS. The build container cannot certify the target PC microphone/speaker/installed engines. **Next gate: F5c Host Acceptance / Voice Ready Gate on the target Windows PC. F6 remains blocked.**

## F5c.1 — STT portugues / voice capture stabilization

O primeiro E2E fisico F5c provou a volta completa de audio, mas mostrou transcricao pt-BR insuficiente e turnos fantasma de nao-fala. ADR 0065 endurece a fronteira STT sem alterar o runtime cognitivo: `-l pt` agora e testado/observavel, prompt pt-BR curto, rejeicao de modelo `.en.bin` incompatível, filtro de anotacoes puras de ruido, gate minimo de fala e launcher preservando `voice-host`. `tools/windows` foi limpo; regressao historica foi movida, nao apagada. F5 permanece aberta ate revalidacao fisica no PC alvo.


## F5c.2 — Voice Runtime Wiring
The Windows launcher now auto-wires whisper.cpp + Windows SAPI into the server-side VoiceMediaRuntime when local voice assets are present. This fixes the physical E2E failure where the Host Voice websocket connected successfully but raw audio hit `UnconfiguredStt` inside the API/runtime process. `.env.example` remains conservative; machine-local voice assets are detected at launch.

## F5c.3 — Host Voice Runtime Readiness

ADR 0066 corrige o crash fisico `RuntimeError: STT adapter is not configured`. A configuracao de voz deixa de depender apenas do launcher: o runtime pode descobrir assets locais existentes, e Call sem STT/TTS retorna erro explicito sem derrubar ASGI/WebSocket. Regressao: **412 PASS**. Nao avancar para F6; repetir Host Acceptance no PC alvo.


## F5c.4 — Host Voice readiness fail-fast
O E2E fisico confirmou que o runtime estava saudavel, mas sem modelo STT multilingue carregado; o cliente continuava enviando PCM e recebendo `voice_stt_not_configured` em loop. F5c.4 torna esse erro terminal no Host Voice e adiciona `tools/windows/PREPARAR_VOZ_F5C.bat`, que valida whisper-cli e instala/valida `models/ggml-small.bin`. O gate F5 continua aberto ate o E2E fisico pt-BR passar.

## FREEZE — F5c.4 physical voice pipeline alive, pt-BR quality pending — 2026-08-25

ADR 0067 is the current recovery point. Physical Windows evidence proves the complete voice/runtime round trip, but not acceptable recognition quality. Spoken `Campanario, voce esta ai?` became `O Brasil e o maior.` before the shared Conversation Runtime; Morgana then answered that corrupted text normally. This isolates the next work to STT/capture quality, not AgentRouter, personalities, memory, API, WebSocket or session architecture.

Resume rule: **do not advance to F6**. First verify actual multilingual Whisper model and effective Portuguese language flag on the target PC; then run a short pt-BR acceptance set and tune VAD/capture only if needed. Keep F5c.4 fail-fast behavior for missing STT. Local `voice/` binaries and `models/` are reinstallable deployment assets; recovery must document them but must not assume they survive a format.

## F5c.4 maintenance refactor — E2E scenario modularization

Sem avanço de gate: F5 continua aberta e F6 bloqueada. O monolito `src/campanario/e2e/scenarios.py` foi dividido em fachada de roteamento, suites de agentes, suites standard/full e utilitarios compartilhados. A API publica `build_scenarios()` e a geração seeded foram preservadas. Equivalencia antes/depois foi verificada em 4 seeds x 8 suites com o mesmo digest SHA-256 `74970171844034c5f06b3d97e2b476d96d7d0283f5c601481c1b44d03c13ce7f`. A regressao completa do pacote recebido ficou em 411 PASS / 2 FAIL; os dois FAILs sao do estado de entrada F5c (`PREPARAR_VOZ_F5C.bat` ausente e launcher sem marcador esperado pelo teste), nao desta refatoracao. `__pycache__`/`.pyc` foram removidos do pacote de handoff.

## 2026-08-26 — F5c.4 maintenance safepoint: external Whisper models

- Gate inalterado: F5 OPEN / F6 BLOCKED.
- Pesos Whisper foram desacoplados do pacote do projeto via `CAMPANARIO_VOICE_MODELS_DIR`.
- Default Windows: `%LOCALAPPDATA%\Campanario\models`; override exato: `CAMPANARIO_VOICE_WHISPER_MODEL_PATH`.
- `PREPARAR_VOZ_F5C.bat` instala `ggml-small.bin` fora do projeto; layouts antigos permanecem como fallback.
- Evidencia automatizada: 15/15 Host Voice PASS; 415/415 regressao completa PASS; compileall PASS.

## 2026-08-26 — F5c.5 safepoint: physical pt-BR recognition boundary

ADR 0068 implementa o próximo trabalho autorizado por ADR 0067 sem fechar F5. O gateway de Call não descarta mais frames de baixa energia dentro de uma frase: usa pre-roll de 4 frames, preserva pausas/sílabas após o início e finaliza após 12 frames de silêncio. O launcher/runtime escolhem o maior modelo Whisper multilíngue disponível por padrão para a aceitação física pt-BR. Nenhum texto é reescrito depois do STT e nenhuma persona foi alterada. Evidência: 21/21 focados PASS; 418/418 regressão completa PASS. **F5 OPEN; F6 BLOCKED.** Próximo passo: E2E físico pt-BR no Windows alvo.

## 2026-08-26 — F5c.6 safepoint: voice addressing and presence semantics

ADR 0069 registra a correcao posterior ao teste fisico F5c.5. Wake agora aceita `Campanário` acentuado, probes de presenca recebem resposta curta orientada pelo runtime e enderecamento explicito de Todd+Morgana em voz isola o segundo agente da resposta recem-gerada pelo primeiro, preservando a fala original como input comum. Personality Core e STT permanecem intactos. Evidencia: 38/38 focados PASS; 422/422 regressao PASS; compileall PASS. **F5 OPEN; F6 BLOCKED.**

## F5c.7 — Physical STT echo / segmentation hardening — ADR 0070 — 2026-08-26

O teste fisico F5c.6 mostrou que frases repetidas ainda podiam virar segmentos quebrados e transcricoes alheias. A causa de fronteira mais forte era dupla: o Host Voice enviava PCM do microfone ao STT enquanto SAPI tocava no alto-falante, permitindo eco como fala do usuario, e o fim de frase de ~480 ms era curto para pausas naturais apos `Campanario`. ADR 0070 suprime PCM durante playback salvo barge-in confirmado com pre-roll local, aumenta hangover para ~960 ms, pre-roll para 6 frames e fala minima para 300 ms, reduz o prompt Whisper a nomes proprios e fixa decoding deterministico (temperature 0, beam 5, no-fallback, suppress-nst, no-speech 0.50). Nao ha correcao semantica pos-STT. Evidencia automatizada: **27/27 focados PASS; 424/424 regressao completa PASS**. **F5 permanece OPEN; F6 permanece BLOCKED** ate nova validacao fisica pt-BR.

## 2026-08-26 — F5c.8 safepoint: complete utterance + stale response isolation

ADR 0071 is the current safepoint. Physical evidence showed sentence splitting and delayed answers from obsolete turns. Host Voice now waits 45 silence frames (~1.8 s) before finalizing, propagates an explicit per-turn correlation id, cancels a superseded running response, and filters stale agent events before TTS. No phrase-specific STT rewrite and no personality change. Evidence: **35/35 focused PASS; 424/424 regression PASS; compileall PASS**. **F5 OPEN / F6 BLOCKED.**

## 2026-08-26 — F5c.9 safepoint: adjustable TTS speed

Windows SAPI playback rate is now an explicit F5 host control. Defaults are Todd=4 and Morgana=3; users can run `tools/windows/AJUSTAR_VELOCIDADE_VOZ.bat` to persist presets from calm through turbo, or set `CAMPANARIO_VOICE_TODD_RATE` / `CAMPANARIO_VOICE_MORGANA_RATE` manually in the supported `-10..+10` range. No content/personality/STT change. Evidence: **21/21 focused PASS; 426/426 regression PASS**. **F5 OPEN / F6 BLOCKED.**

## 2026-08-26 — F5c.10 safepoint: utterance aggregation + natural voice turn

ADR 0072 é o ponto de recuperação atual. Fragmentos STT com forte sinal de continuação não viram turnos imediatamente; ficam até 1200 ms pendentes e, se houver continuação, o áudio original é recombinado e retranscrito. O canal de voz usa entrega curta/conversacional e barge-in mais responsivo, mas Personality Core não foi alterado. Evidência automatizada: **25/25 Host Voice PASS; 430/430 regressão PASS; compileall PASS**. **F5 OPEN / F6 BLOCKED.** Próximo passo: teste físico espontâneo de frases longas/pausadas + interrupção durante TTS.

## Safepoint F5c.11 — 2026-08-26

- Gate: F5 aberto; F6 bloqueado.
- Mudança: fronteira de saída falada contínua, sanitizador TTS visual-only e fila serial/cancelável.
- Invariantes: texto canônico/histórico não é reescrito; Personality Core intacto; modelos externos continuam fora do ZIP.
- Testes: 41/41 focados; 434/434 full regression; compileall PASS.

## Safepoint — Personality turn-local activation — ADR 0073 — 2026-08-26

- F5 Call continua OPEN e deliberadamente pausada no F5c.11; F6 permanece BLOCKED.
- Personality Core canonico permanece em `src/campanario/agents/profiles.py`.
- Nova camada: `src/campanario/agents/personality_application.py`.
- Ela deriva uma lente compacta a partir de `ConversationTurnInterpreter` e do agente; nao possui fatos, memoria, tools ou respostas concretas.
- Ordem de prompt: contexto/dialogue state -> profile/social -> participation/voice note -> personalidade ativa do turno -> AnswerContract -> anchors factuais.
- Factual simples exige assinatura leve; social/technical/creative/discussion ativam diferencas de prioridade sem caricatura.
- Voice guidance preserva a personalidade individual e continua controlando apenas entrega falada/proporcionalidade.
- Testes: 55/55 focados; 438/438 full regression; compileall PASS.
- Proxima validacao: Behavioral E2E Todd x Morgana em prompts novos + revisao humana. Nao congelar novo baseline so por testes unitarios.

## Safepoint — ADR 0074 Human Conversation Baseline — 2026-08-26

- Personality Core continua o baseline congelado; ADR 0073 segue como camada de ativação por turno.
- Novo teste de qualidade: `tools/windows/TESTAR_CONVERSA_HUMANA.bat`.
- Full: `agent_human_baseline` = 10 episódios / 80 turnos.
- Quick: `agent_human_quick` = 5 episódios / 40 turnos.
- Quatro temas individuais são Todd × Morgana com prompts literalmente iguais; duas salas usam runtime multiagente real.
- `blind_review.md` esconde identidades até o gabarito e é a primeira leitura recomendada.
- Naturalidade não é declarada automaticamente por heurística.
- Evidência de código: 61/61 focados, 442/442 full regression, compileall PASS.
- F5 call permanece pausada/não aprovada; F6 bloqueado.

## Freeze 2026-08-26

Desenvolvimento ativo pausado. A frente experimental posterior ao ADR 0074 foi removida deste pacote. Consulte `FREEZE_BASELINE.md`. F5 permanece OPEN/pausado e F6 BLOCKED.
