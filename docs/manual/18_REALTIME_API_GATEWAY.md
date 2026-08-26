# 18 - Realtime / API Gateway

## O que mudou

A interface Web agora é um cliente do Runtime v2. Ela usa a API versionada `/api/v1` para operações e o WebSocket `/ws/v1/events` para acompanhar em tempo real o mesmo Event Bus interno do Campanario.

## Endereços locais

Enquanto PF6 de segurança/rede não existir, mantenha o Campanario em `127.0.0.1`. Não abra a porta para LAN ou internet manualmente.

Principais superfícies:

- `/api/v1/runtime`
- `/api/v1/agents`
- `/api/v1/sessions`
- `/api/v1/sessions/{id}/messages`
- `/api/v1/sessions/{id}/turn`
- `/ws/v1/events?session_id=<id>&after_sequence=<n>`

## Reconexão

`after_sequence` permite pedir os eventos que ainda estiverem no journal process-local depois de uma desconexão. Isso não cria uma nova sessão e não é replay durável entre reinícios do processo.

## Compatibilidade

Os endpoints `/api/...` e o SSE legado continuam presentes nesta fase para permitir migração incremental e diagnóstico.
