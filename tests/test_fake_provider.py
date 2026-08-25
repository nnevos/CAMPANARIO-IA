import pytest

from campanario.model.protocol import FakeModelProvider, ModelRequest


@pytest.mark.asyncio
async def test_fake_provider_streams_without_ollama() -> None:
    provider = FakeModelProvider("teste")
    request = ModelRequest(model="fake", messages=())
    chunks = [chunk async for chunk in provider.stream(request)]
    assert "".join(chunk.text for chunk in chunks) == "teste"
    assert chunks[-1].done is True
