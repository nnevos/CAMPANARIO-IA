from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CAMPANARIO_",
        extra="ignore",
    )

    log_level: str = "INFO"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 120.0
    data_dir: Path = Field(default_factory=lambda: user_data_path("Campanario", appauthor=False))

    @property
    def database_path(self) -> Path:
        return self.data_dir / "campanario.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
