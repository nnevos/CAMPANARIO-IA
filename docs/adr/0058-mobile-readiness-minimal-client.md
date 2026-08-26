# ADR 0058 — Mobile Readiness minimal client (PF8)

## Status
Accepted for F3 / PF8 implementation.

## Context
PF7 proved that sessions belong to Campanario rather than Web/PC clients. PF4–PF6 already provide persistent device identity, semantic capabilities and trust/permission boundaries. The remaining PF8 question is whether a mobile-shaped remote client can use those same contracts without creating another Campanario, another conversation pipeline or mobile-specific Todd/Morgana state.

PF8 must not prematurely build a production Android/iOS app or expose the localhost gateway to LAN/WAN.

## Decision
Add a transport-real, UI-less `MobileReadinessClient` that consumes the existing PF3/PF7 API and realtime contracts:

- register a mobile device over `/ws/v1/devices`;
- pair through the PF6 trust boundary and retain the one-time credential client-side;
- authenticate later HTTP and WebSocket connections with that device credential;
- join/create the same durable `session_id` used by Web/PC;
- send text through `/api/v1/sessions/{id}/turn` with `client_id` + `device_id` provenance;
- observe/reconnect to `/ws/v1/events` using the same session and `after_sequence`;
- publish one explicit authenticated GPS snapshot through the device channel.

An authenticated GPS snapshot is bridged into the normal PF5 registry as semantic `location.current`, requiring `location.read`. The snapshot publishes the existing PF2 `LOCATION_UPDATED` event with device provenance. It is process-local/current-state only and is invalidated on device disconnect so stale coordinates do not become persistent user memory.

A previously paired device must authenticate when reconnecting to `/ws/v1/devices`. First contact may register an untrusted device identity so the local PF6 pairing flow can occur, but an unpaired channel cannot publish location.

PF8 proves one selected mobile location provider. General arbitration among several simultaneous devices/providers is not added here.

The server remains bound to `127.0.0.1`; the mobile proof therefore validates protocol/client independence over real loopback sockets, not production remote-network exposure.

## Consequences
- Android/iOS can later be thin shells over the same runtime contracts;
- mobile text and Web text use the same Conversation Runtime, Social Protocol and agent identities;
- mobile reconnect does not create another session/personality;
- device capability data is authenticated before entering the runtime;
- `location.current` remains provider-independent to callers;
- location snapshot state is not memory and does not survive disconnect;
- no Android/iOS UI, background service, push notifications, STT/TTS, wake word or Patrol mode is implemented;
- PF9 may define Voice/Call readiness contracts, but real continuous voice remains gated by Experience/Learning and later call gates.
