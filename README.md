# Campanario

Sistema pessoal de IA local, modular e extensível.

## Estado atual
Fase 0 — Fundação arquitetural.

Leia **PROJECT_STATE.md antes de qualquer alteração**. Esse arquivo é o ponto de retomada do projeto caso o histórico de conversa seja perdido.

## Início rápido (futuro)
1. Instalar Python 3.12.
2. Instalar `uv`.
3. Copiar `.env.example` para `.env`.
4. `uv sync`
5. `uv run uvicorn campanario.main:app --reload`

> Nesta entrega inicial o projeto contém apenas a fundação mínima e um health check. Chat/Ollama serão o próximo incremento.
