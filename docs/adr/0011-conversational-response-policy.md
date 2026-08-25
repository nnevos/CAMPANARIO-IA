# ADR-0011 — Politica de resposta por modo e continuidade curta

## Status
Aceito em 2026-08-24.

## Contexto
O teste manual da Interpretacao Conversacional v1 mostrou que classificar o turno ajudou a separar factual, tecnico, discussao e criativo, mas `oi`, `beleza?` e mensagens sem assunto ainda viraram atendimento. Confirmacoes como `sim` tambem perdiam o fluxo. A auditoria nao reconheceu mistura de idioma nem perguntas finais repetidas.

## Decisao
Manter o interpretador deterministico e adicionar:
- modo `continuation` para confirmacoes curtas dependentes do turno anterior;
- contratos de resposta mais estritos para `social` e `factual_simple`;
- discussao explicitamente autorizada a discordar quando houver motivo concreto;
- sinais observaveis mecanicos no modo `audit` (perguntas finais, respostas longas e marcadores simples de mistura de idioma);
- referencia de usabilidade operacional separada do runtime.

## Consequencias
Nao ha nova chamada ao LLM, migration, memoria, RAG ou ativacao de agentes. O mecanismo continua sendo hint de comportamento, nao roteador de verdade/ferramentas. Se o modelo continuar ignorando contratos simples, o proximo gate deve avaliar enforcement de geracao/modelo, nao acumular prompt indefinidamente.
