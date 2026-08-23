from datetime import UTC, datetime
from uuid import uuid4

from campanario.chat.models import ChatSession, Message, MessageRole
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import (
    SqlAlchemyChatSessionRepository,
    SqlAlchemyMessageRepository,
)


def test_sqlalchemy_repositories_round_trip() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    sessions = SqlAlchemyChatSessionRepository(factory)
    messages = SqlAlchemyMessageRepository(factory)

    now = datetime.now(UTC)
    session = ChatSession(id=uuid4(), created_at=now, updated_at=now)
    sessions.create(session)
    message = Message(
        id=uuid4(),
        session_id=session.id,
        role=MessageRole.USER,
        content="teste",
        created_at=now,
    )
    messages.append(message)

    loaded_session = sessions.get(session.id)
    loaded_messages = messages.list_by_session(session.id)

    assert loaded_session is not None
    assert loaded_session.id == session.id
    assert [item.content for item in loaded_messages] == ["teste"]
