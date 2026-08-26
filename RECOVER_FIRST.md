# LEIA PRIMEIRO — CAMPANARIO / F4 EXPERIENCE LEARNING CONCLUIDA

> Leia este arquivo e `PROJECT_STATE.md` antes de qualquer alteracao. Considere o codigo como evidencia final. Nao pule gates.

## Estado canonico congelado

- Foundation conversacional aprovada com `gemma3:12b`.
- Regressao pos-organizacao/presence UI: 11/11 cenarios e 64/64 checks no standard real.
- Campanario e o sistema/ambiente, nunca uma persona.
- Morgana e Todd sao participantes persistentes e pontes entre Campanario e usuario.
- Morgana e a default/primary speaker, mas prioridade nunca significa exclusividade.
- Presence UI v1.3.0 representa o sistema como ambiente/call, sem modos ou seletores obrigatorios de agente.
- AgentRouter + ParticipationArbiter existem; multi-speaker e speaker provenance estao ativos.
- Model runtime e portavel; Gemma 3 12B e recomendado, nao acoplado.
- Voz, wake word, STT/TTS, barge-in e modo call constante AINDA NAO ESTAO IMPLEMENTADOS.
- Memoria cognitiva/evolucao dos agentes AINDA NAO ESTA IMPLEMENTADA.

## Leia nesta ordem

1. `PROJECT_STATE.md`
2. `SAFEPOINT.md`
3. `docs/current/ROADMAP.md`
4. `docs/current/PLATFORM_FOUNDATION_HANDOFF.md` (F3 ativa; seguir gates em ordem)
5. `docs/current/AGENT_ARCHITECTURE.md`
6. `docs/current/AGENT_PERSONALITY_ROADMAP.md`
7. `docs/current/AGENT_PERSONALITY_CONCEPT.md`
8. `docs/current/AGENT_TEST_STRATEGY.md`
9. `docs/current/AGENT_LEARNING_STRATEGY.md`
10. `docs/current/ARCHITECTURE.md`
11. `docs/concept/SYSTEM_CONCEPT.md`
12. `docs/concept/MODO_PATRULHA_V2.md`
13. `UI_UX_PRESENCE_ARCHITECTURE.md`

## Gate atual unico

**F4 EXPERIENCE / LEARNING — CONCLUIDA E CONGELADA NO ADR 0061; F5 Realtime Presence / Call / Multi-client e o proximo gate.**

F2 foi congelada como **Personality / Social / Long-Call Baseline v1** apos o Long Call P2.4.4 seed `1787683779`: 36 turnos, 253 PASS / 2 WARN / 0 FAIL; os dois WARNs de tensao criativa foram aceitos em revisao humana como contextuais. ADR 0049 registra o freeze.

PF1a introduziu `CampanarioRuntime`, `RuntimeState`, `ChatSessionManager` e contratos client-independent (ADR 0050). PF1b adicionou lifecycle explicito, `RuntimeHost`, FastAPI lifespan e host headless (ADR 0051). PF2 adicionou `RuntimeEventBus`, contratos versionados `1.0`, ordem monotônica, correlation/causation, provenance explicita e replay process-local basico (ADR 0052). PF3 adicionou `/api/v1` + `/ws/v1/events`, replay por `after_sequence` e migrou a Presence UI para o gateway mantendo `/api` + SSE legado (ADR 0053). PF4 adicionou `DeviceRegistry` persistente em SQLite, `/ws/v1/devices`, discovery por hardware capability e eventos de device com provenance (ADR 0054). PF5 adicionou `CapabilityRegistry` provider-independent, schemas, timeout, permission requirements como metadata, provenance e eventos `TOOL_*`; uma capability ligada a device foi consumida pelo runtime sem o caller conhecer provider (ADR 0055). Testes focados PF5: **22/22**; regressao completa **362/362 PASS** na regressao final.

PF8 foi concluido no ADR 0058: cliente mobile minimo autenticado, mesma sessao/contexto, realtime/reconnect e `location.current` de teste por device. PF9 foi concluido no ADR 0059: Call semantica, contratos VAD/wake/STT/TTS, interruption signal-only e speech final reutilizando a mesma Conversation Runtime.

F3 foi fechada no ADR 0060. F4 Experience / Learning foi fechada no ADR 0061. Proximo passo unico: F5 Realtime Presence / Call / Multi-client. Nao implementar Patrulha completa ou capabilities finais fora de sequencia.

## Regras permanentes

- Campanario nunca e agente/persona;
- Morgana e default primary speaker ate ADR explicito em contrario;
- Todd e Morgana podem estar presentes ao mesmo tempo;
- usuario nao deve gerenciar agentes como modos;
- persona muda perspectiva/comunicacao, nunca fatos/evidencia;
- agentes nao duplicam banco, provider, memoria-base, tools ou knowledge core;
- personalidade-core nao deve sofrer drift silencioso;
- aprendizado futuro usa experiencia/memoria com proveniencia, nao retraining automatico a cada conversa;
- inferencia/opiniao de agente nunca vira fato automaticamente;
- voz/call reutiliza a mesma arquitetura de contexto/participacao; nao cria um segundo Campanario;
- modelos continuam substituiveis;
- nao hardcodar respostas para benchmark;
- fontes privadas brutas nao entram no repositorio;
- toda funcao de usuario atualiza `docs/manual/`;
- mudanca arquitetural relevante exige ADR;
- antes de nova fase, criar/atualizar safepoint e recovery docs.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.

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

## P2.2d — correcoes pos Behavioral E2E seed 1787665713

- execucao real: 3 PASS / 0 WARN / 3 FAIL; 72 PASS / 0 WARN / 4 FAIL;
- referencia-vs-convite e silencio seletivo passaram;
- FAILs restantes: labels/transcript de speaker e corrupcao `18x7 -> 16x7`;
- analise: `docs/current/INTEGRATED_E2E_REVIEW_1787665713.md`;
- novo `Speaker Output Guard`: remove somente header redundante do proprio agente; labels restantes forcam regeneracao e nunca sao relabelados silenciosamente;
- novo `Arithmetic Correction Anchor`: extrai operandos do turno, calcula aritmetica simples deterministicamente, valida resposta, regenera uma vez e possui fallback estreito derivado do proprio enunciado;
- teste generico `9x6=53 -> 54` garante ausencia de hardcode do benchmark;
- Personality Core nao foi alterado;
- regressao local: 283/283;
- proximo passo unico: reexecutar `tools/windows/TESTAR_CONVERSA_MULTIAGENTE.bat`. Se passar speaker provenance + correction fidelity, congelar Social Protocol v1 e avancar para Long Call E2E textual com latencia detalhada.

## P2.3 — Long Call Behavioral E2E

- suite: `agent_long_call`;
- launcher: `tools/windows/TESTAR_LONG_CALL.bat`;
- 3 calls textuais persistentes x 12 turnos = 36 turnos;
- roteiros: tecnico/decisao, criativo/produto, misto/social;
- usa `ChatService.stream_turn()` real e banco temporario isolado;
- mistura convite aos dois, endereco direto, turno aberto, mudanca/retomada de assunto, correcao, ack e encerramento;
- latencia: TTFR, total do turno, geracao por speaker, gap do segundo agente, media/mediana/p95/max, solo vs multiagente;
- recovery de speaker apos seed `1787666272`: extracao somente de segmento explicitamente rotulado como o proprio agente se o repair ainda vier em formato de painel;
- regressao local: 288/288;
- proximo passo unico: rodar `TESTAR_LONG_CALL.bat` com Gemma 3 12B e enviar o relatorio completo.

## P2.3d — Long Call Grounding Hardening apos seed 1787671154

- execucao real: 36 turnos; 230 PASS / 7 WARN / 2 FAIL;
- correction factual cross-turn falhou (`24x6` -> `143`) porque o anchor antigo so lia o turno atual;
- linguagem interna do Focus Stack vazou em respostas (`IDENT`, `frame`);
- `mesma pergunta`, `aterrissa isso` e `sequencia curta` ainda perdiam o referente imediato;
- modelo inventou componentes tecnicos (`X/Y/Z`, integracoes inexistentes);
- briefing de continuidade foi compactado e removeu vocabulario de implementacao do prompt ativo;
- pedido anterior e fala anterior sao reforcados em follow-ups deiticos;
- correction anchor agora busca a expressao aritmetica em turnos recentes e o claim incorreto no turno atual;
- grounding proibe inventar componentes/modulos/requisitos nao fornecidos;
- PromptLeakGuard/E2E reconhecem metadados de continuidade como internos;
- roadmap futuro formaliza F3 Platform Foundation / Runtime v2 antes de Mobile/Voice/Tools em massa;
- regressao local: 300/300;
- proximo passo unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat`.


## P2.3e — Reference Binding + Ambient Call Semantics apos seed 1787678674

- execucao real: 36 turnos; 233 PASS / 8 WARN / 0 FAIL;
- analise: `docs/current/LONG_CALL_REVIEW_1787678674.md`;
- binding explicito de `mesma pergunta`, `resposta/ponto`, `aterrissa isso`, `sequencia curta`, `so o essencial`;
- `qual coisa cortar/preservar` recebe escolhas recentes definidas pelo usuario;
- `primeira ideia` ancora a abertura da call e decisoes/restricoes do usuario;
- `resume a decisao` deve resumir a conclusao, nao explicar o ato de resumir;
- arquitetura que apenas incomoda mas nao quebra nao autoriza inventar modulo/integracao/gargalo/seguranca;
- Social Protocol: call continua nao exige nomes por turno; pensamento em voz alta favorece silencio sem palavra magica;
- ADR: `docs/adr/0043-reference-binding-ambient-call-semantics.md`;
- Personality Core intacto;
- regressao local: 305/305;
- proximo passo unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat`.


## P2.4 — Dialogue State Compiler

- evidencia: seed `1787679961`, 237 PASS / 11 WARN / 1 FAIL;
- diagnostico: limite de coreferencia/answer binding via prompt, nao drift de persona;
- `src/campanario/chat/dialogue_state.py` compila estado tipado antes de cada geracao;
- runtime usa `DialogueStateCompiler`, nao `working_conversation_note`;
- resolve `mesma pergunta`, `aterrissa isso`, `sequencia curta`, proximo passo, resumo de decisao, escolha cortar/preservar e instrucao de ordem;
- acknowledgement/encerramento impede abertura de nova tarefa;
- nao existe segunda inferencia nem memoria persistente;
- ADR `0044-dialogue-state-compiler.md`;
- gate atual: repetir `tools/windows/TESTAR_LONG_CALL.bat`;
- regressao local: **317/317**;
- F3 Platform Foundation continua bloqueada ate congelar F2.

## P2.4.1 — Answer Contract

- seed P2.4 real `1787680836`: 244 PASS / 12 WARN / 0 FAIL;
- `DialogueState` estava correto como estrutura, mas Gemma ainda podia ignora-lo como mero contexto;
- `AnswerContract` agora e anexado por ultimo e vincula pedido/referente/material/desvios do turno;
- bindings criticos possuem validacao deterministica e um retry local maximo;
- checks de binding objetivo no Long Call foram endurecidos para FAIL; criatividade/necessidade do segundo agente continuam contextuais;
- Personality Core intacto; sem memoria aprendida; sem segunda inferencia de interpretacao;
- regressao: **323/323**;
- proximo passo unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat` com Gemma 3 12B;
- F3 Platform Foundation continua bloqueada ate freeze F2.


## P2.4.2 — Conversational Commitment & Contribution Contract

- evidencia de entrada: Long Call seed `1787681697`, 36 turnos, 254 PASS / 2 WARN / 0 FAIL;
- binding/referentes ficaram estaveis, mas revisao humana detectou reabertura de decisao aceita, repeticao quase literal sob `nao repete` e embodiment factual espontaneo em exploracao criativa;
- novo `CommitmentState` registra a decisao imediatamente aceita em turnos de fechamento/ack e o `AnswerContract` exige acknowledgement curto sem reanalise;
- se ate o retry tentar reabrir uma decisao fechada, o runtime usa fallback conversacional seguro `Entendido.`;
- `AnswerContract.distinct_from` valida sobreposicao apenas quando o usuario explicitamente pede uma contribuicao diferente;
- Embodiment Boundary permite atmosfera/metafora, mas rejeita afirmacoes factuais de corpos/acoes fisicas de Todd/Morgana salvo roleplay/ficcao explicita;
- correction anchor rejeita vazamento de linguagem do guard (`enunciado`, `operandos`, `ancoragem`) e cai para correcao natural se necessario;
- Long Call endurecido para decisao fechada curta/nao reaberta e guard factual invisivel;
- Personality Core intacto; nenhuma segunda inferencia;
- regressao local: **329/329**;
- gate atual unico: reexecutar `tools/windows/TESTAR_LONG_CALL.bat`; F3 continua bloqueada ate freeze F2.


## P2.4.3 — Freeze Candidate Polish

Seed de entrada `1787682411`: 256 PASS / 3 WARN / 0 FAIL. P2.4.2 fechou as falhas estruturais; P2.4.3 so reduz parafrase sob `nao repete`, ruido em micro-respostas e jargon interno em semantica social, alem de corrigir um checker lexical de silencio. Regressao local: **333/333**. Proximo gate unico: uma ultima seed `TESTAR_LONG_CALL.bat`; F3 permanece bloqueada ate decisao explicita de freeze F2.


## P2.4.4 — Freeze Gate Fixes

- evidencia de entrada: Long Call seed `1787683144`, 36 turnos, 255 PASS / 2 WARN / 2 FAIL;
- `144` por extenso passa a ser aceito pelo check aritmetico do Long Call;
- `nao repete` exige criterio social novo, nao apenas baixa sobreposicao lexical;
- retry invalido nesse contrato nao persiste silenciosamente a primeira resposta;
- `vou trabalhar agora` nao cria commitment novo e recebe fechamento curto, sem reciclar `ponto de convergencia`;
- Personality Core e Participation Arbiter intactos;
- regressao local: **335/335**;
- gate unico: nova execucao de `tools/windows/TESTAR_LONG_CALL.bat`; somente depois decidir freeze F2 e liberar F3.


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

- `ClientIdentity` separa `client_id` de `device_id` e `agent_id`; nenhum client/device vira participante social.
- `ClientSessionRegistry` mantem attachments process-local; sessao/contexto continuam duraveis e pertencem ao Campanario.
- `/ws/v1/events` aceita `client_id`; reconnect cria novo attachment, nao nova sessao.
- `/api/v1/sessions/{id}/turn` aceita provenance de client e device autenticado; USER_TEXT preserva client provenance enquanto Todd/Morgana preservam agent provenance.
- migration `0008` persiste `client_id`/`device_id` em mensagens USER.
- Presence UI reutiliza `client_id` estavel no navegador.
- `episode_id` e hoje alias do `session_id` tecnico; nao existe segundo container de memoria.
- Testes PF7 provam PC + segundo cliente no mesmo contexto, realtime compartilhado, reconnect e roundtrip SQLite.
- Proximo gate unico: PF8 Mobile Readiness.

## Validacao PF7 — 2026-08-25

- testes focados PF7 + runtime/gateway/security: **36/36 PASS**;
- regressao completa final: **373/373 PASS**;
- migration Alembic `0001 -> 0008`: PASS;
- `compileall`: PASS;
- checkpoint historico PF7: o gate seguinte era PF8; PF8 agora esta concluido e o gate atual esta no topo deste arquivo.


## PF8 Mobile Readiness — 2026-08-25

- ADR 0058 aceito; nenhum novo schema persistente/migration foi necessario.
- `MobileReadinessClient` usa os mesmos contratos PF3/PF7; nao existe ChatService mobile.
- device ja pareado deve autenticar no `/ws/v1/devices`; canal nao pareado nao publica location.
- GPS mock/test autenticado vira `location.current` no PF5 e publica `LOCATION_UPDATED` com provenance.
- E2E real usa Uvicorn + HTTP/WebSocket em loopback; gateway de producao continua `127.0.0.1`.
- Proximo gate unico: PF9 Voice / Call Readiness de contratos; audio final continua bloqueado por Experience/Learning.

## F3 closure — autoridade mais recente

ADR 0060 congela Platform Foundation / Runtime v2. ADR 0061 congela Experience / Learning Baseline v1. **Gate atual: F5 Realtime Presence / Call / Multi-client.** Historicos anteriores que mencionem PF9/F3/F4 como proximos passos estao superseded por este bloco e pelos ADRs 0060/0061.


## F4 Experience / Learning Baseline v1 — ADR 0061

F4 esta concluida. `ExperienceLayer` usa uma unica memoria SQLite compartilhada por Todd/Morgana, com provenance/evidence, confidence, recency/recall, facts/preferences/plans/shared experiences/inferences, supersession, correcao e esquecimento. Captura automatica e conservadora e nao usa outro LLM por turno. A regra de curiosidade e proporcional: perguntar uma informacao do usuario somente quando ela muda materialmente a resposta; nunca inventar nem interrogar para enriquecer perfil. Personality Core permanece congelada. Proximo gate unico: **F5 Realtime Presence / Call / Multi-client**.

## F5 active checkpoint
ADR 0062 is accepted but does NOT freeze F5. Resume with real media adapter/E2E proof (VAD/STT, per-agent TTS, playback barge-in, background lifecycle) on the same runtime/session; do not create a voice ChatService.

## F5b Voice Media Runtime checkpoint

ADR 0063 accepted. Binary PCM -> VAD/STT adapter -> shared Conversation Runtime -> agent-provenanced TTS audio is implemented and regression is 399 PASS. F5 remains OPEN because physical microphone/speaker plus production STT/TTS engines and measured host/mobile E2E are not yet proven. Next gate: F5c host voice integration; do not advance to F6.

## F5c Host Voice Integration checkpoint — ADR 0064

F5c implementation is complete: local whisper.cpp STT, Windows SAPI TTS, sounddevice host microphone/speaker client, authenticated Device presence, physical playback abort before barge-in, and voice latency telemetry are wired to the existing Call/Conversation Runtime. Automated focused gate: 14 PASS; full regression: 403 PASS. The build container cannot certify the target PC microphone/speaker/installed engines. **Next gate: F5c Host Acceptance / Voice Ready Gate on the target Windows PC. F6 remains blocked.**

## F5c.1 — STT portugues / voice capture stabilization

O primeiro E2E fisico F5c provou a volta completa de audio, mas mostrou transcricao pt-BR insuficiente e turnos fantasma de nao-fala. ADR 0065 endurece a fronteira STT sem alterar o runtime cognitivo: `-l pt` agora e testado/observavel, prompt pt-BR curto, rejeicao de modelo `.en.bin` incompatível, filtro de anotacoes puras de ruido, gate minimo de fala e launcher preservando `voice-host`. `tools/windows` foi limpo; regressao historica foi movida, nao apagada. F5 permanece aberta ate revalidacao fisica no PC alvo.

## RECOVERY UPDATE — F5c.4 physical checkpoint — ADR 0067

Current gate is still **F5 Realtime Presence / Call / Multi-client**. A real target-PC voice round trip now works, so do not reopen runtime/API/WebSocket wiring without new evidence. The remaining blocker is physical Portuguese STT quality: `Campanario, voce esta ai?` was transcribed as `O Brasil e o maior.`. Next action is to verify the effective multilingual Whisper model + `-l pt`, then perform focused pt-BR capture/VAD tuning. F6 remains blocked.

If `voice/` or `models/` are missing after deletion/reinstall, restore whisper.cpp binaries and a multilingual model first, then run `tools/windows/PREPARAR_VOZ_F5C.bat`. Machine credentials/secrets are not part of the repository freeze.

## F5c.4 maintenance refactor — E2E scenario modularization

Sem avanço de gate: F5 continua aberta e F6 bloqueada. O monolito `src/campanario/e2e/scenarios.py` foi dividido em fachada de roteamento, suites de agentes, suites standard/full e utilitarios compartilhados. A API publica `build_scenarios()` e a geração seeded foram preservadas. Equivalencia antes/depois foi verificada em 4 seeds x 8 suites com o mesmo digest SHA-256 `74970171844034c5f06b3d97e2b476d96d7d0283f5c601481c1b44d03c13ce7f`. A regressao completa do pacote recebido ficou em 411 PASS / 2 FAIL; os dois FAILs sao do estado de entrada F5c (`PREPARAR_VOZ_F5C.bat` ausente e launcher sem marcador esperado pelo teste), nao desta refatoracao. `__pycache__`/`.pyc` foram removidos do pacote de handoff.

## F5c.4 maintenance refactor — external Whisper model store

Sem avanço de gate: F5 continua aberta e F6 bloqueada. Pesos Whisper `ggml-*.bin` passam a ser tratados como ativos locais de maquina, fora do pacote do projeto. O runtime aceita `CAMPANARIO_VOICE_MODELS_DIR` e preserva `CAMPANARIO_VOICE_WHISPER_MODEL_PATH` como override de arquivo exato; o launcher Windows usa por padrao `%LOCALAPPDATA%\Campanario\models` e mantem layouts antigos apenas como fallback de compatibilidade. `PREPARAR_VOZ_F5C.bat` instala `ggml-small.bin` no store externo. `models/README.md` documenta a separacao e `.gitignore` impede pesos locais no handoff. Testes focados de Host Voice: **15/15 PASS**; regressao completa: **415/415 PASS**; `compileall`: PASS. O proximo gate funcional permanece o mesmo checkpoint fisico pt-BR do ADR 0067.

## F5c.5 — physical pt-BR recognition boundary — ADR 0068 — 2026-08-26

- Sem avanço de gate: **F5 OPEN / F6 BLOCKED**.
- O defeito isolado por ADR 0067 continua tratado somente na fronteira física STT/capture; Personality Core e Conversation Runtime não foram usados para compensação.
- `UtteranceBuffer` adiciona 4 frames de pre-roll e conserva frames internos/cauda até 12 frames de silêncio, usando VAD somente para início/fim da utterance.
- O mínimo de 240 ms continua contando somente frames realmente classificados como fala, preservando proteção contra turnos fantasma.
- Descoberta/launcher agora preferem modelo multilíngue maior quando disponível (`large-v3/large/big/medium` > `small/base`) para o gate físico pt-BR.
- `CAMPANARIO_VOICE_WHISPER_PREFER_ACCURACY=false` é o override explícito para priorizar latência.
- Evidência automatizada: **21/21 focados PASS; 418/418 regressão PASS**.
- Próximo passo único: reexecutar aceitação física pt-BR no PC alvo e observar a transcrição real; não avançar para F6 antes dela passar.

## F5c.6 — voice addressing / presence semantics — ADR 0069 — 2026-08-26

- Sem avanço de gate: **F5 OPEN / F6 BLOCKED**.
- `Campanário` com acento agora acorda o runtime igual a `Campanario`.
- `me escuta?`, `me ouve?`, `ta ai?` e chamadas somente por nome recebem semantica de presenca curta, sem inventar tarefa.
- Em Host Voice, `Todd e Morgana` explicitamente enderecados recebem a mesma fala original; a resposta do primeiro nao entra como novo prompt do segundo.
- Texto/multiagente fora do Host Voice mantem o comportamento anterior.
- Evidencia: **38/38 focados PASS; 422/422 regressao PASS; compileall PASS**.
- Proximo passo unico: repetir o E2E fisico com as frases acima e observar transcript + respostas; nao avancar F6.

## F5c.7 — Physical STT echo / segmentation hardening — ADR 0070 — 2026-08-26

O teste fisico F5c.6 mostrou que frases repetidas ainda podiam virar segmentos quebrados e transcricoes alheias. A causa de fronteira mais forte era dupla: o Host Voice enviava PCM do microfone ao STT enquanto SAPI tocava no alto-falante, permitindo eco como fala do usuario, e o fim de frase de ~480 ms era curto para pausas naturais apos `Campanario`. ADR 0070 suprime PCM durante playback salvo barge-in confirmado com pre-roll local, aumenta hangover para ~960 ms, pre-roll para 6 frames e fala minima para 300 ms, reduz o prompt Whisper a nomes proprios e fixa decoding deterministico (temperature 0, beam 5, no-fallback, suppress-nst, no-speech 0.50). Nao ha correcao semantica pos-STT. Evidencia automatizada: **27/27 focados PASS; 424/424 regressao completa PASS**. **F5 permanece OPEN; F6 permanece BLOCKED** ate nova validacao fisica pt-BR.

## F5c.8 recovery checkpoint — ADR 0071 — 2026-08-26

Do not advance to F6. The current physical-voice build favors complete pt-BR utterances: `VOICE_SILENCE_FRAMES_TO_FINALIZE=45` (~1.8 s) and old in-flight voice responses are isolated by correlation id. A newly confirmed utterance supersedes/cancels the previous response, and stale agent chunks are not allowed to become current TTS. This is generic voice turn integrity; there are no hardcoded test phrases or post-STT semantic substitutions. Automated evidence: **35/35 focused; 424/424 regression; compileall PASS**. Next evidence must come from the target Windows microphone using spontaneous phrases with natural pauses.

## F5c.9 — TTS speed control — 2026-08-26

Sem avanço de gate: **F5 permanece OPEN; F6 permanece BLOCKED**. O Windows SAPI ganhou controle explícito de velocidade por agente, com defaults físicos mais rápidos (Todd=4, Morgana=3) e launcher `tools/windows/AJUSTAR_VELOCIDADE_VOZ.bat` para presets persistentes de velocidade. O ajuste altera somente prosódia/tempo de reprodução; não altera texto, Personality Core, STT, memória, roteamento ou conteúdo das respostas. Evidência automatizada: **21/21 Host Voice focados PASS; 426/426 regressão completa PASS**.

## F5c.10 — utterance aggregation + natural voice turn delivery — ADR 0072 — 2026-08-26

- Sem avanço de gate: **F5 OPEN / F6 BLOCKED**.
- Evidência física F5c.9 mostrou STT bom em frases completas, mas fragmentação ainda criava vários `voce:` e respostas para pedaços intermediários.
- Fragmentos com forte evidência de continuação agora recebem grace window de 1200 ms. Se houver continuação, o **PCM original é recombinado e retranscrito**, sem colar/corrigir strings do Whisper.
- Somente o enunciado consolidado gera `stt_final` conversacional e `turn_id`.
- Barge-in Host ficou mais responsivo (threshold 1600, 2 frames, pre-roll 6), continuando configurável; fala humana confirmada interrompe/cancela resposta antiga.
- Voice channel ganhou instrução de entrega curta/conversacional pt-BR; Personality Core permanece intacto e nenhuma evolução de personalidade é reivindicada.
- Evidência automatizada: **25/25 focados PASS; 430/430 regressão PASS; compileall PASS**.
- Próximo passo único: teste físico espontâneo F5c.10 observando se uma frase vira um único `voce:` e se barge-in corta TTS sem vazamento. F6 continua bloqueado.

## F5c.11 — continuous spoken-output boundary — 2026-08-26

- **F5 permanece OPEN; F6 permanece BLOCKED.**
- TTS agora recebe somente texto falável sanitizado; emoji/Markdown/URL não são pronunciados e o texto canônico permanece intacto para UI/histórico.
- `SpokenOutputBuffer` agrega streaming textual em frases naturais antes da síntese.
- TTS é serial por sessão; barge-in limpa fila pendente e cancela áudio ativo de geração antiga.
- F5c.10 continua responsável por agregação/retranscrição de fragmentos STT; não foram adicionadas frases hardcoded.
- Evidência: **41/41 testes focados; 434/434 regressão; compileall PASS**.
- Próximo passo único: E2E físico espontâneo no Windows alvo, observando entendimento STT, naturalidade da fala e interrupção real.

## Personality refinement checkpoint — ADR 0073 — 2026-08-26

A frente de call foi deliberadamente pausada no F5c.11 porque a experiencia fisica ainda nao foi aprovada. **Nao considerar F5 concluida e nao abrir F6.** O trabalho atual voltou a uma divida de qualidade da Personality Baseline: `PersonalityCore` em `profiles.py` continua sendo a fonte canonica e nao foi substituido. A nova camada `agents/personality_application.py` torna salientes, por tipo de turno/pragmatica, prioridades ja coerentes com o conceito de Todd e Morgana e fica imediatamente antes do `AnswerContract`. Isso deve produzir diferenca de perspectiva sem fatos diferentes nem bordoes. Em perguntas factuais simples a personalidade e deliberadamente leve. Voice guidance nao pode mais neutralizar Todd/Morgana num mesmo estilo generico. Evidencia local: **55/55 focados; 438/438 full regression; compileall PASS**. Proximo passo desta frente: executar/revisar E2E pareado de personalidade com prompts novos antes de recalibrar novamente.

## Personality quality — Human Conversation Baseline — ADR 0074 — 2026-08-26

Sem avanço de gate: **F5 permanece OPEN; F6 permanece BLOCKED** e a call segue pausada em F5c.11. Foi adicionado um instrumento de avaliação de conversa cotidiana após ADR 0073: `agent_human_quick` (5 episódios / 40 turnos) e `agent_human_baseline` (10 episódios / 80 turnos), com quatro roteiros Todd × Morgana literalmente pareados e duas salas compartilhadas. O runner real mantém sessão persistente e o relatório gera `latest.blind.md` para identificação cega dos agentes e rubrica humana de naturalidade. Não hardcodar respostas a partir da suíte; usar o transcript para calibrar aplicação de personalidade/protocolo social somente quando houver padrão consistente. Evidência: **442/442 regressão PASS; compileall PASS**. Próximo passo desta frente: executar `tools/windows/TESTAR_CONVERSA_HUMANA.bat` com o modelo alvo e revisar primeiro o blind report.

## Freeze 2026-08-26

Desenvolvimento ativo pausado. A frente experimental posterior ao ADR 0074 foi removida deste pacote. Consulte `FREEZE_BASELINE.md`. F5 permanece OPEN/pausado e F6 BLOCKED.
