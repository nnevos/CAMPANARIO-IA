"""Calibrate only candidates; hard same-topic negatives never become supported facts."""
from pathlib import Path
import subprocess
import sys

from campanario.config import Settings
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.semantic_library import HybridLocalLibrary

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from eval_fase4_inc3b_calibracao import HARD_NEGATIVES, THRESHOLDS, run
from eval_fase4_inc3b import FixtureEmbeddings
from eval_fase4_inc1 import _TemporaryUtilityService
from uuid import uuid4


def test_hard_negatives_are_same_topic_and_not_answered_by_fixtures():
    assert len(HARD_NEGATIVES) >= 10
    docs = '\n'.join(p.read_text(encoding='utf-8').casefold()
                     for p in (ROOT/'eval/v1/fixtures').glob('*.md'))
    assert all(subject.casefold() in docs for _, _, subject in HARD_NEGATIVES)
    assert all('?' in question for _, question, _ in HARD_NEGATIVES)
    assert len({subject for _, _, subject in HARD_NEGATIVES})>=4


def test_default_semantic_stays_disabled_and_threshold_not_lowered():
    config=Settings(_env_file=None)
    assert config.library_semantic_enabled is False
    assert config.library_semantic_min_similarity == 0.72
    assert THRESHOLDS==(0.72,0.50)


def test_calibration_reuses_synthetic_db_without_changing_it():
    result=run(engine='fixture')
    assert result['user_sqlite_accessed'] is False
    assert result['internet_authorized'] is False
    assert result['temp_sqlite_unchanged'] is True
    assert result['config_changed'] is False
    assert len(result['cases']) == 5 + len(HARD_NEGATIVES)
    assert result['semantic_entailment']=='NOT_MEASURED'
    # Expect some same-topic misleading candidates, revealing the weakness of
    # a threshold-only acceptance rule. Fixture performance is NOT model accuracy.
    assert result['summary']['0.5']['hard_negative_cases_with_accepted_candidate']>0
    assert result['summary']['0.5']['positive_expected_top_accepted']==5
    # Inc.3B.1 prevents lexical topical matches from becoming cited facts.
    assert result['summary']['0.5']['lexical_hard_negative_quote_present']==0
    assert 'DO NOT auto-enable' in result['recommendation']


def test_candidate_from_hard_negative_never_verified_by_semantic_similarity(tmp_path):
    util=_TemporaryUtilityService(tmp_path/'util')
    for f in (ROOT/'eval/v1/fixtures').glob('*.md'):
        target=util.roots[0]/f.name
        target.write_bytes(f.read_bytes())
        assert util.run('library.import', {'path':str(target),'confirm':True})['status']=='success'
    reader=HybridLocalLibrary(util.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    # Force a semantic pass without lexical retrieval: the insufficient excerpt
    # must now be rejected BEFORE being exposed, even as a candidate.
    from unittest.mock import patch
    from campanario.chat.local_library import ReadOnlyLocalLibrary
    question,subject=HARD_NEGATIVES[0][1:]
    with patch.object(ReadOnlyLocalLibrary,'search',return_value=None):
        suggestion=reader.search(question,subject=subject)
    assert suggestion is None
    assert reader.last_semantic_status == 'rejected_insufficient_evidence'
    sheet=build_turn_fact_sheet(uuid4(),question,suggestion,fact_lookup_requested=True)
    assert sheet.status=='insufficient' and not sheet.claims and not sheet.sources
    reader._discard_index()


def test_calibration_cli_cleanup_is_safe_for_windows(tmp_path):
    target=tmp_path/'calibracao.json'
    result=subprocess.run([sys.executable,str(ROOT/'tools/eval_fase4_inc3b_calibracao.py'),
                           '--engine','fixture','--report',str(target)],
                          cwd=ROOT,capture_output=True,text=True,timeout=45)
    assert result.returncode==0,result.stderr+'\n'+result.stdout
    assert target.is_file()
