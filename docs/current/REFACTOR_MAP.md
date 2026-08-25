# Mapa da organizacao pos-refatoracao

## Concluido

- raiz operacional reduzida;
- scripts Windows em `tools/windows/`;
- menu unico `CAMPANARIO.bat`;
- documentos historicos em `docs/history/`;
- `campanario.llm` removido;
- behavior dividido por responsabilidade;
- E2E dividido em scenarios/evaluator/runner/reporting;
- provider/modelo substituivel;
- Agent Architecture v1 em `campanario.agents`;
- selecao de agente por sessao sem memoria/banco paralelo.

## Nao fazer novamente

- arquivos monoliticos misturando responsabilidades;
- documentos ativos duplicados;
- scripts temporarios na raiz;
- versionar `.venv`, `.pytest_cache`, `test_reports` ou `.env`;
- criar banco/memoria por persona;
- codificar comportamento por nome de modelo;
- permitir que persona altere verdade, contexto autoritativo ou capacidades.

## Gate atual

Validar Todd/Morgana com a suite `agents` e revisao humana. Somente depois abrir o proximo bloco funcional.
