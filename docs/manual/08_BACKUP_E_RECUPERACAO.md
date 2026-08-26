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


## Reinstalacao completa / Disaster Recovery (planejado)

O roadmap registra um futuro **Recovery/Reinstall Kit** para casos de formatacao ou falha grave. A meta sera permitir reconstruir Campanario, dependencias/runtime, configuracao e dados a partir de backup/manifesto verificado, potencialmente em midia offline/USB. Segredos nao devem ser embutidos no kit por padrao. Isso ainda nao esta implementado e nao deve ser confundido com o backup atual.
