# PROJECT STATE — Freeze pos-v1.6.1 / Refactor pre-agentes

## Status

O ciclo de patch comportamental foi CONGELADO. O projeto entrou em refatoracao e model bakeoff antes de qualquer agente. O codigo e a evidencia final do estado real.

## Baseline preservado
- SQLite/persistencia e Context Manager existentes.
- PragmaticInterpreter + TurnMode/ContinuationKind.
- Context provenance para USER vs ASSISTANT e ficcao nao factual.
- ResponseContract/ResponseKind + ResponseContractPipeline.
- Prompt leak guard e backstops tipados.
- Behavioral E2E standard/full/mega, seeded.
- ModelRuntimeConfig e adapter Ollama.

## Refatoracao aplicada
- `campanario.model`: protocolo, runtime e adapters de modelo.
- `campanario.response`: contracts, pipeline, safety e response guard.
- `campanario.composition`: composition root compartilhado por API e E2E.
- `campanario.llm`: shims temporarios de compatibilidade.
- Novo `COMPARAR_MODELOS.bat` + `campanario.e2e.model_bakeoff`.
- Documentacao ativa resumida em `docs/current/`; historico antigo preservado em `docs/history/pre_refactor_v1_6_1/`.

## Problemas congelados para comparacao
Consultar `docs/current/BEHAVIORAL_REVIEW.md`. Em resumo: factualidade causal irregular, first-action tecnica inconsistente, naturalidade social variavel e complexidade acumulada de contratos/evaluator. O objetivo do bakeoff e distinguir limite do modelo de limite da arquitetura.

## Portabilidade
Qwen, Gemma, Llama ou outro modelo Ollama usam o mesmo `CAMPANARIO_MODEL_NAME`; trocar modelo nao altera banco, memoria, pipeline, pragmatica ou testes. Backend nao-Ollama futuro exige somente adapter + branch da factory.

## Validacao offline
- Suite pos-refactor: **225/225 testes**.
- `compileall` aprovado.
- Nenhum modulo de producao fora de `campanario.llm` importa os caminhos legacy.

## Gate atual unico
1. Suite offline precisa permanecer verde apos refatoracao.
2. Baseline standard E2E uma vez.
3. `COMPARAR_MODELOS.bat` com pelo menos 3 candidatos/seeds se o hardware permitir.
4. Escolher modelo candidato.
5. Standard + mega E2E no vencedor.
6. Refatoracao final (especialmente `response/contract.py` e `e2e/behavioral.py`) se ainda necessaria.
7. So entao desbloquear Todd/Morgana.

## Bloqueado
Todd/Morgana ativos, RAG/biblioteca, web, tools, voz, memoria cognitiva/knowledge graph.
