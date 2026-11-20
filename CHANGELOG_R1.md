# CHANGELOG — Campanário R1 (incremento parcial de segurança)

**Data:** 19/11/2026. **Base obrigatória:** IA P0 com V9 e V9.1 integradas. Sem migração de schema e sem alteração automática das duas pastas externas.

## Código

- `src/campanario/brains/isolation.py` **novo** — protocolo JSON, execução subprocesso Python, monitor RSS, tempo máximo e encerramento de processo/filhos.
- `src/campanario/brains/worker.py` **novo** — worker allowlist apenas `knowledge`/`analysis`; não executa shell, código arbitrário ou pacote desconhecido; limite CPU POSIX best-effort.
- `src/campanario/brains/executor.py` — usa processo encerrável para os dois cérebros reais, preserva caminho de testes para adapters próprios, adiciona `PermissionPolicy` compartilhada quando vinculada pelo runtime, nega ausência de contexto.
- `src/campanario/brains/contracts.py` — `ResourceBudget.max_memory_mb` validado.
- `src/campanario/brains/api.py` — prévia local encaminha autorização gerada no backend e orçamento configurado, nunca direitos da ficha do agente.
- `src/campanario/chat/service.py` — chat encaminha contexto de leitura e orçamento, mantém lógica de falha e resposta canônica V9.1.
- `src/campanario/composition.py` — vincula executor a `PermissionPolicy` do runtime, configura regra `library:read` somente durante sessão.
- `src/campanario/config.py` e `.env.example` — opção `CAMPANARIO_BRAINS_V9_MAX_MEMORY_MB` (padrão 1024, mínimo 128, máximo 4096); NÃO sobrescrever `.env` pessoal.

## Testes e documentos

- `tests/test_r1_brain_isolation.py` **novo** — 5 casos de política, JSON e fault injection de timeout/RSS.
- `docs/current/R1_ISOLAMENTO_CEREBROS.md` **novo** — arquitetura e atualização sem terminal.
- `docs/operations/RESULTADOS_TESTES_R1.md` **novo** — resultados e limites.
- Atualizados: `README.md`, `docs/current/ROADMAP.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md`, `docs/current/P0_TRES_PASTAS_SEM_POWERSHELL.md`.

## Limites e compatibilidade

- **Não é sandbox OS confiável contra conteúdo hostil.** Worker mantém privilégios do usuário, rede e diretórios não isolados; em Windows não há quota rígida ou Job Object. Nunca habilitar cérebro Programação até S1/S2 reais.
- O `Campanario.exe` compilado que não expõe intérprete Python pode exigir sidecar; sem ele o worker falha fechado. Sem Windows real para homologar.
- Políticas de `/api/v1/utilities` continuam distintas, a unificação completa está pendente.
- `CAMPANARIO-PYTHON/.venv` e `CAMPANARIO-DATABASE/dados/{desenvolvimento|producao}/campanario.db` mantidos externamente; Biblioteca V2 com fallback histórico. Nenhum dado pessoal importado ou alterado.
- V9 flag desligada mantém comportamento anterior; R0/R1 não declarados concluídos até testes no host real.

## Resultado

52 testes direcionados: **52 PASS, 0 FAIL**. Regressão em 3 grupos: **1.016 PASS / 31 FAIL**; os 31 nomes com falha são os mesmos já existentes no checkpoint P0. Relatório em `docs/operations/RESULTADOS_TESTES_R1.md`.
