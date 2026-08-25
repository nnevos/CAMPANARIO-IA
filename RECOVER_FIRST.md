# LEIA PRIMEIRO — CAMPANARIO FOUNDATION ORGANIZADA

> Leia este arquivo e `PROJECT_STATE.md` antes de qualquer alteracao. Considere o codigo como evidencia final e continue somente do gate atual.

## Leia agora

1. `PROJECT_STATE.md`
2. `docs/current/ARCHITECTURE.md`
3. `docs/current/BEHAVIORAL_REVIEW.md`
4. `docs/current/MODEL_STRATEGY.md`
5. `docs/current/REFACTOR_MAP.md`
6. `docs/current/AGENT_READINESS.md`
7. `docs/current/ROADMAP.md`
8. `docs/concept/SYSTEM_CONCEPT.md`

## Estado

- Foundation conversacional organizada e congelada para regressao.
- `gemma3:12b` recomendado atualmente, sem acoplamento de arquitetura.
- Todd/Morgana ainda BLOQUEADOS ate o gate abaixo.
- Historico anterior preservado em `docs/history/`.

## Gate atual unico

**Validar que a reorganizacao nao mudou comportamento.**

1. suite offline verde;
2. standard E2E com Gemma 3 12B;
3. se nao houver regressao estrutural, congelar checkpoint;
4. proximo gate: Agent Architecture v1.

## Regras permanentes

- nao hardcodar respostas para benchmark;
- entender o usuario nao significa imitar o usuario;
- persona nao controla verdade/factualidade;
- modelos sao motores substituiveis;
- agentes nao duplicam memoria, contexto ou tools;
- fontes privadas nao entram no repositorio;
- toda funcao de usuario atualiza `docs/manual/`;
- mudanca arquitetural relevante exige ADR.
