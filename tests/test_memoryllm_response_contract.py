"""MemoryLLM-style RAG answers do not pass through the former audit cascade."""
from __future__ import annotations

import pytest
import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import ModelChunk


class RecordingProvider:
    def __init__(self):
        self.requests = []

    async def health(self):
        return True

    async def stream(self, request):
        self.requests.append(request)
        yield ModelChunk(text='Você está aprendendo violoncelo.')
        yield ModelChunk(text='', done=True)


@pytest.mark.asyncio
async def test_answer_is_natural_and_memory_evidence_reaches_generation(monkeypatch, tmp_path):
    provider = RecordingProvider()
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    runtime = composition.build_runtime(
        Settings(model_name='fake', semantic_memory_enabled=False,
                 low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "memory.db"}', create_schema=True)
    first = runtime.sessions.create_session()
    _ = [x async for x in runtime.conversation.stream_turn(first.id, 'Estou aprendendo a tocar violoncelo.')]
    second = runtime.sessions.create_session()
    events = [x async for x in runtime.conversation.stream_turn(second.id, 'Qual instrumento estou aprendendo?')]
    output = ''.join(x.text for x in events if x.type == 'token')
    assert output == 'Você está aprendendo violoncelo.'
    assert any('Estou aprendendo a tocar violoncelo.' in msg.content
               for req in provider.requests[-1:] for msg in req.messages)
    assert len(provider.requests) == 2  # one generation per user turn


def test_default_memoryllm_backend_and_isolation(tmp_path):
    settings = Settings(data_dir=tmp_path)
    assert settings.semantic_memory_backend == 'memoryllm_chroma'
    assert settings.memory_environment == 'desenvolvimento'
