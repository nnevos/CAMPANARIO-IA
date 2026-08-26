# ADR 0067 — F5c.4 Physical Voice Checkpoint Freeze

Status: Accepted checkpoint — 2026-08-25

## Context

The target Windows PC reached a real end-to-end voice turn after restoring local whisper.cpp/model assets. The Host Voice client connected to the shared Call runtime, captured physical microphone audio, produced an STT final, routed it through the existing shared Conversation Runtime, selected Morgana, generated a response and returned it through the voice path.

Physical evidence from the target host:

- spoken by user: `Campanario, voce esta ai?`
- STT transcript observed: `O Brasil e o maior.`
- Morgana response: `Em area territorial na America do Sul, sim.`

This proves transport/runtime/cognitive round-trip, but also proves Portuguese recognition quality is not acceptable yet. The semantic content was materially corrupted before reaching the conversation runtime.

## Decision

Freeze the project at **F5c.4 physical voice pipeline alive / Portuguese STT quality not accepted**.

Do not advance to F6. Do not modify Personality Core to compensate for STT errors. The next work item is narrowly scoped to physical pt-BR STT quality and capture tuning: verify the effective multilingual model and `-l pt`, then tune VAD/capture only from measured host evidence. Preserve the same Call/Conversation Runtime and agent provenance.

The local voice binaries and model are deployment assets and may need reinstall after deletion/formatting. Recovery documentation must explicitly preserve their expected layout and the preparation command; secrets/credentials must not be embedded in a distributable recovery archive.

## Gate state

- microphone -> host client: PROVEN on target PC;
- host client -> authenticated `/ws/v1/call`: PROVEN;
- Call -> STT -> shared Conversation Runtime: PROVEN;
- Todd/Morgana shared runtime identity/provenance: architecture unchanged;
- agent response returned over voice call: PROVEN;
- pt-BR transcription accuracy: **FAIL / NOT ACCEPTED**;
- silence/noise robustness: NOT YET ACCEPTED;
- playback/barge-in acceptance: NOT YET FROZEN;
- F5 overall: **OPEN**;
- F6: **BLOCKED**.

## Resume point

Start by running the existing preparation/diagnostic path, then one short physical Portuguese phrase. If the transcript is still materially wrong, inspect the effective Whisper model/language before changing runtime architecture.
