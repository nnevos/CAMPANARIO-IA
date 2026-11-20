"""Regression tests for phase 4 inc.1 evaluator's SQLite cleanup on Windows.

These exercise only temporary test databases; no production files or Ollama.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from eval_fase4_inc1 import _TemporaryUtilityService, evaluate
from campanario.utilities.service import UtilityService


def test_inc1_evaluator_closes_connection_after_success(tmp_path):
    util = _TemporaryUtilityService(tmp_path / 'isolated')
    with util.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM documents').fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db.execute('SELECT 1')
    # The reference to `db` remains live: unlink must still work on Windows.
    util.db.unlink()
    assert not util.db.exists()
    assert _TemporaryUtilityService.connect is not UtilityService.connect


def test_inc1_evaluator_closes_connection_and_rolls_back_on_error(tmp_path):
    util = _TemporaryUtilityService(tmp_path / 'isolated')
    with pytest.raises(RuntimeError, match='intentional'):
        with util.connect() as db:
            db.execute("INSERT INTO records VALUES ('note', 'one', '{}', 'now', 'now')")
            raise RuntimeError('intentional')
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db.execute('SELECT 1')
    with util.connect() as db2:
        assert db2.execute("SELECT COUNT(*) FROM records WHERE id='one'").fetchone()[0] == 0
    util.db.unlink()


def test_inc1_evaluator_runs_all_cases_with_temporary_sqlite_cleanup():
    # This runs the real test evaluator, not the application database.
    result = asyncio.run(evaluate())
    assert result['documents_cases'] == 20
    assert result['exact_quotes_and_citations'] == 20
    assert result['model_calls_for_document_answers'] == 0
    assert result['user_database_accessed'] is False
