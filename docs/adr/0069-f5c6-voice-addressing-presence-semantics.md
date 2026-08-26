# ADR 0069 — F5c.6 Voice addressing and presence semantics

Date: 2026-08-26
Status: accepted as implementation checkpoint; physical acceptance still pending

## Context

The F5c.5 target-PC run showed materially improved pt-BR recognition: `Campanário, me escuta`, `Campanario, Todd` and `Campanario, Todd e Morgana` reached the runtime intelligibly. The remaining defect was no longer STT corruption. Presence probes were treated as open content questions, and an explicit two-agent voice address allowed the second agent to see the first agent's answer as immediate conversational history, encouraging it to react to that answer instead of the user's original utterance. The same evidence also showed Whisper returning the correct accented spelling `Campanário`, while `resolve_wake()` only matched the unaccented form.

## Decision

1. Wake recognition is accent-insensitive: `Campanário` and `Campanario` are equivalent at the runtime boundary while the original transcript remains unchanged for display/evidence.
2. Host Voice classifies narrow presence probes such as `me escuta?`, `me ouve?`, `ta ai?` and name-only calls as call-presence semantics. Agents receive a runtime note to confirm presence/audibility briefly instead of inventing a missing task or asking what should be heard.
3. When a physical voice turn explicitly addresses both Todd and Morgana, both answer the same original user utterance. The secondary agent receives the pre-primary history rather than the first agent's newly generated answer, preventing answer-as-input chaining.
4. This independent group context is voice-specific. Existing text multi-agent discussion behavior remains unchanged.
5. No Personality Core, memory model, facts, STT transcript rewriting or F6 behavior is changed.

## Evidence

- Focused voice/presence/agent tests: 38/38 PASS.
- Full regression: 422/422 PASS.
- `compileall`: PASS.

## Gate consequence

F5 remains OPEN and F6 remains BLOCKED. The next step is another physical Host Voice run on Windows, especially `Campanário, me escuta?`, `Campanário, ta ai?`, `Campanário, Todd` and `Campanário, Todd e Morgana`, verifying short presence acknowledgements and that each explicitly addressed agent responds to the user's utterance rather than to the other agent's answer.
