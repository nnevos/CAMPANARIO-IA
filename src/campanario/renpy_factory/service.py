from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

from platformdirs import user_data_path

from campanario.chat.models import MessageRole
from campanario.model.protocol import ModelMessage, ModelProvider, ModelRequest

from .compiler import compile_script, render_code_compat_report, render_evidence_report, render_gdd_docx, render_gdd_markdown, render_options, render_visual_prompts, validate_compiled_project
from .evidence import build_evidence_catalog, catalog_map
from .extractor import extract_ebook
from .models import GDDMetadataSpec, QualityAuditSpec, QualityIssueSpec, QuestionSpec, RenPyGDD, RouteSpec, ValidationReport
from .prompts import SYSTEM_PROMPT, append_quality_feedback, build_choice_consistency_audit_prompt, build_final_adversarial_audit_prompt, build_main_question_prompt, build_metadata_prompt, build_quality_audit_prompt, build_question_adversarial_audit_prompt, build_route_prompt, build_route_question_prompt
from .validator import evidence_quote_present, explicit_question_concepts, validate_gdd


MAX_STAGE_ATTEMPTS = 8
MAX_LOCAL_REPAIR_ATTEMPTS = 8
MAX_GLOBAL_REPAIR_CYCLES = 12


class RenPyFactoryError(RuntimeError):
    pass


class InsufficientEvidenceError(RenPyFactoryError):
    pass


class StageGenerationError(RenPyFactoryError):
    def __init__(self, failed_stage: str, partial_questions: list[QuestionSpec], cause: Exception) -> None:
        self.failed_stage = failed_stage
        self.partial_questions = partial_questions
        self.cause = cause
        super().__init__(f"A etapa {failed_stage} não pôde ser concluída após o fallback por pergunta.")


class GroundingValidationError(RenPyFactoryError):
    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in report.issues if issue.severity == "error")
        if not details:
            details = "falha de validação não especificada"
        super().__init__(f"O GDD foi rejeitado na validação estrutural/grounding: {details}")


def _ensure_distinct_route_titles(gdd: RenPyGDD) -> RenPyGDD:
    """Repair duplicate route titles without another model call.

    Route titles are navigation/editorial metadata, not pedagogical facts. A
    duplicated title must never block an otherwise valid GDD. Preserve the model
    title and add a deterministic route suffix only where needed.
    """
    routes = [("A", gdd.route_a), ("B", gdd.route_b), ("C", gdd.route_c)]
    normalized = [_normalize_title(route.title) for _, route in routes]
    counts = {value: normalized.count(value) for value in set(normalized)}
    for (code, route), key in zip(routes, normalized):
        if counts.get(key, 0) > 1:
            base = route.title.strip() or "Trilha temática"
            route.title = f"{base} — Eixo {code}"
    return gdd


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().strip())


def _default_renpy_output_root() -> Path:
    """Keep the legacy location unless the user explicitly configured a data directory."""
    from campanario.config import Settings
    config = Settings()
    if "data_dir" in config.model_fields_set:
        return config.data_dir / "renpy_factory"
    return user_data_path("Campanario", "Campanario") / "renpy_factory"


class RenPyFactoryService:
    def __init__(self, provider: ModelProvider, model: str, output_root: Path | None = None) -> None:
        self.provider = provider
        self.model = model
        self.output_root = output_root or _default_renpy_output_root()

    async def generate_gdd(self, filename: str, payload: bytes) -> dict[str, object]:
        """Stage 1: ebook -> validated, reviewable GDD only.

        Uploaded ebook bytes are never persisted. The run stores only derived GDD
        artifacts and the minimal evidence report required for review.
        """
        repair_history: list[dict[str, object]] = []
        ebook = extract_ebook(filename, payload)
        evidence_catalog = build_evidence_catalog(ebook)
        evidence_by_id = catalog_map(evidence_catalog)
        if len(evidence_catalog) < 10:
            raise InsufficientEvidenceError("O e-book não contém trechos textuais suficientes para sustentar 10 perguntas.")

        metadata = await self._generate_part(filename, "metadata", build_metadata_prompt(ebook), GDDMetadataSpec, max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history)
        main_question = await self._generate_part(
            filename, "main_question", build_main_question_prompt(ebook), QuestionSpec,
            evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id, max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
        )
        used_prompts = [main_question.prompt]
        routes_done: dict[str, RouteSpec] = {}
        try:
            route_a = await self._generate_route(filename, ebook, "A", used_prompts, evidence_by_id, repair_history=repair_history)
        except StageGenerationError as exc:
            return self._persist_partial_gdd(
                metadata=metadata, main_question=main_question, routes=routes_done, failed_route_code="A",
                partial_questions=exc.partial_questions, failed_stage=exc.failed_stage, error=exc.cause, repair_history=repair_history,
            )
        routes_done["A"] = route_a
        used_prompts.extend(q.prompt for q in route_a.questions)
        try:
            route_b = await self._generate_route(filename, ebook, "B", used_prompts, evidence_by_id, repair_history=repair_history)
        except StageGenerationError as exc:
            return self._persist_partial_gdd(
                metadata=metadata, main_question=main_question, routes=routes_done, failed_route_code="B",
                partial_questions=exc.partial_questions, failed_stage=exc.failed_stage, error=exc.cause, repair_history=repair_history,
            )
        routes_done["B"] = route_b
        used_prompts.extend(q.prompt for q in route_b.questions)
        try:
            route_c = await self._generate_route(filename, ebook, "C", used_prompts, evidence_by_id, repair_history=repair_history)
        except StageGenerationError as exc:
            return self._persist_partial_gdd(
                metadata=metadata, main_question=main_question, routes=routes_done, failed_route_code="C",
                partial_questions=exc.partial_questions, failed_stage=exc.failed_stage, error=exc.cause, repair_history=repair_history,
            )
        gdd = RenPyGDD(
            **metadata.model_dump(), main_question=main_question,
            route_a=route_a, route_b=route_b, route_c=route_c,
        )
        gdd, report, audit, converged = await self._self_heal_gdd(
            filename, ebook, gdd, evidence_by_id, repair_history
        )
        _resolve_source_hints(gdd, ebook.segments)
        if not converged:
            summary = "; ".join(f"{i.path}: {i.message}" for i in audit.issues[:4]) if audit else ""
            return self._persist_gdd_run(
                gdd, report, audit=audit, approved=False,
                rejection_reason=(
                    "A autocorreção esgotou o limite de segurança sem convergir. "
                    "O resultado foi preservado para diagnóstico técnico. " + summary
                ).strip(),
                repair_history=repair_history,
            )
        return self._persist_gdd_run(
            gdd, report, audit=audit, approved=True, repair_history=repair_history
        )

    async def _self_heal_gdd(
        self, filename: str, ebook, gdd: RenPyGDD, evidence_by_id: dict,
        repair_history: list[dict[str, object]],
    ) -> tuple[RenPyGDD, ValidationReport, QualityAuditSpec | None, bool]:
        """Keep repairing the smallest recoverable scope until the GDD converges.

        A pedagogical/structural defect is not a terminal state. The factory
        iterates validation -> surgical repair -> full revalidation. Only a hard
        safety ceiling or an unrecoverable model/provider failure can stop it.
        """
        audit: QualityAuditSpec | None = None
        previous_signature: tuple[str, ...] | None = None
        stagnant_cycles = 0
        for cycle in range(1, MAX_GLOBAL_REPAIR_CYCLES + 1):
            gdd = _ensure_distinct_route_titles(gdd)
            report = validate_gdd(gdd, ebook.normalized_text)
            if not report.valid:
                signature = tuple(sorted(f"{i.path}|{i.message}" for i in report.issues if i.severity == "error"))
                repair_history.append({
                    "scope": "validação estrutural", "status": "retry",
                    "message": f"Ciclo {cycle}: {len(signature)} problema(s) reparável(is) detectado(s); autocorreção iniciada."
                })
                gdd = await self._repair_duplicate_route_questions(
                    filename, ebook, gdd, report, evidence_by_id, repair_history=repair_history
                )
                report = validate_gdd(gdd, ebook.normalized_text)
                if not report.valid:
                    gdd = await self._repair_structural_issues_granular(
                        filename, ebook, gdd, report, evidence_by_id, repair_history
                    )
                    report = validate_gdd(gdd, ebook.normalized_text)
                if not report.valid:
                    new_signature = tuple(sorted(f"{i.path}|{i.message}" for i in report.issues if i.severity == "error"))
                    stagnant_cycles = stagnant_cycles + 1 if new_signature == previous_signature else 0
                    previous_signature = new_signature
                    if stagnant_cycles >= 2:
                        repair_history.append({
                            "scope": "validação estrutural", "status": "retry",
                            "message": "O mesmo conjunto de erros persistiu; a Fábrica escalou a estratégia e continuará tentando no próximo ciclo."
                        })
                    continue

            audit = _merge_report_quality(await self._combined_quality_audit(ebook, gdd), report)
            if audit.passed:
                adversarial = await self._approval_gate_audit(ebook, gdd)
                if adversarial.passed:
                    repair_history.append({
                        "scope": "GDD completo", "status": "fixed",
                        "message": f"Ciclo {cycle}: estrutura, grounding, auditorias pedagógicas e auditoria adversarial passaram; nenhum bloqueio permanece."
                    })
                    return RenPyGDD.model_validate(gdd.model_dump()), report, adversarial, True
                audit = adversarial
                repair_history.append({
                    "scope": "auditoria adversarial", "status": "retry",
                    "message": f"Ciclo {cycle}: a auditoria adversarial encontrou {len(audit.issues)} defeito(s) que as passadas anteriores não detectaram; reparo cirúrgico iniciado."
                })

            repair_history.append({
                "scope": "auditoria pedagógica", "status": "retry",
                "message": f"Ciclo {cycle}: {len(audit.issues)} inconsistência(s) detectada(s); reparo automático do menor escopo iniciado."
            })
            gdd, audit = await self._repair_quality_questions_granular(
                filename, ebook, gdd, audit, evidence_by_id, report, repair_history=repair_history
            )
            if audit.passed:
                report = validate_gdd(gdd, ebook.normalized_text)
                adversarial = await self._approval_gate_audit(ebook, gdd)
                if adversarial.passed:
                    repair_history.append({
                        "scope": "GDD completo", "status": "fixed",
                        "message": f"Ciclo {cycle}: inconsistências foram corrigidas e o GDD também passou na auditoria adversarial final."
                    })
                    return RenPyGDD.model_validate(gdd.model_dump()), report, adversarial, True
                audit = adversarial
                repair_history.append({
                    "scope": "auditoria adversarial", "status": "retry",
                    "message": f"Ciclo {cycle}: após o reparo, a barreira adversarial ainda encontrou {len(audit.issues)} defeito(s); a Fábrica continuará corrigindo."
                })

            # Remaining non-question issues are usually narrative/metadata or a
            # route-level coherence problem. Repair only those owners and loop.
            issue_map = _group_quality_issues(audit)
            if issue_map.get("metadata"):
                metadata = await self._generate_part(
                    filename, f"metadata_self_heal_{cycle}",
                    append_quality_feedback(build_metadata_prompt(ebook), issue_map["metadata"]),
                    GDDMetadataSpec, max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                for key in GDDMetadataSpec.model_fields:
                    setattr(gdd, key, getattr(metadata, key))
                repair_history.append({
                    "scope": "Narrativa / metadados", "status": "fixed",
                    "message": "Problemas narrativos/metadados foram reescritos automaticamente sem alterar o banco já válido."
                })
            route_map = {"route_a": ("A", gdd.route_a), "route_b": ("B", gdd.route_b), "route_c": ("C", gdd.route_c)}
            for route_key, route_code in (("route_a", "A"), ("route_b", "B"), ("route_c", "C")):
                route_issues = issue_map.get(route_key, [])
                if not route_issues:
                    continue
                # Question-specific issues were already handled above. Only
                # regenerate the route if the audit points to the route itself.
                if all("questions[" in msg for msg in route_issues):
                    continue
                excluded = [gdd.main_question.prompt]
                for other_key, (_, other_route) in route_map.items():
                    if other_key != route_key:
                        excluded.extend(q.prompt for q in other_route.questions)
                repaired = await self._generate_part(
                    filename, f"{route_key}_self_heal_{cycle}",
                    append_quality_feedback(build_route_prompt(ebook, route_code, excluded), route_issues),
                    RouteSpec, evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                    max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                setattr(gdd, route_key, repaired)
                route_map[route_key] = (route_code, repaired)
                repair_history.append({
                    "scope": route_key, "status": "fixed",
                    "message": "Problema de coerência da trilha foi corrigido automaticamente e será revalidado no próximo ciclo."
                })

        final_report = validate_gdd(gdd, ebook.normalized_text)
        if final_report.valid:
            audit = _merge_report_quality(await self._combined_quality_audit(ebook, gdd), final_report)
            if audit.passed:
                audit = await self._approval_gate_audit(ebook, gdd)
        return RenPyGDD.model_validate(gdd.model_dump()), final_report, audit, False

    async def _repair_structural_issues_granular(
        self, filename: str, ebook, gdd: RenPyGDD, report: ValidationReport,
        evidence_by_id: dict, repair_history: list[dict[str, object]],
    ) -> RenPyGDD:
        """Repair structural/grounding errors at question scope whenever possible."""
        grouped: dict[tuple[str, int | None], list[str]] = {}
        for issue in report.issues:
            if issue.severity != "error":
                continue
            path = issue.path.casefold().strip()
            if path.startswith("main_question"):
                grouped.setdefault(("main_question", None), []).append(f"{issue.path}: {issue.message}")
                continue
            match = re.match(r"^(route_[abc])\.questions\[(\d+)\]", path)
            if match:
                grouped.setdefault((match.group(1), int(match.group(2)) - 1), []).append(f"{issue.path}: {issue.message}")
                continue
            for owner in ("route_a", "route_b", "route_c"):
                if path.startswith(owner) or path == "routes":
                    grouped.setdefault((owner, None), []).append(f"{issue.path}: {issue.message}")

        route_map = {"route_a": ("A", gdd.route_a), "route_b": ("B", gdd.route_b), "route_c": ("C", gdd.route_c)}
        for (owner, qindex), messages in grouped.items():
            if owner == "main_question":
                gdd.main_question = await self._generate_part(
                    filename, "main_question_structural_self_heal",
                    append_quality_feedback(build_main_question_prompt(ebook), messages),
                    QuestionSpec, evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                    max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                repair_history.append({"scope": "Pergunta principal", "status": "fixed", "message": "Falha estrutural/grounding corrigida automaticamente."})
                continue
            route_code, route = route_map[owner]
            if qindex is not None and 0 <= qindex < len(route.questions):
                excluded = [gdd.main_question.prompt]
                forbidden: set[str] = set(explicit_question_concepts(gdd.main_question.prompt))
                for other_owner, (_, other_route) in route_map.items():
                    for idx, q in enumerate(other_route.questions):
                        if other_owner == owner and idx == qindex:
                            continue
                        excluded.append(q.prompt)
                        forbidden.update(explicit_question_concepts(q.prompt))
                prompt = append_quality_feedback(
                    build_route_question_prompt(ebook, route_code, qindex + 1, excluded, sorted(forbidden)), messages
                )
                route.questions[qindex] = await self._generate_part(
                    filename, f"{owner}_q{qindex + 1}_structural_self_heal", prompt, QuestionSpec,
                    evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                    max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                repair_history.append({"scope": f"{route_code}{qindex + 1}", "status": "fixed", "message": "Falha estrutural/grounding da pergunta corrigida automaticamente."})
            else:
                excluded = [gdd.main_question.prompt]
                for other_owner, (_, other_route) in route_map.items():
                    if other_owner != owner:
                        excluded.extend(q.prompt for q in other_route.questions)
                repaired = await self._generate_part(
                    filename, f"{owner}_structural_self_heal",
                    append_quality_feedback(build_route_prompt(ebook, route_code, excluded), messages),
                    RouteSpec, evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                    max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                setattr(gdd, owner, repaired)
                route_map[owner] = (route_code, repaired)
                repair_history.append({"scope": owner, "status": "fixed", "message": "Estrutura da trilha foi reconstruída automaticamente."})
        return RenPyGDD.model_validate(gdd.model_dump())

    def _persist_gdd_run(
        self,
        gdd: RenPyGDD,
        report: ValidationReport,
        *,
        audit: QualityAuditSpec | None,
        approved: bool,
        rejection_reason: str = "",
        repair_history: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        run_id = uuid4().hex
        run_dir = self.output_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "gdd.json").write_text(gdd.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "GDD.md").write_text(render_gdd_markdown(gdd), encoding="utf-8")
        render_gdd_docx(gdd, run_dir / "GDD.docx")
        (run_dir / "EVIDENCE_REPORT.md").write_text(render_evidence_report(gdd, report), encoding="utf-8")
        audit_issues = [] if audit is None else [f"{i.path}: {i.message}" for i in audit.issues]
        validation_issues = [f"{i.path}: {i.message}" for i in report.issues if i.severity == "error"]
        audit_items: list[dict[str, str]] = []
        for issue in report.issues:
            audit_items.append({
                "source": "validation",
                "severity": issue.severity,
                "path": issue.path,
                "message": issue.message,
            })
        if audit is not None:
            for issue in audit.issues:
                audit_items.append({
                    "source": "quality",
                    "severity": "error",
                    "path": issue.path,
                    "message": issue.message,
                })
        repair_history = list(repair_history or [])
        audit_lines = [
            "# AUDITORIA DO GDD",
            "",
            f"Status: {'APROVADO' if approved else 'NÃO CONCLUÍDO AUTOMATICAMENTE'}",
            "",
        ]
        if rejection_reason:
            audit_lines += [f"Motivo geral: {rejection_reason}", ""]
        if validation_issues:
            audit_lines += ["## Validação estrutural / grounding", *[f"- {x}" for x in validation_issues], ""]
        if audit_issues:
            audit_lines += ["## Auditoria pedagógica", *[f"- {x}" for x in audit_issues], ""]
        if repair_history:
            audit_lines += ["## Autocorreções executadas"]
            for event in repair_history:
                mark = "✓" if event.get("status") == "fixed" else "•"
                audit_lines.append(f"- {mark} {event.get('scope', 'geração')}: {event.get('message', '')}")
            audit_lines.append("")
        if approved and not validation_issues and not audit_issues:
            audit_lines += ["Nenhum bloqueio permanece após validação e autocorreção.", ""]
        (run_dir / "AUDIT_REPORT.md").write_text("\n".join(audit_lines), encoding="utf-8")
        status = {
            "approved": approved,
            "rejection_reason": rejection_reason,
            "validation_issues": validation_issues,
            "quality_issues": audit_issues,
        }
        (run_dir / "run_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "README_GDD.txt").write_text(
            (
                "ETAPA 1 concluída e aprovada. Revise GDD.docx/GDD.md antes de compilar. "
                if approved else
                "ETAPA 1 não convergiu automaticamente dentro do limite de segurança. O GDD permanece disponível para diagnóstico, "
                "mas a compilação está bloqueada porque ainda existem inconsistências. "
            ) + "O e-book enviado não foi salvo.\n", encoding="utf-8"
        )
        return {
            "run_id": run_id, "title": gdd.title, "profile": "legacy_un01_10x21",
            "questions": 10, "alternatives": 21, "evidence_checked": report.checked_evidence,
            "approved": approved,
            "quality_audit": "approved" if approved else "rejected",
            "quality_issues": len(audit_issues),
            "issues": validation_issues + audit_issues,
            "audit_items": audit_items,
            "audit_counts": {
                "errors": sum(1 for item in audit_items if item["severity"] == "error"),
                "warnings": sum(1 for item in audit_items if item["severity"] == "warning"),
            },
            "auto_repair": {
                "enabled": True,
                "question_attempts": MAX_LOCAL_REPAIR_ATTEMPTS,
                "global_cycles": MAX_GLOBAL_REPAIR_CYCLES,
                "strategy": "menor_escopo_ate_convergir",
            },
            "repair_history": repair_history,
            "repair_summary": {
                "fixed": sum(1 for e in repair_history if e.get("status") == "fixed"),
                "attempts": len(repair_history),
            },
            "rejection_reason": rejection_reason,
            "warnings": [i.message for i in report.issues if i.severity == "warning"],
            "gdd_docx_url": f"/api/v1/renpy-factory/runs/{run_id}/files/GDD.docx",
            "gdd_md_url": f"/api/v1/renpy-factory/runs/{run_id}/files/GDD.md",
            "gdd_json_url": f"/api/v1/renpy-factory/runs/{run_id}/files/gdd.json",
            "audit_report_url": f"/api/v1/renpy-factory/runs/{run_id}/files/AUDIT_REPORT.md",
            "run_dir": str(run_dir), "gdd": gdd.model_dump(mode="json"),
            "stage": "gdd_ready" if approved else "gdd_rejected",
        }

    def compile_run(self, run_id: str) -> dict[str, object]:
        """Stage 2: approved gdd.json -> script/screens/options. No model call."""
        if not run_id.isalnum():
            raise FileNotFoundError(run_id)
        run_dir = self.output_root / run_id
        status_path = run_dir / "run_status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if not status.get("approved", False):
                raise RenPyFactoryError("Este GDD ainda não concluiu a autocorreção com sucesso. A compilação permanece bloqueada até o estado ficar consistente.")
        gdd_path = run_dir / "gdd.json"
        if not gdd_path.exists():
            raise FileNotFoundError(run_id)
        gdd = RenPyGDD.model_validate_json(gdd_path.read_text(encoding="utf-8"))
        game_dir = run_dir / "project" / "game"
        template_game = Path(__file__).with_name("template") / "game"
        shutil.copytree(template_game, game_dir, dirs_exist_ok=True)
        script_text = compile_script(gdd)
        options_text = render_options(gdd.title)
        (game_dir / "script.rpy").write_text(script_text, encoding="utf-8")
        (game_dir / "options.rpy").write_text(options_text, encoding="utf-8")
        # screens.rpy comes verbatim from the user's canonical Ren'Py template.
        if not (game_dir / "screens.rpy").exists():
            raise RenPyFactoryError("Template canônico sem screens.rpy.")
        screens_text = (game_dir / "screens.rpy").read_text(encoding="utf-8-sig")
        compat_issues = validate_compiled_project(gdd, script_text, screens_text, options_text)
        (run_dir / "CODE_COMPAT_REPORT.md").write_text(
            render_code_compat_report(gdd, compat_issues), encoding="utf-8"
        )
        if compat_issues:
            raise RenPyFactoryError(
                "O preflight de compatibilidade do código falhou: " + "; ".join(compat_issues[:6])
            )
        (game_dir / "images_LEIA.txt").write_text(
            "As imagens ainda são placeholders. A etapa visual/build WEB permanece fora deste fluxo mínimo.\n",
            encoding="utf-8",
        )
        (run_dir / "README_CODIGO.txt").write_text(
            "ETAPA 2 concluída. script.rpy foi compilado exclusivamente de gdd.json; "
            "screens.rpy é cópia intacta do template; options.rpy altera apenas config.name, build.name e config.save_directory.\n", encoding="utf-8"
        )
        zip_path = self.output_root / f"{run_id}.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in run_dir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(run_dir))
        return {
            "run_id": run_id, "title": gdd.title, "stage": "code_ready",
            "download_url": f"/api/v1/renpy-factory/runs/{run_id}/download",
            "script_url": f"/api/v1/renpy-factory/runs/{run_id}/files/project/game/script.rpy",
            "screens_url": f"/api/v1/renpy-factory/runs/{run_id}/files/project/game/screens.rpy",
            "options_url": f"/api/v1/renpy-factory/runs/{run_id}/files/project/game/options.rpy",
            "compat_report_url": f"/api/v1/renpy-factory/runs/{run_id}/files/CODE_COMPAT_REPORT.md",
            "compatibility": "passed",
            "run_dir": str(run_dir),
        }

    async def generate(self, filename: str, payload: bytes) -> dict[str, object]:
        """Compatibility path: create GDD first, then compile deterministically."""
        result = await self.generate_gdd(filename, payload)
        compiled = self.compile_run(str(result["run_id"]))
        return {**result, **compiled, "gdd": result["gdd"]}

    def artifact_path(self, run_id: str, relative_path: str) -> Path:
        if not run_id.isalnum():
            raise FileNotFoundError(run_id)
        safe = Path(relative_path)
        if safe.is_absolute() or ".." in safe.parts:
            raise FileNotFoundError(relative_path)
        root = (self.output_root / run_id).resolve()
        path = (root / safe).resolve()
        if root not in path.parents and path != root:
            raise FileNotFoundError(relative_path)
        if not path.is_file():
            raise FileNotFoundError(relative_path)
        return path

    async def _repair_duplicate_route_questions(
        self, filename: str, ebook, gdd: RenPyGDD, report: ValidationReport, evidence_by_id: dict, repair_history: list[dict[str, object]] | None = None
    ) -> RenPyGDD:
        """Repair duplicated/reused route questions at the exact question level.

        The validator already knows the precise offending path. Treat that as a
        repair instruction rather than a reason to regenerate a whole route. Each
        offending question uses the same convergent retry budget as the rest of the factory; after every attempt
        the complete GDD is revalidated. This lets the factory notice when a first
        repair still reused the same concept and retry only that question again.
        """
        route_map = {
            "route_a": ("A", gdd.route_a),
            "route_b": ("B", gdd.route_b),
            "route_c": ("C", gdd.route_c),
        }

        def repair_targets(current_report: ValidationReport) -> dict[tuple[str, int], list[str]]:
            targets: dict[tuple[str, int], list[str]] = {}
            for issue in current_report.issues:
                if issue.severity != "error":
                    continue
                match = re.match(r"^(route_[abc])\.questions\[(\d+)\]$", issue.path.casefold().strip())
                if not match:
                    continue
                message = issue.message.casefold()
                if "conceito repetido" not in message and "pergunta duplicada" not in message:
                    continue
                targets.setdefault((match.group(1), int(match.group(2)) - 1), []).append(issue.message)
            return targets

        current_report = report
        targets = repair_targets(current_report)
        if not targets:
            return gdd

        # Earlier questions keep ownership of a concept; later offending questions
        # are repaired. The order is stable so the result is deterministic.
        for route_key, qindex in sorted(targets):
            route_code, route = route_map[route_key]
            last_messages = targets[(route_key, qindex)]

            for attempt in range(1, MAX_LOCAL_REPAIR_ATTEMPTS + 1):
                excluded_prompts: list[str] = [gdd.main_question.prompt]
                forbidden_concepts: set[str] = set(explicit_question_concepts(gdd.main_question.prompt))
                for other_key, (_, other_route) in route_map.items():
                    for idx, question in enumerate(other_route.questions):
                        if other_key == route_key and idx == qindex:
                            continue
                        excluded_prompts.append(question.prompt)
                        forbidden_concepts.update(explicit_question_concepts(question.prompt))

                repair_prompt = build_route_question_prompt(
                    ebook, route_code, qindex + 1, excluded_prompts, sorted(forbidden_concepts)
                )
                repair_prompt = append_quality_feedback(
                    repair_prompt,
                    [
                        *last_messages,
                        "Corrija SOMENTE esta pergunta; não altere a rota inteira.",
                        "A nova pergunta deve avaliar um conceito central diferente de todos os conceitos proibidos listados.",
                        f"Tentativa de auto-reparo granular {attempt}/{MAX_LOCAL_REPAIR_ATTEMPTS}.",
                    ],
                )
                candidate = await self._generate_part(
                    filename, f"{route_key}_q{qindex + 1}_surgical_repair_{attempt}",
                    repair_prompt, QuestionSpec,
                    evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                    max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                )
                route.questions[qindex] = candidate

                # Revalidate the whole bank immediately. If this exact question is
                # clean, keep it. If it still collides, feed the new validator
                # messages into the next surgical attempt without touching anything
                # else.
                current_report = validate_gdd(gdd, ebook.normalized_text)
                remaining = repair_targets(current_report).get((route_key, qindex), [])
                if not remaining:
                    if repair_history is not None:
                        repair_history.append({"scope": f"{route_key}.questions[{qindex + 1}]", "status": "fixed", "message": "Pergunta duplicada/conceito repetido detectado e substituído automaticamente; banco completo revalidado."})
                    break
                last_messages = remaining

        return RenPyGDD.model_validate(gdd.model_dump())

    async def _generate_route(self, filename: str, ebook, route_code: str, excluded_prompts: list[str], evidence_by_id: dict, repair_history: list[dict[str, object]] | None = None) -> RouteSpec:
        part_name = f"route_{route_code.lower()}"
        try:
            return await self._generate_part(
                filename, part_name, build_route_prompt(ebook, route_code, excluded_prompts), RouteSpec,
                evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id, max_attempts=2, repair_history=repair_history,
            )
        except RenPyFactoryError:
            # A rota completa é o maior payload JSON do GDD. Se o modelo local
            # truncar/malformar esse bloco, gere B1/B2/B3 (ou A/C) separadamente.
            if repair_history is not None:
                repair_history.append({"scope": part_name, "status": "fixed", "message": "A rota completa não fechou JSON; a Fábrica mudou automaticamente para geração pergunta a pergunta."})
            questions: list[QuestionSpec] = []
            fallback_excluded = list(excluded_prompts)
            for index in range(1, 4):
                try:
                    question = await self._generate_part(
                        filename, f"{part_name}_q{index}",
                        build_route_question_prompt(ebook, route_code, index, fallback_excluded),
                        QuestionSpec, evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                        max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                    )
                except RenPyFactoryError as question_error:
                    raise StageGenerationError(f"{part_name}_q{index}", questions, question_error) from question_error
                questions.append(question)
                fallback_excluded.append(question.prompt)
            return RouteSpec(title=f"Trilha {route_code}", questions=questions)

    def _persist_partial_gdd(
        self, *, metadata: GDDMetadataSpec, main_question: QuestionSpec,
        routes: dict[str, RouteSpec], failed_route_code: str,
        partial_questions: list[QuestionSpec], failed_stage: str, error: Exception, repair_history: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        run_id = uuid4().hex
        run_dir = self.output_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        partial = {
            **metadata.model_dump(mode="json"),
            "main_question": main_question.model_dump(mode="json"),
            "routes": {key: value.model_dump(mode="json") for key, value in routes.items()},
            "failed_route": failed_route_code,
            "failed_stage": failed_stage,
            "partial_failed_route_questions": [q.model_dump(mode="json") for q in partial_questions],
        }
        (run_dir / "PARTIAL_GDD.json").write_text(json.dumps(partial, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# GAME DESIGN DOCUMENT (GDD) — RASCUNHO PARCIAL", "",
            "## 1. RESUMO DO JOGO",
            f"- Tema: {metadata.theme}",
            f"- Objetivo educacional: {metadata.educational_objective}", "",
            "## 3. PERSONAGENS, CENÁRIOS E ENREDO",
            f"- Personagem: {metadata.character.name} — {metadata.character.role}",
            f"- Cenário: {metadata.scenario.name}",
            f"- Conflito narrativo: {metadata.narrative_conflict}", "",
            "## 5. BANCO DE QUESTÕES — CONTEÚDO RECUPERADO", "",
            "### PERGUNTA PRINCIPAL", main_question.prompt,
        ]
        def emit_question(label: str, question: QuestionSpec) -> None:
            lines.extend(["", f"### {label}", question.prompt])
            for idx, choice in enumerate(question.choices):
                letter = chr(65 + idx)
                lines.append(f"- {letter}) {choice.text}")
                lines.append(f"  - ({choice.score:+d} | Justificativa: {choice.justification} | Feedback: {choice.feedback})")
        for code in ("A", "B", "C"):
            route = routes.get(code)
            if route is not None:
                lines.extend(["", f"## TRILHA {code} — {route.title}"])
                for idx, question in enumerate(route.questions, start=1):
                    emit_question(f"{code}{idx}", question)
            elif code == failed_route_code:
                lines.extend(["", f"## TRILHA {code} — INCOMPLETA"])
                for idx, question in enumerate(partial_questions, start=1):
                    emit_question(f"{code}{idx}", question)
                lines.extend(["", f"> Geração interrompida em {failed_stage}. Esta trilha ainda não está aprovada."])
        (run_dir / "PARTIAL_GDD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        repair_history = list(repair_history or [])
        history_text = ""
        if repair_history:
            history_text = "\n## Tentativas automáticas\n" + "".join(f"- {e.get('scope', 'geração')}: {e.get('message', '')}\n" for e in repair_history)
        (run_dir / "AUDIT_REPORT.md").write_text(
            "# GERAÇÃO PARCIAL\n\nStatus: FALHA TÉCNICA NÃO CONCLUÍDA\n\n"
            f"Etapa que falhou: {failed_stage}\nErro técnico: {type(error).__name__}\n"
            "O e-book original não foi salvo. O código Ren'Py permanece bloqueado.\n" + history_text,
            encoding="utf-8",
        )
        return {
            "run_id": run_id, "title": metadata.title, "approved": False,
            "stage": "technical_incomplete", "quality_audit": "not_run",
            "issues": [f"{failed_stage}: geração incompleta"],
            "rejection_reason": f"A geração não conseguiu concluir automaticamente {failed_stage}; o GDD parcial foi preservado para diagnóstico.",
            "repair_history": repair_history,
            "gdd_md_url": f"/api/v1/renpy-factory/runs/{run_id}/files/PARTIAL_GDD.md",
            "gdd_json_url": f"/api/v1/renpy-factory/runs/{run_id}/files/PARTIAL_GDD.json",
            "audit_report_url": f"/api/v1/renpy-factory/runs/{run_id}/files/AUDIT_REPORT.md",
            "run_dir": str(run_dir), "gdd": partial,
        }

    async def _combined_quality_audit(self, ebook, gdd: RenPyGDD) -> QualityAuditSpec:
        general = await self._quality_audit(ebook, gdd)
        consistency = await self._choice_consistency_audit(ebook, gdd)
        issues: list[QualityIssueSpec] = []
        seen: set[tuple[str, str]] = set()
        for issue in [*general.issues, *consistency.issues]:
            key = (issue.path, issue.message)
            if key not in seen:
                seen.add(key)
                issues.append(issue)
        return QualityAuditSpec(passed=general.passed and consistency.passed and not issues, issues=issues)

    async def _approval_gate_audit(self, ebook, gdd: RenPyGDD) -> QualityAuditSpec:
        """Strong final gate used only when normal QA thinks the GDD is clean.

        It attacks each question in isolation so score polarity cannot hide inside a
        long GDD, then runs one final adversarial pass over the complete document.
        """
        issues: list[QualityIssueSpec] = []
        seen: set[tuple[str, str]] = set()
        for path, question in _iter_gdd_questions(gdd):
            prompt = build_question_adversarial_audit_prompt(
                path, json.dumps(question.model_dump(), ensure_ascii=False)
            )
            audit = await self._audit_json_prompt(prompt, f"adversarial_{path.replace('.', '_').replace('[', '_').replace(']', '')}")
            for issue in audit.issues:
                key = (issue.path, issue.message)
                if key not in seen:
                    seen.add(key)
                    issues.append(issue)
        final_prompt = build_final_adversarial_audit_prompt(ebook, gdd.model_dump_json(indent=2))
        final = await self._audit_json_prompt(final_prompt, "final_adversarial_audit")
        for issue in final.issues:
            key = (issue.path, issue.message)
            if key not in seen:
                seen.add(key)
                issues.append(issue)
        return QualityAuditSpec(passed=not issues, issues=issues)

    async def _audit_json_prompt(self, prompt: str, part_name: str) -> QualityAuditSpec:
        last_error: Exception | None = None
        for attempt in range(MAX_STAGE_ATTEMPTS):
            user_prompt = prompt if attempt == 0 else prompt + f"\nTentativa automática {attempt + 1}/{MAX_STAGE_ATTEMPTS}. Retorne SOMENTE JSON mínimo válido."
            raw = await self._generate_json(user_prompt)
            try:
                return QualityAuditSpec.model_validate(_parse_json_payload(raw))
            except Exception as exc:
                last_error = exc
        diagnostic_id = self._write_failure_diagnostic(last_error, part_name=part_name)
        raise RenPyFactoryError(
            f"A auditoria '{part_name}' não retornou JSON válido. Diagnóstico salvo como {diagnostic_id}."
        ) from last_error

    async def _choice_consistency_audit(self, ebook, gdd: RenPyGDD) -> QualityAuditSpec:
        # Keep this audit focused and compact so the model cannot overlook a
        # score/text/justification contradiction inside a long narrative GDD.
        compact = {
            "main_question": gdd.main_question.model_dump(),
            "route_a": {"questions": [q.model_dump() for q in gdd.route_a.questions]},
            "route_b": {"questions": [q.model_dump() for q in gdd.route_b.questions]},
            "route_c": {"questions": [q.model_dump() for q in gdd.route_c.questions]},
        }
        prompt = build_choice_consistency_audit_prompt(ebook, json.dumps(compact, ensure_ascii=False))
        last_error: Exception | None = None
        for attempt in range(MAX_STAGE_ATTEMPTS):
            audit_prompt = prompt if attempt == 0 else prompt + f"\nTentativa automática {attempt + 1}/{MAX_STAGE_ATTEMPTS}. Retorne SOMENTE JSON mínimo válido, sem markdown."
            raw = await self._generate_json(audit_prompt)
            try:
                return QualityAuditSpec.model_validate(_parse_json_payload(raw))
            except Exception as exc:
                last_error = exc
        diagnostic_id = self._write_failure_diagnostic(last_error, part_name="choice_consistency_audit_json")
        raise RenPyFactoryError(
            f"A auditoria de consistência das alternativas não retornou JSON válido. Diagnóstico salvo como {diagnostic_id}."
        ) from last_error

    async def _repair_quality_questions_granular(
        self, filename: str, ebook, gdd: RenPyGDD, audit: QualityAuditSpec,
        evidence_by_id: dict, report: ValidationReport, repair_history: list[dict[str, object]] | None = None,
    ) -> tuple[RenPyGDD, QualityAuditSpec]:
        """Repair question-level quality failures without regenerating a whole route.

        Audit paths such as route_b.questions[2].choices[1] are collapsed to B2.
        The complete GDD is re-audited after each surgical repair, using the shared convergent retry budget per question. Metadata issues are intentionally left for the
        existing metadata-only repair path.
        """
        route_map = {
            "route_a": ("A", gdd.route_a),
            "route_b": ("B", gdd.route_b),
            "route_c": ("C", gdd.route_c),
        }

        def targets(current: QualityAuditSpec) -> dict[tuple[str, int], list[str]]:
            found: dict[tuple[str, int], list[str]] = {}
            for issue in current.issues:
                path = issue.path.casefold().strip()
                if path.startswith("main_question"):
                    found.setdefault(("main_question", 0), []).append(issue.message)
                    continue
                match = re.match(r"^(route_[abc])\.questions\[(\d+)\](?:\.choices\[\d+\])?", path)
                if match:
                    raw_index = int(match.group(2))
                    qindex = 0 if raw_index <= 0 else raw_index - 1
                    found.setdefault((match.group(1), qindex), []).append(issue.message)
            return found

        current = audit
        pending = targets(current)
        for (owner, qindex), messages in sorted(pending.items()):
            for attempt in range(1, MAX_LOCAL_REPAIR_ATTEMPTS + 1):
                if owner == "main_question":
                    prompt = append_quality_feedback(
                        build_main_question_prompt(ebook),
                        [*messages, "Corrija SOMENTE a pergunta principal e suas alternativas.",
                         "Garanta consistência entre texto, score, justificativa, feedback e evidência.",
                         f"Tentativa de auto-reparo granular de qualidade {attempt}/{MAX_LOCAL_REPAIR_ATTEMPTS}."],
                    )
                    candidate = await self._generate_part(
                        filename, f"main_question_quality_surgical_{attempt}", prompt, QuestionSpec,
                        evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                        max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                    )
                    gdd.main_question = candidate
                else:
                    route_code, route = route_map[owner]
                    excluded = [gdd.main_question.prompt]
                    forbidden: set[str] = set(explicit_question_concepts(gdd.main_question.prompt))
                    for other_owner, (_, other_route) in route_map.items():
                        for idx, question in enumerate(other_route.questions):
                            if other_owner == owner and idx == qindex:
                                continue
                            excluded.append(question.prompt)
                            forbidden.update(explicit_question_concepts(question.prompt))
                    prompt = build_route_question_prompt(ebook, route_code, qindex + 1, excluded, sorted(forbidden))
                    prompt = append_quality_feedback(
                        prompt,
                        [*messages, "Corrija SOMENTE esta pergunta e suas duas alternativas; não altere a rota inteira.",
                         "Garanta consistência entre texto, score, justificativa, feedback e evidência.",
                         "A alternativa +2 precisa ser realmente sustentada; a alternativa 0 precisa ser incompatível.",
                         f"Tentativa de auto-reparo granular de qualidade {attempt}/{MAX_LOCAL_REPAIR_ATTEMPTS}."],
                    )
                    candidate = await self._generate_part(
                        filename, f"{owner}_q{qindex + 1}_quality_surgical_{attempt}", prompt, QuestionSpec,
                        evidence_text=ebook.normalized_text, evidence_by_id=evidence_by_id,
                        max_attempts=MAX_STAGE_ATTEMPTS, repair_history=repair_history,
                    )
                    route.questions[qindex] = candidate

                structural = validate_gdd(gdd, ebook.normalized_text)
                if not structural.valid:
                    gdd = await self._repair_duplicate_route_questions(filename, ebook, gdd, structural, evidence_by_id)
                    structural = validate_gdd(gdd, ebook.normalized_text)
                current = _merge_report_quality(await self._combined_quality_audit(ebook, gdd), structural)
                remaining = targets(current).get((owner, qindex), [])
                if not remaining:
                    if repair_history is not None:
                        scope = "main_question" if owner == "main_question" else f"{owner}.questions[{qindex + 1}]"
                        repair_history.append({"scope": scope, "status": "fixed", "message": "Inconsistência pedagógica detectada e corrigida automaticamente; GDD completo reaudited."})
                    break
                messages = remaining

        # `current` is already the full combined audit after the last surgical
        # change. Avoid an unnecessary duplicate model audit here.
        return RenPyGDD.model_validate(gdd.model_dump()), current

    async def _quality_audit(self, ebook, gdd: RenPyGDD) -> QualityAuditSpec:
        last_error: Exception | None = None
        prompt = build_quality_audit_prompt(ebook, gdd.model_dump_json(indent=2))
        for attempt in range(MAX_STAGE_ATTEMPTS):
            audit_prompt = prompt if attempt == 0 else prompt + f"\nTentativa automática {attempt + 1}/{MAX_STAGE_ATTEMPTS}. Retorne SOMENTE JSON mínimo válido, sem markdown."
            raw = await self._generate_json(audit_prompt)
            try:
                return QualityAuditSpec.model_validate(_parse_json_payload(raw))
            except Exception as exc:
                last_error = exc
        diagnostic_id = self._write_failure_diagnostic(last_error, part_name="quality_audit_json")
        raise RenPyFactoryError(
            f"A auditoria pedagógica não retornou JSON válido. Diagnóstico salvo como {diagnostic_id}."
        ) from last_error

    async def _generate_part(self, filename: str, part_name: str, prompt: str, model_type, evidence_text: str | None = None, evidence_by_id: dict | None = None, *, max_attempts: int = 2, repair_history: list[dict[str, object]] | None = None):
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            user_prompt = prompt if attempt == 0 else _retry_part_prompt(prompt, part_name, grounding=bool(evidence_text and last_error)) + f"\nTentativa automática {attempt + 1}/{max_attempts}. Retorne o MENOR JSON possível que satisfaça exatamente o schema."
            raw = await self._generate_json(user_prompt)
            try:
                payload_json = _parse_json_payload(raw)
                if evidence_by_id is not None:
                    _hydrate_evidence_from_catalog(payload_json, evidence_by_id)
                candidate = model_type.model_validate(payload_json)
                structure_errors = _invalid_stage_structure(candidate, part_name)
                if structure_errors:
                    raise ValueError("invalid stage structure: " + "; ".join(structure_errors))
                if evidence_text is not None:
                    invalid_paths = _invalid_evidence_paths(candidate, evidence_text)
                    if invalid_paths:
                        raise ValueError(
                            "evidence quotes not verbatim at: " + ", ".join(invalid_paths)
                        )
                if attempt > 0 and repair_history is not None:
                    repair_history.append({"scope": part_name, "status": "fixed", "message": f"A etapa falhou {attempt} vez(es) e foi recuperada automaticamente na tentativa {attempt + 1}."})
                return candidate
            except Exception as exc:
                last_error = exc
                if repair_history is not None:
                    repair_history.append({"scope": part_name, "status": "retry", "message": f"Tentativa {attempt + 1}/{max_attempts} inválida ({type(exc).__name__}); nova tentativa automática iniciada."})
        diagnostic_id = self._write_failure_diagnostic(
            last_error, part_name=part_name
        )
        if last_error and ("evidence quotes not verbatim" in str(last_error) or "unknown evidence_id" in str(last_error)):
            message = (
                f"A etapa '{part_name}' não conseguiu selecionar evidências válidas do catálogo do e-book "
                f"após {max_attempts} tentativas automáticas. Diagnóstico salvo como {diagnostic_id}."
            )
        else:
            message = (
                f"A etapa '{part_name}' não retornou JSON válido após {max_attempts} tentativas automáticas. "
                f"Diagnóstico salvo como {diagnostic_id}."
            )
        raise RenPyFactoryError(message) from last_error

    async def _generate_json(self, user_prompt: str) -> str:
        request = ModelRequest(
            model=self.model,
            messages=(
                ModelMessage(MessageRole.SYSTEM, SYSTEM_PROMPT),
                ModelMessage(MessageRole.USER, user_prompt),
            ),
            # Ollama honors these hints; other providers can safely ignore them.
            response_format="json",
            temperature=0.1,
            max_output_tokens=8192,
            context_window=65536,
        )
        text = ""
        async for chunk in self.provider.stream(request):
            text += chunk.text
        return text.strip()

    def _write_failure_diagnostic(self, error: Exception | None, part_name: str = "full_gdd") -> str:
        """Persist only technical metadata; never persist uploaded ebook content or model output."""
        diagnostic_id = f"failed-{uuid4().hex[:12]}"
        failure_dir = self.output_root / "failed" / diagnostic_id
        failure_dir.mkdir(parents=True, exist_ok=True)
        (failure_dir / "README.txt").write_text(
            f"Etapa: {part_name}\nErro: {type(error).__name__ if error else 'unknown'}\n",
            encoding="utf-8",
        )
        return diagnostic_id

    def zip_path(self, run_id: str) -> Path:
        if not run_id.isalnum():
            raise FileNotFoundError(run_id)
        path = self.output_root / f"{run_id}.zip"
        if not path.exists():
            raise FileNotFoundError(run_id)
        return path



def _iter_gdd_questions(gdd: RenPyGDD):
    yield "main_question", gdd.main_question
    for route_name, route in (("route_a", gdd.route_a), ("route_b", gdd.route_b), ("route_c", gdd.route_c)):
        for idx, question in enumerate(route.questions, start=1):
            yield f"{route_name}.questions[{idx}]", question

def _retry_part_prompt(original_prompt: str, part_name: str, grounding: bool = False) -> str:
    grounding_rule = ""
    if grounding:
        grounding_rule = "\nEVIDÊNCIA: selecione apenas um evidence.source_hint ev_XXXX existente no CATÁLOGO e use USE_SOURCE_HINT em evidence.quote. Não invente IDs nem citações.\n"
    return original_prompt + f"""

REPETIÇÃO AUTOMÁTICA DE ROBUSTEZ — ETAPA {part_name}:
A tentativa anterior não pôde ser validada como JSON completo desta etapa.
Retorne SOMENTE o objeto JSON pedido nesta etapa, do primeiro {{ ao último }}, sem markdown e sem texto antes/depois.
Seja conciso. Não omita campos obrigatórios e não acrescente conhecimento novo.
{grounding_rule}
"""




def _invalid_stage_structure(candidate, part_name: str) -> list[str]:
    """Validate the score/cardinality contract before a stage is accepted.

    Pydantic validates shape and types, but the Ren'Py profile also has semantic
    cardinality/score invariants. Catch them here so a bad stage is retried locally
    instead of surfacing later as a misleading grounding failure.
    """
    errors: list[str] = []
    if isinstance(candidate, QuestionSpec):
        route_question = part_name.startswith("route_")
        expected = [2, 0] if route_question else [3, 1, 0]
        scores = [choice.score for choice in candidate.choices]
        expected_count = 2 if route_question else 3
        label = "pergunta de rota" if route_question else "pergunta principal"
        if len(candidate.choices) != expected_count:
            errors.append(f"{label} deve ter {expected_count} alternativas; recebeu {len(candidate.choices)}")
        if scores != expected:
            errors.append(f"scores da {label} devem ser {expected}; recebeu {scores}")
    elif isinstance(candidate, RouteSpec):
        if len(candidate.questions) != 3:
            errors.append(f"rota deve ter 3 perguntas; recebeu {len(candidate.questions)}")
        for idx, question in enumerate(candidate.questions, start=1):
            scores = [choice.score for choice in question.choices]
            if len(question.choices) != 2:
                errors.append(f"pergunta {idx} da rota deve ter 2 alternativas; recebeu {len(question.choices)}")
            if scores != [2, 0]:
                errors.append(f"scores da pergunta {idx} da rota devem ser [2, 0]; recebeu {scores}")
    return errors


def _group_validation_errors(report: ValidationReport) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"main_question": [], "route_a": [], "route_b": [], "route_c": []}
    for issue in report.issues:
        if issue.severity != "error":
            continue
        path = issue.path.casefold().strip()
        target = None
        for key in grouped:
            if path.startswith(key):
                target = key
                break
        if target is not None:
            grouped[target].append(f"{issue.path}: {issue.message}")
    return {key: value for key, value in grouped.items() if value}

def _invalid_evidence_paths(candidate, ebook_text: str) -> list[str]:
    paths: list[str] = []
    if isinstance(candidate, QuestionSpec):
        questions = [("question", candidate)]
    elif isinstance(candidate, RouteSpec):
        questions = [(f"questions[{idx}]", question) for idx, question in enumerate(candidate.questions, start=1)]
    else:
        return paths
    for qpath, question in questions:
        for cidx, choice in enumerate(question.choices, start=1):
            if not evidence_quote_present(choice.evidence.quote, ebook_text):
                paths.append(f"{qpath}.choices[{cidx}].evidence.quote")
    return paths



def _merge_report_quality(audit: QualityAuditSpec, report: ValidationReport) -> QualityAuditSpec:
    warnings = [QualityIssueSpec(path=i.path, message=i.message) for i in report.issues if i.severity == "warning"]
    if not warnings:
        return audit
    return QualityAuditSpec(passed=False, issues=[*audit.issues, *warnings])

def _group_quality_issues(audit: QualityAuditSpec) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"metadata": [], "main_question": [], "route_a": [], "route_b": [], "route_c": []}
    for issue in audit.issues:
        path = issue.path.casefold().strip()
        target = "metadata"
        for key in ("main_question", "route_a", "route_b", "route_c"):
            if path.startswith(key):
                target = key
                break
        grouped[target].append(f"{issue.path}: {issue.message}")
    return grouped

def _hydrate_evidence_from_catalog(payload: dict[str, object], evidence_by_id: dict) -> None:
    """Replace model-authored quote placeholders with verbatim source snippets.

    Unknown evidence IDs fail the stage. This makes evidence source-first: the
    model selects an existing ID but cannot author or paraphrase the quote.
    """
    found = 0

    def walk(node):
        nonlocal found
        if isinstance(node, dict):
            evidence = node.get("evidence")
            if isinstance(evidence, dict):
                evidence_id = str(evidence.get("source_hint", "")).strip()
                item = evidence_by_id.get(evidence_id)
                if item is None:
                    raise ValueError(f"unknown evidence_id: {evidence_id or '<empty>'}")
                evidence["quote"] = item.quote
                evidence["source_hint"] = f"{item.evidence_id} | {item.source_id}"
                found += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    if found == 0:
        raise ValueError("stage did not select any evidence_id")


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _extract_balanced_object(text: str) -> str:
    """Extract the first complete JSON object while respecting quoted braces."""
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    raise json.JSONDecodeError("unterminated JSON object", text, len(text))


def _parse_json_payload(text: str) -> dict[str, object]:
    cleaned = _strip_code_fence(text).lstrip("\ufeff")
    candidates = [cleaned]
    try:
        candidates.append(_extract_balanced_object(cleaned))
    except json.JSONDecodeError:
        pass

    seen: set[str] = set()
    errors: list[Exception] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        variants = [candidate, re.sub(r",\s*([}\]])", r"\1", candidate)]
        for variant in variants:
            try:
                parsed = json.loads(variant)
                if not isinstance(parsed, dict):
                    raise TypeError("GDD JSON root must be an object")
                return parsed
            except Exception as exc:
                errors.append(exc)
    if errors:
        raise errors[-1]
    raise ValueError("empty JSON response")


def build_default_factory_service(provider: ModelProvider, model: str) -> RenPyFactoryService:
    return RenPyFactoryService(provider, model)


def _resolve_source_hints(gdd: RenPyGDD, segments) -> None:
    questions = [gdd.main_question]
    questions.extend(gdd.route_a.questions)
    questions.extend(gdd.route_b.questions)
    questions.extend(gdd.route_c.questions)
    normalized = [(segment.source_id, " ".join(segment.text.casefold().split())) for segment in segments]
    for question in questions:
        for choice in question.choices:
            if choice.evidence.source_hint.startswith("ev_") and " | " in choice.evidence.source_hint:
                continue
            quote = " ".join(choice.evidence.quote.casefold().split())
            hits = [source_id for source_id, text in normalized if quote in text]
            choice.evidence.source_hint = ", ".join(hits) if hits else "unresolved"
