# Changelog P0 — separacao de 3 pastas e failsafe operacional

**Data:** 19/11/2026. **Base:** V9 + V9.1 integrada com patch documental R0–R10.

- Criado `brains/environment.py`: inspecao somente leitura de IA, Python/.venv, Database, variaveis de dados e header SQLite; sem migrar, apagar ou criar pastas.
- Criada API local `GET /api/v1/brains/environment`, inclusive com a V9 desabilitada, e painel real na Central de Cerebros (Dark Matter mantido).
- Fortalecido `BrainExecutor`: bloqueio de escopos de permissao nao concedidos e rejeicao de resultado com ID/trace incorreto ou `completed` sem operacao. Nao substitui `PermissionPolicy` nem sandbox real.
- Detectado SQLite legado da Biblioteca Conversacional V2 no IA: a consulta agora prefere `Database/dados/reference` quando presente e mantém fallback de leitura original. Sem cópia/migração automática.
- Criado teste `tests/test_p0_three_folders.py` para limites de pastas, read-only, invalidos, traces e controle de acesso loopback.
- Atualizados `ROADMAP.md`, `ROADMAP_V9_CEREBROS_COMPLETO.md`, `FAILSAFE_V9_CEREBROS.md`, README e manuais historicos com os contratos da venv externa, Database isolado, .env e atualizacao por copia via Explorador sem PowerShell.
- Criado manual unificado `P0_TRES_PASTAS_SEM_POWERSHELL.md`, runbook e relatorio de execucao.
- Corrigido texto de estado gerado por `tools/exportar_campanario.py` para nao alegar que o novo P0 foi homologado em Windows sem acesso ao host.
- Nenhuma migration aplicada, nenhum dado real migrado, nenhuma personalidade alterada e nenhuma mudanca feita em `CAMPANARIO-PYTHON` ou `CAMPANARIO-DATABASE`.

## Estado

Este checkpoint **nao fecha o gate P0**, porque os repositorios Python/Database reais e o Windows nao foram fornecidos; falta sandbox com kill real, politica de autorizacao unificada, restore de backup de teste, Ollama/voz e homologacao mobile. Ver `docs/operations/P0_RELATORIO_EXECUCAO.md`.

## Testes executados

1.011 aprovados / 31 falhas já existentes na base V9+V9.1 (mesmos nomes), 18 warnings; 53 testes direcionados aprovados. Consulte `docs/operations/RESULTADOS_TESTES_P0.md` para limites, comando e lista completa de falhas.
