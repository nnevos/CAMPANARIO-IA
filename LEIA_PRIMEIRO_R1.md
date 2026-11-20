# CAMPANÁRIO — R1: atualizar somente por cópia de arquivos

**Base exigida:** CAMPANARIO-IA P0 (V9+V9.1 integrados). Feche o Campanário antes de copiar.

## Passos no Explorador de Arquivos do Windows

1. Faça **cópia de segurança separada** das pastas `CAMPANARIO-IA` e `CAMPANARIO-DATABASE` em lugar privado; guarde também seu `.env` pessoal. **Não compartilhe backups**.
2. Baixe `CAMPANARIO_R1_ARQUIVOS_PARA_COPIAR.zip` e extraia em `Downloads\CAMPANARIO_R1_EXTRAIDO` (fora do IA).
3. Entre na pasta extraída, selecione **todos os arquivos e pastas internos**, copie e cole dentro de `C:\Users\Steam Deck\Documents\GitHub\CAMPANARIO-IA`.
4. Mescle pastas e substitua arquivos homônimos **somente se a base for P0 e não houver código personalizado**. Não apague outros arquivos nem a pasta IA.
5. Não copie nada sobre `CAMPANARIO-PYTHON`, `CAMPANARIO-DATABASE`, `.env`, `.venv`, memórias, conversas, modelos e SQLite. O ZIP de overlay **não contém esses dados**.
6. Abra pelo launcher normal e verifique o diagnóstico em **Ferramentas → Central de Cérebros**. A V9 continua desativada até que seu `.env` já esteja configurado e migração 0010 homologada; não é necessário editar `.env` só para instalar o código.

**PowerShell NÃO é necessário para atualizar arquivos.** Use comandos apenas se precisar instalar/reparar dependências, executar migrações planejadas ou testar/diagnosticar manualmente.

## Atenção ao EXE e à venv externa

- O launcher atual prefere `CAMPANARIO-IA\Campanario.exe` se existir. Um EXE compilado **não é atualizado** só por copiar código Python, e os novos workers de subprocesso requerem um Python interpretável. Se o EXE não expõe intérprete compatível, os cérebros falham fechado. Não renomeie/apague o EXE sem backup.
- O Python 3.12 esperado está em `CAMPANARIO-PYTHON\.venv\Scripts\python.exe` / `pythonw.exe`, separado. Não recrie essa venv a cada atualização. `psutil` já consta como dependência base; `pandas`/`openpyxl` dependem das opções existentes.
- Os dados persistentes ficam em `CAMPANARIO-DATABASE\dados\{desenvolvimento|producao}\campanario.db` conforme `CAMPANARIO_DATA_DIR` e `CAMPANARIO_MEMORY_ENVIRONMENT` no `.env` existente. O acervo opcional ZIM fica em `CAMPANARIO-DATABASE\zim`. A biblioteca V2 de referência ainda tem fallback legado dentro do IA até validação da cópia externa.

## Recuperação

Se algo falhar: feche o app, configure `CAMPANARIO_BRAINS_V9_ENABLED=false` no `.env` caso ainda precise isolar o recurso, reinicie. Se necessário, restaure arquivos **do IA** do backup anterior. Nunca execute `alembic downgrade 0010` por tentativa, pois apaga tabelas V9. Database e .venv não foram alterados pelo ZIP.

Leia `docs/current/R1_ISOLAMENTO_CEREBROS.md`, `docs/operations/FAILSAFE_V9_CEREBROS.md`, `docs/current/ROADMAP_V9_CEREBROS_COMPLETO.md`, `CHANGELOG_R1.md` e `docs/operations/RESULTADOS_TESTES_R1.md`. Este R1 ainda não é sandbox/homologação completa no Windows.
