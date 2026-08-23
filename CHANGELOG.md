# Changelog — Campanario

## 2026-08-23 — Incremento 2 / Fase 1 parcial

Adicionado:
- ambiente Alembic e migration `0001` para `chat_sessions` e `messages`;
- repositories SQLAlchemy concretos;
- `ChatService` para criação de sessão, histórico e turno de chat;
- `OllamaProvider` via HTTPX e `/api/chat` com streaming NDJSON;
- endpoints `/api/sessions`, `/api/sessions/{id}/messages` e `/api/sessions/{id}/chat/stream`;
- streaming HTTP em SSE;
- `FakeModelProvider` permanece como caminho de testes sem Ollama/GPU;
- testes unitários/API/repositories;
- documento `docs/RECOVERY.md`.

Validação realizada no ambiente de desenvolvimento:
- 5 testes passaram;
- migration Alembic `0001` aplicada com sucesso em SQLite temporário;
- `compileall` passou;
- Ruff não pôde ser executado neste ambiente porque o binário não está instalado globalmente; permanece dependência de desenvolvimento no `pyproject.toml`.

Limitações conscientes:
- não houve teste real contra uma instalação Ollama nesta entrega;
- não há UI;
- não há Context Manager inteligente; todo histórico concluído da sessão é enviado ao modelo;
- cancelamento/stream interrompido ainda não possui estado persistente específico.

## 2026-08-23 — Hardening de validação de entrada

- Teste real mostrou que `{"message":"   "}` era aceito.
- `ChatRequest` passou a normalizar com `strip()` e rejeitar whitespace-only.
- Adicionado teste automatizado para garantir 422 e ausência de persistência.
- Mensagem vazia `""` já era rejeitada por `min_length=1`.
- Próximo gate: validar a correção no Windows e definir política de falha/interrupção de turno.

## 2026-08-23 — Hardening final da Fase 1

- Exceções HTTPX deixaram de vazar para a camada API.
- Criados erros próprios de `ModelProvider`: unavailable, timeout e response error.
- OllamaProvider traduz falhas de transporte para contratos do Campanario.
- Política mínima congelada: mensagem do usuário permanece; resposta assistant incompleta não é persistida.
- Timeout do Ollama permanece configurável por `CAMPANARIO_OLLAMA_TIMEOUT_SECONDS`.
- Adicionados testes para falha do modelo e ausência de assistant persistido.

## 2026-08-23 — Fase 1 encerrada e recovery consolidado

- Validação final com provider indisponível concluída.
- Mensagem do usuário preservada sem resposta assistant falsa.
- Provider religado e resposta normal `Campanario OK.` validada por SSE.
- Fase 1 declarada concluída.
- Próxima fase definida: Context Manager.
- Adicionado `RECOVER_FIRST.md`.
- Adicionado manifesto com hashes das referências externas.
- Adicionada política/script de backup local incluindo app-data SQLite.
