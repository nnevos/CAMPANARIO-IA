# CAMPANÁRIO R1.1 — Changelog

**Base:** R1 IA, sem alterações em `CAMPANARIO-PYTHON` ou `CAMPANARIO-DATABASE`.

- `src/campanario/brains/executor.py`: orçamento total para o plano, `turn_budget_exhausted`, circuit breaker em memória por cérebro, sem retry; auditoria e política preservadas.
- `src/campanario/brains/isolation.py`: ambiente reduzido do subprocesso e falha fechada quando falta monitor RSS/psutil.
- `src/campanario/brains/network_guard.py` (novo): bloqueio de chamadas de socket Python no worker (defesa em profundidade; não é isolamento OS).
- `src/campanario/brains/worker.py`: aplicação do bloqueio durante adaptação de Conhecimento/Análise.
- `tests/test_r11_brain_guardrails.py` (novo): 6 testes de orçamento, falhas, higiene de ambiente, rede e cancelamento.
- `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/current/ROADMAP.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md`: estado real e gates R1/R2.
- `docs/current/R11_PROTECOES_EXECUTOR_CEREBROS.md` (novo): arquitetura, três pastas, segurança e instalação sem PowerShell.
- `docs/operations/RESULTADOS_TESTES_R11.md` (novo): metodologia, resultados e bloqueios.
- `docs/current/R1_ISOLAMENTO_CEREBROS.md`, `README.md` e `LEIA_PRIMEIRO_R11.md` (novo): índice, instalação e diferenciação do R1.

**Não alterado:** perfis de Morgana/Todd, memória, chat anterior, AgentRouter, ingestão, migrações SQLite, `.env`, launcher, modelos locais, venv externa e dados pessoais.

**Aceite:** 58/58 testes dirigidos; regressão disjunta 1.022 aprovados/31 falhas antigas, zero nomes novos de falhas. **R1 não está completamente homologada.**
