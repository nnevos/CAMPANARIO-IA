import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from campanario.api import router, v1_router
from campanario.gateway.realtime import router as realtime_router
from campanario.gateway.devices import router as device_router
from campanario.gateway.call import router as call_router
from campanario.bootstrap import get_runtime_host
from campanario.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    host = get_runtime_host()
    try:
        from campanario.app.schema import prepare_schema
        prepare_schema(settings)
        host.start()
    except Exception:
        logging.getLogger(__name__).exception("Runtime indisponivel; interface de diagnostico permanece acessivel")
    try:
        yield
    finally:
        from campanario.app.remote import listener
        listener.stop()
        host.stop()


app = FastAPI(title="Campanario", version="0.8.0", lifespan=lifespan)
from campanario.utilities.api import router as utilities_router
app.include_router(utilities_router)
from campanario.brains.api import router as brains_router
app.include_router(brains_router)
from campanario.brains.casework_api import router as casework_router
app.include_router(casework_router)
app.include_router(router)
app.include_router(v1_router)
app.include_router(realtime_router)
app.include_router(device_router)
app.include_router(call_router)
from campanario.voice25 import router as voice25_router
app.include_router(voice25_router)
from campanario.app.api import router as app_router
from campanario.app.security import LocalOnlyBoundary
app.include_router(app_router)
app.add_middleware(LocalOnlyBoundary)
_web_index = Path(__file__).with_name("web") / "index.html"
_web_assets = Path(__file__).with_name("web") / "assets"


def _web_index_response() -> FileResponse:
    return FileResponse(
        _web_index,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/", include_in_schema=False)
def web_ui() -> FileResponse:
    return _web_index_response()


@app.get("/ui-assets/{filename}", include_in_schema=False)
def web_asset(filename: str) -> FileResponse:
    allowed = {f"{agent}_{state}.svg" for agent in ("morgana", "todd", "campanario") for state in ("idle", "thinking", "speaking")}
    if filename not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    return FileResponse(_web_assets / filename, headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/ferramentas")
def utilities_page():
    # R2.6: isolate the sensitive utilities UI from inline script execution and framing.
    # Styles remain inline-compatible because the existing Dark Matter UI uses style attrs.
    headers = {
        "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; img-src 'self' data:; font-src 'self' data:; "
            "base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'"
        ),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    }
    return FileResponse(Path(__file__).with_name("web") / "ferramentas.html", headers=headers)

@app.get("/ferramentas.css", include_in_schema=False)
def utilities_css():
    return FileResponse(Path(__file__).with_name("web") / "ferramentas.css", media_type="text/css")

@app.get("/ferramentas.js", include_in_schema=False)
def utilities_js():
    return FileResponse(Path(__file__).with_name("web") / "ferramentas.js", media_type="application/javascript")


@app.get("/health/live")
def live():
    from campanario.bootstrap import get_runtime_host
    return {"app": "campanario", "version": "0.8.0", "runtime_running": get_runtime_host().is_running}

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=Path(__file__).with_name("web") / "static"), name="frontend-static")
