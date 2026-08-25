# 13 - Proveniencia de contexto

## Por que existe

O Campanario permite criatividade sem transformar automaticamente uma invencao antiga em conhecimento factual. A partir da v1.5.3, o contexto recente possui classificacao interna de origem/autoridade.

## Regras principais

- mensagens do usuario continuam sendo evidencia do que o usuario declarou;
- texto produzido pelo assistant e `assistant_generated_unverified`: pode ajudar continuidade, mas nao vira fato so porque foi dito antes;
- resposta produzida a um pedido criativo e `assistant_fiction_nonfactual`;
- `assistant_fiction_nonfactual` nunca deve servir como fonte, explicacao ou evidencia em pergunta factual posterior;
- em turno factual/tecnico, o texto bruto de ficcao anterior pode ser omitido do contexto enviado ao modelo; o transcript salvo nao e apagado nem reescrito.

## Exemplo

1. Usuario pede uma teoria ficticia sobre um animal.
2. Campanario inventa uma teoria com nome proprio.
3. Usuario muda para `agora falando serio` e pergunta a explicacao real.
4. A teoria inventada permanece no historico visivel/auditavel, mas nao pode alimentar a resposta factual.

## O que isso nao faz

Esta camada nao prova que toda resposta factual esta correta e nao substitui grounding/RAG. Ela impede uma classe especifica de contaminacao: transformar criacao anterior do proprio modelo em evidencia do mundo real.
