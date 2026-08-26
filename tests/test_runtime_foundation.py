from campanario.composition import build_runtime
from campanario.config import Settings


def test_runtime_boots_without_fastapi_or_web_ui(tmp_path):
    settings = Settings()
    runtime = build_runtime(settings, database_url=f"sqlite:///{tmp_path / 'runtime.db'}", create_schema=True)

    assert runtime.state.status == "running"
    assert runtime.conversation is not None
    assert runtime.sessions.list_sessions() == []


def test_session_is_owned_by_runtime_not_client(tmp_path):
    settings = Settings()
    runtime = build_runtime(settings, database_url=f"sqlite:///{tmp_path / 'runtime.db'}", create_schema=True)

    created = runtime.sessions.create_session("shared")
    observed_from_same_runtime = runtime.conversation.list_sessions()

    assert [session.id for session in observed_from_same_runtime] == [created.id]
    assert created.primary_agent_id == runtime.conversation.default_primary_agent_id


def test_api_runtime_boundary_can_expose_same_runtime_identity(tmp_path):
    settings = Settings()
    runtime = build_runtime(settings, database_url=f"sqlite:///{tmp_path / 'runtime.db'}", create_schema=True)

    first_id = runtime.state.runtime_id
    runtime.sessions.create_session("same-runtime")

    assert runtime.state.runtime_id == first_id
    assert [session.title for session in runtime.conversation.list_sessions()] == ["same-runtime"]


def test_runtime_exposes_single_event_bus_identity(tmp_path):
    settings = Settings()
    runtime = build_runtime(settings, database_url=f"sqlite:///{tmp_path / 'runtime-events.db'}", create_schema=True)

    assert runtime.events.runtime_id == runtime.state.runtime_id
    first = runtime.events
    second = runtime.events
    assert first is second
