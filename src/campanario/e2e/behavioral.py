"""CLI facade for the split Behavioral E2E implementation."""
from __future__ import annotations
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from .evaluator import evaluate_response
from .reporting import save_report
from .runner import run_suite
from .scenarios import build_scenarios
from .types import CheckResult, CheckSpec, RunReport, ScenarioResult, ScenarioSpec, TurnResult, TurnSpec

__all__ = [
    "CheckResult", "CheckSpec", "RunReport", "ScenarioResult", "ScenarioSpec", "TurnResult", "TurnSpec",
    "build_scenarios", "evaluate_response", "run_suite", "save_report",
]

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Campanario behavioral E2E against the configured local Ollama model.")
    parser.add_argument("--suite", choices=("standard", "full", "mega", "agents", "agent_personality", "agent_mega", "agent_integrated", "agent_long_call", "agent_human_quick", "agent_human_baseline"), default="standard")
    parser.add_argument("--seed", type=int, default=None, help="Scenario variation seed; omitted = current timestamp")
    parser.add_argument("--output", type=Path, default=Path("test_reports") / "behavioral_e2e")
    parser.add_argument("--no-open", action="store_true", help="Do not open the HTML report automatically")
    return parser.parse_args(argv)


async def _main_async(args: argparse.Namespace) -> int:
    seed = args.seed if args.seed is not None else int(datetime.now().timestamp())
    try:
        report = await run_suite(seed=seed, suite=args.suite)
    except Exception as exc:
        print(f"[ERRO] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    run_dir = save_report(report, args.output)
    print("\n========================================")
    print("Behavioral E2E concluído")
    print(f"Gate automático: {report.summary['automatic_gate']}")
    print(f"Relatório: {run_dir / 'report.html'}")
    concept = report.summary.get("personality_concept")
    if isinstance(concept, dict):
        counts = concept.get("counts", {})
        print("Análise conceitual:")
        if isinstance(counts, dict):
            for agent in ("todd", "morgana"):
                item = counts.get(agent, {})
                if isinstance(item, dict):
                    print(f"  {agent.capitalize()}: {item.get('bate', 0)} BATE / {item.get('misto', 0)} MISTO / {item.get('revisar', 0)} REVISAR / {item.get('sem_dado', 0)} SEM DADO")
    pair = report.summary.get("personality_pair")
    if isinstance(pair, dict):
        axes = pair.get("axes", {})
        if isinstance(axes, dict):
            print("Comparação pareada:")
            for dimension, item in sorted(axes.items()):
                if isinstance(item, dict):
                    print(f"  {dimension}: {item.get('policy', '')} -> {item.get('status', '')}")
    latency = report.summary.get("latency")
    if isinstance(latency, dict):
        ttfr = latency.get("time_to_first_response", {})
        multi = latency.get("multiagent_turn_total", {})
        if isinstance(ttfr, dict) and isinstance(multi, dict):
            print(
                f"Latencia: TTFR mediana={ttfr.get('median')}s / p95={ttfr.get('p95')}s; "
                f"multiagente medio={multi.get('mean')}s"
            )
    print("========================================")
    return 1 if report.summary["automatic_gate"] == "FAIL" else 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
