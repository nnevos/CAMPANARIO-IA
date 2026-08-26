# ADR 0063 — F5b Voice Media Runtime checkpoint

Status: ACCEPTED (F5b checkpoint; F5 remains open)

## Decision
The Call gateway now accepts signed 16-bit PCM binary frames through the existing `/ws/v1/call` connection. `VoiceMediaRuntime` owns provider-independent streaming STT/TTS adapter boundaries plus a conservative energy-VAD fallback. Finalized STT text is sent through the existing `VoiceCallCoordinator` and therefore the same Conversation Runtime, AgentRouter, ParticipationArbiter, Experience Layer and session.

Agent response chunks keep `agent_id`; TTS output is emitted as a versioned `tts_audio` metadata frame followed by binary audio. Barge-in cancels the cooperative conversation task, cancels active synthesis tasks and invokes the TTS adapter cancellation contract.

## Evidence
`tests/test_voice_media_f5b.py` proves binary PCM -> VAD -> STT -> shared conversation -> agent-provenanced TTS audio over a real FastAPI WebSocket test transport, plus TTS cancellation on barge-in. Full regression at this checkpoint: 399 PASS.

## Boundary / non-claim
No production STT or TTS engine is bundled by this ADR, and CI has no physical microphone/speaker. Therefore F5 is NOT frozen and this checkpoint must not be described as human voice ready. The next F5 gate is a host/device adapter proof on the target PC (microphone capture + chosen local STT/TTS engines + speaker playback + measured end-of-speech-to-first-audio latency), followed by PC/mobile continuity E2E.
