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

### Checkpoint R2.2 — Ponte conservadora de permissões para utilidades (23/11/2026)

- [x] Código: `utilities/api.py` consulta `PermissionPolicy` do runtime ao executar ferramentas via HTTP local, **somente quando V9 está ativada**. A identidade é criada no boundary local, não importada de argumentos/headers do cliente.
- [x] Leitura exige decisão central `ALLOW`; resposta `DENY` não executa ferramenta. Erro/indisponibilidade da política bloqueia acesso (503).
- [x] Escritas (`WRITE`), uploads Base64 e uploads streaming exigem decisão central `ALLOW`; `confirm=true` no JSON não substitui aprovação PF6. Downloads de originais passam pela checagem central de leitura.
- [x] Com `CAMPANARIO_BRAINS_V9_ENABLED=false`, comportamento HTTP legado mantido; testes direcionados passam.
- [ ] **Gate R1 aberto**: falta fluxo seguro de aprovação PF6 no cliente de utilidades (nesta versão, escritas e uploads no modo V9 normalmente recebem 403), autenticação de principal humano, cobertura de outras rotas como catálogo/status, isolamento OS e teste Windows real. Não confundir essa ponte com autorização unificada de todas as superfícies.
- [ ] **F5 continua gate canônico**, com reconhecimento pt-BR, playback, barge-in e latência física sem aceite; F6 e release continuam bloqueados.

**Três pastas preservadas:** `CAMPANARIO-IA` guarda este código; `CAMPANARIO-PYTHON/.venv` é externa (Python 3.12 alvo), não distribuída; `CAMPANARIO-DATABASE` contém dados persistentes/SQLite e ZIM, não modificado nem incluído neste incremento. A biblioteca de referência V2 já existente no IA permanece como fallback, sem migração automática. Não foi possível testar as duas pastas externas.

**Próximo incremento recomendado:** R1, implementar aprovação explícita PF6 com principal de usuário autenticado para o navegador de utilidades, garantindo escopo por operação, uso único e trilha de auditoria; em seguida testar fault injection e isolamento efetivo no Windows sem habilitar cérebros perigosos. A trilha R2 permanece parcial. Consulte `docs/operations/RESULTADOS_TESTES_R22.md`.

### Checkpoint R2.3 — Endurecimento de confirmações PF6 (23/11/2026)

- [x] Em `runtime/permissions.py`, confirmação PF6 agora expira em cinco minutos e exige correspondência de principal, dispositivo, sessão, permissão, capacidade e escopo; bloqueia reaprovação, replay concorrente e crescimento ilimitado de pendências. Sem novos endpoints ou permissões.
- [x] Testes locais de expiração, troca de contexto, reuso simultâneo e trilha de auditoria: `tests/test_r23_pf6_confirmation_hardening.py`.
- [ ] **R1 continua parcial**: aprovação humana autenticada na UI não foi criada; o método interno `approve` NÃO é autenticação humana. Escritas/uploads HTTP V9 permanecem bloqueadas sem autorização adequada. Faltam isolamento de SO e testes Windows.
- [ ] Manter F5 (voz física), F6 e F7 nos seus gates anteriores, sem promoção automática.

**Próxima etapa:** implementar identidade humana autenticada e consentimento explícito de operação na interface, sem endpoint de autoaprovação; depois teste de sandbox Windows. Preservar `CAMPANARIO-IA` (código), `CAMPANARIO-PYTHON/.venv` (Python 3.12 compartilhado externo) e `CAMPANARIO-DATABASE` (SQLite, Biblioteca V2, memórias e documentos), sem criar cópias ou migrar bancos durante merge do ZIP. Ver `docs/operations/FAILSAFE_V9_CEREBROS.md` e `RESULTADOS_TESTES_R23.md`.


### Checkpoint R2.4 — Aprovação local PF6 opt-in (23/11/2026)

- [x] API `/api/v1/utilities/confirmations/request` cria solicitação da `PermissionPolicy` para ferramenta WRITE conhecida; argumentos são vinculados ao escopo `operation:sha256` por JSON canônico. O token nunca é fornecido na solicitação.
- [x] API `/api/v1/utilities/confirmations/approve` exige credencial local do proprietário `CAMPANARIO_PF6_OWNER_TOKEN` forte (mínimo 32 caracteres, até 256) configurada privadamente; verifica confirmação, ferramenta, escopo, principal, reconhecimento explícito e validade antes de aprovar. Ausente = indisponível, sem autoaprovação. Segredo nunca é salvo pelo frontend nem incluído no ZIP.
- [x] Interface `ferramentas.js` revisa argumentos e exige credencial via prompt, por operação. `/invoke` aceita token PF6 fora dos argumentos; token é consumido somente na operação exata e uma vez. A confirmação legada do `UtilityService` permanece, não substitui PF6.
- [x] Regra `utilities.write` agora usa `SCOPED_CONFIRM` no runtime (somente V9); leitura e V9 desligado preservados. Upload binário/Base64 sem fluxo PF6 continuam NEGADOS em V9. Nenhuma migração, banco, `.venv` ou alteração em outros repositórios.
- [x] 36 testes direcionados aprovados e `node --check` aprovado no ambiente Linux. Suíte ampla: 530 aprovados até primeira falha de `test_g2_grounding_audit`, reproduzida no ZIP R2.3 sem alteração; suíte total NÃO aprovada.
- [ ] **R1 NÃO FECHADO:** a credencial local é prova de posse de um segredo, não identidade humana ou sessão autenticada com revalidação/revogação. Browser pode sofrer XSS; falta autenticação individual, CSRF hardening completo, proteção física da máquina, rate limiting, UI não baseada em prompt, autorização de uploads, isolamento SO/Windows Job Objects, testes reais Windows/Python 3.12 e testes dos repositórios separados. Não habilitar Programação ou expansão invasiva.

**Próxima etapa:** R2.5: revisar autenticação individual/sessões reais e UI de consentimento resistente a XSS/CSRF, revogação, limites de tentativas e ciclo de vida; em paralelo homologar Windows 3.12, baseline da suíte ampla e F5 físico. Topologia preservada: `CAMPANARIO-IA` código e interface, `CAMPANARIO-PYTHON/.venv` Python externo, `CAMPANARIO-DATABASE` SQLite/documentos/memórias persistentes externos.


### Checkpoint R2.5 — Sessões locais PF6 e revogação (23/11/2026)

- [x] Em `utilities/pf6_sessions.py`, sessão PF6 **temporária em memória** (15 minutos desde login, no máximo 32 sessões), token aleatório armazenado somente como SHA-256 no servidor, vinculado à impressão da credencial do proprietário; rotação da credencial invalida sessões existentes, reinicialização do processo também. Sem persistência, migrations ou usuários artificiais.
- [x] Rotas locais `/api/v1/utilities/sessions/login` e `/sessions/logout`, com limite de cinco falhas de login por cliente local / janela de bloqueio de 60 segundos. O segredo não é retornado; tokens não vão para URL, cookies ou logs de auditoria. É limitação por processo, não proteção contra ataques distribuídos.
- [x] As rotas PF6 de solicitação, aprovação e execução de escrita com token exigem **a mesma sessão autenticada**; `AuthorizationContext.session_id` atravessa a `PermissionPolicy`. Logout/expiração/rotação do segredo invalidam a execução de token de confirmação ainda não consumido. Mantém escopo exato e uso único da R2.3/R2.4.
- [x] UI de ferramentas mantém token de sessão somente na memória da aba, disponibiliza botão de logout e nunca grava token em `localStorage` ou cookies. Mantido `prompt` legado para digitar a credencial: revisão visual e consentimento ainda dependem da interface e do navegador confiável. Sem mudanças no Dark Matter, na expressão V9.1 ou na Biblioteca V2.
- [x] 41 testes direcionados passaram; `node --check` passou. Suíte ampla interrompida na falha de grounding G2 **preexistente no R2.3/R2.4**, após 530 aprovações; NÃO homologar o todo.
- [ ] **R1 permanece aberto:** sessão de proprietário compartilhado NÃO é identidade individual, grupos de usuários, MFA, isolamento contra XSS, sandbox de SO, CSRF de todos os endpoints, upload autorizado, testes Windows 3.12 e testes das três pastas reais ainda não concluídos. `VERSAO.json` não é número do incremento; não inventar release binária.

**Próximo incremento recomendado:** R2.6: substituir `prompt` por diálogo acessível que apresente diff/escopo, implementar identidade humana individual robusta compatível com offline e fortalecer defesas XSS/CSRF; depois realizar homologação Windows 3.12/Job Objects, F5 físico e gate R1. **Topologia invariável:** código e interface em `CAMPANARIO-IA`, Python 3.12 e `.venv` compartilhada externa em `CAMPANARIO-PYTHON`, SQLite/memórias/conversas/Biblioteca V2/documentos e dados persistentes em `CAMPANARIO-DATABASE`. Merge apenas por Explorador de Arquivos com backup.


## Checkpoint transversal R2.6 — Consentimento PF6 Web (23/11/2026)

R2.6 adiciona diálogo nativo para credencial e revisão exata de operações PF6, sem `prompt` de credencial nem `confirm` de aprovação V9; parâmetros exibidos como texto. API de utilidades reforça Fetch Metadata/Origin, e a página de ferramentas recebe CSP restritiva para scripts e frames. Testes direcionados 22 PASS, suite geral 530 PASS/1 FAIL G2 preexistente ao interromper; regressão não aprovada. **F5 permanece gate principal aberto; R1 segurança V9 permanece parcial; F6/F7 não liberadas.** Não há identidade individual, sandbox Windows nem homologação de navegador real. Próximo incremento R2.7: identidade offline, auditoria XSS e validação Windows. Continuam três pastas: CAMPANARIO-IA código, CAMPANARIO-PYTHON com `.venv` externa compartilhada, CAMPANARIO-DATABASE persistente (SQLite, Biblioteca V2, memórias, conversas e documentos). Sem mudança de esquema, migração ou duplicação. Ver FAILSAFE V9 e resultados R2.6.


## Checkpoint R2.7 — Identidades PF6 individuais opcionais (23/11/2026)

**Incremento implementado (R1 ainda PARCIAL):** `utilities/pf6_identities.py` permite configurar voluntariamente operadores locais nomeados (`CAMPANARIO_PF6_USERS_JSON`) com verificadores PBKDF2-HMAC-SHA256 (600.000 iterações, salt individual de 16 bytes). Identificadores validados (3–32 caracteres ASCII definidos) e credenciais de no mínimo 16 caracteres para novos verificadores. Sem novo banco ou conta padrão; verificadores permanecem no `.env` privado, não em ZIP, IA ou Database. O login de Ferramentas aceita nome de usuário e senha, continua com sessões de 15 minutos, lockout de cinco tentativas/60 segundos por cliente e revogação em memória. Ao configurar contas individuais, a senha antiga `CAMPANARIO_PF6_OWNER_TOKEN` **não** permite login ou bypass no modo individual; no modo antigo sem contas configuradas, o proprietário continua compatível.

**PF6 e auditoria:** `principal_id=pf6-user:<nome>` percorre solicitação, aprovação e invocação e é gravado nas trilhas de política existentes. O token PF6 ainda é escopado à operação exata, sessão e principal, one-shot/TTL de cinco minutos. Alteração do conjunto de verificadores invalida sessões individuais existentes; configuração não vazia malformada é erro fechado 503 e nunca aceita segredo proprietário como fallback. A interface Dark Matter passou a mostrar campo opcional de usuário, mantendo segredo e bearer em memória temporária, nunca em LocalStorage.

**Validação observada (Linux):** 27/27 testes direcionados PASS; `node --check` PASS; regressão geral `pytest -q -x`: 530 PASS / 1 FAIL no G2 (`test_false_claim_never_streamed_or_saved`), mesma falha pré-existente R2.3–R2.6; suíte não aprovada. Integração real com navegador, Windows 3.12, mobile, Ollama e repositórios externos não testada. Revisão de XSS/CSRF limitada à superfície Ferramentas, sem alegar auditoria global. Sem sandbox Windows/Job Objects, MFA, ACL individual por capacidade, identidade por OS ou autenticação de clientes remotos; falhas não devem liberar os outros seis executores nem F6/F7.

**Próximo desenvolvimento sugerido R2.8:** revisão de permissões/ACL por usuário, sessão e rota para todo o sistema; auditoria da UI e E2Es reais Windows/mobile, sandbox SO e resolução da falha G2. **Três pastas intactas:** `CAMPANARIO-IA` contém código e interface, `CAMPANARIO-PYTHON` contém Python e `.venv` externa compartilhada, `CAMPANARIO-DATABASE` mantém SQLite, Biblioteca V2, memórias, conversas e documentos persistentes. Sem migrations nem duplicação de dados. A instalação e rollback são feitos por mesclagem/restauração apenas da pasta IA no Explorador de Arquivos, com backups privados independentes antes de qualquer alteração. Ver FAILSAFE e `RESULTADOS_TESTES_R27.md`.


## Checkpoint R2.8 — ACL individual deny-only e documentação técnica obrigatória (23/11/2026)

- [x] `utilities/pf6_acl.py` valida lista privada explícita por identidade/ferramenta de escrita e recusa desconhecidos, curingas, duplicados e configuração inválida; sem ACL, contas individuais **não** escrevem. Não há novo banco/venv.
- [x] `utilities/api.py` aplica este filtro **antes** de solicitar/aprovar consentimento e **de novo** antes de executar a operação; política central PF6 e escopo exato continuam obrigatórios. ACL nunca concede uma permissão.
- [x] Manual didático vivo `docs/governance/MANUAL_TECNICO_VIVO.md`, procedimento obrigatório `docs/governance/PROCESSO_OBRIGATORIO_DE_DESENVOLVIMENTO.md`, gate estático `scripts/check_documentation_gate.py` e CI bloqueando documentação ausente/dessincronizada.
- [x] Testes direcionados dos mecanismos PF6: 28 PASS no Linux/Python 3.13; relatório em `docs/operations/RESULTADOS_TESTES_R28.md` (sujeito a validação complementar, sem homologação Windows).
- [ ] **R1 e F5 continuam abertos**: ainda faltam sandbox OS no Windows, autenticação ligada ao OS, RBAC da leitura, auditoria XSS/CSRF global e aceites reais da voz/mobile/Ollama. Outros seis cérebros permanecem sem executores. Não declarar R10.

**Próximo passo recomendado:** R2.9 — auditoria e testes de endpoints e superfícies XSS/CSRF, leitura/catalog/status, compatibilidade e verificação Windows; não liberar F6 sem aceite físico de F5. **Processo obrigatório em TODA próxima entrega:** atualizar simultaneamente ambos ROADMAPs, FAILSAFE e Manual Vivo, além de changelog, instruções e testes; executar gate documental. Três pastas: código somente em `CAMPANARIO-IA`; `.venv` externa única em `CAMPANARIO-PYTHON`; SQLite, biblioteca e memórias persistentes em `CAMPANARIO-DATABASE`. Não distribuir segredos ou bancos; atualizar IA por cópia no Explorador e ter rollback.


## Checkpoint R2.9 — fronteira factual dos cérebros (23/11/2026)

**Prioridade deliberada:** factualidade cérebro → agente. A F5 física de voz permanece pendente e não faz parte deste incremento; nenhuma promoção automática de F6. Este checkpoint não substitui o planejamento de segurança de endpoints da R2.9 original, agora explicitamente **pendente / reprogramado**, e não fecha R1.

- [x] Em `chat/grounded_expression.py`, resultados canônicos marcados com `brain_ids` e modo factual são emitidos sem nova chamada gerativa ao LLM; somente uma introdução fixa por agente precede o texto canônico intacto. Respostas sem evidência suficiente são retornadas literalmente, sem personalização que simule sucesso.
- [x] Em `chat/service.py`, o conteúdo canônico de um resultado de cérebro prevalece sobre extratos auxiliares antes da camada de expressão. A classificação factual e as referências continuam sob responsabilidade do compilador/runtime, não do agente.
- [x] Testes automatizados de não alucinação nesse limite, incluindo dois agentes, modelo hostil, fontes ausentes e compatibilidade legado. Resultados concretos em `docs/operations/RESULTADOS_TESTES_R29.md`.
- [ ] **Não concluído:** seis cérebros sem executor; qualidade real de recuperação/verdade das fontes; comparação semântica multifuentes, regressão total e homologação Ollama/Windows/3 repositórios. A validação heurística V9.1 continua para turnos não originados pelos cérebros.
- [ ] **R2.10 recomendada:** aprofundar verificações de suporte das afirmações de Conhecimento/Análise (incluindo contradições e escopo de evidência) antes de criar Investigação/Estratégia; retomar auditoria HTTP/XSS/CSRF e sandbox OS como dependências R1.

**Estrutura preservada:** `CAMPANARIO-IA` = código/interface; `CAMPANARIO-PYTHON` = Python e `.venv` externa única; `CAMPANARIO-DATABASE` = SQLite, Biblioteca V2, documentos e memórias persistentes. Sem migração, sem criar bancos ou ambientes. Manual Vivo/FAILSAFE/ROADMAP V9 atualizados juntos.


## Checkpoint R2.10 — vinculo literal de evidencias e conversa sem aviso generico (23/11/2026)

**Escopo:** foco em factualidade dos cerebros e roteamento de conversa; voz/F5 sem alteracoes (gate fisico permanece aberto). A compilacao factual de saidas individuais de cerebros V9 passou a exigir que cada afirmacao classificada `source_assertion` exista literalmente em um dos trechos vinculados a seus `source_ids`. Identificador valido sozinho nao comprova o texto; divergencia rebaixa a resposta para `not_found`, sem promover valores falsos. Calculos `computed` continuam sob o adaptador deterministico de Analise, sem tentativa de validar numeros por substring do documento. Conflitos continuam explicitos; nao ha verificacao semantica geral ou prova de verdade externa.

**Conversa natural:** perguntas subjetivas claramente identificadas deixam de acionar desnecessariamente biblioteca, ZIM e busca automatica; no caso objetivo sem fonte consultada, a resposta nao alega que uma busca foi executada ou estava desativada. Perguntas sobre identidade e atributos factuais sem fonte continuam sem chute. Roteamento conservador com testes para falsos positivos; perguntas abertas fora dos padroes cobertos ainda podem mostrar limitacoes anteriores. O modelo local ainda pode gerar erro em conversacao nao fundamentada: R2.10 nao garante verdade universal.

**Aceite realizado:** 76 testes direcionados PASS; regressao `pytest -q -x` 530 PASS e falha historica G2 de auditoria pessoal na primeira falha; gate documental e sintaxe verificados. **Nao** homologado Windows, Ollama, Database externo, fonte factual externa nem benchmark amplo de factualidade. R1 sandbox, R10 e seis executores futuros permanecem abertos. Os 3 repositorios continuam: IA=codigo e docs; PYTHON=.venv externa compartilhada; DATABASE=SQLite, biblioteca, memorias e historico.

**Proximo passo recomendado R2.11:** benchmark factual com casos de contradição, relacao de resposta com pergunta, citacoes e recuperacao mal sucedida; integrar um auditor de cobertura sem fabricar evidencias, investigar G2 e testar host real. Nao habilitar novos executores perigosos antes de R1. Toda entrega deve atualizar simultaneamente 2 ROADMAPs, FAILSAFE, Manual Vivo, changelog, instrucoes e relatorio de testes, e rodar o gate documental.


## Checkpoint R2.11 — auditoria de memoria pessoal e bateria factual (23/11/2026)

- [x] Restaurar a auditoria explicita G2 antes de qualquer token/persistencia de respostas de memoria pessoal: `chat/service.py` chama `verification_messages` e `verdict_supported`, exige quote do usuario e conserva o veto deterministico para intensidade/exclusividade nao licenciadas. Uma tentativa de reparo tem de passar pela mesma auditoria; caso contrario, cita literalmente o que foi dito ou admite ausencia de memoria.
- [x] Falta de evidencia pessoal nao autoriza a proposta do LLM. O caminho testa a auditoria e retorna desconhecido independentemente do parecer do modelo; nenhum banco externo e criado.
- [x] Adicionar matriz automatizada `tests/test_r211_evidence_audit.py` para pergunta versus atributo do trecho, divergencia entre documentos, alteracao de percentual mantendo source_id e resposta pessoal sem citacao. Este conjunto usa os validadores de relevancia/conflito existentes, **nao** representa um novo motor de implicacao semantica.
- [x] G2: casos do arquivo `test_g2_grounding_audit.py` agora passam nos testes direcionados; a suite ampla ultrapassou o bloqueio anterior. Depois de 601 PASS, parou em `test_knowledge_guard_v30.py::test_web_data_is_not_allowed_to_rewrite_instructions`. Esse mesmo teste falha no ZIP R2.10 original (baseline confirmado). Outro teste legado de HTML foi compatibilizado com um meta tag ASCII `CAMPANARIO`, sem alterar o visual.
- [ ] Suite geral integral, Windows/Python 3.12 externo, Ollama local real, semantica de evidencias, veracidade externa, testes com Database e atualizacoes de seguranca R1 permanecem abertos.

**Proxima etapa R2.12 proposta:** ampliar benchmark de relevancia/contradicao com corpus real e parametrizado, solucionar falhas legadas da pesquisa sem reduzir defesas de prompt injection e medir taxa de respostas pertinentes/abstencoes. Nao trabalhar em voz agora por preferencia do usuario, mas F5 continua aberta no ROADMAP. Os 8 cerebros sao 2 executores mais 6 catalogados. **Processo obrigatorio:** modificar em conjunto ROADMAP, ROADMAP V9, FAILSAFE, Manual Vivo, changelog, resultados, instrucoes e executar gate. Repositorios permanecem separados: IA codigo; PYTHON `.venv` unica externa; DATABASE arquivos e SQLite persistentes.


## Checkpoint R2.12 — seleção de fontes web e benchmark factual (23/11/2026)

- [x] Corrigida a seleção conservadora de um perfil **qualificado pela categoria solicitada** em `utilities/web_chat.py`. Exige título iniciado pelo referente e marcador da categoria, além de uma primeira frase da página realmente lida que mencione referente e categoria. **Não** autoriza snippet de buscador, simples ocorrência em rodapé ou comando de página como instrução.
- [x] Benchmark offline parametrizado com 16 cenários sintéticos: 10 de identidade/pertinência e 6 de atributo literal / prompt injection; 16/16 aprovados. Conjunto factual direcionado maior: 64 PASS. Resultados e limitações em `docs/operations/RESULTADOS_TESTES_R212.md`.
- [ ] Regressão geral: 603 PASS e 1 FAIL em `test_correction_starts_fresh_identification_and_passes_category`; mock antigo não possui `_sessions` para guarda atual do `ChatService`. Falha reproduzida no código R2.10 original. Suíte **não aprovada**.
- [ ] Próximo R2.13: reparar testes de chat legados **sem relaxar a exigência de sessão válida**, ampliar corpus de documentos reais anonimizados e medir precisão/revocação de pertinência e abstenção; revisar guardas web/prompt injection e concluir regressão. Continuam pendentes sandbox/ACL Windows, integração três repositórios, Ollama real, seis executores e F5 físico (voz fora do foco).

**Regra obrigatória:** R2.12 também modifica ROADMAP V9, FAILSAFE, Manual Técnico Vivo, processo de desenvolvimento, changelog, instruções e relatório. Não considerar `grounded` comprovação de verdade externa. `CAMPANARIO-IA` contém código, `CAMPANARIO-PYTHON` possui `.venv` externa compartilhada, `CAMPANARIO-DATABASE` preserva SQLite, biblioteca e memórias; nenhum dos dois repositórios externos foi alterado.

## Checkpoint R2.13 — testes de sessão e corpus factual offline (23/11/2026)

- [x] Ajustados os dois testes legados `tests/test_knowledge_guard_v30.py` para usar `ChatService` com sessão real em memória. A validação de sessão do código de produção permanece **inalterada**, incluindo rejeição prévia à pesquisa.
- [x] Sincronizadas as verificações legadas de documentação e layout com o conteúdo realmente distribuído no ZIP R2.12, sem criar duplicatas de arquivos ou exigir deleções impossíveis por mesclagem no Explorador. README dos manuais explica material legado.
- [x] Atualizado teste de memória para respeitar auditoria pessoal obrigatória R2.11; teste de streaming verifica conteúdo preservado sem pressupor número de fragmentos que o guard de vazamento pode agregar.
- [x] Criado `tests/test_r213_evidence_corpus.py` com 27 casos sintéticos de atributo, conflito declarado, falta de fonte e adulteração de número. Não equivale a teste de verdade real, análise semântica ou detecção automática de contradição.
- [x] 52 testes focados PASS (Linux/Python 3.13). Regressão geral percorreu 700 PASS e depois excedeu limite da execução em ~66%: **não aprovada**. Ver `docs/operations/RESULTADOS_TESTES_R213.md`.
- [ ] Próximo R2.14: localizar o teste que trava a suíte inteira (execução isolada), manter guardas de sessão e evidência; ampliar benchmark de qualidade com fontes independentes e homologar Windows 3.12, Ollama e três repositórios. R1 e R10 seguem abertos, seis cérebros sem executor. Voz fora do escopo.

**Separação preservada:** `CAMPANARIO-IA` código/docs; `CAMPANARIO-PYTHON` `.venv` externa única; `CAMPANARIO-DATABASE` SQLite, documentos, biblioteca e memórias persistentes. Sem migrações, dependências novas ou cópia de dados. ROADMAPs, FAILSAFE, Manual Vivo e processo de governança devem ser sincronizados em toda revisão.


## Marco R3.0 — consolidação factual entre fontes (23/11/2026)

**Esta é uma entrega maior de marco, não um fechamento fictício dos oito cérebros.** Decisão do usuário: priorizar fatos, colaboração e execução real de capacidades; não trabalhar em voz neste marco. F5 continua aberta e F6 não está liberada. A partir daqui os incrementos menores devem ser agrupados em marcos verificáveis, sem multiplicar versões por ajustes isolados de testes.

- [x] `chat/evidence_reconciliation.py`: revisor determinístico de divergência numérica entre frases comparáveis de **fontes independentes já recuperadas**. Requer mesmo enquadramento textual, exatamente um número por frase e identificadores/locadores distintos. Não usa LLM e não executa ferramentas. Limites: até 25 fontes, 6.000 caracteres por trecho e até 8 conflitos reportados.
- [x] `chat/canonical_answer.py`: no fluxo canônico originado por cérebros, divergência identificada rebaixa/define `CONFLICTING` e substitui possível conclusão por aviso neutro. Os valores e fontes permanecem no registro auditável, não são escolhidos pelo agente. O Motor V9.1 e respostas de cálculo determinístico permanecem.
- [x] Testes focados: 56 PASS sobre revisor R3.0, corpus R2.13, colaboração real e fronteira cérebro/agente. Ver `docs/operations/RESULTADOS_TESTES_R30.md`.
- [ ] **Oito cérebros operacionais: NÃO.** Conhecimento e Análise continuam os únicos executores. Investigação/Estratégia ainda não foram implantados; Programação/Percepção/Comunicação/Criação também não. Revisão de evidência é uma capacidade **compartilhada**, não um executor fictício.
- [ ] **Regressão total: NÃO.** `pytest -q -x` parou após 875 PASS no teste `test_removed_factory_boundary.py` que exige ausência de `renpy_factory` embora a pasta conste na base R2.13. Não apagar recursos existentes para fazer o teste passar. Precisam de reconciliação do contrato de layout e reexecução total.
- [ ] Sem validação real Windows, Ollama, Database externo ou verdade independente das fontes. Não reivindicar acurácia sem medição. Não foi criado banco, `.venv`, dependência externa ou migração.

**Próximo MARCO técnico (não microversão):** resolver inconsistências históricas dos testes com decisão explícita sobre módulos legados; tornar execução/recuperação de Conhecimento/Análise mensurável com corpus documentado e Ollama real no host; então projetar implementações **read-only** de Investigação e Estratégia com execução isolada, contratos próprios, autorização e teste de não alucinação. Programação só depois de sandbox OS e R1. R2.14 antiga fica absorvida pela consolidação R3.0, sem declarar o aceite R0/R1/F5/R10 concluído.

**Fronteira:** `CAMPANARIO-IA` código/docs; `CAMPANARIO-PYTHON` `.venv` externa; `CAMPANARIO-DATABASE` SQLite/documentos/memória. Preservar os três sem migrações não testadas. Atualizações futuras exigem ROADMAPs + FAILSAFE + Manual Vivo + testes + changelog + instruções e rollback.


## Marco R3.1 — Investigação e Estratégia operacionais de leitura (23/11/2026)

- [x] Quatro executores **registrados no código**: Conhecimento, Análise, Investigação e Estratégia (`brains/registry.py`). Os dois novos executam `search_document` em SQLite local read-only dentro do subprocesso de `brains/worker.py`, reutilizando `library:read` e a política central, sem memória/DB novo, modelo ou rede.
- [x] Investigação entrega relatório determinístico com trechos referenciados por ID, lacunas, hipóteses rotuladas **não confirmadas** e divergências numéricas conservadoras entre documentos distintos. Estratégia entrega plano **condicional**, verificações, critérios de parada e necessidade de aprovação; não decide nem executa ações autonomamente.
- [x] Roteamento apenas para intenção explícita de investigar/planejar, prévia controlada e colaboração limitada (até 3 etapas) preservando `CanonicalAnswer` antes da personalidade; erro, fonte ausente ou permissão negada nunca gera relatório factual.
- [ ] Análise semântica profunda (causalidade, cronologia, relações entre pessoas, ranking quantitativo de alternativas), planejamento adaptativo completo e confiabilidade externa **não implementados**. Conhecimento e Análise continuam sendo as capacidades de recuperação e cálculo; os novos executores dependem delas conceitualmente, mas reutilizam a biblioteca diretamente. Programação, Percepção, Comunicação e Criação continuam **sem executor**.
- [ ] Homologação Windows/Python 3.12, `.venv` externa, Ollama, Database real e isolamento OS forte pendentes. F5 voz permanece formalmente aberta, fora do foco desta entrega. R1/R10 não promovidos.

**Próximo marco recomendado:** investigação multietapa com matriz estruturada de entidades/tempo/afirmações e comparação de alternativas por dados medidos, preservando proveniência; depois integração real em Windows com os três repositórios e estudo do isolamento OS. Não liberar programação antes do sandbox.

**Governança:** checkpoint R3.1 exige atualização atômica dos dois ROADMAPs, FAILSAFE, Manual Técnico Vivo, processo, changelog, relatório e instruções. `CAMPANARIO-IA` código, `CAMPANARIO-PYTHON` `.venv` externa, `CAMPANARIO-DATABASE` dados persistentes. Nenhum repositório irmão foi enviado ou modificado.

**Complemento R3.1 verificado:** os relatórios agora contam trechos/origens efetivamente recuperados, e Investigação lista datas dd/mm/aaaa literais válidas sem associá-las automaticamente a eventos. Estratégia bloqueia escolha por valores numéricos comparáveis em conflito. Bateria final 74 PASS; regressão anterior 881 PASS/1 FAIL legado e reexecução após ajuste final interrompida antes de completar.


## Marco R3.2 — Central de Casos offline (23/11/2026)

**Decisão do usuário:** priorizar marcos amplos e operacionalidade real em investigações documentais, não microversões nem voz. Cenário de aceitação: simulação inteiramente fictícia *Operação Eclipse*, com importação de arquivos autorizados, cronologia, hipóteses alternativas e dossiê, sem atribuir culpa ou afirmar eventos não comprovados.

- [x] `brains/casework.py`: caso persistente em arquivos de metadados JSON + cópias imutáveis de evidências com SHA-256; referência individual, origem e responsável declarados; checagem de adulteração. **Não usa novo SQLite.** Exige `CAMPANARIO-DATABASE/dados` existente, explicitamente configurado, e escreve apenas em `dados/cases/`.
- [x] Cronologia de eventos **declarados** com vínculo obrigatório a evidências existentes, fuso ISO 8601 explícito e intervalos de horário aritméticos. CSV/JSON com `timestamp` e `action` pode produzir propostas, nunca eventos automáticos sem confirmação humana.
- [x] Hipóteses concorrentes com fonte pró/contra, ação de verificação e veredito sempre `unresolved`; relatório/dossiê referenciado e limites de autenticidade explícitos.
- [x] `ABRIR_CENTRAL_DE_CASOS.bat` e `brains/casework_cli.py`: acesso local por menu no Windows, usando `.venv` externa; nenhum endpoint HTTP novo com poder de escrita. A integração com chat em tempo real e Field mobile **não** está implementada nesta entrega.
- [ ] **Pendente de aceite:** importação assistida de PDFs/XLSX/imagens (preservados, porém conteúdo não interpretado), vinculação aos executores Investigation/Strategy no chat, autorização granular PF6 para casos multiusuário, captura Field, grafo semântico, métricas e georreferenciamento. Não declarar espaço de casos totalmente integrado aos agentes.
- [ ] R1 Windows/ACL/sandbox e F5 continuam abertos. Sem teste no Windows real, Python 3.12 externo ou Database real. Não há migração, exclusão ou leitura das memórias pessoais.

**Próximo marco recomendado:** integrar um fluxo de caso ao runtime de Investigação/Estratégia com identidade, sessão e autorização da plataforma, depois expandir extração tipada e revisão de evidências; somente com homologaçao Windows/Database disponíveis promover a integração de campo. Gate documental R3.2 obrigatório; confirmar resultados em `docs/operations/RESULTADOS_TESTES_R32.md`.

## Marco R3.3 — Central de Casos nativa no Campanário (23/11/2026)

**Critério de aceite do usuário:** toda atividade de caso deve ocorrer na própria interface Dark Matter, sem abrir janela de outro programa ou outra aba do navegador. R3.3 substitui a obrigatoriedade de uso do menu BAT R3.2; o launcher legado permanece somente por compatibilidade.

- [x] `brains/casework_api.py`: API local PF6 para listar, criar, consultar, importar, verificar e revisar evidências, cronologia, hipóteses e dossiê. Usa `CaseWorkspace` R3.2, sem duplicar SQLite nem criar arquivos no IA. Rejeita caminhos fornecidos pelo navegador.
- [x] `web/static/cases.js`, `web/static/workspaces.js` e `web/index.html`: seção **Database > Casos** nativa no Campanário; navegação sem nova aba nem nova aplicação. Login PF6 e confirmações explícitas de escrita na própria tela; tokens apenas na memória JavaScript.
- [x] Isolamento de casos por principal PF6 autenticado; casos de outro operador não são listados ou lidos. Escritas verificam ACL adicional para usuário individual e `PermissionPolicy` central com confirmação de uso único, vinculada a sessão, operação e conteúdo.
- [x] Upload de até 25 MiB com origem declarada; nomes de arquivo limitados, ZIP não extraído, nenhuma leitura arbitrária de caminhos. Revisão de propostas CSV/JSON com confirmação individual. Dossiê exibido e baixado diretamente na tela.
- [x] Testes direcionados cobrindo caminho autorizado, negação entre operadores, consentimento, replay, alteração de argumentos, upload e interface embutida.
- [ ] **Pendente:** chamada direta dos cérebros pelo contexto de caso na conversa de Morgana/Todd, extração e interpretação aprofundadas de PDF/planilha/imagem e sincronização Field autenticada. O resumo atual de caso é determinístico; não é uma investigação semântica LLM, não comprova a origem dos documentos e não realiza buscas externas.
- [ ] Homologação real Windows/Python 3.12/Ollama/Database, suíte ampla e R1 sandbox continuam abertas; F5 voz permanece fora do foco desta entrega.

**Próximo marco agregado:** vínculo rastreável caso → evidências autorizadas → quatro cérebros existentes → resposta canônica → agentes, com testes de isolamento entre usuários e de não alucinação, sem abrir acessos externos indevidos. Não liberar R10 nem F6 por esta interface.


## Marco R3.4 — Consultas investigativas no chat principal (23/11/2026)

- [x] Perguntas case-aware explicitamente selecionadas usam sessão/identidade PF6 e APIs locais, sem nova aplicação ou aba; Central de Casos inclui diálogo e o chat principal pode consultar o caso autenticado.
- [x] Respostas read-only de evidências, cronologia, hipóteses e plano condicional são extraídas de `case.json`/hashes verificados sem envio de dados privados ao Ollama ou escrita implícita. Morgana/Todd mudam apenas a apresentação fixa.
- [ ] Persistir o diálogo de caso com vínculos sessão/ACL e integrar os quatro executores para leitura semântica de originais. Atualmente o módulo determinístico não invoca `BrainExecutor`; não declarar inferência investigativa autônoma.
- [ ] Homologação Windows, Field e base externa; R1/F5/R10 permanecem abertos. Próximo marco agregado: pipeline case-aware com leitura selecionada de arquivos e colaboração rastreável dos quatro cérebros.
- IA=código; PYTHON=.venv externa única; DATABASE=casos, memória e conversas, separado.


### R3.4 — Modo pessoal local sem dependência PF6/V9 (checkpoint de uso)

- [x] Central **Database > Casos** e a consulta de caso no chat principal agora funcionam no servidor local quando nenhuma credencial/identidade PF6 foi configurada, sem ativar `CAMPANARIO_BRAINS_V9_ENABLED`. O modo de casos é independente da flag experimental dos oito cérebros.
- [x] Interface escolhe automaticamente modo pessoal local em `/api/v1/cases/mode` e não exibe login ou texto de configuração obrigatória; confirmação de escrita é uma pergunta simples de interface. No modo local, API de casos executa operações diretamente; a confirmação da interface não é uma fronteira de segurança contra código malicioso no próprio PC.
- [x] Quando identidades/credencial PF6 **estão configuradas**, preserva a sessão PF6, ACL e confirmação central existente. Credenciais malformadas não são interpretadas como modo livre. A API permanece restrita a loopback/origem local, sem abrir acesso mobile/remoto.
- [ ] Integração futura: autenticação multiusuário e uso Field/mobile com autorização própria; preservar evidências pessoais já atribuídas a identidades PF6 (não reatribuir automaticamente); integração semântica dos quatro executores com os anexos; homologar Windows real.
- **Prioridade operacional:** o projeto deve funcionar antes de adicionar etapas de configuração desnecessárias. Nenhuma dessas facilidades altera a factualidade do Motor V9.1, a integridade dos arquivos ou a separação IA/PYTHON/DATABASE.

## Marco R3.5 — leitura factual de originais pela conversa (23/11/2026)

- [x] `brains/casework_sources.py` lê **cópias preservadas verificadas por SHA-256** de TXT/LOG/MD/CSV/JSON; tenta PDF textual via `pypdf` já declarado e XLSX via `openpyxl` opcional, sem executar fórmulas nem extrair ZIP. Ausência de leitor/arquivo ilegível é explicitada. Busca lexical limitada e citações por ID de evidência + linha (PDF por número de página escrito na linha; XLSX por aba/linha).
- [x] `casework_dialogue.py` direciona perguntas de conteúdo/investigação para trechos literais citados e reutiliza o `structured_report` puro dos executores Investigação/Estratégia para revisão e plano condicional. O chat Dark Matter usa o endpoint de casos R3.4; não requer nova aba nem senha PF6 no modo pessoal local. Não envia o cofre ao Ollama e não reescreve fatos com persona.
- [x] Divergências quantitativas conservadoras quando há uma única quantidade e frase circundante idêntica entre originais distintos. Não resolve contradições semânticas, não comprova autoria ou verdade externa.
- [x] 117 testes focalizados aprovados; regressão geral: 566 PASS, depois teste de Biblioteca de Interações falhou, reproduzido em ZIP original R3.4. Homologação Windows/Ollama/Database externo pendente.
- [ ] **Próximo marco agregado:** extração estruturada melhor de PDF/XLSX com referências estáveis, grafo auditável de entidades, hipóteses e cronologia derivadas com revisão humana, recuperação de contexto por relevância semântica avaliada, testes reais integrados no Windows; UI de casos nativa. Quatro cérebros instalados; quatro ainda pendentes. F5 e R1 permanecem abertos, voz não é foco do marco.
- **Topologia obrigatória:** `CAMPANARIO-IA` código; `CAMPANARIO-PYTHON/.venv` única externa; `CAMPANARIO-DATABASE/dados/cases` dados persistentes. Nenhum novo banco ou ambiente criado.

## Marco R3.6 — investigação multietapa, OCR e recuperação semântica opcional (23/11/2026)

- [x] `brains/case_investigation_pipeline.py`: cinco etapas executáveis em leitura: integridade, recuperação de citações, cronologia cadastrada, confronto numérico estrito e matriz de hipóteses. Relatório acessível pela pergunta `Caso: investigue...` no chat Dark Matter, sem nova aba. As verificações sugeridas **não são executadas** nem viram conclusões autônomas.
- [x] `brains/casework_sources.py`: OCR **opt-in**, local e limitado de PNG/JPEG e páginas de PDF digitalizado com Tesseract/por+eng; nenhuma evidência original é modificada. Requer bibliotecas do host para PDF digitalizado. Textos obtidos por OCR são dados de fonte não verificada.
- [x] Recuperação semântica **opt-in** via embeddings do Ollama em `127.0.0.1:11434`, com modelo configurável, limite de 60 linhas e timeout. O resultado é similaridade para recuperar trechos exatos, não verificação de verdade; sem Ollama recai na busca lexical. Nenhum endpoint remoto configurável para dados privados.
- [x] Testes R3.6 para ausência de dependências, hashes adulterados, hipóteses concorrentes, OCR seguro, degradação e compatibilidade das APIs; ver relatório.
- [ ] Entendimento universal de todos os documentos, compreensão visual de cenas, investigação causal autônoma, revisão semântica robusta e homologação Windows/Ollama/Database real **não estão concluídos**. OCR de imagem não equivale à percepção visual, e modelos locais podem errar.
- [ ] Próximo marco: percepção visual com saída revisável e citações, extração de relações entre entidades/histórico e hipótese causal falsificável, com benchmark real e homologação no host. Não executar ações autônomas sem autorização.
- IA contém código/docs; `CAMPANARIO-PYTHON/.venv` externa única contém bibliotecas opcionais; `CAMPANARIO-DATABASE/dados/cases` contém os arquivos de caso, sem novo banco ou migração. Voz segue fora do foco, com seu gate aberto.

- [x] `brains/casework_vision.py`: percepção local **opt-in** de imagem por Ollama, retornando apenas `unverified_visual_suggestion` para revisão humana, sem validar fatos, identidades ou autoria. A interface do chat mostra identificação de pista provisória.


## Marco R3.7 — ciclo investigativo limitado e documentos DOCX/HTML (23/11/2026)

- [x] `brains/case_investigation_pipeline.py` evoluiu de uma passagem para até **três consultas sucessivas**: pergunta inicial e até duas verificações registradas pelo operador nas hipóteses. Cada rodada é somente leitura, verifica SHA-256 e registra quantidade de citações novas e motivo de parada; saída limitada a 16 citações deduplicadas. Não executa buscas novas na internet, ações de sistema ou decisões sem autorização.
- [x] Se somente uma consulta secundária tiver trechos, a pergunta principal permanece **sem evidência suficiente**; hipóteses mantêm `unverified`. A resposta canônica de Morgana/Todd preserva os trechos, sem reescrita generativa.
- [x] `casework_sources.py` agora extrai texto de DOCX (XML Word com limites para ZIP, sem macros nem relações externas) e HTML/HTM (somente texto visível, sem executar scripts); `casework.py` e o seletor Dark Matter aceitam essas extensões. PDF digitalizado, OCR, embeddings Ollama e imagem continuam opcionais, sujeitos às limitações R3.6. DOCX/HTML não equivalem a compreensão universal de formatos ou verdade semântica.
- [x] 108 testes direcionados aprovados em Linux/Python 3.13 (incluindo 8 novos testes R3.7). Suíte ampla parou após 566 PASS/1 FAIL em Biblioteca de Interações, já presente na base R3.6/R3.5; não homologada.
- [ ] Investigador universal e compreensão semântica universal **não são atingíveis como garantias gerais**: faltam leitura fiel de documentos complexos, planejamento causal com revisão humana, avaliação em corpus real, OCR/Ollama reais no host Windows, segurança de arquivos não confiáveis e autorização de ações. O ciclo R3.7 é investigação iterativa documental limitada.
- [ ] Outros quatro cérebros especializados permanecem sem executor e R1/R10 continuam abertos. Voz F5 continua fora do foco solicitado, sem ser declarada concluída.

**Próximo marco maior:** avaliar fidelidade e cobertura documental com conjunto de casos reproduzível (incluindo contradições semânticas), permitir revisão humana das hipóteses e conectar decisões justificadas a novas perguntas sem promover palpites a fatos. IA mantém só código, PYTHON mantém uma única `.venv` externa, DATABASE mantém casos/SQLite/memórias; rollback apenas substituindo arquivos IA via Explorador do Windows.


## Marco R3.8 — relações auditáveis e priorização adaptativa de investigação (23/11/2026)

- [x] Adicionado `brains/case_reasoning.py` para matriz **não causal** de vínculos explicitamente cadastrados entre eventos, hipóteses e evidências; pistas entre documentos exigem pelo menos dois termos compartilhados em trechos SHA-256 verificados.
- [x] `case_investigation_pipeline.py` prioriza verificações `next_check` já cadastradas pelo operador conforme a pergunta e posições pró/contra; até três rodadas, sem novas perguntas inventadas, ações, internet ou escrita. A primeira rodada continua determinando se a **pergunta principal** possui trechos recuperados.
- [x] Matriz por hipótese diferencia referências pró e contra cadastradas que também foram recuperadas; **não verifica suporte semântico, causalidade, culpabilidade nem probabilidade**. Morgana/Todd apresentam essas ressalvas no chat nativo Dark Matter.
- [x] 91 testes integrados direcionados aprovados no ambiente Linux/Python 3.13. Suíte geral: 566 PASS e 1 FAIL preexistente em `test_interaction_library.py`; não homologada.
- [ ] Detecção semântica de implicação/contradição, investigação causal, revisão humana persistente, extração exaustiva de documentos, benchmark com dados consentidos e homologação Windows/Ollama/Database externos permanecem pendentes.
- [ ] Quatro executores de cérebro ainda ausentes: Programação, Percepção, Comunicação e Criação. F5 voz não alterada; sandbox R1/R10 ainda abertos.

**Critério do próximo marco maior:** validar conclusões com múltiplas fontes independentes e revisão explícita de proposições, medições e hipóteses por humanos; não confundir afinidade lexical com verdade. `CAMPANARIO-IA` = código; `CAMPANARIO-PYTHON/.venv` = ambiente externo único; `CAMPANARIO-DATABASE` = originais e persistência sem migração. Atualização conjunta do ROADMAP V9, FAILSAFE, Manual Vivo e Processo Obrigatório é exigida.

## Marco R3.9 — leitura auditável de proposições (23/11/2026)

- [x] `brains/case_claims.py`: classificador determinístico **restrito** dos trechos já recuperados e conferidos por hash: relato, negação explícita, linguagem incerta/hipotética e atribuição textual. Cada cartão conserva ID, linha, SHA-256 e citação literal. Não declara verdade externa.
- [x] Identificação de **oposição textual explícita** entre arquivos diferentes quando o mesmo sujeito, predicado e complemento literais aparecem com e sem a negação imediatamente anterior ao verbo. Não infere equivalência semântica, autoria ou causalidade. Conflitos são pistas a revisar.
- [x] Integração `case_investigation_pipeline.py` -> `casework_dialogue.py` no chat principal Dark Matter; consultas "o que as evidências afirmam?" são roteadas para conteúdo. Não há escrita nem chamadas de LLM ou serviços externos.
- [x] Testes novos e regressão focalizada; resultados em `docs/operations/RESULTADOS_TESTES_R39.md`. Teste amplo permanece bloqueado por falha legada da Biblioteca de Interações (566 PASS/1 FAIL).
- [ ] Extração semântica livre, desambiguação de referentes, múltiplas frases, escopo de negação, causalidade, confiabilidade das fontes e revisão humana persistente. **Não declarar compreensão universal.** Testes com Ollama real no Windows/Database seguem pendentes.
- **Próximo marco agregado:** revisão humana de proposições com proveniência e evidência contrária, avaliação de implicação semântica em corpus real e benchmark rotulado, sempre sem promover interpretação gerada a fato.
- **Topologia intocada:** CAMPANARIO-IA código; CAMPANARIO-PYTHON/.venv compartilhada; CAMPANARIO-DATABASE memória, conversas e originais. Sem novos bancos, migrações ou alterações em voz/F5.



## Marco R3.10 — semântica assistida, ancorada em trechos (23/11/2026)

- [x] Classificador semântico **opt-in** por Ollama local de citações já verificadas: anota substrings literais e sugere relações entre arquivos sem converter saída do modelo em verdade. Integrado à Investigação e ao chat Dark Matter.
- [x] Validação de IDs, hashes, trecho literal, rótulos permitidos, limites de saída e falha segura; modelo ausente deixa caminho determinístico existente operacional. Correção de roteamento de perguntas investigativas sobre documentos.
- [ ] Compreensão universal ou profunda de **qualquer documento**, implicação semântica comprovada, causalidade, análise visual universal e revisão humana persistente continuam abertos. As sugestões do modelo não são evidência nova.
- [ ] Benchmark representativo com documentos reais autorizados e homologação Windows/Ollama/Database externo; resolver falha geral de Biblioteca de Interações sem mascará-la.
- **Próximo marco agregado:** revisão humana auditável de proposições e benchmark semântico contra exemplos adversariais, tabela de métricas e cobertura documental. Manter quatro executores reais de oito.
- Três repositórios preservados: CAMPANARIO-IA código, CAMPANARIO-PYTHON/.venv externa única, CAMPANARIO-DATABASE dados persistentes. Sem migração, banco duplicado ou mudança de voz F5.


## Marco R3.11 — ativação assistida e avaliação antes dos próximos cérebros (23/11/2026)

- [x] Ativador local `scripts/activate_local_capabilities.py` + BAT Windows: diagnóstico, backup privado de `.env` e ativação condicionada à presença de modelos locais/OCR/ZIM. Nenhum arquivo privado distribuído; configuração **não aplicada ao PC do usuário** neste ambiente.
- [x] Avaliador com 18 exemplos artificiais anotados, métricas por classe e modo opcional de Ollama real; teste offline verifica o instrumento, **não mede o acerto de LLM**.
- [ ] **Bloqueio para promoção de próximos cérebros:** executar benchmark no Windows com modelo local, medir falsos positivos em documentos consentidos anotados, validar OCR/visão e completar teste end-to-end com DATABASE externo. Proibido declarar compreensão universal/segurança global.
- [ ] Regressão geral continua aberta; falha histórica da Biblioteca de Interações ainda requer investigação específica. R1/R10 e F5 não foram homologados.
- Repositórios separados: IA = código; PYTHON = única `.venv` externa; DATABASE = originais/SQLite/memórias; rollback apenas de código/configuração privada com backup.


## Marco R3.12 — gate de homologação factual com Ollama real (23/11/2026)

**Entrega de engenharia implementada, homologação real PENDENTE.** `scripts/homologate_factual.py` executa duas passagens sobre 34 pares sintéticos anotados, exige nome explícito de modelo Ollama via loopback, calcula acurácia, macro-F1, recall de contradições, estabilidade entre rodadas e falso conflito em itens não contraditórios. Resultado `PASS` significa somente **gate técnico no corpus sintético**; `BLOCKED` impede promoção e `INCONCLUSIVE` indica modelo ausente/resposta inválida. O R3.11 não traz dados de Ollama Windows ou Database privado.

**Aceite exigido antes de expandir cérebros:** (1) teste real Windows + Ollama local instalado, guardar JSON no Database externo; (2) corpus humano independente de documentos legítimos de múltiplos formatos e línguas, revisar falsos positivos/negativos e citações; (3) validar OCR, planilhas, PDF, segurança do cofre e fluxo de conversa real com Morgana/Todd; (4) regressão total e baseline de falhas antigas; (5) repetir em modelos selecionados. Sem todos estes itens, a homologação permanece aberta. Os quatro cérebros existentes não ganham novas permissões. Voz fora do escopo.

**Próxima etapa de capacidade:** somente depois de avaliação factual efetiva e revisão humana iniciar os executores de Programação (sandbox obrigatório), Percepção, Comunicação e Criação com testes próprios, sem trocar factos por estilo. Três repositórios: IA=código; PYTHON=única .venv externa; DATABASE=relatórios/dados persistentes.


## Marco R3.13 — correção de anexo no chat pessoal local (23/11/2026)

**Implementado:** `POST /api/v1/utilities/upload-stream` e upload legado passam a respeitar o modo pessoal local *sem PF6 configurado*, inclusive quando `CAMPANARIO_BRAINS_V9_ENABLED=true`. O navegador continua limitado ao loopback, à mesma origem, à pasta de utilidades existente, a extensões permitidas, a limites de tamanho e a gravação sem sobrescrever. O botão de anexo agora também aceita DOCX/XLSX, compatíveis com a API; a versão do script foi atualizada para evitar cache antigo. **Não** desativa V9 globalmente, não autoriza `utilities.invoke` e **não** libera upload sem aprovação quando PF6 estiver configurado. O anexo é guardado na pasta de utilidades; **não é importado automaticamente para Biblioteca/Casos ou enviado ao Ollama**.

**Aceite:** testes de integração de upload local/V9/PF6, regressão e documentação. **Pendente:** validação com instalação Windows real, `.env` privado e navegador final.


## R3.14 — Uso pessoal local sem PF6 como padrão (23/11/2026)

- [x] `CAMPANARIO_LOCAL_PERSONAL_MODE=true` por padrão no `Settings`: dispensa login PF6, confirmações de operação e ACL por usuário no chat/utilidades e Central de Casos em loopback, mesmo que credenciais legadas persistam no `.env` privado. Em modo local, utilidades aceitam a própria invocação explícita como autorização da operação.
- [x] Casos anteriores pertencentes a antigas identidades aparecem no modo pessoal sem reescrever o campo `authorized_by`; seleção por usuário volta ao escolher `false`. Não modifica DATABASE real durante instalação.
- [x] Importação de evidências por streaming com SHA-256 e staging só no DATABASE externo, sem buffering de arquivo inteiro em RAM; limite operacional ampliado para 1 GiB por arquivo e até 4096 evidências/caso. Upload utilitário em streaming também até 1 GiB.
- [x] Interface da Central sem pop-up de autorização repetitiva nem bloqueio de 25 MiB; cache JS atualizado.
- [ ] Nenhum teto técnico deve ser confundido com limite de acesso PF6: permanecem limites de armazenamento/integridade, proteção contra sobrescrita, nomes inválidos, origem externa, formato e a fronteira de fatos. Não habilitar acesso remoto indiscriminado.
- **Testes:** 138 direcionados aprovados; regressão geral bloqueada após 33 PASS no `uv.lock` ausente também na base R3.13. Windows/Database/Ollama pessoais não homologados.
- **Próximo marco:** melhorar os quatro cérebros pendentes, sem vincular capacidade factual a um modo de autenticação que o operador pessoal não utiliza.


## Checkpoint R3.15 — biblioteca realmente acessível e respostas ligadas ao documento

**Falha real reportada:** clipe do chat fazia apenas staging de arquivos, mas não invocava `library.import`; portanto, um arquivo presente em `CAMPANARIO-DATABASE/dados/.../utilidades/arquivos/` podia não existir em `documents` nem em `document_sections`, impossibilitando `search_document`. A UI não tornava essa distinção visível. Uma continuação com `qual` sem interrogação era classificada como conversa genérica, fazendo o modelo responder sem a fonte desejada.

**Correção integrada na UI:** chat passa `index=true` em `upload-stream`; o endpoint preserva o arquivo no workspace, importa por `UtilityService` no mesmo DATABASE externo e retorna `indexed`, `indexed_sections`, `index_state`, `document_id` ou `index_error` sem fingir êxito. Importação é feita em thread durante a requisição, nunca em background silencioso. PDF sem texto/OCR ausente e JSON inválido são marcados como não pesquisáveis. Arquivos antigos enviados somente ao staging: em Ferramentas → Arquivos, usar **Indexar**; documentos com erros: Ferramentas → Biblioteca → **Reindexar**. O original continua imutável, com SHA-256 validado antes da reindexação.

**Gerenciamento:** o Explorador e a Biblioteca têm paginação (100 itens/página e total real), nomes, estados, visualização do texto extraído, exclusão e renomeação. A Biblioteca tem `library.rename` (metadados apenas, preservando extensão/arquivo) e `library.reindex` (reextração do original validado e substituição transacional da indexação). Arquivos na pasta autorizada oferecem Indexar/Renomear/Mover/Lixeira. O conteúdo original preservado não é editado diretamente; nova versão deve ser importada conscientemente. Chat permanece na interface Dark Matter, sem nova aba/aplicativo de investigação.

**Intenção documental:** `document_request` reconhece “arquivo relacionado a ordem paranormal” e remove o sufixo “e me diga...” do nome sugerido. Perguntas de acompanhamento com “qual/quais/quem...” sem `?` mantêm a referência explícita recente ao documento; falta de citação continua exigindo abstenção factual. Nenhum nome de criatura da franquia foi codificado como resposta. Trecho recuperado mostra **o que a fonte diz**, não valida cânone externo.

**Verificação:** 90 testes direcionados PASS, incluindo regressões V8, PF6 pessoal, cérebros, casos e semântica; regressão geral: 33 PASS, 1 falha preexistente em `uv.lock` ausente. Compilação e JavaScript verificados. Não houve acesso ao acervo privado do operador nem homologação com Windows/Ollama reais. **Rollback:** fechar o Campanário, restaurar a cópia R3.14 do código e reiniciar; preservar o DATABASE. Metadados criados nesta versão são compatíveis com schema V8; cópia privada de segurança recomendada antes de reindexar ou excluir.


## Checkpoint R3.16 — CAMPANÁRIO MAPS V2 integrado ao Dark Matter (23/11/2026)

- [x] NavigationService independente da interface, com estados, origem GPS validada, sessão pessoal volátil, manobras e detecção de desvio com três leituras; recálculo solicitado a grafo OSM real e falha explícita.
- [x] Navegação com chat do desktop e Modo Patrulha na mesma aba; voz local do navegador, progresso geométrico aproximado e mapa-base offline ou tiles online apenas após opt-in.
- [x] Geocodificador Nominatim e busca por categoria Overpass **locais configuráveis**; proximidade é avaliada por distância de rota OSRM nos pedidos genéricos. Caminhada exige grafo OSRM pedestre distinto.
- [x] Cliente Android existente ganhou orientação **apenas em primeiro plano** via canal HTTPS pareado, TTS nativo e geometria esquemática sem mapa-base de ruas. Não existe APK homologado.
- [x] Testes de contrato e trajetórias sintéticas, endpoints, isolamento de dispositivos; instalação e atualização de grafos documentadas.
- [ ] **Gate de navegação real:** instalar extratos OSM, OSRM, Nominatim/Overpass na máquina do usuário, testar GPS real com métricas e ruas, homologar voz/Android, map matching em cruzamentos, desvio seguro e tolerância a perda de rede.
- [ ] **Android em segundo plano e mapa móvel de ruas:** implementar Android ForegroundService com notificações/permissões e dados offline; nenhum modo offline de roteamento no celular nesta release.
- [ ] **Outras integrações:** ações de Agenda, investigação espacial aprofundada e ferramentas PF5 para os cérebros ainda pendentes; não tratar eventos de chat como ações externas autorizadas.
- Repos continuam independentes: IA, PYTHON com .venv única externa, DATABASE com mapas somente se o usuário instalar.


## Checkpoint R3.17 — Campanário Field Android / navegação nativa

- [x] Activity Android nativa para navegação com GPS, POIs e rotas geográficas reais via servidor Maps V2 pareado; chat e biblioteca permanecem no mesmo Field existente, sem segunda IA. Comando “rota para ...” encaminha à tela nativa e inicia fluxo automático sem ambiguidades.
- [x] ForegroundService de localização e TTS Android com notificação, recálculo pelo OSRM, retorno ao chat sem encerrar a navegação; API HTTPS versionada e SecureStore existente.
- [x] Build por Android Studio documentado e `.bat` opcional para Gradle instalado; sem segredos e sem alteração de Database externo.
- [ ] **Não há APK compilado**: Android SDK/Gradle e rede de dependências ausentes neste ambiente. Não homologado em celular; sem basemap, offline routing, Compose/Room geral, OTA assinado, Patrol Engine nativo persistente ou WireGuard automatizado.
- [ ] Preparar SDK, compilar e executar em Android real; instalar grafo OSM, medir GPS e navegação em vias seguras; só depois avançar para Field completo.

## Checkpoint R3.19 — projeto enxuto e Maps: busca independente do GPS (23/11/2026)

- [x] Remoção do artefato distribuído de `.venv` interna, `.git`, backups, bancos SQLite, `.env` pessoal, modelos de voz duplicados, cópia integral de projeto em `docs/operations` e documentação histórica redundante.
- [x] Projeto Android e assets `apps/mobile/www` preservados para build; launcher Windows utiliza o Python do repositório irmão sem impor PREPARAR_PC.
- [x] Busca de endereço sem GPS; latitude/longitude aproximadas aceitas como contexto, identificadas como aproximadas; manual tem prioridade, GPS de até 100 m permanece necessário para guia ao vivo.
- [x] Tiles online ativados por padrão e cache-bust dos scripts; preferência explícita de desligar permanece respeitada.
- [ ] Build APK Android Studio e teste em celular real, serviços Nominatim/Overpass/OSRM e navegação de campo ainda pendentes.
- [ ] Confirmar no Windows que a pasta nova com `.env` preservado abre pela raiz e o fluxo Maps atende a origem manual; nenhuma pasta externa foi modificada.


## R3.20 — localização automática e busca/rota com fallback (23/11/2026)

- Ao abrir Maps no Dark Matter, o cliente tenta `navigator.geolocation.watchPosition` automaticamente, conforme a autorização do Windows/navegador. Mantém latitude, longitude, precisão e horário somente em memória de interface; não envia localização ao servidor durante a simples observação. Sem GPS, busca por endereço permanece disponível e a origem manual continua possível.
- A tela Maps usa somente `CampanarioNavigationV2` para os botões de busca/rota, evitando que o antigo `gps-map.js` sobrescreva os handlers.
- Busca por endereço: Nominatim local primeiro; se estiver indisponível, Nominatim público em consulta explícita. Categoria próxima: Overpass local e depois público; roteamento carro: OSRM local e, se estiver indisponível, servidor público de demonstração OSRM. Caminhada: somente grafo pedestre local (não inventar rota de carro).
- O fallback está **ativado por padrão para uso pessoal** e pode ser desativado com `CAMPANARIO_MAPS_PUBLIC_FALLBACK=false`. Serviços públicos recebem a busca e, em roteamento, as coordenadas. Nominatim público tem limitação de uso, identificação do aplicativo, cache em memória e espaçamento de 1,1 s por host; não usar autocomplete nem disparar varreduras. Não há GPS fictício.
- Pendente: teste de campo em Windows/Android; conectividade e política dos provedores públicos; precisão do GPS no PC; compilação APK e navegação Android em segundo plano. Não declarar homologação de campo.


## Checkpoint R3.21 — Field GitHub Pages (23/11/2026)
- Frontend PWA público estático, isolado em `pages/`, com GPS do navegador, mapa OSM e consulta de rotas públicas; não contém dados privados.
- Servidor Python/Ollama/Database continuam exclusivamente no PC; acesso opcional via listener Companion HTTPS autenticado e CORS para origem Pages explicitamente configurada.
- Compatibilidade e limitações: consulta cartográfica pública sujeita a quota, rota de carro somente, GPS em primeiro plano, sem APK nem homologação em campo; tela e notas offline, sem roteamento offline.
- Implantação reversível: excluir publicação Pages / desabilitar `CAMPANARIO_FIELD_PAGES_ORIGIN`; sem migração de dados e sem alterações nos três repositórios externos.
- Testes da alteração e pendências descritos em `docs/operations/RESULTADOS_TESTES_R321.md`. Não declarar homologado o acesso real a PC ou geolocalização do usuário.
