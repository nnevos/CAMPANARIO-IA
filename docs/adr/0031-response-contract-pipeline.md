# ADR-0031 — Response Contract Pipeline

## Status
Aceito — 2026-08-24

## Contexto

A serie v1.5.x acumulou regras de prompt, validators, retries e backstops dentro de `BehaviorResponseGuardProvider`.
O E2E real mostrou que o modelo continuava escapando de regras explicitas e que a classe de guard estava concentrando
planejamento, geracao, validacao, reparo e fallback num unico fluxo dificil de testar isoladamente.

## Decisao

Introduzir `ResponseContractPipeline` com estagios explicitos:

1. compilar interpretacao + contrato antes da geracao;
2. anexar contrato preventivo ao unico `system` lider;
3. gerar uma resposta;
4. validar objetivamente;
5. aplicar reparo deterministico apenas para atos conversacionais fechados;
6. para conteudo aberto, permitir um reparo pelo modelo;
7. aplicar enforcement estrutural verificavel;
8. usar fallback seguro sem inventar fatos.

`BehaviorResponseGuardProvider` permanece como adapter de compatibilidade e delega para a pipeline.

## Consequencias

- Responsabilidades ficam explicitamente separadas e testaveis.
- O modelo recebe o contrato antes da primeira resposta, reduzindo retries evitaveis.
- A pipeline pode ser instrumentada sem expor regras internas ao usuario.
- Factualidade aberta nao ganha answer-key no runtime; erros permanecem visiveis no E2E.
- O novo marcador interno do contrato entra na protecao contra prompt leakage.

## Gate

Standard E2E v1.6.0 + revisao humana. Se satisfatorio, mega E2E. Depois, refatoracao estrutural obrigatoria antes de Todd/Morgana.
