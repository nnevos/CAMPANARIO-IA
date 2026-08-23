# Arquitetura — Campanario

## Escopo atual
Fases 0 e preparação da Fase 1.

```text
Client
  |
FastAPI
  |
ChatService (próximo incremento)
  |
ModelProvider ---------------- OllamaProvider
  |
Repositories ---------------- SQLite/SQLAlchemy
```

## Direção de dependências
A lógica de aplicação depende de contratos próprios, nunca de tipos do Ollama ou objetos ORM como contrato público.

## Fronteiras
- `api`: transporte HTTP.
- `chat`: modelos e contratos do domínio de conversa.
- `llm`: abstração e adapters de modelos.
- `storage`: infraestrutura SQLite/SQLAlchemy.
- `config`: configuração técnica.
- `shared`: somente utilidades genuinamente compartilhadas; não virar pasta de despejo.

## Regras
1. `ChatService` não importa SDK/tipos Ollama.
2. Tipos ORM não devem virar o modelo público do domínio.
3. Mensagens são histórico, não memória.
4. Recursos futuros só ganham módulo quando houver implementação real.
