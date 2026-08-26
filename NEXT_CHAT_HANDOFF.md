# NEXT CHAT HANDOFF — 2026-08-25

Read `RECOVER_FIRST.md`, `PROJECT_STATE.md`, `SAFEPOINT.md`, `docs/current/ROADMAP.md`, then ADR 0067. Code remains final evidence.

## Exact resume point

F5c.4 physical voice pipeline is alive. On the target Windows PC, microphone audio reached the shared Call/Conversation Runtime and Morgana answered. The blocker is Portuguese STT accuracy, not runtime wiring.

Observed physical test:
- user actually said: `Campanario, voce esta ai?`
- STT delivered: `O Brasil e o maior.`
- Morgana answered: `Em area territorial na America do Sul, sim.`

## Next gate

1. Verify which Whisper multilingual model is actually loaded.
2. Verify effective language is Portuguese (`-l pt`).
3. Run a very small pt-BR acceptance set.
4. Only then tune VAD/capture/noise based on evidence.
5. Do not touch Personality Core to mask transcription errors.
6. Do not advance to F6 until F5 voice acceptance is frozen.

## Recovery note

`voice/` and `models/` are local deployment assets and can be lost on deletion/format. Restore them and run `tools/windows/PREPARAR_VOZ_F5C.bat`. Do not bundle machine credentials/secrets into recovery media.

## F5c.10 current handoff — 2026-08-26

Current gate remains F5, F6 blocked. ADR 0072 adds conservative incomplete-fragment holding, PCM re-transcription across adjacent voice chunks, shorter spoken delivery guidance, and more responsive configurable barge-in. Do not tune Personality Core from voice style evidence yet. Next evidence must be physical Windows Host Voice: spontaneous long/paused utterances should normally produce one `voce:`; speaking over active TTS should stop it and the old turn must not reappear.

## Freeze 2026-08-26

Desenvolvimento ativo pausado. A frente experimental posterior ao ADR 0074 foi removida deste pacote. Consulte `FREEZE_BASELINE.md`. F5 permanece OPEN/pausado e F6 BLOCKED.
