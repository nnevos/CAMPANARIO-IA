# ADR 0072 — F5c.10 Utterance aggregation + natural voice turns

Date: 2026-08-26
Status: Accepted inside F5; F5 remains open and F6 remains blocked.

## Evidence

Physical F5c.9 logs show pt-BR STT can transcribe complete spontaneous questions well, but a single spoken request can still be split into independent finals. Example shape: an arithmetic request becomes `... 123`, then a hallucinated short fragment, then `mais 49`; each fragment can trigger a separate agent turn. Physical use also shows that spoken answers feel overly expository and that human interruption during TTS needs to win quickly.

## Decision

1. Add a conservative pt-BR `likely_incomplete_voice_fragment()` boundary. It does not rewrite STT text or encode benchmark answers. It only delays dispatch for strong continuation evidence: isolated wake/name, ellipsis/dangling connectors, short continuation fragments, and clipped arithmetic requests.
2. Hold only risky fragments for a short 1200 ms grace window. Complete utterances do not pay this extra latency.
3. If speech continues during that window, combine the original PCM chunks, remove most duplicated VAD hangover silence, retain a short natural gap, and re-run Whisper over the combined audio. Do not concatenate potentially wrong STT strings.
4. Only the consolidated `stt_final` creates a Conversation Runtime turn. Intermediate risky fragments do not reach Todd/Morgana.
5. Every voice turn receives a delivery-only system note asking for concise, conversational Brazilian Portuguese suitable for speech. This is not a Personality Core change and does not claim trained personality.
6. Host barge-in defaults become slightly more responsive (energy 1600, 2 frames, 6-frame pre-roll) and stay configurable through Settings/env. Existing cancellation/correlation isolation remains authoritative: new human speech supersedes obsolete response/TTS work.

## Consequences

- Better chance that spontaneous phrases with pauses are recognized as one utterance.
- A wrong isolated Whisper fragment can be corrected by re-transcribing the original combined PCM.
- Calls should feel less like alternating text chat read aloud; user speech can interrupt active playback and take priority.
- Voice responses are shorter by default, while personality evolution remains a later explicit gate.
- F5 remains open pending physical verification on the target Windows microphone/speaker.

## Automated evidence

- Host Voice focused tests: 25/25 PASS.
- Full regression: 430/430 PASS.
- `compileall`: PASS.
