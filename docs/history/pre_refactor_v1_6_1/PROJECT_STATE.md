# CAMPANARIO — PROJECT STATE / HANDOFF

> **ARQUIVO CRITICO DE CONTINUIDADE.** Leia antes de alterar o projeto e atualize apos cada incremento relevante.


> **Regra de gate:** secoes marcadas como historicas podem conter o texto do gate antigo apenas para auditoria. O unico gate normativo e a secao mais recente explicitamente marcada `Gate atual` / `Proximo gate unico` para a versao corrente.

## 1. Estado atual

- Fase 1: concluida.
- Fase 2 / Context Manager source-aware: concluida e validada no Windows/Ollama.
- Behavior v1/v2/v2.1: absorvidos pela fundacao atual.
- Interpretacao Conversacional v1/v1.1/v1.2: testadas manualmente e absorvidas.
- Interpretacao Conversacional v1.3 — Turn Boundary & Mode Isolation: validada parcialmente; isolamento de modo melhorou, mas continuacoes curtas repetiram respostas e naturalidade ainda falhou.
- Interpretacao Conversacional v1.4.2: testada manualmente; seguranca de prompt passou, mas naturalidade/continuation por prompt permaneceu insuficiente.
- Interpretacao Conversacional v1.5 — Pragmatic Input Integration: implementada e validada pelo primeiro Behavioral E2E, que revelou novos gaps.
- Conversational v1.5.1: E2E real executado; melhorou topic-drop/correcao/self-awareness, mas falhou em formato, restraint, idioma e truth-over-agreement.
- Conversational v1.5.2: E2E real executado; progresso estrutural, mas falhou em enforcement de contrato, contaminacao ficcao->fato e falso PASS factual.
- Conversational v1.5.3: E2E real executado; automatico 9 PASS / 2 WARN / 0 FAIL, mas revisao humana encontrou gaps pragmaticos finos.
- Conversational v1.5.4/v1.5.5/v1.5.6: E2E reais executados e absorvidos pelos incrementos seguintes.
- Conversational v1.5.7: E2E real executado; 9 PASS / 1 WARN / 1 FAIL, liberando o fechamento v1.5.8.
- Conversational v1.5.8 — Semantic Closure & Technical Quality: implementada; aguardando E2E real no Windows/Ollama.
- Suite atual: **214/214 testes**.
- Migration atual: `0002` (`context_summaries`).
- Temperatura default: `0.35`.

## 2. Fundacoes congeladas

Memoria/contexto source-aware permanece validada e nao deve ser alterada neste gate. O teste longo preservou `CODIGO-TESTE-4821`, capivara, verde, Marte e astronomia/historia/programacao inclusive apos reinicio.

## 3. Evidencia manual mais recente — Conversational v1.3

Passou/melhorou:
- `creative -> factual` deixou de carregar ficcao para o turno factual seguinte;
- `social -> technical` voltou ao contrato tecnico;
- formato solicitado em duas frases e calculo `23 x 7` foram obedecidos;
- boundary por turno mostrou efeito real no Ollama.

Falhou:
- `aham`, `mas posso estar errado`, `pois entao` e `ok` repetiram integralmente a resposta anterior;
- `deixa isso pra la por enquanto` encerrou o tema, mas ainda puxou automaticamente um novo assunto;
- conversa social segue com tendencia a atendimento/perguntas por reflexo;
- factualidade do modelo-base ainda apresentou erros (`chega` em vez de guepardo; explicacao molecular incorreta para gelo);
- auditoria nao detectou as repeticoes nem os principais erros factuais.

Conclusao: isolamento de modo foi aprovado como mecanismo, mas `continuation` precisava distinguir a funcao da mensagem curta em vez de tratar todas as continuacoes igualmente.

## 4. Incremento atual — Conversational v1.4 / Continuation Semantics

- `TurnMode.CONTINUATION` permanece como modo de alto nivel;
- adicionada `ContinuationKind` com `acknowledgement`, `reflection`, `revision` e `topic_drop`;
- acknowledgements proibem recapitulacao automatica da resposta anterior;
- reflexoes curtas reconhecem o fluxo sem fabricar tarefa;
- revisoes/hesitacoes respondem ao ponto de incerteza sem repetir a explicacao inteira;
- abandono de topico encerra o tema sem perguntar automaticamente o proximo;
- boundary informa `SEMANTICA DE CONTINUACAO`;
- trace de auditoria registra a semantica esperada;
- sinais observaveis detectam repeticao integral da resposta imediatamente anterior;
- regressao automatizada cobre exemplos variados de cada categoria.

ADR: `docs/adr/0014-continuation-semantics.md`.

## 5. Conceito e referencia

- `docs/CAMPANARIO_SYSTEM_CONCEPT.md`: Campanario = sistema persistente; agentes = personas/pontes.
- `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md`: delegacao natural e conhecimento compartilhado do sistema.
- Referencias nao declaram capacidades ativas.

## 5A. Descoberta nova — pragmatica de entrada

- corpus privado real foi usado somente para extrair padroes generalizaveis de comunicacao informal;
- a arquitetura passa a distinguir: pragmatica geral -> futura adaptacao ao usuario -> persona de resposta;
- novo `src/campanario/chat/pragmatics.py` representa atos conversacionais sem selecionar persona ou resposta;
- a fundacao v0 foi conectada ao runtime no v1.5 apos o gate manual v1.4.2 demonstrar insuficiencia do continuation apenas por prompt;
- nenhuma informacao pessoal/lore do corpus foi incorporada ao comportamento central;
- documentos: `docs/reference/CONVERSATIONAL_PRAGMATICS_FINDINGS.md`, `docs/PRAGMATIC_INTERPRETATION_PLAN.md`, ADR-0015.

O bloqueio foi removido somente apos evidencia manual do v1.4.2. A integracao permanece separada de persona, memoria nova, RAG e tools.

## 6. Proximo gate registrado

**Executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama e revisar `test_reports/behavioral_e2e/latest.html` para validar a Conversational v1.5.8, com foco em risada textual da IA, registro contextual semanticamente valido, restraint de truth-over-agreement e primeiro diagnostico tecnico acionavel.**

Se o standard ficar verde **e** a revisao humana estiver satisfatoria, executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Se o mega tambem for satisfatorio, iniciar a refatoracao estrutural obrigatoria antes de Todd/Morgana.

Nao ativar personas completas, RAG, banco de livros, internet, voz, tools ou memoria cognitiva antes da refatoracao.

## 7. Regra de retomada

1. Ler `RECOVER_FIRST.md` e este arquivo.
2. Conferir codigo/testes como evidencia final.
3. Continuar exclusivamente do gate da secao 6.
4. Mudanca arquitetural exige ADR.
5. Atualizar failsafes em toda entrega relevante.

## Privacy boundary — pragmatic evidence

- Fontes conversacionais privadas usadas para descobrir pragmatica sao insumos efemeros.
- O projeto/release nao conserva copia, nome, hash, caminho ou identificador da fonte privada.
- Permanecem apenas descobertas generalizaveis e testes anonimizados.
- ADR-0016 registra esta decisao.

## 8. Correcao emergencial — Conversational v1.4.1 / System Prompt Isolation

O primeiro gate manual v1.4 foi BLOQUEADO por prompt leakage: uma entrada social simples fez `llama3:latest` ecoar/reformular o prompt interno.

Correcao implementada:
- exatamente uma mensagem `system`, sempre na primeira posicao;
- turn boundary incorporado ao `system` lider, nunca inserido entre turnos;
- resumo persistido continua no mesmo bloco `system`;
- `PromptLeakGuardProvider` bloqueia marcadores internos durante streaming, inclusive entre chunks;
- resposta bloqueada nao deve ser persistida como mensagem do assistant;
- regressao automatizada cobre estrutura de request e leakage no stream.

Suite atual: **88/88 testes**.
ADR: `docs/adr/0017-system-prompt-isolation-and-output-guard.md`.

### Proximo gate atualizado

**Validar Conversational v1.4.1 no Windows/Ollama, primeiro confirmando que nenhuma instrucao interna aparece na resposta; depois retomar o teste de Continuation Semantics.**

Pragmatica v0 permanece implementada, mas NAO conectada ao runtime. RAG, personas, tools e memoria nova continuam bloqueados.

## 9. Incremento atual — Conversational v1.4.2 / Leak Guard Diagnostics + Continuation Corrections

Evidencia manual v1.4.1:
- nenhum prompt interno apareceu na UI;
- a primeira mensagem social `salve` terminou em `model_response_error`, indicando bloqueio sem recuperacao;
- `muda de assunto` ainda perguntou o proximo tema;
- acknowledgement curto ainda podia ser espelhado artificialmente (`Blz tambem!`);
- revisao/hesitacao ainda recebia reassurance generico;
- isolamento ficcao -> factual e formato numerico continuaram funcionando.

Correcao v1.4.2:
- `PromptLeakGuardProvider` descarta integralmente a tentativa contaminada antes da UI;
- retry unico com system minimo endurecido e mesmas mensagens nao-system;
- marcadores de leak agora sao somente headings internos altamente distintivos;
- logs registram apenas marker-id/stage, nunca prompt, usuario, resposta ou memoria;
- segundo leak falha fechado com `ModelResponseError`;
- acknowledgement: maximo 4 palavras, sem recap/pergunta/novo assunto e sem espelhamento `X tambem`;
- reflection: uma frase curta, sem pergunta por reflexo;
- revision inclui formas de entendimento incorreto/confusao, evita reassurance generico e limita a duas frases;
- topic_drop: maximo 4 palavras e proibicao explicita de propor/perguntar novo tema.

Suite atual: **96/96 testes**.
ADR: `docs/adr/0018-leak-guard-safe-retry-and-continuation-corrections.md`.

### Proximo gate atualizado

**Validar Conversational v1.4.2 no Windows/Ollama. Confirmar: (1) `salve` nao produz prompt leak nem `model_response_error`; (2) acknowledgements nao repetem/espelham; (3) revision reconsidera sem reassurance automatico; (4) topic drop realmente encerra sem puxar outro tema.**

Pragmatica v0 permanece NAO conectada. Fase 3, RAG, personas, tools e memoria nova continuam bloqueados.


## 10. Incremento atual — Conversational v1.5 / Pragmatic Input Integration

Evidencia manual v1.4.2:
- prompt interno nao vazou e o primeiro turno nao gerou `model_response_error`;
- isolamento ficcao -> factual e formato explicito continuaram funcionando;
- `show`, `blz`, risadas, topic drops e revisoes ainda foram interpretados literalmente ou receberam perguntas/recaps artificiais;
- a autoanalise nao reconheceu esses problemas;
- conclusao: continuation por regras de prompt/lista atingiu limite pratico e liberou integracao pragmatica.

Implementado no v1.5:
- `PragmaticInterpreter` conectado ao `ConversationTurnInterpreter`;
- `TurnInterpretation` passa a carregar atos pragmaticos e confianca;
- boundary informa os atos da entrada e reforca que compreensao nao implica imitacao;
- `close_topic`, `acknowledge` e `correct_previous` podem superar leitura literal;
- perguntas sociais com `?` permanecem sociais quando a funcao pragmatica indica isso;
- `vent_or_share` evita problem-solving automatico;
- `react` curto evita explicar risada/reacao;
- audit trace registra atos pragmaticos esperados;
- sem chamada adicional ao LLM.

Suite no fechamento da integracao v1.5: **111/111 testes**.
ADR: `docs/adr/0019-pragmatic-input-runtime-integration.md`.

### Gate historico substituido

A validacao manual por roteiro foi substituida pelo Behavioral E2E Harness v1; consultar a secao de gate atual abaixo.

Personas completas, RAG, banco de livros, internet, voz, tools e memoria cognitiva continuam bloqueados.


## Gate historico — Behavioral E2E Harness v1

- O usuario nao precisa mais copiar roteiros longos manualmente como caminho padrao.
- `TESTAR_COMPORTAMENTO.bat` roda cenarios variados contra o Ollama configurado usando a pipeline real.
- Os testes usam SQLite temporario isolado; nao alteram sessoes/memoria do usuario.
- Relatorios ficam apenas localmente em `test_reports/behavioral_e2e/` (`HTML`, `MD`, `JSON`).
- `CONSULTAR_ULTIMO_TESTE.bat` reabre o ultimo HTML sem executar nova suite.
- Checks automaticos medem propriedades observaveis; revisao humana do transcript continua obrigatoria para naturalidade.
- Suite offline do projeto: **115/115 testes**.
- ADR: `docs/adr/0020-behavioral-e2e-harness.md`.
- Proximo gate: executar o harness `standard` no Windows/Ollama e trazer/inspecionar o relatorio.
- NAO ativar Todd/Morgana, RAG, tools, internet, voz ou memoria cognitiva antes desse gate.


## 11. Incremento atual — Conversational v1.5.1 / Self-Aware Expression + Pragmatic Corrections

Evidencia do primeiro Behavioral E2E v1 sobre v1.5:
- `social_presence` ainda apresentou linguagem de atendimento/reassurance;
- `topic_drop` falhou ao puxar novo tema;
- `correction_previous` reconheceu `cachorro*`, mas depois preservou `gato`;
- discussao gerou alegacoes de "conexao emocional"/flexibilidade de concordar com erro;
- factualidade/proporcionalidade continuam sendo trilha paralela de modelo/grounding.

Implementado v1.5.1:
- comportamento-base self-aware: IA nao finge sentimentos/sensacoes humanas como estado interno;
- emoji opcional como marcador paralinguistico, nao emocao;
- `BehaviorResponseGuardProvider` como backstop de acknowledgement/topic-drop/correcao e retry self-aware;
- correcoes `*` viram notas autoritativas de contexto e prevalecem semanticamente sem apagar historico;
- E2E varia casos de correcao por seed e testa self-awareness;
- manual oficial criado em `docs/manual/` e `ABRIR_MANUAL.bat`;
- ADR-0021 e ADR-0022.

Suite offline: **123/123 testes**.

### Gate historico v1.5.1

Este gate foi executado e liberou o v1.5.2.


## 12. Gate historico — Conversational v1.5.2 / Response Contract & Conversational Restraint

Evidencia E2E v1.5.1:
- prompt isolation, topic-drop, formato numerico e self-awareness estrutural melhoraram;
- social/reaction ainda verbosos ou metalinguisticos;
- pedido `uma frase` podia virar varias;
- pedido em portugues podia sair inteiro em ingles;
- preferencia do usuario podia fazer o modelo prometer concordar com falsidade;
- correcao atual prevalecia, mas a resposta ainda recitava o valor substituido;
- factualidade aberta segue instavel no `llama3:latest`.

Implementado v1.5.2:
- `ResponseContractPolicy`;
- budget por modo e numero explicito de frases;
- retry unico por contrato violado;
- reaction-meta e social institutional backstops;
- invariavel `truth_over_agreement`;
- current-state apos correcao sem recitar valor antigo;
- check E2E de idioma e restraint;
- manual atualizado; ADR-0023.

Suite offline: **132/132 testes**.

### Gate historico
E2E real v1.5.2 executado; resultado reprovou o gate e liberou v1.5.3.


## 13. Incremento atual — Conversational v1.5.3 / Contract Enforcement + Context Provenance

Evidencia E2E v1.5.2:
- contratos eram detectados, mas o retry podia continuar fora de formato/budget;
- teoria ficticia nomeada pelo assistant reapareceu como explicacao factual;
- checker de estacoes aceitou resposta envolvendo distancia/mudanca de inclinacao;
- technical/discussion/self-awareness continuaram verbosos.

Implementado:
- enforcement deterministico pos-retry para forma/budget verificaveis;
- proveniencia interna `assistant_generated_unverified` e `assistant_fiction_nonfactual`;
- em factual/tecnico, texto de assistant-ficcao e omitido do request sem apagar o transcript;
- E2E detecta reutilizacao dinamica de termos inventados e falsos PASS de estacoes;
- manual e ADR-0024 atualizados.

Suite offline: **139/139 testes**.

### Gate historico v1.5.3
E2E real executado: 9 PASS / 2 WARN / 0 FAIL automaticos; revisao humana liberou v1.5.4 para corrigir naturalidade pragmatica fina.


## 14. Incremento historico — Conversational v1.5.4 / Pragmatic Semantics + Natural Expression

Evidencia v1.5.3: contratos/proveniencia ficaram estruturalmente estaveis, mas o modelo ainda verbalizou interpretacoes sociais (`risada curta`), leu acknowledgement literalmente (`show -> Nada a mostrar!`), ecoou vocativo e usou metalinguagem desnecessaria.

Implementado:
- `greet` e familias pragmaticas ampliadas;
- acknowledgement/reaction/social-share tratados por funcao, nao por resposta hardcoded;
- contratos para greeting mirror, literalizacao, simulated laughter, meta preamble, reassurance e identity drift;
- truth-over-agreement preserva contexto recente;
- E2E metamorfoco com vocabulario/assuntos/entidades variados e ordem seeded;
- Manual 14 e ADR-0025.

Suite offline: **164/164 testes**.

### Gate historico v1.5.4
E2E executado: 11 PASS / 0 WARN / 0 FAIL automaticos; revisao humana liberou v1.5.5 por falsos PASS semanticos.


## 15. Incremento atual — Conversational v1.5.5 / Semantic Coherence + Evaluator Hardening

Evidencia E2E v1.5.4:
- gate automatico 11 PASS / 0 WARN / 0 FAIL;
- revisao humana encontrou falsos PASS semanticamente invalidos apesar de forma correta;
- exemplos de classe: vocativo solto em greeting, contexto temporal inventado/parafrase obvia em social share, topic-drop curto mas quebrado e promessa de simular concordancia falsa.

Implementado v1.5.5:
- contratos semanticos adicionais no runtime;
- evaluator hardening com checks semanticamente auditaveis;
- ancoras factuais variadas no caminho creative->factual;
- nenhum LLM-as-judge e nenhuma resposta factual hardcoded no runtime;
- anti-overfitting por familias/seed permanece obrigatorio;
- Manual 15 e ADR-0026 adicionados.

Suite offline historica v1.5.5: **172/172 testes**.

### Gate historico v1.5.5

Gate executado; resultado absorvido pela v1.5.6.


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

**Gate executado:** o E2E v1.5.6 liberou o v1.5.7.

**Gate subsequente obrigatorio se a naturalidade estabilizar:** refatoracao estrutural antes de Todd/Morgana. Agentes, RAG, tools, internet, voz e memoria cognitiva continuam bloqueados.


## Gate historico — Conversational v1.5.7 / Truth Contract + Whole-Output Validation + Factual Mechanism Hardening

Evidencia E2E v1.5.6:
- 10 PASS / 0 WARN / 1 FAIL automaticos;
- truth-over-agreement ainda teve falso PASS para `nao vou corrigir/contradizer`;
- whole-output podia conter preambulo fora do formato;
- factual anchors de pombos/gelo estavam permissivos;
- trimming tecnico podia deixar lista numerada pendente.

Implementado:
- truth contract semantico cobre concordar/confirmar e tambem nao contrariar/corrigir/contradizer falsidade;
- whole-output preamble validation + fallback estrutural;
- factual mechanism hardening no E2E, sem respostas factuais hardcoded;
- technical first-step/trimming endurecidos;
- suite `mega` e `TESTAR_COMPORTAMENTO_MEGA.bat` preparados para o gate posterior;
- suite offline: **189/189 testes**.

**Gate executado:** o E2E v1.5.7 liberou o v1.5.8.

**Se standard ficar verde + revisao humana aprovar:** executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Somente depois do mega teste satisfatorio iniciar a refatoracao estrutural obrigatoria.

**Agentes continuam bloqueados:** Todd/Morgana, RAG, tools, internet, voz e memoria cognitiva nao avancam antes da refatoracao.


## Gate historico — Conversational v1.5.8 / Semantic Closure & Technical Quality

Evidencia E2E v1.5.7:
- 9 PASS / 1 WARN / 1 FAIL automaticos;
- truth contract no follow-up ficou correto, mas discussao inicial ainda foi longa;
- `Ahah!` escapou como risada textual simulada;
- registro contextual curto aceitou resposta desconexa (`Ola!`);
- primeiro diagnostico tecnico ainda podia enterrar a acao concreta;
- mecanismo factual de caranguejos continuou falhando, mantendo a trilha de qualidade factual do modelo separada do contrato conversacional.

Implementado v1.5.8:
- detector de risada textual por familia (`haha/ahah/hehe/hihi/rsrs/k/ksk`);
- registro contextual exige acknowledgement plausivel ou reflexo do valor registrado;
- truth-over-agreement usa budget maximo de 65 palavras, sem pergunta reflexa e sem meta-preambulo;
- primeiro diagnostico tecnico exige acao + mecanismo observavel na primeira frase e rejeita estruturas incompletas;
- E2E espelha esses checks sem LLM-as-judge e sem resposta factual hardcoded;
- suite offline: **198/198 testes**;
- Manual 18 e ADR-0029.

**Proximo gate unico:** `TESTAR_COMPORTAMENTO.bat` v1.5.8 + revisao humana. Se aprovado, `TESTAR_COMPORTAMENTO_MEGA.bat`; depois, refatoracao estrutural obrigatoria pre-agentes.


## Gate historico - Conversational v1.5.9 / Embodied Expression Guard + Causal Factuality + Diagnostic First Action

- v1.5.8 foi executado no E2E real; revisao humana liberou v1.5.9 por encenacao corporal/subjetiva, causalidade factual e first-action tecnica.
- `ResponseContract.prohibit_embodied_expression` e global e persona-agnostico.
- Technical first-step exige acao + evidencia observavel ja no inicio da primeira frase.
- E2E causal ampliado por familias; respostas factuais nao foram hardcodadas no runtime.
- Suite offline: **206/206 testes**.
- Manual 19 e ADR-0030.

**Gate historico v1.6.0:** executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama e revisar o transcript v1.6.0. Se aprovado, executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Depois do mega satisfatorio, refatoracao estrutural obrigatoria; agentes permanecem bloqueados ate o fim da refatoracao.


## Gate historico - Conversational v1.5.9

O standard E2E real v1.5.9 terminou em 7 PASS / 0 WARN / 4 FAIL. O resultado mostrou que reaction, causalidade factual e first-action tecnica ainda escapavam de regras acumuladas, justificando parar os patches locais e introduzir uma pipeline explicita.

## Gate historico - Conversational v1.6.0 / Response Contract Pipeline

Implementado:
- `src/campanario/llm/response_pipeline.py` com `ResponseTurnPlan`, `PipelineAttempt`, `PipelineResult` e `ResponseContractPipeline`;
- contrato compilado antes da primeira geracao;
- validacao pos-geracao permanece autoritativa;
- reparo deterministico para atos fechados e reparo pelo modelo para conteudo aberto;
- enforcement/fallback separado e sem invencao factual;
- `BehaviorResponseGuardProvider` reduzido a adapter;
- current-state correction como estagio auditavel;
- Prompt Leak Guard cobre o heading da pipeline;
- bug de `HTTP 500.` confundido com lista pendente corrigido.

Suite offline: **214/214 testes**. Manual 20. ADR-0031.

**Gate historico v1.6.0:** executar `TESTAR_COMPORTAMENTO.bat` no Windows/Ollama e revisar o transcript v1.6.0. Se standard + revisao humana forem satisfatorios, executar `TESTAR_COMPORTAMENTO_MEGA.bat`. Depois do mega satisfatorio, refatoracao estrutural obrigatoria; agentes permanecem bloqueados ate o fim da refatoracao.

## Gate atual — Conversational v1.6.1 / Typed Contracts + Model Runtime Portability

Evidencia do E2E real v1.6.0:
- pipeline melhorou isolamento de contratos, mas uma resposta criativa foi substituida por fallback de self-awareness;
- factualidade aberta e primeiro diagnostico continuam variando conforme qualidade do modelo-base;
- conclusao: fallback precisa ser tipado e o modelo precisa ser infraestrutura substituivel, nao fundamento comportamental.

Implementado v1.6.1:
- `ResponseKind` explicito em `ResponseContract`;
- reparos/fallbacks compativeis somente com o tipo do turno;
- `creative_exact`, `creative`, `factual` e `technical_first_step` nao usam fallback de self-awareness/social;
- `ModelRuntimeConfig` + factory `build_model_provider` como composition boundary;
- `CAMPANARIO_MODEL_*` como configuracao generica, com aliases Ollama legados;
- `TROCAR_MODELO.bat` para troca segura de modelo local;
- standard/mega E2E usam a mesma configuracao generica;
- suite offline: **221/221 testes**.

**Proximo gate unico:** executar `TESTAR_COMPORTAMENTO.bat` no Windows com o modelo configurado e revisar o transcript v1.6.1. Se o modelo atual continuar sendo o gargalo, e permitido trocar `CAMPANARIO_MODEL_NAME` e repetir o mesmo E2E sem reimplementar comportamento/memoria. Quando standard + revisao humana estabilizarem, executar mega E2E. Depois do mega satisfatorio: refatoracao estrutural obrigatoria; Todd/Morgana continuam bloqueados ate a refatoracao.
