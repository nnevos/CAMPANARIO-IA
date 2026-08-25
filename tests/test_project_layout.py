from pathlib import Path


def test_root_is_intentionally_small_and_operational() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = {
        "BEHAVIORAL_FOUNDATION_PLAN.md",
        "CHANGELOG.md",
        "PHASE2_CONTEXT_MANAGER_PLAN.md",
        "RECOVERY.md",
        "REFACTOR_CHECKPOINT.md",
        "ABRIR_MANUAL.bat",
        "COMPARAR_MODELOS.bat",
        "CONSULTAR_ULTIMO_TESTE.bat",
        "INICIAR_CAMPANARIO.bat",
        "TESTAR_COMPORTAMENTO.bat",
        "TESTAR_COMPORTAMENTO_MEGA.bat",
        "TROCAR_MODELO.bat",
    }
    assert not any((root / name).exists() for name in forbidden)
    assert (root / "CAMPANARIO.bat").exists()
    assert (root / "RECOVER_FIRST.md").exists()
    assert (root / "PROJECT_STATE.md").exists()


def test_windows_launchers_live_under_tools() -> None:
    root = Path(__file__).resolve().parents[1]
    windows = root / "tools" / "windows"
    expected = {
        "ABRIR_MANUAL.bat",
        "COMPARAR_MODELOS.bat",
        "CONSULTAR_ULTIMO_TESTE.bat",
        "INICIAR_CAMPANARIO.bat",
        "TESTAR_COMPORTAMENTO.bat",
        "TESTAR_COMPORTAMENTO_MEGA.bat",
        "TROCAR_MODELO.bat",
    }
    assert expected <= {p.name for p in windows.glob("*.bat")}


def test_transient_artifacts_are_ignored_by_project_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    ignored = (root / ".gitignore").read_text(encoding="utf-8")
    for marker in (".venv/", ".pytest_cache/", "test_reports/", ".env"):
        assert marker in ignored
