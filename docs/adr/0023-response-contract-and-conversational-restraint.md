# ADR-0023 — Response Contract & Conversational Restraint

## Status
Aceito em 2026-08-24 para Conversational v1.5.2.

## Contexto
O E2E real da v1.5.1 mostrou que a interpretacao pragmatica melhorou topic-drop e correcoes, mas o modelo ainda podia:
- ignorar pedidos como "uma frase";
- narrar a reacao do usuario (`voce esta rindo`);
- produzir respostas muito longas para turnos simples;
- responder em ingles a um pedido em portugues;
- prometer concordar com afirmacoes que considera falsas para satisfazer preferencia do usuario;
- mencionar o valor antigo ao responder pelo estado atual apos uma correcao explicita.

Aumentar apenas o system prompt estava produzindo ganhos marginais e comportamento pouco previsivel.

## Decisao
Adicionar uma camada `ResponseContractPolicy` entre a geracao e a entrega da resposta.

O contrato e derivado do pedido atual + `TurnInterpretation` e cobre apenas propriedades observaveis que podem ser verificadas sem julgar subjetivamente o conteudo:
- budget de palavras por modo;
- numero explicito de frases quando solicitado;
- ausencia de pergunta em reacoes/continuacoes que nao pedem follow-up;
- proibicao de explicar a risada/reacao ao usuario;
- consistencia de idioma para drift evidente;
- invariavel `truth_over_agreement`;
- estado corrente apos correcao explicita.

Quando o contrato falha, ocorre no maximo um retry especifico com os requisitos violados. Backstops deterministas permanecem apenas em casos de baixa ambiguidade (acknowledgement, topic-drop, reacao meta, truth-over-agreement e estado corrigido).

## Nao decisoes
- O contrato nao verifica factualidade aberta por banco de respostas prontas.
- Nao hardcodar respostas para perguntas do E2E (estacoes do ano, gelo, caranguejos etc.).
- Nao selecionar persona.
- Nao criar memoria nova.
- Nao ativar RAG/internet/tools.

## Consequencias
- Menor dependencia de obediencia perfeita ao prompt pelo modelo-base.
- Formato e proporcionalidade tornam-se testaveis e reproduziveis.
- O E2E pode falhar por factualidade mesmo quando contratos de saida passam; isso e intencional e aponta para a futura trilha de modelo/grounding.
