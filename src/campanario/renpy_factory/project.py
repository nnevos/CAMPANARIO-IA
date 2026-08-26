from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from .compiler import compile_script, render_gdd_markdown, render_options, render_visual_prompts
from .models import CharacterSpec, RenPyGDD, ScenarioSpec


class FactoryWorkspaceSettings(BaseModel):
    sdk_path: str = r"C:\renply\renpy-8.4.1-sdk"
    workspace_path: str = r"C:\Users\Steam Deck\Desktop\Renpy"
    use_cover_as_web_splash: bool = True
    remove_web_icons: bool = True


class ArtBible(BaseModel):
    character: CharacterSpec
    scenario: ScenarioSpec


class SubjectState(BaseModel):
    subject_id: str
    name: str
    settings: FactoryWorkspaceSettings
    units: list[dict[str, str]] = Field(default_factory=list)
    art_bible: ArtBible | None = None


def safe_name(value: str, fallback: str = "MATERIA") -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = "_".join(part for part in __import__("re").split(r"[^A-Za-z0-9]+", text) if part)
    return (text or fallback)[:100]


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path.name} não é PNG válido")
    return struct.unpack(">II", data[16:24])


class RenPyProjectManager:
    def __init__(self, state_root: Path) -> None:
        self.state_root = state_root / "subjects"
        self.state_root.mkdir(parents=True, exist_ok=True)

    def create_subject(self, name: str, settings: FactoryWorkspaceSettings | None = None) -> SubjectState:
        subject_id = uuid4().hex
        state = SubjectState(subject_id=subject_id, name=name.strip() or "Materia", settings=settings or FactoryWorkspaceSettings())
        self._save(state)
        return state

    def load(self, subject_id: str) -> SubjectState:
        path = self.state_root / subject_id / "subject.json"
        if not path.exists():
            raise FileNotFoundError(subject_id)
        return SubjectState.model_validate_json(path.read_text(encoding="utf-8"))

    def _save(self, state: SubjectState) -> None:
        folder = self.state_root / state.subject_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "subject.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def register_unit(self, subject_id: str, run_dir: Path, gdd: RenPyGDD, source_filename: str) -> dict[str, str]:
        state = self.load(subject_id)
        unit_index = len(state.units) + 1
        unit_code = f"UN{unit_index:02d}"
        if state.art_bible is None:
            state.art_bible = ArtBible(character=gdd.character, scenario=gdd.scenario)
        else:
            # Visual/narrative continuity is inherited from UN01; pedagogical content remains unit-local.
            gdd.character = state.art_bible.character.model_copy(deep=True)
            gdd.scenario = state.art_bible.scenario.model_copy(deep=True)
            self._rewrite_run(run_dir, gdd)

        workspace = Path(state.settings.workspace_path)
        subject_folder = workspace / safe_name(state.name)
        editable = subject_folder / unit_code
        if editable.exists():
            backup = subject_folder / f"{unit_code}_backup_{uuid4().hex[:8]}"
            editable.rename(backup)
        shutil.copytree(run_dir / "project", editable)

        prompts_dir = subject_folder / "PROMPTS_DE_IMAGEM"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        (prompts_dir / f"CAPA_{unit_code}.txt").write_text(_cover_prompt(gdd), encoding="utf-8")
        if unit_index == 1:
            (prompts_dir / "PERSONAGEM.txt").write_text(_character_prompt(gdd), encoding="utf-8")
            (prompts_dir / "CENARIO.txt").write_text(_scenario_prompt(gdd), encoding="utf-8")
            (subject_folder / "ART_BIBLE.json").write_text(state.art_bible.model_dump_json(indent=2), encoding="utf-8")

        unit = {
            "code": unit_code,
            "title": gdd.title,
            "source_filename": source_filename,
            "project_path": str(editable),
            "run_dir": str(run_dir),
        }
        state.units.append(unit)
        self._save(state)
        return unit

    def _rewrite_run(self, run_dir: Path, gdd: RenPyGDD) -> None:
        game = run_dir / "project" / "game"
        (run_dir / "gdd.json").write_text(gdd.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "GDD.md").write_text(render_gdd_markdown(gdd), encoding="utf-8")
        (run_dir / "visual_prompts.txt").write_text(render_visual_prompts(gdd), encoding="utf-8")
        (game / "script.rpy").write_text(compile_script(gdd), encoding="utf-8")
        (game / "options.rpy").write_text(render_options(gdd.title), encoding="utf-8")

    def validate_assets(self, subject_id: str) -> list[str]:
        state = self.load(subject_id)
        errors: list[str] = []
        required = ("fundoiniciar.png", "cenarioinicial.png", "cenarioinstrutor.png", "Final_Iniciante.png", "Final_Proficiente.png", "Final_Mestre.png")
        for unit in state.units:
            game = Path(unit["project_path"]) / "game"
            for name in required:
                path = game / name
                if not path.exists():
                    errors.append(f"{unit['code']}: ausente {name}")
                    continue
                try:
                    if png_size(path) != (1920, 1080):
                        errors.append(f"{unit['code']}: {name} deve ser 1920x1080")
                except ValueError as exc:
                    errors.append(f"{unit['code']}: {exc}")
        return errors

    def build_web(self, subject_id: str) -> dict[str, object]:
        state = self.load(subject_id)
        errors = self.validate_assets(subject_id)
        if errors:
            raise ValueError("Imagens não estão prontas: " + "; ".join(errors[:12]))
        sdk = Path(state.settings.sdk_path)
        python_exe = sdk / "lib" / "py3-windows-x86_64" / "python.exe"
        renpy_py = sdk / "renpy.py"
        if not python_exe.exists() or not renpy_py.exists():
            raise FileNotFoundError(f"SDK Ren'Py não encontrado/configurado em {sdk}")
        subject_folder = Path(state.settings.workspace_path) / safe_name(state.name)
        builds = subject_folder / "WEB_BUILDS"
        builds.mkdir(parents=True, exist_ok=True)
        outputs = []
        for unit in state.units:
            project = Path(unit["project_path"])
            destination = builds / unit["code"]
            destination.mkdir(parents=True, exist_ok=True)
            command = [str(python_exe), str(renpy_py), "launcher", "web_build", str(project), "--destination", str(destination)]
            result = subprocess.run(command, cwd=sdk, capture_output=True, text=True, timeout=900, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Build {unit['code']} falhou: {(result.stderr or result.stdout)[-2000:]}")
            _postprocess_web(destination, project / "game" / "fundoiniciar.png", state.settings)
            zip_path = builds / f"{safe_name(unit['title'], unit['code'])}-1.0-web.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in destination.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(destination))
            outputs.append(str(zip_path))
        return {"subject_id": subject_id, "units": len(state.units), "web_zips": outputs}


def _postprocess_web(destination: Path, cover: Path, settings: FactoryWorkspaceSettings) -> None:
    if settings.remove_web_icons:
        for name in ("icon", "icons"):
            shutil.rmtree(destination / name, ignore_errors=True)
    if settings.use_cover_as_web_splash:
        splash = destination / "web-presplash.jpg"
        if os.name == "nt":
            ps = (
                "Add-Type -AssemblyName System.Drawing; "
                f"$i=[System.Drawing.Image]::FromFile('{str(cover).replace("'", "''")}'); "
                f"$i.Save('{str(splash).replace("'", "''")}',[System.Drawing.Imaging.ImageFormat]::Jpeg); $i.Dispose()"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], check=True, capture_output=True, text=True)


def _cover_prompt(gdd: RenPyGDD) -> str:
    return f'CRIE UMA CAPA DE INICIO DE JOGO COM O NOME “{gdd.title.upper()}” COM DETALHES RELACIONADOS CENTRALIZADO EM 1920x1080 16:9\n'

def _scenario_prompt(gdd: RenPyGDD) -> str:
    return f"crie uma imagem de um Nome: {gdd.scenario.name} Função pedagógica: {gdd.scenario.pedagogical_function} Descrição visual: {gdd.scenario.visual_description} realista, sem efeitos, sem texto no cenario, sem estilização, sem pessoas, em 1920x1080 16:9\n"

def _character_prompt(gdd: RenPyGDD) -> str:
    return f"crie a imagem do personagem ficticio Nome: {gdd.character.name}\n\nPapel: {gdd.character.role}\n\nPersonalidade: {gdd.character.personality}\n\nAparência: {gdd.character.appearance} de braços cruzados olhando para a câmera realista sem filtro sem fundo camera do quadril para cima sem fundo\n"
