# ADR 0062 — Realtime Presence / Call orchestration checkpoint

Status: ACCEPTED (F5 checkpoint; F5 is not frozen)

## Decision
F5 presence is session/runtime state, never client or agent state. `PresenceManager` exposes `present`, `attentive`, and `engaged`, with a bounded attention window. A semantic Call starts attentive; wake `Campanario` reopens attention; direct `Todd`/`Morgana` preserves the address for the existing AgentRouter. Ambient final speech outside attention does not enter conversation memory.

A live `call_id` can hand off to another authenticated microphone-capable device while preserving `session_id`. Interruption now cooperatively cancels the gateway generation task and emits `AGENT_INTERRUPTED`; provider-specific hard cancellation and audio-device stop remain adapter concerns.

## Safety boundary
This ADR does not claim final VAD/STT/TTS engines, always-on microphone, OS background audio, wake model, desktop tray or production mobile audio. Those require real media adapters/E2E and remain inside the active F5 gate. No second ChatService, memory, Todd or Morgana may be introduced to implement them.
