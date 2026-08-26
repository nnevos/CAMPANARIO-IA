# ADR 0060 — Platform Foundation / Runtime v2 freeze

Status: **Accepted / Frozen**  
Date: 2026-08-25

## Context

PF1a..PF9 established a UI-independent Campanario Runtime, versioned events/realtime gateway, device and capability registries, permission/trust, client-independent sessions, mobile readiness and semantic Call contracts. The remaining F3 gate required architectural latency telemetry plus an integrated closure proof without claiming final voice/mobile/product features.

## Decision

Freeze **Platform Foundation / Runtime v2** as the F3 baseline.

A process-local `RuntimeTelemetry` journal is owned by the runtime and records stable, provider-independent milestones with runtime/session/correlation and optional agent/client/device provenance. Conversation instrumentation records `request_received`, `routing_completed`, `context_ready`, `generation_started`, provider `first_token`, `first_usable_output`, `generation_finished`, optional `second_agent_started`, and `turn_finished`. Tool lifecycle is observed from the Event Bus as `tool_started` / `tool_finished`.

`first_token` intentionally means first model-provider token; `first_usable_output` means the first output that survives the response-contract pipeline and is ready to be emitted. They are not conflated, because perceived Call latency depends on that distinction.

Telemetry is exposed read-only at `/api/v1/runtime/telemetry` for diagnostics. The journal is bounded and process-local; durable metrics storage/export is not required to freeze F3.

The integrated closure E2E proves one headless runtime, two client identities writing into one durable session/context, one Event Bus/runtime identity, and the same telemetry identity. Existing PF3/PF8/PF9 E2Es remain part of the gate.

## Consequences

- F3 is complete; F4 Experience / Learning is the next gate.
- No second memory, agent, provider or conversation pipeline was introduced.
- No final STT/TTS, wake engine, background audio, Patrulha, native mobile app or cloud exposure is implied.
- Future metrics exporters consume `RuntimeTelemetry`; they do not redefine conversation semantics.
- Personality / Social / Long-Call Baseline v1 remains frozen and unchanged.
