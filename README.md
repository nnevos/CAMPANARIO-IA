# Campanario

Inteligencia pessoal local, persistente e modular.

Este checkpoint e a **foundation organizada pre-agentes**. Gemma 3 12B e o modelo recomendado atual, mas o sistema continua independente de familia de modelo.

## Uso rapido no Windows

Execute:

```text
CAMPANARIO.bat
```

O menu centraliza iniciar o sistema, abrir manual, trocar modelo, rodar testes, comparar modelos e consultar relatorios.

## Desenvolvimento

Leia antes de alterar:

1. `RECOVER_FIRST.md`
2. `PROJECT_STATE.md`
3. `docs/current/`

## Estrutura

```text
docs/          documentacao atual, manual, ADRs, referencias e historico
migrations/    migrations do banco
src/           codigo do Campanario
tests/         testes offline
tools/         launchers e manutencao
```

Arquitetura de runtime:

```text
API -> ChatService -> Context/Pragmatics -> Behavior -> Response Pipeline -> ModelProvider -> Adapter
```

## Modelo

Default recomendado no `.env.example`: `gemma3:12b`.

Trocar o modelo nao reinicia o projeto. Use `CAMPANARIO.bat` -> **Trocar modelo**.

## Estado dos agentes

Todd e Morgana ainda nao estao ativos. O proximo gate apos a regressao desta reorganizacao e **Agent Architecture v1**.
