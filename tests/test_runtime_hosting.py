from threading import Event

import pytest

from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.runtime.core import RuntimeNotRunningError
from campanario.runtime.hosting import RuntimeHost
from campanario.runtime.process import run_until_stopped


def test_runtime_lifecycle_is_explicit_and_idempotent(tmp_path):
    runtime = build_runtime(
        Settings(),
        database_url=f"sqlite:///{tmp_path / 'runtime.db'}",
        create_schema=True,
        autostart=False,
    )

    assert runtime.state.status == "stopped"
    assert runtime.state.started_at is None

    runtime.start()
    first_started_at = runtime.state.started_at
    runtime.start()

    assert runtime.state.status == "running"
    assert runtime.state.started_at == first_started_at

    runtime.stop()
    assert runtime.state.status == "stopped"
    assert runtime.state.stopped_at is not None
    with pytest.raises(RuntimeNotRunningError):
        _ = runtime.conversation


def test_runtime_host_owns_single_active_runtime(tmp_path):
    settings = Settings()
    database_url = f"sqlite:///{tmp_path / 'runtime.db'}"
    created = []

    def factory():
        runtime = build_runtime(settings, database_url=database_url, create_schema=True, autostart=False)
        created.append(runtime)
        return runtime

    host = RuntimeHost(factory)
    first = host.start()
    second = host.start()

    assert first is second
    assert len(created) == 1
    assert host.runtime is first
    assert host.is_running is True


def test_runtime_host_restart_rebuilds_runtime_but_preserves_sessions(tmp_path):
    settings = Settings()
    database_url = f"sqlite:///{tmp_path / 'runtime.db'}"

    def factory():
        return build_runtime(settings, database_url=database_url, create_schema=True, autostart=False)

    host = RuntimeHost(factory)
    first = host.start()
    session = first.sessions.create_session("persisted")
    first_runtime_id = first.state.runtime_id
    host.stop()

    second = host.start()

    assert second.state.runtime_id != first_runtime_id
    assert [item.id for item in second.sessions.list_sessions()] == [session.id]


def test_headless_host_process_can_run_without_fastapi_or_web_ui(monkeypatch):
    class FakeRuntime:
        def __init__(self) -> None:
            self.state = type("State", (), {"runtime_id": "runtime-test"})()

    class FakeHost:
        def __init__(self) -> None:
            self.started = 0
            self.stopped = 0

        def start(self):
            self.started += 1
            return FakeRuntime()

        def stop(self):
            self.stopped += 1

    fake = FakeHost()
    monkeypatch.setattr("campanario.runtime.process.get_runtime_host", lambda: fake)
    stop = Event()
    stop.set()

    run_until_stopped(stop)

    assert fake.started == 1
    assert fake.stopped == 1


def test_fastapi_lifespan_starts_and_stops_runtime_host(monkeypatch):
    from fastapi.testclient import TestClient
    import campanario.main as main_module

    class FakeHost:
        def __init__(self) -> None:
            self.started = 0
            self.stopped = 0

        def start(self):
            self.started += 1
            return object()

        def stop(self):
            self.stopped += 1

    fake = FakeHost()
    monkeypatch.setattr(main_module, "get_runtime_host", lambda: fake)

    with TestClient(main_module.app) as client:
        assert client.get("/health").status_code == 200
        assert fake.started == 1
        assert fake.stopped == 0

    assert fake.stopped == 1
