from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from campanario.model.runtime import ModelBackend, ModelRuntimeConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CAMPANARIO_",
        extra="ignore",
    )

    log_level: str = "INFO"

    # Generic model runtime configuration. Behavior must not depend on a model family.
    model_provider: ModelBackend = ModelBackend.OLLAMA
    model_name: str = ""
    model_base_url: str = "http://127.0.0.1:11434"
    model_timeout_seconds: float = 120.0
    model_temperature: float = Field(default=0.35, ge=0.0, le=2.0)

    # Legacy aliases kept for existing .env files. Generic values above take precedence when set.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 120.0
    ollama_temperature: float = Field(default=0.35, ge=0.0, le=2.0)

    context_max_messages: int = Field(default=20, ge=1)
    context_summary_max_chars: int = Field(default=4000, ge=500, le=20000)
    data_dir: Path = Field(default_factory=lambda: user_data_path("Campanario", appauthor=False))

    # F5c host voice integration. Defaults stay disabled so server startup never pretends that
    # microphone/STT/TTS are ready. The Windows target baseline is whisper.cpp + local SAPI.
    voice_stt_backend: str = "unconfigured"
    voice_tts_backend: str = "unconfigured"
    voice_whisper_cpp_path: str = "whisper-cli.exe"
    voice_whisper_model_path: Path | None = None
    # Optional external model store. Keeps multi-hundred-MB Whisper weights outside project handoffs.
    voice_models_dir: Path | None = None
    voice_language: str = "pt"
    voice_whisper_prompt: str = "Campanario. Todd. Morgana."
    voice_whisper_no_speech_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    # Physical F5 pt-BR favors recognition quality when multiple local weights are available.
    voice_whisper_prefer_accuracy: bool = True
    voice_powershell_path: str = "powershell.exe"
    voice_todd_voice: str = ""
    voice_morgana_voice: str = ""
    voice_todd_rate: int = Field(default=4, ge=-10, le=10)
    voice_morgana_rate: int = Field(default=3, ge=-10, le=10)
    voice_vad_threshold: int = Field(default=450, ge=1, le=32767)
    voice_silence_frames_to_finalize: int = Field(default=45, ge=1, le=100)
    voice_preroll_frames: int = Field(default=6, ge=0, le=25)
    voice_min_speech_ms: int = Field(default=300, ge=80, le=5000)
    # Short grace window only for STT fragments that look linguistically unfinished.
    voice_fragment_hold_ms: int = Field(default=1200, ge=0, le=4000)
    voice_stt_timeout_seconds: float = Field(default=45.0, gt=0)
    voice_tts_timeout_seconds: float = Field(default=30.0, gt=0)
    voice_barge_in_threshold: int = Field(default=1600, ge=100, le=32767)
    voice_barge_in_frames: int = Field(default=2, ge=1, le=10)
    voice_barge_in_preroll_frames: int = Field(default=6, ge=1, le=25)

    @property
    def effective_model_name(self) -> str:
        return self.model_name.strip() or self.ollama_model.strip()

    @property
    def model_runtime(self) -> ModelRuntimeConfig:
        # Ollama legacy URL/options are honored only when generic fields are still defaults.
        base_url = self.model_base_url
        timeout = self.model_timeout_seconds
        temperature = self.model_temperature
        if self.model_provider == ModelBackend.OLLAMA:
            if self.model_base_url == "http://127.0.0.1:11434" and self.ollama_base_url != self.model_base_url:
                base_url = self.ollama_base_url
            if self.model_timeout_seconds == 120.0 and self.ollama_timeout_seconds != 120.0:
                timeout = self.ollama_timeout_seconds
            if self.model_temperature == 0.35 and self.ollama_temperature != 0.35:
                temperature = self.ollama_temperature
        return ModelRuntimeConfig(
            backend=self.model_provider,
            model=self.effective_model_name,
            base_url=base_url,
            timeout_seconds=timeout,
            temperature=temperature,
        )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "campanario.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
