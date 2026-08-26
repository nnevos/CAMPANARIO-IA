# F5c — Host Voice Integration Review

## Implemented

- local host client `campanario-host-voice`;
- physical microphone/speaker boundary via optional `sounddevice` extra;
- selected local STT baseline: whisper.cpp (`whisper-cli` + configured model);
- selected local TTS baseline: Windows SAPI, producing WAV bytes locally;
- Todd/Morgana keep `agent_id` through synthesis and may use distinct SAPI voice names/rates;
- authenticated host device remains connected in Device Registry during the Call;
- physical playback abort precedes the versioned barge-in interrupt;
- `voice_end_of_speech` / `voice_first_audio` telemetry milestones;
- host prints `stt_final -> first playback` latency;
- no cloud voice provider and no second conversation pipeline.

## Windows acceptance flow

1. Configure `.env`:
   - `CAMPANARIO_VOICE_STT_BACKEND=whisper_cpp`
   - `CAMPANARIO_VOICE_TTS_BACKEND=windows_sapi`
   - `CAMPANARIO_VOICE_WHISPER_CPP_PATH=...whisper-cli.exe`
   - `CAMPANARIO_VOICE_WHISPER_MODEL_PATH=...ggml-*.bin`
   - optional Todd/Morgana SAPI voice names.
2. `uv sync --extra voice-host`.
3. Start Campanario normally.
4. Run `tools/windows/DIAGNOSTICO_VOZ_F5C.bat`.
5. Run `tools/windows/PAREAR_VOZ_HOST_F5C.bat` once.
6. Run `tools/windows/INICIAR_VOZ_HOST_F5C.bat`.
7. Speak, hear the correct agent, interrupt while it speaks and record latency.

## Automated evidence

- focused F5c/F5b/F5/PF9: 14 PASS;
- full repository regression: 403 PASS;
- compileall: PASS.

## Gate status

Implementation is ready for target-host acceptance, but physical device acceptance is not reproducible in the build container. F5 remains open and F6 is blocked.

Acceptance checklist: `docs/current/F5C_HOST_ACCEPTANCE_CHECKLIST.md`.
