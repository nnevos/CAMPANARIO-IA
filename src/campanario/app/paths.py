from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", project_root()))
