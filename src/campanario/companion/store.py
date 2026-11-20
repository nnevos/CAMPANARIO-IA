"""Companion data is separate from the conversation DB. All writes are transactional.

Mobile has device-scoped notes and an explicitly published offline package, never raw DB access.
Credentials are hashed; pair codes are single-use and expire. Tombstones avoid resurrected notes.
"""
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3
import time
from uuid import uuid4


class Conflict(ValueError):
    pass


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CompanionStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL,
                chat INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, revoked REAL
            );
            CREATE TABLE IF NOT EXISTS pair_codes (
                code_hash TEXT PRIMARY KEY, name TEXT NOT NULL, chat INTEGER NOT NULL,
                expires REAL NOT NULL, consumed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS snapshots (
                device_id TEXT PRIMARY KEY REFERENCES devices(id), revision INTEGER NOT NULL,
                content TEXT NOT NULL, updated REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notes (
                device_id TEXT NOT NULL REFERENCES devices(id), id TEXT NOT NULL,
                title TEXT NOT NULL, body TEXT NOT NULL, revision INTEGER NOT NULL,
                deleted INTEGER NOT NULL, updated REAL NOT NULL,
                PRIMARY KEY(device_id,id)
            );
            CREATE TABLE IF NOT EXISTS operations (
                device_id TEXT NOT NULL, id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                result TEXT NOT NULL, PRIMARY KEY(device_id,id)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                device_id TEXT NOT NULL REFERENCES devices(id), client_id TEXT NOT NULL,
                session_id TEXT NOT NULL, PRIMARY KEY(device_id,client_id), UNIQUE(device_id,session_id)
            );
            CREATE TABLE IF NOT EXISTS gps_tracks (
                device_id TEXT NOT NULL REFERENCES devices(id), id TEXT NOT NULL,
                name TEXT NOT NULL, content TEXT NOT NULL, created REAL NOT NULL,
                PRIMARY KEY(device_id,id)
            );
            CREATE TABLE IF NOT EXISTS turns (
                device_id TEXT NOT NULL, id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                state TEXT NOT NULL, result TEXT, created REAL NOT NULL,
                PRIMARY KEY(device_id,id)
            );
            """)
        try:
            path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def save_gps_track(self, device_id: str, track_id: str, name: str, points: list[dict]) -> dict:
        # No telemetry by default; this method is invoked only by explicit upload.
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute("SELECT content FROM gps_tracks WHERE device_id=? AND id=?", (device_id, track_id)).fetchone()
            payload = canonical(points)
            if existing:
                if existing["content"] != payload:
                    raise Conflict("Identificador de trilha ja utilizado com conteudo diferente")
                return {"id": track_id, "stored": True, "duplicate": True}
            if con.execute("SELECT COUNT(*) FROM gps_tracks WHERE device_id=?", (device_id,)).fetchone()[0] >= 100:
                raise ValueError("Limite de 100 trilhas por dispositivo")
            con.execute("INSERT INTO gps_tracks VALUES(?,?,?,?,?)", (device_id, track_id, name, payload, time.time()))
        return {"id": track_id, "stored": True, "duplicate": False}

    def list_gps_tracks(self, device_id: str | None = None) -> list[dict]:
        with self.connect() as con:
            if device_id:
                rows = con.execute("SELECT device_id,id,name,content,created FROM gps_tracks WHERE device_id=? ORDER BY created DESC", (device_id,)).fetchall()
            else:
                rows = con.execute("SELECT device_id,id,name,content,created FROM gps_tracks ORDER BY created DESC LIMIT 1000").fetchall()
        return [{"device_id": r["device_id"], "id": r["id"], "name": r["name"], "points": json.loads(r["content"]), "created": r["created"]} for r in rows]

    def delete_gps_track(self, device_id: str, track_id: str) -> bool:
        with self.connect() as con:
            return con.execute("DELETE FROM gps_tracks WHERE device_id=? AND id=?", (device_id, track_id)).rowcount > 0

    def create_pair_code(self, name: str, chat: bool = False) -> dict:
        code = secrets.token_urlsafe(24)
        expires = time.time() + 300
        with self.connect() as con:
            con.execute("DELETE FROM pair_codes WHERE expires < ? OR consumed = 1", (time.time(),))
            con.execute("INSERT INTO pair_codes VALUES(?,?,?,?,0)", (digest(code), name, int(chat), expires))
        return {"code": code, "expires_at": expires, "expires_in": 300, "chat_allowed": chat}

    def redeem(self, code: str) -> dict:
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM pair_codes WHERE code_hash=?", (digest(code),)).fetchone()
            if row is None or row["consumed"] or row["expires"] <= time.time():
                raise PermissionError("Codigo invalido, expirado ou ja usado")
            device_id, token = str(uuid4()), secrets.token_urlsafe(32)
            con.execute("UPDATE pair_codes SET consumed=1 WHERE code_hash=?", (digest(code),))
            con.execute("INSERT INTO devices VALUES(?,?,?,?,?,NULL)", (device_id, row["name"], digest(token), row["chat"], time.time()))
        return {"device_id": device_id, "token": token, "name": row["name"], "chat_allowed": bool(row["chat"])}

    def authenticate(self, token: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT id,name,chat,revoked FROM devices WHERE token_hash=?", (digest(token),)).fetchone()
        if not row or row["revoked"] is not None:
            raise PermissionError("Dispositivo nao autorizado")
        return {"id": row["id"], "name": row["name"], "chat": bool(row["chat"])}

    def _active(self, con, device_id):
        row = con.execute("SELECT id FROM devices WHERE id=? AND revoked IS NULL", (device_id,)).fetchone()
        if not row:
            raise PermissionError("Dispositivo revogado ou inexistente")

    def list_devices(self) -> list:
        with self.connect() as con:
            return [dict(row) for row in con.execute("SELECT id,name,chat,created,revoked FROM devices ORDER BY created DESC")]

    def revoke(self, device_id: str) -> None:
        with self.connect() as con:
            cur = con.execute("UPDATE devices SET revoked=? WHERE id=?", (time.time(), device_id))
            if cur.rowcount != 1:
                raise KeyError(device_id)

    def publish(self, device_id: str, items: list[dict]) -> dict:
        content = canonical(items)
        if len(content.encode()) > 2_000_000:
            raise ValueError("Pacote offline excede 2 MB")
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            self._active(con, device_id)
            old = con.execute("SELECT revision FROM snapshots WHERE device_id=?", (device_id,)).fetchone()
            revision = old[0] + 1 if old else 1
            updated = time.time()
            con.execute("INSERT INTO snapshots VALUES(?,?,?,?) ON CONFLICT(device_id) DO UPDATE SET revision=excluded.revision,content=excluded.content,updated=excluded.updated", (device_id, revision, content, updated))
        return {"revision": revision, "items": len(items), "updated": updated}

    def snapshot(self, device_id: str) -> dict:
        with self.connect() as con:
            self._active(con, device_id)
            row = con.execute("SELECT * FROM snapshots WHERE device_id=?", (device_id,)).fetchone()
        if row is None:
            return {"revision": 0, "items": [], "updated": None}
        return {"revision": row["revision"], "items": json.loads(row["content"]), "updated": row["updated"]}

    def sync_notes(self, device_id: str, mutations: list[dict]) -> dict:
        results = []
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            self._active(con, device_id)
            for mutation in mutations:
                op_id = mutation["mutation_id"]
                fingerprint = digest(canonical(mutation))
                seen = con.execute("SELECT fingerprint,result FROM operations WHERE device_id=? AND id=?", (device_id, op_id)).fetchone()
                if seen:
                    if seen["fingerprint"] != fingerprint:
                        raise Conflict("Identificador de operacao reutilizado com outro conteudo")
                    results.append(json.loads(seen["result"]))
                    continue
                old = con.execute("SELECT * FROM notes WHERE device_id=? AND id=?", (device_id, mutation["id"])).fetchone()
                actual_revision = old["revision"] if old else 0
                if mutation["base_revision"] != actual_revision:
                    result = {"mutation_id": op_id, "id": mutation["id"], "status": "conflict", "remote": dict(old) if old else None}
                else:
                    revision = actual_revision + 1
                    con.execute("INSERT INTO notes VALUES(?,?,?,?,?,?,?) ON CONFLICT(device_id,id) DO UPDATE SET title=excluded.title,body=excluded.body,revision=excluded.revision,deleted=excluded.deleted,updated=excluded.updated", (device_id, mutation["id"], mutation["title"], mutation["body"], revision, int(mutation["deleted"]), time.time()))
                    result = {"mutation_id": op_id, "id": mutation["id"], "status": "accepted", "revision": revision}
                con.execute("INSERT INTO operations VALUES(?,?,?,?)", (device_id, op_id, fingerprint, canonical(result)))
                results.append(result)
            # Capacity applies to the final transaction, including tombstones; no silent pruning.
            total, size = con.execute("SELECT COUNT(*),COALESCE(SUM(length(CAST(title AS BLOB))+length(CAST(body AS BLOB))),0) FROM notes WHERE device_id=?", (device_id,)).fetchone()
            if total > 2000 or size > 5_000_000:
                raise ValueError("Limite de notas por dispositivo atingido")
            notes = [dict(row) for row in con.execute("SELECT id,title,body,revision,deleted,updated FROM notes WHERE device_id=? ORDER BY updated", (device_id,))]
        return {"results": results, "notes": notes}

    def session(self, device_id: str, client_id: str, create) -> str:
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            self._active(con, device_id)
            row = con.execute("SELECT session_id FROM sessions WHERE device_id=? AND client_id=?", (device_id, client_id)).fetchone()
            if row:
                return row[0]
            session_id = str(create())
            con.execute("INSERT INTO sessions VALUES(?,?,?)", (device_id, client_id, session_id))
            return session_id

    def owns_session(self, device_id: str, session_id: str) -> bool:
        with self.connect() as con:
            return bool(con.execute("SELECT 1 FROM sessions WHERE device_id=? AND session_id=?", (device_id, session_id)).fetchone())

    def begin_turn(self, device_id: str, request_id: str, payload: dict) -> dict:
        fingerprint = digest(canonical(payload))
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            self._active(con, device_id)
            row = con.execute("SELECT * FROM turns WHERE device_id=? AND id=?", (device_id, request_id)).fetchone()
            if row:
                if row["fingerprint"] != fingerprint:
                    raise Conflict("ID de mensagem reutilizado")
                return {"state": row["state"], "result": json.loads(row["result"]) if row["result"] else None}
            con.execute("INSERT INTO turns VALUES(?,?,?,'pending',NULL,?)", (device_id, request_id, fingerprint, time.time()))
        return {"state": "new", "result": None}

    def finish_turn(self, device_id: str, request_id: str, state: str, result: dict):
        with self.connect() as con:
            con.execute("UPDATE turns SET state=?,result=? WHERE device_id=? AND id=?", (state, canonical(result), device_id, request_id))


@lru_cache
def get_store() -> CompanionStore:
    from campanario.config import get_settings
    return CompanionStore(get_settings().database_path.parent / "companion.db")
