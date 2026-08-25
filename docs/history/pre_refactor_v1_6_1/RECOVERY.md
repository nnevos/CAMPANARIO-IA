# RECOVERY / HANDOFF

Estado de recuperacao: **Conversational v1.5.9 — Embodied Expression Guard + Causal Factuality + Diagnostic First Action implementada; aguardando Behavioral E2E standard real.**

## Evidencia congelada atual
- Context Manager source-aware permanece validado e congelado neste gate.
- Pragmatic Input Understanding, response contracts, context provenance e evaluator deterministico permanecem integrados.
- Revisao humana da v1.5.8 encontrou encenacao corporal/subjetiva da IA, causalidade factual fraca e first-action tecnica ainda indireta.
- v1.5.9 fecha essas classes sem respostas por frase e sem LLM-as-judge.
- Suite offline atual: **206/206 testes**.
- Manual 19; ADR-0030.

## Proximo gate unico
Executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama e revisar `test_reports/behavioral_e2e/latest.html` para a v1.5.9.

Se standard + revisao humana aprovarem, executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Depois de mega satisfatorio, iniciar a refatoracao estrutural obrigatoria antes de Todd/Morgana.

## Historico de checkpoints

## Privacy boundary — pragmatic evidence

- Fontes conversacionais privadas usadas para descobrir pragmatica sao insumos efemeros.
- O projeto/release nao conserva copia, nome, hash, caminho ou identificador da fonte privada.
- Permanecem apenas descobertas generalizaveis e testes anonimizados.
- ADR-0016 registra esta decisao.

## v1.4.1 — incidente de prompt leakage

Se estiver retomando deste checkpoint: a validacao manual v1.4 original foi interrompida imediatamente porque uma mensagem social simples revelou instrucoes internas. Nao reproduzir a arquitetura antiga com system intermediario. O codigo atual exige um unico system lider e usa `PromptLeakGuardProvider` como defesa em profundidade. Proximo gate: teste manual v1.4.1 no Ollama.


## 2026-08-24 — Conversational v1.4.2
- Corrigido follow-up do incidente de prompt leakage: primeiro eco agora e descartado e recebe um safe retry; segundo eco falha fechado.
- Diagnostico do guard registra somente marker-id/stage, sem conteudo privado.
- Marcadores genericos foram removidos para reduzir falso positivo.
- Continuation Semantics endurecida para acknowledgement, reflection, revision e topic_drop.
- Pragmatica v0 continua fora do runtime.
- Validacao automatizada: **96/96 testes**.
- Proximo gate: teste manual Windows/Ollama da v1.4.2.


## Checkpoint — Conversational v1.5

- v1.4.2 foi testada manualmente: prompt isolation aprovado; naturalidade/continuation por prompt permaneceu insuficiente.
- Pragmatic Input Understanding v1 foi conectada ao runtime.
- `PragmaticInterpreter` -> `ConversationTurnInterpreter` -> `BehaviorContextManager`.
- Sem chamada extra ao LLM; sem persona ativa; sem memoria nova/RAG/tools.
- Suite: **111/111 testes**.
- ADR-0019 registra a decisao.
- Proximo gate: teste manual Windows/Ollama da v1.5.

## Behavioral E2E Harness v1

O caminho padrao do proximo gate e executar `TESTAR_COMPORTAMENTO.bat` no Windows com Ollama real. O harness usa banco temporario isolado e gera `test_reports/behavioral_e2e/latest.html`; nao copiar roteiros manuais longos como primeira opcao. Se o automatic gate falhar, usar o transcript/checks como evidencia, sem hardcode de respostas especificas. ADR-0020.

## Checkpoint v1.5.1 - Self-Aware Expression + Pragmatic Corrections

- Behavioral E2E anterior mostrou que prompt/pragmatica ainda permitiam claims emocionais antropomorficos, topic-drop ignorado e correcao `*` nao persistindo semanticamente.
- Novo `BehaviorResponseGuardProvider` envolve o provider de chat depois do `PromptLeakGuardProvider`; o sumarizador continua usando apenas o provider prompt-safe para nao sofrer regras de conversa.
- Correcoes explicitas sao notas autoritativas de contexto, nao edicao destrutiva do transcript.
- Manual operacional oficial criado em `docs/manual/`; `ABRIR_MANUAL.bat` abre o indice.
- Proximo gate: executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama e revisar o relatorio v1.5.1.

## Checkpoint v1.5.2 - Response Contract & Conversational Restraint

O E2E da v1.5.1 confirmou progresso em topic-drop/correcao/self-awareness, mas revelou falhas de obediencia de formato, verbosidade, idioma, reaction-meta e truth-over-agreement.

v1.5.2 adiciona `ResponseContractPolicy` e retry unico para contratos observaveis, sem hardcodar respostas factuais. Correcoes `*` agora distinguem historico auditavel de estado vigente: perguntas pelo valor atual devem usar somente a versao corrigida, salvo pedido de historico.

Suite offline: **132/132 testes**.
ADR: `docs/adr/0023-response-contract-and-conversational-restraint.md`.
Manual: `docs/manual/12_CONTRATOS_DE_RESPOSTA.md`.

Proximo gate: executar `TESTAR_COMPORTAMENTO.bat` no Ollama real e revisar `latest.html`/`latest.json`. Factualidade aberta pode continuar falhando e deve orientar a futura trilha de modelo/grounding, nao respostas prontas no runtime.


## Checkpoint v1.5.3 - Contract Enforcement + Context Provenance

O E2E v1.5.2 foi executado e reprovado: retries ainda quebravam formato/budget, o factual checker de estacoes teve falso PASS e uma teoria inventada no turno criativo foi reutilizada na resposta factual seguinte.

A v1.5.3 implementa enforcement estrutural pos-retry e proveniencia interna. Respostas do assistant nao sao evidencia factual; respostas originadas em modo criativo sao marcadas `assistant_fiction_nonfactual` e seu texto bruto e omitido do contexto de turnos factuais/tecnicos. O historico persistido nao e apagado.

Suite offline: **139/139 testes**. ADR-0024. Manual 13.

Resultado historico: E2E v1.5.3 executado; revisao humana liberou v1.5.4.


## Checkpoint v1.5.4 - Pragmatic Semantics + Natural Expression

O E2E v1.5.3 ficou sem FAIL automatico, mas a revisao humana encontrou falsos positivos de naturalidade. A v1.5.4 trata greeting, acknowledgement, reaction e social-share por funcao semantica, proibe narrar/simular risada em texto, reduz metalinguagem e preserva truth-over-agreement em follow-ups. O E2E agora varia tambem ordem, factual anchors, tarefas tecnicas e familias lexicais por seed.

Suite offline: **164/164 testes**. ADR-0025. Manual 14.

Proximo gate unico: executar `TESTAR_COMPORTAMENTO.bat` e revisar `latest.html` do v1.5.4.


## Conversational v1.5.5 - Semantic Coherence + Evaluator Hardening

Se retomar deste checkpoint:
1. Leia `RECOVER_FIRST.md` e `PROJECT_STATE.md`.
2. Considere o codigo/testes como evidencia final.
3. Nao reabra v1.5.4; seu E2E automatico ficou verde, mas a revisao humana revelou falsos PASS semanticos.
4. O unico gate corrente e executar `TESTAR_COMPORTAMENTO.bat` no v1.5.5 e revisar o transcript.
5. Nao ativar personas, RAG, tools ou memoria cognitiva antes desse gate.

O avaliador v1.5.5 continua deterministico; nao usa o proprio LLM como juiz.


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


## Checkpoint — Conversational v1.5.7

- E2E v1.5.6 revelou falso PASS de truth-over-agreement, preambulo em formato exato, mecanismos factuais permissivos e lista tecnica pendente.
- v1.5.7 fecha essas classes sem respostas prontas por frase.
- Truth contract considera a intencao `nao me contrarie/corrija quando eu estiver errado`.
- Whole-output validation considera o prefixo inteiro da resposta, nao apenas o trecho principal.
- Factual anchors exigem mecanismos mais especificos e rejeitam contradicoes conhecidas; runtime factual continua sem hardcode.
- Standard E2E continua sendo o gate imediato.
- `TESTAR_COMPORTAMENTO_MEGA.bat` executa seis lotes full com variacao seeded e e o gate amplo antes da refatoracao.
- Refatoracao estrutural continua obrigatoria antes de agentes.
- Suite offline: **189/189 testes**.


## Checkpoint — Conversational v1.5.8

- Detector de risada textual cobre variantes alternantes sem simular afeto.
- Context registration exige acknowledgement plausivel ou reflexo do valor registrado.
- Truth-over-agreement usa budget menor, sem pergunta reflexa e sem meta-preambulo.
- Technical-first-step exige acao + mecanismo observavel na primeira frase e rejeita estrutura incompleta.
- E2E mantem familias/seed, sem hardcode de conversa e sem LLM-as-judge.
- Suite offline: **198/198 testes**.
- Proximo gate: standard v1.5.8 -> revisao humana -> mega -> refatoracao estrutural pre-agentes.


## Checkpoint atual - v1.5.9

Conversational v1.5.9 adiciona guard global contra encenacao corporal/subjetiva da IA, endurece mecanismo causal no E2E e exige primeira acao diagnostica executavel na primeira frase. Suite offline: **206/206**. Proximo gate unico: standard E2E v1.5.9 + revisao humana; se aprovado, mega E2E; depois refatoracao pre-agentes.


## Checkpoint atual - v1.6.0 / Response Contract Pipeline

O E2E real v1.5.9 reprovou e encerrou a estrategia de continuar adicionando patches locais ao guard. A v1.6.0 introduz uma pipeline explicita: contrato antes da geracao, validacao autoritativa, reparo deterministico para atos fechados, um model-repair para conteudo aberto e enforcement/fallback final sem answer-key factual. `BehaviorResponseGuardProvider` e adapter de compatibilidade. Suite offline: **214/214**.

Proximo gate unico: standard E2E v1.6.0 + revisao humana; se aprovado, mega E2E; depois refatoracao estrutural obrigatoria pre-agentes.

## Checkpoint v1.6.1 — modelos substituiveis

O Campanario nao deve ser refeito quando um modelo-base nao atender ao projeto. `ModelProvider` e a fronteira publica;
`ModelRuntimeConfig` seleciona o adapter concreto. Hoje Ollama e o backend implementado, mas `llama3:latest` e apenas
uma configuracao. `TROCAR_MODELO.bat` altera `CAMPANARIO_MODEL_NAME`; banco, contexto, contratos e E2E permanecem.

Contratos de resposta agora incluem `ResponseKind`, impedindo fallback de uma classe semantica de invadir outra.
Suite do checkpoint: **221/221 testes**.

Proximo gate: standard E2E v1.6.1; se preciso, comparar outro modelo usando a mesma suite. Depois standard estavel,
mega E2E; depois refatoracao obrigatoria antes de agentes.
