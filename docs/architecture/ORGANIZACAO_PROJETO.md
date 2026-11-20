# Organizacao do projeto — Fase 4

## Arquivos ativos

- `CAMPANARIO.bat`: menu principal; depende de `tools/windows/*.bat`.
- `src/campanario/`: implementacao; pastas `chat`, `agents`, `storage`, `runtime`, `web`, `model` etc. permanecem com os nomes atuais para nao quebrar imports.
- `tools/windows/`: scripts usados pelo menu, inclusive diagnostico e voz legada.
- `tools/maintenance/ATUALIZAR_CONTINUIDADE.py`: gera o handoff.
- `migrations/`, `alembic.ini`, `pyproject.toml`, `uv.lock`, `.env.example`: infraestrutura de instalacao.

## Documentacao

- `docs/handoff`: continuidade entre chats.
- `docs/operations`: instalacao e diagnosticos.
- `docs/architecture`: decisoes e plano de evolucao.
- `docs/reference/personas`: definicoes originais de Todd e Morgana.
- `docs/manual`: guias funcionais.
- `docs/history/checkpoints`: estado legado, checkpoints e resumos antigos.
- `docs/history/reports`: relatorios historicos, nao saidas ativas.

## Preservados por compatibilidade

- `voice/`: executaveis e bibliotecas Windows de voz. Nao remover sem revisar `src/campanario/runtime/host_voice.py` e scripts Windows.
- `models/`: local esperado para modelos de voz.
- `docs/current/`, `docs/adr/`, `docs/concept/`: referencias tecnicas e historicas, ainda nao deduplicadas.

## Nao confundir

- `data/development` e `data/production` sao diretorios preparados, nao uma migracao automatica de banco.
- SQLite de desenvolvimento/producao e selecionado pelo codigo existente; revisar caminhos antes do Ponto Zero.
- A reestruturacao nao implementa memoria evolutiva nem pesquisa na internet.

## Politica de limpeza

1. Nao apagar codigo ou bibliotecas apenas porque nao sao usados no fluxo principal.
2. Primeiro verificar referencias de imports, launcher e testes.
3. Guardar arquivos de auditoria legados em `docs/history`.
4. Nao incluir `.env`, SQLite, caches, credenciais, `.git` ou pesos no ZIP.
