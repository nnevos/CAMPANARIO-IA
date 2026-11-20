"""v0.6: deletion safeguards; no model service or user data required."""
from datetime import datetime, UTC
from types import SimpleNamespace
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from campanario.storage.database import Base, build_session_factory
from campanario.storage.repositories import SqlAlchemyChatSessionRepository
from campanario.storage.models import ChatSessionRow, MessageRow
from campanario.chat.models import ChatSession
from campanario.main import app
import campanario.api as api_module


def test_session_delete_removes_chat_and_keeps_other_sessions(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'test.db'))
    Base.metadata.create_all(engine)
    repo=SqlAlchemyChatSessionRepository(build_session_factory(engine))
    first=ChatSession(id=uuid4(),title='Um',created_at=datetime.now(UTC),updated_at=datetime.now(UTC),primary_agent_id='morgana')
    other=ChatSession(id=uuid4(),title='Outro',created_at=datetime.now(UTC),updated_at=datetime.now(UTC),primary_agent_id='morgana')
    repo.create(first);repo.create(other)
    with build_session_factory(engine)() as db:
        db.add(MessageRow(id=str(uuid4()),session_id=str(first.id),role='user',content='segredo de teste',created_at=datetime.now(UTC),status='completed'))
        db.commit()
    assert repo.delete(first.id) is True
    assert repo.get(first.id) is None
    assert repo.get(other.id) is not None
    assert repo.delete(first.id) is False
    with build_session_factory(engine)() as db:
        assert not db.scalars(select(MessageRow).where(MessageRow.session_id==str(first.id))).all()
    engine.dispose()


def test_destructive_endpoints_require_exact_phrase(monkeypatch):
    class DummyConversation:
        def delete_session(self,session_id):pass
    monkeypatch.setattr(api_module,'get_runtime',lambda:SimpleNamespace(conversation=DummyConversation()))
    with TestClient(app) as client:
        route=f'/api/v1/sessions/{uuid4()}'
        assert client.request('DELETE',route,json={'confirmation':'incorrect'}).status_code==422
        assert client.request('DELETE',route,json={'confirmation':'EXCLUIR CONVERSA'}).status_code==200
        assert client.post('/api/v1/memory/forget-all',json={'confirmation':'incorrect'}).status_code==422
