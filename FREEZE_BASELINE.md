# CAMPANARIO — FREEZE BASELINE

**Data:** 2026-08-26  
**Estado congelado:** base geral do Campanario imediatamente apos ADR 0074, sem a frente experimental Ren'Py.

## Decisao

O desenvolvimento ativo do Campanario fica pausado neste checkpoint. A frente Ren'Py/GDD/Fabrica foi removida do codigo, UI, rotas, testes, launchers e documentacao ativa porque nao faz parte do nucleo que se deseja preservar.

Este pacote existe como **base tecnica preservada**, nao como declaracao de produto final pronto.

## Base preservada

- runtime/model provider substituivel;
- Conversation Runtime e RuntimeHost;
- Event Bus e gateway realtime;
- identidade de clients/devices e capability registry;
- trust/permissoes e sessoes client-independent;
- Todd e Morgana, Personality Core e Social Protocol;
- memoria/Experience-Learning ja existente no checkpoint;
- UI de presenca/conversa;
- contratos e infraestrutura de voz/call desenvolvidos ate F5c.11;
- Turn-local Personality Activation (ADR 0073);
- Human Conversation Baseline (ADR 0074).

## Gate congelado

- **F5 Realtime Presence / Call / Multi-client: OPEN / pausado.**
- **F6: BLOCKED.**
- Nenhuma nova fase deve ser inferida como aprovada a partir deste freeze.

## Ultima evidencia antes da frente removida

ADR 0074 registrou Human Conversation Baseline com 61/61 testes focados, 442/442 regressao completa e compileall PASS. Naturalidade continua dependente de revisao humana; o baseline nao fecha F5.

## Retomada futura

Se o projeto voltar a ser desenvolvido, comece por `RECOVER_FIRST.md`, `PROJECT_STATE.md`, `SAFEPOINT.md` e ADR 0074. Reavalie primeiro a proposta de valor e a experiencia desejada antes de adicionar novas features.
