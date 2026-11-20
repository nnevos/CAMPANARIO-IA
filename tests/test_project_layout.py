from pathlib import Path


def test_root_is_intentionally_small_and_operational() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = {
        "BEHAVIORAL_FOUNDATION_PLAN.md", "CHANGELOG.md", "PHASE2_CONTEXT_MANAGER_PLAN.md",
        "RECOVERY.md", "REFACTOR_CHECKPOINT.md", "ABRIR_MANUAL.bat", "AJUSTAR_VELOCIDADE_VOZ.bat", "COMPARAR_MODELOS.bat",
        "CONSULTAR_ULTIMO_TESTE.bat", "INICIAR_CAMPANARIO.bat", "TESTAR_COMPORTAMENTO.bat",
        "TESTAR_COMPORTAMENTO_MEGA.bat", "TROCAR_MODELO.bat", "TESTAR_AGENTES.bat",
    }
    assert not any((root / name).exists() for name in forbidden)
    assert (root / "CAMPANARIO.bat").exists()
    assert (root / "docs/history/checkpoints/RECOVER_FIRST.md").exists()
    assert (root / "docs/history/checkpoints/PROJECT_STATE.md").exists()


def test_windows_root_contains_only_current_operational_launchers() -> None:
    root = Path(__file__).resolve().parents[1]
    windows = root / "tools" / "windows"
    expected = {'INICIAR_RUNTIME_HEADLESS.bat', 'ABRIR_MANUAL.bat', 'TESTAR_CONVERSA_HUMANA.bat', 'TESTAR_COMPORTAMENTO.bat', 'DIAGNOSTICAR_QWEN.bat', 'INICIAR_CAMPANARIO.bat', 'TESTAR_REALTIME_F5.bat', 'TESTAR_COMPORTAMENTO_MEGA.bat', 'TESTAR_LONG_CALL.bat', 'TESTAR_PERSONALIDADES.bat', 'CONSULTAR_ULTIMO_TESTE.bat', 'TESTAR_PERSONALIDADES_MEGA.bat', 'COMPARAR_MODELOS.bat', 'PREPARAR_MEMORIA_SEMANTICA.bat', 'TROCAR_MODELO.bat', 'TESTAR_AGENTES.bat'}
    assert expected == {p.name for p in windows.glob("*.bat")}
    assert (windows / "regression" / "platform" / "TESTAR_RUNTIME_PF9.bat").exists()
    assert (windows / "regression" / "conversation" / "TESTAR_CONVERSA_MULTIAGENTE.bat").exists()
    assert (windows / "TESTAR_CONVERSA_HUMANA.bat").exists()


def test_transient_artifacts_are_ignored_by_project_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    ignored = (root / ".gitignore").read_text(encoding="utf-8")
    for marker in (".venv/", ".pytest_cache/", "test_reports/", ".env"):
        assert marker in ignored


def test_presence_ui_starts_new_and_only_opens_archives_explicitly():
    html = Path('src/campanario/web/index.html').read_text(encoding='utf-8')
    js = Path('src/campanario/web/static/chat.js').read_text(encoding='utf-8')
    boot = js.split('async function boot()', 1)[1].split('function renderParticipants', 1)[0]
    assert "await selectSession(ss[0])" not in js
    assert "localStorage.getItem('campanario.active_session')" not in js
    assert "localStorage.removeItem('campanario.active_session')" in boot
    assert "sessionId=null;$('conversation').innerHTML=''" in boot
    assert 'id="chatSidebar"' in html
    assert 'id="sidebarNew"' in html
    assert 'b.onclick=()=>selectSession(s)' in js
