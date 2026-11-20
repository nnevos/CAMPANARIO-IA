"""G1 user-observed regression: explicit episode separation and contextual memory.

These inspect real persistence and messages sent to the provider, not canned model replies.
"""
from __future__ import annotations

from pathlib import Path

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
        yield ModelChunk(text="Resposta de teste.")
        yield ModelChunk(text="", done=True)


async def say(runtime, session, text):
    return [e async for e in runtime.conversation.stream_turn(session.id, text)]


@pytest.mark.asyncio
async def test_zed_preference_recalled_across_new_episode_and_restart(monkeypatch, tmp_path):
    db = tmp_path / "persistence.db"
    provider = CaptureProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda conf: provider)
    settings = Settings(model_name="fake", low_latency_mode=True, live_streaming=True)
    runtime = composition.build_runtime(settings, database_url=f"sqlite:///{db}", create_schema=True)
    first = runtime.sessions.create_session()
    await say(runtime, first, "Meu editor de código favorito é o Zed.")
    saved = runtime.experience.list_memories()
    assert len(saved) == 1
    assert saved[0].value == "o Zed."  # stored value is extracted directly, no fabricated claim
    assert saved[0].key == "user.editor.de.código.favorito"
    second = runtime.sessions.create_session()
    assert second.id != first.id
    await say(runtime, second, "Morgana, o que você lembra sobre minhas ferramentas de programação?")
    prompt = "\n".join(m.content for m in next(req for req in reversed(provider.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role == "system")
    assert "editor de código favorito" in prompt
    assert '"o Zed."' in prompt
    assert "declarado pelo usuario" in prompt
    assert "nao existe memoria entre sessoes" in prompt  # explicitly prohibited by prompt
    # A new episode must not import the old transcript: only relevant memory is injected.
    turns = [m.content for m in next(req for req in reversed(provider.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role != "system"]
    assert "Meu editor de código favorito é o Zed." not in turns
    runtime.stop()

    provider_after_restart = CaptureProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda conf: provider_after_restart)
    restarted = composition.build_runtime(settings, database_url=f"sqlite:///{db}", create_schema=False)
    third = restarted.sessions.create_session()
    await say(restarted, third, "Todd, quais ferramentas de programação eu já mencionei?")
    prompt_after = "\n".join(m.content for m in next(req for req in reversed(provider_after_restart.requests) if not any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content or "REPARO DE RESPOSTA FUNDAMENTADA" in m.content for m in req.messages)).messages if m.role == "system")
    assert "editor de código favorito" in prompt_after and "Zed" in prompt_after
    assert len(restarted.sessions.list_sessions()) == 3


@pytest.mark.asyncio
async def test_topic_bridge_is_not_a_license_to_recall_unrelated_memories(monkeypatch, tmp_path):
    provider = CaptureProvider()
    monkeypatch.setattr(composition, "build_model_provider", lambda conf: provider)
    runtime = composition.build_runtime(
        Settings(model_name="fake", low_latency_mode=True, live_streaming=True),
        database_url=f"sqlite:///{tmp_path / 'negative.db'}", create_schema=True,
    )
    first = runtime.sessions.create_session()
    await say(runtime, first, "meu editor de código favorito é Helix")
    await say(runtime, first, "eu gosto de jazz")
    assert runtime.experience.recall("Minha impressora não conecta no wi-fi?", agent_id="morgana") == ()
    assert runtime.experience.recall("Como usar ferramentas de jardinagem?", agent_id="morgana") == ()
    recalled = runtime.experience.recall("O que você lembra sobre minhas ferramentas de programação?", agent_id="morgana")
    assert len(recalled) == 1
    assert "Helix" in recalled[0].value
    assert "jazz" not in runtime.experience.render_context(
        "O que você lembra sobre minhas ferramentas de programação?", agent_id="morgana"
    )


def test_ui_exposes_explicit_new_conversation_actions_and_preserves_archives():
    html = (Path(__file__).resolve().parents[1] / "src/campanario/web/index.html").read_text(encoding="utf-8")
    html += "\n".join(f.read_text(encoding="utf-8") for f in sorted((Path(__file__).resolve().parents[1] / "src/campanario/web/static").glob("*")) if f.suffix in {".js", ".css"})
    assert 'id="newConversation"' in html
    assert 'id="newSessionPanel"' in html
    assert "$('newConversation').onclick=newConversation" in html
    assert "$('newSessionPanel').onclick=newConversation" in html
    assert "if(busy)return" in html
    assert "closeRealtime();sessionId=null;localStorage.removeItem('campanario.active_session');lastSequence=0;viewingArchive=false;" in html
    assert "$('conversation').replaceChildren()" in html
    assert "await createSession()" in html  # lazy new episode on the following message
    assert "sessionCache.filter(" in html  # previous and active episodes appear together
    assert "await connectRealtime(true)" in html  # reopen session without replaying old bubbles
    assert '<time class="message-time"></time>' in html
