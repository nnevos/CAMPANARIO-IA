"""Local optional speech adapters. No audio is stored by this module."""
import io
import re
import html
import unicodedata
import json
import subprocess
import shutil
import tempfile
from pathlib import Path
import os
import threading
import sys
import wave
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/voice")
_CONFIG_PATH = Path(os.getenv("CAMPANARIO_VOICE_CONFIG", str(Path.home() / ".campanario" / "voice26.json")))
_CONFIG_LOCK = threading.RLock()
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULTS = {
    "morgana": {"engine": "piper", "language": "pt_BR", "model_path": str(_PROJECT_ROOT / "vozes" / "dii_pt-BR.onnx")},
    "todd": {"engine": "piper", "language": "pt_BR", "model_path": str(_PROJECT_ROOT / "vozes" / "pt-BR-razo-medium.onnx")},
}

def _piper_executable():
    """Find Piper in the running Python environment, even if Scripts is not on PATH."""
    candidates = [os.getenv("CAMPANARIO_PIPER_EXE", "").strip()]
    scripts = Path(sys.executable).resolve().parent
    candidates.extend([str(scripts / "piper.exe"), str(scripts / "piper")])
    # In some launchers sys.executable is outside the project virtualenv.
    candidates.extend([str(_PROJECT_ROOT / ".venv" / "Scripts" / "piper.exe"),
                       str(_PROJECT_ROOT / ".venv" / "bin" / "piper")])
    candidates.append(shutil.which("piper") or "")
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    return None


def _settings():
    with _CONFIG_LOCK:
        try:
            raw = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            raw = {}
        result = {}
        for agent, defaults in _DEFAULTS.items():
            supplied = raw.get(agent, {}) if isinstance(raw, dict) else {}
            result[agent] = {**defaults, **{k: v for k, v in supplied.items() if k in defaults and isinstance(v, str)}} if isinstance(supplied, dict) else defaults.copy()
        return result

def _save_settings(settings):
    with _CONFIG_LOCK:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(_CONFIG_PATH)

@lru_cache(maxsize=1)
def _xtts_model():
    from TTS.api import TTS
    # The XTTS model is cached across calls. A voice sample is supplied per agent.
    import torch
    return TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda" if torch.cuda.is_available() else "cpu")

def _wav_from_xtts(text, speaker_wav):
    if not speaker_wav or not Path(speaker_wav).is_file():
        raise HTTPException(422, "XTTS: configure um arquivo WAV de referencia para Morgana nas configuracoes de voz")
    import soundfile as sf
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "voice.wav"
        _xtts_model().tts_to_file(text=text, speaker_wav=speaker_wav, language="pt", file_path=str(output))
        return output.read_bytes()

@lru_cache(maxsize=2)
def _piper_voice(model_path: str):
    """Load each Piper ONNX voice once; synthesis uses Unicode directly."""
    from piper.voice import PiperVoice
    return PiperVoice.load(model_path)


def _wav_from_piper(text, model_path):
    if not model_path or not Path(model_path).is_file() or Path(model_path).suffix.lower() != ".onnx":
        raise HTTPException(422, "Piper: configure um modelo .onnx para este agente nas configuracoes de voz")
    if not Path(str(model_path) + ".json").is_file():
        raise HTTPException(422, "Piper: falta o arquivo .onnx.json ao lado do modelo")
    # The Piper CLI can mishandle accented input on Windows. The Python API
    # receives the original Unicode string, as verified in a direct voice test.
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        _piper_voice(str(Path(model_path).resolve())).synthesize_wav(text, wav)
    return output.getvalue()

class VoiceSettings(BaseModel):
    agent: str
    engine: str
    speaker_wav: str = ""
    model_path: str = ""

@router.get("/voices")
def voices():
    settings = _settings()
    return {"agents": settings, "engines": ["xtts", "piper", "pocket"], "xtts_installed": __import__("importlib").util.find_spec("TTS") is not None, "piper_installed": __import__("importlib").util.find_spec("piper") is not None}

@router.post("/voices")
def set_voices(payload: VoiceSettings):
    if payload.agent not in _DEFAULTS or payload.engine not in {"xtts", "piper", "pocket"}:
        raise HTTPException(422, "Agente ou motor desconhecido")
    if len(payload.speaker_wav) > 1024 or len(payload.model_path) > 1024:
        raise HTTPException(422, "Caminho muito longo")
    settings = _settings()
    settings[payload.agent] = {**_DEFAULTS[payload.agent], "engine": payload.engine, "speaker_wav": payload.speaker_wav.strip(), "model_path": payload.model_path.strip()}
    _save_settings(settings)
    return {"agents": settings}

_lock = threading.Lock()


@lru_cache(maxsize=1)
def _stt_model():
    from faster_whisper import WhisperModel
    size = os.getenv("CAMPANARIO_STT_MODEL", "turbo")
    device = os.getenv("CAMPANARIO_STT_DEVICE", "auto")
    compute = os.getenv("CAMPANARIO_STT_COMPUTE", "default")
    return WhisperModel(size, device=device, compute_type=compute)


@lru_cache(maxsize=1)
def _tts_model():
    from pocket_tts import TTSModel
    return TTSModel.load_model()


@lru_cache(maxsize=2)
def _voice_state(agent: str):
    model = _tts_model()
    voice = os.getenv("CAMPANARIO_VOICE_" + agent.upper(), "alba" if agent == "morgana" else "marius")
    return model.get_state_for_audio_prompt(voice)


@router.get("/status")
def status():
    import importlib.util
    return {"stt_installed": importlib.util.find_spec("faster_whisper") is not None,
            "tts_installed": importlib.util.find_spec("pocket_tts") is not None,
            "stt_model": os.getenv("CAMPANARIO_STT_MODEL", "turbo"),
            "audio_local_only": True}


@router.post("/transcribe")
async def transcribe(request: Request):
    # Browser records audio locally and sends it to this loopback-only API.
    content_type = request.headers.get("content-type", "")
    if not any(x in content_type for x in ("audio/", "application/octet-stream")):
        raise HTTPException(415, "Formato de audio nao suportado")
    length = request.headers.get("content-length")
    if length and int(length) > 8_000_000:
        raise HTTPException(413, "Audio excede 8 MB")
    data = await request.body()
    if not data or len(data) > 8_000_000:
        raise HTTPException(413, "Audio vazio ou acima de 8 MB")
    import tempfile
    from pathlib import Path
    suffix = ".webm" if "webm" in content_type else ".wav" if "wav" in content_type else ".ogg"
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            path = Path(f.name)
            f.write(data)
        try:
            with _lock:
                segments, _ = _stt_model().transcribe(str(path), language="pt", vad_filter=True, beam_size=1)
                text = " ".join(s.text.strip() for s in segments).strip()
        except (ImportError, ModuleNotFoundError) as exc:
            raise HTTPException(503, "Instale faster-whisper para ativar STT") from exc
        except Exception as exc:
            raise HTTPException(503, "STT indisponivel; verifique FFmpeg/modelo e logs") from exc
        return {"text": text, "language": "pt"}
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def _speech_text(raw: str) -> str:
    """Convert chat Markdown/HTML into readable speech, retaining Portuguese accents."""
    text = html.unescape(raw or "")
    text = re.sub(r"```[\s\S]*?```", " código omitido. ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", " link ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*>\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)
    text = re.sub(r"[*_~|#]", "", text)
    # Remove nonverbal pictographs/control characters, not Portuguese letters.
    text = "".join(c for c in text if c in "\n\t" or (unicodedata.category(c)[0] not in "CS" and not (0x1F000 <= ord(c) <= 0x1FAFF) and not (0x2600 <= ord(c) <= 0x27BF)))
    text = re.sub(r"\s+", " ", text).strip()
    return text


class SpeakRequest(BaseModel):
    agent: str
    text: str = Field(min_length=1, max_length=1200)


@router.post("/preview")
def preview(payload: SpeakRequest):
    return speak(payload)

@router.post("/speak")
def speak(payload: SpeakRequest):
    if payload.agent not in {"morgana", "todd"}:
        raise HTTPException(422, "Agente desconhecido")
    clean_text = _speech_text(payload.text)
    if not clean_text:
        raise HTTPException(422, "Nenhum texto pronunciavel para gerar audio")
    engine_settings = _settings()[payload.agent]
    engine = engine_settings["engine"]
    try:
        # Do not run concurrent synthesizers on a shared GPU/model instance.
        with _lock:
            if engine == "xtts":
                data = _wav_from_xtts(clean_text, engine_settings.get("speaker_wav", ""))
            elif engine == "piper":
                data = _wav_from_piper(clean_text, engine_settings.get("model_path", ""))
            else:
                import numpy as np
                model = _tts_model()
                audio = model.generate_audio(_voice_state(payload.agent), clean_text)
                samples = audio.detach().cpu().numpy() if hasattr(audio, "detach") else audio.numpy()
                samples = np.clip(samples, -1.0, 1.0)
                output = io.BytesIO()
                with wave.open(output, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(model.sample_rate)
                    wav.writeframes((samples * 32767).astype("<i2").tobytes())
                data = output.getvalue()
        return Response(data, media_type="audio/wav", headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except (ImportError, ModuleNotFoundError) as exc:
        raise HTTPException(503, f"Motor {engine} nao instalado no Python do Campanario") from exc
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Falha TTS (%s)", engine)
        raise HTTPException(503, f"TTS {engine} indisponivel; consulte os logs") from exc
