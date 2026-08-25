# ADR 0039 — Continuous presence, episodic history

## Decision
The Presence UI must never boot into an old transcript. Campanario is a continuous environment, not a chat picker.

On every UI boot the visible surface starts in **PRESENTE** with no historical messages rendered. A technical chat session/episode is created lazily on the first new user turn. Existing sessions remain persisted as episodic records and are available only through the secondary System area for deliberate inspection.

## Why
A previous transcript on screen makes the product feel like a conventional messenger. The intended mental model is closer to re-entering a call: the relationship and system memory can persist while the visible conversational surface represents the present moment.

## Boundaries
- Sessions remain a backend implementation detail for context, persistence, audit and future memory extraction.
- This change does **not** claim cross-session semantic memory is complete. That belongs to the later Experience/Learning layer.
- Inspecting an archived episode is deliberate. Starting a new turn after inspection returns to a clean present surface and creates a fresh episode.
- Voice/wake-word work remains blocked by the personality/learning roadmap.
