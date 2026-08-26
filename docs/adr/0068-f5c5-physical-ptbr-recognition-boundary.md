# ADR 0068 — F5c.5 Physical pt-BR recognition boundary

Date: 2026-08-26
Status: accepted as implementation checkpoint; physical acceptance still pending

## Context

ADR 0067 proved the complete Windows microphone -> Host Voice -> Call -> STT -> shared Conversation Runtime -> agent -> TTS round trip, but the spoken phrase `Campanario, voce esta ai?` reached the runtime as `O Brasil e o maior.`. The cognitive/runtime path behaved correctly on the corrupted transcript, so the next work is constrained to the physical STT/capture boundary.

Inspection of the implemented boundary found two accuracy risks. First, the Call gateway appended only PCM frames individually classified as speech by the energy VAD. This could delete soft consonants/syllables and short pauses inside a sentence before Whisper saw the WAV, and it had no pre-roll for the beginning of speech. Second, the Windows launcher selected `ggml-small.bin` before a locally available larger multilingual model, so an accuracy-oriented physical gate could silently use the smaller model even when `big/large` was present.

## Decision

1. VAD remains a boundary detector, not an audio filter. `UtteranceBuffer` preserves a four-frame pre-roll before speech and retains every frame after speech starts until a twelve-frame silence hangover closes the utterance.
2. The minimum-speech gate still counts only frames classified as speech. Pre-roll/tail silence can improve Whisper context but cannot manufacture a user turn from silence.
3. Physical pt-BR model discovery is accuracy-first by default: `large-v3/large/big/medium` precede `small/base/tiny`. `CAMPANARIO_VOICE_WHISPER_PREFER_ACCURACY=false` can restore a latency-oriented preference.
4. Portuguese remains explicit (`-l pt`) and no semantic correction/post-hoc rewriting is allowed between Whisper and the Conversation Runtime. Personality Core, AgentRouter, memory and conversation behavior remain untouched.
5. Defaults for the physical gate become `VOICE_PREROLL_FRAMES=4` and `VOICE_SILENCE_FRAMES_TO_FINALIZE=12` while preserving `VOICE_MIN_SPEECH_MS=240` and the existing no-speech filtering.

## Evidence

- Focused Host Voice / Voice Media tests: 21/21 PASS.
- Full regression: 418/418 PASS.
- The build environment cannot certify microphone acoustics or actual target-PC transcription quality; a physical pt-BR re-run is still required.

## Gate consequence

F5 remains OPEN and F6 remains BLOCKED. The next gate is physical pt-BR acceptance on the target Windows PC using the effective larger multilingual model when present. If recognition still fails, collect the actual selected input device/model and measured audio evidence before further VAD/capture tuning. Do not compensate in Todd/Morgana or the shared Conversation Runtime.
