"""Desktop host: local API + owned native window. No install, git pull or model download on open."""
import html
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import shutil
import socket
import sys
from threading import Event, Thread
import time
from campanario.app.instance import InstanceLock
from campanario.app.kiwix_autostart import DesktopKiwix
from campanario.app.paths import project_root

SPLASH = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><style>
body{margin:0;background:#0e0f12;color:#c7b894;font:16px system-ui;display:grid;place-items:center;height:100vh;text-align:center}
.circle{border:1px solid #786344;border-radius:50%;width:84px;height:84px;margin:0 auto 24px;animation:breathe 2s ease-in-out infinite}
h1{font:28px Georgia;letter-spacing:.18em}p{color:#a6a8b3;max-width:560px;padding:0 24px}@keyframes breathe{50%{opacity:.25}}@media(prefers-reduced-motion:reduce){.circle{animation:none}}
</style><main><div class="circle"></div><h1>CAMPANARIO</h1><p>Iniciando ambiente local...</p></main></html>"""


def native_error(message):
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Campanario", 0x10)
    elif sys.stderr:
        print(message, file=sys.stderr)


class DesktopServer:
    def __init__(self, port):
        self.port, self.server, self.thread, self.socket = port, None, None, None
        self.error = None

    def start(self):
        import uvicorn
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if os.name == "nt":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind(("127.0.0.1", self.port))
            sock.listen(128)
        except OSError as exc:
            sock.close()
            raise RuntimeError(f"Porta {self.port} indisponivel. Nenhum processo foi encerrado. Altere CAMPANARIO_DESKTOP_PORT no .env.") from exc
        self.socket = sock
        self.server = uvicorn.Server(uvicorn.Config("campanario.main:app", proxy_headers=False, access_log=False, log_config=None, lifespan="on", timeout_graceful_shutdown=8))
        def run():
            try:
                self.server.run(sockets=[sock])
            except BaseException as exc:
                self.error = exc
                logging.getLogger(__name__).exception("Desktop server startup failed")
        self.thread = Thread(target=run, daemon=True, name="campanario-local-api")
        self.thread.start()
        deadline = time.monotonic() + 120
        while not self.server.started:
            if self.error or not self.thread.is_alive():
                raise RuntimeError("Servidor nao iniciou. Consulte desktop.log") from self.error
            if time.monotonic() > deadline:
                self.stop()
                raise RuntimeError("Inicializacao excedeu o limite. Consulte desktop.log")
            time.sleep(.05)
        return f"http://127.0.0.1:{self.port}/"

    def stop(self):
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=10)
        if self.socket:
            self.socket.close()


def main():
    root = project_root()
    os.chdir(root)
    if not (root / ".env").exists() and (root / ".env.example").exists():
        shutil.copyfile(root / ".env.example", root / ".env")
    from campanario.config import get_settings
    settings = get_settings()
    logs = settings.database_path.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(logs / "desktop.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    lock = InstanceLock(settings.database_path.parent / "desktop.lock")
    server = DesktopServer(settings.desktop_port)
    kiwix = DesktopKiwix(settings)
    closing = Event()
    try:
        lock.acquire()
        try:
            import webview
        except ImportError:
            native_error("Ambiente desktop nao preparado. Execute PREPARAR_PC.bat uma vez. Seus dados nao foram alterados.")
            return 1
        window = webview.create_window("Campanario", html=SPLASH, width=1280, height=850, min_size=(800, 600), background_color="#0e0f12", confirm_close=True, text_select=True)
        def boot():
            try:
                try:
                    kiwix.start()
                except Exception:
                    logging.getLogger(__name__).exception('Kiwix opcional indisponivel; iniciando Campanario normalmente')
                if closing.is_set():
                    return
                url = server.start()
                if not closing.is_set():
                    window.load_url(url)
            except Exception as exc:
                logging.getLogger(__name__).exception("Startup error")
                message = html.escape(str(exc))
                window.load_html(SPLASH.replace("Iniciando ambiente local...", message + "<br>Log: " + html.escape(str(logs / "desktop.log"))))
        webview.start(boot, gui="edgechromium" if os.name == "nt" else None, debug=False, private_mode=False, storage_path=str(settings.database_path.parent / "desktop-webview"))
        return 0
    except Exception as exc:
        logging.getLogger(__name__).exception("Desktop failed")
        native_error(f"Nao foi possivel abrir Campanario: {exc}\nLog: {logs / 'desktop.log'}")
        return 1
    finally:
        closing.set()
        from campanario.app.remote import listener
        listener.stop()
        server.stop()
        kiwix.stop()
        lock.release()
        handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
