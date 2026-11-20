from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from campanario.chat.models import ChatSession, ContextSummary, Message, MessageRole
from campanario.storage.models import ChatSessionRow, ContextSummaryRow, MessageRow

SessionFactory = Callable[[], Session]


def _session_from_row(row: ChatSessionRow) -> ChatSession:
    return ChatSession(
        id=UUID(row.id),
        title=row.title,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        primary_agent_id=row.primary_agent_id,
    )


def _message_from_row(row: MessageRow) -> Message:
    return Message(
        id=UUID(row.id),
        session_id=UUID(row.session_id),
        role=MessageRole(row.role),
        content=row.content,
        created_at=row.created_at,
        model=row.model,
        status=row.status,
        agent_id=row.agent_id,
        client_id=row.client_id,
        device_id=row.device_id,
    )


class SqlAlchemyChatSessionRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def create(self, session: ChatSession) -> ChatSession:
        row = ChatSessionRow(
            id=str(session.id),
            title=session.title,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            primary_agent_id=session.primary_agent_id,
        )
        with self._session_factory() as db:
            db.add(row)
            db.commit()
        return session

    def get(self, session_id: UUID) -> ChatSession | None:
        with self._session_factory() as db:
            row = db.get(ChatSessionRow, str(session_id))
            return _session_from_row(row) if row else None

    def list(self) -> list[ChatSession]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(ChatSessionRow).order_by(ChatSessionRow.updated_at.desc())
            ).all()
            return [_session_from_row(row) for row in rows]

    def delete(self, session_id: UUID) -> bool:
        from sqlalchemy import delete
        from campanario.storage.models import ContextSummaryRow, MessageRow
        with self._session_factory() as db:
            row = db.get(ChatSessionRow, str(session_id))
            if row is None:
                return False
            # Explicit ordering works across SQLite and other SQL engines.
            db.execute(delete(ContextSummaryRow).where(ContextSummaryRow.session_id == str(session_id)))
            db.execute(delete(MessageRow).where(MessageRow.session_id == str(session_id)))
            db.delete(row)
            db.commit()
        return True

    def set_primary_agent(self, session_id: UUID, agent_id: str) -> ChatSession | None:
        with self._session_factory() as db:
            row = db.get(ChatSessionRow, str(session_id))
            if row is None:
                return None
            row.primary_agent_id = agent_id
            db.commit()
            db.refresh(row)
            return _session_from_row(row)

    def set_agent(self, session_id: UUID, agent_id: str) -> ChatSession | None:
        return self.set_primary_agent(session_id, agent_id)


class SqlAlchemyMessageRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def append(self, message: Message) -> Message:
        row = MessageRow(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role.value,
            content=message.content,
            created_at=message.created_at,
            model=message.model,
            status=message.status,
            agent_id=message.agent_id,
            client_id=message.client_id,
            device_id=message.device_id,
        )
        with self._session_factory() as db:
            db.add(row)
            db.commit()
        return message

    def list_by_session(self, session_id: UUID) -> list[Message]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(MessageRow)
                .where(MessageRow.session_id == str(session_id))
                .order_by(MessageRow.created_at.asc())
            ).all()
            return [_message_from_row(row) for row in rows]


class SqlAlchemyContextSummaryRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def get(self, session_id: UUID) -> ContextSummary | None:
        with self._session_factory() as db:
            row = db.get(ContextSummaryRow, str(session_id))
            if row is None:
                return None
            return ContextSummary(
                session_id=UUID(row.session_id),
                content=row.content,
                through_message_id=UUID(row.through_message_id),
                updated_at=row.updated_at,
            )

    def upsert(self, summary: ContextSummary) -> ContextSummary:
        with self._session_factory() as db:
            row = db.get(ContextSummaryRow, str(summary.session_id))
            if row is None:
                row = ContextSummaryRow(session_id=str(summary.session_id))
                db.add(row)
            row.content = summary.content
            row.through_message_id = str(summary.through_message_id)
            row.updated_at = summary.updated_at
            db.commit()
        return summary


def _device_from_row(row):
    from campanario.runtime.devices import Device, DeviceConnectionState

    return Device(
        id=row.id,
        name=row.name,
        type=row.type,
        capabilities=tuple(row.capabilities or ()),
        connection_state=DeviceConnectionState(row.connection_state),
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_seen=row.last_seen,
    )


class SqlAlchemyDeviceRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def get(self, device_id: str):
        from campanario.storage.models import DeviceRow

        with self._session_factory() as db:
            row = db.get(DeviceRow, device_id)
            return _device_from_row(row) if row else None

    def list(self):
        from campanario.storage.models import DeviceRow

        with self._session_factory() as db:
            rows = db.scalars(select(DeviceRow).order_by(DeviceRow.last_seen.desc(), DeviceRow.id.asc())).all()
            return [_device_from_row(row) for row in rows]

    def upsert(self, device):
        from campanario.storage.models import DeviceRow

        with self._session_factory() as db:
            row = db.get(DeviceRow, device.id)
            if row is None:
                row = DeviceRow(id=device.id)
                db.add(row)
            row.name = device.name
            row.type = device.type
            row.capabilities = list(device.capabilities)
            row.connection_state = device.connection_state.value
            row.created_at = device.created_at
            row.updated_at = device.updated_at
            row.last_seen = device.last_seen
            db.commit()
            db.refresh(row)
            return _device_from_row(row)

    def find_by_capability(self, capability: str):
        # JSON membership differs by SQL backend; keep PF4 provider-neutral at the repository API
        # and filter the small local registry in Python. The storage detail can evolve independently.
        return [device for device in self.list() if capability in device.capabilities]


class SqlAlchemyTrustRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def get_trust(self, device_id: str):
        from campanario.storage.models import DeviceRow
        with self._session_factory() as db:
            row = db.get(DeviceRow, device_id)
            if row is None:
                return None
            return {"trusted": bool(row.trusted), "credential_hash": row.credential_hash, "revoked_at": row.revoked_at}

    def set_trust(self, device_id: str, *, trusted: bool, credential_hash: str | None, revoked_at):
        from campanario.storage.models import DeviceRow
        with self._session_factory() as db:
            row = db.get(DeviceRow, device_id)
            if row is None:
                raise KeyError(device_id)
            row.trusted = trusted
            row.credential_hash = credential_hash
            row.revoked_at = revoked_at
            db.commit()

    def append_audit(self, *, action: str, principal_id: str, device_id: str | None, capability: str | None, permission: str | None, decision: str, detail: str | None):
        from datetime import UTC, datetime
        from campanario.storage.models import SecurityAuditRow
        with self._session_factory() as db:
            db.add(SecurityAuditRow(created_at=datetime.now(UTC), action=action, principal_id=principal_id, device_id=device_id, capability=capability, permission=permission, decision=decision, detail=detail))
            db.commit()

    def list_audit(self, *, limit: int = 100):
        from campanario.storage.models import SecurityAuditRow
        with self._session_factory() as db:
            rows = db.scalars(select(SecurityAuditRow).order_by(SecurityAuditRow.id.desc()).limit(max(1, min(limit, 1000)))).all()
            return [{"id": row.id, "created_at": row.created_at, "action": row.action, "principal_id": row.principal_id, "device_id": row.device_id, "capability": row.capability, "permission": row.permission, "decision": row.decision, "detail": row.detail} for row in rows]


def _experience_from_row(row):
    from uuid import UUID
    from campanario.runtime.experience import ExperienceMemory, MemoryKind, MemorySource, MemoryStatus

    return ExperienceMemory(
        id=UUID(row.id),
        kind=MemoryKind(row.kind),
        subject=row.subject,
        key=row.key,
        value=row.value,
        confidence=row.confidence,
        source=MemorySource(row.source),
        status=MemoryStatus(row.status),
        evidence=row.evidence,
        source_session_id=UUID(row.source_session_id) if row.source_session_id else None,
        source_message_id=UUID(row.source_message_id) if row.source_message_id else None,
        source_agent_id=row.source_agent_id,
        supersedes_id=UUID(row.supersedes_id) if row.supersedes_id else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_confirmed_at=row.last_confirmed_at,
        last_recalled_at=row.last_recalled_at,
        recall_count=row.recall_count,
    )


class SqlAlchemyExperienceRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def create(self, memory):
        from campanario.storage.models import ExperienceMemoryRow

        row = ExperienceMemoryRow(
            id=str(memory.id), kind=memory.kind.value, subject=memory.subject, key=memory.key,
            value=memory.value, confidence=memory.confidence, source=memory.source.value,
            status=memory.status.value, evidence=memory.evidence,
            source_session_id=str(memory.source_session_id) if memory.source_session_id else None,
            source_message_id=str(memory.source_message_id) if memory.source_message_id else None,
            source_agent_id=memory.source_agent_id,
            supersedes_id=str(memory.supersedes_id) if memory.supersedes_id else None,
            created_at=memory.created_at, updated_at=memory.updated_at,
            last_confirmed_at=memory.last_confirmed_at, last_recalled_at=memory.last_recalled_at,
            recall_count=memory.recall_count,
        )
        with self._session_factory() as db:
            db.add(row)
            db.commit()
        return memory

    def get(self, memory_id):
        from campanario.storage.models import ExperienceMemoryRow
        with self._session_factory() as db:
            row = db.get(ExperienceMemoryRow, str(memory_id))
            return _experience_from_row(row) if row else None

    def list(self, *, include_inactive: bool = False, limit: int = 500):
        from campanario.storage.models import ExperienceMemoryRow
        from campanario.runtime.experience import MemoryStatus
        query = select(ExperienceMemoryRow)
        if not include_inactive:
            query = query.where(ExperienceMemoryRow.status == MemoryStatus.ACTIVE.value)
        query = query.order_by(ExperienceMemoryRow.updated_at.desc()).limit(limit)
        with self._session_factory() as db:
            rows = db.scalars(query).all()
            return [_experience_from_row(row) for row in rows]

    def find_active(self, subject: str, key: str):
        from campanario.storage.models import ExperienceMemoryRow
        from campanario.runtime.experience import MemoryStatus
        with self._session_factory() as db:
            row = db.scalars(
                select(ExperienceMemoryRow)
                .where(ExperienceMemoryRow.subject == subject)
                .where(ExperienceMemoryRow.key == key)
                .where(ExperienceMemoryRow.status == MemoryStatus.ACTIVE.value)
                .order_by(ExperienceMemoryRow.updated_at.desc())
                .limit(1)
            ).first()
            return _experience_from_row(row) if row else None

    def update(self, memory):
        from campanario.storage.models import ExperienceMemoryRow
        with self._session_factory() as db:
            row = db.get(ExperienceMemoryRow, str(memory.id))
            if row is None:
                raise KeyError(str(memory.id))
            row.kind = memory.kind.value
            row.subject = memory.subject
            row.key = memory.key
            row.value = memory.value
            row.confidence = memory.confidence
            row.source = memory.source.value
            row.status = memory.status.value
            row.evidence = memory.evidence
            row.source_session_id = str(memory.source_session_id) if memory.source_session_id else None
            row.source_message_id = str(memory.source_message_id) if memory.source_message_id else None
            row.source_agent_id = memory.source_agent_id
            row.supersedes_id = str(memory.supersedes_id) if memory.supersedes_id else None
            row.updated_at = memory.updated_at
            row.last_confirmed_at = memory.last_confirmed_at
            row.last_recalled_at = memory.last_recalled_at
            row.recall_count = memory.recall_count
            db.commit()
        return memory
