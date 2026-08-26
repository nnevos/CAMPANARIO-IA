# F5b — Voice Media Runtime / Call media E2E

## Implemented
- binary signed-16-bit PCM on `/ws/v1/call`;
- provider-independent `VoiceMediaRuntime`;
- energy VAD fallback behind an adapter boundary;
- streaming STT boundary and utterance finalization;
- final speech reuses `VoiceCallCoordinator` and the shared Conversation Runtime;
- TTS audio preserves `agent_id` and is returned as metadata + binary bytes;
- cooperative barge-in cancels turn task, synthesis tasks and calls TTS cancellation;
- legacy semantic `speech_final` / `tts_text` frames remain compatible.

## Gate evidence
Focused F5/F5b tests: 10 PASS. Full repository regression: 399 PASS. `compileall`: PASS.

## Still required before user-facing voice-ready claim
A real host adapter must capture the target PC microphone, connect a selected STT engine, connect agent-specific TTS voices, play audio on the speaker, prove actual stop-on-barge-in, and record perceived latency. Physical PC/mobile media cannot be truthfully proven inside the build container.

F5 remains active. Do not advance to F6.
