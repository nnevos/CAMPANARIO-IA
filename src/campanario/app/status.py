"""Liveness is not model readiness. Never contact an external Internet service here."""
import asyncio
import sqlite3
import httpx
from campanario.config import get_settings
from campanario.bootstrap import get_runtime_host


async def system_status() -> dict:
    settings = get_settings()
    host = get_runtime_host()
    parts = {
        "runtime": {"state": "ready" if host.is_running else "unavailable"},
        "database": {"state": "unavailable"},
        "model": {"state": "unconfigured", "name": settings.effective_model_name},
        "semantic": {"state": "configured" if settings.semantic_memory_enabled else "disabled", "backend": settings.semantic_memory_backend, "checked": False},
        "tts": {"state": "not_installed"},
        "stt": {"state": "not_installed"},
        "gps": {"state": "not_installed"},
    }
    def check_db():
        if not settings.database_path.exists():
            return False
        with sqlite3.connect(f"{settings.database_path.resolve().as_uri()}?mode=ro", uri=True, timeout=1) as con:
            return con.execute("SELECT 1 FROM alembic_version LIMIT 1").fetchone() is not None
    try:
        parts["database"]["state"] = "ready" if await asyncio.to_thread(check_db) else "unavailable"
    except sqlite3.Error:
        pass
    if settings.model_provider.value == "fake":
        parts["model"]["state"] = "test_provider"
    elif settings.effective_model_name:
        try:
            async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
                resp = await client.get(settings.model_runtime.base_url.rstrip("/") + "/api/tags")
                resp.raise_for_status()
                installed = {v.get("name", "") for v in resp.json().get("models", [])}
                configured = settings.effective_model_name
                parts["model"]["state"] = "ready" if configured in installed or configured + ":latest" in installed else "missing_model"
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            parts["model"]["state"] = "unavailable"
    can_chat = parts["runtime"]["state"] == "ready" and parts["database"]["state"] == "ready" and parts["model"]["state"] in {"ready", "test_provider"}
    return {"version": "0.8.0", "status": "ready" if can_chat else "degraded", "can_chat": can_chat, "components": parts}
