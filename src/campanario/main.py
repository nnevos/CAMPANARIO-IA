import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from campanario.api import router
from campanario.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Campanario", version="0.1.0")
app.include_router(router)
_web_index = Path(__file__).with_name("web") / "index.html"


@app.get("/", include_in_schema=False)
def web_ui() -> FileResponse:
    return FileResponse(_web_index)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
