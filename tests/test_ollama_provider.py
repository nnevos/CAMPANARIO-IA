from campanario.chat.models import MessageRole
from campanario.model.adapters.ollama import OllamaProvider
from campanario.model.protocol import ModelMessage, ModelRequest


def test_ollama_payload_includes_configured_temperature() -> None:
    provider = OllamaProvider("http://127.0.0.1:11434", temperature=0.35)
    request = ModelRequest(
        model="llama3:latest",
        messages=(ModelMessage(role=MessageRole.USER, content="oi"),),
    )

    payload = provider._build_payload(request, stream=True)

    assert payload["stream"] is True
    assert payload["options"] == {"temperature": 0.35}
    assert payload["messages"] == [{"role": "user", "content": "oi"}]
