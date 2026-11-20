"""G1/G2 foundation: real request context contracts, not expected canned replies."""
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import ModelChunk
from campanario.runtime.experience import MemoryKind, MemorySource


class RecordingProvider:
    def __init__(self) -> None:
        self.requests = []

    async def health(self) -> bool:
        return True

    async def stream(self, request):
        self.requests.append(request)
        yield ModelChunk(text="Respondi ao assunto.")
        yield ModelChunk(text="", done=True)


@pytest.fixture
def runtime_factory(monkeypatch, tmp_path):
    provider = RecordingProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda config: provider)
    def make(name="first_wave.db", create_schema=True):
        runtime = composition.build_runtime(
            Settings(model_name="fake", low_latency_mode=True, live_streaming=True),
            database_url=f"sqlite:///{tmp_path / name}", create_schema=create_schema,
        )
        return runtime, provider
    return make


async def send(runtime, session, text):
    return [event async for event in runtime.conversation.stream_turn(session.id, text)]


@pytest.mark.asyncio
async def test_unrelated_high_confidence_preference_stays_out_of_model_request(runtime_factory):
    runtime, provider = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "eu prefiro jazz instrumental")
    before = len(provider.requests)
    assert runtime.experience.recall("como consertar a conexao da impressora?") == ()
    await send(runtime, session, "como consertar a conexao da impressora?")
    assert len(provider.requests) == before + 1  # no additional memory extraction call
    system_text = provider.requests[-1].messages[0].content
    assert "jazz instrumental" not in system_text


@pytest.mark.asyncio
async def test_accent_and_inflection_support_relevance_not_stray_memories(runtime_factory):
    runtime, _ = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "eu prefiro respostas curtas")
    assert "respostas curtas" in runtime.experience.render_context("me responda curto")
    assert "respostas curtas" not in runtime.experience.render_context("explica astronomia")


@pytest.mark.asyncio
async def test_general_user_profile_query_recalls_confirmed_user_facts(runtime_factory):
    runtime, _ = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "meu editor é Zed")
    await send(runtime, session, "eu prefiro respostas objetivas")
    recalled = runtime.experience.recall("O que você sabe sobre mim?", agent_id="morgana")
    assert {m.value for m in recalled} >= {"Zed", "respostas objetivas"}
    assert runtime.experience.recall("qual a previsão de chuva?", agent_id="morgana") == ()


@pytest.mark.asyncio
async def test_shared_facts_and_agent_private_hypotheses_in_actual_model_context(runtime_factory):
    runtime, provider = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "meu editor é Zed")
    hypothesis = runtime.experience.create_inference(
        value="talvez prefira atalhos do Zed", evidence="observacao hipotetica",
        source_agent_id="todd", session_id=session.id,
    )
    assert hypothesis.kind == MemoryKind.INFERENCE
    await send(runtime, session, "Morgana, como configurar Zed e atalhos?")
    morgana_context = provider.requests[-1].messages[0].content
    assert "Zed" in morgana_context
    assert "talvez prefira atalhos do Zed" not in morgana_context
    await send(runtime, session, "Todd, como configurar Zed e atalhos?")
    todd_context = provider.requests[-1].messages[0].content
    assert "Zed" in todd_context
    assert "talvez prefira atalhos do Zed" in todd_context
    assert "INFERENCIA / HIPOTESE" in todd_context


@pytest.mark.asyncio
async def test_relationship_outcome_restricted_to_agent_who_participated(runtime_factory):
    runtime, _ = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "Todd, sugestao sobre o worker travado?")
    await send(runtime, session, "isso funcionou")
    memories = [m for m in runtime.experience.list_memories() if m.kind == MemoryKind.SHARED_EXPERIENCE]
    assert memories
    assert "worker" in memories[0].value or "Respondi" in memories[0].value
    assert memories[0].id in {m.id for m in runtime.experience.recall("funcionou", agent_id="todd")}
    assert memories[0].id not in {m.id for m in runtime.experience.recall("funcionou", agent_id="morgana")}


@pytest.mark.asyncio
async def test_correction_forgetting_and_restart_do_not_retrieve_stale_fact(runtime_factory):
    runtime, provider = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "meu editor é Zed")
    await send(runtime, session, "meu editor é Helix")
    assert "Zed" not in runtime.experience.render_context("editor")
    assert "Helix" in runtime.experience.render_context("editor")
    runtime.stop()
    restarted, _ = runtime_factory(create_schema=False)
    memories = restarted.experience.recall("editor")
    assert len(memories) == 1 and memories[0].value == "Helix"
    restarted.experience.forget(memories[0].id)
    assert restarted.experience.recall("editor") == ()


@pytest.mark.asyncio
async def test_context_and_model_call_metrics_contain_counts_not_user_content(runtime_factory):
    runtime, provider = runtime_factory()
    session = runtime.sessions.create_session()
    secret_phrase = "jardim-das-andorinhas"
    await send(runtime, session, f"pode explicar o conceito {secret_phrase}?")
    marks = runtime.telemetry.snapshot()
    ready = [m for m in marks if m.name == "context_ready"]
    calls = [m for m in marks if m.name == "model_call_started"]
    assert len(ready) == 1 and len(calls) == 1
    attrs = dict(ready[0].attributes)
    assert int(attrs["context_messages"]) >= 2
    assert int(attrs["context_chars"]) >= len(secret_phrase)
    assert all(secret_phrase not in str(m.attributes) for m in marks)
    assert len(provider.requests) == 1


@pytest.mark.asyncio
async def test_memory_context_length_bounded_for_long_notes(runtime_factory):
    runtime, _ = runtime_factory()
    session = runtime.sessions.create_session()
    await send(runtime, session, "lembre que " + "telescopio " * 200)
    rendered = runtime.experience.render_context("telescopio", max_chars=600)
    assert len(rendered) <= 600
    assert rendered.startswith("CONTINUIDADE")
