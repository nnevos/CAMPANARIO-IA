"""Kiwix desktop lifecycle: no real .exe, HTTP server, internet or user files."""
from __future__ import annotations

import subprocess
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
import sys

import pytest

from campanario.app import kiwix_autostart as ka
from campanario.config import Settings


class FakeChild:
    def __init__(self, returncode=None, *, timeout=False):
        self.returncode = returncode
        self.timeout = timeout
        self.terminated = 0
        self.killed = 0
        self.waited = []

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated += 1
        self.returncode = 0

    def kill(self):
        self.killed += 1
        self.returncode = -9

    def wait(self, timeout=None):
        self.waited.append(timeout)
        if self.timeout and not self.killed:
            raise subprocess.TimeoutExpired('kiwix-serve', timeout)
        return self.returncode


@pytest.fixture
def fake_install(tmp_path):
    # Include spaces to prove Popen uses argument arrays, not shell quoting.
    base = tmp_path / 'GitHub with spaces' / 'CAMPANARIO-DATABASE'
    data = base / 'dados'
    data.mkdir(parents=True)
    zim = base / 'zim'
    zim.mkdir()
    old = zim / 'wikipedia_pt_all_nopic_2026-04.zim'
    new = zim / 'wikipedia_pt_all_nopic_2026-05.zim'
    old.write_bytes(b'old')
    new.write_bytes(b'new')
    tools = base / 'kiwix' / 'kiwix-tools_win-x86_64'
    tools.mkdir(parents=True)
    exe = tools / 'kiwix-serve.exe'
    exe.write_bytes(b'dummy')
    settings = Settings(data_dir=data, zim_dir=zim, zim_enabled=True,
                        zim_auto_start=True, _env_file=None)
    return settings, exe, new


@pytest.mark.parametrize('url,port', [
    ('http://127.0.0.1:8181', 8181),
    ('http://localhost:8182/', 8182),
    ('https://127.0.0.1:8181', None),
    ('http://192.168.1.1:8181', None),
    ('http://0.0.0.0:8181', None),
    ('http://example.com:8181', None),
    ('http://127.0.0.1:8181/x', None),
    ('http://u:p@127.0.0.1:8181', None),
    ('http://127.0.0.1:8181?x=1', None),
    ('http://127.0.0.1:8181#x', None),
    ('http://127.0.0.1', None),
    ('http://127.0.0.1:0', None),
    ('http://127.0.0.1:99999', None),
    ('not a URL', None),
])
def test_only_loopback_http_with_explicit_port(url, port):
    assert ka._listen_port(url) == port


@pytest.mark.parametrize('disabled', ['zim', 'auto'])
def test_disabled_never_launches(fake_install, monkeypatch, disabled):
    settings, _, _ = fake_install
    settings.zim_enabled = disabled != 'zim'
    settings.zim_auto_start = disabled != 'auto'
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: pytest.fail('spawned while disabled'))
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'disabled'
    runner.stop()


def test_non_windows_does_not_spawn_windows_executable(fake_install, monkeypatch):
    settings, _, _ = fake_install
    monkeypatch.setattr(ka, '_is_windows', lambda: False)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: pytest.fail('spawning on Linux'))
    assert ka.DesktopKiwix(settings).start() == 'windows_only'


@pytest.mark.parametrize('missing,expected', [
    ('dir', 'zim_directory_missing'),
    ('archive', 'zim_file_missing'),
    ('tools', 'kiwix_tools_missing'),
    ('exe', 'kiwix_executable_missing'),
])
def test_missing_dependencies_do_not_spawn(fake_install, monkeypatch, missing, expected):
    settings, exe, article = fake_install
    if missing == 'dir':
        settings.zim_dir = article.parent / 'does_not_exist'
    elif missing == 'archive':
        article.unlink()
        (article.parent / 'wikipedia_pt_all_nopic_2026-04.zim').unlink()
    elif missing == 'tools':
        import shutil
        shutil.rmtree(exe.parent.parent)
    else:
        exe.unlink()
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: pytest.fail('spawned without files'))
    assert ka.DesktopKiwix(settings).start() == expected


def test_starts_silent_loopback_and_only_stops_owned_child(fake_install, monkeypatch):
    settings, exe, article = fake_install
    child = FakeChild()
    launch = []
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: bool(launch))
    monkeypatch.setattr(ka.subprocess, 'CREATE_NO_WINDOW', 0x08000000, raising=False)
    def fake_popen(args, **kwargs):
        launch.append((args, kwargs))
        return child
    monkeypatch.setattr(ka.subprocess, 'Popen', fake_popen)
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'running'
    args, kwargs = launch[0]
    assert args == [str(exe), '--address=127.0.0.1', '--port=8181',
                    '--blockexternal', str(article)]
    assert kwargs['cwd'] == str(exe.parent)
    assert kwargs['creationflags'] == 0x08000000
    assert kwargs['shell'] is False
    assert kwargs['stdin'] == kwargs['stdout'] == kwargs['stderr'] == subprocess.DEVNULL
    assert runner.start() == 'already_started_by_campanario'
    runner.stop()
    runner.stop()
    assert child.terminated == 1
    assert child.killed == 0
    assert runner.start() == 'stopped'


def test_existing_manual_server_is_not_stopped(fake_install, monkeypatch):
    settings, _, _ = fake_install
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: True)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: pytest.fail('launched a second server'))
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'external_listener'
    runner.stop()  # must never taskkill, terminate, or adopt external process


def test_custom_port_and_book_selection_matches_reader(fake_install, monkeypatch):
    settings, exe, article = fake_install
    settings.zim_base_url = 'http://localhost:8190/'
    seen = []
    child = FakeChild()
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: bool(seen))
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda args, **kw: (seen.append(args) or child))
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'running'
    assert '--port=8190' in seen[0]
    assert seen[0][-1] == str(article)
    runner.stop()


def test_unavailable_child_does_not_crash_desktop(fake_install, monkeypatch):
    settings, _, _ = fake_install
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: False)
    def denied(*args, **kwargs):
        raise PermissionError('simulated denied')
    monkeypatch.setattr(ka.subprocess, 'Popen', denied)
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'start_failed'
    runner.stop()


def test_child_exits_early_and_is_not_reaped_twice(fake_install, monkeypatch):
    settings, _, _ = fake_install
    child = FakeChild(returncode=1)
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: False)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: child)
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'exited_early'
    runner.stop()
    assert child.terminated == 0


def test_termination_escalates_only_for_owned_child(fake_install, monkeypatch):
    settings, _, _ = fake_install
    child = FakeChild(timeout=True)
    monkeypatch.setattr(ka, '_is_windows', lambda: True)
    monkeypatch.setattr(ka, '_listening', lambda port: False)
    monkeypatch.setattr(ka.subprocess, 'Popen', lambda *a, **k: child)
    monkeypatch.setattr(ka.time, 'monotonic', lambda: 0)  # start() loops unless externally closed
    monkeypatch.setattr(ka.Event, 'wait', lambda event, seconds: runner._closed.set())
    runner = ka.DesktopKiwix(settings)
    assert runner.start() == 'stopped'
    runner.stop()
    assert child.terminated == 1
    assert child.killed == 1


def test_desktop_starts_then_stops_kiwix_even_when_window_closes(fake_install, monkeypatch, tmp_path):
    from campanario.app import desktop
    settings, _, _ = fake_install
    events = []
    class FakeLock:
        def __init__(self, path):
            pass
        def acquire(self): events.append('lock')
        def release(self): events.append('unlock')
    class FakeServer:
        def __init__(self, port): pass
        def start(self):
            events.append('server.start')
            return 'http://127.0.0.1:8000/'
        def stop(self): events.append('server.stop')
    class FakeKiwix:
        def __init__(self, settings): pass
        def start(self): events.append('kiwix.start')
        def stop(self): events.append('kiwix.stop')
    class FakeWindow:
        def load_url(self, url): events.append('window.load')
        def load_html(self, text): events.append('window.error')
    monkeypatch.setattr(desktop, 'project_root', lambda: tmp_path)
    monkeypatch.setattr(desktop, 'InstanceLock', FakeLock)
    monkeypatch.setattr(desktop, 'DesktopServer', FakeServer)
    monkeypatch.setattr(desktop, 'DesktopKiwix', FakeKiwix)
    monkeypatch.setattr('campanario.config.get_settings', lambda: settings)
    monkeypatch.setattr(desktop.os, 'chdir', lambda _: None)
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace(
        create_window=lambda *a, **kw: FakeWindow(),
        start=lambda boot, **kw: boot(),
    ))
    assert desktop.main() == 0
    assert events.index('kiwix.start') < events.index('server.start')
    assert events.index('window.load') < events.index('server.stop')
    assert events.index('server.stop') < events.index('kiwix.stop') < events.index('unlock')


def test_kiwix_exception_does_not_block_application(fake_install, monkeypatch, tmp_path):
    from campanario.app import desktop
    settings, _, _ = fake_install
    events = []
    class FakeLock:
        def __init__(self, path): pass
        def acquire(self): pass
        def release(self): pass
    class FakeServer:
        def __init__(self, port): pass
        def start(self):
            events.append('server')
            return 'http://127.0.0.1:8000/'
        def stop(self): pass
    class FailingKiwix:
        def __init__(self, settings): pass
        def start(self): raise RuntimeError('KIWIX offline')
        def stop(self): events.append('kiwix.stop')
    class FakeWindow:
        def load_url(self, url): events.append('loaded')
        def load_html(self, text): events.append('error')
    monkeypatch.setattr(desktop, 'project_root', lambda: tmp_path)
    monkeypatch.setattr(desktop, 'InstanceLock', FakeLock)
    monkeypatch.setattr(desktop, 'DesktopServer', FakeServer)
    monkeypatch.setattr(desktop, 'DesktopKiwix', FailingKiwix)
    monkeypatch.setattr('campanario.config.get_settings', lambda: settings)
    monkeypatch.setattr(desktop.os, 'chdir', lambda _: None)
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace(
        create_window=lambda *a, **kw: FakeWindow(),
        start=lambda boot, **kw: boot(),
    ))
    assert desktop.main() == 0
    assert events == ['server', 'loaded', 'kiwix.stop']


def test_closing_desktop_mid_kiwix_start_prevents_late_server(fake_install, monkeypatch, tmp_path):
    from threading import Event, Thread
    from campanario.app import desktop
    settings, _, _ = fake_install
    entered, release = Event(), Event()
    events = []
    threads = []
    class FakeLock:
        def __init__(self, path): pass
        def acquire(self): pass
        def release(self): pass
    class FakeServer:
        def __init__(self, port): pass
        def start(self):
            events.append('server.start')
            return 'http://127.0.0.1:8000/'
        def stop(self): events.append('server.stop')
    class FakeKiwix:
        def __init__(self, settings): pass
        def start(self):
            entered.set()
            release.wait(2)
        def stop(self):
            events.append('kiwix.stop')
            release.set()
    class FakeWindow:
        def load_url(self, url): events.append('window.load')
        def load_html(self, text): events.append('window.error')
    def webview_start(boot, **kwargs):
        thread = Thread(target=boot)
        threads.append(thread)
        thread.start()
        assert entered.wait(2)
        # Window closes while Kiwix is still loading the archive.
    monkeypatch.setattr(desktop, 'project_root', lambda: tmp_path)
    monkeypatch.setattr(desktop, 'InstanceLock', FakeLock)
    monkeypatch.setattr(desktop, 'DesktopServer', FakeServer)
    monkeypatch.setattr(desktop, 'DesktopKiwix', FakeKiwix)
    monkeypatch.setattr('campanario.config.get_settings', lambda: settings)
    monkeypatch.setattr(desktop.os, 'chdir', lambda _: None)
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace(
        create_window=lambda *a, **kw: FakeWindow(),
        start=webview_start,
    ))
    assert desktop.main() == 0
    for t in threads:
        t.join(timeout=2)
        assert not t.is_alive()
    assert 'server.start' not in events
    assert 'kiwix.stop' in events
