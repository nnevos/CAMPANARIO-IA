# CAMPANÁRIO R2 — Changelog incremental

- `brains/router.py`: `BrainStep`/`BrainPlan` tipados, dependências acíclicas, justificativa, escopos e roteamento explícito documento + dados.
- `brains/contracts.py`, `isolation.py`, `worker.py`, `executor.py`: rastreio de IDs de evidência entre etapas concluídas, orçamento de turno da R1.1 mantido, validações contra resultado incompatível.
- `brains/collaboration.py`: novo consolidado factual imutável a partir de operações realmente executadas, com faltas e limitações preservadas. Não faz comparação semântica.
- `chat/document_intent.py`: reconhecimento de imperativos explícitos como `Compare o documento ...` e delimitação de nome de arquivo antes de `com a planilha`.
- `chat/service.py`: execução e consolidação multi-etapas no mesmo turno, repassadas à ficha factual neutra/CanonicalAnswer, sem alterar `AgentRouter`.
- `brains/api.py`: prévia de plano completo e consolidação observável, sem habilitar cérebros indisponíveis.
- `tests/test_r2_collaboration.py`: testes de roteamento, dependências, fonte real, cálculo, erro parcial, permissão negada e chat/fallback.
- ROADMAP/FAILSAFE/README atualizados, inclusive explicação das três pastas, `.venv` externa, Database e procedimento **sem PowerShell**.

**Sem alterações:** migration 0010, `.env` do usuário, arquivos pessoais, venv externa, SQLite do Database, modelos Ollama, personalidades e vozes. Não é homologação de R1/R2 completas.
