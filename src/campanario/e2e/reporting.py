from __future__ import annotations
import html
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from .types import RunReport

def _personality_markdown(summary: dict[str, object]) -> list[str]:
    concept = summary.get("personality_concept")
    if not isinstance(concept, dict):
        return []
    agents = concept.get("agents", {})
    counts = concept.get("counts", {})
    evidence = concept.get("evidence", {})
    lines = [
        "## Análise conceitual de personalidade",
        "",
        "> BATE = a resposta exibiu sinais observáveis do conceito. REVISAR = os sinais foram insuficientes ou houve anti-sinal; leia o transcript antes de alterar a persona.",
        "",
    ]
    for agent in ("todd", "morgana"):
        dimensions = agents.get(agent, {}) if isinstance(agents, dict) else {}
        count = counts.get(agent, {}) if isinstance(counts, dict) else {}
        lines.append(f"### {agent.capitalize()}")
        lines.append("")
        if isinstance(count, dict):
            lines.append(f"Resumo: **{count.get('bate', 0)} BATE / {count.get('misto', 0)} MISTO / {count.get('revisar', 0)} REVISAR / {count.get('sem_dado', 0)} SEM DADO**")
            lines.append("")
        if isinstance(dimensions, dict):
            for dimension, status in sorted(dimensions.items()):
                symbol = "✅" if status == "BATE" else ("◐" if status == "MISTO" else ("⚠️" if status == "REVISAR" else "—"))
                lines.append(f"- {symbol} **{dimension}**: {status}")
        lines.append("")
    return lines


def _personality_html(summary: dict[str, object]) -> str:
    concept = summary.get("personality_concept")
    if not isinstance(concept, dict):
        return ""
    agents = concept.get("agents", {})
    counts = concept.get("counts", {})
    evidence = concept.get("evidence", {})
    blocks = ['<section><h2>Análise conceitual de personalidade</h2><p class="review">BATE = evidência consistente; MISTO = comportamento aparece em parte das variações; REVISAR = evidência fraca. Em Mega, um WARN isolado não reprova mais o eixo.</p>']
    for agent in ("todd", "morgana"):
        dimensions = agents.get(agent, {}) if isinstance(agents, dict) else {}
        count = counts.get(agent, {}) if isinstance(counts, dict) else {}
        if isinstance(count, dict):
            blocks.append(f'<h3>{agent.capitalize()} — {count.get("bate", 0)} BATE / {count.get("misto", 0)} MISTO / {count.get("revisar", 0)} REVISAR / {count.get("sem_dado", 0)} SEM DADO</h3>')
        blocks.append('<ul>')
        if isinstance(dimensions, dict):
            for dimension, status in sorted(dimensions.items()):
                cls = "pass" if status == "BATE" else ("warn" if status in {"MISTO", "REVISAR"} else "")
                agent_evidence = evidence.get(agent, {}) if isinstance(evidence, dict) else {}
                ev = agent_evidence.get(dimension, {}) if isinstance(agent_evidence, dict) else {}
                suffix = ""
                if isinstance(ev, dict) and ev.get("total"):
                    suffix = f' — evidência {ev.get("pass", 0)}/{ev.get("total", 0)} variantes'
                blocks.append(f'<li class="{cls}"><b>{html.escape(str(dimension))}</b>: {html.escape(str(status))}{html.escape(suffix)}</li>')
        blocks.append('</ul>')
    blocks.append('</section>')
    return ''.join(blocks)



def _personality_pair_markdown(summary: dict[str, object]) -> list[str]:
    pair = summary.get("personality_pair")
    if not isinstance(pair, dict):
        return []
    axes = pair.get("axes", {})
    if not isinstance(axes, dict):
        return []
    lines = [
        "## Comparação pareada Todd × Morgana",
        "",
        "> A régua agora é contextual: algumas situações aceitam convergência, outras esperam perspectiva diferente e outras pedem apenas uma assinatura leve. Similaridade lexical é só um sinal de revisão, nunca uma prova de personalidade.",
        "",
    ]
    for dimension, item in sorted(axes.items()):
        if not isinstance(item, dict):
            continue
        policy = str(item.get("policy", ""))
        status = str(item.get("status", ""))
        if policy == "DIVERGENCIA_ESPERADA":
            evidence = f'{item.get("distinct", 0)}/{item.get("total", 0)} pares com distinção clara'
        else:
            avg = item.get("average_similarity")
            evidence = f'similaridade média={avg}' if avg is not None else 'sem medida'
        lines.append(f"- **{dimension}** — `{policy}` → **{status}** ({evidence})")
    lines.append("")
    return lines


def _personality_pair_html(summary: dict[str, object]) -> str:
    pair = summary.get("personality_pair")
    if not isinstance(pair, dict):
        return ""
    axes = pair.get("axes", {})
    if not isinstance(axes, dict):
        return ""
    blocks = [
        '<section><h2>Comparação pareada Todd × Morgana</h2>',
        '<p class="review">A régua é contextual: convergência pode ser correta; divergência só é cobrada em eixos abertos. Similaridade lexical serve apenas como pista de revisão.</p><ul>'
    ]
    for dimension, item in sorted(axes.items()):
        if not isinstance(item, dict):
            continue
        policy = str(item.get("policy", ""))
        status = str(item.get("status", ""))
        cls = "pass" if status in {"BATE", "OK_CONTEXTUAL"} else ("warn" if status in {"MISTO", "REVISAR", "OBSERVAR"} else "")
        if policy == "DIVERGENCIA_ESPERADA":
            detail = f'{item.get("distinct", 0)}/{item.get("total", 0)} pares com distinção clara'
        else:
            detail = f'similaridade média={item.get("average_similarity")}'
        blocks.append(f'<li class="{cls}"><b>{html.escape(str(dimension))}</b> — <code>{html.escape(policy)}</code> → {html.escape(status)} · {html.escape(detail)}</li>')
    blocks.append('</ul></section>')
    return ''.join(blocks)

def _multiagent_markdown(summary: dict[str, object]) -> list[str]:
    data = summary.get("multiagent")
    if not isinstance(data, dict):
        return []
    counts = data.get("speaker_counts", {})
    return [
        "## Resumo multiagente integrado", "",
        f"- Turnos com resposta: **{data.get('turns', 0)}**",
        f"- Turnos em que Todd + Morgana falaram: **{data.get('both_spoke', 0)}**",
        f"- Turnos com um único agente: **{data.get('solo_turns', 0)}**",
        f"- Participações: Morgana **{counts.get('morgana', 0) if isinstance(counts, dict) else 0}** · Todd **{counts.get('todd', 0) if isinstance(counts, dict) else 0}**",
        "",
        "> Este resumo mede forma de participação. Qualidade de complemento, discordância e química entre os três deve ser lida no transcript.", "",
    ]


def _multiagent_html(summary: dict[str, object]) -> str:
    data = summary.get("multiagent")
    if not isinstance(data, dict):
        return ""
    counts = data.get("speaker_counts", {})
    morgana = counts.get("morgana", 0) if isinstance(counts, dict) else 0
    todd = counts.get("todd", 0) if isinstance(counts, dict) else 0
    return (
        '<section><h2>Resumo multiagente integrado</h2>'
        f'<p>Turnos: <b>{data.get("turns", 0)}</b> · ambos falaram: <b>{data.get("both_spoke", 0)}</b> · solo: <b>{data.get("solo_turns", 0)}</b></p>'
        f'<p>Participações: Morgana <b>{morgana}</b> · Todd <b>{todd}</b></p>'
        '<p class="review">A forma de participação é automática; complemento, discordância útil e química exigem leitura do transcript.</p></section>'
    )



def _latency_markdown(summary: dict[str, object]) -> list[str]:
    data = summary.get("latency")
    if not isinstance(data, dict):
        return []
    def fmt(key: str) -> str:
        item = data.get(key, {})
        if not isinstance(item, dict) or not item.get("count"):
            return "sem dados"
        return f"média {item.get('mean')}s · mediana {item.get('median')}s · p95 {item.get('p95')}s · máx {item.get('max')}s"
    speakers = data.get("speaker_generation", {})
    lines = [
        "## Latência conversacional", "",
        f"- Até a primeira resposta utilizável: **{fmt('time_to_first_response')}**",
        f"- Turno total: **{fmt('turn_total')}**",
        f"- Turnos solo: **{fmt('solo_turn_total')}**",
        f"- Turnos multiagente: **{fmt('multiagent_turn_total')}**",
        f"- Gap até a resposta do segundo agente: **{fmt('second_speaker_gap')}**",
    ]
    if isinstance(speakers, dict):
        for agent in ("morgana", "todd"):
            item = speakers.get(agent, {})
            if isinstance(item, dict) and item.get("count"):
                lines.append(f"- Geração {agent.capitalize()}: **média {item.get('mean')}s · p95 {item.get('p95')}s · máx {item.get('max')}s**")
    lines.extend(["", "> TTFR é medido até o primeiro conteúdo utilizável do agente. `speaker_start` não é usado como latência percebida porque ocorre antes da inferência do modelo.", ""] )
    return lines


def _latency_html(summary: dict[str, object]) -> str:
    data = summary.get("latency")
    if not isinstance(data, dict):
        return ""
    def fmt(key: str) -> str:
        item = data.get(key, {})
        if not isinstance(item, dict) or not item.get("count"):
            return "sem dados"
        return f"média {item.get('mean')}s · mediana {item.get('median')}s · p95 {item.get('p95')}s · máx {item.get('max')}s"
    speakers = data.get("speaker_generation", {})
    speaker_lines = []
    if isinstance(speakers, dict):
        for agent in ("morgana", "todd"):
            item = speakers.get(agent, {})
            if isinstance(item, dict) and item.get("count"):
                speaker_lines.append(f'<li><b>Geração {agent.capitalize()}</b>: média {item.get("mean")}s · p95 {item.get("p95")}s · máx {item.get("max")}s</li>')
    return (
        '<section><h2>Latência conversacional</h2><ul>'
        f'<li><b>Primeira resposta utilizável</b>: {html.escape(fmt("time_to_first_response"))}</li>'
        f'<li><b>Turno total</b>: {html.escape(fmt("turn_total"))}</li>'
        f'<li><b>Solo</b>: {html.escape(fmt("solo_turn_total"))}</li>'
        f'<li><b>Multiagente</b>: {html.escape(fmt("multiagent_turn_total"))}</li>'
        f'<li><b>Gap até segundo agente</b>: {html.escape(fmt("second_speaker_gap"))}</li>'
        + ''.join(speaker_lines) +
        '</ul><p class="review">TTFR mede o primeiro conteúdo utilizável; speaker_start ocorre antes da inferência e não representa silêncio percebido.</p></section>'
    )

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
    lines.extend(_personality_markdown(report.summary))
    lines.extend(_personality_pair_markdown(report.summary))
    lines.extend(_multiagent_markdown(report.summary))
    lines.extend(_latency_markdown(report.summary))
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
                speaker = (turn.speaker_id or "Campanario").capitalize()
                lines.append(f"**{speaker}:** {turn.assistant}")
            lines.append("")
            lines.append(f"Tempo total: `{turn.duration_seconds:.3f}s`")
            if turn.time_to_first_response_seconds is not None:
                lines.append(f"TTFR: `{turn.time_to_first_response_seconds:.3f}s`")
            if turn.second_speaker_gap_seconds is not None:
                lines.append(f"Gap segundo agente: `{turn.second_speaker_gap_seconds:.3f}s`")
            for reply in turn.speakers:
                if reply.generation_seconds is not None:
                    lines.append(f"Geração {reply.agent_id.capitalize()}: `{reply.generation_seconds:.3f}s`")
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
            speaker = html.escape((turn.speaker_id or "Campanario").capitalize())
            if turn.error:
                assistant = f'<div class="error">{html.escape(turn.error)}</div>'
            elif turn.speakers:
                speaker_blocks = []
                for reply in turn.speakers:
                    label = html.escape(reply.agent_id.capitalize())
                    reason = html.escape(reply.reason or "")
                    reason_html = f'<span class="meta"> · {reason}</span>' if reason else ''
                    speaker_blocks.append(f'<div class="speaker-label">{label}{reason_html}</div><div class="bubble assistant agent-{html.escape(reply.agent_id)}">{html.escape(reply.text)}</div>')
                assistant = ''.join(speaker_blocks)
            else:
                assistant = f'<div class="speaker-label">{speaker}</div><div class="bubble assistant">{html.escape(turn.assistant)}</div>' 
            turns.append(
                f'<div class="turn"><div class="bubble user">{html.escape(turn.user)}</div>'
                f'{assistant}<div class="meta">total {turn.duration_seconds:.3f}s'
                + (f' · TTFR {turn.time_to_first_response_seconds:.3f}s' if turn.time_to_first_response_seconds is not None else '')
                + (f' · gap 2º agente {turn.second_speaker_gap_seconds:.3f}s' if turn.second_speaker_gap_seconds is not None else '')
                + '</div>'
                f'<ul>{checks}</ul></div>'
            )
        blocks.append(
            f'<section><h2><span class="pill {scenario.status.lower()}">{scenario.status}</span> '
            f'{html.escape(scenario.id)}</h2><p><b>{html.escape(scenario.category)}</b> — '
            f'{html.escape(scenario.description)}</p><p class="review"><b>Revisão humana:</b> '
            f'{html.escape(scenario.review_focus)}</p>{"".join(turns)}</section>'
        )
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campanario Behavioral E2E</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;margin:0 auto;padding:28px;background:#111;color:#eee;line-height:1.45}}h1,h2{{line-height:1.15}}section{{background:#1b1b1b;border:1px solid #333;border-radius:14px;padding:18px;margin:20px 0}}.summary{{background:#181818;padding:16px;border-radius:12px}}.pill{{font-size:.72em;padding:4px 9px;border-radius:999px}}.pass{{color:#8ee39f}}.warn{{color:#ffd36a}}.fail,.error{{color:#ff8b8b}}.pill.pass{{background:#173d21}}.pill.warn{{background:#493b13}}.pill.fail{{background:#4b1c1c}}.bubble{{padding:10px 12px;border-radius:10px;margin:8px 0;white-space:pre-wrap}}.user{{background:#253650}}.assistant{{background:#262626}}.speaker-label{{font-size:.74em;font-weight:700;color:#9aa6b7;text-transform:uppercase;letter-spacing:.08em;margin:10px 0 -3px}}.meta{{font-size:.8em;color:#999}}ul{{margin-top:7px}}.review{{color:#c8c8c8;border-left:3px solid #666;padding-left:10px}}code{{background:#222;padding:2px 5px;border-radius:4px}}</style></head><body>
<h1>Campanario — Behavioral E2E</h1><div class="summary"><p>Modelo: <code>{html.escape(report.model)}</code> · suite: <code>{report.suite}</code> · seed: <code>{report.seed}</code></p><p>Gate automático: <span class="pill {badge}">{s['automatic_gate']}</span> · Cenários: {s['scenario_pass']} PASS / {s['scenario_warn']} WARN / {s['scenario_fail']} FAIL · Checks: {s['check_pass']} PASS / {s['check_warn']} WARN / {s['check_fail']} FAIL</p><p><b>Importante:</b> os checks automáticos medem propriedades observáveis; naturalidade precisa de revisão humana do transcript abaixo.</p></div>{_personality_html(report.summary)}{_personality_pair_html(report.summary)}{_multiagent_html(report.summary)}{_latency_html(report.summary)}{''.join(blocks)}</body></html>'''



def _blind_human_review(report: RunReport) -> str | None:
    if report.suite not in {"agent_human_quick", "agent_human_baseline"}:
        return None
    by_theme: dict[str, dict[str, object]] = {}
    for scenario in report.scenarios:
        if not scenario.id.startswith("human_") or scenario.id.startswith("human_shared_room_"):
            continue
        parts = scenario.id.split("_", 2)
        if len(parts) != 3 or parts[1] not in {"todd", "morgana"}:
            continue
        by_theme.setdefault(parts[2], {})[parts[1]] = scenario
    lines = [
        "# Campanario — Revisão Cega de Conversa Humana",
        "",
        f"Seed: `{report.seed}` · Modelo: `{report.model}`",
        "",
        "> Leia esta folha antes do relatório principal. Em cada par, tente identificar qual conversa é Todd e qual é Morgana sem procurar bordões. Julgue postura, foco, ritmo, curiosidade e forma de acompanhar o usuário.",
        "",
        "## Rubrica humana",
        "",
        "Dê 1–5 para cada conversa em: naturalidade; continuidade; curiosidade proporcional; ausência de palestra; ausência de interrogatório; memória contextual sem prontuário; personalidade consistente; vontade de continuar conversando.",
        "",
    ]
    answer_key: list[str] = []
    for index, (theme, pair) in enumerate(sorted(by_theme.items()), start=1):
        if set(pair) != {"todd", "morgana"}:
            continue
        # Deterministic blind side assignment from seed/theme, reproducible without leaking labels.
        flip = (report.seed + sum(ord(ch) for ch in theme)) % 2 == 1
        agents = ("morgana", "todd") if flip else ("todd", "morgana")
        lines.extend([f"## Par {index} — {theme.replace('_', ' ').title()}", ""])
        for side, agent in zip(("A", "B"), agents):
            scenario = pair[agent]
            lines.extend([f"### Conversa {side}", ""])
            for turn in scenario.turns:
                lines.append(f"**Usuário:** {turn.user}")
                lines.append("")
                lines.append(f"**Resposta:** {turn.assistant or '[sem resposta]'}")
                lines.append("")
            lines.append(f"**Seu palpite para {side}:** __________")
            lines.append(f"**Naturalidade 1–5:** __  **Continuidade 1–5:** __  **Personalidade 1–5:** __  **Quero continuar conversando 1–5:** __")
            lines.append("")
        lines.append("**Qual dos dois parece mais robótico e por quê?** ______________________________________________")
        lines.append("")
        answer_key.append(f"- Par {index}: A = {agents[0].capitalize()} · B = {agents[1].capitalize()}")
    lines.extend(["---", "", "## Gabarito — só consulte depois de avaliar", ""] + answer_key + [""])
    return "\n".join(lines)

def save_report(report: RunReport, output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = output_root / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    payload = asdict(report)
    (run_dir / "report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(_markdown(report), encoding="utf-8")
    (run_dir / "report.html").write_text(_html(report), encoding="utf-8")
    blind = _blind_human_review(report)
    if blind is not None:
        (run_dir / "blind_review.md").write_text(blind, encoding="utf-8")
    output_root.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "report.md", "report.html"):
        shutil.copy2(run_dir / name, output_root / f"latest.{name.split('.')[-1]}")
    if blind is not None:
        shutil.copy2(run_dir / "blind_review.md", output_root / "latest.blind.md")
    return run_dir


