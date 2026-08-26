from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from uuid import UUID

from campanario.agents.addressing import fold_text
from campanario.runtime.events import ContextUpdatedPayload, EventProvenance, EventSourceKind, EventType


class PresenceState(StrEnum):
    PRESENT = "present"
    ATTENTIVE = "attentive"
    ENGAGED = "engaged"


@dataclass(frozen=True, slots=True)
class SessionPresence:
    session_id: UUID
    state: PresenceState = PresenceState.PRESENT
    attention_until: datetime | None = None
    active_agent_id: str | None = None
    updated_at: datetime | None = None

    @property
    def attention_open(self) -> bool:
        return self.attention_until is not None and self.attention_until > datetime.now(UTC)


class PresenceManager:
    """Shared session-level presence. It belongs to Campanario, not to a UI or an agent."""

    def __init__(self, event_bus, *, attention_window_seconds: int = 45) -> None:
        self._events = event_bus
        self._window = timedelta(seconds=attention_window_seconds)
        self._items: dict[UUID, SessionPresence] = {}
        self._lock = RLock()

    def get(self, session_id: UUID) -> SessionPresence:
        with self._lock:
            item = self._items.get(session_id)
            if item is None:
                item = SessionPresence(session_id=session_id, updated_at=datetime.now(UTC))
                self._items[session_id] = item
            if item.state != PresenceState.PRESENT and not item.attention_open:
                item = replace(item, state=PresenceState.PRESENT, active_agent_id=None, updated_at=datetime.now(UTC))
                self._items[session_id] = item
            return item

    def wake(self, session_id: UUID, *, source_id: str, direct_agent_id: str | None = None) -> SessionPresence:
        now = datetime.now(UTC)
        state = PresenceState.ENGAGED if direct_agent_id else PresenceState.ATTENTIVE
        item = SessionPresence(session_id, state, now + self._window, direct_agent_id, now)
        return self._set(item, source_id)

    def engage(self, session_id: UUID, *, source_id: str, agent_id: str | None = None) -> SessionPresence:
        now = datetime.now(UTC)
        return self._set(SessionPresence(session_id, PresenceState.ENGAGED, now + self._window, agent_id, now), source_id)

    def quiet(self, session_id: UUID, *, source_id: str) -> SessionPresence:
        now = datetime.now(UTC)
        return self._set(SessionPresence(session_id, PresenceState.PRESENT, None, None, now), source_id)

    def _set(self, item: SessionPresence, source_id: str) -> SessionPresence:
        with self._lock:
            self._items[item.session_id] = item
        self._events.publish(
            EventType.CONTEXT_UPDATED,
            ContextUpdatedPayload(keys=("presence.state", item.state.value)),
            provenance=EventProvenance(source_kind=EventSourceKind.RUNTIME, source_id=source_id),
            session_id=item.session_id,
        )
        return item


def resolve_wake(text: str) -> tuple[bool, str | None, str]:
    """Recognize Campanario wake/direct address without turning agent names into separate sessions.

    STT commonly returns the correct Portuguese spelling ``Campanário``. Matching therefore uses
    accent-folded text while slicing the original utterance, so both accented and unaccented wake
    forms behave identically.
    """
    raw = text.strip()
    folded = fold_text(raw)
    for token, agent in (("morgana", "morgana"), ("todd", "todd")):
        if folded == token or folded.startswith(token + ",") or folded.startswith(token + " "):
            return True, agent, raw[len(token):].lstrip(" ,:;-")
    token = "campanario"
    if folded == token or folded.startswith(token + ",") or folded.startswith(token + " "):
        return True, None, raw[len(token):].lstrip(" ,:;-")
    return False, None, raw
