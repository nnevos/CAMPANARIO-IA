# Response Contract Pipeline — v1.6.0

## O que mudou

A partir da v1.6.0, o Campanario nao depende apenas de um prompt grande para lembrar todas as regras de resposta.
Cada turno passa por uma pipeline explicita:

```text
mensagem do usuario
  -> interpretacao pragmatica
  -> contrato do turno
  -> geracao inicial
  -> validacao
  -> reparo deterministico para atos fechados OU reparo pelo modelo
  -> enforcement estrutural/fallback seguro
  -> resposta final
```

## Por que isso existe

As versoes v1.5.x mostraram que o `llama3:latest` pode ignorar uma regra mesmo quando ela esta escrita no prompt.
A pipeline separa responsabilidades e torna cada etapa testavel. Regras objetivas como formato, acknowledgement,
topic-drop, reaction, truth-over-agreement e primeiro diagnostico tecnico deixam de depender apenas da memoria do modelo.

## Contrato antes da geracao

O `ResponseContractPolicy` deriva o contrato antes da primeira chamada ao modelo. O system prompt recebe um bloco curto,
valido apenas para o turno atual, com restricoes como limite de palavras, numero de frases, ausencia de pergunta reflexa,
idioma, truth-over-agreement ou primeiro passo tecnico.

A validacao depois da geracao continua sendo a fonte de verdade. O bloco preventivo nao substitui o validator.

## Reparos

- Atos fechados e de baixo conteudo factual, como acknowledgement, topic-drop, reaction, greeting e registro contextual,
  podem receber reparo deterministico curto quando a resposta viola o contrato.
- Respostas com conteudo aberto recebem no maximo um reparo pelo modelo, guiado pelas violacoes detectadas.
- Depois do reparo, propriedades estruturais verificaveis podem sofrer enforcement deterministico.
- A pipeline nao inventa uma resposta factual melhor como fallback. Erros de conhecimento continuam aparecendo no E2E
  e devem orientar benchmark/grounding/modelo.

## Auditoria interna

A pipeline registra internamente os estagios `generate`, `current_state_repair`, `deterministic_repair`, `model_repair`,
`structural_enforcement` e `safe_fallback`. Esses nomes sao para testes/diagnostico e nao devem aparecer no dialogo.

## Seguranca de prompt

`CONTRATO DE RESPOSTA DO TURNO` e marcador interno protegido pelo Prompt Leak Guard. Se o modelo tentar ecoa-lo,
a resposta e bloqueada e o fluxo seguro existente continua valendo.

## Como testar

1. Rode `TESTAR_COMPORTAMENTO.bat`.
2. Revise o transcript mesmo se o gate automatico estiver verde.
3. Se o standard v1.6.0 for satisfatorio, rode `TESTAR_COMPORTAMENTO_MEGA.bat`.
4. Se o mega for satisfatorio, o proximo passo obrigatorio e a refatoracao estrutural pre-agentes.

## Limites atuais

A pipeline melhora obediencia, consistencia conversacional e recuperacao de violacoes. Ela nao transforma conhecimento
incorreto do modelo em conhecimento correto. Factualidade aberta continua dependendo do modelo e, futuramente, de grounding/RAG.
