"""Own a local Kiwix child process for the desktop window lifetime only.

No network download, external command shell, archive editing or memory writes.
A pre-existing listener is never terminated (it may be a manually run Kiwix).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import socket
import subprocess
from threading import Event, Lock
import time
from urllib.parse import urlsplit

from campanario.config import Settings

logger = logging.getLogger(__name__)


def _is_windows() -> bool:
    return os.name == 'nt'


def _listen_port(base_url: str) -> int | None:
    """Accept ONLY explicit HTTP loopback endpoints, never LAN or remote ports."""
    try:
        parsed = urlsplit(base_url)
        if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost')
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            return None
        port = parsed.port
        return port if port and 1 <= port <= 65535 else None
    except (ValueError, TypeError):
        return None


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.2):
            return True
    except OSError:
        return False


class DesktopKiwix:
    """Start when the desktop opens; stop exclusively the subprocess we own."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.status = 'not_started'
        self._owned: subprocess.Popen | None = None
        self._closed = Event()
        self._lock = Lock()

    def _resources(self) -> tuple[Path, Path] | None:
        zim_dir = Path(self.settings.zim_dir or (self.settings.data_dir.parent / 'zim'))
        if not zim_dir.is_dir():
            self.status = 'zim_directory_missing'
            return None
        # Must match OfflineWikipediaZim._book() exactly.
        archives = sorted((p for p in zim_dir.glob('wikipedia_pt*.zim') if p.is_file()),
                          reverse=True)
        if not archives:
            self.status = 'zim_file_missing'
            return None
        archive = archives[0]
        tools_dir = zim_dir.parent / 'kiwix'
        if not tools_dir.is_dir():
            self.status = 'kiwix_tools_missing'
            return None
        # Prefer the documented location but permit ZIPs with an extra folder.
        direct = tools_dir / 'kiwix-serve.exe'
        executables = [direct] if direct.is_file() else sorted(
            p for p in tools_dir.rglob('kiwix-serve.exe') if p.is_file()
        )
        if not executables:
            self.status = 'kiwix_executable_missing'
            return None
        return executables[0], archive

    def start(self) -> str:
        if not self.settings.zim_enabled or not self.settings.zim_auto_start:
            self.status = 'disabled'
            return self.status
        if not _is_windows():
            self.status = 'windows_only'
            return self.status
        port = _listen_port(self.settings.zim_base_url)
        if port is None:
            self.status = 'invalid_loopback_url'
            logger.warning('Kiwix: endereco invalido; apenas HTTP local permitido')
            return self.status
        resources = self._resources()
        if resources is None:
            logger.info('Kiwix nao iniciado: %s', self.status)
            return self.status
        executable, archive = resources
        with self._lock:
            if self._closed.is_set():
                self.status = 'stopped'
                return self.status
            if self._owned is not None:
                self.status = 'already_started_by_campanario'
                return self.status
            if _listening(port):
                # Crucial: do not claim ownership of somebody else's server.
                self.status = 'external_listener'
                logger.info('Kiwix: porta %s ja ocupada; processo externo preservado', port)
                return self.status
            try:
                self._owned = subprocess.Popen(
                    [str(executable), '--address=127.0.0.1', f'--port={port}',
                     '--blockexternal', str(archive)],
                    cwd=str(executable.parent),
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, shell=False,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except (OSError, ValueError) as exc:
                self.status = 'start_failed'
                logger.warning('Kiwix: falha ao iniciar %s', type(exc).__name__)
                return self.status
        # Do not hold the lock while waiting: closing the desktop must be able
        # to terminate the child even when the ZIM takes time to open.
        deadline = time.monotonic() + 10
        while not self._closed.is_set() and time.monotonic() < deadline:
            if self._owned is None or self._owned.poll() is not None:
                self.status = 'exited_early'
                logger.warning('Kiwix encerrou antes de abrir a porta %s', port)
                return self.status
            if _listening(port):
                self.status = 'running'
                logger.info('Kiwix iniciado automaticamente em 127.0.0.1:%s; ZIM=%s',
                            port, archive.name)
                return self.status
            self._closed.wait(0.15)
        if self._closed.is_set():
            self.status = 'stopped'
        elif self._owned is not None and self._owned.poll() is None:
            # Kiwix may finish loading a large ZIM later: keep this owned child.
            self.status = 'starting_slowly'
            logger.info('Kiwix ainda inicializando, mantendo processo em segundo plano')
        else:
            self.status = 'exited_early'
        return self.status

    def stop(self) -> None:
        self._closed.set()
        with self._lock:
            proc, self._owned = self._owned, None
        if proc is None or proc.poll() is not None:
            self.status = 'stopped'
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning('Kiwix: falha ao encerrar processo proprio %s', type(exc).__name__)
        self.status = 'stopped'
