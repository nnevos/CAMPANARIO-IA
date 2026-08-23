import logging

from fastapi import FastAPI

from campanario.api import router
from campanario.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Campanario", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
