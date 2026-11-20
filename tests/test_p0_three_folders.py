"""P0 tests: no user databases/venvs are touched; all layouts are temporary."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from campanario.brains.environment import inspect_three_folders
from campanario.brains.contracts import BrainDefinition, BrainRequest, BrainResult, BrainStatus
from campanario.brains.executor import BrainExecutor
from campanario.brains.registry import BrainRegistry
from campanario.brains.router import BrainPlan


def _fixture(tmp_path: Path):
    ia = tmp_path / 'CAMPANARIO-IA'
    (ia / 'src' / 'campanario').mkdir(parents=True)
    (ia / 'pyproject.toml').write_text('[project]\nname = "test"\n')
    venv_python = tmp_path / 'CAMPANARIO-PYTHON' / '.venv' / 'Scripts' / 'python.exe'
    venv_python.parent.mkdir(parents=True)
    venv_python.write_bytes(b'fixture binary')
    db_dir = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    db_path = db_dir / 'desenvolvimento' / 'campanario.db'
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b'SQLite format 3\x00' + b'\0' * 96)
    return ia, venv_python, db_dir, db_path


def test_three_folders_expected_paths_and_no_writes(tmp_path):
    ia, py, data, db = _fixture(tmp_path)
    before = {str(p): p.stat().st_mtime_ns for p in tmp_path.rglob('*') if p.is_file()}
    report = inspect_three_folders(project_root=ia, data_dir=data, zim_dir=None,
                                   python_executable=py)
    after = {str(p): p.stat().st_mtime_ns for p in tmp_path.rglob('*') if p.is_file()}
    assert before == after
    assert report['checked_without_changes'] is True
    assert report['host_homologated'] is False
    assert report['folders']['sqlite'] == str(db)
    assert report['memory_environment'] == 'desenvolvimento'
    assert 'interaction_library_reference' in {x['id'] for x in report['checks']}
    assert not {'runtime_python', 'external_venv', 'data_dir_external', 'sqlite_header'} & set(report['blocking'])
    assert report['status'] == ('paths_ok' if not report['warnings'] and not report['blocking'] else ('blocked' if report['blocking'] else 'partial'))
    assert set(report['blocking']) <= {'python_version'}  # The test host may use Python 3.13.


def test_missing_folders_report_blockers_and_never_create(tmp_path):
    ia = tmp_path / 'CAMPANARIO-IA'
    ia.mkdir()
    report = inspect_three_folders(project_root=ia, data_dir=tmp_path / 'other-data',
                                   zim_dir=tmp_path / 'other-zim',
                                   python_executable=tmp_path / 'other-python')
    assert report['status'] == 'blocked'
    assert {'project_root', 'python_repository', 'external_venv', 'database_repository',
            'data_dir_external', 'zim_dir'} <= set(report['blocking'])
    assert not (tmp_path / 'CAMPANARIO-DATABASE').exists()
    assert not (tmp_path / 'CAMPANARIO-PYTHON').exists()
    assert not (tmp_path / 'other-data').exists()


def test_no_trust_in_sqlite_filename_only(tmp_path):
    ia, py, data, db = _fixture(tmp_path)
    db.write_bytes(b'not a database')
    report = inspect_three_folders(project_root=ia, data_dir=data, zim_dir=None,
                                   python_executable=py)
    assert 'sqlite_header' in report['blocking']


@pytest.mark.asyncio
async def test_executor_denies_ungranted_scope_before_execution():
    calls = []

    @dataclass
    class SensitiveBrain:
        definition = BrainDefinition('sensitive', 'Sensivel', ('custom',), installed=True,
                                     permission_scopes=frozenset({'files:write'}))
        def health_check(self):
            return True, 'ok'
        def execute(self, request):
            calls.append('called')
            return BrainResult('sensitive', BrainStatus.COMPLETED, request.trace_id, 0,
                               operations=('files.write',))

    executor = BrainExecutor(BrainRegistry({'sensitive': SensitiveBrain()}))
    trace = uuid4()
    plan = BrainPlan(trace, 'custom', ('sensitive',), ('explicit',))
    req = BrainRequest(uuid4(), None, 'example', 'custom', trace_id=trace)
    out, = await executor.execute(plan, req)
    assert out.error == 'permission_denied'
    assert calls == []


@pytest.mark.asyncio
async def test_executor_rejects_forged_trace_and_evidence():
    @dataclass
    class ForgedBrain:
        definition = BrainDefinition('forged', 'Fraudado', ('custom',), installed=True)
        def health_check(self):
            return True, 'ok'
        def execute(self, request):
            return BrainResult('forged', BrainStatus.COMPLETED, uuid4(), 0,
                               operations=('library.retrieve',))

    executor = BrainExecutor(BrainRegistry({'forged': ForgedBrain()}))
    trace = uuid4()
    req = BrainRequest(uuid4(), None, 'consulta', 'custom', trace_id=trace)
    out, = await executor.execute(BrainPlan(trace, 'custom', ('forged',), ('test',)), req)
    assert out.status == BrainStatus.FAILED and out.error == 'invalid_brain_result'
    assert not out.evidence_refs and out.guard is None


def test_environment_api_accessible_when_brains_feature_disabled():
    from campanario.main import app
    client = TestClient(app)
    res = client.get('/api/v1/brains/environment')
    assert res.status_code == 200
    body = res.json()
    assert body['checked_without_changes'] is True
    assert body['host_homologated'] is False
    assert body['status'] in {'blocked', 'partial', 'paths_ok'}
    assert body['checks'] and 'folders' in body
    remote = TestClient(app, base_url='http://public.example.org')
    assert remote.get('/api/v1/brains/environment').status_code == 403


def test_interaction_reference_prefers_external_database_and_preserves_fallback(tmp_path, monkeypatch):
    from campanario.agents.interaction_library import _reference_db_path, DEFAULT_PATH
    from campanario.config import Settings
    data = tmp_path / 'dados'
    monkeypatch.setenv('CAMPANARIO_DATA_DIR', str(data))
    monkeypatch.delenv('CAMPANARIO_INTERACTION_DB', raising=False)
    assert _reference_db_path() == DEFAULT_PATH  # Existing installation is not broken.
    reference = data / 'reference' / 'interaction_library_v2.sqlite'
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b'SQLite format 3\x00')
    assert _reference_db_path() == reference
    monkeypatch.setenv('CAMPANARIO_INTERACTION_DB', str(tmp_path / 'explicit.sqlite'))
    assert _reference_db_path() == tmp_path / 'explicit.sqlite'
