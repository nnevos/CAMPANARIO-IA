from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from time import perf_counter_ns
from typing import Any
from uuid import UUID

from campanario.runtime.events import EventType, RuntimeEvent, RuntimeEventBus


@dataclass(frozen=True, slots=True)
class TelemetryPoint:
    name: str
    occurred_at: datetime
    monotonic_ns: int
    runtime_id: UUID
    correlation_id: UUID | None = None
    session_id: UUID | None = None
    agent_id: str | None = None
    client_id: str | None = None
    device_id: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()


class RuntimeTelemetry:
    """Process-local architectural timing journal.

    This is deliberately transport/provider independent. It records stable milestone names and
    provenance now; exporting to OpenTelemetry/Prometheus is a later adapter concern.
    """

    def __init__(self, runtime_id: UUID, *, journal_limit: int = 20_000) -> None:
        self.runtime_id = runtime_id
        self._journal_limit = journal_limit
        self._points: list[TelemetryPoint] = []
        self._lock = RLock()

    def mark(
        self,
        name: str,
        *,
        correlation_id: UUID | None = None,
        session_id: UUID | None = None,
        agent_id: str | None = None,
        client_id: str | None = None,
        device_id: str | None = None,
        **attributes: Any,
    ) -> TelemetryPoint:
        point = TelemetryPoint(
            name=name,
            occurred_at=datetime.now(UTC),
            monotonic_ns=perf_counter_ns(),
            runtime_id=self.runtime_id,
            correlation_id=correlation_id,
            session_id=session_id,
            agent_id=agent_id,
            client_id=client_id,
            device_id=device_id,
            attributes=tuple(sorted((str(key), str(value)) for key, value in attributes.items() if value is not None)),
        )
        with self._lock:
            self._points.append(point)
            if len(self._points) > self._journal_limit:
                del self._points[: len(self._points) - self._journal_limit]
        return point

    def snapshot(self, *, correlation_id: UUID | None = None) -> tuple[TelemetryPoint, ...]:
        with self._lock:
            points = tuple(self._points)
        if correlation_id is None:
            return points
        return tuple(point for point in points if point.correlation_id == correlation_id)

    def duration_ms(self, start: TelemetryPoint, end: TelemetryPoint) -> float:
        return max(0.0, (end.monotonic_ns - start.monotonic_ns) / 1_000_000.0)

    def bind_event_bus(self, event_bus: RuntimeEventBus) -> None:
        event_bus.subscribe(self._on_event)

    def _on_event(self, event: RuntimeEvent) -> None:
        names = {
            EventType.TOOL_STARTED: "tool_started",
            EventType.TOOL_RESULT: "tool_finished",
            EventType.TOOL_FAILED: "tool_finished",
        }
        name = names.get(event.event_type)
        if name is None:
            return
        self.mark(
            name,
            correlation_id=event.correlation_id,
            session_id=event.session_id,
            agent_id=event.provenance.agent_id,
            client_id=event.provenance.client_id,
            device_id=event.provenance.device_id,
            event_id=event.event_id,
            event_type=event.event_type.value,
            source_kind=event.provenance.source_kind.value,
            source_id=event.provenance.source_id,
        )
