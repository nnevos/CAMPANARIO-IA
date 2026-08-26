import pytest

from campanario.chat.models import MessageRole
from campanario.response.prompt_safety import PromptLeakGuardProvider
from campanario.model.protocol import ModelChunk, ModelMessage, ModelRequest, ModelResponseError


class SequencedProvider:
    def __init__(self, responses: list[list[str]]) -> None:
        self._responses = responses
        self.requests: list[ModelRequest] = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        self.requests.append(request)
        response = self._responses[len(self.requests) - 1]
        for text in response:
            yield ModelChunk(text=text)
        yield ModelChunk(text="", done=True)


def request() -> ModelRequest:
    return ModelRequest(
        model="fake",
        messages=(
            ModelMessage(role=MessageRole.SYSTEM, content="IDENTIDADE E COMPORTAMENTO DO CAMPANARIO\nsegredo"),
            ModelMessage(role=MessageRole.USER, content="salve"),
        ),
    )


@pytest.mark.asyncio
async def test_prompt_leak_guard_preserves_normal_response() -> None:
    inner = SequencedProvider([["Oi", "! Tudo certo."]])
    provider = PromptLeakGuardProvider(inner)
    chunks = [chunk async for chunk in provider.stream(request())]

    assert "".join(chunk.text for chunk in chunks) == "Oi! Tudo certo."
    assert chunks[-1].done is True
    assert len(inner.requests) == 1


@pytest.mark.asyncio
async def test_prompt_leak_guard_retries_with_minimal_system_after_leak() -> None:
    inner = SequencedProvider(
        [
            ["IDENTIDADE E COMPORTAMENTO ", "DO CAMPANARIO\nVoce e..."],
            ["Salve!"],
        ]
    )
    provider = PromptLeakGuardProvider(inner)

    chunks = [chunk async for chunk in provider.stream(request())]

    assert "".join(chunk.text for chunk in chunks) == "Salve!"
    assert len(inner.requests) == 2
    retry = inner.requests[1]
    assert retry.messages[0].role == MessageRole.SYSTEM
    assert "IDENTIDADE E COMPORTAMENTO DO CAMPANARIO" not in retry.messages[0].content
    assert retry.messages[-1].content == "salve"
    assert sum(message.role == MessageRole.SYSTEM for message in retry.messages) == 1


@pytest.mark.asyncio
async def test_prompt_leak_guard_detects_marker_across_chunk_boundary_and_retries() -> None:
    inner = SequencedProvider(
        [
            ["Resposta: LIMITE DO TUR", "NO ATUAL\nsegredo"],
            ["Tudo certo."],
        ]
    )
    provider = PromptLeakGuardProvider(inner)

    chunks = [chunk async for chunk in provider.stream(request())]

    assert "".join(chunk.text for chunk in chunks) == "Tudo certo."
    assert len(inner.requests) == 2


@pytest.mark.asyncio
async def test_prompt_leak_guard_fails_closed_if_retry_also_leaks() -> None:
    inner = SequencedProvider(
        [
            ["MODO ATUAL CONFIRMADO: social"],
            ["SEMANTICA DE CONTINUACAO: acknowledgement"],
        ]
    )
    provider = PromptLeakGuardProvider(inner)

    with pytest.raises(ModelResponseError, match="after a safe retry"):
        _ = [chunk async for chunk in provider.stream(request())]

    assert len(inner.requests) == 2


@pytest.mark.asyncio
async def test_guard_does_not_false_positive_on_generic_conversation_words() -> None:
    inner = SequencedProvider([["Conversa natural depende de contexto e timing."]])
    provider = PromptLeakGuardProvider(inner)

    chunks = [chunk async for chunk in provider.stream(request())]

    assert "".join(chunk.text for chunk in chunks) == "Conversa natural depende de contexto e timing."
    assert len(inner.requests) == 1

@pytest.mark.asyncio
async def test_v160_guard_blocks_response_contract_heading_if_model_echoes_it() -> None:
    inner = SequencedProvider(
        [
            ["CONTRATO DE RESPOSTA DO TURNO\n- Maximo de 8 palavras"],
            ["Opa."],
        ]
    )
    provider = PromptLeakGuardProvider(inner)
    chunks = [chunk async for chunk in provider.stream(request())]
    assert "".join(chunk.text for chunk in chunks) == "Opa."
    assert len(inner.requests) == 2

@pytest.mark.asyncio
async def test_prompt_leak_guard_blocks_continuity_metadata_heading() -> None:
    inner = SequencedProvider(
        [
            ["CONTEXTO TEMPORARIO DE CONTINUIDADE — assunto atual..."],
            ["Vamos continuar do ponto anterior."],
        ]
    )
    provider = PromptLeakGuardProvider(inner)
    chunks = [chunk async for chunk in provider.stream(request())]
    assert "".join(chunk.text for chunk in chunks) == "Vamos continuar do ponto anterior."
    assert len(inner.requests) == 2
