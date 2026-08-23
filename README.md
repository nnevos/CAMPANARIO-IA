# Campanario

Sistema pessoal de IA local, modular e extensível.

## Antes de alterar qualquer coisa
Leia **`PROJECT_STATE.md`**. Ele é o ponto de retomada do projeto caso o histórico de conversa seja perdido.

## Estado atual
Fase 0 concluída. Fase 1 parcialmente implementada: persistência, API de sessões, ChatService, adapter Ollama e streaming SSE já existem. Falta validar o circuito contra Ollama real no hardware alvo e fechar os detalhes restantes da Fase 1.

## Requisitos planejados para o ambiente alvo
- Windows
- Python 3.12
- `uv`
- Ollama para o teste real do LLM

## Preparação

```bash
copy .env.example .env
uv sync
uv run alembic upgrade head
```

Configure em `.env` um modelo que já exista no Ollama:

```text
CAMPANARIO_OLLAMA_MODEL=nome-do-modelo
```

## Executar

```bash
uv run uvicorn campanario.main:app --reload
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

## API atual
- `POST /api/sessions`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}/messages`
- `POST /api/sessions/{session_id}/chat/stream`

O último endpoint usa Server-Sent Events (SSE).

## Continuidade/backup lógico
Leia `docs/RECOVERY.md`. Nunca confie apenas na conversa como memória de desenvolvimento.
