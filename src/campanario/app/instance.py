"""OS-held lock: stale files do not imply a running process. No PID killing."""
import os
from pathlib import Path


class InstanceLock:
    def __init__(self, path: Path):
        self.path, self.handle = path, None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, "a+b")
        self.handle.seek(0)
        if self.handle.read(1) == b"":
            self.handle.write(b"0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            self.handle = None
            raise RuntimeError("Campanario ja esta aberto neste perfil. Verifique a janela existente.")
        return self

    def release(self):
        if self.handle is None:
            return
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()
        self.handle = None
