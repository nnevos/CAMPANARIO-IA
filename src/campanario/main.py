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
    host.start()
    try:
        yield
    finally:
        host.stop()


app = FastAPI(title="Campanario", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.include_router(v1_router)
app.include_router(realtime_router)
app.include_router(device_router)
app.include_router(call_router)
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
    allowed = {"todd.jpg", "morgana.jpg"}
    if filename not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    return FileResponse(_web_assets / filename, headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
