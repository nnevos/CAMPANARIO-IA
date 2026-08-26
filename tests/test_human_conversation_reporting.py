from datetime import UTC, datetime
from pathlib import Path

from campanario.e2e.reporting import save_report
from campanario.e2e.types import RunReport, ScenarioResult, TurnResult


def test_human_baseline_generates_blind_review_with_hidden_labels_until_key(tmp_path: Path) -> None:
    scenarios = []
    for agent in ("todd", "morgana"):
        scenarios.append(ScenarioResult(
            id=f"human_{agent}_getting_to_know", category="human_conversation", description="x", review_focus="x",
            turns=[TurnResult(user="oi", assistant=f"resposta-{agent}", speaker_id=agent)], status="PASS",
        ))
    report = RunReport(
        generated_at=datetime.now(UTC).isoformat(), model="fake", base_url="local", seed=7,
        suite="agent_human_baseline", scenarios=scenarios,
        summary={"automatic_gate":"PASS","scenario_pass":2,"scenario_warn":0,"scenario_fail":0,"check_pass":0,"check_warn":0,"check_fail":0},
    )
    run_dir = save_report(report, tmp_path)
    blind = (run_dir / "blind_review.md").read_text(encoding="utf-8")
    body, key = blind.split("## Gabarito", 1)
    assert "Resposta:" in body
    assert "**Todd:**" not in body and "**Morgana:**" not in body
    assert "Todd" in key and "Morgana" in key
    assert (tmp_path / "latest.blind.md").exists()
