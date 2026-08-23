# CHANGELOG — Campanario

## 2026-08-23 — Persistência pós-reinício validada

- Servidor Uvicorn encerrado e reiniciado.
- Sessão existente continuou acessível.
- Mensagens anteriores foram recuperadas após reinício.
- Persistência SQLite real confirmada.
- Circuito principal da Fase 1 considerado funcional.
- Próximo passo: hardening mínimo de erros e interrupções antes de iniciar Context Manager.

## 2026-08-23 — Primeiro circuito real de chat validado

- Python 3.12.10 validado no Windows.
- Ollama 0.32.15 validado.
- `llama3:latest` usado como modelo provisório.
- `uv run pytest`: 5/5 testes passaram.
- `/health` validado.
- sessão criada via API.
- streaming SSE Campanario -> Ollama validado token a token.
- pergunta e resposta persistidas no SQLite.
- histórico recuperado pela API.
