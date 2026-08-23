# ADR-0005 — Erros de ModelProvider pertencem ao Campanario

**Status:** Aceito.

Adapters de modelos traduzem exceções específicas da biblioteca/provedor para erros próprios do Campanario (`ModelUnavailableError`, `ModelTimeoutError`, `ModelResponseError`).

A API e o `ChatService` não devem conhecer `httpx`, SDK do Ollama ou exceções de um fornecedor específico.

Em falha de geração na Fase 1:
- a mensagem já recebida do usuário permanece persistida;
- nenhuma mensagem `assistant` incompleta é persistida;
- a falha é comunicada pelo stream e registrada operacionalmente;
- uma entidade de `turn`/`generation_attempt` só será criada futuramente se houver necessidade real.
