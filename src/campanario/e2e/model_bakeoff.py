from __future__ import annotations
import argparse, json, os, subprocess, sys
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(slots=True)
class ModelResult:
    model: str
    exit_code: int
    automatic_gate: str
    scenario_pass: int = 0
    scenario_warn: int = 0
    scenario_fail: int = 0
    check_pass: int = 0
    check_warn: int = 0
    check_fail: int = 0
    total_seconds: float = 0.0
    avg_turn_seconds: float = 0.0


def _slug(value: str) -> str:
    return ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in value)


def run_model(model: str, seed: int, suite: str, root: Path) -> ModelResult:
    out = root / _slug(model)
    env = os.environ.copy()
    env['CAMPANARIO_MODEL_NAME'] = model
    cmd = [sys.executable, '-m', 'campanario.e2e.behavioral', '--suite', suite, '--seed', str(seed), '--output', str(out), '--no-open']
    proc = subprocess.run(cmd, env=env, check=False)
    latest = out / 'latest.json'
    if not latest.exists():
        return ModelResult(model, proc.returncode, 'ERROR')
    payload = json.loads(latest.read_text(encoding='utf-8'))
    s = payload['summary']
    durations = [float(turn.get('duration_seconds', 0.0)) for scenario in payload.get('scenarios', []) for turn in scenario.get('turns', [])]
    total = round(sum(durations), 3)
    avg = round(total / len(durations), 3) if durations else 0.0
    return ModelResult(model, proc.returncode, str(s['automatic_gate']), int(s['scenario_pass']), int(s['scenario_warn']), int(s['scenario_fail']), int(s['check_pass']), int(s['check_warn']), int(s['check_fail']), total, avg)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Compare multiple configured local models against the same Campanario E2E seed.')
    ap.add_argument('models', nargs='+')
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--suite', choices=('standard','full'), default='standard')
    ap.add_argument('--output', type=Path, default=Path('test_reports')/'model_bakeoff')
    args=ap.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    results=[run_model(m,args.seed,args.suite,args.output) for m in args.models]
    data=[asdict(r) for r in results]
    (args.output/'comparison.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Campanario — Model Bakeoff','',f'Seed: `{args.seed}` · suite: `{args.suite}`','', '| Modelo | Gate | Cenários P/W/F | Checks P/W/F | Tempo total | Média/turno |','|---|---:|---:|---:|---:|---:|']
    for r in results:
        lines.append(f'| `{r.model}` | {r.automatic_gate} | {r.scenario_pass}/{r.scenario_warn}/{r.scenario_fail} | {r.check_pass}/{r.check_warn}/{r.check_fail} | {r.total_seconds:.1f}s | {r.avg_turn_seconds:.2f}s |')
    (args.output/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))
    return 0 if all(r.automatic_gate != 'ERROR' for r in results) else 2

if __name__ == '__main__':
    raise SystemExit(main())
