# ADR 0059 — Voice / Call Readiness Contracts (PF9)

## Status
Accepted for F3 / PF9 implementation.

## Context
PF1–PF8 established one persistent Campanario Runtime, versioned realtime events, trusted devices, provider-independent capabilities, permissions, client-independent sessions and a minimal mobile client. Voice must not create a second cognitive pipeline, another ChatService, another memory or agent copies. At the same time, final VAD/wake/STT/TTS engines and continuous audio are intentionally blocked until Experience/Learning proves sufficient continuity.

## Decision
Add a transport-neutral voice contract layer and a semantic Call proof without final audio engines.

- `VoiceCallRegistry` owns process-local live call lifecycle; durable conversation ownership remains `session_id`.
- `VoiceCallCoordinator` accepts wake, speech partial/final, interruption and call end signals.
- only `speech_final` enters the existing `ChatService.stream_turn()`; partial speech and wake are operational realtime events and are not persisted as user messages;
- speech-final and resulting `USER_TEXT` share one correlation id, and `USER_TEXT.causation_id` points to the `USER_SPEECH_FINAL` event;
- device/client provenance is preserved through the existing PF7 identity model;
- a call requires an authenticated/trusted device with `microphone` capability and the existing `microphone.listen = ALLOW_WHILE_CALL` PF6 policy;
- VAD, wake, STT and TTS are represented by adapter protocols (`VoiceActivityDetector`, `WakeWordDetector`, `SpeechToTextAdapter`, `TextToSpeechAdapter`) rather than concrete engines;
- `/ws/v1/call` is a versioned semantic proof channel. It accepts already-decoded wake/STT frames and emits call events plus `tts_text` synthesis directives with `agent_id`;
- `AGENT_INTERRUPTED` is an explicit barge-in/interruption signal. PF9 deliberately labels acknowledgement as `signal_only`; it does not claim safe model-generation cancellation or audio cutoff.

No binary audio transport, final wake model, final STT/TTS provider, background audio service or Patrulha behavior is introduced.

## Consequences
- Web/Mobile/Voice now target the same conversation, agents and context boundaries;
- a future audio adapter can replace semantic test frames without changing Todd/Morgana or Social Protocol;
- TTS routing preserves speaker provenance so Todd/Morgana may later have separate voices without separate cognitive stacks;
- PF9 closes the contract/readiness slice but does not make Voice/Call a production feature;
- the next gate is F3 Platform Foundation final validation/telemetry closure before F4 Experience / Learning.
