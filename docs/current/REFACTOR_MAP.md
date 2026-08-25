# Mapa da organizacao pre-agentes

## Concluido nesta refatoracao

- raiz operacional reduzida;
- scripts Windows movidos para `tools/windows/`;
- menu unico `CAMPANARIO.bat` na raiz;
- documentos de evolucao antigos movidos para `docs/history/`;
- manual ativo reduzido a guias operacionais atuais;
- `campanario.llm` removido; codigo/testes usam `model` e `response` canonicos;
- `chat/behavior.py` dividido em modulos por responsabilidade;
- E2E ja estava dividido em scenarios/evaluator/runner/reporting;
- provider/modelo continua substituivel.

## Nao fazer novamente

- criar arquivos de 500-1000 linhas misturando responsabilidades;
- duplicar documento ativo na raiz e em `docs/`;
- colocar scripts temporarios na raiz;
- versionar `.venv`, `.pytest_cache`, `test_reports` ou `.env`;
- criar um banco/memoria por persona;
- codificar comportamento por nome de modelo.

## Proximo gate

1. suite offline da estrutura organizada;
2. standard curto com `gemma3:12b` para garantir que mover codigo nao mudou comportamento;
3. mega apenas se houver duvida/regressao relevante;
4. congelar a foundation organizada;
5. iniciar arquitetura de agentes Todd/Morgana.
