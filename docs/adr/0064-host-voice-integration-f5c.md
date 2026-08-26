# ADR 0064 — F5c Host Voice Integration checkpoint

Status: ACCEPTED (implementation complete; target-PC acceptance pending; F5 remains open)

## Decision

The Windows host baseline for real Call media is **local whisper.cpp STT + Windows SAPI TTS + sounddevice/PortAudio host I/O**. These are adapters at the host/media boundary; Conversation Runtime, AgentRouter, ParticipationArbiter, Experience Layer and session state are unchanged.

`WhisperCppStt` converts the finalized 16 kHz mono PCM utterance to a temporary WAV and invokes a configured local `whisper-cli` + model. `WindowsSapiTts` synthesizes local WAV audio and preserves per-agent voice/rate selection for Todd and Morgana. The host client captures physical PCM and plays returned WAV/PCM through a selected sounddevice endpoint.

The host voice client remains an authenticated PF4/PF6 device with `microphone` + `speaker` capabilities and keeps `/ws/v1/devices` alive while attached to `/ws/v1/call`. It never owns conversation state.

## Barge-in

While playback is active, local microphone energy can trigger host barge-in. The host immediately aborts local playback, then sends the existing versioned `interrupt` frame. The gateway cooperatively cancels the active turn and TTS adapter. Acoustic echo cancellation is not claimed; headphones are recommended for acceptance testing.

## Latency

The Call gateway records `voice_end_of_speech` and `voice_first_audio` runtime telemetry milestones. The host client also prints `stt_final -> first playback` latency for a directly observable acceptance metric.

## Security

Host credentials are produced only by explicit `--pair` and stored in Campanario's user data directory; POSIX permissions are narrowed where supported. `device_id` remains identity, never credential. No LAN exposure is introduced.

## Evidence and non-claim

Automated focused F5c/F5b/F5/PF9 tests pass and full repository regression passes. CI/container cannot prove the user's physical microphone, speaker, installed SAPI voices, or local whisper.cpp binary/model. Therefore this ADR does **not** freeze F5 or claim human voice acceptance.

The next gate is **F5c Host Acceptance / Voice Ready Gate on the target Windows PC**. F6 remains blocked until that acceptance records successful microphone capture, transcription, audible Todd/Morgana output, physical barge-in, and perceived latency.
