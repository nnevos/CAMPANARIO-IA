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
    # The UI is a single local file and changes between development releases.
    # Force revalidation so an old browser cache cannot make a new backend look unchanged.
    return FileResponse(
        _web_index,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
