> Estado atual: v1.5.3 implementada; suite offline 139/139; proximo gate unico = Behavioral E2E real no Windows/Ollama. Secoes antigas abaixo sao historico.

# FUNDACAO COMPORTAMENTAL — v1.5.3 / CONTRACT ENFORCEMENT + CONTEXT PROVENANCE

## Evidencia manual da v1

Passou parcialmente:
- factual simples, tecnico, discussao e criativo receberam posturas diferentes;
- calculos/fatos centrais do roteiro permaneceram razoavelmente corretos.

Nao passou:
- `oi`, `beleza?` e `sem assunto` ainda receberam perguntas por reflexo;
- limao continuou mais longo que o necessario;
- `sim` virou reacao generica em vez de continuidade contextual;
- `blue whale` misturou idioma;
- autoanalise nao detectou problemas concretos e se avaliou positivamente.

## Incremento v1.1

- adiciona `continuation` para confirmacoes curtas;
- torna `social` um contrato de presenca curta, sem atendimento/menu automatico;
- torna `factual_simple` mais proporcional;
- reforca que discordancia e parte normal de uma discussao quando sustentada;
- amplia trace de auditoria e adiciona sinais mecanicos observaveis;
- incorpora referencia de dialogo operacional/usabilidade em `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md`.

## Conceito de produto preservado

O usuario nao precisa conhecer modulos. A experiencia-alvo e falar com uma persona/presenca, enquanto o Campanario decide internamente quais capacidades e fontes usar. Bancos de livros/documentos sao conhecimento compartilhado do sistema, nao propriedade de um agente.

## Congelado neste gate

Nao alterar:
- Context Manager source-aware;
- migration `0002`;
- temperatura default `0.35`;
- Todd/Morgana como agentes ativos;
- RAG, internet, voz ou tools.

## Proximo gate

Validar v1.1 no Windows/Ollama com roteiro fechado fornecido na entrega. O teste deve medir principalmente social sem entrevista, continuidade de `sim`, concisao factual, discordancia natural e auditoria concreta.


## Gate historico — Conversational v1.2

Objetivo: validar conversa social sem continuidade forcada, discordancia genuina e auditoria contextual.

Criterios manuais:
- mensagens sociais/continuacoes curtas nao devem virar entrevista, menu, oferta ou eco;
- discordancia pode ser direta e respeitosa sem concordar primeiro por cortesia;
- ficcao explicitamente pedida nao pode ser marcada como erro/alucinacao na autoanalise;
- auditoria deve citar somente problemas sustentados pelo par pedido/resposta;
- factualidade e idioma continuam observados, mas nao criar regra ad hoc para cada fato do modelo.

Se o gate falhar por limite factual recorrente do modelo-base, investigar grounding/modelo antes de inflar o prompt.


## Gate historico — Conversational v1.3 / Turn Boundary & Mode Isolation

Evidencia manual da v1.2:
- modo criativo vazou para uma pergunta factual posterior;
- continuacoes como `pois entao` herdaram indevidamente a tarefa criativa;
- risada/bordao persistiu em excesso;
- auditoria nao reconheceu as violacoes de modo mais graves.

Incremento v1.3:
- boundary system imediatamente antes do USER atual;
- regra central: personalidade pode persistir, modo de tarefa nao;
- ficcao/humor autorizados expiram no fim do pedido criativo;
- `aham`, `uhum` e `pois entao` tratados como continuacao;
- auditoria registra modo esperado para cada par pedido/resposta;
- testes adversariais de transicao entre modos.

Proximo gate: validar v1.3 no Windows/Ollama antes de qualquer fase nova.


## Gate historico — Conversational v1.4 / Continuation Semantics

Evidencia manual da v1.3:
- isolamento de modo melhorou e `creative -> factual` deixou de vazar ficcao;
- continuacoes curtas repetiram respostas anteriores integralmente;
- `deixa isso pra la` ainda puxou novo assunto;
- auditoria nao detectou repeticoes importantes.

Incremento v1.4:
- mantem `continuation` como modo alto nivel e adiciona quatro semanticas internas;
- `acknowledgement`: confirmar sem recapitular;
- `reflection`: reagir sem fabricar tarefa;
- `revision`: reconsiderar sem repetir toda a tese;
- `topic_drop`: encerrar/pausar o tema sem puxar outro;
- boundary e trace de auditoria carregam a semantica;
- auditoria detecta respostas consecutivas identicas.

Proximo gate: validar v1.4 no Windows/Ollama com frases diferentes dos testes anteriores.

## Trilha seguinte — Pragmatic Input Understanding

Descoberta registrada a partir de corpus real de conversa informal: entender o que uma mensagem esta fazendo socialmente e um problema separado de escolher como a persona responde.

Fundacao v0 ja existe em `src/campanario/chat/pragmatics.py`, mas permanece fora do runtime ate fechar o gate manual v1.4.

Principios:
- compreender nao significa imitar;
- uma mensagem pode ter varios atos conversacionais;
- atos pragmaticos nao selecionam persona e nao decidem factualidade;
- corpus privado nao vira prompt, memoria pessoal ou dataset embarcado;
- testes devem usar exemplos anonimizados e variados para evitar overfitting;
- futura adaptacao ao usuario deve ficar acima da pragmatica geral e abaixo da persona de resposta.

Plano de integracao apos v1.4: comparar `PragmaticAct` com `TurnMode`/`ContinuationKind`, definir precedencia, integrar sinais minimos ao boundary e validar naturalidade antes de qualquer persona ativa.

## Privacy boundary — pragmatic evidence

- Fontes conversacionais privadas usadas para descobrir pragmatica sao insumos efemeros.
- O projeto/release nao conserva copia, nome, hash, caminho ou identificador da fonte privada.
- Permanecem apenas descobertas generalizaveis e testes anonimizados.
- ADR-0016 registra esta decisao.

## Gate emergencial v1.4.1 — Prompt Isolation

Antes de continuar avaliando naturalidade/continuacoes, validar que o modelo nao ecoa instrucoes internas. O contrato passa a exigir um unico `system` lider e output guard. Somente apos esse gate retomar Continuation Semantics e, posteriormente, integrar a fundacao pragmatica.


## 2026-08-24 — Conversational v1.4.2
- Corrigido follow-up do incidente de prompt leakage: primeiro eco agora e descartado e recebe um safe retry; segundo eco falha fechado.
- Diagnostico do guard registra somente marker-id/stage, sem conteudo privado.
- Marcadores genericos foram removidos para reduzir falso positivo.
- Continuation Semantics endurecida para acknowledgement, reflection, revision e topic_drop.
- Pragmatica v0 continua fora do runtime.
- Validacao automatizada: **96/96 testes**.
- Proximo gate: teste manual Windows/Ollama da v1.4.2.

## Gate historico — Conversational v1.5 / Pragmatic Input Integration

Evidencia manual da v1.4.2:
- seguranca de prompt/guard passou no uso real;
- isolamento de modo e formatos explicitos continuaram uteis;
- continuation por prompt/lista ainda interpretou atos sociais literalmente (`show`, risada, topic drop, acknowledgement, revisao) e puxou perguntas/recaps indevidos;
- isso confirma que compreender a funcao da entrada precisa preceder o estilo de resposta.

Incremento v1.5:
- conecta a fundacao `PragmaticInterpreter` ao `ConversationTurnInterpreter` sem chamada extra ao LLM;
- atos pragmaticos orientam o significado do turno antes da geracao;
- pragmatica pode resolver conflito entre forma literal e funcao social;
- boundary inclui atos + confianca e reforca que compreender nao significa imitar;
- audit trace registra os atos esperados para cada pedido;
- nenhuma persona, memoria nova, RAG ou tool e ativada.

Criterios manuais do gate:
- cumprimentos/reacoes nao devem virar atendimento ou explicacao do proprio ato;
- acknowledgements e topic drops devem ser entendidos semanticamente, sem recap/novo tema por reflexo;
- desabafo/compartilhamento nao deve virar checklist ou reassurance automatico sem pedido;
- correcao curta deve emendar o enunciado anterior em vez de abrir assunto novo;
- pergunta factual/tecnica deve continuar recebendo modo proprio mesmo apos humor/social;
- a persona futura continua responsavel pela voz da resposta; o interpretador nao deve copiar girias.


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

## Incremento v1.5.1 - Self-Aware Expression + Pragmatic Corrections

Objetivo: manter naturalidade sem antropomorfizacao emocional e transformar correcoes pragmaticas em estado contextual confiavel.

- Campanario sabe que e IA; compreender emocao nao equivale a declarar experiencia subjetiva.
- Humor, opiniao e informalidade continuam permitidos; emoji e marcador de tom opcional.
- `BehaviorResponseGuardProvider` e um backstop, nao uma persona: so substitui saidas quando contratos objetivos de continuation/correction sao violados e tenta retry self-aware em alegacoes emocionais explicitas.
- `X*` cria nota autoritativa no contexto e deve prevalecer sobre o valor anterior sem apagar o historico.
- E2E deve variar entidades/valores para impedir overfitting a um exemplo especifico.
- Gate: rodar Behavioral E2E no Ollama real e revisar especialmente `self_aware_expression`, `correction_previous`, `topic_drop`, `social_presence` e proporcionalidade.

## Incremento v1.5.2 - Response Contract & Conversational Restraint

Evidencia do E2E v1.5.1 mostrou que a pragmatica estava correta em varios casos, mas o modelo ainda ignorava formato, tamanho, idioma e invariantes de verdade.

v1.5.2 adiciona contrato de saida verificavel sem transformar o runtime em banco de respostas:
- numero de frases solicitado;
- budget por modo;
- reacao sem metacomentario;
- consistencia de idioma para drift evidente;
- `truth_over_agreement`;
- estado atual de correcao sem recitar o valor substituido;
- retry unico antes de backstops deterministas de baixa ambiguidade.

Factualidade aberta continua fora do contrato: nao hardcodar respostas do E2E. O erro factual deve permanecer visivel para benchmark/modelo/grounding.

### Gate historico v1.5.2

Gate executado; resultado absorvido pela v1.5.3.


## Incremento v1.5.3 - Contract Enforcement + Context Provenance

Evidencia do E2E v1.5.2: detectar violacao e pedir retry nao bastou; formato/budget podiam continuar errados e uma teoria ficticia anterior do assistant reapareceu como explicacao factual.

Implementacao:
- enforcement deterministico depois de retry para contratos estruturais;
- proveniencia `assistant_generated_unverified` / `assistant_fiction_nonfactual`;
- omissao de texto criativo anterior quando o turno atual for factual/tecnico;
- transcript persistido continua intacto;
- E2E mais rigoroso contra contaminacao dinamica e falsos PASS factuais.

Gate: executar Behavioral E2E v1.5.3 no Ollama real. Nao abrir novas fases antes da revisao.

## Incremento v1.5.4 - Pragmatic Semantics + Natural Expression

Evidencia do E2E v1.5.3: o gate automatico quase verde nao bastou para naturalidade humana. Eco de vocativo, acknowledgement literalizado, risada narrada e metalinguagem passaram em checks antigos.

Regras:
- compreender ato social nao implica verbalizar a interpretacao;
- IA nao simula risada textual como sentimento proprio;
- acknowledgement e greeting sao classes semanticas, nao respostas por palavra;
- persona futura continua dona da voz; backstops atuais sao neutros;
- testes usam familias metamorfica e variacao seeded de vocabulario, assunto, entidade e ordem;
- mesma seed = reproducao; seed diferente = superficie/ordem potencialmente diferentes;
- nunca corrigir naturalidade hardcodando a conversa do relatorio.

Gate: Behavioral E2E real v1.5.4. Nenhuma nova fase antes da revisao.


## Incremento v1.5.5 — Semantic Coherence + Evaluator Hardening

Objetivo: reduzir falsos PASS em que a forma esta correta, mas a funcao conversacional nao.

Principios:
- sem LLM-as-judge como gate principal;
- checks deterministas/auditaveis por classe semantica;
- runtime e evaluator compartilham invariantes quando objetivamente verificaveis;
- factual anchors variam no E2E e nunca viram respostas hardcoded do runtime;
- corrigir a classe de comportamento, nao a frase do relatorio.

Gate: E2E real v1.5.5 + revisao humana do transcript.


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


## Gate historico — Conversational v1.5.7 / Truth Contract + Whole-Output Validation + Factual Mechanism Hardening

Objetivo: fechar falsos PASS semanticos do v1.5.6 sem transformar o runtime em banco de respostas.

Regras:
- truth-over-agreement e invariavel mesmo quando o usuario formula a preferencia como `nao me contrarie`, `nao me corrija` ou `nao me contradiga`;
- formato exato vale para o output inteiro; preambulo nao e parte neutra da resposta;
- ancoras factuais do E2E devem validar mecanismos, nao apenas palavras correlatas;
- technical-first-step deve priorizar observacao concreta e nunca terminar em item numerado truncado;
- toda regressao nova deve variar superficie lexical/assunto e permanecer anti-overfitting.

Gate imediato: standard E2E real + revisao humana.
Gate amplo posterior: mega E2E (seis lotes full seeded) + revisao humana amostral.
Depois: refatoracao estrutural obrigatoria antes de agentes.


## v1.5.8 — Semantic Closure & Technical Quality

- Fecha variantes de risada textual simulada por classe, sem mapear uma frase para uma resposta.
- Context registration precisa produzir acknowledgement semanticamente valido ou refletir o valor registrado.
- Truth-over-agreement recebe restraint estrutural (65 palavras, sem pergunta reflexa/meta-preambulo).
- Technical first-step precisa trazer acao + mecanismo observavel na primeira frase e nao pode terminar truncado.
- E2E continua seeded/metamorfoco e sem LLM-as-judge.
- Gate: standard v1.5.8 -> revisao humana -> mega -> refatoracao pre-agentes.


## Gate atual - Conversational v1.5.9 / Embodied Expression Guard + Causal Factuality + Diagnostic First Action

Evidencia v1.5.8: revisao humana encontrou encenacao corporal da IA, mecanismos causais factuais incorretos e primeiro diagnostico tecnico sem acao direta no inicio.

Implementado:
- guard global contra stage directions/acoes corporais subjetivas da IA;
- causal guidance + E2E por familias de mecanismo, sem answer-key no runtime;
- primeira frase tecnica deve iniciar com acao investigativa e evidencia observavel;
- anti-overfitting por familias/seed/ordem permanece obrigatorio.

Proximo gate unico: `TESTAR_COMPORTAMENTO.bat` v1.5.9 + revisao humana. Se aprovado, `TESTAR_COMPORTAMENTO_MEGA.bat`; se o mega for satisfatorio, refatoracao estrutural obrigatoria antes de Todd/Morgana.


## v1.6.0 - Response Contract Pipeline

A fundacao deixa de tratar contratos apenas como guard pos-geracao. Cada turno compila um `ResponseTurnPlan` antes da chamada ao modelo. O contrato preventivo e anexado ao unico `system`; depois a saida passa por validacao, reparo e finalizacao em estagios explicitos.

Regras:
- atos fechados podem ser reparados deterministicamente;
- conteudo aberto recebe no maximo um model-repair;
- fallback nunca inventa conhecimento factual/tecnico;
- pipeline nao escolhe persona;
- respostas factuais continuam sem answer-key no runtime;
- gate: standard v1.6.0 -> mega -> refatoracao estrutural -> agentes.

## v1.6.1 — Typed Contracts + Model Runtime Portability

A politica comportamental nao pode depender da obediencia de um modelo especifico. Cada turno compila um
`ResponseKind` e somente reparos/fallbacks do mesmo tipo podem ser usados. O model runtime fica abaixo da pipeline:
`ModelProvider` -> adapter concreto. Trocar modelo e uma operacao de configuracao + revalidacao, nao um reset do projeto.

Gate: standard v1.6.1 -> mega -> refatoracao estrutural -> agentes.
