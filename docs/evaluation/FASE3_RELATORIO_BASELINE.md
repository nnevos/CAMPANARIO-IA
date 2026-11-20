# CAMPANARIO-IA — Fase 3: conjunto fixo e baseline anterior à implementação

**Data:** 19/11/2026. **Fonte de código:** `CAMPANARIO_IA_ETAPA3_CORRIGIDO_COMPLETO.zip`, 0.8.0. **Status:** avaliação estrutural concluída; comparação empírica dos LLMs **BLOQUEADA por ausência de Ollama local**. **O núcleo do Campanario NÃO foi alterado.**

## 1. O que foi realmente entregue e executado

Corpus **versionado v1.0.0**, com hashes SHA-256 em `eval/v1/manifest.json`: 50 perguntas factuais (15 pessoas conhecidas, 7 menos conhecidas, 8 homônimos, 8 obras, 5 conceitos, 7 referentes inventados deliberadamente); 15 negativos de intenção (conversa/tarefa sem consulta factual); 20 perguntas sobre **5 arquivos sintéticos** com trecho gabaritado; 12 cenários de grupo, correção, falha de rede, persona, neutralidade e latência. Nenhuma ficha revela dados reais do usuário. A existência de um nome no corpus não é prova de sua identidade.

**FATO VERIFICADO — comando executado:**

```bash
python tools/eval_fase3.py --mode both --engine probe --project-root <diretorio-do-projeto> --report-dir eval/v1/baselines
```

Resultados em `baseline_offline_probe_stub.json` e `baseline_online_probe_stub.json`. O backend `probe` usa um **stub instrumentado** para testar fluxo/roteamento; suas falas **NÃO** são respostas de IA a avaliar. O modo `online` desse probe não realiza acesso à internet: faz uma **injeção de falha** no passo de pesquisa e mede apenas o tratamento da exceção. O modo `offline` bloqueia tentativas de conexão TCP externa dentro do processo; isso **não é** captura de pacotes/garantia de isolamento do SO.

| Indicador do código atual | Baseline offline (probe) | Baseline online (probe, **sem acesso web**) | Interpretação correta |
|---|---:|---:|---|
| Identidades/perguntas factuais no corpus | 50 | 50 | Perguntas, não verdades pré-carregadas |
| Decisões regex que acionariam guarda/consulta | 48/50 | 48/50 | 2 falsos negativos de roteamento |
| Casos que abstêm **pela guarda determinística**, não pelo modelo | 48/50 | 48/50 | Sem fonte, muitos assuntos conhecidos também são recusados |
| Trechos da biblioteca local recuperados no utilitário | 20/20 | 20/20 | Fonte disponível ao **utilitário** |
| Trechos dos documentos presentes no contexto enviado ao modelo pelo chat | **0/20** | **0/20** | Lacuna real de integração biblioteca → chat |
| Perguntas negativas classificadas indevidamente como consulta | 1/15 | 1/15 | Risco de pesquisa desnecessária |
| Casos do conjunto de grupo | 12 | 12 | Apenas subconjunto automatizado; demais pendentes |
| Egress público usado pelo benchmark | 0 observado | 0 observado | A execução não solicitou busca pública; medição no processo, não na rede do SO |

### Regras regex versus alternativas (apenas decisão de consulta)

**FATO VERIFICADO:** com `utilities/web_intent.py:direct_decision`, matriz de confusão no corpus de 65 entradas:

| Estratégia | TP | FN | FP | TN | Medição |
|---|---:|---:|---:|---:|---|
| Regex atual | 48 | 2 | 1 | 14 | **Executada** |
| Consultar base local em toda mensagem | 50 | 0 | 15 | 0 | **Simulação de política**, não implementação |
| Tool calling com Qwen3.5:9b | — | — | — | — | **Não executada**: Ollama ausente |
| Tool calling com Gemma3:12b | — | — | — | — | **Não executada**: Ollama ausente |

- **FATO:** falsos negativos `F038` (“Me fala sobre a obra 1984.”) e `F041` (“Me fala sobre deriva continental.”). Falso positivo `N007` (“Como você está hoje?”). A estatística mede apenas identificação da necessidade de consulta, **não** identidade correta, relevância de fonte ou qualidade da resposta.
- **HIPÓTESE:** consultar a base local primeiro em perguntas factuais (sem exigir internet) pode reduzir tanto alucinações quanto recusas indevidas. A medição de recall, latência e taxa de recusa após integração ainda falta.
- **PROPOSTA:** decidir entre regras, pré-consulta local e tool calling **após** executar `tools/eval_fase3_roteamento.py` em ambos os modelos no Windows. Não criar um roteador LLM sem confirmar que ele supera o baseline e não aumenta o tempo desnecessariamente.

## 2. Grupo, neutralidade, terceira persona e fontes

**FATO VERIFICADO (provas de fluxo em `group_dispositions`, com stub):**

- `G001`, `G002`: convite explícito em modo `independent_group_turn=True` produziu dois participantes, `morgana` e `todd`, inclusive para um nome propositalmente inventado. **Naturalidade, factualidade e duplicação semântica não foram avaliadas**, pois o modelo é simulado.
- `G006`: a rota endereçada a Todd funciona para conversa cotidiana (um participante); **empatia não avaliada** sem modelo real.
- `G007`: mensagem endereçada à Morgana escolheu um participante.
- `G004`: no fluxo grupal padrão, o texto não verificado do primeiro agente **aparece no contexto do segundo**; com `independent_group_turn=True`, esse texto foi excluído do contexto. Isso evidencia **exposição** ao erro, não sua adoção pelo segundo agente.
- `G008`: ferramenta de biblioteca pode ser usada sem agente, mas `ChatService.create_session(agent_id=None)` escolheu `morgana`; **chat neutro não existe**.
- `G009`: terceiro perfil inserido em `AgentRegistry` em memória gerou `ValueError` na personalidade. A criação **só por arquivo** permanece não suportada/não testável.
- `G010` online: `research_entity` foi substituído **apenas durante o probe** por função que lança `OSError` e a conversa simulada foi concluída; **não foi simulado corte real de rede após início do streaming**.
- `G003`, `G005`, `G011` e `G012`: consistência após correção, divergência sem consenso, igualdade factual entre personas e latência de modelos requerem execução com geração real, fontes verificadas e, em parte, revisão humana.

**PROPOSTA:** a Fase 4 só pode tratar `ficha factual única`, `perfil N` e `sistema sem agente` como validados depois de testes de regressão gerando **mesmos `fact_id/source_id`**, e não apenas linguagem plausível.

## 3. Baseline da suíte do projeto

**FATO VERIFICADO — novo recorte reproduzido:** `pytest` com `test_factual_quem_e.py`, `test_etapa3_grounding_naturalidade.py`, `test_utilities_offline.py`, `test_agents.py`, `test_chat_service.py` e `test_knowledge_guard_v30.py` terminou em **108 passed, 3 failed**, código de saída 1. As três falhas ocorreram em `test_knowledge_guard_v30.py`: uma esperava `grounded` e recebeu `insufficient`; duas usam stub sem `_sessions`. Log: `pytest_direcionado_fase3.log`.

**FATO VERIFICADO — teste do avaliador:** **11 passed** em `tests/test_fase3_evaluation.py`, incluindo checksum do dataset, isolamento das bases temporárias e bloqueio de socket externo. São testes da **infraestrutura da Fase 3**, não da precisão do Qwen.

**FATO VERIFICADO — primeira falha da suíte:** `pytest tests -q -x` terminou em **323 passed, 1 failed** no caso G2 de memória pessoal em `test_g2_grounding_audit.py`. Log: `pytest_primeira_falha.log`.

**EXECUÇÃO INCOMPLETA:** uma tentativa de suíte integral sem `-x` ultrapassou o limite do executor, com progresso até cerca de **84%**, **sem relatório final**: `pytest_projeto_fase3.log`. Não inferir total de aprovados/falhas a partir desse log.

**REFERÊNCIA HISTÓRICA, não reexecutada integralmente nesta Fase 3:** a Fase 1 anotou **655 passed, 30 failed, 14 warnings**, Python 3.13.5 em 34,96 s. Log preservado sob nome inequívoco `pytest_historico_fase1_655p_30f.log`. Não comparar totais de suítes parciais como se fossem a mesma amostra. O projeto exige Python 3.12, conforme `pyproject.toml`.

## 4. Baseline dos modelos Qwen e Gemma

**FATO VERIFICADO:** `http://127.0.0.1:11434/api/tags` não estava acessível neste ambiente. Tentativas com `--engine ollama` para `qwen3.5:9b` e `gemma3:12b`, nos dois modos, gravaram **`status=not_executed`** (`ollama_unavailable_ConnectError`). O comparador nativo de tool calling também anotou `not_executed_ConnectError` para ambos. **Nenhuma resposta real de nenhum dos modelos foi gerada.**

| Métrica de qualidade solicitada | Baseline atual | Próxima evidência necessária |
|---|---|---|
| Identidades inventadas (meta 0) | **Não medido** | Saída do modelo, cotejo pessoa/obra ↔ trecho/documento fonte |
| Recusa indevida | **Não medido empiricamente** | Fonte previamente recuperável e abstenção sem motivo |
| Cobertura offline | **20/20 busca de trechos na ferramenta**, mas **0/20 ligação ao chat** | Acervo local real/enciclopédia instalada e respostas citadas |
| Citações corretas | **Não medida** | Citação de arquivo/página/trecho com correspondência verificável |
| Consistência factual entre agentes | **Não medida semanticamente** | Ficha por turno, resposta de cada agente, `fact_id` |
| Distinção de ângulo e empatia | **Não medida** | Revisão humana cega por duas respostas |
| Tempo até a primeira resposta com Qwen/Gemma | **Não medido** | Telemetria no Windows + cada modelo quantizado |
| VRAM real/pico da RTX 5060 Ti | **Não medida** | Captura de GPU na máquina de destino; não estimar como benchmark |
| Queda de internet durante o stream | **Não testada** | Injeção controlada de rede no equipamento, sem afetar os bancos |

A métrica de `first_visible_ms` no runner ao vivo é **primeira saída validada e exposta pelo ChatService**, e não necessariamente o primeiro token bruto do Ollama. O runner de respostas reais armazena por padrão apenas SHA-256 e metadados, não textos; use `--include-responses` para revisão humana, com cuidado para não empregar dados pessoais. `docs/evaluation/MODELO_REVISAO_HUMANA_FASE3.csv` traz campos para revisão de todos os 82 casos.

## 5. Regras de autorização e escopo

- `--mode both --engine probe`: **não usa internet pública nem Ollama**; confirma integrações e fraquezas do caminho atual.
- `--mode both --engine ollama` **sem** `--allow-web`: chama **somente Ollama em loopback**; mesmo que o modo se chame `online`, não testa pesquisa na internet sem consentimento. Esse modo serve de controle.
- `--mode both --engine ollama --allow-web`: **autoriza explicitamente rede pública SOMENTE na metade online**; a metade offline permanece bloqueada por guarda de socket TCP no processo. O runner redireciona acesso de utilidades para **banco temporário**, removido ao final; não modifica SQLite do usuário.
- `tools/eval_fase3_roteamento.py`: avalia apenas **chamadas à ferramenta local** via endpoint Ollama em loopback. Não acessa pesquisa pública nem implementa ferramenta nova no produto.
- Não baixa Ollama, modelos, ZIM nem dependências automaticamente. Não altera `.env`, memória pessoal ou dados do usuário.

## 6. Riscos e decisão recomendada

| Prioridade | Risco com evidência | Impacto |
|---|---|---|
| P0 | 20/20 trechos da biblioteca recuperáveis, **0/20 passados ao contexto do chat** | Recusas indevidas offline e respostas sem citação |
| P0 | 2 perguntas factuais escapam à decisão de busca no conjunto fixo | Possibilidade de geração sem evidência |
| P0 | Sem ficha factual comum, resposta anterior exposta ao segundo agente no modo padrão | Propagação de inferência sem fonte |
| P1 | Modo sem agente ausente no chat e terceiro perfil lança exceção | Viola premissa de sistema independente de personas |
| P1 | Falhas G2 de memória pessoal reproduzidas | Risco de afirmar conclusões pessoais sem suporte |
| P1 | Ausência de Qwen/Gemma, Kiwix e Windows neste executor | Impossibilidade de homologar critérios reais da Fase 3 |
| P2 | Regex acionou consulta para 1/15 perguntas sociais | Custo desnecessário e latência; não representa risco factual por si só |

**HIPÓTESE:** os maiores ganhos virão da integração biblioteca/enciclopédia → ficha única, não de outra camada de regex. **PROPOSTA:** antes de aprovar qualquer modificação da Fase 4, executar o conjunto real **offline e online**, com opt-in explícito, no Windows/Python 3.12, **Qwen3.5:9b** e **Gemma3:12b** que já estejam instalados. Se um modelo ou o acervo não estiver disponível, registrar `not_executed`, não inventar métrica. Preservar o baseline v1 intacto para comparações posteriores. **Não avançar para a Fase 4 automaticamente.**
