from pathlib import Path


def test_manual_area_contains_only_current_operational_guides() -> None:
    root = Path(__file__).resolve().parents[1]
    manual = root / "docs" / "manual"
    expected = {
        "README.md",
        "01_PRIMEIROS_PASSOS.md",
        "02_INICIAR_E_ENCERRAR.md",
        "03_USAR_O_CHAT.md",
        "04_TESTES_COMPORTAMENTAIS.md",
        "05_RELATORIOS_DE_TESTE.md",
        "06_CONFIGURACOES.md",
        "07_MEMORIA_E_CONTEXTO.md",
        "08_BACKUP_E_RECUPERACAO.md",
        "09_SOLUCAO_DE_PROBLEMAS.md",
        "10_ARQUITETURA_PARA_USUARIO.md",
        "11_FUNCOES_DO_SISTEMA.md",
    }
    actual = {path.name for path in manual.iterdir() if path.is_file()}
    assert actual == expected
    assert (root / "CAMPANARIO.bat").exists()


def test_historical_behavior_manuals_are_archived_not_active() -> None:
    root = Path(__file__).resolve().parents[1]
    archive = root / "docs" / "history" / "manual_evolution"
    assert (archive / "20_RESPONSE_CONTRACT_PIPELINE.md").exists()
    assert (archive / "21_MODELOS_E_PORTABILIDADE.md").exists()
    assert not (root / "docs" / "manual" / "20_RESPONSE_CONTRACT_PIPELINE.md").exists()


def test_manual_marks_agents_as_next_gate_not_active() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "manual" / "11_FUNCOES_DO_SISTEMA.md").read_text(encoding="utf-8")
    assert "Todd/Morgana | PROXIMO GATE" in text
    assert "Gemma 3 12B recomendado | ATIVO" in text
