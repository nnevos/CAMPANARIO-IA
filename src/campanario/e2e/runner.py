from __future__ import annotations
import asyncio
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from campanario.chat.service import ChatService
from campanario.composition import build_chat_stack
from campanario.config import get_settings
from campanario.model.protocol import ModelProvider, ModelProviderError
from .evaluator import evaluate_response
from .scenarios import build_scenarios
from .types import RunReport, ScenarioResult, TurnResult

def _scenario_status(turns: list[TurnResult]) -> str:
    statuses = [check.status for turn in turns for check in turn.checks]
    if any(turn.error for turn in turns) or "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _build_service(database_path: Path) -> tuple[ChatService, ModelProvider]:
    settings = get_settings()
    return build_chat_stack(
        settings,
        database_url=f"sqlite:///{database_path.as_posix()}",
        create_schema=True,
    )


async def _send(service: ChatService, session_id, text: str) -> str:
    parts: list[str] = []
    async for chunk in service.stream_reply(session_id, text):
        parts.append(chunk)
    return "".join(parts).strip()


async def run_suite(seed: int, suite: str) -> RunReport:
    settings = get_settings()
    runtime = settings.model_runtime
    if not runtime.model.strip():
        raise RuntimeError("CAMPANARIO_MODEL_NAME não está configurado.")

    root_tmp = Path(tempfile.mkdtemp(prefix="campanario-e2e-"))
    try:
        service, raw_provider = _build_service(root_tmp / "e2e.db")
        if not await raw_provider.health():
            raise RuntimeError(f"Model provider {runtime.backend.value} não respondeu em {runtime.base_url}.")

        scenarios = build_scenarios(seed, suite)
        results: list[ScenarioResult] = []
        loop = asyncio.get_running_loop()
        for index, scenario in enumerate(scenarios, start=1):
            print(f"[{index:02d}/{len(scenarios):02d}] {scenario.id} ...", flush=True)
            session = service.create_session(title=f"E2E {scenario.id}")
            scenario_result = ScenarioResult(
                id=scenario.id,
                category=scenario.category,
                description=scenario.description,
                review_focus=scenario.review_focus,
            )
            for turn in scenario.turns:
                started = loop.time()
                turn_result = TurnResult(user=turn.user)
                try:
                    response = await _send(service, session.id, turn.user)
                    turn_result.assistant = response
                    prior_assistant = tuple(item.assistant for item in scenario_result.turns if item.assistant)
                    turn_result.checks = evaluate_response(response, turn.checks, prior_assistant, turn.user)
                except ModelProviderError as exc:
                    turn_result.error = f"{type(exc).__name__}: {exc}"
                except Exception as exc:  # report harness/runtime faults instead of hiding them
                    turn_result.error = f"{type(exc).__name__}: {exc}"
                turn_result.duration_seconds = round(loop.time() - started, 3)
                scenario_result.turns.append(turn_result)
                if turn_result.error:
                    break
            scenario_result.status = _scenario_status(scenario_result.turns)
            results.append(scenario_result)

        passed = sum(item.status == "PASS" for item in results)
        warned = sum(item.status == "WARN" for item in results)
        failed = sum(item.status == "FAIL" for item in results)
        all_checks = [check for scenario in results for turn in scenario.turns for check in turn.checks]
        check_pass = sum(item.status == "PASS" for item in all_checks)
        check_warn = sum(item.status == "WARN" for item in all_checks)
        check_fail = sum(item.status == "FAIL" for item in all_checks)
        report = RunReport(
            generated_at=datetime.now(UTC).isoformat(),
            model=runtime.model,
            base_url=runtime.base_url,
            seed=seed,
            suite=suite,
            scenarios=results,
            summary={
                "scenario_count": len(results),
                "scenario_pass": passed,
                "scenario_warn": warned,
                "scenario_fail": failed,
                "check_count": len(all_checks),
                "check_pass": check_pass,
                "check_warn": check_warn,
                "check_fail": check_fail,
                "automatic_gate": "FAIL" if failed else ("WARN" if warned else "PASS"),
                "human_review_required": True,
                "note": "Checks automáticos não substituem revisão humana de naturalidade.",
            },
        )
        return report
    finally:
        shutil.rmtree(root_tmp, ignore_errors=True)


