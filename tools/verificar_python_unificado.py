"""Verify a separately installed CAMPANARIO-PYTHON environment (no data changes).

Marking is explicit, after the PowerShell bootstrap has run `uv pip check`.
No voice model is downloaded, no user databases are opened.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_environment(root: Path, prefix: Path) -> tuple[dict, list[str]]:
    root, prefix = root.resolve(), prefix.resolve()
    profile = root / "config" / "ambiente_unificado.json"
    data = json.loads(profile.read_text(encoding="utf-8"))
    errors: list[str] = []
    if sys.version_info[:3] != (3, 12, 10):
        errors.append("Python deve ser 3.12.10, como nos dois inventarios")
    if Path(sys.prefix).resolve() != prefix:
        errors.append("Python executado nao pertence ao ambiente externo escolhido")
    if prefix != (root.parent / "CAMPANARIO-PYTHON" / ".venv").resolve():
        errors.append("Destino diferente de ../CAMPANARIO-PYTHON/.venv")
    for name, version in data["packages_to_verify"].items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        if installed != version:
            errors.append(f"{name}: esperado {version}; instalado {installed}")
    for name in ("fastapi", "pywebview", "pytest", "pydantic", "sqlalchemy"):
        try:
            metadata.version(name)
        except metadata.PackageNotFoundError:
            errors.append(f"Pacote do nucleo nao instalado: {name}")
    try:
        import campanario
        source = Path(campanario.__file__).resolve()
        if not source.is_relative_to((root / "src" / "campanario").resolve()):
            errors.append("campanario importado fora do codigo local atual")
    except Exception as exc:
        errors.append(f"Nao foi possivel importar o Campanario atual: {type(exc).__name__}")
    import importlib.util
    for mod in ("piper", "pocket_tts", "torch"):
        try:
            if importlib.util.find_spec(mod) is None:
                errors.append(f"Modulo opcional de voz ausente: {mod}")
        except (ImportError, ValueError):
            errors.append(f"Modulo opcional de voz ausente: {mod}")
    result = {
        "schema_version": 1,
        "project_root": str(root),
        "environment": str(prefix),
        "python_version": sys.version.split()[0],
        "verified_packages": dict(data["packages_to_verify"]),
        "profile_sha256": sha256(profile),
        "pyproject_sha256": sha256(root / "pyproject.toml"),
        "uv_lock_sha256": sha256(root / "uv.lock"),
        "result": "OK" if not errors else "FAIL",
    }
    return result, errors


def check_marker(root: Path, prefix: Path) -> tuple[dict, list[str]]:
    result, errors = check_environment(root, prefix)
    marker = (root.parent / "CAMPANARIO-PYTHON" / "AMBIENTE_VALIDADO.json").resolve()
    try:
        previous = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        errors.append("Marcador AMBIENTE_VALIDADO.json nao encontrado ou invalido")
        return result, errors
    for key in ("project_root", "environment", "profile_sha256", "pyproject_sha256", "uv_lock_sha256"):
        if previous.get(key) != result.get(key):
            errors.append(f"Marcador desatualizado: {key}")
    if previous.get("result") != "OK":
        errors.append("Marcador nao validado")
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--mark", action="store_true", help="write marker after uv pip check")
    parser.add_argument("--require-marker", action="store_true")
    args = parser.parse_args()
    root, prefix = args.project.resolve(), args.environment.resolve()
    result, errors = (check_marker(root, prefix) if args.require_marker else check_environment(root, prefix))
    for error in errors:
        print("ERRO:", error)
    print("Python externo:", result["environment"], "status:", "OK" if not errors else "FALHA")
    if errors:
        return 1
    if args.mark:
        marker = root.parent / "CAMPANARIO-PYTHON" / "AMBIENTE_VALIDADO.json"
        marker.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Marcador atualizado:", marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
