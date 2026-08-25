from campanario.model.protocol import FakeModelProvider, ModelRequest
from campanario.model.runtime import ModelBackend, ModelRuntimeConfig, build_model_provider
from campanario.response.contract import ResponseKind
from campanario.response.pipeline import ResponseContractPipeline


def test_canonical_model_and_response_packages_import():
    assert FakeModelProvider is not None
    assert ModelRequest is not None
    assert ResponseKind.OPEN.value == "open"
    assert ResponseContractPipeline is not None


def test_legacy_llm_package_is_removed_after_pre_agent_cleanup():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert not (root / "src" / "campanario" / "llm").exists()


def test_ollama_model_family_is_configuration_not_behavior():
    qwen = ModelRuntimeConfig(ModelBackend.OLLAMA, "qwen-any-tag", "http://127.0.0.1:11434")
    gemma = ModelRuntimeConfig(ModelBackend.OLLAMA, "gemma-any-tag", "http://127.0.0.1:11434")
    assert type(build_model_provider(qwen)) is type(build_model_provider(gemma))


def test_model_bakeoff_module_imports():
    from campanario.e2e.model_bakeoff import ModelResult
    assert ModelResult("x", 0, "PASS").model == "x"


def test_chat_behavior_is_split_by_responsibility():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    chat = root / "src" / "campanario" / "chat"
    for name in ("prompts.py", "turns.py", "audit.py", "provenance.py", "behavior.py"):
        assert (chat / name).exists()
    assert len((chat / "behavior.py").read_text(encoding="utf-8").splitlines()) < 150
