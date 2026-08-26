from __future__ import annotations
import asyncio
import re
import shutil
import unicodedata
import tempfile
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path

from campanario.chat.service import ChatService
from campanario.composition import build_chat_stack
from campanario.config import get_settings
from campanario.model.protocol import ModelProvider, ModelProviderError
from .evaluator import evaluate_multiagent_turn, evaluate_response
from .scenarios import build_scenarios
from .types import CheckSpec, RunReport, ScenarioResult, SpeakerResult, TurnResult

def _scenario_status(turns: list[TurnResult]) -> str:
    statuses = [check.status for turn in turns for check in turn.checks]
    if any(turn.error for turn in turns) or "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"



def _personality_concept_summary(results: list[ScenarioResult]) -> dict[str, object] | None:
    """Aggregate concept checks without turning one lexical miss into an axis failure.

    Quick runs contain one observation per axis, so PASS/WARN maps directly to BATE/REVISAR.
    Mega runs contain repeated semantic variants. There we expose the evidence ratio and use
    three states: BATE (>=75% passes), MISTO (>=50%), REVISAR (<50%). This keeps lexical
    heuristics as evidence rather than letting a single WARN poison an entire dimension.
    """
    personality = [item for item in results if item.id.startswith("personality_")]
    if not personality:
        return None

    observations: dict[str, dict[str, list[tuple[str, str]]]] = {"todd": {}, "morgana": {}}
    for scenario in personality:
        base_id = scenario.id.split("__agentmega", 1)[0]
        parts = base_id.split("_", 2)
        if len(parts) != 3 or parts[1] not in observations:
            continue
        agent, dimension = parts[1], parts[2]
        checks = [
            check for turn in scenario.turns for check in turn.checks
            if check.label.startswith("CONCEITO:")
        ]
        if not checks:
            observations[agent].setdefault(dimension, []).append(("SEM_DADO", "check conceitual ausente"))
            continue
        status = "PASS" if all(check.status == "PASS" for check in checks) else "WARN"
        detail = "; ".join(check.detail for check in checks)
        observations[agent].setdefault(dimension, []).append((status, detail))

    agents: dict[str, dict[str, str]] = {"todd": {}, "morgana": {}}
    details: dict[str, dict[str, str]] = {"todd": {}, "morgana": {}}
    evidence: dict[str, dict[str, dict[str, object]]] = {"todd": {}, "morgana": {}}
    for agent, dimensions in observations.items():
        for dimension, items in dimensions.items():
            measured = [status for status, _ in items if status != "SEM_DADO"]
            passes = sum(status == "PASS" for status in measured)
            warns = sum(status == "WARN" for status in measured)
            total = len(measured)
            ratio = (passes / total) if total else None
            if total == 0:
                status = "SEM_DADO"
            elif total == 1:
                status = "BATE" if passes == 1 else "REVISAR"
            elif ratio is not None and ratio >= 0.75:
                status = "BATE"
            elif ratio is not None and ratio >= 0.50:
                status = "MISTO"
            else:
                status = "REVISAR"
            agents[agent][dimension] = status
            evidence[agent][dimension] = {
                "pass": passes, "warn": warns, "total": total,
                "pass_ratio": round(ratio, 3) if ratio is not None else None,
            }
            details[agent][dimension] = " | ".join(detail for _, detail in items)

    counts: dict[str, dict[str, int]] = {}
    for agent, dimensions in agents.items():
        counts[agent] = {
            "bate": sum(value == "BATE" for value in dimensions.values()),
            "misto": sum(value == "MISTO" for value in dimensions.values()),
            "revisar": sum(value == "REVISAR" for value in dimensions.values()),
            "sem_dado": sum(value == "SEM_DADO" for value in dimensions.values()),
            "total": len(dimensions),
        }
    return {"agents": agents, "details": details, "evidence": evidence, "counts": counts}


_PERSONALITY_PAIR_POLICIES: dict[str, str] = {
    "decision": "DIVERGENCIA_ESPERADA",
    "simplicity": "CONVERGENCIA_OK",
    "disagreement": "DIVERGENCIA_ESPERADA",
    "uncertainty": "ASSINATURA_LEVE",
    "urgency": "CONVERGENCIA_OK",
    "technical": "ASSINATURA_LEVE",
    "creative": "DIVERGENCIA_ESPERADA",
    "social": "ASSINATURA_LEVE",
}


def _pair_tokens(text: str, prompt: str = "") -> set[str]:
    def fold(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    stop = {
        "para", "como", "isso", "essa", "esse", "uma", "uns", "umas", "que", "com",
        "por", "mais", "menos", "muito", "muita", "tambem", "ainda", "entao", "depois",
        "antes", "pode", "podem", "ser", "esta", "estao", "voce", "seu", "sua", "seus",
        "suas", "ter", "tem", "dos", "das", "nos", "nas", "mas", "sem", "sim", "nao",
    }
    prompt_tokens = set(re.findall(r"[a-z0-9]+", fold(prompt)))
    tokens = {token for token in re.findall(r"[a-z0-9]+", fold(text)) if len(token) >= 4 and token not in stop}
    return tokens - prompt_tokens


def _pair_similarity(left: str, right: str, prompt: str = "") -> float:
    a, b = _pair_tokens(left, prompt), _pair_tokens(right, prompt)
    if not a and not b:
        return 1.0 if left.strip() == right.strip() else 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _concept_pass(scenario: ScenarioResult) -> bool:
    checks = [
        check for turn in scenario.turns for check in turn.checks
        if check.label.startswith("CONCEITO:")
    ]
    return bool(checks) and all(check.status == "PASS" for check in checks)


def _personality_pair_summary(results: list[ScenarioResult]) -> dict[str, object] | None:
    """Compare Todd/Morgana as a pair, respecting when convergence is natural.

    This is intentionally heuristic and WARN-only. It does not demand opposite answers. It only
    flags likely base-model convergence in axes where the prompt leaves meaningful room for
    perspective. Prompt vocabulary is removed before surface-overlap is calculated.
    """
    grouped: dict[tuple[str, str], dict[str, ScenarioResult]] = {}
    for scenario in results:
        if not scenario.id.startswith("personality_"):
            continue
        base, sep, batch = scenario.id.partition("__agentmega")
        parts = base.split("_", 2)
        if len(parts) != 3 or parts[1] not in {"todd", "morgana"}:
            continue
        agent, dimension = parts[1], parts[2]
        grouped.setdefault((dimension, batch if sep else "quick"), {})[agent] = scenario

    observations: dict[str, list[dict[str, object]]] = {}
    for (dimension, batch), pair in grouped.items():
        if set(pair) != {"todd", "morgana"}:
            continue
        todd_turn = pair["todd"].turns[0] if pair["todd"].turns else None
        morgana_turn = pair["morgana"].turns[0] if pair["morgana"].turns else None
        if not todd_turn or not morgana_turn or todd_turn.error or morgana_turn.error:
            continue
        prompt = todd_turn.user
        similarity = round(_pair_similarity(todd_turn.assistant, morgana_turn.assistant, prompt), 3)
        policy = _PERSONALITY_PAIR_POLICIES.get(dimension, "ASSINATURA_LEVE")
        both_concept = _concept_pass(pair["todd"]) and _concept_pass(pair["morgana"])

        if policy == "CONVERGENCIA_OK":
            status = "CONVERGENCIA_OK"
            reason = "a situação admite a mesma conclusão sensata; similaridade não é penalizada"
        elif policy == "ASSINATURA_LEVE":
            status = "ASSINATURA_LEVE"
            reason = "diferença pode aparecer só em foco, ritmo ou formulação; não há obrigação de divergir"
        elif similarity >= 0.72:
            status = "REVISAR_CONVERGENCIA"
            reason = "sobreposição alta em eixo aberto onde perspectiva deveria aparecer"
        elif similarity <= 0.45 or (both_concept and similarity < 0.68):
            status = "DISTINCAO_PRESENTE"
            reason = "há separação observável sem exigir respostas opostas"
        else:
            status = "MISTO"
            reason = "há alguma separação, mas o par ainda merece leitura humana"

        observations.setdefault(dimension, []).append({
            "batch": batch,
            "policy": policy,
            "status": status,
            "similarity": similarity,
            "both_concept_pass": both_concept,
            "reason": reason,
        })

    axes: dict[str, dict[str, object]] = {}
    for dimension, items in observations.items():
        policy = str(items[0]["policy"])
        if policy == "DIVERGENCIA_ESPERADA":
            distinct = sum(item["status"] == "DISTINCAO_PRESENTE" for item in items)
            mixed = sum(item["status"] == "MISTO" for item in items)
            review = sum(item["status"] == "REVISAR_CONVERGENCIA" for item in items)
            total = len(items)
            ratio = distinct / total if total else 0.0
            aggregate = "BATE" if ratio >= 0.75 else ("MISTO" if ratio >= 0.50 else "REVISAR")
            axes[dimension] = {
                "policy": policy, "status": aggregate, "distinct": distinct, "mixed": mixed,
                "review": review, "total": total, "observations": items,
            }
        else:
            avg = round(sum(float(item["similarity"]) for item in items) / len(items), 3) if items else None
            axes[dimension] = {
                "policy": policy,
                "status": "OK_CONTEXTUAL" if policy == "CONVERGENCIA_OK" else "OBSERVAR",
                "average_similarity": avg, "total": len(items), "observations": items,
            }

    counts = {
        "divergencia_bate": sum(v.get("status") == "BATE" for v in axes.values()),
        "divergencia_misto": sum(v.get("status") == "MISTO" for v in axes.values()),
        "divergencia_revisar": sum(v.get("status") == "REVISAR" for v in axes.values()),
        "convergencia_ok": sum(v.get("policy") == "CONVERGENCIA_OK" for v in axes.values()),
        "assinatura_leve": sum(v.get("policy") == "ASSINATURA_LEVE" for v in axes.values()),
    }
    return {"axes": axes, "counts": counts, "heuristic": "surface overlap without prompt vocabulary; human review remains authoritative"}

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


def _multiagent_summary(results: list[ScenarioResult]) -> dict[str, object] | None:
    turns = [turn for scenario in results for turn in scenario.turns if turn.speakers]
    if not turns:
        return None
    both = sum({reply.agent_id for reply in turn.speakers} >= {"todd", "morgana"} for turn in turns)
    solo = sum(len({reply.agent_id for reply in turn.speakers}) == 1 for turn in turns)
    speaker_counts = {
        agent: sum(reply.agent_id == agent for turn in turns for reply in turn.speakers)
        for agent in ("morgana", "todd")
    }
    return {
        "turns": len(turns),
        "both_spoke": both,
        "solo_turns": solo,
        "speaker_counts": speaker_counts,
    }


async def _send_multiagent(service: ChatService, session_id, text: str) -> tuple[list[SpeakerResult], dict[str, float | None]]:
    replies: list[SpeakerResult] = []
    current: SpeakerResult | None = None
    loop = asyncio.get_running_loop()
    turn_started = loop.time()
    speaker_started_at: dict[int, float] = {}
    first_response_at: float | None = None
    async for event in service.stream_turn(session_id, text):
        now = loop.time()
        if event.type == "speaker_start":
            current = SpeakerResult(
                agent_id=event.agent_id,
                reason=event.reason,
                start_offset_seconds=round(now - turn_started, 3),
            )
            replies.append(current)
            speaker_started_at[id(current)] = now
        elif event.type == "token":
            if current is None or current.agent_id != event.agent_id:
                current = SpeakerResult(
                    agent_id=event.agent_id,
                    reason=event.reason,
                    start_offset_seconds=round(now - turn_started, 3),
                )
                replies.append(current)
                speaker_started_at[id(current)] = now
            if current.first_response_offset_seconds is None:
                current.first_response_offset_seconds = round(now - turn_started, 3)
                current.generation_seconds = round(now - speaker_started_at.get(id(current), turn_started), 3)
                if first_response_at is None:
                    first_response_at = now
            current.text += event.text or ""
    first = replies[0].first_response_offset_seconds if replies else None
    second_gap: float | None = None
    ready = [reply.first_response_offset_seconds for reply in replies if reply.first_response_offset_seconds is not None]
    if len(ready) >= 2:
        second_gap = round(float(ready[1]) - float(ready[0]), 3)
    return replies, {
        "time_to_first_response_seconds": first,
        "second_speaker_gap_seconds": second_gap,
    }


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return round(ordered[index], 3)


def _latency_summary(results: list[ScenarioResult]) -> dict[str, object] | None:
    turns = [turn for scenario in results for turn in scenario.turns if turn.speakers and not turn.error]
    if not turns:
        return None
    ttfr = [float(turn.time_to_first_response_seconds) for turn in turns if turn.time_to_first_response_seconds is not None]
    totals = [float(turn.duration_seconds) for turn in turns]
    solo = [float(turn.duration_seconds) for turn in turns if len(turn.speakers) == 1]
    multi = [float(turn.duration_seconds) for turn in turns if len(turn.speakers) >= 2]
    gaps = [float(turn.second_speaker_gap_seconds) for turn in turns if turn.second_speaker_gap_seconds is not None]
    by_agent: dict[str, list[float]] = {"morgana": [], "todd": []}
    for turn in turns:
        for speaker in turn.speakers:
            if speaker.generation_seconds is not None and speaker.agent_id in by_agent:
                by_agent[speaker.agent_id].append(float(speaker.generation_seconds))

    def stats(values: list[float]) -> dict[str, float | int | None]:
        return {
            "count": len(values),
            "mean": round(statistics.fmean(values), 3) if values else None,
            "median": round(statistics.median(values), 3) if values else None,
            "p95": _percentile(values, 0.95),
            "max": round(max(values), 3) if values else None,
        }

    return {
        "time_to_first_response": stats(ttfr),
        "turn_total": stats(totals),
        "solo_turn_total": stats(solo),
        "multiagent_turn_total": stats(multi),
        "second_speaker_gap": stats(gaps),
        "speaker_generation": {agent: stats(values) for agent, values in by_agent.items()},
    }


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
            session = service.create_session(title=f"E2E {scenario.id}", agent_id=scenario.agent_id)
            scenario_result = ScenarioResult(
                id=scenario.id,
                category=scenario.category,
                description=scenario.description,
                review_focus=scenario.review_focus,
            )
            for turn in scenario.turns:
                started = loop.time()
                turn_result = TurnResult(user=turn.user, speaker_id=(scenario.agent_id if suite in {"agents", "agent_personality", "agent_mega", "agent_human_quick", "agent_human_baseline"} else None))
                try:
                    if suite in {"agent_integrated", "agent_long_call"} or (suite in {"agent_human_quick", "agent_human_baseline"} and scenario.agent_id is None):
                        replies, latency = await _send_multiagent(service, session.id, turn.user)
                        turn_result.speakers = replies
                        turn_result.time_to_first_response_seconds = latency.get("time_to_first_response_seconds")
                        turn_result.second_speaker_gap_seconds = latency.get("second_speaker_gap_seconds")
                        turn_result.speaker_id = replies[0].agent_id if replies else None
                        turn_result.assistant = "\n\n".join(f"{reply.agent_id}: {reply.text}" for reply in replies)
                        turn_result.checks = evaluate_multiagent_turn(
                            [(reply.agent_id, reply.text) for reply in replies], turn.checks, turn.user
                        )
                        generic = (
                            CheckSpec('not_contains_any', ("minha persona", "como campanario", "como campanário"), label='sem metalinguagem de persona'),
                            CheckSpec('not_contains_any', ("Todd:", "Morgana:", "Campanario:", "Campanário:"), label='não simula outros speakers'),
                            CheckSpec('no_internal_prompt', label='sem prompt interno'),
                            CheckSpec('not_embodied_expression', severity='warn', label='sem encenação humana'),
                        )
                        for reply in replies:
                            for check in evaluate_response(reply.text, generic, user_text=turn.user):
                                check.label = f"{reply.agent_id.capitalize()} — {check.label}"
                                turn_result.checks.append(check)
                    else:
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
        personality_concept = _personality_concept_summary(results)
        personality_pair = _personality_pair_summary(results)
        multiagent = _multiagent_summary(results)
        latency = _latency_summary(results)
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
                "personality_concept": personality_concept,
                "personality_pair": personality_pair,
                "multiagent": multiagent,
                "latency": latency,
                "note": "Avaliação de personalidade é heurística e contextual: convergência é permitida quando natural; divergência só é cobrada em eixos abertos. Revisão humana continua autoritativa.",
            },
        )
        return report
    finally:
        shutil.rmtree(root_tmp, ignore_errors=True)


