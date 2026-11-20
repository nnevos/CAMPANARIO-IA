"""Default-deny boundary for the existing local API, including WebSockets."""
from urllib.parse import urlsplit
from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient", "testserver"}


def local_request(scope) -> bool:
    peer = (scope.get("client") or ("", 0))[0]
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    try:
        host = urlsplit("http://" + headers.get("host", "")).hostname
        origin = headers.get("origin")
        origin_ok = not origin or (
            urlsplit(origin).scheme in {"http", "https"}
            and urlsplit(origin).netloc.lower() == headers.get("host", "").lower()
        )
    except ValueError:
        return False
    # Do not trust forwarded headers; a local reverse proxy must not expose the admin API.
    forwarded = any(k in headers for k in ("forwarded", "x-forwarded-for", "x-forwarded-host"))
    return peer in LOCAL_HOSTS and host in LOCAL_HOSTS and origin_ok and not forwarded


def require_local(request: Request) -> None:
    if not local_request(request.scope):
        raise HTTPException(403, "Administracao disponivel apenas neste computador")


class LocalOnlyBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"} and not local_request(scope):
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            else:
                await JSONResponse({"detail": "Use a API mobile pareada, nao a API local"}, status_code=403)(scope, receive, send)
            return
        await self.app(scope, receive, send)
