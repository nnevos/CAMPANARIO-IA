# Roadmap — Campanario

- **Fase 0:** fundação arquitetural — concluída.
- **Fase 1:** LLM local + chat + streaming + persistência — concluída.
- **Fase 2:** Context Manager — concluída e validada no Windows/Ollama (janela recente + sumarização persistida source-aware).
- **Fundação comportamental (gate transversal):** v1/v2/v2.1 produziram melhorias, mas o teste v2.1 ainda mostrou naturalidade social artificial. Interpretacao conversacional v1 implementada como hint deterministico por turno, aguardando validacao no Ollama antes de personas completas.
- **Pragmatic Input Understanding (trilha transversal):** v1 integrada ao runtime na Conversational v1.5; Behavioral E2E Harness v1 implementado para validacao no Ollama real antes de personas/memoria nova/RAG.
- **Fase 3:** memória auditável.
- **Fase 4:** RAG/documentos.
- **Fase 5:** Morgana e Todd.
- **Fase 6:** internet controlada.
- **Fase 7:** voz.
- **Fase 8:** tools/agentes.
- **Fase 9:** learning + knowledge graph.
- **Fase 10:** realtime/dispositivos.

A descrição operacional mais atual e o próximo gate ficam em `PROJECT_STATE.md`.

## Gate historico — Conversational v1.4

Antes de personas ativas/RAG/tools, validar semantica de continuacoes curtas sobre o isolamento de modo ja implementado: acknowledgement sem recapitulacao, reflexao sem tarefa fabricada, revisao sem repeticao e abandono de topico sem puxar novo assunto. A referencia operacional de longo prazo esta em `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md`: agentes devem ocultar complexidade de modulos e servir como ponte para capacidades compartilhadas do Campanario.


## Descoberta registrada — pragmatica de entrada

Corpus real de conversa informal confirmou que compreender mensagens curtas, risadas, fragmentos,
correcoes e mudancas de topico e um problema distinto de escolher como uma persona responde. A fundacao
esta em `chat/pragmatics.py` e `docs/PRAGMATIC_INTERPRETATION_PLAN.md`, mas o gate atual continua sendo
a validacao manual do v1.4.

## Gate emergencial atual — Conversational v1.4.1

O teste manual v1.4 foi bloqueado por prompt leakage. Antes de qualquer integracao pragmatica ou nova fase, validar no Windows/Ollama que o request com system unico nao expoe instrucoes internas e que Continuation Semantics continua funcional.


## Conversational v1.4.2 — guard/recovery boundary
- Request normal continua com exatamente um `system` lider.
- `PromptLeakGuardProvider` valida a resposta inteira antes de liberar texto e faz no maximo um retry com system minimo se detectar heading interno.
- O retry nao ativa capacidades novas nem Pragmatic Input Understanding.
- O gate manual v1.4.2 precisa fechar antes de integrar pragmatica ao runtime ou avancar o roadmap.


## Gate historico — Conversational v1.5 / Pragmatic Input Integration

A v1.4.2 confirmou seguranca de prompt, mas mostrou que continuation apenas por prompt/listas ainda interpreta atos sociais literalmente. A v1.5 conecta pragmatica deterministica ao runtime antes de TurnMode/ContinuationKind. Validar naturalidade e generalizacao no Windows/Ollama antes de avancar Fase 3 ou personas.


## Gate historico — Behavioral E2E do v1.5

Executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama. O gate automatico e apenas triagem; revisar o transcript em `test_reports/behavioral_e2e/latest.html` antes de fechar naturalidade/pragmatica. Os cenarios sao variados por seed e nao devem induzir hardcode de respostas no runtime.

## Atualizacao 2026-08-24 — v1.5.1 e documentacao operacional

- Naturalidade continua como gate transversal antes da Fase 3.
- v1.5.1 adiciona self-awareness sem roleplay emocional humano, correcoes pragmaticas autoritativas e backstops objetivos de continuation.
- Behavioral E2E e o caminho padrao de validacao no Ollama real.
- `docs/manual/` e parte do contrato de entrega: recurso voltado ao usuario deve ter tutorial/estado/teste/troubleshooting antes de ser considerado concluido.
- Proximo gate: E2E v1.5.1; personas/RAG/tools/memoria cognitiva permanecem bloqueados.

## Gate historico — v1.5.2 Response Contract & Conversational Restraint

- E2E v1.5.1 mostrou que pragmatica sem contrato de saida ainda permite verbosidade, quebra de formato, drift de idioma e concordancia falsa.
- v1.5.2 adiciona contratos observaveis e retry unico; nao inclui factual answers hardcoded.
- Proximo teste: E2E real v1.5.2.
- Se naturalidade/obediencia estabilizarem e o gap restante for factualidade do modelo, abrir trilha de benchmark/grounding antes de RAG/personas completas.


## Gate historico — v1.5.3 Contract Enforcement + Context Provenance

- v1.5.2 E2E confirmou progresso, mas retry ainda nao impunha contratos e ficcao anterior contaminou resposta factual.
- v1.5.3 aplica enforcement estrutural pos-retry e proveniencia de contexto; ficcao do assistant e omitida de turnos factuais/tecnicos sem apagar o historico.
- O avaliador E2E foi endurecido para falsos PASS em estacoes e contaminacao por termos inventados.
- Resultado: E2E v1.5.3 executado; 9 PASS / 2 WARN / 0 FAIL automaticos, com gaps pragmaticos encontrados na revisao humana.
- Fase 3, RAG, personas, tools, internet e voz continuam bloqueados ate essa avaliacao.

## Gate historico — v1.5.4 Pragmatic Semantics + Natural Expression

- O E2E real v1.5.3 atingiu 9 PASS / 2 WARN / 0 FAIL automaticos, mas a revisao humana encontrou literalizacao de acknowledgement, narracao de risada, eco de vocativo, metalinguagem e verbosidade self-aware/tecnica.
- v1.5.4 corrige essas classes semanticamente e amplia o E2E com familias metamorfica, variacao de assuntos/entidades e ordem embaralhada por seed.
- Nao foram adicionadas respostas factuais hardcoded nem imitacao do vocabulario do usuario.
- Proximo gate: executar `TESTAR_COMPORTAMENTO.bat` no Ollama real e revisar o relatorio v1.5.4.
- Fase 3, RAG, personas, tools, internet e voz continuam bloqueados ate essa avaliacao.


## Gate historico — v1.5.5 Semantic Coherence + Evaluator Hardening

- v1.5.4 atingiu 11 PASS / 0 WARN / 0 FAIL automaticos, mas a revisao humana provou que PASS formal ainda podia esconder incoerencia semantica.
- v1.5.5 endurece runtime e E2E para greeting, social share, topic drop e truth-over-agreement, alem de ancoras factuais variadas no caminho creative->factual.
- O evaluator permanece deterministico e auditavel; naturalidade continua exigindo revisao humana.
- Gate executado; resultado absorvido pela v1.5.6.
- Fase 3, RAG, personas, tools, internet e voz continuam bloqueados ate esse gate.


## Gate historico — v1.5.6 Semantic Evaluator Closure

- Fecha falsos PASS restantes do v1.5.5 sem hardcode de conversas.
- Proximo gate: E2E real v1.5.6 + revisao humana.
- Se a fundacao comportamental estabilizar, o proximo passo NAO e ativar agentes: e uma refatoracao estrutural obrigatoria.
- Todd/Morgana, RAG, tools, internet, voz e memoria cognitiva permanecem bloqueados ate a refatoracao ser concluida.


## Gate historico — v1.5.7 Truth Contract + Whole-Output Validation + Factual Mechanism Hardening

- Rodar standard E2E real e revisar transcript.
- Se aprovado, rodar MEGA E2E com multiplos lotes/variacoes seeded.
- Se o mega teste for satisfatorio, iniciar refatoracao estrutural obrigatoria.
- Todd/Morgana continuam bloqueados ate a refatoracao ser concluida.


## Gate historico — v1.5.8 Semantic Closure & Technical Quality

- Rodar standard E2E real e revisar transcript completo.
- Validar risada textual da IA, registro contextual, restraint de discussao/truth e primeiro diagnostico tecnico.
- Se standard + revisao humana aprovarem, rodar MEGA E2E.
- Se mega for satisfatorio, iniciar refatoracao estrutural obrigatoria.
- Todd/Morgana continuam bloqueados ate a refatoracao ser concluida.


## Gate historico - v1.5.9

O E2E real v1.5.9 reprovou reaction/technical/factual e liberou a mudanca arquitetural v1.6.0.

## Gate historico - v1.6.0 / Response Contract Pipeline

Standard E2E + revisao humana -> mega E2E -> refatoracao estrutural obrigatoria -> somente depois agentes/personas ativos.


## Gate atual - v1.6.1 / Typed Contracts + Model Runtime Portability

- validar standard E2E com o modelo configurado;
- se necessario, trocar o modelo via configuracao sem reescrever comportamento;
- quando standard + revisao humana estabilizarem, executar mega E2E;
- mega satisfatorio libera refatoracao estrutural obrigatoria;
- Todd/Morgana permanecem bloqueados ate a refatoracao.
