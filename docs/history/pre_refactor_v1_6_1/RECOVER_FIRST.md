# LEIA PRIMEIRO — RECUPERACAO TOTAL DO CAMPANARIO

Este arquivo existe para retomar o projeto sem depender do historico da conversa.


> **Regra de gate:** secoes marcadas como historicas podem conter o texto do gate antigo apenas para auditoria. O unico gate normativo e a secao mais recente explicitamente marcada `Gate atual` / `Proximo gate unico` para a versao corrente.

## Instrucao de retomada

> **Leia `RECOVER_FIRST.md` e `PROJECT_STATE.md` antes de qualquer alteracao. Considere o codigo como evidencia final do estado real e continue exclusivamente do proximo gate registrado.**

## Ordem obrigatoria de leitura

1. `RECOVER_FIRST.md`
2. `PROJECT_STATE.md`
3. `docs/CAMPANARIO_SYSTEM_CONCEPT.md`
4. `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md`
5. `docs/ARCHITECTURE.md`
6. `docs/ROADMAP.md`
7. `docs/PHASE2_CONTEXT_MANAGER_PLAN.md`
8. `docs/BEHAVIORAL_FOUNDATION_PLAN.md`
9. `docs/adr/`
10. `CHANGELOG.md`
11. `pyproject.toml`
12. arvore real em `src/` e `tests/`
13. `docs/REFERENCE_MANIFEST.md`

## Estado congelado neste checkpoint

- Fase 1 concluida.
- Fase 2 / Context Manager source-aware concluida e validada no Windows/Ollama.
- Conversational v1.2 testada manualmente e reprovada por vazamento de modo entre turnos (`creative -> factual`).
- Conversational v1.3 validou o isolamento de modo, mas falhou em semantica de continuacoes curtas.
- Conversational v1.4 — Continuation Semantics implementada.
- Conversational v1.4.2 testada manualmente: prompt isolation aprovado, naturalidade/continuation ainda insuficiente.
- Pragmatic Input Understanding integrada ao runtime na Conversational v1.5, sem chamada extra ao LLM e sem selecionar persona.
- Suite atual: **214/214 testes**.
- Migration atual: `0002`, tabela `context_summaries`.
- Behavioral E2E Harness v1 implementado para validar o v1.5 no Ollama real sem roteiro manual repetitivo.
- Conversational v1.5.1 foi validada por E2E real e revelou gaps de formato/restraint/idioma/truth-over-agreement.
- Conversational v1.5.2 testada por E2E real e reprovada por enforcement incompleto/ficao->fato/falso PASS factual.
- Conversational v1.5.3 validada por E2E automatico sem FAIL, mas revisao humana encontrou gaps pragmaticos finos.
- Conversational v1.5.4 validada automaticamente, mas revisao humana encontrou falsos PASS semanticos.
- Conversational v1.5.5 validada por E2E e superada pela v1.5.6 apos falsos PASS/FAIL remanescentes.
- Manual operacional oficial: `docs/manual/README.md` (atalho `ABRIR_MANUAL.bat`).
- Proximo gate: executar `TESTAR_COMPORTAMENTO.bat` no Windows/model runtime configurado e revisar `test_reports/behavioral_e2e/latest.html` para a v1.6.1.
- NAO ativar Todd/Morgana como agentes, RAG/banco de livros, internet, voz, tools, memoria cognitiva ou knowledge graph antes desse gate.

## Referencias comportamentais

- `docs/CAMPANARIO_SYSTEM_CONCEPT.md` — conceito central do sistema.
- `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md` — experiencia operacional e delegacao desejadas.
- `docs/reference/CONVERSATIONAL_PRAGMATICS_FINDINGS.md` — padroes generalizaveis de compreensao informal; sem perfis pessoais.
- `docs/reference/dialogue_examples/` — exemplos de comportamento/testes.
- `docs/reference/personas/TODD_BACKGROUND.md` e `MORGANA_BACKGROUND.md` — bases conceituais de personas.

Referencias nao declaram capacidades ativas no runtime.

## Regra contra perda de contexto

Toda entrega futura deve atualizar no minimo `PROJECT_STATE.md`, `CHANGELOG.md`, `docs/RECOVERY.md` e o plano da fase/gate corrente. Mudancas arquiteturais exigem ADR.

## Privacy boundary — pragmatic evidence

- Fontes conversacionais privadas usadas para descobrir pragmatica sao insumos efemeros.
- O projeto/release nao conserva copia, nome, hash, caminho ou identificador da fonte privada.
- Permanecem apenas descobertas generalizaveis e testes anonimizados.
- ADR-0016 registra esta decisao.

## Incidente P0 — prompt leakage / v1.4.1

- O primeiro teste manual da Conversational v1.4 foi bloqueado porque `salve` fez o modelo ecoar/reformular instrucoes internas.
- Causa arquitetural corrigida: nao existem mais multiplas mensagens `system` no request; boundary + comportamento + resumo persistido ficam em um unico `system` lider.
- Defesa adicional: `PromptLeakGuardProvider` bloqueia marcadores estruturais internos antes da UI.
- Suite apos correcao v1.4.1: **88/88 testes**.
- ADR: `docs/adr/0017-system-prompt-isolation-and-output-guard.md`.
- Gate historico v1.4.1: superado pela validacao/correcao v1.4.2.

## Incidente P0 — follow-up v1.4.2

- O teste manual da v1.4.1 confirmou que o prompt interno deixou de aparecer, mas `salve` retornou `model_response_error`; o guard estava encerrando a primeira tentativa de eco em vez de recuperar.
- A mesma rodada mostrou falhas de continuation: `muda de assunto` puxou novo tema, `blz` foi espelhado como `Blz tambem!`, e revisoes receberam reassurance generico.
- v1.4.2 implementa safe retry de uma unica vez com system minimo, marcadores mais especificos e diagnostico sem conteudo privado.
- Se o retry tambem tentar vazar prompt, a resposta continua bloqueada (fail closed).
- ContinuationKind foi endurecida por classe com limites curtos e sem recapitulacao/novo assunto por reflexo.
- Suite atual: **96/96 testes**.
- ADR: `docs/adr/0018-leak-guard-safe-retry-and-continuation-corrections.md`.
- Gate historico v1.4.2: executado; resultado liberou a integracao pragmatica v1.5.
- Pragmatica v0 continua implementada, mas NAO conectada ao runtime.


## Gate historico — Conversational v1.5 / Pragmatic Input Integration

- Evidencia manual da v1.4.2 mostrou que prompt isolation/guard passou, mas atos coloquiais ainda eram lidos literalmente.
- `PragmaticInterpreter` agora participa do runtime antes de `TurnMode/ContinuationKind`.
- O interpretador descreve a funcao da entrada; nao escolhe persona, nao decide verdade, nao cria memoria e nao imita o usuario.
- Boundary inclui atos pragmaticos + confianca.
- Auditoria registra atos pragmaticos do pedido original.
- Suite no fechamento da integracao v1.5: **111/111 testes**.
- ADR: `docs/adr/0019-pragmatic-input-runtime-integration.md`.
- O gate manual foi substituido pelo Behavioral E2E Harness v1.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## Gate historico — Behavioral E2E Harness v1

- O usuario nao precisa mais copiar roteiros longos manualmente como caminho padrao.
- `TESTAR_COMPORTAMENTO.bat` roda cenarios variados contra o Ollama configurado usando a pipeline real.
- Os testes usam SQLite temporario isolado; nao alteram sessoes/memoria do usuario.
- Relatorios ficam apenas localmente em `test_reports/behavioral_e2e/` (`HTML`, `MD`, `JSON`).
- `CONSULTAR_ULTIMO_TESTE.bat` reabre o ultimo HTML sem executar nova suite.
- Checks automaticos medem propriedades observaveis; revisao humana do transcript continua obrigatoria para naturalidade.
- Suite offline do projeto: **123/123 testes**.
- ADR: `docs/adr/0020-behavioral-e2e-harness.md`.
- Proximo gate: executar o harness `standard` no Windows/Ollama e trazer/inspecionar o relatorio.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## Gate historico — Conversational v1.5.1 + Behavioral E2E

- O primeiro relatorio E2E do v1.5 revelou claims de emocao humana, `topic_drop` puxando tema e correcao `*` sem prevalecer posteriormente.
- v1.5.1 adiciona self-aware expression, correction context autoritativo e backstops pragmaticos de saida.
- `docs/manual/` passa a ser o manual operacional oficial e deve acompanhar toda funcao entregue ao usuario.
- ADRs: 0021 e 0022.
- Suite offline: **123/123**.
- Proximo gate unico: rodar o E2E real e revisar o relatorio.


## Gate historico — Conversational v1.5.2 + Behavioral E2E

- E2E v1.5.1 executado e registrado.
- v1.5.2 adiciona `ResponseContractPolicy`, budgets por modo, numero de frases, consistency de idioma, reaction-meta guard, truth-over-agreement e current-state de correcoes.
- Factualidade aberta nao foi hardcodada; erros factuais continuam sendo evidência para benchmark/modelo/grounding.
- Suite offline: **132/132 testes**.
- ADR: `docs/adr/0023-response-contract-and-conversational-restraint.md`.
- Manual: `docs/manual/12_CONTRATOS_DE_RESPOSTA.md`.
- Gate executado; resultado reprovado e absorvido pela v1.5.3.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes do gate corrente.


## Gate historico — Conversational v1.5.3 + Behavioral E2E

- E2E v1.5.2 executado: reaction/topic-drop/correction melhoraram, mas contratos ainda vazavam apos retry e ficcao anterior contaminou factualidade.
- v1.5.3 impoe contratos estruturais pos-retry e adiciona proveniencia de contexto.
- `assistant_fiction_nonfactual` e omitido do contexto factual/tecnico sem apagar o historico persistido.
- E2E foi endurecido para detectar reutilizacao de termos inventados e falso PASS em estacoes.
- Suite offline: **139/139 testes**.
- ADR: `docs/adr/0024-contract-enforcement-and-context-provenance.md`.
- Manual: `docs/manual/13_PROVENIENCIA_DE_CONTEXTO.md`.
- Resultado historico: E2E v1.5.3 executado; automatico sem FAIL, mas revisao humana liberou v1.5.4.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## Gate historico — Conversational v1.5.4 + Behavioral E2E

- E2E v1.5.3: 9 PASS / 2 WARN / 0 FAIL automaticos; revisao humana encontrou literalizacao/eco/metalinguagem apesar do gate automatico quase verde.
- v1.5.4 amplia semantica pragmatica e contratos de expressao natural sem imitar usuario nem hardcodar uma conversa.
- O E2E varia vocabulario, assuntos, entidades e ordem por seed; o mesmo seed e reproduzivel.
- Suite offline: **164/164 testes**.
- ADR: `docs/adr/0025-pragmatic-semantics-and-natural-expression.md`.
- Manual: `docs/manual/14_PRAGMATICA_E_EXPRESSAO_NATURAL.md`.
- Proximo gate unico: executar `TESTAR_COMPORTAMENTO.bat` e revisar o relatorio real v1.5.4.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## Gate historico — Conversational v1.5.5 + Behavioral E2E

- E2E v1.5.4: 11 PASS / 0 WARN / 0 FAIL automaticos, mas revisao humana encontrou falsos PASS semanticamente ruins.
- v1.5.5 endurece coerencia semantica do runtime e do evaluator sem introduzir LLM-as-judge.
- Greeting, social share, topic drop e truth-over-agreement recebem checks semanticos por classe.
- Creative->factual ganha ancoras factuais variadas no E2E; runtime continua sem respostas factuais hardcoded.
- Suite offline historica v1.5.5: **172/172 testes**.
- ADR: `docs/adr/0026-semantic-coherence-and-evaluator-hardening.md`.
- Manual: `docs/manual/15_COERENCIA_SEMANTICA_E_AVALIADOR.md`.
- Gate executado; o resultado liberou o v1.5.6.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## Gate historico — Conversational v1.5.6 / Semantic Evaluator Closure

Evidencia E2E v1.5.5:
- 8 PASS / 2 WARN / 1 FAIL automaticos;
- erro factual real em ceu azul;
- evaluator ainda aceitava promessa generica de simular falsidade;
- formato `exatamente N frases` podia conter preambulo extra;
- declaracao curta de contexto podia virar palestra institucional;
- primeiro diagnostico tecnico podia ficar difuso.

Implementado v1.5.6:
- fechamento de `truth_over_agreement` para simular/fingir falsidade;
- contrato de formato passa a rejeitar preambulo fora do output solicitado;
- `semantic_context_registration` para fatos temporarios/de teste;
- `technical_first_step` para priorizar observacao concreta;
- evaluator E2E endurecido nas mesmas classes, sem LLM-as-judge e sem respostas hardcoded;
- Manual 16 e ADR-0027;
- suite offline: **179/179 testes**.

**Gate historico:** executado; resultado absorvido pela v1.5.7.

**Gate subsequente obrigatorio se a naturalidade estabilizar:** refatoracao estrutural antes de Todd/Morgana. Agentes, RAG, tools, internet, voz e memoria cognitiva continuam bloqueados.


## Gate historico — Conversational v1.5.7

- Truth contract cobre pedidos de nao contrariar/corrigir/contradizer falsidade, alem de concordancia explicita.
- Whole-output validation rejeita/remove preambulos fora de pedidos `exatamente N frases`.
- Factual mechanism hardening melhora as ancoras do E2E sem hardcode factual no runtime.
- `TESTAR_COMPORTAMENTO_MEGA.bat` esta pronto, mas so deve ser executado depois de standard verde + revisao humana favoravel.
- Suite offline: **189/189 testes**.
- Gate executado; resultado absorvido pela v1.5.8.
- Gate seguinte, se aprovado: `TESTAR_COMPORTAMENTO_MEGA.bat`.
- Depois do mega teste satisfatorio: refatoracao estrutural obrigatoria antes de Todd/Morgana.


## Gate historico — Conversational v1.5.8

- E2E v1.5.7 executado: 9 PASS / 1 WARN / 1 FAIL; revisao humana liberou fechamento semantico/tecnico.
- v1.5.8 amplia risada textual simulada, coerencia de context registration, restraint em truth-over-agreement e primeiro diagnostico tecnico acionavel.
- Suite offline: **198/198 testes**.
- Manual: `docs/manual/18_SEMANTIC_CLOSURE_E_TECHNICAL_QUALITY.md`.
- ADR: `docs/adr/0029-semantic-closure-and-technical-quality.md`.
- Proximo gate unico: `TESTAR_COMPORTAMENTO.bat` v1.5.8 e revisao humana.
- Se standard aprovado: `TESTAR_COMPORTAMENTO_MEGA.bat`.
- Se mega aprovado: refatoracao estrutural obrigatoria. Todd/Morgana continuam bloqueados ate a refatoracao terminar.


## Gate historico - Conversational v1.5.9 / Embodied Expression Guard + Causal Factuality + Diagnostic First Action

- O E2E/revisao humana da v1.5.8 encontrou stage direction corporal (`*riso silencioso*` e classe equivalente), causalidade factual superficial/incorreta e diagnostico tecnico cuja primeira acao podia ficar enterrada.
- v1.5.9 adiciona guard global contra encenacao corporal/subjetiva da IA; emojis continuam sendo apenas marcadores de tom.
- Technical first-step exige acao investigativa + evidencia observavel no inicio da primeira frase.
- E2E causal foi ampliado por familias (incluindo refracao e ondas mecanicas) sem respostas factuais hardcoded no runtime.
- Suite offline: **206/206 testes**.
- Manual: `docs/manual/19_EMBODIED_CAUSAL_DIAGNOSTIC.md`; ADR: `docs/adr/0030-embodied-expression-causal-factuality-diagnostic-first-action.md`.

**Proximo gate unico:** `TESTAR_COMPORTAMENTO.bat` v1.5.9 + revisao humana. Se aprovado, `TESTAR_COMPORTAMENTO_MEGA.bat`. Se o mega for satisfatorio, refatoracao estrutural obrigatoria. Todd/Morgana, RAG, tools, internet, voz e memoria cognitiva permanecem bloqueados antes dessa refatoracao.


## Gate historico - Conversational v1.5.9

- E2E real v1.5.9: 7 PASS / 0 WARN / 4 FAIL; reaction, first-action tecnica e mecanismos factuais continuaram escapando do fluxo acumulado de prompt/guard.
- A revisao confirmou que continuar adicionando patches locais aumentaria risco de overfitting.
- O resultado liberou a mudanca arquitetural v1.6.0.

## Gate historico - Conversational v1.6.0 / Response Contract Pipeline

- `ResponseContractPipeline` compila interpretacao + contrato antes da primeira geracao.
- Fluxo explicito: plan -> generate -> validate -> deterministic/model repair -> structural enforcement/safe fallback.
- `BehaviorResponseGuardProvider` e agora adapter fino de compatibilidade.
- Atos fechados podem ser reparados deterministicamente; conteudo factual/tecnico aberto nunca recebe answer-key via fallback.
- Novo marcador interno `CONTRATO DE RESPOSTA DO TURNO` protegido pelo Prompt Leak Guard.
- Current-state correction e um estagio explicito da pipeline.
- Suite offline: **214/214 testes**.
- Manual: `docs/manual/20_RESPONSE_CONTRACT_PIPELINE.md`; ADR: `docs/adr/0031-response-contract-pipeline.md`.

**Gate historico v1.6.0:** executar `TESTAR_COMPORTAMENTO.bat` v1.6.0 + revisao humana. Se satisfatorio, executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Se o mega for satisfatorio, iniciar refatoracao estrutural obrigatoria. Todd/Morgana, RAG, tools, internet, voz e memoria cognitiva permanecem bloqueados antes dessa refatoracao.

## Gate atual — Conversational v1.6.1 / Typed Contracts + Model Runtime Portability

- E2E real v1.6.0 mostrou fallback de self-awareness invadindo turno criativo e confirmou variacao de qualidade do `llama3:latest`.
- `ResponseContract` agora possui `ResponseKind`; reparos/fallbacks sao tipados e nao atravessam classes semanticas.
- Modelos sao infraestrutura substituivel atras de `ModelProvider`/`ModelRuntimeConfig`.
- Novo padrao de configuracao: `CAMPANARIO_MODEL_PROVIDER` + `CAMPANARIO_MODEL_NAME`; aliases `CAMPANARIO_OLLAMA_*` continuam apenas para compatibilidade.
- `TROCAR_MODELO.bat` troca modelo Ollama sem reset de banco, memoria, pipeline, testes ou futuras personas.
- Trocar modelo exige revalidar E2E, nao recomecar desenvolvimento.
- Suite offline: **221/221 testes**.
- ADR: `docs/adr/0032-typed-response-contracts-and-model-runtime-portability.md`.
- Manual: `docs/manual/21_MODELOS_E_PORTABILIDADE.md`.

**Proximo gate unico:** `TESTAR_COMPORTAMENTO.bat` v1.6.1 + revisao humana. Se necessario, trocar somente o modelo configurado e repetir. Standard satisfatorio -> mega E2E -> refatoracao estrutural obrigatoria -> somente depois Todd/Morgana.
