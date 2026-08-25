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
