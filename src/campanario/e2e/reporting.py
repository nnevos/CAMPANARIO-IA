from __future__ import annotations
import html
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from .types import RunReport

def _markdown(report: RunReport) -> str:
    s = report.summary
    lines = [
        "# Campanario — Behavioral E2E Report",
        "",
        f"- Gerado em: `{report.generated_at}`",
        f"- Modelo: `{report.model}`",
        f"- Suite: `{report.suite}`",
        f"- Seed: `{report.seed}`",
        f"- Gate automático: **{s['automatic_gate']}**",
        f"- Cenários: {s['scenario_pass']} PASS / {s['scenario_warn']} WARN / {s['scenario_fail']} FAIL",
        f"- Checks: {s['check_pass']} PASS / {s['check_warn']} WARN / {s['check_fail']} FAIL",
        "",
        "> O gate automático mede propriedades observáveis. Naturalidade continua exigindo revisão humana do transcript.",
        "",
    ]
    for scenario in report.scenarios:
        lines.extend(
            [
                f"## [{scenario.status}] {scenario.id}",
                "",
                f"**Categoria:** {scenario.category}",
                "",
                scenario.description,
                "",
                f"**Revisar:** {scenario.review_focus}",
                "",
            ]
        )
        for turn_index, turn in enumerate(scenario.turns, start=1):
            lines.append(f"### Turno {turn_index}")
            lines.append("")
            lines.append(f"**Usuário:** {turn.user}")
            lines.append("")
            if turn.error:
                lines.append(f"**ERRO:** `{turn.error}`")
            else:
                lines.append(f"**Campanario:** {turn.assistant}")
            lines.append("")
            lines.append(f"Tempo: `{turn.duration_seconds:.3f}s`")
            if turn.checks:
                lines.append("")
                for check in turn.checks:
                    lines.append(f"- **{check.status}** — {check.label}: {check.detail}")
            lines.append("")
    return "\n".join(lines)


def _html(report: RunReport) -> str:
    s = report.summary
    badge = str(s["automatic_gate"]).lower()
    blocks: list[str] = []
    for scenario in report.scenarios:
        turns = []
        for turn in scenario.turns:
            checks = "".join(
                f'<li class="{check.status.lower()}"><b>{html.escape(check.status)}</b> — '
                f'{html.escape(check.label)}: {html.escape(check.detail)}</li>'
                for check in turn.checks
            )
            assistant = (
                f'<div class="error">{html.escape(turn.error)}</div>'
                if turn.error
                else f'<div class="bubble assistant">{html.escape(turn.assistant)}</div>'
            )
            turns.append(
                f'<div class="turn"><div class="bubble user">{html.escape(turn.user)}</div>'
                f'{assistant}<div class="meta">{turn.duration_seconds:.3f}s</div>'
                f'<ul>{checks}</ul></div>'
            )
        blocks.append(
            f'<section><h2><span class="pill {scenario.status.lower()}">{scenario.status}</span> '
            f'{html.escape(scenario.id)}</h2><p><b>{html.escape(scenario.category)}</b> — '
            f'{html.escape(scenario.description)}</p><p class="review"><b>Revisão humana:</b> '
            f'{html.escape(scenario.review_focus)}</p>{"".join(turns)}</section>'
        )
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campanario Behavioral E2E</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;margin:0 auto;padding:28px;background:#111;color:#eee;line-height:1.45}}h1,h2{{line-height:1.15}}section{{background:#1b1b1b;border:1px solid #333;border-radius:14px;padding:18px;margin:20px 0}}.summary{{background:#181818;padding:16px;border-radius:12px}}.pill{{font-size:.72em;padding:4px 9px;border-radius:999px}}.pass{{color:#8ee39f}}.warn{{color:#ffd36a}}.fail,.error{{color:#ff8b8b}}.pill.pass{{background:#173d21}}.pill.warn{{background:#493b13}}.pill.fail{{background:#4b1c1c}}.bubble{{padding:10px 12px;border-radius:10px;margin:8px 0;white-space:pre-wrap}}.user{{background:#253650}}.assistant{{background:#262626}}.meta{{font-size:.8em;color:#999}}ul{{margin-top:7px}}.review{{color:#c8c8c8;border-left:3px solid #666;padding-left:10px}}code{{background:#222;padding:2px 5px;border-radius:4px}}</style></head><body>
<h1>Campanario — Behavioral E2E</h1><div class="summary"><p>Modelo: <code>{html.escape(report.model)}</code> · suite: <code>{report.suite}</code> · seed: <code>{report.seed}</code></p><p>Gate automático: <span class="pill {badge}">{s['automatic_gate']}</span> · Cenários: {s['scenario_pass']} PASS / {s['scenario_warn']} WARN / {s['scenario_fail']} FAIL · Checks: {s['check_pass']} PASS / {s['check_warn']} WARN / {s['check_fail']} FAIL</p><p><b>Importante:</b> os checks automáticos medem propriedades observáveis; naturalidade precisa de revisão humana do transcript abaixo.</p></div>{''.join(blocks)}</body></html>'''


def save_report(report: RunReport, output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = output_root / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    payload = asdict(report)
    (run_dir / "report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(_markdown(report), encoding="utf-8")
    (run_dir / "report.html").write_text(_html(report), encoding="utf-8")
    output_root.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "report.md", "report.html"):
        shutil.copy2(run_dir / name, output_root / f"latest.{name.split('.')[-1]}")
    return run_dir


