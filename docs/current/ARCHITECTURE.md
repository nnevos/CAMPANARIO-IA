# Arquitetura atual — pre-agentes organizada

## Fluxo canonico

```text
Interface/API
  -> ChatService
  -> Context + Pragmatics
  -> Behavior Context Assembly
  -> Response Contract Pipeline
  -> ModelProvider
  -> Adapter (Ollama hoje)
  -> Modelo configurado
```

## Pacotes

```text
campanario.chat
  behavior.py      composicao do contexto comportamental
  prompts.py       prompts-base sem logica de classificacao
  turns.py         TurnMode / ContinuationKind / interpretacao de turno
  pragmatics.py    atos pragmaticos da entrada
  provenance.py    autoridade de fontes e correcoes
  audit.py         sinais observaveis para autoauditoria
  context.py       selecao/resumo de contexto
  service.py       caso de uso principal de chat

campanario.response
  types.py         tipos de contrato/violacao
  contract.py      politica e enforcement
  semantics.py     validadores semanticos
  pipeline.py      generate -> validate -> repair -> enforce/fallback
  prompt_safety.py isolamento/leak guard
  guard.py         adapter da pipeline

campanario.model
  protocol.py      interface independente de fornecedor
  runtime.py       configuracao/factory
  adapters/ollama.py

campanario.storage persistencia
campanario.e2e     cenarios/evaluator/runner/reporting/bakeoff
campanario.composition composition root unico
```

## Regra de dependencia

`chat` e `response` nao podem depender de nomes de familia como Llama, Gemma ou Qwen. O modelo e uma dependencia substituivel atras de `ModelProvider`.

## Agentes — proxima camada

Todd/Morgana deverao entrar acima da interpretacao comum e abaixo da escolha final de estilo, sem criar bancos, pipelines ou memorias paralelas. Conceitualmente:

```text
entrada -> pragmatica/contexto comum -> agente/persona ativa -> response contract -> modelo
```

Agentes continuam desativados ate a regressao final desta refatoracao.
