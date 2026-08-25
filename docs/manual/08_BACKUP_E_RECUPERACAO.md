# 08 - Backup e recuperacao

## Atualizar release

Prefira extrair uma release nova em pasta separada. Preserve seu `.env` local e o diretorio de dados do Campanario antes de substituir uma instalacao.

## Desenvolvimento

Para retomar o projeto:
1. `RECOVER_FIRST.md`
2. `PROJECT_STATE.md`
3. `docs/current/`

O codigo e a evidencia final.

## Banco

Migrations sao aplicadas pelo launcher. Nao edite tabelas SQLite manualmente para corrigir memoria sem backup e diagnostico.

## Ferramenta de backup

Script tecnico: `tools/maintenance/backup_project.ps1`.
