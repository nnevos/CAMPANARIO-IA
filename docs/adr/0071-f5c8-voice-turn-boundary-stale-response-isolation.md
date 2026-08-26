# ADR 0071 — F5c.8 Voice Turn Boundary / Stale Response Isolation

Date: 2026-08-26
Status: Accepted inside F5; F5 remains open and F6 remains blocked.

## Context

Physical F5c.7 evidence showed that intelligible pt-BR speech could still be split at natural pauses. A phrase addressed to Morgana was finalized after the comparative fragment `onde que e o lugar mais`, while the continuation arrived as another user turn. The same physical run also showed delayed responses from older turns (for example an arithmetic answer resurfacing after later user speech).

This is a media/turn-boundary problem, not a Personality Core problem and not evidence that phrase-specific semantic rewrites are needed.

## Decision

1. Increase the physical Host Voice end-of-speech hangover from 24 to 45 PCM frames. At the current 40 ms host frame this is about 1.8 s, favoring complete natural phrases over minimum latency.
2. Keep pre-roll and all intra-utterance PCM unchanged; VAD remains a boundary detector only.
3. Every voice turn gets an explicit correlation id before entering `VoiceCallCoordinator.speech_final()`.
4. If a new confirmed utterance arrives while the prior response is still running, cancel the prior Conversation/TTS tasks before starting the new turn.
5. Agent events whose correlation id belongs to a replaced turn are filtered at the Call gateway and cannot become TTS for the current turn.
6. Do not add phrase-specific corrections, violence-specific recognition rules, or post-STT text rewriting.

## Consequences

- Natural pauses are less likely to split a single sentence into multiple user turns.
- Voice latency after the user stops speaking can increase by roughly 0.8 s relative to F5c.7; this is an intentional accuracy/turn-integrity tradeoff for the physical acceptance gate.
- A cancelled/obsolete response cannot leak delayed chunks into a newer voice turn at the Call transport boundary.
- F5 is still not frozen. Target-PC physical validation remains required.

## Automated evidence

- Focused voice/runtime tests: 35/35 PASS.
- Full regression: 424/424 PASS.
- `compileall`: PASS.
