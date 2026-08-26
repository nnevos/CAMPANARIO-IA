# ADR 0066 — Host Voice Runtime Readiness (F5c.3)

Status: Accepted — 2026-08-25

## Context

The physical Windows E2E proved that device pairing and `/ws/v1/call` connectivity were healthy, but a fresh checkpoint could start the API with conservative `.env` voice defaults. Raw PCM then reached `UnconfiguredStt` and crashed the ASGI call task. The launcher also recognized only one model layout, while the project has used `models/`, `voice/models/` and `voice/` during F5c setup.

## Decision

Voice readiness belongs to the runtime/media boundary, not only to a Windows launcher. `build_host_voice_media()` may discover existing local whisper.cpp assets from the supported project layouts when explicit settings remain unconfigured. Explicit settings still take precedence and no model/provider is downloaded automatically.

`VoiceMediaRuntime` exposes STT/TTS readiness. The Call gateway never lets missing STT/TTS become an uncaught runtime exception: raw audio without STT returns a versioned `voice_stt_not_configured` error, and missing TTS returns `voice_tts_not_configured`. The Host Voice client renders these errors directly.

The Windows launcher additionally searches the known model layouts plus a recursive project-local fallback and prints actionable warnings when a multilingual model is absent.

## Consequences

- Fresh `.env` defaults no longer silently break an otherwise prepared local voice checkout.
- Missing models remain a deployment/setup condition, not a cognitive-runtime failure.
- F5 remains open until the target Windows host passes physical Portuguese STT, silence/noise, TTS and barge-in acceptance.
