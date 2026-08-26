from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from campanario.config import Settings
from campanario.runtime.host_voice import WhisperCppStt, build_host_voice_media, probe_host_voice
from campanario.voice.host_client import HostVoiceClient


def test_host_voice_defaults_are_explicitly_unconfigured() -> None:
    settings = Settings(_env_file=None)
    assert build_host_voice_media(settings) is None
    probe = probe_host_voice(settings)
    assert probe.stt_ready is False
    assert probe.tts_ready is False


@pytest.mark.asyncio
async def test_whisper_cpp_adapter_transcribes_final_pcm_via_local_cli(tmp_path: Path) -> None:
    model = tmp_path / "model.bin"
    model.write_bytes(b"model")
    cli = tmp_path / "fake-whisper"
    cli.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib,sys\n"
        "args=sys.argv\n"
        "prefix=pathlib.Path(args[args.index('-of')+1])\n"
        "prefix.with_suffix('.txt').write_text('Campanario teste host', encoding='utf-8')\n",
        encoding="utf-8",
    )
    cli.chmod(0o755)
    adapter = WhisperCppStt(str(cli), model, language="pt")
    assert await adapter.push(b"\x01\x00" * 100, final=False) is None
    result = await adapter.push(b"\x01\x00" * 100, final=True)
    assert result is not None
    assert result.text == "Campanario teste host"
    assert result.final is True


class _FakeAudio:
    playing = True

    def stop_output(self) -> None:
        self.playing = False


class _FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[object] = []

    async def send(self, value) -> None:
        self.sent.append(value)


@pytest.mark.asyncio
async def test_host_barge_in_stops_local_playback_before_forwarding_pcm() -> None:
    audio = _FakeAudio()
    client = HostVoiceClient(
        http_base="http://127.0.0.1:8000",
        device_id="pc",
        client_id="host",
        credential="secret",
        audio=audio,  # type: ignore[arg-type]
        barge_in_threshold=100,
        barge_in_frames=1,
    )
    websocket = _FakeWebSocket()
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    task = asyncio.create_task(client._mic_sender(websocket, queue))
    loud = b"\xff\x7f" * 320
    await queue.put(loud)
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert audio.playing is False
    assert isinstance(websocket.sent[0], str)
    assert json.loads(websocket.sent[0])["frame_type"] == "interrupt"
    assert websocket.sent[1] == loud



@pytest.mark.asyncio
async def test_host_playback_echo_is_not_forwarded_to_stt_without_confirmed_barge_in() -> None:
    audio = _FakeAudio()
    client = HostVoiceClient(
        http_base="http://127.0.0.1:8000",
        device_id="pc",
        client_id="host",
        credential="secret",
        audio=audio,  # type: ignore[arg-type]
        barge_in_threshold=30000,
        barge_in_frames=3,
    )
    websocket = _FakeWebSocket()
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    task = asyncio.create_task(client._mic_sender(websocket, queue))
    await queue.put(b"\xe8\x03" * 320)
    await queue.put(b"\xe8\x03" * 320)
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert websocket.sent == []


def test_physical_ptbr_defaults_keep_short_pauses_inside_one_utterance() -> None:
    settings = Settings(_env_file=None)
    assert settings.voice_silence_frames_to_finalize == 45
    assert settings.voice_preroll_frames == 6
    assert settings.voice_min_speech_ms == 300
    assert settings.voice_whisper_prompt == "Campanario. Todd. Morgana."
    assert settings.voice_whisper_no_speech_threshold == 0.50

def test_f5_voice_defaults_are_faster_and_still_tunable() -> None:
    settings = Settings(_env_file=None)
    assert settings.voice_todd_rate == 4
    assert settings.voice_morgana_rate == 3


def test_voice_speed_preset_launcher_is_present() -> None:
    source = Path("tools/windows/AJUSTAR_VELOCIDADE_VOZ.bat").read_text(encoding="utf-8")
    assert "CAMPANARIO_VOICE_TODD_RATE" in source
    assert "CAMPANARIO_VOICE_MORGANA_RATE" in source
    assert "setx" in source.casefold()


def test_host_voice_settings_build_whisper_and_sapi_boundaries(tmp_path: Path) -> None:
    model = tmp_path / "model.bin"
    model.write_bytes(b"model")
    settings = Settings(
        _env_file=None,
        voice_stt_backend="whisper_cpp",
        voice_tts_backend="windows_sapi",
        voice_whisper_cpp_path="whisper-cli.exe",
        voice_whisper_model_path=model,
        voice_todd_voice="ToddVoice",
        voice_morgana_voice="MorganaVoice",
    )
    media = build_host_voice_media(settings)
    assert media is not None
    assert media.tts.agent_voices["todd"] == "ToddVoice"  # type: ignore[attr-defined]
    assert media.tts.agent_voices["morgana"] == "MorganaVoice"  # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_whisper_cpp_command_binds_portuguese_language_and_prompt(tmp_path: Path) -> None:
    model = tmp_path / "ggml-small.bin"
    model.write_bytes(b"model")
    args_file = tmp_path / "args.json"
    cli = tmp_path / "fake-whisper"
    cli.write_text(
        "#!/usr/bin/env python3\n"
        "import json,pathlib,sys\n"
        f"pathlib.Path({str(args_file)!r}).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n"
        "a=sys.argv[1:]\n"
        "prefix=pathlib.Path(a[a.index('-of')+1])\n"
        "prefix.with_suffix('.txt').write_text('Campanario, estou ouvindo.', encoding='utf-8')\n",
        encoding="utf-8",
    )
    cli.chmod(0o755)
    adapter = WhisperCppStt(
        str(cli), model, language="pt", prompt="Campanario Todd Morgana portugues"
    )
    result = await adapter.push(b"\x01\x00" * 4000, final=True)
    assert result is not None
    args = json.loads(args_file.read_text(encoding="utf-8"))
    assert args[args.index("-l") + 1] == "pt"
    assert args[args.index("--prompt") + 1] == "Campanario Todd Morgana portugues"
    assert "--no-timestamps" in args
    assert "--no-speech-thold" in args
    assert args[args.index("--temperature") + 1] == "0.00"
    assert args[args.index("--beam-size") + 1] == "5"
    assert "--no-fallback" in args
    assert "--suppress-nst" in args


def test_whisper_noise_only_annotations_do_not_become_user_turns() -> None:
    for value in ("[MÚSICA DE FUNDO]", "[MUSIC]", "(silêncio)", "[BLANK AUDIO]"):
        assert WhisperCppStt._clean_transcript(value) == ""
    assert WhisperCppStt._clean_transcript("tem música de fundo aqui") == "tem música de fundo aqui"


def test_probe_rejects_english_only_model_for_portuguese(tmp_path: Path) -> None:
    model = tmp_path / "ggml-base.en.bin"
    model.write_bytes(b"model")
    cli = tmp_path / "whisper-cli.exe"
    cli.write_bytes(b"x")
    settings = Settings(
        _env_file=None,
        voice_stt_backend="whisper_cpp",
        voice_tts_backend="unconfigured",
        voice_whisper_cpp_path=str(cli),
        voice_whisper_model_path=model,
        voice_language="pt",
    )
    probe = probe_host_voice(settings)
    assert probe.stt_ready is False
    assert any("English-only" in detail for detail in probe.details)


def test_voice_media_has_minimum_speech_gate(tmp_path: Path) -> None:
    model = tmp_path / "ggml-base.bin"
    model.write_bytes(b"model")
    settings = Settings(
        _env_file=None,
        voice_stt_backend="whisper_cpp",
        voice_tts_backend="unconfigured",
        voice_whisper_model_path=model,
        voice_min_speech_ms=240,
    )
    media = build_host_voice_media(settings)
    assert media is not None
    assert media.min_speech_ms == 240
    assert media.min_speech_bytes == 7680


def test_main_launcher_preserves_voice_host_extra() -> None:
    launcher = Path("tools/windows/INICIAR_CAMPANARIO.bat").read_text(encoding="utf-8")
    assert "uv sync --extra voice-host" in launcher
    assert "runtime-v2-pf8" not in launcher



def test_main_launcher_auto_wires_local_voice_assets_into_server_runtime() -> None:
    launcher = Path("tools/windows/INICIAR_CAMPANARIO.bat").read_text(encoding="utf-8")
    assert 'if exist "voice\\whisper-cli.exe" if defined VOICE_MODEL' in launcher
    assert 'set "CAMPANARIO_VOICE_STT_BACKEND=whisper_cpp"' in launcher
    assert 'set "CAMPANARIO_VOICE_TTS_BACKEND=windows_sapi"' in launcher
    assert 'set "CAMPANARIO_VOICE_WHISPER_CPP_PATH=%CD%\\voice\\whisper-cli.exe"' in launcher
    assert 'set "CAMPANARIO_VOICE_WHISPER_MODEL_PATH=!VOICE_MODEL!"' in launcher
    assert 'set "CAMPANARIO_VOICE_LANGUAGE=pt"' in launcher
    assert 'models\\ggml-small.bin' in launcher
    assert 'models\\ggml-base.bin' in launcher


def test_runtime_discovers_local_whisper_assets_even_with_fresh_unconfigured_env(tmp_path: Path, monkeypatch) -> None:
    voice = tmp_path / "voice"
    models = tmp_path / "models"
    voice.mkdir(); models.mkdir()
    cli = voice / "whisper-cli.exe"
    cli.write_bytes(b"exe")
    model = models / "ggml-base.bin"
    model.write_bytes(b"model")
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None)
    media = build_host_voice_media(settings)
    # On non-Windows test hosts STT discovery is still valid; TTS may remain disabled.
    assert media is not None
    assert media.stt_ready is True
    assert isinstance(media.stt, WhisperCppStt)
    assert media.stt.model_path == model.resolve()
    assert media.stt.language == "pt"


def test_main_launcher_searches_checkpoint_voice_model_layouts() -> None:
    launcher = Path("tools/windows/INICIAR_CAMPANARIO.bat").read_text(encoding="utf-8")
    assert "CAMPANARIO_VOICE_MODELS_DIR" in launcher
    assert "%LOCALAPPDATA%\\Campanario\\models" in launcher
    assert 'voice\\models\\ggml-base.bin' in launcher
    assert 'voice\\ggml-base.bin' in launcher




def test_runtime_prefers_external_voice_models_dir(tmp_path: Path) -> None:
    voice = tmp_path / "voice"
    external = tmp_path / "shared-models"
    voice.mkdir(); external.mkdir()
    (voice / "whisper-cli.exe").write_bytes(b"exe")
    external_model = external / "ggml-small.bin"
    external_model.write_bytes(b"model")
    settings = Settings(_env_file=None, voice_models_dir=external, voice_whisper_cpp_path=str(voice / "whisper-cli.exe"))
    media = build_host_voice_media(settings)
    assert media is not None
    assert media.stt_ready is True
    assert isinstance(media.stt, WhisperCppStt)
    assert media.stt.model_path == external_model.resolve()


def test_prepare_voice_installs_model_outside_project_by_default() -> None:
    prepare = Path("tools/windows/PREPARAR_VOZ_F5C.bat").read_text(encoding="utf-8")
    assert "CAMPANARIO_VOICE_MODELS_DIR" in prepare
    assert "%LOCALAPPDATA%\\Campanario\\models" in prepare
    assert 'set "MODEL=!MODELS_DIR!\\ggml-small.bin"' in prepare

def test_host_client_fatal_voice_readiness_errors_are_documented_as_terminal():
    source = Path("src/campanario/voice/host_client.py").read_text(encoding="utf-8")
    assert 'error_code in {"voice_stt_not_configured", "voice_tts_not_configured"}' in source
    assert "Host Voice encerrado" in source


def test_runtime_prefers_larger_multilingual_model_for_physical_ptbr(tmp_path: Path) -> None:
    voice = tmp_path / "voice"
    external = tmp_path / "shared-models"
    voice.mkdir(); external.mkdir()
    cli = voice / "whisper-cli.exe"
    cli.write_bytes(b"exe")
    (external / "ggml-small.bin").write_bytes(b"small")
    big = external / "ggml-big.bin"
    big.write_bytes(b"big")
    settings = Settings(
        _env_file=None,
        voice_models_dir=external,
        voice_whisper_cpp_path=str(cli),
        voice_whisper_prefer_accuracy=True,
    )
    media = build_host_voice_media(settings)
    assert media is not None
    assert isinstance(media.stt, WhisperCppStt)
    assert media.stt.model_path == big.resolve()


def test_main_launcher_prefers_big_before_small_for_f5_ptbr() -> None:
    launcher = Path("tools/windows/INICIAR_CAMPANARIO.bat").read_text(encoding="utf-8")
    big_pos = launcher.index('ggml-big.bin')
    small_pos = launcher.index('ggml-small.bin')
    assert big_pos < small_pos


def test_f5c10_incomplete_voice_fragment_detection_is_generic() -> None:
    from campanario.runtime.utterance import likely_incomplete_voice_fragment

    assert likely_incomplete_voice_fragment("Campanario.") is True
    assert likely_incomplete_voice_fragment("Reis de...") is True
    assert likely_incomplete_voice_fragment("Mais 49.") is True
    assert likely_incomplete_voice_fragment("Morgana, onde que é o lugar mais?") is True
    assert likely_incomplete_voice_fragment("Todd, calcula para mim 123.") is True
    assert likely_incomplete_voice_fragment("Campanario, qual a diferença de uma estrela para um planeta?") is False
    assert likely_incomplete_voice_fragment("E aí?") is False
    assert likely_incomplete_voice_fragment("Campanario, preciso de ajuda.") is False


def test_f5c10_pcm_join_removes_most_finalize_silence() -> None:
    from campanario.runtime.utterance import join_voice_pcm

    previous = b"a" * 64000
    current = b"b" * 16000
    joined = join_voice_pcm(previous, current, sample_rate=16000, channels=1, sample_width=2)
    # one second trimmed, 160 ms silence reinserted
    assert len(joined) == 32000 + 5120 + 16000
    assert joined.endswith(current)


def test_f5c10_fragment_grace_and_spoken_style_defaults() -> None:
    from campanario.runtime.voice import voice_turn_directives

    settings = Settings(_env_file=None)
    assert settings.voice_fragment_hold_ms == 1200
    note, _ = voice_turn_directives("qual a diferença entre isso e aquilo?")
    assert note is not None
    folded = note.casefold()
    assert "conversa por voz" in folded
    assert "uma ou duas frases" in folded


def test_f5c10_barge_in_defaults_favor_human_interruption() -> None:
    settings = Settings(_env_file=None)
    assert settings.voice_barge_in_threshold == 1600
    assert settings.voice_barge_in_frames == 2
    assert settings.voice_barge_in_preroll_frames == 6
