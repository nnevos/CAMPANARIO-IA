# ADR 0057 — Client-independent sessions and client provenance (PF7)

## Status
Accepted for F3 / PF7 implementation.

## Context
PF1–PF6 established one persistent runtime, versioned events/realtime gateway, device identity, provider-independent capabilities and trust/permissions. The remaining session risk was conceptual and operational: a Web/PC client could still look like the owner of a conversation because client identity was not modeled separately from session, device or speaker provenance.

PF7 must prove that two client surfaces can observe and continue the same durable conversation without creating another Todd, Morgana, memory/context store or chat session.

## Decision
Sessions belong to Campanario. A client only **attaches** to a session while connected.

Introduce:

- `ClientIdentity(client_id, device_id?)`: identifies one software client surface;
- `ClientAttachment`: process-local live attachment of one client to one durable `session_id`;
- `ClientSessionRegistry`: runtime-owned registry of live attachments, intentionally non-durable;
- persistent `client_id` / `device_id` provenance on user messages;
- client provenance on `USER_TEXT` RuntimeEvents;
- stable agent provenance on Todd/Morgana events remains independent from client/device provenance.

`client_id` is not a social speaker and is not a security credential. `device_id`, when present, is PF4 physical-device identity and must authenticate through PF6 before it can be accepted on a client-originated turn or WebSocket connection. A localhost browser client can use a stable client id without claiming a device.

`/ws/v1/events` accepts `client_id` and optional `device_id`. For a session-specific observer, connection creates a live attachment and disconnect removes only that attachment; the durable session remains. Reconnect with the same `client_id` and `session_id` creates a new transport attachment, not a new conversation.

The Presence Web UI stores one stable `client_id` in browser local storage and sends it through both `/api/v1/.../turn` and `/ws/v1/events`.

The current persisted `ChatSession` is also the current technical conversation **episode**. PF7 therefore exposes `episode_id` as an alias of `session_id` rather than inventing a second durable container. A separate cross-episode abstraction, if needed, belongs to the Experience/Memory layer and requires its own ADR.

## Consequences
- PC and a second client can continue the same `session_id` and model context;
- multiple clients can observe the same realtime event stream simultaneously;
- disconnect/reconnect does not duplicate session, agent identities or context;
- user-origin provenance survives SQLite persistence (`client_id`, optional `device_id`);
- Todd/Morgana speaker provenance remains `agent_id`, never client/device id;
- live attachments disappear on transport/process disconnect while conversation history remains durable;
- PF7 does not build a mobile app, expose LAN/WAN, add voice or introduce another memory pipeline;
- PF8 Mobile Readiness is the next gate.
