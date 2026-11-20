"""G2 foundation: preserve user evidence in the context, never a memorized script.

The fake model captures its input; these tests do NOT assert Qwen's output.
"""
from __future__ import annotations

import pytest
import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import ModelChunk


class CaptureProvider:
    def __init__(self):
        self.requests = []

    async def health(self):
        return True

    async def stream(self, request):
        self.requests.append(request)
        yield ModelChunk(text="Resposta simulada.")
        yield ModelChunk(text="", done=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("statement,query,original", [
    ("gosto de jazz instrumental", "qual musica eu gosto?", "gosto de jazz instrumental"),
    ("prefiro trabalhar de madrugada", "eu prefiro trabalhar quando?", "prefiro trabalhar de madrugada"),
    ("planejo visitar a Chapada Diamantina", "qual viagem eu planejo?", "planejo visitar a Chapada Diamantina"),
    ("meu sistema operacional é Linux", "qual sistema operacional eu uso?", "meu sistema operacional é Linux"),
    ("gosto de Petit Gâteau", "qual doce eu gosto?", "gosto de Petit Gâteau"),
])
async def test_independent_episode_preserves_exact_evidence(monkeypatch, tmp_path, statement, query, original):
    provider = CaptureProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda _settings: provider)
    rt = composition.build_runtime(
        Settings(model_name="fake", low_latency_mode=True, live_streaming=True),
        database_url=f"sqlite:///{tmp_path / 'mem.db'}", create_schema=True,
    )
    first = rt.sessions.create_session()
    _ = [e async for e in rt.conversation.stream_turn(first.id, statement)]
    second = rt.sessions.create_session()
    _ = [e async for e in rt.conversation.stream_turn(second.id, query)]
    system = "\n".join(m.content for m in next(req for req in reversed(provider.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role == "system")
    assert f'declaracao original: "{original}"' in system
    assert "gostar NAO significa favorito" in system
    non_system = "\n".join(m.content for m in next(req for req in reversed(provider.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role != "system")
    assert statement not in non_system


@pytest.mark.asyncio
async def test_older_fact_is_not_resurrected_after_correction(monkeypatch, tmp_path):
    provider = CaptureProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda _settings: provider)
    rt = composition.build_runtime(Settings(model_name="fake", low_latency_mode=True),
        database_url=f"sqlite:///{tmp_path / 'correction.db'}", create_schema=True)
    first = rt.sessions.create_session()
    for utterance in ("meu editor é VSCode", "meu editor é Helix"):
        _ = [e async for e in rt.conversation.stream_turn(first.id, utterance)]
    second = rt.sessions.create_session()
    _ = [e async for e in rt.conversation.stream_turn(second.id, "qual editor eu uso?")]
    system = "\n".join(m.content for m in next(req for req in reversed(provider.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role == "system")
    assert 'declaracao original: "meu editor é Helix"' in system
    assert 'declaracao original: "meu editor é VSCode"' not in system
