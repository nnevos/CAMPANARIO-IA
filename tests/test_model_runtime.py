from campanario.config import Settings
from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.runtime import ModelBackend, ModelRuntimeConfig, build_model_provider


def test_generic_model_runtime_builds_ollama_adapter() -> None:
    config = ModelRuntimeConfig(
        backend=ModelBackend.OLLAMA,
        model="qwen3:8b",
        base_url="http://127.0.0.1:11434",
        timeout_seconds=90,
        temperature=0.2,
    )
    provider = build_model_provider(config)
    assert isinstance(provider, OllamaProvider)


def test_settings_generic_model_name_overrides_legacy_alias(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        model_provider="ollama",
        model_name="qwen3:8b",
        ollama_model="llama3:latest",
    )
    assert settings.effective_model_name == "qwen3:8b"
    assert settings.model_runtime.model == "qwen3:8b"


def test_settings_legacy_ollama_model_still_works(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path, model_name="", ollama_model="llama3:latest")
    assert settings.effective_model_name == "llama3:latest"
