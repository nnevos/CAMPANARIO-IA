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
    model_temperature: float = Field(default=0.55, ge=0.0, le=2.0)
    # Low latency is opt-in for existing callers; the packaged Windows profile enables it.
    model_think: bool | None = False
    model_context_window: int = Field(default=4096, ge=1024, le=131072)
    model_max_output_tokens: int = Field(default=320, ge=16, le=8192)
    model_keep_alive: str = "20m"
    low_latency_mode: bool = True
    live_streaming: bool = True
    context_auto_summarize: bool = False
    participation_arbiter_enabled: bool = False
    # Local chat may consult public internet on ordinary factual questions. Disable to stay offline.
    web_auto_search: bool = False
    # When web access is authorized, try public sources first, then local ZIM
    # and imported documents. Offline requests keep the legacy local-first order.
    research_priority: str = Field(default='web_first', pattern=r'^(web_first|local_first)$')

    # Legacy aliases kept for existing .env files. Generic values above take precedence when set.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 120.0
    ollama_temperature: float = Field(default=0.35, ge=0.0, le=2.0)

    context_max_messages: int = Field(default=20, ge=1)
    context_summary_max_chars: int = Field(default=4000, ge=500, le=20000)
    data_dir: Path = Field(default_factory=lambda: user_data_path("Campanario", appauthor=False))
    # No automatic directory movement. Set CAMPANARIO_DATA_DIR in the local .env after verified copy.
    # Optional archive directory for future offline Kiwix/ZIM integration.
    zim_dir: Path | None = None
    # Wikipedia in a local ZIM, served by a separately installed kiwix-serve.
    # OFF by default, no internet; the desktop starts a local process only if enabled.
    zim_enabled: bool = False
    # Desktop only: start the local Kiwix service with no console window.
    # Disable explicitly to use a manually managed server.
    zim_auto_start: bool = True
    zim_base_url: str = 'http://127.0.0.1:8181'
    zim_book_name: str = ''  # optional explicit book name when different from filename
    zim_timeout_seconds: float = Field(default=3.0, ge=0.5, le=8.0)
    # Explicitly isolate test history from the eventual Point Zero production history.
    memory_environment: str = Field(default="desenvolvimento", pattern=r"^(desenvolvimento|producao)$")

    # Fase 4 Inc.3B: optional read-only semantic document candidates.
    # Default OFF until a real Windows+embeddinggemma benchmark is reviewed.
    # Different from personal-memory semantic embeddings; no persistent index.
    library_semantic_enabled: bool = False
    library_semantic_model: str = 'embeddinggemma'
    library_semantic_timeout_seconds: float = Field(default=5.0, ge=1.0, le=20.0)
    library_semantic_min_similarity: float = Field(default=0.72, ge=0.0, le=1.0)
    library_semantic_max_segments: int = Field(default=96, ge=8, le=256)

    # G2: local Ollama embeddings + SQLite index, no Qwen chat call for retrieval.
    # Install once: ollama pull embeddinggemma. When unavailable, lexical search remains.
    semantic_memory_enabled: bool = True
    semantic_memory_backend: str = "memoryllm_chroma"  # memoryllm_chroma | sqlite
    semantic_memory_model: str = "embeddinggemma"
    semantic_memory_timeout_seconds: float = Field(default=7.0, ge=1.0, le=60.0)
    semantic_memory_min_similarity: float = Field(default=0.43, ge=0.0, le=1.0)
    semantic_memory_batch_size: int = Field(default=32, ge=1, le=64)


    # Optional providers are not installed or started by the desktop launcher.
    update_repository: str = ""
    desktop_port: int = Field(default=8000, ge=1024, le=65535)

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
            if self.model_temperature in (0.35, 0.55) and self.ollama_temperature != 0.35:
                temperature = self.ollama_temperature
        return ModelRuntimeConfig(
            backend=self.model_provider,
            model=self.effective_model_name,
            base_url=base_url,
            timeout_seconds=timeout,
            temperature=temperature,
            think=self.model_think,
            context_window=self.model_context_window,
            max_output_tokens=self.model_max_output_tokens,
            keep_alive=self.model_keep_alive,
        )

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.memory_environment / "campanario.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
