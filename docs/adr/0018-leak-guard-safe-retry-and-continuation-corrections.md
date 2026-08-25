# ADR-0018 — Leak guard safe retry and continuation corrections

## Status
Accepted — 2026-08-24

## Context
The first Windows/Ollama validation after ADR-0017 confirmed that internal prompt text no longer reached the UI, but a simple social turn (`salve`) ended as `model_response_error`. The guard was failing closed on the first detected echo attempt. The same manual run also showed continuation-policy misses: acknowledgements could be mirrored mechanically, topic drops could ask for a new topic, and revision/hesitation phrases could trigger generic reassurance.

## Decision
1. Keep exactly one leading `system` message in the primary request.
2. Narrow leak markers to highly distinctive internal structural headings to reduce false positives.
3. Buffer a candidate response inside the guard. If an internal marker is detected, discard the entire candidate before any user-visible emission.
4. Retry once with a minimal hardened system prompt and the same non-system conversation messages.
5. If the retry leaks too, fail closed with `ModelResponseError`.
6. Diagnostics log only marker IDs and retry stage. Do not log prompt text, user content, model output, private corpus material, or persisted memory.
7. Tighten continuation guidance by semantic class:
   - acknowledgement: max 4 words, no recap/question/new topic, no mechanical `X tambem` mirroring;
   - reflection: one short sentence, no forced question;
   - revision: reconsider only the uncertain point, no reflex reassurance, max two sentences unless explicitly asked;
   - topic drop: max 4 words, stop the topic, do not propose or ask for the next topic.

## Consequences
- A first prompt-echo attempt no longer necessarily becomes a visible model error.
- Prompt leakage remains fail-closed after one safe retry.
- Normal short responses are buffered until accepted by the guard before being emitted, prioritizing confidentiality over token-by-token latency at this layer.
- The retry intentionally uses a reduced system instruction; it is an emergency recovery path, not the normal behavioral path.
- Pragmatic Input Understanding v0 remains disconnected from runtime until the conversational gate is closed.
