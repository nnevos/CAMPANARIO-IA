"""Regressions for UTC timestamps and epistemic grounding."""
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from campanario.api import _session_payload, _utc_iso


def test_naive_sqlite_utc_is_serialized_with_explicit_offset():
    assert _utc_iso(datetime(2026, 10, 29, 18, 46)) == "2026-10-29T18:46:00+00:00"


def test_aware_timestamp_normalizes_to_utc():
    from datetime import timedelta, timezone
    value = datetime(2026, 10, 29, 15, 46, tzinfo=timezone(timedelta(hours=-3)))
    assert _utc_iso(value) == "2026-10-29T18:46:00+00:00"


def test_session_timestamps_have_utc_offset():
    now = datetime(2026, 10, 29, 18, 46)
    item = SimpleNamespace(id=uuid4(), title='test', status='active', created_at=now,
                           updated_at=now, primary_agent_id='morgana')
    assert _session_payload(item)['updated_at'].endswith('+00:00')


def test_browser_converts_legacy_naive_utc_and_session_times():
    html = (Path(__file__).resolve().parents[1] / 'src/campanario/web/index.html').read_text()
    html += "\n".join(f.read_text(encoding="utf-8") for f in sorted((Path(__file__).resolve().parents[1] / "src/campanario/web/static").glob("*")) if f.suffix in {".js", ".css"})
    assert "return new Date(value+'Z')" in html
    assert 'const parsed=parseCampanarioTime(createdAt)' in html
    assert 'const d=parseCampanarioTime(s.updated_at)' in html


def test_personal_answer_contract_preserves_unknown_state():
    source = (Path(__file__).resolve().parents[1] / 'src/campanario/chat/service.py').read_text()
    assert 'A ausencia de uma afirmacao' in source
    assert 'explicitamente negado e desconhecido' in source
