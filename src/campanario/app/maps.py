"""Read-only local MBTiles raster maps. No automatic downloads or tracking."""
import os
import sqlite3
from pathlib import Path


def package_path():
    # Only a local operator controls this path; never accept arbitrary file paths via HTTP.
    configured = os.environ.get("CAMPANARIO_MBTILES", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / "Campanario" / "maps" / "offline.mbtiles"


def map_status():
    path = package_path()
    if not path.is_file():
        return {"offline_available": False, "format": "MBTiles raster PNG", "message": "Instale um arquivo offline.mbtiles na pasta Campanario/maps ou configure CAMPANARIO_MBTILES"}
    try:
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=2) as db:
            meta = dict(db.execute("SELECT name, value FROM metadata WHERE name IN ('format','name','minzoom','maxzoom')"))
        return {"offline_available": meta.get("format") == "png", "format": meta.get("format", "unknown"), "name": meta.get("name", "Mapa local"), "minzoom": meta.get("minzoom"), "maxzoom": meta.get("maxzoom")}
    except (sqlite3.Error, OSError) as exc:
        return {"offline_available": False, "message": f"Pacote inválido: {type(exc).__name__}"}


def read_tile(z: int, x: int, y: int):
    if not 0 <= z <= 19 or not 0 <= x < (1 << z) or not 0 <= y < (1 << z):
        return None
    path = package_path()
    if not path.is_file():
        return None
    try:
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=2) as db:
            fmt = db.execute("SELECT value FROM metadata WHERE name='format'").fetchone()
            if not fmt or fmt[0] != 'png':
                return None  # Endpoint only serves PNG; other formats require a dedicated media route.
            result = db.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, (1 << z) - 1 - y)).fetchone()
        data = result[0] if result else None
        return data if data and len(data) <= 2_000_000 and data[:8] == b'\x89PNG\r\n\x1a\n' else None
    except (sqlite3.Error, OSError):
        return None
