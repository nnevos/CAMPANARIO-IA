# 02 - Iniciar e encerrar

## Iniciar

Execute `CAMPANARIO.bat` e escolha **Iniciar Campanario**.

O launcher verifica `uv` e Ollama, prepara `.env`, valida o modelo, executa `uv sync`, aplica `alembic upgrade head` e inicia Uvicorn em `127.0.0.1:8000`.

## Encerrar

Na janela do servidor, pressione `Ctrl+C`. Sessoes e mensagens persistidas permanecem no SQLite.

## Scripts individuais

Para automacao/diagnostico, os launchers estao em `tools/windows/`. O menu principal e o caminho recomendado para uso normal.

## Host headless PF1b (desenvolvimento)

`tools/windows/INICIAR_RUNTIME_HEADLESS.bat` inicia apenas o Runtime v2, sem Web/FastAPI. Serve para validar a separacao de hosting; nao e um Windows service. Pare com `Ctrl+C`.

Enquanto o Realtime Gateway ainda nao existe, o host headless e o host Web sao alternativas: iniciar os dois nao faz deles clientes do mesmo runtime em memoria.

Para validar PF1 automaticamente, use `tools/windows/regression/platform/TESTAR_RUNTIME_PF1.bat`.
