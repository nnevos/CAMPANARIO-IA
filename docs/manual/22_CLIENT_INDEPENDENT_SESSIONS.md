# Client-independent sessions

PF7 transforma a sessao em recurso do Campanario, nao da janela que a abriu.

## Identidades

- `session_id`: conversa/contexto duravel do Campanario;
- `episode_id`: hoje e o mesmo registro tecnico de `session_id`;
- `client_id`: instancia de software (Web, futuro Desktop/Mobile etc.);
- `device_id`: dispositivo fisico do Device Registry, quando existir;
- `agent_id`: speaker IA (`morgana` ou `todd`).

Esses ids nao sao intercambiaveis.

## Realtime

Um observador de sessao pode conectar em:

`/ws/v1/events?session_id=<id>&client_id=<id-do-cliente>`

Enquanto o WebSocket esta vivo, o runtime registra um attachment. Fechar o cliente remove somente o attachment; a sessao e o historico continuam.

## Turnos

Clientes v1 podem enviar `X-Campanario-Client-Id` no `POST /api/v1/sessions/{id}/turn`. Se tambem informarem `X-Campanario-Device-Id`, a credencial PF6 e obrigatoria.

A Presence UI atual gera um `client_id` uma vez no navegador e o reutiliza automaticamente.

## Inspecao

`GET /api/v1/sessions/{id}/clients` mostra apenas clientes atualmente anexados. Isso nao e lista de participantes sociais: Todd, Morgana e usuario continuam representados pela camada conversacional/provenance apropriada.
