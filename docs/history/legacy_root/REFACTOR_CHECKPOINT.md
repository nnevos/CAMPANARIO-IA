# Checkpoint — Freeze v1.6.1 / Refatoracao pre-agentes R1

Este pacote preserva o comportamento v1.6.1 como baseline, mas reorganiza a estrutura para permitir comparar/trocar modelos antes de Todd/Morgana.

## Mudancas estruturais (sem tuning comportamental intencional)
- `model/` separado de `response/`;
- composition root unico para API e E2E;
- E2E dividido em scenarios/evaluator/runner/reporting;
- response contract dividido em types/policy/semantics;
- `llm/` convertido em compatibility shims;
- docs operacionais atuais em `docs/current/`;
- historico pre-refactor preservado em `docs/history/pre_refactor_v1_6_1/`;
- `COMPARAR_MODELOS.bat` adicionado.

## Baseline de validacao
225/225 testes offline passam apos a refatoracao.

## Proximo gate
Comparar modelos sobre o mesmo Campanario, sem alterar prompts/regras entre candidatos. Depois standard + mega no vencedor e somente entao agentes.
