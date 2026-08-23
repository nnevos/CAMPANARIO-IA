# RECOVERY — Protocolo permanente do Campanario

## Se o chat original desaparecer

Envie o ZIP completo do projeto e diga:

> Leia `RECOVER_FIRST.md` e `PROJECT_STATE.md` primeiro. Compare com o código e continue do próximo gate, sem pular fases.

## O que uma nova IA deve fazer

1. Identificar fase atual no `PROJECT_STATE.md`.
2. Inspecionar árvore real do projeto.
3. Ler ADRs.
4. Rodar testes se possível.
5. Verificar divergências entre documentação e código.
6. Não reconstruir decisões já congeladas sem motivo novo.
7. Pedir referências externas somente se a tarefa realmente depender delas.
8. Atualizar a documentação de continuidade ao final.

## Backup de dados locais

O banco de execução não vive necessariamente no repositório. No Windows, normalmente fica em:

`%LOCALAPPDATA%\Campanario\campanario.db`

Use `scripts/backup_project.ps1` para gerar um pacote local com código + dados.

## Arquivos críticos de continuidade

- `RECOVER_FIRST.md`
- `PROJECT_STATE.md`
- `CHANGELOG.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/PHASE2_CONTEXT_MANAGER_PLAN.md`
- `docs/adr/`
- `docs/REFERENCE_MANIFEST.md`
