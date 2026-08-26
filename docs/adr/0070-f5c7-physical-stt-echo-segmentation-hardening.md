# ADR 0070 — F5c.7 Physical STT echo/segmentation hardening

Date: 2026-08-26
Status: accepted as an F5 checkpoint; F5 remains open and F6 remains blocked.

## Evidence

The target Windows physical run after ADR 0069 showed correct short pt-BR recognition, but repeated spoken prompts still produced split turns and unrelated transcripts. The log contained isolated `Campanário.` segments followed by a second fragment, and microphone PCM continued to be forwarded while SAPI audio was playing. Therefore the remaining defect was still at the capture/STT boundary, not in AgentRouter or personalities.

## Decision

- Host Voice no longer forwards microphone frames to server STT during local TTS playback unless human barge-in is confirmed. A small local pre-roll is retained and forwarded only after confirmed interruption.
- Default barge-in confirmation is stricter (energy 1800, 3 frames) to reduce loudspeaker echo falsely becoming user speech.
- End-of-utterance hangover grows from 12 to 24 40-ms frames (~960 ms), pre-roll from 4 to 6 frames, and minimum detected speech from 240 to 300 ms. This keeps natural short pauses after the wake name inside the same utterance.
- Whisper initial prompt is reduced to proper names only: `Campanario. Todd. Morgana.`
- whisper.cpp decoding is deterministic beam search: Portuguese remains explicit; temperature is zero; beam size is 5; temperature fallback is disabled; non-speech tokens are suppressed. The no-speech threshold is 0.50.
- No semantic post-correction is introduced. The shared Conversation Runtime still receives the STT transcript as accepted by the voice boundary.

## Evidence after change

- Focused voice/runtime tests: 27/27 PASS.
- Full regression: 424/424 PASS.
- Personality Core, ExperienceLayer and F6 were not changed.

## Next gate

Repeat physical pt-BR acceptance on the target Windows PC. F5 can only close on physical evidence; F6 remains blocked.
