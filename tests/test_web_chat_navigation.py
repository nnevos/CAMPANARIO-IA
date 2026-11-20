from pathlib import Path


def test_conversation_sidebar_is_first_class_and_searchable():
    html = (Path(__file__).resolve().parents[1] / "src/campanario/web/index.html").read_text(encoding="utf-8")
    html += "\n".join(f.read_text(encoding="utf-8") for f in sorted((Path(__file__).resolve().parents[1] / "src/campanario/web/static").glob("*")) if f.suffix in {".js", ".css"})
    for name in ("chatSidebar", "sidebarNew", "sessionSearch", "sidebarToggle", "sidebarScrim", "sessions"):
        assert f'id="{name}"' in html
    assert 'id="sessions"' in html and html.count('id="sessions"') == 1
    assert 'class="chat-history"' in html
    assert "$('sessionSearch').addEventListener('input',renderSessions)" in html
    assert "b.onclick=()=>selectSession(s)" in html
    assert "sessionId=s.id;localStorage.setItem('campanario.active_session',sessionId);lastSequence=0;viewingArchive=false" in html
    assert "history.forEach(m=>addTurn(m.role,m.content,m.agent_id,m.created_at))" in html
    assert "await connectRealtime(true)" in html
    assert "localStorage.getItem('campanario.active_session')" not in html
    assert "localStorage.removeItem('campanario.active_session')" in html
    assert "main.sidebar-open .chat-sidebar" in html


def test_memory_policy_does_not_claim_generic_semantic_retrieval():
    source = (Path(__file__).resolve().parents[1] / "src/campanario/runtime/experience.py").read_text(encoding="utf-8")
    assert "This is deliberately *not* embedding search" in source
    assert "intentionally narrow and can miss paraphrases" in source
