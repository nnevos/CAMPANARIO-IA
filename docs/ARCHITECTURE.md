# Arquitetura — Campanario

## Escopo atual
Fase 0 concluída; Fase 1 em implementação.

```text
Client
  |
FastAPI / SSE
  |
ChatService
  |---------------------------|
  |                           |
Repositories              ModelProvider
  |                           |
SQLite/SQLAlchemy          OllamaProvider
                              |
                           HTTPX
                              |
                           Ollama
```

## Direção de dependências
A lógica de aplicação depende de contratos próprios. Tipos específicos do Ollama e objetos ORM não são contratos públicos do Campanario.

## Fronteiras atuais
- `api.py`: transporte HTTP/SSE.
- `chat/`: modelos, contratos e serviço de conversa.
- `llm/`: abstração e adapters de modelos.
- `storage/`: infraestrutura SQLite/SQLAlchemy.
- `config.py`: configuração técnica.
- `bootstrap.py`: composição das implementações concretas.

## Regras preservadas
1. `ChatService` não importa SDK/tipos Ollama.
2. Tipos ORM não viram modelos de domínio.
3. Mensagens são histórico, não memória.
4. Ollama é primeiro adapter, não fundamento do domínio.
5. O streaming interno usa tipos do Campanario (`ModelChunk`).
6. Recursos futuros só ganham módulo quando houver implementação real.

## Contexto da Fase 1
Nesta fase, o histórico completo de mensagens concluídas é usado como contexto. Isso é propositalmente simples. Seleção, janela de tokens e sumarização pertencem à Fase 2 — Context Manager.
