# Roadmap canonico

## F0 — Foundation conversacional — CONCLUIDA

- [x] provider/model portavel;
- [x] Response Contract Pipeline;
- [x] pragmatica/context provenance;
- [x] standard/mega E2E;
- [x] model bakeoff;
- [x] Gemma 3 12B baseline recomendado;
- [x] reorganizacao estrutural;
- [x] standard real pos-organizacao 11/11 · 64/64.

## F1 — Sistema, participantes e Presence UI — CONCLUIDA COMO BASE

- [x] Campanario != agente;
- [x] Morgana default primary speaker;
- [x] Todd/Morgana participantes persistentes;
- [x] AgentRouter;
- [x] ParticipationArbiter;
- [x] multi-speaker/provenance;
- [x] Presence UI orientada a ambiente/call;
- [x] sem modos obrigatorios Todd/Morgana.

## F2 — Agent Personality Foundation — CONCLUIDA E CONGELADA

- [x] consolidar personalidade-core de Todd;
- [x] consolidar personalidade-core de Morgana;
- [x] definir traits / anti-traits / tendencies / boundaries;
- [x] definir comportamento social, tecnico, criativo, discussao e urgencia para cada agente;
- [x] formalizar anti-traits contra caricatura/bordoes;
- [x] quick personality E2E;
- [x] personality mega E2E;
- [ ] regressao de identidade em contexto longo;
- [x] Long Call textual + Long Context Grounding;
- [x] Conversation Focus Stack P2.3c (frames/tangentes/retomada/answer binding);
- [x] revalidar Long Call P2.3c com Gemma 3 12B (seed 1787671154);
- [x] P2.3d Long Call Grounding Hardening: briefing sem metalinguagem interna + referente imediato + correction anchor cross-turn + anti-hallucination de componentes;
- [x] revalidar Long Call P2.3d com Gemma 3 12B (seed 1787678674: 233 PASS / 8 WARN / 0 FAIL);
- [x] P2.3e Reference Binding + Ambient Call Semantics;
- [x] revalidar Long Call P2.3e com Gemma 3 12B (seed 1787679961: 237 PASS / 11 WARN / 1 FAIL; revelou limite do prompt-based binding);
- [x] P2.4 Dialogue State Compiler: estado tipado antes da geracao, sem segunda inferencia;
- [x] revalidar Long Call P2.4 com Gemma 3 12B (seed 1787680836: 244 PASS / 12 WARN / 0 FAIL; Dialogue State ainda era tratado como contexto descritivo);
- [x] P2.4.1 Answer Contract: binding final depois de persona/social + validacao local/retry unico para contratos criticos;
- [x] revalidar Long Call P2.4.1 com Gemma 3 12B (seed 1787681697: 254 PASS / 2 WARN / 0 FAIL);
- [x] P2.4.2 Conversational Commitment & Contribution Contract: decisao aceita, contribuicao distinta e Embodiment Boundary;
- [x] revalidar Long Call P2.4.2 com Gemma 3 12B (seed 1787682411: 256 PASS / 3 WARN / 0 FAIL; falhas estruturais fechadas, restou polish de naturalidade);
- [x] P2.4.3 Freeze Candidate Polish: contribuicao distinta mais forte sob `nao repete`, respostas triviais curtas, sem jargon interno em semantica social, checker de silencio ampliado;
- [x] revalidar Long Call P2.4.3 com Gemma 3 12B (seed 1787683144: 255 PASS / 2 WARN / 2 FAIL; um falso negativo aritmetico + repeticao semantica em `nao repete`);
- [x] P2.4.4 Freeze Gate Fixes: criterio social novo, check aritmetico por valor equivalente e despedida curta sem commitment indevido;
- [x] revalidar Long Call P2.4.4 com Gemma 3 12B (seed 1787683779: 253 PASS / 2 WARN / 0 FAIL; WARNs contextuais aceitos em revisao humana);
- [ ] regressao de factualidade compartilhada;
- [ ] validar diferenca perceptivel Todd vs Morgana com mesmos prompts;
- [x] validar multiagente: complementar, discordar, interagir e evitar overtalk;
- [x] Long Call Behavioral E2E textual: 3 calls longas, continuidade + latencia + retomadas;
- [x] congelar Personality / Social / Long-Call Baseline v1 (ADR 0049).

## F3 — Platform Foundation / Runtime v2

**Somente depois de congelar F2. Esta e a base maior para Web, Desktop, Mobile, Call, Wake, Tools e Patrulha.**

Documento de handoff: `docs/current/PLATFORM_FOUNDATION_HANDOFF.md`.

- [x] PF1a: separar boundary logica Campanario Runtime de API/UI (ADR 0050);
- [x] PF1a: runtime componivel e testado sem navegador/FastAPI;
- [x] PF1b: lifecycle/hosting persistente + boundary API/runtime estabilizados (ADR 0051);
- [x] SessionManager/ConversationService client-independent no boundary PF1;
- [x] PF2: Event Bus com contratos versionados, ordem, provenance e replay basico (ADR 0052);
- [x] PF3: Realtime/API Gateway (`/api/v1`, `/ws/v1`) + Web UI migrada incrementalmente (ADR 0053);
- [x] PF4: Device Registry persistente + capabilities por dispositivo + reconnect por identidade (ADR 0054);
- [x] PF5: Capability/Tool Registry provider-independent (ADR 0055);
- [x] PF6: Permission/Trust Layer (pairing, confirmacao, revogacao, audit) (ADR 0056);
- [x] segundo cliente de teste conectado ao mesmo runtime (PF7 / ADR 0057);
- [x] PF3: reconexao WebSocket por `after_sequence` sem criar nova sessao;
- [x] PF4: disconnect/reconnect de device preserva a mesma identidade persistente sem duplicar agentes/memoria;
- [x] PF7: reconexao multi-client sobre a mesma sessao/contexto sem duplicar sessao, memoria ou agentes (ADR 0057);
- [x] Web UI existente migrada para `/api/v1` + `/ws/v1/events`, com `/api`/SSE legado preservado;
- [x] telemetria de latencia preservada/expandida no runtime (ADR 0060);
- [x] PF8: Mobile Readiness com cliente remoto minimo autenticado, mesma sessao/reconnect e `location.current` de teste (ADR 0058);
- [x] PF9: Voice / Call Readiness de contratos, sem STT/TTS final e sem segundo pipeline cognitivo (ADR 0059);
- [x] F3 closure: telemetria runtime + E2Es/ADRs finais; Runtime v2 congelado (ADR 0060);

**Gate F3:** Web + segundo cliente observam a mesma sessao/contexto, capability remota funciona sob Permission Layer e todos os Behavioral/Long Call anteriores continuam verdes.

## F4 — Experience / Learning Layer

**CONCLUIDA no ADR 0061 — Experience / Learning Baseline v1.**

Somente depois de F2 e sobre a base de runtime de F3.

- [x] memoria experiencial com source/provenance;
- [x] preferencias de comunicacao aprendidas;
- [x] experiencias compartilhadas usuario/agentes;
- [x] relacao Todd<->usuario, Morgana<->usuario e Todd<->Morgana sem duplicar fatos;
- [x] inferencia separada de fato;
- [x] confidence/recency;
- [x] correcao e esquecimento;
- [x] anti-drift do core da personalidade;
- [x] inspecao administrativa da memoria aprendida;
- [x] testes de aprendizagem e continuidade entre reinicios.

## F5 — Realtime Presence / Call / Multi-client

**GATE ATUAL.** F3 + continuidade minima de F4 estao concluidas.

- [x] estados PRESENTE / ATENTO / ENGAJADO no runtime (ADR 0062);
- [~] wake `Campanario` semantico implementado; detector de audio real ainda pendente;
- [x] endereco direto `Morgana` / `Todd` preservado para o AgentRouter;
- [ ] VAD + STT streaming;
- [ ] TTS separado por agente;
- [~] interruption cooperativa no gateway; corte de playback/media ainda pendente;
- [x] janela conversacional continua sem repetir wake;
- [ ] attention/participation arbiter para call real;
- [ ] audio background/service;
- [x] cliente mobile minimo pareado ao mesmo runtime (PF8, revalidado em F5);
- [x] handoff de Call PC<->mobile preservando call_id/session_id sem nova persona;
- [ ] shell desktop/tray/hotkey quando apropriado.

## F6 — Capabilities, Knowledge e Modo Patrulha

- [ ] RAG/biblioteca local;
- [ ] web/grounding;
- [ ] mapa/localizacao/rotas;
- [ ] clima/transito/locais proximos;
- [ ] notes/capture/fotos deliberadas;
- [ ] tools/automacao sob Permission Layer;
- [ ] integracoes externas;
- [ ] proactive layer controlada;
- [ ] Modo Patrulha sobre a mesma Call/Runtime, conforme `docs/concept/MODO_PATRULHA_V2.md`;
- [ ] debrief/historico de patrulha e integracao com Experience Layer.

## F7 — Production Readiness / Memory Clean Start

**Somente quando o Campanario estiver funcional de ponta a ponta e pronto para comecar uso real. Nao e gate antecipado de memoria nem pre-requisito isolado de voz.**

- [ ] concluir e estabilizar as fases necessarias para uso cotidiano real;
- [ ] executar regressao final Behavioral/Long Call, runtime, devices, tools e memoria;
- [ ] inspecionar e exportar apenas fixtures/evidencias de desenvolvimento que precisem ser preservadas;
- [ ] apagar episodios, fatos, preferencias e experiencias aprendidas durante desenvolvimento/testes;
- [ ] preservar Personality Core, codigo, schemas/migrations, contratos versionados e fixtures isoladas;
- [ ] validar boot, identidade, memoria vazia e anti-drift depois do reset;
- [ ] criar snapshot **Usage Learning Baseline v1**;
- [ ] criar **Recovery/Reinstall Kit v1** para formatacao/falha grave: manifesto de release/dependencias/modelos, restauracao de dados/configuracao, verificacao de integridade/migrations e opcao de midia offline/USB sem segredos embutidos por padrao;
- [ ] provar reinstalacao limpa em maquina/ambiente vazio antes do uso cotidiano real;
- [ ] a partir desse marco, novas conversas passam a formar a historia relacional/experiencial de uso real.

Esse reset nao treina/fine-tuna o modelo-base; ele cria uma origem limpa para aprendizagem por memoria e experiencia quando o sistema ja estiver pronto para uso real.

## Regra de sequenciamento

**Nao iniciar Platform/Voice/Mobile porque a UI ja parece pronta. Primeiro fechar F2. Depois construir F3 Platform Foundation antes de espalhar funcionalidades por clientes. Experience vem sobre essa base e voz/mobile reutilizam o mesmo runtime.** A Presence UI prepara o destino; nao libera pular gates.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.


## F5b checkpoint — ADR 0063
Binary PCM media now crosses the existing Call gateway through provider-independent VAD/STT/TTS boundaries and reuses the same conversation/session. F5 remains active until target-host microphone/speaker, real engines, barge-in and latency are proven. Next: F5c host voice integration; F6 remains blocked.

## F5c checkpoint — ADR 0064

Host voice integration is implemented for the Windows target using configurable local whisper.cpp STT, Windows SAPI TTS and sounddevice microphone/speaker I/O. Automated gates are green. **Next gate: F5c Host Acceptance / Voice Ready Gate on the target PC.** Do not advance to F6 until microphone -> STT -> shared conversation -> agent-specific audible TTS, barge-in and perceived latency are physically verified.

## F5c.1 — Voice Capture / Portuguese STT stabilization

- [x] idioma STT efetivo observavel no diagnostico;
- [x] contrato testado de `-l pt` no whisper.cpp;
- [x] protecao contra modelo `.en.bin` com idioma nao-ingles;
- [x] prompt curto pt-BR / nomes do dominio;
- [x] filtro estreito de anotacao pura de nao-fala;
- [x] duracao minima de fala antes de STT;
- [x] launcher preserva extra `voice-host`;
- [x] tools Windows reorganizadas sem apagar regressao historica;
- [ ] revalidacao fisica pt-BR no PC alvo;
- [ ] depois: tuning de VAD/self-hearing/barge-in somente se a evidencia fisica ainda exigir.

F6 continua bloqueada ate o freeze de F5.


### F5c.2 — Voice Runtime Wiring
- [x] Normal Windows launcher wires local Whisper/SAPI into the same runtime used by `/ws/v1/call`.
- [x] Preserve conservative unconfigured defaults when host assets do not exist.
- [ ] Physical Portuguese capture E2E re-run on Windows host.

### F5c.4 — Physical Voice Checkpoint Freeze (ADR 0067)
- [x] physical microphone -> Host Voice -> authenticated Call transport proven on target Windows PC;
- [x] STT final reaches the same shared Conversation Runtime and returns an agent response;
- [x] missing-STT loop is fail-fast;
- [ ] pt-BR recognition acceptance: current physical evidence is materially wrong (`Campanario, voce esta ai?` -> `O Brasil e o maior.`);
- [ ] verify effective multilingual Whisper model and `-l pt` on target host;
- [ ] short pt-BR acceptance set with silence/noise checks;
- [ ] tune VAD/capture only if evidence still requires it;
- [ ] freeze playback/barge-in/perceived-latency acceptance.

**F5 remains the only active gate. F6 remains blocked.**


## Trilha V9 + V9.1 — Integração completa dos cérebros (experimental / opt-in)

**Documento executável de planejamento:** [`ROADMAP_V9_CEREBROS_COMPLETO.md`](ROADMAP_V9_CEREBROS_COMPLETO.md).  
**Runbook de contingência:** [`../operations/FAILSAFE_V9_CEREBROS.md`](../operations/FAILSAFE_V9_CEREBROS.md).

**NÃO altera o gate canônico:** F5/aceite físico de voz continua aberto; liberação formal de F6 e F7 exige os respectivos critérios já descritos acima. A trilha V9 pode avançar em código/testes isolados, sem declarar F6 concluída, com a flag `CAMPANARIO_BRAINS_V9_ENABLED=false` por padrão.

| Trilha | Prioridade | Situação documentada em 19/11/2026 | Condição de encerramento |
|---|---|---|---|
| R0 — Baseline das 3 pastas e host | P0 | [~] Base IA auditada; Python/Database reais não disponíveis | Backup/restore de cópia + Python 3.12/Windows/Ollama + contratos das 3 pastas |
| R1 — Sandbox e permissão única | P0 | [~] Worker separado para Conhecimento/Análise com kill em timeout e limite RSS monitorado; leitura ligada à PermissionPolicy. **Não é sandbox de segurança**; APIs de utilidades ainda distintas | Isolamento OS de diretórios/rede/processos, política unificada em todas as rotas, aceite Windows e fault injection real |
| R2 — Planejador colaborativo | P0 | [~] R2 parcial: plano tipado e sequência Conhecimento→Análise (somente leitura), sem comparação semântica | Integração factual cross-brain, cache, permissão/isolamento R1 e homologação host |
| R3/R4 — Conhecimento e Análise sólidos | P0/P1 | [~] Dois executores reais reutilizam V8 | Evidências/páginas reais, planilha reproduzível, citações e fallback corretos |
| R5 — Investigação e Estratégia | P1 | [ ] Catálogo apenas, sem executor | Executors tipados, health-check e testes independentes |
| R6 — Programação | P1 | [ ] Indisponível | Sandbox R1 + diffs/autorização/rollback testados |
| R7 — Percepção | P1/P2 | [ ] Indisponível | Modelo local, provenance/consentimento; mídia segue F5 |
| R8 — Comunicação e Criação | P1/P2 | [ ] Indisponíveis | Executors integrados ao validador V9.1; sem novas alegações |
| R9 — Forja, talentos e `.campagent` | P1/P2 | [~] MVP de fichas, 8 arquétipos e 6 talentos | Preconditions completas, UI/mobile e pacote hostil testados |
| R10 — Homologação integrada | P0 release | [ ] 1.029 testes passaram, 31 falhas conhecidas (grupos disjuntos, Linux/Python 3.13); sem host real | 8 cérebros comprovados + falhas triadas + SLIs medidos + F5/F6/F7 |

**Regras inegociáveis:** política/permissões > integridade factual > pedido > tarefa > talento > estilo; memórias e personalidade não migram para cérebros; ferramenta sem execução não gera fonte; falha de validação retorna resposta canônica/limitação. Arquétipos não bloqueiam capacidades, e registro no catálogo não substitui implementação. O roadmap detalhado define subtarefas, testes de aceite, dependências, entregáveis, métricas e rollback por fase. **Acrescentar esta trilha aos documentos não implementa as pendências.**


### Checkpoint P0 da trilha V9 (19/11/2026) — parcial

- [x] Diagnóstico de layout de `CAMPANARIO-IA` + `.venv` externa em `CAMPANARIO-PYTHON` + `CAMPANARIO-DATABASE/dados`/`zim` e SQLite, acessível pela Central de Cérebros com flag desligada; somente leitura.
- [x] Testes sintéticos e defesas no executor contra escopo de permissão não concedido e `trace_id`/`brain_id` falsos.
- [x] Procedimento de atualização por cópia via Explorador, sem PowerShell para substituir arquivos de código.
- [ ] Homologação das **pastas reais** Python/Database, backup/restore em cópia, Python 3.12/Windows e Ollama/voz/mobile.
- [ ] Sandbox isolado e política única com permissões reais; **P0 não está concluído e F5/F6 seguem bloqueados**.

Veja [`P0_TRES_PASTAS_SEM_POWERSHELL.md`](P0_TRES_PASTAS_SEM_POWERSHELL.md), [`ROADMAP_V9_CEREBROS_COMPLETO.md`](ROADMAP_V9_CEREBROS_COMPLETO.md) e [`FAILSAFE_V9_CEREBROS.md`](../operations/FAILSAFE_V9_CEREBROS.md) para a arquitetura, as dependências, as instruções sem console e os gates restantes.

**Exceção de banco identificada no P0:** a Biblioteca Conversacional V2 ainda tem fallback de SQLite de referência em `IA/data/interaction_library_v2.sqlite`. O código agora prefere o arquivo em `DATABASE/dados/reference/` quando disponível, sem mover dados automaticamente; a cópia/homologação no host está pendente. Consulte o roadmap V9 e FAILSAFE para não confundir isso com `campanario.db` pessoal.


### Checkpoint R1 incremental (19/11/2026) — processo controlado, gate ainda aberto

- [x] `brains/worker.py` executa apenas Conhecimento/Análise existentes em subprocesso Python da instalação (sem shell, código de usuário, serialização pickle ou modelo extra). `brains/isolation.py` limita a espera e **encerra o processo** no timeout, monitora RSS por `psutil`, valida JSON/tamanhos e devolve dados estruturados ao chat. Limites de memória observados por amostragem, não quota OS infalível.
- [x] O executor consulta a `PermissionPolicy` compartilhada do runtime para leitura de biblioteca quando inicializado pela composição canônica. Contexto ausente falha fechado. O endpoint de prévia usa contexto criado no backend local; builds e talentos não são fonte de autorização. Testes de recusa e subprocesso travado adicionados.
- [ ] Faltam integração uniforme de `utilities/api.py` à política central, autorização real de clientes pareados, sandbox OS sem rede/fora da pasta, job-object no Windows, cancelamento de árvores não confiáveis, comportamento do EXE congelado com interpreter sidecar e teste em Python 3.12/Windows real. **Programação, rede e ações sensíveis permanecem proibidas como cérebros**.
- [ ] R0 continua pendente na instalação real: acesso a `CAMPANARIO-PYTHON/.venv`, `CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db` e ZIM/referência, backup/restore em cópia, migração e Ollama.

Atualizações do código continuam por **cópia manual de arquivos pelo Explorador**, com Campanário fechado e backup; PowerShell é opcional somente para instalar/reparar dependências, migrações planejadas e diagnósticos técnicos. Ver `docs/current/R1_ISOLAMENTO_CEREBROS.md` e `docs/operations/FAILSAFE_V9_CEREBROS.md`.


## Trilha experimental V9 — checkpoint R1.1 (não promove F5/F6)

A R1.1 implementa orçamento total de tempo para o plano de cérebros, contenção de falhas sucessivas, higiene de ambiente e cancelamento de worker de leitura. **A R1 ainda não está homologada:** sem sandbox OS/Job Objects, autorização unificada das utilidades ou teste nas três pastas reais. A sequência R1 pendente → R2 tipada permanece em [`ROADMAP_V9_CEREBROS_COMPLETO.md`](ROADMAP_V9_CEREBROS_COMPLETO.md), com procedimentos de falha no [`FAILSAFE_V9_CEREBROS.md`](../operations/FAILSAFE_V9_CEREBROS.md). As fases F5/F6 permanecem com seus gates próprios.


## Checkpoint experimental R2 — planejamento tipado (19/11/2026)

Sobre R1.1, a R2 acrescenta `BrainStep`/`BrainPlan`, dependências ordenadas, trace real de evidências e apresentação conjunta **somente** de Conhecimento e Análise quando o usuário menciona explicitamente um documento **e** uma planilha. O `CollaborationSnapshot` consolida dados canônicos com fontes reais antes da expressão por Morgana/Todd e deixa claro que **não** executou comparação semântica. Nenhum dos outros seis cérebros foi ativado.

**Gates R0/R1/R2 continuam pendentes** para o release: sandbox OS, utilidades com permissões centralizadas, Windows 3.12, três pastas e restore no host, Ollama/mobile e análise semântica cross-brain. Regressão no ambiente de teste: **1.029 PASS / 31 falhas históricas sem novas falhas** (1.022 testes legados + 7 novos; grupos disjuntos). Ver [`R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md`](R2_PLANEJAMENTO_COLABORACAO_CEREBROS.md), [`RESULTADOS_TESTES_R2.md`](../operations/RESULTADOS_TESTES_R2.md) e [`FAILSAFE`](../operations/FAILSAFE_V9_CEREBROS.md). Atualização de arquivos por cópia no Explorador, sem PowerShell; não alterar `.env`, `.venv` externa ou SQLite de usuário.

### Trilha experimental de cérebros — checkpoint R2.1 (19/11/2026)

A R2.1 acrescentou contratos `optional|required` para dependências, checagem de proveniência first-party e exigência de contexto de autorização explícito no registro de capacidades **quando V9 está ativada**. Isso NÃO libera F6, não conclui R0/R1/R2 e não inclui `/api/v1/utilities/invoke` na mesma política. O roadmap detalhado e o FAILSAFE documentam os gates abertos e a topologia IA / `.venv` externa no Python / Database externo. Ver `ROADMAP_V9_CEREBROS_COMPLETO.md`, `R21_DEPENDENCIAS_PROVENIENCIA_PERMISSOES.md` e `../operations/FAILSAFE_V9_CEREBROS.md`.
