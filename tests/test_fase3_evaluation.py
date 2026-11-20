"""Tests for the Phase 3 benchmark itself, not tests that assert current Campanario bugs."""
import asyncio
import importlib.util
import json
import sqlite3
from pathlib import Path
import shutil
import socket
import sys
import tempfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'tools'/'eval_fase3.py'
spec=importlib.util.spec_from_file_location('eval_fase3_runner',MODULE)
runner=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=runner
spec.loader.exec_module(runner)


def test_versioned_manifest_and_counts():
    manifest,facts,docs,group=runner.validate_corpus()
    assert manifest['schema_version']=='1.0.0'
    assert (len(facts),len(docs),len(group))==(50,20,12)
    assert len({x['id'] for x in facts+docs+group})==82


def test_factual_categories_and_varied_phrasings():
    _,facts,_,_=runner.validate_corpus()
    categories={x['category'] for x in facts}
    assert categories=={'pessoa_conhecida','pessoa_menos_conhecida','homonimo',
                        'obra','conceito','nome_ficticio_inventado'}
    prompts=' '.join(x['question'].casefold() for x in facts)
    assert 'quem foi' in prompts and 'me fala' in prompts and 'conhece' in prompts
    assert all(x['no_source_rule']=='abstain_no_identity_claim' for x in facts)


def test_document_quotes_are_in_local_synthetic_fixtures():
    _,_,docs,_=runner.validate_corpus()
    assert len({x['document'] for x in docs})==5
    for d in docs:
        text=(runner.DATASET/'fixtures'/d['document']).read_text(encoding='utf-8')
        assert d['expected_quote'] in text
        assert d['lookup_term'] in d['expected_quote']


def test_manifest_catches_modified_dataset(monkeypatch,tmp_path):
    copy=tmp_path/'corpus'
    shutil.copytree(runner.DATASET,copy,ignore=shutil.ignore_patterns('baselines'))
    monkeypatch.setattr(runner,'DATASET',copy)
    (copy/'factual.jsonl').write_text('alterado\n',encoding='utf-8')
    with pytest.raises(ValueError,match='SHA-256 divergente'):
        runner.validate_corpus()


def test_offline_socket_guard_blocks_external_without_dialing():
    with runner.network_gate(True) as blocked:
        sock=socket.socket()
        try:
            with pytest.raises(OSError,match='FASE3_OFFLINE_NON_LOOPBACK_BLOCKED'):
                sock.connect(('203.0.113.10',80))
        finally:
            sock.close()
    assert len(blocked)==1


def test_offline_socket_guard_permits_localhost():
    server=socket.socket()
    try:
        server.bind(('127.0.0.1',0))
        server.listen(1)
        with runner.network_gate(True) as blocked:
            client=socket.socket()
            try:
                client.settimeout(1)
                client.connect(('127.0.0.1',server.getsockname()[1]))
                conn,_=server.accept()
                conn.close()
            finally:
                client.close()
        assert blocked==[]
    finally:
        server.close()


@pytest.mark.asyncio
async def test_probe_both_modes_use_isolated_fixture_db(tmp_path):
    _,facts,docs,group=runner.validate_corpus()
    # A temporary SQLite is created only below this directory.
    probe=await runner.run_probe('offline',facts,docs,group,tmp_path,ROOT)
    assert probe['model_accuracy']=='not_measured'
    assert len(probe['factual_turns'])==50
    assert len(probe['document_turns'])==20
    assert probe['summary']['docs_search_exact_excerpts']==20
    assert len(probe['group_dispositions'])==12
    assert probe['summary']['docs_source_in_model_context']==0
    assert (tmp_path/'isolated_utilities'/'utilidades.sqlite3').exists()


@pytest.mark.asyncio
async def test_no_public_web_calls_in_probe_online(tmp_path):
    _,facts,docs,group=runner.validate_corpus()
    with runner.network_gate(True) as blocked:
        data=await runner.run_probe('online',facts,docs,group,tmp_path,ROOT)
    assert blocked==[]
    injected=[x for x in data['group_dispositions'] if x['id']=='G010'][0]
    assert injected['status']=='injected_failure_probe_executed'
    assert injected['real_mid_stream_drop']=='not_tested'


@pytest.mark.asyncio
async def test_live_mode_rejects_non_local_ollama_address():
    status,models=await runner.check_ollama('https://example.com:11434','qwen3.5:9b')
    assert status=='invalid_endpoint_non_loopback'
    assert models==[]


def test_abstention_regex_is_only_heuristic():
    assert runner.ABSTENTION.search('Não encontrei uma fonte adequada.')
    assert not runner.ABSTENTION.search('Ada Lovelace foi matemática.')
    assert not runner.ABSTENTION.search(runner.FAKE_TEXT)


def test_intent_negative_controls_are_versioned():
    manifest,_,_,_=runner.validate_corpus()
    rows=runner.jsonl(runner.DATASET/'intent_negatives.jsonl')
    assert manifest['negative_intent_cases']==15
    assert len(rows)==15
    assert all(x['expected']=='no_external_fact_lookup' for x in rows)


def test_evaluator_sqlite_handles_close_explicitly(tmp_path):
    runner.add_project_path(ROOT)
    util = runner.isolated_utilities(tmp_path/'isolated_utilities')
    held = util.connect()
    assert held.execute('SELECT 1').fetchone()[0] == 1
    util.close()
    with pytest.raises(sqlite3.ProgrammingError, match='closed database'):
        held.execute('SELECT 1')
    # Idempotent, including after a partially completed evaluation.
    util.close()
