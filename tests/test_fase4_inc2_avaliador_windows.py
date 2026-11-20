"""Regression tests for temporary SQLite handles in Fase 4 inc.2 evaluator.

The tests use only isolated files in pytest's temporary directory. The evaluator
is not allowed to access the user's local databases or public internet.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from eval_fase4_inc2 import _TemporaryUtilityService, evaluate
from campanario.utilities.service import UtilityService


def test_evaluator_sqlite_handle_closed_after_success(tmp_path):
    service = _TemporaryUtilityService(tmp_path / 'isolated_utilities')
    with service.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM documents').fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db.execute('SELECT 1')
    # Keep the Python connection object alive: this must also work on Windows.
    service.db.unlink()
    assert not service.db.exists()
    assert _TemporaryUtilityService.connect is not UtilityService.connect


def test_evaluator_sqlite_handle_closed_and_rolled_back_after_failure(tmp_path):
    service = _TemporaryUtilityService(tmp_path / 'isolated_utilities')
    with pytest.raises(RuntimeError, match='intentional'):
        with service.connect() as db:
            db.execute("INSERT INTO records VALUES ('test', 'item', '{}', 'now', 'now')")
            raise RuntimeError('intentional failure')
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db.execute('SELECT 1')
    with service.connect() as db2:
        assert db2.execute("SELECT COUNT(*) FROM records WHERE id='item'").fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db2.execute('SELECT 1')
    service.db.unlink()


def test_entire_fase4_inc2_evaluator_completes_and_cleans_tempdb():
    # In particular, exiting TemporaryDirectory must succeed on Windows.
    result = asyncio.run(evaluate())
    assert result['documents_total'] == 20
    assert result['documents_in_immutable_source_ledger'] == 20
    assert result['documents_cited_by_chat'] == 20
    assert result['model_calls_for_document_answers'] == 0
    assert result['temporary_sqlite_unchanged_by_reader'] is True
    assert result['user_sqlite_accessed'] is False
