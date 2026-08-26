# ADR 0055 — Capability / Tool Registry Provider Independence (PF5)

## Status
Accepted for F3 / PF5 implementation.

## Context
PF4 lets Campanario identify connected devices and discover hardware capabilities such as `gps`, `microphone` and `screen`. The runtime still lacked a provider-independent execution layer for semantic capabilities such as `location.current`, `weather.current` or `files.search`.

Without a registry, agents or clients would need to know provider details (Android, HTTP API, local Python adapter, etc.), which would duplicate tool logic across clients and violate the single-runtime architecture.

## Decision
Add a runtime-owned `CapabilityRegistry` exposed as `runtime.tools` / `runtime.capabilities`.

A `CapabilityDefinition` contains:

- stable semantic `name`;
- human description;
- input/output schemas;
- `provider_id`;
- permission requirement metadata (not authorization decisions);
- availability derived from the registered provider;
- timeout;
- explicit provider/device provenance.

Providers implement one transport-neutral async `invoke(capability, arguments)` boundary. Callers execute by capability name and do not select or import a concrete provider.

PF5 includes a `DeviceCapabilityProvider` bridge whose availability follows one PF4 device and, optionally, one advertised hardware capability. This proves a mock/remote device capability can be consumed by the same runtime while the caller only asks for `location.current` (or another semantic name).

Capability execution validates the PF5 schema subset, applies timeout at the runtime boundary, and publishes the existing PF2 events:

- `TOOL_REQUESTED`;
- `TOOL_STARTED`;
- `TOOL_RESULT`;
- `TOOL_FAILED`.

The API exposes read-only catalog discovery through `/api/v1/capabilities`. PF5 deliberately does **not** expose a generic remote execute endpoint because authorization, confirmation, trust, pairing and revocation belong to PF6.

## Consequences
- Todd/Morgana and future clients can reason in semantic capabilities rather than provider APIs;
- providers can be local, device-backed, external or test adapters without changing agent personality;
- device disconnect immediately affects capability availability without deleting its definition;
- provenance and timeout are centralized and observable through PF2 events;
- permission names exist only as declarative requirements until PF6 decides whether execution is authorized;
- no LAN/WAN exposure, unrestricted PC automation or mass provider integration is introduced in PF5;
- Personality / Social / Long-Call Baseline v1 remains unchanged.
