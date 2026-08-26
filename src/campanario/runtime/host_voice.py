from __future__ import annotations

import asyncio
import io
import os
import re
import shutil
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from campanario.runtime.media import EnergyVad, PcmFormat, VoiceMediaRuntime
from campanario.runtime.voice import SttSegment, TtsChunk


@dataclass(frozen=True, slots=True)
class HostVoiceProbe:
    stt_backend: str
    stt_ready: bool
    tts_backend: str
    tts_ready: bool
    audio_backend_ready: bool
    details: tuple[str, ...] = ()


class WhisperCppStt:
    """Local whisper.cpp adapter.

    The gateway supplies the complete PCM utterance on ``final=True``. Partial pushes are ignored
    by this baseline adapter so no audio is duplicated. A streaming whisper implementation can
    replace this adapter later without touching Conversation Runtime.
    """

    def __init__(
        self,
        executable: str,
        model_path: str | Path,
        *,
        language: str = "pt",
        pcm: PcmFormat = PcmFormat(),
        timeout_seconds: float = 45.0,
        prompt: str = "",
        no_speech_threshold: float = 0.60,
    ) -> None:
        self.executable = str(executable)
        self.model_path = Path(model_path)
        self.language = language
        self.pcm = pcm
        self.timeout_seconds = timeout_seconds
        self.prompt = prompt.strip()
        self.no_speech_threshold = max(0.0, min(1.0, float(no_speech_threshold)))

    async def push(self, audio: bytes, *, final: bool = False) -> SttSegment | None:
        if not final:
            return None
        if not audio:
            return None
        text = await asyncio.to_thread(self._transcribe_sync, audio)
        text = self._clean_transcript(text)
        if not text:
            return None
        return SttSegment(text=text, final=True, confidence=None)

    async def reset(self) -> None:
        return None

    def _transcribe_sync(self, audio: bytes) -> str:
        import subprocess

        if not self.model_path.exists():
            raise RuntimeError(f"whisper.cpp model not found: {self.model_path}")
        executable = shutil.which(self.executable) or self.executable
        with tempfile.TemporaryDirectory(prefix="campanario-stt-") as directory:
            root = Path(directory)
            wav_path = root / "utterance.wav"
            output_prefix = root / "transcript"
            with wave.open(str(wav_path), "wb") as handle:
                handle.setnchannels(self.pcm.channels)
                handle.setsampwidth(self.pcm.sample_width)
                handle.setframerate(self.pcm.sample_rate)
                handle.writeframes(audio)
            command = [
                executable,
                "-m",
                str(self.model_path),
                "-f",
                str(wav_path),
                "-l",
                self.language,
                "--no-timestamps",
                "--no-speech-thold",
                f"{self.no_speech_threshold:.2f}",
                "--temperature",
                "0.00",
                "--beam-size",
                "5",
                "--no-fallback",
                "--suppress-nst",
            ]
            if self.prompt:
                command.extend(["--prompt", self.prompt])
            command.extend([
                "-otxt",
                "-of",
                str(output_prefix),
            ])
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
            transcript_path = output_prefix.with_suffix(".txt")
            if completed.returncode != 0:
                stderr = (completed.stderr or completed.stdout or "").strip()
                raise RuntimeError(f"whisper.cpp failed ({completed.returncode}): {stderr[-600:]}")
            if transcript_path.exists():
                return transcript_path.read_text(encoding="utf-8", errors="replace")
            return completed.stdout or ""

    @staticmethod
    def _clean_transcript(text: str) -> str:
        value = " ".join(text.replace("\ufeff", "").split()).strip()
        if not value:
            return ""
        # whisper.cpp can emit non-speech annotations as if they were user turns.
        # Drop them only when the whole transcript is an annotation, never when real speech exists.
        annotation = value.casefold().strip(" .!?,;:")
        annotation = re.sub(r"^[\[\(]+|[\]\)]+$", "", annotation).strip()
        non_speech = {
            "musica", "música", "musica de fundo", "música de fundo", "music",
            "background music", "blank audio", "silencio", "silêncio", "silence",
            "inaudivel", "inaudível", "unintelligible", "aplausos", "applause",
        }
        if annotation in non_speech:
            return ""
        return value


class WindowsSapiTts:
    """Local Windows SAPI synthesis with per-agent voice/rate selection.

    Output is WAV bytes so the host client can play it on the selected speaker. ``cancel`` kills
    the active PowerShell synthesis process, making barge-in observable at the media boundary.
    """

    def __init__(
        self,
        *,
        powershell_path: str = "powershell.exe",
        agent_voices: Mapping[str, str] | None = None,
        agent_rates: Mapping[str, int] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.powershell_path = powershell_path
        self.agent_voices = dict(agent_voices or {})
        self.agent_rates = {"todd": 4, "morgana": 3, **dict(agent_rates or {})}
        self.timeout_seconds = timeout_seconds
        self._active: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def synthesize(self, text: str, *, agent_id: str):
        if os.name != "nt":
            raise RuntimeError("Windows SAPI TTS is only available on Windows")
        with tempfile.TemporaryDirectory(prefix="campanario-tts-") as directory:
            root = Path(directory)
            text_path = root / "speech.txt"
            wav_path = root / "speech.wav"
            text_path.write_text(text, encoding="utf-8")
            voice = self.agent_voices.get(agent_id, "")
            rate = max(-10, min(10, int(self.agent_rates.get(agent_id, 0))))
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$voice={self._ps_quote(voice)}; "
                "if ($voice) { $s.SelectVoice($voice) }; "
                f"$s.Rate={rate}; "
                f"$s.SetOutputToWaveFile({self._ps_quote(str(wav_path))}); "
                f"$t=[IO.File]::ReadAllText({self._ps_quote(str(text_path))}, [Text.Encoding]::UTF8); "
                "$s.Speak($t); $s.Dispose();"
            )
            async with self._lock:
                process = await asyncio.create_subprocess_exec(
                    self.powershell_path,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                self._active = process
            try:
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout_seconds)
            except asyncio.TimeoutError as exc:
                process.kill()
                await process.wait()
                raise RuntimeError("Windows SAPI TTS timed out") from exc
            finally:
                async with self._lock:
                    if self._active is process:
                        self._active = None
            if process.returncode != 0:
                raise RuntimeError(f"Windows SAPI TTS failed: {(stderr or b'').decode(errors='replace')[-600:]}")
            audio = wav_path.read_bytes()
            yield TtsChunk(agent_id=agent_id, audio=audio, final=True, audio_format="wav")

    async def cancel(self) -> None:
        async with self._lock:
            process = self._active
        if process is not None and process.returncode is None:
            process.kill()
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pass

    @staticmethod
    def _ps_quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"


class UnconfiguredHostTts:
    async def synthesize(self, text: str, *, agent_id: str):
        raise RuntimeError("host TTS backend is not configured")
        yield TtsChunk(agent_id=agent_id, audio=b"", final=True)

    async def cancel(self) -> None:
        return None


class UnconfiguredHostStt:
    async def push(self, audio: bytes, *, final: bool = False) -> SttSegment | None:
        raise RuntimeError("host STT backend is not configured")

    async def reset(self) -> None:
        return None


def _discover_local_whisper_assets(settings, root: Path | None = None) -> tuple[str | None, Path | None]:
    """Resolve local whisper.cpp assets without coupling callers to one extraction layout.

    Explicit settings win.  For the Windows development host we then recognize the layouts used
    throughout F5c checkpoints (``voice/`` and ``models/``).  No downloads or provider setup happen
    here; discovery is intentionally local and deterministic.
    """
    root = (root or Path.cwd()).resolve()
    configured_exe = settings.voice_whisper_cpp_path.strip()
    exe_candidate = shutil.which(configured_exe) if configured_exe else None
    if exe_candidate is None and configured_exe:
        path = Path(configured_exe)
        if path.exists():
            exe_candidate = str(path.resolve())
    if exe_candidate is None:
        for candidate in (root / "voice" / "whisper-cli.exe", root / "whisper-cli.exe"):
            if candidate.exists():
                exe_candidate = str(candidate.resolve())
                break

    configured_model = settings.voice_whisper_model_path
    model_candidate = configured_model.resolve() if configured_model and configured_model.exists() else None
    if model_candidate is None:
        external_dir = settings.voice_models_dir
        if external_dir:
            external_dir = external_dir.expanduser().resolve()
        legacy_dirs = (root / "models", root / "voice" / "models", root / "voice")
        search_dirs = ((external_dir,) if external_dir else ()) + legacy_dirs
        discovered: list[Path] = []
        for directory in search_dirs:
            if directory and directory.exists():
                discovered.extend(item for item in directory.glob("ggml*.bin") if ".en." not in item.name.lower())

        def model_rank(item: Path) -> tuple[int, str]:
            name = item.name.lower()
            if settings.voice_whisper_prefer_accuracy:
                order = ("large-v3", "large", "big", "medium", "small", "base", "tiny")
            else:
                order = ("small", "base", "medium", "large-v3", "large", "big", "tiny")
            for index, token in enumerate(order):
                if token in name:
                    return index, name
            return len(order), name

        model_candidate = min(discovered, key=model_rank).resolve() if discovered else None
    return exe_candidate, model_candidate


def build_host_voice_media(settings) -> VoiceMediaRuntime | None:
    stt_backend = settings.voice_stt_backend.strip().lower()
    tts_backend = settings.voice_tts_backend.strip().lower()
    whisper_exe, whisper_model = _discover_local_whisper_assets(settings)

    # A local Windows checkout with whisper.cpp + a multilingual model is enough to make the
    # runtime voice-ready.  This keeps the API/runtime boundary correct even when a fresh .env
    # still contains the conservative ``unconfigured`` defaults.
    if stt_backend in {"", "none", "unconfigured"} and whisper_exe and whisper_model:
        stt_backend = "whisper_cpp"
    if tts_backend in {"", "none", "unconfigured"} and os.name == "nt":
        tts_backend = "windows_sapi"

    if stt_backend in {"", "none", "unconfigured"} and tts_backend in {"", "none", "unconfigured"}:
        return None

    if stt_backend == "whisper_cpp":
        # Explicit backend configuration may intentionally point to an executable available only
        # on the target host/PATH.  Keep that boundary constructible; auto-discovery itself still
        # requires concrete local assets before enabling STT from fresh defaults.
        whisper_exe = whisper_exe or settings.voice_whisper_cpp_path.strip() or "whisper-cli.exe"
        if not whisper_model:
            raise RuntimeError("whisper.cpp multilingual model not found; expected a multilingual ggml model in CAMPANARIO_VOICE_MODELS_DIR, models, or voice\\models")
        if ".en." in whisper_model.name.lower() and settings.voice_language.strip().lower() not in {"en", "english"}:
            raise RuntimeError("English-only whisper model cannot be used with Portuguese; use ggml-small.bin or ggml-base.bin")
        stt = WhisperCppStt(
            whisper_exe,
            whisper_model,
            language=settings.voice_language,
            timeout_seconds=settings.voice_stt_timeout_seconds,
            prompt=settings.voice_whisper_prompt,
            no_speech_threshold=settings.voice_whisper_no_speech_threshold,
        )
        stt_ready = True
    else:
        stt = UnconfiguredHostStt()
        stt_ready = False

    if tts_backend == "windows_sapi":
        tts = WindowsSapiTts(
            powershell_path=settings.voice_powershell_path,
            agent_voices={
                "todd": settings.voice_todd_voice,
                "morgana": settings.voice_morgana_voice,
            },
            agent_rates={
                "todd": settings.voice_todd_rate,
                "morgana": settings.voice_morgana_rate,
            },
            timeout_seconds=settings.voice_tts_timeout_seconds,
        )
        tts_ready = True
    else:
        tts = UnconfiguredHostTts()
        tts_ready = False

    return VoiceMediaRuntime(
        stt=stt,
        tts=tts,
        vad=EnergyVad(threshold=settings.voice_vad_threshold),
        silence_frames_to_finalize=settings.voice_silence_frames_to_finalize,
        preroll_frames=settings.voice_preroll_frames,
        min_speech_ms=settings.voice_min_speech_ms,
        fragment_hold_ms=settings.voice_fragment_hold_ms,
        stt_ready=stt_ready,
        tts_ready=tts_ready,
    )


def probe_host_voice(settings) -> HostVoiceProbe:
    details: list[str] = []
    stt_backend = settings.voice_stt_backend.strip().lower()
    tts_backend = settings.voice_tts_backend.strip().lower()

    stt_ready = False
    if stt_backend == "whisper_cpp":
        discovered_exe, discovered_model = _discover_local_whisper_assets(settings)
        executable = discovered_exe or shutil.which(settings.voice_whisper_cpp_path) or Path(settings.voice_whisper_cpp_path)
        exe_ok = bool(executable and Path(executable).exists())
        model_path = discovered_model
        model_ok = bool(model_path and model_path.exists())
        language = settings.voice_language.strip().lower() or "auto"
        english_only = bool(model_path and ".en." in model_path.name.lower())
        language_model_ok = not (english_only and language not in {"en", "english"})
        stt_ready = exe_ok and model_ok and language_model_ok
        details.append(f"whisper.cpp executable={'ok' if exe_ok else 'missing'}")
        details.append(f"whisper.cpp model={'ok' if model_ok else 'missing'} ({model_path.name if model_path else 'unset'})")
        details.append(f"whisper.cpp language={language}")
        details.append(f"whisper.cpp prompt={'configured' if settings.voice_whisper_prompt.strip() else 'empty'}")
        details.append(f"whisper.cpp multilingual={'no (.en model)' if english_only else 'yes/unknown'}")
        details.append(f"whisper.cpp quality_preference={'accuracy' if settings.voice_whisper_prefer_accuracy else 'balanced'}")
        if not language_model_ok:
            details.append("ERROR: English-only whisper model cannot be used with non-English language")
    else:
        details.append("STT backend is not whisper_cpp")

    tts_ready = False
    if tts_backend == "windows_sapi":
        tts_ready = os.name == "nt" and bool(shutil.which(settings.voice_powershell_path) or Path(settings.voice_powershell_path).exists())
        details.append(f"Windows SAPI/PowerShell={'ok' if tts_ready else 'unavailable'}")
    else:
        details.append("TTS backend is not windows_sapi")

    try:
        import sounddevice  # noqa: F401
        audio_ready = True
    except Exception:
        audio_ready = False
    details.append(f"sounddevice={'ok' if audio_ready else 'missing'}")
    return HostVoiceProbe(stt_backend, stt_ready, tts_backend, tts_ready, audio_ready, tuple(details))
