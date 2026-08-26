from __future__ import annotations

import logging
import signal
from threading import Event

from campanario.bootstrap import get_runtime_host

logger = logging.getLogger(__name__)


def run_until_stopped(stop_event: Event | None = None) -> None:
    """Run Campanario headlessly until SIGINT/SIGTERM or an injected stop event.

    This is a plain Python host process, not a Windows service. It proves the runtime can remain
    alive independently from browser/FastAPI hosting while PF1 stabilizes the boundary.
    """
    event = stop_event or Event()
    host = get_runtime_host()
    runtime = host.start()

    def request_stop(signum, frame) -> None:  # noqa: ARG001
        event.set()

    handlers_installed = stop_event is None
    previous_handlers: dict[int, object] = {}
    if handlers_installed:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, request_stop)

    logger.info("Campanario runtime started runtime_id=%s", runtime.state.runtime_id)
    try:
        event.wait()
    finally:
        host.stop()
        logger.info("Campanario runtime stopped runtime_id=%s", runtime.state.runtime_id)
        if handlers_installed:
            for signum, previous in previous_handlers.items():
                signal.signal(signum, previous)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    run_until_stopped()
