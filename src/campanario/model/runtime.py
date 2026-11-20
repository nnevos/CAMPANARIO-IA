from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.protocol import ModelProvider


class ModelBackend(StrEnum):
    OLLAMA = "ollama"


@dataclass(frozen=True, slots=True)
class ModelRuntimeConfig:
    backend: ModelBackend
    model: str
    base_url: str
    timeout_seconds: float = 120.0
    temperature: float = 0.35
    think: bool | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    keep_alive: str | None = None


class UnsupportedModelBackendError(ValueError):
    pass


def build_model_provider(config: ModelRuntimeConfig) -> ModelProvider:
    """Build only the raw model adapter.

    Campanario behavior, prompt safety, response contracts and memory stay outside this factory.
    Adding a future backend should require a new adapter plus one factory branch, not changes to chat.
    """
    if config.backend == ModelBackend.OLLAMA:
        return OllamaProvider(
            config.base_url,
            config.timeout_seconds,
            temperature=config.temperature,
            think=config.think,
            context_window=config.context_window,
            max_output_tokens=config.max_output_tokens,
            keep_alive=config.keep_alive,
        )
    raise UnsupportedModelBackendError(f"Unsupported model backend: {config.backend}")
