# ADR-0037 — Persistent participants and primary speaker

## Status
Accepted — Agent Architecture v1.2.

## Contexto
Todd e Morgana nao devem funcionar como skins mutuamente exclusivas. O conceito do Campanario exige que sejam IAs-persona presentes no mesmo espaco, capazes de ouvir o contexto compartilhado, responder ao usuario e interagir entre si.

## Decisao
- substituir `active agent` por `primary speaker`;
- Morgana e a default primary speaker;
- ambos os agentes permanecem participantes;
- chamadas diretas alteram prioridade, nao presenca;
- `ParticipationArbiter` pode permitir fala secundaria quando acrescenta algo distinto;
- convite explicito ao grupo permite ambos;
- SSE preserva fronteiras de speaker;
- `chat_sessions.primary_agent_id` persiste somente prioridade;
- `messages.agent_id` persiste provenance da fala.

## Consequencias
Maior naturalidade social e base reutilizavel para call/voz futura. Ha custo potencial de uma chamada curta adicional ao modelo em turnos abertos elegiveis; a politica conservadora evita duas respostas em todo turno.
