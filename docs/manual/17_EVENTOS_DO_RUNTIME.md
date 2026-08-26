# 17 - Eventos do Runtime

PF2 introduz um Event Bus interno do Campanario. Ele nao e uma nova interface de usuario e nao abre portas de rede.

Cada evento possui contrato versionado, ordem (`sequence`), `runtime_id`, `session_id` quando aplicavel, correlation/causation e provenance da origem. Payloads sao validados por schema.

Eventos ja emitidos pela conversa incluem criacao de sessao, texto do usuario, selecao/intencao do agente e inicio/chunk/fim da resposta.

O runtime mantem um journal limitado em memoria para replay basico durante o mesmo processo. Reiniciar o processo cria um journal novo; sessoes/mensagens continuam persistidas normalmente no SQLite.

PF3 usara esses contratos para construir o Realtime/API Gateway. PF2 nao implementa WebSocket, Device Registry ou Tool Registry.
