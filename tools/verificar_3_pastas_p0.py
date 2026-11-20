"""Optional read-only console diagnostic; normal updates need no PowerShell."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from campanario.brains.environment import inspect_current_environment  # noqa: E402
from campanario.config import Settings  # noqa: E402


def main():
    result = inspect_current_environment(Settings(), project_root=ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'paths_ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
