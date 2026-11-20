"""Smoke test for installed voice imports in CAMPANARIO-PYTHON.

No synthesis, model download, user database access or configuration writes.
This is deliberately a file rather than `python -c` (Windows PowerShell 5.1
can strip quotes inside inline Python snippets).
"""
from __future__ import annotations

import sys
import traceback


def main() -> int:
    try:
        from campanario.voice25 import _piper_executable
        from piper.voice import PiperVoice  # noqa: F401 - verifies native Piper dependencies
        from pocket_tts import TTSModel  # noqa: F401 - verifies Pocket TTS imports
        import torch

        print('PIPER API: OK')
        cli = _piper_executable()
        print('PIPER CLI:', cli if cli else 'nao detectado (API Python disponivel)')
        print('POCKET TTS: import OK')
        print('TORCH:', torch.__version__, 'CUDA:', torch.version.cuda,
              'GPU disponivel:', torch.cuda.is_available())
        print('IMPORTS DE VOZ: OK (sem executar sintese ou baixar modelos)')
        return 0
    except Exception:
        print('IMPORTS DE VOZ: FALHA; nao migrar dados nem apagar as .venv antigas.', file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
