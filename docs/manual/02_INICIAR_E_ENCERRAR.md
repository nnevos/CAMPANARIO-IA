# 02 - Iniciar e encerrar

## Iniciar

Execute `CAMPANARIO.bat` e escolha **Iniciar Campanario**.

O launcher verifica `uv` e Ollama, prepara `.env`, valida o modelo, executa `uv sync`, aplica `alembic upgrade head` e inicia Uvicorn em `127.0.0.1:8000`.

## Encerrar

Na janela do servidor, pressione `Ctrl+C`. Sessoes e mensagens persistidas permanecem no SQLite.

## Scripts individuais

Para automacao/diagnostico, os launchers estao em `tools/windows/`. O menu principal e o caminho recomendado para uso normal.
