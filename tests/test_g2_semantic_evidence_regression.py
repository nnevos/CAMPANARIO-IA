"""G2 replacement regression: no conversational LLM selection of memory IDs."""
from __future__ import annotations

import json
import re

import pytest
import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import ModelChunk
from campanario.chat.memory_grounding import parse_semantic_selection
from campanario.runtime.semantic_index import normalize_vector


# Simulate an independent multilingual embedding MODEL, not the chat LLM.
# These vectors are fixtures for integration plumbing; not a claim about real model accuracy.
class FixtureEmbeddings:
    def embed(self, texts):
        vectors = []
        for text in texts:
            low = text.lower()
            if 'blender' in low or 'programa estou usando' in low:
                vector = [1, 0, 0]
            elif 'astronomia' in low or 'tema venho explorando' in low:
                vector = [0, 1, 0]
            elif 'violão' in low or 'atividade tenho me dedicado' in low:
                vector = [0, 0, 1]
            else:
                vector = [0.1, 0.1, 0.1]
            vectors.append(normalize_vector(vector))
        return vectors


class FakeChat:
    def __init__(self):
        self.requests = []

    async def health(self):
        return True

    async def stream(self, request):
        self.requests.append(request)
        contents = '\n'.join(m.content for m in request.messages)
        if 'AUDITORIA DE EVIDENCIA PESSOAL' in contents:
            output = '{"supported":false,"quotes":[]}'
        else:
            output = 'Não tenho certeza.'
        yield ModelChunk(text=output)
        yield ModelChunk(text='', done=True)


@pytest.mark.asyncio
@pytest.mark.parametrize('statement,question', [
    ('estou aprendendo o Blender', 'qual programa estou usando ultimamente?'),
    ('estou estudando astronomia', 'qual tema venho explorando?'),
    ('estou praticando violão', 'em que atividade tenho me dedicado?'),
])
async def test_general_memory_retrieval_uses_local_vectors_not_chat_selector(monkeypatch, tmp_path, statement, question):
    chat = FakeChat()
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: chat)
    monkeypatch.setattr(composition, 'OllamaEmbeddingProvider', lambda **_: FixtureEmbeddings())
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "memory.db"}', create_schema=True)
    first = rt.sessions.create_session()
    _ = [e async for e in rt.conversation.stream_turn(first.id, statement)]
    second = rt.sessions.create_session()
    events = [e async for e in rt.conversation.stream_turn(second.id, question)]
    assert not any('SELECAO DE MEMORIAS PARA RECUPERACAO' in m.content for req in chat.requests for m in req.messages)
    primary = [r for r in chat.requests if any('CONTEXTO APRENDIDO RELEVANTE' in m.content for m in r.messages)]
    assert primary and statement in '\n'.join(m.content for m in primary[-1].messages)
    output = ''.join(e.text for e in events if e.type == 'token')
    assert statement in output  # quote-backed fallback, not a hallucinated user fact


def test_legacy_selector_never_accepts_invented_ids():
    assert parse_semantic_selection('{"ids":["00000000-0000-0000-0000-000000000000"]}', ()) == ()
