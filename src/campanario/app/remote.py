"""Explicit TLS-only companion listener. Never exposes the local/admin routes."""
from pathlib import Path
from threading import RLock, Thread
import socket
import ssl
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from campanario.companion.api import router


class BodyLimit:
    def __init__(self, app, limit=2_000_000):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        data = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            data.extend(event.get("body", b""))
            if len(data) > self.limit:
                await JSONResponse({"detail": "Requisicao excede 2 MB"}, status_code=413)(scope, receive, send)
                return
            if not event.get("more_body", False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()
        await self.app(scope, replay, send)


def create_companion_app():
    app = FastAPI(title="Campanario Companion", docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(router)
    app.add_middleware(BodyLimit)
    app.add_middleware(CORSMiddleware, allow_origins=["https://appassets.androidplatform.net"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
    return app


class RemoteListener:
    def __init__(self):
        self._lock = RLock()
        self.server = self.thread = self.socket = None
        self.endpoint = None

    def status(self):
        return {"running": bool(self.thread and self.thread.is_alive() and self.server and self.server.started), "listen": self.endpoint, "tls_required": True}

    def start(self, host: str, port: int, cert: Path, key: Path):
        with self._lock:
            if self.thread and self.thread.is_alive():
                raise ValueError("Servidor mobile ja esta em execucao")
            # Validate credentials before binding; never disable certificate validation on clients.
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(str(cert), str(key))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((host, port))
                sock.listen(128)
                config = uvicorn.Config(create_companion_app(), host=host, port=port, ssl_certfile=str(cert), ssl_keyfile=str(key), proxy_headers=False, lifespan="off", access_log=False, log_config=None, timeout_graceful_shutdown=3)
                server = uvicorn.Server(config)
                thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True, name="campanario-companion")
                self.server, self.thread, self.socket = server, thread, sock
                self.endpoint = f"{host}:{port}"
                thread.start()
            except Exception:
                sock.close()
                raise
        return {"starting": True, "listen": self.endpoint}

    def stop(self):
        with self._lock:
            if self.server:
                self.server.should_exit = True
            if self.thread:
                self.thread.join(timeout=5)
                if self.thread.is_alive():
                    return {"stopping": True}
            if self.socket:
                self.socket.close()
            self.server = self.thread = self.socket = None
            self.endpoint = None
        return {"running": False}


listener = RemoteListener()
