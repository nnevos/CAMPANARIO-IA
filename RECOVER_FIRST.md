# LEIA PRIMEIRO — RECUPERAÇÃO TOTAL DO CAMPANARIO

Este arquivo existe para retomar o projeto em uma conversa nova sem depender do histórico anterior.

## Instrução para uma nova IA/conversa

Envie o ZIP completo e diga exatamente:

> **Leia `RECOVER_FIRST.md` e `PROJECT_STATE.md` antes de qualquer alteração. Considere o código como evidência final do estado real. Continue exclusivamente do próximo gate registrado.**

## Ordem obrigatória de leitura

1. `RECOVER_FIRST.md`
2. `PROJECT_STATE.md`
3. `docs/ARCHITECTURE.md`
4. `docs/ROADMAP.md`
5. `docs/PHASE2_CONTEXT_MANAGER_PLAN.md`
6. `docs/adr/`
7. `CHANGELOG.md`
8. `pyproject.toml`
9. árvore real em `src/` e `tests/`
10. `docs/REFERENCE_MANIFEST.md`

## Estado congelado neste checkpoint

- **Fase 1 concluída.**
- Código da Fase 1 passou **8/8 testes** neste pacote.
- Testes manuais no Windows confirmaram chat real, SSE, SQLite, reinício, erro de Ollama e recuperação do provider.
- Próximo trabalho: **Fase 2 — Context Manager**, primeiro incremento apenas.
- NÃO iniciar memória cognitiva, RAG, Morgana/Todd, voz, internet, tools/agentes ou knowledge graph agora.

## Regra contra perda de contexto

Toda entrega futura deve atualizar, no mínimo:

- `PROJECT_STATE.md`
- `CHANGELOG.md`
- `docs/RECOVERY.md`
- plano da fase corrente quando houver mudança de escopo

Se uma decisão arquitetural mudar, criar ou substituir um ADR. Não apagar silenciosamente a decisão anterior.

## Atenção: banco SQLite fica fora do repositório

Por configuração atual, os dados de execução ficam no diretório de dados do usuário do Windows, normalmente:

`%LOCALAPPDATA%\Campanario\campanario.db`

Portanto **o ZIP do código sozinho não contém necessariamente o histórico real das sessões do PC**.
Use `scripts/backup_project.ps1` para gerar um backup local incluindo o diretório de dados.

Não versionar `.env` em Git. Se futuramente houver chaves/API secrets, mantenha-as fora dos backups compartilhados.
