# F3 Platform Foundation — Closure Review

Date: 2026-08-25  
Decision: **F3 CLOSED / Runtime v2 frozen**

## What is now true

Campanario can exist as a logical runtime without the Web UI. Web, second client, mobile proof client and semantic Call all enter the same runtime/session model. Devices, capabilities, permissions and tools are system resources, not agent-owned copies. Todd and Morgana remain persistent participants over the same Conversation Runtime and state.

## Telemetry closure

`RuntimeTelemetry` adds a bounded process-local timing journal with stable milestones:

- request_received
- routing_completed
- context_ready
- generation_started
- first_token
- first_usable_output
- generation_finished
- second_agent_started (when applicable)
- turn_finished
- tool_started
- tool_finished

Every point carries runtime identity and can carry correlation/session/agent/client/device provenance. `/api/v1/runtime/telemetry` exposes recent points read-only. No transcript text or hidden prompt is copied into telemetry.

## Closure proof

`tests/test_platform_foundation_closure.py` integrates the headless runtime, two client identities, one session/context, Event Bus identity and telemetry identity. `tests/test_runtime_telemetry.py` validates milestone ordering, second-agent timing and tool timing. PF3 gateway, PF8 mobile and PF9 Call E2Es remain regression gates.

## Explicit non-claims

F3 does not claim final audio, native mobile apps, cloud sync, continuous GPS/camera, unrestricted automation, durable telemetry backend or Experience/Learning memory. PF9 Call interruption remains signal-only.

## Next gate

**F4 — Experience / Learning Layer.** Do not skip directly to final voice/Patrulha. F4 must establish provenance-aware experiential continuity and anti-drift before realtime presence/call expands.
