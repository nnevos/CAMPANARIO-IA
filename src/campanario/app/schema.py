"""Schema upgrade only when revisions differ, preceded by a consistent SQLite backup."""
from datetime import datetime, UTC
from pathlib import Path
import sqlite3
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from campanario.app.paths import resource_root


def backup_sqlite(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
    try:
        destination.chmod(0o600)
    except OSError:
        pass


def prepare_schema(settings, root: Path | None = None) -> dict:
    root = root or resource_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.attributes["campanario_settings"] = settings
    config.attributes["configure_logging"] = False
    head = ScriptDirectory.from_config(config).get_current_head()
    database = settings.database_path
    database.parent.mkdir(parents=True, exist_ok=True)
    current = None
    if database.exists():
        with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as connection:
            has_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()
            if has_table:
                row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
                current = row[0] if row else None
    if current == head:
        return {"changed": False, "revision": head, "backup": None}
    backup = None
    if database.exists() and database.stat().st_size:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup = database.parent / "backups" / f"campanario-before-{head}-{stamp}.db"
        backup_sqlite(database, backup)
    # Never stamp an unknown database or erase data to make migration pass.
    command.upgrade(config, "head")
    return {"changed": True, "revision": head, "backup": str(backup) if backup else None}
