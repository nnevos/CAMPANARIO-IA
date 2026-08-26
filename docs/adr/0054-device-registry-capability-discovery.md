# ADR 0054 — Device Registry and Capability Discovery (PF4)

## Status
Accepted for F3 / PF4 implementation.

## Context
PF1–PF3 established a persistent client-independent runtime, an ordered event bus and a versioned realtime/API gateway. The runtime still had no durable representation of connected devices, so a future mobile/headset/desktop client could not announce what physical capabilities it can provide without hardcoding platform details.

PF4 must establish device identity and connection state before the Capability/Tool Registry and Permission/Trust Layer. Device identity at this stage is operational registry identity only; it must not be mistaken for authentication or authorization.

## Decision
Add a runtime-owned `DeviceRegistry` backed by SQLite.

A `Device` persists:

- stable `id` supplied by the client;
- human-readable `name`;
- descriptive `type` (metadata only, never capability routing logic);
- normalized advertised `capabilities`;
- `connection_state` (`connected` / `disconnected`);
- `created_at`, `updated_at` and `last_seen`.

Capability lookup is explicit through `find_capable("gps")`, `find_capable("microphone")`, etc. Runtime code does not ask for an Android/Windows-specific provider.

Add migration `0006_device_registry.py` and a provider-independent `DeviceRepository` boundary.

Add `/ws/v1/devices` as the PF4 device lifecycle channel. A client sends a versioned `device_hello` frame containing its stable id, name, type and capabilities. The registry marks it connected and returns a versioned `device_ready` frame. Disconnect marks the same record disconnected; reconnecting with the same id updates the record rather than creating another device. A minimal `ping` frame updates `last_seen`.

Add read-only API discovery:

- `GET /api/v1/devices`;
- `GET /api/v1/devices?capability=gps&connected_only=true`;
- `GET /api/v1/devices/{device_id}`.

Device lifecycle publishes the existing PF2 events `DEVICE_CONNECTED`, `DEVICE_STATE_CHANGED` and `DEVICE_DISCONNECTED`, with explicit device provenance.

PF4 does **not** add `trusted`, pairing credentials, action authorization or network exposure. A stable `device_id` is not a security credential. Those semantics belong to PF6.

## Consequences
- device identity and advertised capabilities survive runtime restart through SQLite;
- disconnect/reconnect preserves one registry identity;
- future code can discover a device by capability instead of platform name;
- PF2/PF3 observers see device state changes through the same event vocabulary;
- the gateway remains localhost-only and does not claim secure remote pairing;
- Tool/Capability Registry remains PF5 and Permission/Trust remains PF6;
- Personality / Social / Long-Call Baseline v1 is unchanged.
