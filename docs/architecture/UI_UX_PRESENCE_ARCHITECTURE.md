# Campanário — Presence UI/UX Architecture v1.3

## Product rule
Campanário is the system/environment. Morgana and Todd are persistent agent participants inside it. The user expresses intent; Campanário coordinates execution.

## Presence surface
The root UI is intentionally not a chat dashboard. It represents the current shared conversational space:
- **PRESENTE**: system available, no active turn.
- **ATENTO**: user has the floor / conversational window remains open.
- **ENGAJADO**: a turn is being coordinated or an agent is speaking.

Morgana is shown as the default primary voice, never as a mode. Todd remains visibly present. Agent names become prominent in the conversation only when they speak.

## System surface
Administrative/history concerns live behind `Sistema`: model/build, inhabitants, previous contexts, and future memory/tool/voice administration. This keeps mechanics out of everyday interaction.

## Voice contract (prepared, not faked)
The current backend has text/SSE but no microphone, STT, wake-word, TTS, or barge-in transport. The UI reserves those states and explicitly reports voice as not connected rather than pretending it works.

Future event flow should be transport-independent:
`PRESENTE -> wake/direct address -> ATENTO -> user speech -> processing -> agent speech -> ATENTO -> inactivity/end -> PRESENTE`.

Wake word opens attention, not a new session. Direct `Todd`/`Morgana` addresses only prioritize that turn/continuation; they never activate exclusive modes.

## Barge-in target
When TTS exists, user voice activity must immediately stop agent playback, move the core from speaking to attentive, and give the user the floor. This should be implemented as an interruption event in the voice transport, not UI-only animation.

## Existing functionality preserved
- `/api/system`
- `/api/agents`
- sessions/history
- shared primary-speaker routing
- SSE multi-agent responses
- persistent-participant semantics

The manual primary-speaker switch was removed from the presence UI because normal users should not route the system. The compatibility API remains available for diagnostics/advanced tooling.

## Sequenciamento de produto apos v1.3
A UI estar preparada para voz nao libera implementacao de voz. O gate atual e personalidade/continuidade dos agentes. Wake/STT/TTS/barge-in entram somente depois que Todd/Morgana tiverem baseline de personalidade e uma camada minima de experiencia persistente validada em texto.


## Continuous Presence update (v1.3.1)
- Presence UI boots clean: no old transcript is rendered automatically.
- A fresh technical episode is created lazily on the first new turn.
- Previous sessions are secondary **episodic memory records** under Sistema and require deliberate access.
- Sessions remain internal infrastructure; the user-facing concept is continuous coexistence/presence.
- Cross-episode learned memory is **not yet claimed as implemented**; it remains part of the Experience/Learning gate before voice.
- See `docs/adr/0039-continuous-presence-episodic-history.md`.
