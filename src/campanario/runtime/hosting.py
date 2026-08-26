from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from campanario.runtime.core import CampanarioRuntime, RuntimeNotRunningError, RuntimeState


class RuntimeHost:
    """Process-local lifecycle owner for exactly one active Campanario runtime.

    The host is deliberately transport-agnostic. FastAPI, a future desktop shell or a headless
    process can own this same abstraction without becoming the Campanario runtime itself.
    """

    def __init__(self, runtime_factory: Callable[[], CampanarioRuntime]) -> None:
        self._runtime_factory = runtime_factory
        self._runtime: CampanarioRuntime | None = None
        self._lock = RLock()

    def start(self) -> CampanarioRuntime:
        with self._lock:
            if self._runtime is not None and self._runtime.state.status == "running":
                return self._runtime
            runtime = self._runtime_factory()
            runtime.start()
            self._runtime = runtime
            return runtime

    def stop(self) -> None:
        with self._lock:
            if self._runtime is not None:
                self._runtime.stop()

    @property
    def runtime(self) -> CampanarioRuntime:
        with self._lock:
            if self._runtime is None or self._runtime.state.status != "running":
                raise RuntimeNotRunningError("Campanario runtime host is not running")
            return self._runtime

    @property
    def state(self) -> RuntimeState | None:
        with self._lock:
            return None if self._runtime is None else self._runtime.state

    @property
    def is_running(self) -> bool:
        state = self.state
        return state is not None and state.status == "running"
