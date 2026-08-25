# Arquitetura — Campanario

## Escopo atual

Fase 1 concluída. Fase 2 — Context Manager source-aware validado. Fundação comportamental v1 adicionada como camada transversal antes dos agentes completos.

```text
Client
  |
FastAPI / SSE
  |
ChatService
  |---------------------------|
  |                           |
Repositories          BehaviorContextManager
  |                         |
SQLite/SQLAlchemy        ContextManager
  |                      /             \
  |                 resumo persistido  janela recente
  |                      \             /
  +----------------------- ModelRequest
                              |
                         ModelProvider
                              |
                       ModelRuntimeFactory
                              |
                         ModelProvider adapter
                              |
                            HTTPX
                              |
                            Ollama
```


## Response Contract Pipeline v1.6.0

A camada de saida agora e explicitamente segmentada:

```text
ModelRequest
  -> Pragmatic/Turn interpretation
  -> ResponseContract compile (antes da geracao)
  -> ModelProvider generation
  -> Contract validation
  -> deterministic repair (atos fechados) OU model repair (conteudo aberto)
  -> structural enforcement / safe fallback
  -> resposta final
```

`BehaviorResponseGuardProvider` e somente um adapter de compatibilidade. A orquestracao esta em
`llm/response_pipeline.py`; `ResponseContractPolicy` continua responsavel por derivar/validar contratos.
A pipeline nao possui answer-key factual e nao escolhe persona.

## Typed Contracts + Model Runtime v1.6.1

`ResponseContract` inclui `ResponseKind`, compilado antes da geracao. Reparos deterministas e safe fallbacks
sao escolhidos por esse tipo; `creative_exact`, `factual` e `technical_first_step` nao podem receber fallback
de `self_aware`, `reaction` ou outro ato incompatível.

`llm/runtime.py` e a composition boundary dos modelos. `ModelRuntimeConfig` seleciona backend/modelo e cria
o adapter concreto atras de `ModelProvider`. Ollama continua implementado, mas `llama3:latest` nao e dependencia
do dominio. Trocar modelo dentro do Ollama e configuracao; adicionar outro backend exige novo adapter/factory branch.

## Direção de dependências

A lógica de aplicação depende de contratos próprios. Tipos específicos do Ollama e objetos ORM não são contratos públicos do Campanario.

## Fronteiras atuais

- `api.py`: transporte HTTP/SSE.
- `chat/`: modelos, contratos, Context Manager e serviço de conversa.
- `llm/`: abstração e adapters de modelos.
- `storage/`: infraestrutura SQLite/SQLAlchemy.
- `config.py`: configuração técnica.
- `bootstrap.py`: composição das implementações concretas.

## Regras preservadas

1. `ChatService` não importa SDK/tipos Ollama.
2. Tipos ORM não viram modelos de domínio.
3. Mensagens são histórico, não memória.
4. Ollama é primeiro adapter, não fundamento do domínio.
5. O streaming interno usa tipos do Campanario (`ModelChunk`).
6. Histórico persistido e contexto do modelo são responsabilidades diferentes.
7. `ChatService` delega seleção de contexto ao contrato `ContextManager`.
8. Modelo/backend e configuracao de infraestrutura; politica comportamental nao importa adapter concreto.
9. Recursos futuros só ganham módulo quando houver implementação real.

## Contexto da Fase 2 atual

A política atual combina janela recente determinística com um resumo incremental persistido e estruturado por fonte do trecho antigo. `USER` alimenta campos factuais/preferências/planos; conteúdo anterior do `ASSISTANT` fica separado como contexto não autoritativo. Resumos legados em texto livre são reconstruídos do histórico real. O histórico original permanece em `messages`; `context_summaries` continua sendo contexto operacional, não memória cognitiva. Tokenizer específico continua fora do escopo.


## Interpretacao conversacional v1

`BehaviorContextManager` continua sem possuir memoria nem fazer chamada extra ao modelo. Ele usa `ConversationTurnInterpreter` para produzir um hint deterministico de estilo por turno (`social`, `factual_simple`, `technical`, `discussion`, `creative`, `audit`, `general`) e combina esse hint com o contexto persistido. Em `audit`, um trace observavel das respostas recentes ajuda a revisar a conversa real. O interpretador nao decide verdade, memoria, tools ou agente. A temperatura permanece configuravel (`CAMPANARIO_OLLAMA_TEMPERATURE`, default 0.35). Todd e Morgana permanecem somente em `docs/reference/` ate gate futuro especifico.

## Interacao e capacidades futuras

A arquitetura de produto preserva a separacao `usuario -> persona/agente -> Campanario -> capacidades/fontes`. O banco de conhecimento, arquivos, ferramentas e memoria pertencem ao Campanario e devem ser compartilhaveis entre agentes. `ConversationTurnInterpreter` e apenas uma dica de comportamento do turno; nao e o futuro roteador de ferramentas/agentes. Ver `docs/reference/OPERATIONAL_DIALOGUE_AND_USABILITY.md` e ADR-0011.


## Conversational v1.3 — limite de turno

`BehaviorContextManager` combina o contexto persistente com o guidance do modo atual e insere uma mensagem `system` de limite imediatamente antes do USER mais recente. O historico continua disponivel como contexto, mas o modo de tarefa nao e herdado: criatividade, humor, formato e objetivo de um turno anterior expiram salvo quando o pedido atual os renova.

## Conversational v1.4 — Continuation Semantics

O interpretador mantem `continuation` como modo de alto nivel, mas anexa uma semantica deterministica ao turno: `acknowledgement`, `reflection`, `revision` ou `topic_drop`. Essa semantica e guidance de resposta, nao memoria nem verdade. O boundary do turno carrega a semantica e o trace de auditoria registra o contrato esperado. Nenhuma persona, ferramenta ou fonte externa e ativada por essa classificacao.

## Fundacao pragmatica (nao ativa)

`chat/pragmatics.py` define uma primeira camada de interpretacao de atos conversacionais. Ela esta
deliberadamente desconectada do `BehaviorContextManager` enquanto o gate manual do Conversational v1.4
nao for fechado. A camada interpreta entrada; nao seleciona persona, nao decide verdade, nao grava memoria
e nao prescreve estilo de resposta.

Direcao futura: `USER -> pragmatica -> modo/contexto -> persona -> resposta`.

## System prompt isolation (v1.4.1)

O boundary comportamental nao cria mais mensagens `system` intermediarias. Behavior, boundary do turno e contexto persistido sao compostos em um unico `system` lider. O provider de runtime e envolvido por `PromptLeakGuardProvider`, que impede blocos estruturais internos de chegarem ao stream visivel caso o modelo tente ecoa-los.


## Conversational v1.4.2 — guard/recovery boundary
- Request normal continua com exatamente um `system` lider.
- `PromptLeakGuardProvider` valida a resposta inteira antes de liberar texto e faz no maximo um retry com system minimo se detectar heading interno.
- O retry nao ativa capacidades novas nem Pragmatic Input Understanding.
- O gate manual v1.4.2 precisa fechar antes de integrar pragmatica ao runtime ou avancar o roadmap.


## Conversational v1.5 — Pragmatic Input Integration

Fluxo comportamental atual:

```text
User message
   |
PragmaticInterpreter (deterministico, sem LLM)
   |  acts/confidence
ConversationTurnInterpreter
   |  TurnMode + ContinuationKind + pragmatic acts
BehaviorContextManager
   |  single leading system / turn boundary
Context summary + recent history
   |
ModelProvider / PromptLeakGuardProvider
```

Regras arquiteturais:
- Pragmatica interpreta a entrada, nao a persona de saida.
- Pragmatica nao decide factualidade nem autoriza tools.
- Nao ha chamada extra ao modelo para classificar atos.
- O mesmo resultado pragmatico podera servir Todd, Morgana ou outro agente no futuro.
- Materiais privados usados para derivar padroes nao ficam no repositorio.


## Behavioral E2E Harness (fora do runtime)

O harness de validacao nao e uma capacidade conversacional nem dependencia do runtime. Ele compoe a mesma pipeline real em um banco SQLite temporario:

```text
Scenario generator (seeded)
        |
isolated ChatService
        |
Pragmatics -> Behavior -> Context -> PromptLeakGuard -> Ollama
        |
deterministic checks + transcript
        |
HTML / JSON / Markdown report
```

Ele nao usa o banco principal, nao seleciona persona, nao cria memoria cognitiva e nao usa o proprio LLM como juiz principal. Seu papel e transformar gates comportamentais em experimentos reproduziveis e consultaveis.

## Self-aware expression e response backstops (v1.5.1)

O pipeline de chat usa dois wrappers distintos sobre o provider:

```text
OllamaProvider
  -> PromptLeakGuardProvider        # seguranca de prompt / retry seguro
  -> BehaviorResponseGuardProvider  # backstop pragmatico e self-aware do chat
  -> ChatService
```

O `SummarizingContextManager` usa `PromptLeakGuardProvider`, mas nao o `BehaviorResponseGuardProvider`, evitando que regras de conversa alterem JSON/resumos internos.

Correcoes explicitas curtas (`valor*`) nao apagam o transcript. `BehaviorContextManager` deriva uma nota `CORRECOES EXPLICITAS DO USUARIO` a partir do historico persistido e a inclui no unico system context; a correcao tem prioridade sem destruir auditabilidade.

## Response contracts e conversational restraint (v1.5.2)

A pipeline passa a ter uma camada pos-geracao de contratos observaveis:

```text
PragmaticInterpreter -> TurnMode -> Context Manager -> LLM
                                             |
                                             v
                                  ResponseContractPolicy
                                             |
                              accept / single retry / backstop
```

O contrato pode limitar palavras, numero de frases, perguntas de follow-up, reaction-meta, drift evidente de idioma e a invariavel `truth_over_agreement`. Essa camada nao decide factualidade aberta e nao seleciona persona.

Correcoes explicitas mantem o transcript original para auditoria, mas o estado corrente deve refletir a correcao; o valor substituido nao e repetido em perguntas de current-state, salvo se o usuario pedir historico.

## Conversational v1.5.4 — Pragmatic Semantics + Natural Expression

A interpretacao pragmatica passa a distinguir explicitamente o ato de `greet` e usa familias semanticas para acknowledgements, reactions, topic-drops e compartilhamentos de estado. A camada nao escolhe persona nem resposta pronta; ela descreve a funcao da entrada.

Na saida, `ResponseContractPolicy` verifica erros pragmaticos observaveis: eco mecanico de vocativo, acknowledgement literalizado, narracao/simulacao textual de risada, preambulo metalinguistico, reassurance automatico e drift de identidade self-aware. `truth_over_agreement` considera o contexto recente para que follow-ups nao apaguem a premissa anterior.

O Behavioral E2E continua fora do runtime e agora varia tambem a ordem dos cenarios por seed. A regra arquitetural e: **generalizar por comportamento, nao otimizar para uma conversa fixa**.

## v1.5.5 - Semantic coherence boundary

`BehaviorResponseGuardProvider` continua sem escolher persona. A v1.5.5 adiciona verificacoes semanticamente auditaveis para atos em que forma curta, sozinha, nao garante coerencia: greeting, social share, topic drop e truth-over-agreement.

O Behavioral E2E possui checks equivalentes, mas permanece um avaliador deterministico. Ele nao chama outro LLM para decidir se a resposta e natural. Ancoras factuais do E2E sao dados de regressao variados e nao sao injetadas como respostas no runtime.

## Fechamento semantico v1.5.6

`ResponseContractPolicy` passa a reconhecer declaracoes curtas de contexto e pedidos de primeiro diagnostico tecnico. O runtime continua sem LLM-as-judge: contratos verificaveis geram retry/backstop, enquanto factualidade aberta permanece observavel no E2E. Se o gate v1.5.6 estabilizar a fundacao conversacional, o proximo passo arquitetural obrigatorio e refatorar os modulos comportamentais antes de ativar personas/agentes.

## Conversational v1.5.7 — truth/output/factual validation boundary

A camada de response contract trata `truth_over_agreement` como uma invariante semantica: pedidos para concordar, confirmar, nao contrariar, nao corrigir ou nao contradizer nao autorizam apresentar falsidade conhecida como verdade. Pedidos de formato exato sao validados sobre o output inteiro, incluindo preambulos. O E2E factual usa ancoras positivas/negativas de mecanismo apenas para avaliacao; essas respostas nao sao injetadas no runtime.

O harness possui `standard`, `full` e `mega`. `mega` agrega seis lotes full com seeds derivados e e reservado ao gate amplo pre-refactor. Depois de standard + mega satisfatorios, a arquitetura deve ser refatorada antes de ativar personas/agentes.


## Behavioral closure v1.5.8

A camada de saida continua separada da persona e aplica apenas contratos observaveis. Na v1.5.8, `ResponseContractPolicy` trata quatro fechamentos semanticos: risada textual simulada, registro contextual semanticamente valido, restraint em truth-over-agreement e primeiro diagnostico tecnico acionavel. O E2E espelha esses contratos com checks deterministas e auditaveis.

Apos standard + mega satisfatorios, esta area deve ser **refatorada por dominio antes de adicionar agentes**. A refatoracao deve separar claramente interpretacao pragmatica, contratos/guards, contexto/proveniencia, E2E/fixtures e configuracao, preservando os contratos publicos existentes.


## Behavioral output guard v1.5.9

A camada de contrato de resposta inclui **Embodied Expression Guard** (IA nao encena corpo/gesto/estado subjetivo), causalidade continua avaliada por familias no E2E e pedidos de primeiro diagnostico exigem acao + evidencia observavel na primeira frase. A camada e persona-agnostica e sera reorganizada na refatoracao pre-agentes.

## Gate historico — v1.6.0

A pipeline de resposta e a arquitetura corrente para o gate comportamental. O proximo teste e o standard E2E real; se satisfatorio, mega E2E. A refatoracao estrutural completa continua obrigatoria antes de ativar agentes/personas.


## Gate atual — v1.6.1

Executar standard E2E com o modelo configurado e revisar o transcript. Se satisfatorio, mega E2E; depois refatoracao estrutural obrigatoria antes de agentes. A troca de modelo e permitida sem reset do projeto, mas cada modelo candidato deve ser revalidado.
