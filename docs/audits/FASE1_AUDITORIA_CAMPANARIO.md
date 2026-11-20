# FASE 1 — Auditoria de fluxos, factualidade e offline (sem mudar codigo)

**Versao auditada:** ZIP `CAMPANARIO_IA_ETAPA3_CORRIGIDO_COMPLETO.zip`, `pyproject.toml` versao 0.8.0. **Data:** 19/11/2026. **Metodo:** leitura de codigo e docs, suite pytest, provas deterministicas isoladas em pastas temporarias. **Limitacoes:** auditoria em Linux/Python 3.13.5; sem Ollama escutando em `127.0.0.1:11434`, sem Windows/GPU/modelos/enciclopedia Kiwix para E2E fisico; nenhuma internet publica foi consultada.

**Documento de referencia encontrado:** `docs/reference/Projeto_Campanario_v2.0_Documento_de_Conceito.docx`, intitulado *Projeto Campanario v2.0*. A versao **v2.2 citada no pedido nao consta deste ZIP**; nao foi presumida nem reconstruida. O documento e visao conceitual, nao prova de implementacao.

## 1. Fluxo real de um turno

1. **Entrada e sessao:** `src/campanario/main.py:39-51` monta FastAPI; `api.py:437-443` inicia SSE; `chat/service.py:756-775` valida sessao/modelo. Caminho de ferramentas neutras separado: `utilities/api.py:22-38` (`/api/v1/utilities/invoke`).
2. **Decisao de pesquisa PREVIA a selecao de agente:** `chat/service.py:776-903` avalia `/pesquisar`, `CAMPANARIO_WEB_AUTO_SEARCH`, `_NO_WEB`, `direct_decision`, `short_entity_decision` e, opcionalmente, o planejador LLM `utilities/web_intent.py:135-225`. Nao ha chamada automatica a `library.search` nesse trecho. A decisao so solicita busca WEB.
3. **Coleta de fatos externos:** `chat/service.py:873-903` chama `utilities/web_chat.py:252` (`research_entity`) ou `:441` (`research_topic`); ambos usam ferramentas `web.search`/`web.read`, provedor em `utilities/web_research.py:247-318` (Wikipedia, DDG/Bing, Brave ou SearXNG local). `ResearchResult` registra status, fontes, falhas e candidatos (`web_chat.py:79-100`). A mesma variavel `research_guard` e passada aos participantes do turno.
4. **Registro do usuario e roteamento:** `chat/service.py:932-1018` chama `agents/router.py:43-64` (primary speaker), salva mensagem do usuario, observa memoria (`runtime/experience.py:391`) e publica eventos. `agents/addressing.py:12-29` interpreta vocativos de Todd/Morgana. O roteamento acontece **apos** a decisao preliminar de pesquisa web, embora o registro do usuario ocorra antes da resposta.
5. **Contexto e memoria:** `_run_agent` (`chat/service.py:253-360`) recompila o contexto para **cada agente**. Memoria lexical/semantica por agente: `chat/service.py:279-317`, `runtime/experience.py:500-627`; identidade e proveniencia conversacional: `chat/behavior.py:42-100`, `chat/provenance.py:10-107`, quando o modo completo esta ativo. Aplica a persona com `agents/context.py:11-51` e `agents/personality_application.py:41-50`.
6. **Geracao/auditoria:** `composition.py:53-86` escolhe Ollama e guardas. Na configuracao enxuta (`low_latency_mode=true`), usa `safe_provider` e **nao instancia `BehaviorResponseGuardProvider`**; `chat/service.py:393-395` deixa `audited_stream=False`, logo acumula antes de emitir. `chat/service.py:398-414` pode responder sem LLM, com extrato Wikipedia ou abstencao; `:460-462` coleta a geracao; `:475-703` aplica verificacao de speaker, reparos, auditoria web condicional e guarda de memoria. Auditoria semantica `chat/knowledge.py:166-219` exige fontes web/LLM; nao e verificador universal.
7. **Grupo e saida:** `chat/service.py:1037-1134` chama `agents/participation.py:61-150`, escolhe **um segundo agente** e opcionalmente turnos adicionais. Repassa a mesma pesquisa `research_guard`, mas recompila memoria/contexto por agente; em turnos normais o segundo tambem recebe a resposta anterior no historico (`chat/service.py:1058-1062`). Persiste a resposta antes da entrega (`chat/service.py:722-754`) e emite tokens/eventos. `chat/service.py:196-251` registra interrupcoes.

**Conclusao verificada:** ha **um resultado de pesquisa web compartilhado** por turno, **nao uma ficha neutra unica de fatos locais + memoria + web**. As duas geracoes/model requests sao distintas; a recuperacao de memoria e feita por participante.

## 2. Inventario e maturidade

| Capacidade | Classificacao | Evidencia / limite |
|---|---|---|
| API, sessao e chat local | **Parcial** | `main.py`, `api.py`, `chat/service.py`, testes; conversa geral exige Ollama local funcionando. Sem isso o chat gera `ModelUnavailableError`. |
| Biblioteca local TXT/MD/PDF | **Funcional como ferramenta isolada** | `utilities/service.py:181-215`, `utilities/api.py:27-31`; importacao e busca lexical por substring, retorno com pagina/trecho; prova temporaria `provas_offline.txt`. OCR ausente para PDF escaneado; limite 20 MB/documento. |
| Biblioteca/RAG automatico no chat | **Ausente** | `chat/service.py:776-903` consulta so `web_chat` em perguntas factuais; `library.search` so aparece em `utilities/service.py`, nao no fluxo do chat. |
| Enciclopedia Kiwix/ZIM offline | **Ausente no ZIP/fluxo analisado** | Nao ha arquivo `.zim`, adaptador Kiwix nem consulta a enciclopedia em `src/campanario`. |
| Memoria SQLite e recuperacao lexical | **Parcial** | `runtime/experience.py:391,500-583`, `storage/repositories.py:279-334`; persiste/recupera. Falhas em G2 na suite principal demonstram problemas de recuperacao e inferencias. |
| Vetores da memoria do usuario | **Parcial** | `composition.py:110-148`, `runtime/semantic_index.py:116-126`, `experience.py:585-627`; usa `embeddinggemma` via Ollama `/api/embed`, fallback lexical se indisponivel. Nao indexa a biblioteca geral. |
| Cache web Meilisearch | **Protótipo/opcional** | `utilities/web_chat.py:51-75,343-360`, `utilities/meili_sources.py:25,65-155`; exige `CAMPANARIO_MEILI_ENABLED`; cache de paginas web previamente lidas, NAO enciclopedia. |
| Pesquisa web e identificacao | **Instavel** | `web_intent.py:57-165`, `web_chat.py:252-419`, `web_research.py:247-318`; existe gate de fontes lidas, mas falhas em `test_knowledge_guard_v30`, `test_web_auto_chat` e `test_web_research`. |
| Router para dois participantes | **Funcional no escopo atual** | `agents/router.py:29-64`, `participation.py:47-74`; prova de convite de grupo e resultado com dois speakers `prova_grupo_offline.txt`. |
| Suporte a N agentes so por perfil | **Ausente** | `agents/profiles.py:293-294` registra so dois em Python; `agents/personality_application.py:46-50` falha para terceiro; routing/convite hardcoded. |
| Chat neutro SEM agente | **Ausente** | `chat/service.py:109-119,953-954` sempre resolve uma persona. **Ferramentas neutras funcionam separadas**, `utilities/api.py:22-38`. |
| Contratos de resposta | **Parcial** | `response/pipeline.py`, `response/guard.py`, `composition.py:55-61`; pipeline completa nao fica ativa no modo enxuto padrao; restam validacoes manuais em `chat/service.py`. |
| Proveniencia conversacional | **Parcial** | `chat/provenance.py:10-107` diferencia USER/assistant e corrige, mas `chat/behavior.py:45-53` retorna cedo no modo compacto, sem as notas detalhadas de proveniencia nem sanitizacao de ficcao. |
| Auditoria factual | **Parcial** | `chat/knowledge.py:166-219,246-329`, `chat/service.py:623-678`. Cobertura limitada a pesquisas com guard; extrato seguro especial da Wikipedia, nao prova todos os fatos. |
| Preferencias/voz/ferramentas por perfil externo | **Planejado / ausente** | `agents/profiles.py:27-38` e objetos declarados em Python, sem loader de perfis em arquivo; tool permissions do sistema nao sao campos de perfil. |

## 3. Baseline da suite, ANTES de qualquer mudanca

**Comando:** `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q --tb=short -p no:cacheprovider` (diretorio do projeto). **Resultado:** **655 passed, 30 failed, 14 warnings em 34,96 s**; exit code 1; arquivo `FASE1_EVIDENCIAS/pytest_suite_completa.log`. Ambiente Python 3.13.5, pytest 9.0.2; declaracao do projeto `pyproject.toml:6` = `>=3.12,<3.13`. Nao representa validacao no Windows/Python 3.12.

**Triagem das 30 falhas:** 12 relacionadas a grounding e memoria pessoal (9 `test_g2_grounding_audit`, 3 `test_g2_semantic_evidence_regression`), 3 `test_knowledge_guard_v30`, 5 `test_web_auto_chat`, 2 `test_web_research`, 1 `test_research_anti_hallucination`, 1 `test_neptune_mode`, 6 de estrutura/manual/legado (`test_manual_docs`, `test_project_layout`, `test_removed_factory_boundary`, `test_v08_platform`). **Nao e correto chamar todas de stubs obsoletos**: ha falhas onde uma afirmacao pessoal infundada foi transmitida/gravada, e falhas de recuperacao semantica. Existem stubs sem `_sessions` e mocks sem o argumento `skip_wikipedia`, mas tambem ha divergencia real de contrato. Afirmar que cada falha ja existia na Etapa 2 exigiria repetir a suite da versao anterior sob o mesmo ambiente; nao feito nesta fase.

**Recorte independente:** `test_utilities_offline.py`, `test_factual_quem_e.py`, `test_etapa3_grounding_naturalidade.py`, `test_agents.py`, `test_event_bus.py` => **73 passed** em 1,47 s. Nao equivale a homologacao de modelo real.

## 4. Origem de recusas e inventos — FATO, HIPOTESE, PROPOSTA

**FATO VERIFICADO — Recusa indevida offline:** `chat/service.py:792-796,840-870` cria `ResearchResult(status='disabled')` para pergunta de identidade quando auto-search=false; `_run_agent` aplica `natural_uncertainty` (`:404-407`) **sem verificar biblioteca**. Reproducao: importar em pasta temporaria `prova.md` contendo texto sobre Ada Lovelace, consultar `library.search` (1 trecho) e rodar chat local `quem foi Ada Lovelace?` (resposta: pesquisa desativada, nao posso confirmar). Arquivos `provas_offline.txt` e `prova_runtime_sem_ollama.txt`.

**FATO VERIFICADO — Lacunas de decisao:** `web_intent.py:135-165` so reconhece certas formulacoes e expoe perguntas nao cobertas a geracao pura: `qual a historia de Ada Lovelace?` retorna `None` em `direct_decision`. O planejador `decide` existe quando web-auto=true, mas nao substitui uma politica de evidencias locais. `web_chat.py:395-408` pode recusar quando ha pagina relevante sem criteros de confianca; ha falhas de testes de fonte/ambiguidade.

**FATO VERIFICADO — Risco de invento pessoal reproduzido nos testes:** o baseline falha em varios `test_g2_grounding_audit.py::test_false_claim_never_streamed_or_saved` (ex.: converter "pretendo estudar" em "se formou", "talvez me mude" em "mora"). **A verificacao semantica falhou em testes simulados**, sem evidenciar taxa real com Qwen.

**HIPOTESE NAO VALIDADA:** resposta identitaria inventada pelo Qwen real a pergunta que nao acionou preflight; truncamento silencioso com janela de 4096; falsos negativos da Wikipedia/buscadores e saturacao por prompts. Sem logs Ollama reais, nao atribuir causa unica nem porcentagem de erro.

**FATO VERIFICADO — Janela/controle:** `.env.example:5` define 4096; `model/adapters/ollama.py:42-68` envia `num_ctx` e `:128-146` avisa se prompt >=95% e rejeita stream sem `done`. Nao mede tokens antes de enviar; nenhuma evidencia de truncamento ocorreu nesta auditoria.

## 5. Offline, grupo e neutralidade de fatos

**FATO VERIFICADO:** sem internet publica, importar/buscar documentos na ferramenta funciona; SQLite da sessao e da biblioteca pode iniciar; um turno de identidade protegido funciona ate sem Ollama mas retorna abstencao, nao o conhecimento importado. Um turno social `Ola, tudo bem?` com Ollama ausente gera `ModelUnavailableError`, nao uma resposta. Prova: `prova_runtime_sem_ollama.txt`. Isso nao significa que com Ollama instalado, internet publica seja necessaria: a geracao aponta para endpoint **local** em `config.py:21-29`.

**FATO VERIFICADO:** `chat/service.py:776-903` monta uma unica pesquisa web para o turno e a reutiliza com `research_guard` em `:1029,1084`; portanto ambos podem receber as mesmas fontes web. **Nao e uma ficha de fatos compartilhada de todas as camadas**: a memoria e consultada separadamente com `agent_id=profile.id` (`:279-315`), com inferencias de agente de escopo individual (`experience.py:500-514`); segundo agente le historico do primeiro (`service.py:1058-1062`). A fala do primeiro e tratada como contexto, mas a fonte canonicamente separada nao esta implementada. Em pergunta de grupo offline, ambos recusaram separadamente (`prova_grupo_offline.txt`).

**FATO VERIFICADO:** ferramentas `library.search`, `files.read`, `calc.evaluate`, memoria utilitaria nao exigem persona, via `utilities/api.py:22-38`. O **chat conversacional completo exige profile**, `chat/service.py:109-119,333-335,953-954`. `build_personality_application()` lanca `ValueError: unsupported personality profile: terceiro` para um perfil novo (`agents/personality_application.py:41-50`, prova `prova_runtime_sem_ollama.txt`).

**Degradacoes identificadas na indisponibilidade de rede:** web auto habilitada gera consultas impossiveis e consultas dependentes de tempo/resposta de buscadores; sem web, status insuficiente; cache Meili e opcional e so recuperado dentro de um fluxo `research_entity`; SearXNG pode ser local mas suas fontes ainda dependem da rede; embeddings Ollama locais podem cair para lexical (`runtime/semantic_index.py:116-126`); modelos nao baixados ou Ollama parado impedem chat. Queda **durante** streaming de rede publica nao foi testada.

## 6. Acoplamento persona/sistema e dependencia de exatamente dois agentes

**FATO VERIFICADO — acoplamentos centrais que exigem mudanca futura:** `chat/knowledge.py:246-275` e `:280-329` geram respostas factuais distintas por `agent_id == 'todd'` (violacao da fronteira fatos/persona); `chat/knowledge.py:289` remove apenas nomes hardcoded. `agents/addressing.py:20-28` e `agents/router.py:37-49` reconhecem so Todd/Morgana; `agents/participation.py:30-33,47-59,145` usa nomes fixos e `secondary_for` escolhe apenas um outro; `agents/personality_application.py:46-50` so aceita dois e falha para qualquer outro; `agents/profiles.py:120,267-294` usa branch Todd e registry codificado; `agents/output.py:10,72` lista speakers fixos.

**Outras referencias relevantes fora de `agents/`:** `utilities/web_intent.py:21,67`, `utilities/web_chat.py:426` (parsing/stopwords); `chat/dialogue_state.py:15-16,129,249-250,307,332-333,405` (texto de contrato e regex especificas), `chat/prompts.py:18,142,159`, `chat/working_context.py:14,187`; `runtime/presence.py:87`, `runtime/voice.py:55,70`, `runtime/utterance.py:31`, `runtime/host_voice.py:161,336-341`, `main.py:75` (interfaces/voz); `storage/models.py` e `chat/models.py:21` (default Morgana). `e2e/agent_scenarios.py`, `e2e/evaluator.py`, `e2e/runner.py`, `e2e/reporting.py`, `e2e/human_scenarios.py` contêm cenarios/expectativas especificos (nao sao motor factual). `api.py:359-369` lista perfis sem hardcode, mas `composition.py:81` sempre carrega a registry de dois. Referencias em migrations sao historicas e nao devem ser reescritas.

**Consequencia:** um terceiro agente nao entra apenas por arquivo de configuracao, e o modo de participacao seleciona no maximo um secundario, alternando depois entre dois. E tambem impossivel nao escolher uma persona dentro do chat atual.

## 7. Elementos que podem ser DESLIGADOS sem eliminar o nucleo

**PROPOSTA REVERSIVEL, nao aplicada:** `CAMPANARIO_WEB_AUTO_SEARCH=false` (ja aparece no `.env.example`, mas `Settings.web_auto_search` e **True quando nao ha `.env`**, `config.py:35-36`), `CAMPANARIO_PARTICIPATION_ARBITER_ENABLED=false` (participacao explicita em grupo permanece), `CAMPANARIO_CONTEXT_AUTO_SUMMARIZE=false`, `CAMPANARIO_MEILI_ENABLED=false` se nao houver politica de cache, `CAMPANARIO_SEMANTIC_MEMORY_ENABLED=false` apenas quando `embeddinggemma` nao estiver instalado e a latencia prejudicar. Despriorizar voz, remoto, GPS, RenPy e UI mobile nas proximas avaliacoes; **nao desligar SQLite, biblioteca, memoria lexical, guardas nem registro de fontes**.

## 8. Encerramento e decisao

**FATO:** scripts de source no ZIP permanecem byte a byte iguais (135/135 `src/*.py` conferidos contra arquivo original). **Nenhuma alteracao de codigo foi feita nesta fase**. Os logs e documentos novos ficam fora do diretorio de trabalho do projeto.

**HIPOTESE principal:** o problema observavel nao e primariamente a ausencia de mais regex, mas a ausencia de um caminho factual **offline-first, neutro e obrigatorio**, integrado a biblioteca local, memoria e fontes opcionais, com limite claro do que pode afirmar. Necessita validacao com conjunto fixo antes de design definitivo.

**PROPOSTA de proximo passo (ainda nao implementada):** apos aprovacao, Fase 2 desenha fluxo factual independente de agente, ficha unica por turno, recuperacao offline e interfaces de perfil, com trade-offs de latencia/VRAM. **Parar aqui e aguardar aprovacao.**
