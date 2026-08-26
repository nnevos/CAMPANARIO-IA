# PROJECT STATE — F4 Experience / Learning Baseline v1

## Status atual

F2 esta **CONCLUIDA E CONGELADA** como Personality / Social / Long-Call Baseline v1 (ADR 0049). A revalidacao final P2.4.4 com Gemma 3 12B, seed `1787683779`, terminou com 253 PASS / 2 WARN / 0 FAIL; os WARNs criativos foram aceitos como contextuais em revisao humana. F3 foi congelada no ADR 0060 e F4 Experience / Learning foi concluida no ADR 0061. O gate ativo agora e **F5 Realtime Presence / Call / Multi-client**.

PF1a + PF1b + PF2 + PF3 + PF4 + PF5 + PF6 + PF7 + PF8 + PF9 estao implementados. `CampanarioRuntime` e o boundary client-independent; `RuntimeHost` possui lifecycle explicito; FastAPI/headless sao hosts. PF2 adicionou `RuntimeEventBus` versionado. PF3 adicionou `/api/v1` e `/ws/v1/events`. PF4 adicionou `DeviceRegistry` persistente em SQLite, `/ws/v1/devices`, lookup por hardware capability e lifecycle de device no Event Bus. PF5 adicionou `CapabilityRegistry` provider-independent, providers transport-neutral, schemas, timeout, availability/provenance e eventos `TOOL_*`. `device_id` continua separado de `client_id` e `agent_id`. PF6 implementa trust/autorizacao; PF7 implementa attachments multi-client e provenance persistente de origem; PF8 prova um cliente mobile minimo autenticado sobre os mesmos contratos, inclusive `location.current` de teste. PF9 prova Call semantica e contratos VAD/wake/STT/TTS/interruption sobre a mesma Conversation Runtime, sem audio final. O gateway continua localhost-only ate um gate remoto apropriado.

## O que ja foi concluido

### Foundation

- runtime/model provider separado e model-portable;
- Response Contract Pipeline;
- pragmatica/continuation semantics;
- context provenance e isolamento creative->factual;
- E2E standard/mega e model bakeoff;
- Gemma 3 12B escolhido como baseline recomendado apos superar Llama 3 nos testes;
- reorganizacao estrutural pre-agents;
- standard real pos-organizacao: 11/11 cenarios, 64/64 checks.

### Sistema/agentes

- Campanario separado conceitualmente de agentes;
- Morgana = default primary speaker;
- Todd + Morgana = participantes persistentes;
- `AgentRouter` para prioridade/endereco;
- `ParticipationArbiter` para entrada secundaria conservadora;
- `messages.agent_id` registra quem falou;
- `chat_sessions.primary_agent_id` guarda prioridade, nao exclusividade;
- multi-speaker SSE/API/UI.

### UI/UX

- Presence UI v1.3.0;
- experiencia orientada a ambiente/call, nao chatbot convencional;
- sem "Modo Morgana" / "Modo Todd" como UX principal;
- agentes aparecem por participacao, nao por selecao obrigatoria;
- estados conceituais PRESENTE / ATENTO / ENGAJADO preparados visualmente;
- voz ainda e apenas arquitetura/UX preparada, nao funcionalidade simulada.

## Automacao de testes adicionada neste safepoint

- `TESTAR_AGENTES.bat`: invariantes basicas de identidade/factualidade;
- `TESTAR_PERSONALIDADES.bat`: 8 eixos conceituais pareados, 16 cenarios quick;
- `TESTAR_PERSONALIDADES_MEGA.bat`: 8 lotes da bateria completa, 128 cenarios;
- relatorio agrega checks heurísticos `CONCEITO:<eixo>` em BATE/REVISAR por agente;
- checks conceituais sao WARN-only e nao exigem resposta exata; invariantes duras continuam separadas;
- diferenca fina de personalidade continua exigindo revisao humana do transcript.

## Personality Foundation — progresso

- PersonalityCore estruturado e Personality Core intacto desde a calibracao conceitual;
- Quick/Mega reais executados com Gemma 3 12B e regua pareada contextual;
- Behavioral E2E multiagente + Social Protocol v1 executados e endurecidos;
- Long Call E2E foi congelado em P2.4.4 seed `1787683779`, com 253 PASS / 2 WARN / 0 FAIL e revisao humana dos WARNs contextuais;
- Personality / Social / Long-Call Baseline v1 permanece congelada pelo ADR 0049 durante PF7.

## O que NAO esta pronto

- aprendizado/evolucao persistente;
- memoria relacional/experiencial de agente;
- RAG/web/tools;
- wake word;
- STT/TTS;
- vozes diferentes;
- barge-in;
- call persistente/background audio;
- proactive layer.

## Gate atual unico

**F3 Platform Foundation / Runtime v2 — PF9 concluido; proximo slice: F3 closure (telemetria runtime + E2Es/ADRs finais).**

F2 nao deve ser recalibrada durante trabalho de plataforma sem evidencia explicita de regressao. PF1 fechou runtime/hosting; PF2 fechou event model; PF3 fechou o gateway versionado; PF4 fechou identidade/capabilities fisicas de devices e reconnect persistente; PF5 fechou capability/tool registry provider-independent. PF6 fechou pairing/trust/policy/revogacao. PF7 fechou client-independent sessions. PF8 fechou Mobile Readiness. PF9 fechou Voice / Call Readiness de contratos sem segundo pipeline cognitivo. F3 foi congelada no ADR 0060 e F4 Experience / Learning no ADR 0061. O gate atual e F5 Realtime Presence / Call / Multi-client.

## Modelo recomendado

`gemma3:12b`. Continua sendo configuracao substituivel.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.

## P2 — revisão do Mega seed 1787660853

- execução real recebida: 128 cenários, 63 PASS / 65 WARN / 0 FAIL;
- revisão registrada em `docs/current/PERSONALITY_MEGA_REVIEW_1787660853.md`;
- identificado bug de agregação: um único WARN lexical contaminava o eixo inteiro no Mega;
- agregador corrigido para preservar frequência: BATE >=75%, MISTO >=50%, REVISAR <50%;
- diagnóstico humano: factualidade/invariantes preservadas, mas Todd/Morgana ainda convergem para uma voz genérica de assistente em disagreement, urgency, technical e creative;
- personas ainda NÃO foram alteradas com base em palavras do benchmark;
- regressão local após correção do avaliador: 265/265.

### Decisão após a revisão do Mega

Não calibrar `profiles.py` ainda. Primeiro validar a régua pareada contextual P2.1 em um novo Quick real. Só alterar traits/tendencies se o transcript confirmar convergência indevida nos eixos em que divergência é realmente esperada.

## P2.1 — avaliacao pareada contextual implementada

- nenhuma persona foi alterada nesta etapa;
- eixos classificados por expectativa de diferenca: `CONVERGENCIA_OK`, `DIVERGENCIA_ESPERADA`, `ASSINATURA_LEVE`;
- convergencia natural nao e mais tratada como defeito em `urgency`/`simplicity`;
- `decision`/`disagreement`/`creative` recebem uma analise pareada adicional para detectar convergencia excessiva do modelo-base;
- `uncertainty`/`technical`/`social` sao observados sem obrigacao de contraste forte;
- comparacao remove vocabulario do prompt antes de calcular sobreposicao de superficie;
- a metrica continua heuristica/WARN-only e nao substitui leitura humana;
- proximo passo: Quick real com Gemma 3 12B usando esta nova regua; depois teste integrado usuario + Todd + Morgana.

## P2.2 — Behavioral E2E multiagente integrado implementado

- suite nova: `agent_integrated`;
- launcher: `tools/windows/TESTAR_CONVERSA_MULTIAGENTE.bat`;
- 4 cenarios / 7 turnos no mesmo episodio por cenario;
- usa `ChatService.stream_turn()` real, `AgentRouter`, `ParticipationArbiter`, historico compartilhado e speaker provenance;
- cobre complemento, replica direcionada entre agentes, criatividade compartilhada, discordancia util e silencio seletivo;
- relatorio preserva falas separadas por agente e resume participacao;
- checks de forma incluem ambos presentes quando convidados, prioridade direta, nao duplicacao, proporcionalidade e ausencia de overtalk;
- proximo passo: execucao real com Gemma 3 12B e revisao humana do transcript; nenhuma calibracao de persona antes dessa evidencia.

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

## Marco futuro registrado — Memory Go-Live / Clean Start

O roadmap de Production Readiness (F7) possui um `Memory Go-Live Readiness Gate`. Ele deve ocorrer somente depois de Personality Baseline v1 + Experience/Learning funcional + continuidade/anti-drift validados + Long Call/Behavioral E2E textual estavel.

Nesse gate, a memoria acumulada por desenvolvimento/testes sera inspecionada e apagada antes do uso real. Personality Core, schemas, codigo, contratos versionados e fixtures isoladas permanecem. Depois do reset sera criado `Usage Learning Baseline v1`; novas conversas a partir dali passam a constituir a memoria relacional/experiencial real dos agentes.

Este marco e futuro e NAO altera o gate atual P2.3d.

## P2.2d — Speaker Output Guard + Correction Anchor

- seed real `1787665713`: 3 PASS / 0 WARN / 3 FAIL; 72 PASS / 0 WARN / 4 FAIL;
- referencia-vs-convite e silencio seletivo confirmados;
- speaker labels continuam sendo gerados pelo Gemma em parte dos turnos;
- `src/campanario/agents/output.py` agora separa normalizacao segura do proprio header de violacao real de transcript;
- foreign/remaining speaker labels geram uma unica regeneracao e falham fechado se persistirem;
- correcoes aritmeticas explicitas usam anchor deterministico generico para impedir mutacao de operandos;
- Personality Core intacto;
- regressao: 283/283;
- proximo gate: repetir `TESTAR_CONVERSA_MULTIAGENTE.bat`; aprovado isso, Long Call E2E com TTFT/gap/tempo por speaker/tempo total.

## P2.3 — Long Call Behavioral E2E implementado

- `agent_long_call`: 3 episodios persistentes / 36 turnos;
- launcher `tools/windows/TESTAR_LONG_CALL.bat`;
- instrumentacao de TTFR, geracao por speaker, gap do segundo agente e tempo total;
- resumo de latencia com media, mediana, p95, max e solo vs multiagente;
- recovery de speaker output refinado apos o seed real `1787666272`;
- Personality Core nao foi alterado;
- regressao local: 288/288;
- proximo passo: execucao real do Long Call com `gemma3:12b`.

## P2.3b — Long Context Grounding apos seed 1787669291

- Long Call real: 36 turnos; 222 PASS / 2 WARN / 2 FAIL;
- dois FAILs objetivos: vocativo no fim da frase nao era reconhecido;
- transcript revelou perda de binding semantico em retomadas/elipses apesar do historico bruto existir;
- analise: `docs/current/LONG_CALL_REVIEW_1787669291.md`;
- `AgentRouter`/`ParticipationArbiter` agora reconhecem vocativo inicial e final sem converter mencao interna em endereco;
- novo `Working Conversation State` temporario e deterministico ancora abertura, turnos recentes, ancoras relacionadas, ultima fala e pedido atual;
- working state nao e memoria aprendida e nao adiciona uma segunda inferencia;
- output normaliza autoidentificacao estreita `Todd aqui.` / `Morgana aqui.`;
- Long Call ganhou checks de continuidade semantica para arquitetura, latencia, elipse de UI, sintese criativa e referencia social;
- Personality Core e Social Protocol nao foram recalibrados;
- regressao local: 292/292;
- proximo passo: reexecutar `TESTAR_LONG_CALL.bat` com Gemma 3 12B e revisar os novos checks de grounding + latencia.

## P2.3c — Conversation Focus Stack apos seed 1787670418

- Long Call real: 36 turnos; 230 PASS / 5 WARN / 0 FAIL;
- P2.3b confirmou vocativo final, correction anchor, speaker provenance e melhora de latencia;
- problema remanescente: tangentes do assistant podiam dominar elipses/sinteses e respostas podiam ficar no tema sem responder a funcao exata;
- novo `ConversationFocusStack` em `src/campanario/chat/working_context.py`: frame raiz, frame ativo, frames suspensos/guardados e movimentos `mudando`/`voltando`/`guarda`;
- foco e dirigido por mensagens do usuario; tangente de agente nao vira foco automaticamente;
- nota de contexto explicita `answer binding`;
- Social Protocol: Todd/Morgana nao tem autoridade para silenciar um ao outro;
- Long Call ganhou checks para autoridade social, resposta ao silencio e vazamento de tangente de memoria;
- ADR: `docs/adr/0041-conversation-focus-stack.md`;
- Personality Core intacto;
- regressao local: 295/295;
- proximo passo: reexecutar `TESTAR_LONG_CALL.bat` com Gemma 3 12B.

## P2.3d — Long Call Grounding Hardening apos seed 1787671154

- Long Call real: 36 turnos; 230 PASS / 7 WARN / 2 FAIL;
- analise: `docs/current/LONG_CALL_REVIEW_1787671154.md`;
- note de grounding nao expõe mais `frame/stack/answer binding` ao modelo;
- referentes imediatos recebem reforco do pedido/fala anteriores;
- correction anchor atravessa turnos para preservar aritmetica atribuida;
- grounding proibe componentes/modulos/integracoes/requisitos inventados;
- Social Protocol proibe especular espontaneamente sobre mecanismos internos do Campanario;
- Long Call checks endurecidos para placeholders e sintese de produto;
- Personality Core intacto;
- regressao local: 300/300;
- proximo gate: nova execucao de `TESTAR_LONG_CALL.bat`.

## Direcao futura registrada — Platform Foundation / Runtime v2

Depois de congelar F2, a proxima grande fase e F3 Platform Foundation. A Web UI passa a ser um cliente do mesmo runtime persistente que futuramente atendera Desktop, Mobile, Voice/Call, Tools e Modo Patrulha. Handoff detalhado: `docs/current/PLATFORM_FOUNDATION_HANDOFF.md`. Conceito de Patrulha: `docs/concept/MODO_PATRULHA_V2.md`. Nao implementar esta fase antes da aprovacao do Long Call atual.


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


## P2.4 — Dialogue State Compiler

- seed de entrada `1787679961`: 237 PASS / 11 WARN / 1 FAIL;
- runtime novo: `src/campanario/chat/dialogue_state.py`;
- `ChatService` usa `DialogueStateCompiler` antes da geracao;
- Focus Stack continua como estrutura interna de topicos, mas nao e mais o briefing principal do modelo;
- estado compilado separa interpretacao da conversa de geracao da resposta;
- nenhuma alteracao em `profiles.py`;
- nenhuma segunda inferencia;
- Long Call E2E endurecido para perda de referente, metalinguagem de papeis, resumo vazio e despedida com nova tarefa;
- regressao local: **317/317**;
- gate unico: reexecutar Long Call; somente depois avaliar congelamento F2 e inicio F3 Platform Foundation.

## P2.4.1 — Answer Contract

- evidencia de entrada: Long Call seed `1787680836`, 36 turnos, 244 PASS / 12 WARN / 0 FAIL;
- P2.4 confirmou que `DialogueState` tipado ajuda, mas o modelo ainda podia trata-lo como briefing e ignorar o binding exato;
- novo `AnswerContract` e derivado deterministicamente do `DialogueState` e anexado por ultimo no system prompt, depois de persona/Social Protocol/speaker contract/participation note;
- contrato contem pedido exato, sujeito/referente resolvido, material relevante, ancoras leves, desvios proibidos, no-clarification e no-new-question quando aplicavel;
- contratos criticos sao validados localmente e recebem no maximo uma regeneracao se o modelo pedir contexto ja disponivel, perder o sujeito, entrar em metatopico proibido ou abrir pergunta em fechamento;
- nenhuma segunda inferencia para interpretar/julgar a conversa; nenhuma memoria persistente; Personality Core intacto;
- Long Call E2E endurecido: binding objetivo passa a FAIL; participacao criativa/segundo speaker continua contextual/WARN;
- ADR: `docs/adr/0045-answer-contract-binding.md`;
- review: `docs/current/LONG_CALL_REVIEW_1787680836.md`;
- regressao local: **323/323**;
- gate atual unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat`; F3 Platform Foundation continua bloqueada ate decisao de freeze F2.


## P2.4.2 — Conversational Commitment & Contribution Contract

- entrada: seed `1787681697`, 254 PASS / 2 WARN / 0 FAIL;
- `CommitmentState` + Answer Contract impedem reabertura silenciosa de decisao explicitamente aceita;
- acknowledgement de decisao fechada e curto; se retry ainda violar, fallback seguro `Entendido.`;
- `distinct_from` mede sobreposicao da contribuicao quando o usuario pede explicitamente `nao repete`;
- Embodiment Boundary separa metafora/atmosfera de afirmacao factual de corpo/acao dos agentes;
- correction anchor nao pode vazar linguagem do mecanismo de validacao;
- E2E ganhou checks de compromisso fechado e invisibilidade do guard;
- regressao local: **329/329**;
- gate unico: nova execucao de `TESTAR_LONG_CALL.bat`; somente depois avaliar freeze F2 e inicio de F3.


## P2.4.3 — Freeze Candidate Polish

- evidencia de entrada: Long Call seed `1787682411`, 36 turnos, 256 PASS / 3 WARN / 0 FAIL;
- P2.4.2 confirmou compromisso fechado, binding longo, arithmetic fidelity e embodiment boundary;
- WARN de `discordem ... se precisarem` permanece contextual e nao forca segundo speaker;
- `distinct_from` foi apertado somente sob pedido explicito `nao repete`;
- semantica social rejeita jargon interno do runtime quando uma fala natural basta;
- aritmetica trivial dirigida recebe resposta curta; acknowledgements simples nao abrem novo assunto;
- checker Long Call aceita formulacoes naturais equivalentes de silencio;
- Personality Core e Participation Arbiter intactos; nenhuma inferencia adicional;
- ADR: `docs/adr/0047-freeze-candidate-naturality-polish.md`;
- review: `docs/current/LONG_CALL_REVIEW_1787682411.md`;
- regressao local: **333/333**;
- gate unico: uma ultima execucao de `tools/windows/TESTAR_LONG_CALL.bat`; so depois decidir freeze F2 e liberar F3.


## P2.4.4 — Freeze Gate Fixes

- seed de entrada `1787683144`: 255 PASS / 2 WARN / 2 FAIL;
- arithmetic check do Long Call aceita `144` numerico ou `cento e quarenta e quatro`;
- `AnswerContract` ganha criterio social novo obrigatorio em `mesma pergunta ... nao repete`;
- retry que ainda falha nesse contrato usa fallback social estreito em vez de persistir a primeira resposta invalida;
- despedida de trabalho nao e tratada como nova decisao aceita e fica limitada a fechamento curto;
- regressao local: **335/335**;
- gate unico: reexecutar Long Call e decidir freeze F2.


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

- `ClientIdentity` (`client_id`, `device_id?`) separado de speaker `agent_id`.
- attachments de client sao process-local; sessao/contexto e historico continuam no runtime/SQLite.
- dois clientes de teste entram na mesma `session_id`, observam o mesmo realtime e continuam o mesmo model context.
- reconnect preserva sessao e cria somente um novo attachment de transporte.
- mensagens USER persistem `client_id`/`device_id` via migration `0008`; eventos USER_TEXT carregam client provenance.
- Presence UI usa `client_id` estavel; `episode_id` e alias atual do `session_id`.
- checkpoint historico PF7: o gate seguinte era PF8; PF8 agora esta concluido e o gate atual esta no topo deste arquivo.

## Validacao PF7 — 2026-08-25

- testes focados PF7 + runtime/gateway/security: **36/36 PASS**;
- regressao completa final: **373/373 PASS**;
- migration `0001 -> 0008`: PASS;
- `compileall`: PASS;
- checkpoint historico PF7: o gate seguinte era PF8; PF8 agora esta concluido e o gate atual esta no topo deste arquivo.


## PF8 Mobile Readiness — 2026-08-25

- ADR 0058; `MobileReadinessClient` sem UI/platform SDK.
- pairing/autenticacao PF6, device PF4, capability PF5 e sessao/realtime PF7/PF3 foram reutilizados sem pipeline paralelo.
- `location.current` e fornecida por snapshot GPS autenticado e fica indisponivel ao disconnect.
- E2E com sockets HTTP/WebSocket reais em loopback.
- testes focados PF3-PF8: **29/29 PASS**; regressao completa: **377/377 PASS**; Alembic `0001 -> 0008`: PASS; `compileall`: PASS.
- proximo gate unico: PF9 Voice / Call Readiness de contratos.


## PF9 Voice / Call Readiness — 2026-08-25

- `VoiceCallRegistry` process-local, com `session_id` como conversa duravel;
- `VoiceCallCoordinator` publica wake/speech/call/interruption no mesmo Event Bus;
- somente `speech_final` entra no `ChatService.stream_turn()` compartilhado, preservando correlation/causation e client/device provenance;
- contratos de adapter para VAD, wake word, STT e TTS; nenhum engine final foi acoplado;
- `/ws/v1/call` prova Call semantica e emite `tts_text` por `agent_id`;
- `interrupt` e signal-only e nao afirma cancelamento real do model/TTS;
- ADR 0059; testes PF9 focados: **5/5 PASS**; regressao completa: **382/382 PASS**; Alembic `0001 -> 0008`: PASS; `compileall`: PASS. Proximo gate: F3 closure (telemetria runtime + E2Es/ADRs finais).

## F3 Platform Foundation closure — ADR 0060

F3 esta **concluida e congelada**. `RuntimeTelemetry` registra milestones de conversa e tools com correlation/session/provenance; `/api/v1/runtime/telemetry` fornece diagnostico read-only. E2E integrado prova runtime headless + dois client ids + mesma sessao/contexto + mesma identidade de Event Bus/telemetria. Personality Core nao foi alterado. Gate atual unico: **F5 Realtime Presence / Call / Multi-client**.


## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.

## F5 checkpoint — ADR 0062
Realtime presence orchestration is now implemented: runtime-owned present/attentive/engaged state, bounded attention window, semantic Campanario wake/direct address, cooperative interruption and authenticated call handoff preserving call_id/session_id. F5 remains ACTIVE: final VAD/STT/TTS media adapters, playback-level barge-in and background audio are not yet proven.

## F5b Voice Media Runtime checkpoint

ADR 0063 accepted. Binary PCM -> VAD/STT adapter -> shared Conversation Runtime -> agent-provenanced TTS audio is implemented and regression is 399 PASS. F5 remains OPEN because physical microphone/speaker plus production STT/TTS engines and measured host/mobile E2E are not yet proven. Next gate: F5c host voice integration; do not advance to F6.

## F5c Host Voice Integration checkpoint — ADR 0064

F5c implementation is complete: local whisper.cpp STT, Windows SAPI TTS, sounddevice host microphone/speaker client, authenticated Device presence, physical playback abort before barge-in, and voice latency telemetry are wired to the existing Call/Conversation Runtime. Automated focused gate: 14 PASS; full regression: 403 PASS. The build container cannot certify the target PC microphone/speaker/installed engines. **Next gate: F5c Host Acceptance / Voice Ready Gate on the target Windows PC. F6 remains blocked.**

## F5c.1 — STT portugues / voice capture stabilization

O primeiro E2E fisico F5c provou a volta completa de audio, mas mostrou transcricao pt-BR insuficiente e turnos fantasma de nao-fala. ADR 0065 endurece a fronteira STT sem alterar o runtime cognitivo: `-l pt` agora e testado/observavel, prompt pt-BR curto, rejeicao de modelo `.en.bin` incompatível, filtro de anotacoes puras de ruido, gate minimo de fala e launcher preservando `voice-host`. `tools/windows` foi limpo; regressao historica foi movida, nao apagada. F5 permanece aberta ate revalidacao fisica no PC alvo.


## F5c.2 — Voice Runtime Wiring
The Windows launcher now auto-wires whisper.cpp + Windows SAPI into the server-side VoiceMediaRuntime when local voice assets are present. This fixes the physical E2E failure where the Host Voice websocket connected successfully but raw audio hit `UnconfiguredStt` inside the API/runtime process. `.env.example` remains conservative; machine-local voice assets are detected at launch.

## F5c.3 — Host Voice Runtime Readiness

O E2E fisico encontrou um segundo problema de wiring: uma extracao com `.env` conservador podia subir `/ws/v1/call` com `UnconfiguredStt`, causando queda do WebSocket ao primeiro PCM. ADR 0066 move a robustez para a fronteira runtime/media: descoberta local de `whisper-cli.exe` + modelo multilingue em layouts conhecidos, readiness explicita de STT/TTS e erro de contrato em vez de traceback. O launcher tambem procura `models/`, `voice/models/`, `voice/` e fallback recursivo. Regressao completa: **412 PASS**. F5 continua aberta ate revalidacao fisica no Windows alvo.


## F5c.4 — Host Voice readiness fail-fast
O E2E fisico confirmou que o runtime estava saudavel, mas sem modelo STT multilingue carregado; o cliente continuava enviando PCM e recebendo `voice_stt_not_configured` em loop. F5c.4 torna esse erro terminal no Host Voice e adiciona `tools/windows/PREPARAR_VOZ_F5C.bat`, que valida whisper-cli e instala/valida `models/ggml-small.bin`. O gate F5 continua aberto ate o E2E fisico pt-BR passar.

## F5c.4 physical checkpoint freeze — ADR 0067 — 2026-08-25

Target-PC E2E finally completed a real microphone -> Host Voice -> `/ws/v1/call` -> STT -> shared Conversation Runtime -> Morgana -> voice-return round trip. However, Portuguese STT is not accepted: the user said `Campanario, voce esta ai?` and STT produced `O Brasil e o maior.`; Morgana correctly answered the corrupted transcript she received. Therefore the runtime path is alive, but input semantics are being corrupted at the STT/capture boundary. **F5 remains OPEN and F6 remains BLOCKED.** Next gate: stabilize physical pt-BR recognition by verifying effective multilingual Whisper model + `-l pt`, then tune VAD/capture only if measured evidence requires it. Do not compensate in Personality Core.

## F5c.4 maintenance refactor — E2E scenario modularization

Sem avanço de gate: F5 continua aberta e F6 bloqueada. O monolito `src/campanario/e2e/scenarios.py` foi dividido em fachada de roteamento, suites de agentes, suites standard/full e utilitarios compartilhados. A API publica `build_scenarios()` e a geração seeded foram preservadas. Equivalencia antes/depois foi verificada em 4 seeds x 8 suites com o mesmo digest SHA-256 `74970171844034c5f06b3d97e2b476d96d7d0283f5c601481c1b44d03c13ce7f`. A regressao completa do pacote recebido ficou em 411 PASS / 2 FAIL; os dois FAILs sao do estado de entrada F5c (`PREPARAR_VOZ_F5C.bat` ausente e launcher sem marcador esperado pelo teste), nao desta refatoracao. `__pycache__`/`.pyc` foram removidos do pacote de handoff.

## F5c.4 maintenance — externalizacao dos modelos Whisper — 2026-08-26

- Nenhum avanço de gate: **F5 permanece OPEN; F6 permanece BLOCKED**.
- `ggml-*.bin` nao faz mais parte do handoff de codigo; sao ativos locais compartilhados entre versoes.
- novo `CAMPANARIO_VOICE_MODELS_DIR` aponta para um diretorio externo; `CAMPANARIO_VOICE_WHISPER_MODEL_PATH` continua tendo precedencia para arquivo explicito.
- Windows usa `%LOCALAPPDATA%\Campanario\models` por padrao; `PREPARAR_VOZ_F5C.bat` baixa `ggml-small.bin` ali.
- layouts legados dentro do projeto continuam suportados apenas para compatibilidade.
- `models/README.md` + `.gitignore` formalizam que pesos nao entram no ZIP/repo.
- Host Voice focado: **15/15 PASS**; regressao completa: **415/415 PASS**; `compileall`: PASS.
- proximo gate funcional continua: estabilizar reconhecimento fisico pt-BR conforme ADR 0067; nao compensar no Personality Core.

## F5c.5 — Physical pt-BR recognition boundary — ADR 0068 — 2026-08-26

O próximo gate de ADR 0067 foi aplicado sem avançar de fase. O VAD deixa de filtrar o conteúdo interno da fala: `UtteranceBuffer` preserva 4 frames de pre-roll e mantém todos os frames após início de fala até 12 frames de silêncio final, evitando cortar consoantes/sílabas fracas antes do Whisper. O gate mínimo continua contando apenas áudio classificado como fala. Quando há múltiplos pesos multilíngues externos, o F5 físico agora prioriza qualidade (`large-v3/large/big/medium` antes de `small/base`); `CAMPANARIO_VOICE_WHISPER_PREFER_ACCURACY=false` permite priorizar latência. `-l pt` e ausência de correção semântica pós-STT permanecem invariantes. Personality Core não foi alterado. Evidência automatizada: **21/21 focados PASS; 418/418 regressão completa PASS**. **F5 permanece OPEN; F6 permanece BLOCKED** até nova aceitação física pt-BR no Windows alvo.

## F5c.6 — Voice addressing / presence semantics — ADR 0069 — 2026-08-26

Evidencia fisica do F5c.5 mostrou STT pt-BR inteligivel, mas revelou defeito pragmatico de call: probes como `Campanario, me escuta?` viravam perguntas abertas e `Todd e Morgana` permitia que a segunda persona reagisse a resposta da primeira como se fosse novo input. ADR 0069 torna wake accent-insensitive (`Campanário`/`Campanario`), adiciona semantica estreita de probe/chamada de presenca e, somente em voz com enderecamento explicito aos dois, entrega ao secundario o historico anterior a resposta primaria + a fala original do usuario. Personality Core, memoria e STT nao foram reescritos. Evidencia automatizada: **38/38 focados PASS; 422/422 regressao PASS; compileall PASS**. **F5 permanece OPEN; F6 permanece BLOCKED** ate nova validacao fisica.

## F5c.7 — Physical STT echo / segmentation hardening — ADR 0070 — 2026-08-26

O teste fisico F5c.6 mostrou que frases repetidas ainda podiam virar segmentos quebrados e transcricoes alheias. A causa de fronteira mais forte era dupla: o Host Voice enviava PCM do microfone ao STT enquanto SAPI tocava no alto-falante, permitindo eco como fala do usuario, e o fim de frase de ~480 ms era curto para pausas naturais apos `Campanario`. ADR 0070 suprime PCM durante playback salvo barge-in confirmado com pre-roll local, aumenta hangover para ~960 ms, pre-roll para 6 frames e fala minima para 300 ms, reduz o prompt Whisper a nomes proprios e fixa decoding deterministico (temperature 0, beam 5, no-fallback, suppress-nst, no-speech 0.50). Nao ha correcao semantica pos-STT. Evidencia automatizada: **27/27 focados PASS; 424/424 regressao completa PASS**. **F5 permanece OPEN; F6 permanece BLOCKED** ate nova validacao fisica pt-BR.

## F5c.8 — Voice turn boundary / stale-response isolation — ADR 0071 — 2026-08-26

Physical F5c.7 evidence showed a remaining turn-boundary failure: natural pauses could split one pt-BR sentence into multiple `voce:` turns, and responses from superseded turns could arrive late. ADR 0071 raises Host Voice end-of-speech hangover from 24 to 45 frames (~1.8 s at the current host frame), gives each voice turn an explicit correlation id, cancels an older running Conversation/TTS response when a new confirmed utterance supersedes it, and filters agent events from obsolete correlations before TTS. No phrase-specific post-STT rewrite and no Personality Core change. Evidence: **35/35 focused PASS; 424/424 full regression PASS; compileall PASS**. **F5 remains OPEN; F6 remains BLOCKED** pending target-PC physical validation.

## F5c.9 — Adjustable SAPI speech rate — 2026-08-26

Physical feedback showed Windows SAPI playback was too slow for a natural realtime call. The host TTS already supported per-agent SAPI rate but hid it behind conservative defaults. F5c.9 exposes the existing boundary as an operational control: Todd defaults to rate 4, Morgana to 3, both remain configurable in the SAPI `-10..+10` range, and `tools/windows/AJUSTAR_VELOCIDADE_VOZ.bat` persists five user-facing presets. This changes playback speed only; no agent prompt/personality/STT semantics changed. Evidence: **21/21 focused PASS; 426/426 full regression PASS**. **F5 remains OPEN; F6 remains BLOCKED.**

## F5c.10 — utterance aggregation / natural spoken delivery — ADR 0072 — 2026-08-26

Gate permanece **F5 Realtime Presence / Call / Multi-client OPEN; F6 BLOCKED**. O Host Voice agora distingue finais STT completos de fragmentos fortemente incompletos. Apenas estes últimos recebem 1200 ms de grace; fala subsequente recombina PCM, remove a maior parte do hangover duplicado e retranscreve a utterance inteira antes de criar o turno. Não existe tabela de frases/respostas nem correção semântica pós-STT. Voice delivery pede respostas curtas/conversacionais sem alterar Personality Core. Barge-in padrão foi endurecido para interrupção humana mais rápida e continua configurável. Evidência: **25/25 focados; 430/430 full regression; compileall PASS**. Próxima evidência exigida: E2E físico espontâneo no PC alvo.

## F5c.11 — continuous spoken-output boundary / TTS sanitization — 2026-08-26

Gate permanece **F5 Realtime Presence / Call / Multi-client OPEN; F6 BLOCKED**. A sessão Host Voice continua no mesmo websocket/call e agora separa explicitamente texto canônico de texto falável. `sanitize_for_tts()` remove emoji, Markdown visual, URLs e marcadores somente na fronteira TTS; histórico/UI preservam a resposta original. A saída falada deixa de sintetizar chunks concorrentes do modelo: `SpokenOutputBuffer` agrupa chunks em unidades de frase, com fallback limitado por tamanho, e uma fila TTS serial por sessão preserva ordem/prosódia. Barge-in incrementa a geração da fila, limpa fala pendente e cancela a síntese ativa, evitando retorno de áudio obsoleto. A agregação/retranscrição de utterance do F5c.10 permanece ativa; nenhuma frase pronta foi adicionada e Personality Core não foi alterado. Evidência automatizada: **41/41 focados PASS; 434/434 regressão completa PASS; compileall PASS**. Próxima evidência exigida: teste físico espontâneo, incluindo emoji na resposta, fala longa e interrupção durante TTS.

## Personality quality refinement — turn-local activation — ADR 0073 — 2026-08-26

A call F5 permanece pausada/nao aprovada no checkpoint F5c.11; **F5 continua OPEN e F6 continua BLOCKED**. Foi retomada uma divida de qualidade da Personality Baseline sem reabrir o core nem alterar fatos/memoria/tools. `src/campanario/agents/personality_application.py` ativa, por turno, apenas as prioridades relevantes do Personality Core ja canonico usando `ConversationTurnInterpreter`: Todd recebe saliencia de decisao/trade-off/acao/reversibilidade e Morgana de contexto/criterios/relacoes/inferencia quando isso agrega; em factual simples ambos recebem ordem explicita de manter assinatura leve. A camada e anexada perto da geracao, antes do `AnswerContract`, que continua soberano sobre a obrigacao factual/conversacional. O guidance de voz deixou de achatar ambos no mesmo estilo generico e agora preserva a persona do agente. Nao ha bordoes, respostas benchmark ou segunda inferencia. Evidencia automatizada: **55/55 focados PASS; 438/438 regressao completa PASS; compileall PASS**. Proxima evidencia de personalidade deve ser Behavioral E2E pareado Todd x Morgana com prompts novos e revisao humana; nao declarar novo baseline antes dessa evidencia.

## Human Conversation Baseline — ADR 0074 — 2026-08-26

A frente de qualidade de personalidade ganhou um Behavioral E2E específico para conversa humana cotidiana sem alterar o Personality Core nem o gate de call. `agent_human_baseline` executa **10 episódios persistentes / 80 turnos**: quatro roteiros pareados Todd × Morgana com falas do usuário literalmente idênticas (`getting_to_know`, `daily_continuity`, `casual_disagreement`, `story_and_followup`) e duas salas compartilhadas com os dois agentes presentes. `agent_human_quick` fornece smoke test de **5 episódios / 40 turnos**. O relatório gera `blind_review.md`, escondendo os nomes dos agentes até o gabarito e pedindo avaliação humana de naturalidade, continuidade, curiosidade proporcional, ausência de palestra/interrogatório, memória contextual, consistência de personalidade e vontade de continuar conversando. Launcher: `tools/windows/TESTAR_CONVERSA_HUMANA.bat`. Evidência automatizada: **61/61 focados PASS; 442/442 regressão completa PASS; compileall PASS**. A call F5 permanece pausada/não aprovada em F5c.11; **F5 OPEN, F6 BLOCKED**.

## Freeze 2026-08-26

Desenvolvimento ativo pausado. A frente experimental posterior ao ADR 0074 foi removida deste pacote. Consulte `FREEZE_BASELINE.md`. F5 permanece OPEN/pausado e F6 BLOCKED.
