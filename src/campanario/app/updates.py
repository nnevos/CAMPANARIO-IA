"""Opt-in release discovery. No git pull, downloaded code execution or silent installation."""
import re
import httpx
from urllib.parse import urlsplit

REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Apenas releases estaveis major.minor.patch")
    return tuple(map(int, match.groups()))


async def check_release(repository: str, current: str = "0.8.0") -> dict:
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("Informe dono/repositorio do GitHub")
    async with httpx.AsyncClient(timeout=8, trust_env=False, follow_redirects=False) as client:
        response = await client.get(f"https://api.github.com/repos/{repository}/releases/latest", headers={"Accept": "application/vnd.github+json", "User-Agent": "Campanario/0.8"})
        response.raise_for_status()
        data = response.json()
    version = data.get("tag_name", "")
    newer = version_tuple(version) > version_tuple(current)
    url = data.get("html_url", "")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.startswith(f"/{repository}/releases/"):
        raise ValueError("Link de release inesperado")
    if data.get("draft") or data.get("prerelease"):
        raise ValueError("Release nao estavel")
    return {"current": current, "latest": version, "available": newer, "url": url, "automatic_install": False}
