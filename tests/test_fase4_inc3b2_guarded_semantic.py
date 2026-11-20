"""Inc.3B.2: source sufficiency gates vector candidates before chat exposure."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest

from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.semantic_library import HybridLocalLibrary
from test_fase4_inc1_biblioteca import _ask, _chat, CountingProvider
from test_fase4_inc3b_semantic import source  # noqa: F401 (pytest fixture)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from eval_fase4_inc3b import FixtureEmbeddings, PARAPHRASES
from eval_fase4_inc3b2 import GUARDED_POSITIVES, run
from eval_fase4_inc3b_calibracao import HARD_NEGATIVES


@pytest.mark.parametrize('case_id,question,subject,name,expected', GUARDED_POSITIVES)
def test_lexical_miss_can_be_semantic_candidate_only_with_explicit_attribute(
        source, case_id, question, subject, name, expected):
    original = ReadOnlyLocalLibrary(source.db)
    assert original.search(question, subject=subject) is None, case_id
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings(),
                                min_similarity=.50)
    suggestion = reader.search(question, subject=subject)
    assert suggestion is not None and suggestion.status == 'semantic_candidate', case_id
    assert suggestion.quote.name == name and expected in suggestion.quote.excerpt
    assert reader.last_semantic_status == 'candidate_only'
    sheet = build_turn_fact_sheet(uuid4(), question, suggestion, fact_lookup_requested=True)
    assert sheet.status == 'insufficient' and len(sheet.sources) == 1
    assert sheet.origin == 'library' and not sheet.claims and not sheet.evidence_available
    assert 'NAO confirmei' in suggestion.verified_answer
    reader._discard_index()
    original._discard_index()


@pytest.mark.parametrize('case_id,question,subject', HARD_NEGATIVES)
def test_same_subject_missing_attribute_cannot_be_displayed(source,case_id,question,subject):
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    hit=reader.search(question,subject=subject)
    assert hit is None, case_id
    assert reader.last_semantic_status in {'rejected_insufficient_evidence', 'no_safe_candidate'}
    sheet=build_turn_fact_sheet(uuid4(), question, hit, fact_lookup_requested=True)
    assert sheet.status=='insufficient' and sheet.origin=='none'
    assert not sheet.sources and not sheet.claims and sheet.extractive_answer is None
    reader._discard_index()


@pytest.mark.parametrize('case_id,question,subject,name,expected', PARAPHRASES)
def test_synonym_without_explicit_evidence_cannot_be_shown(source,case_id,question,subject,name,expected):
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    assert reader.search(question,subject=subject) is None, case_id
    assert reader.last_semantic_rejected > 0
    assert reader.last_semantic_status == 'rejected_insufficient_evidence'
    reader._discard_index()


@pytest.mark.asyncio
async def test_chat_can_show_unconfirmed_candidate_without_model_generation(source):
    provider=CountingProvider()
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    _,question,_,name,expected=GUARDED_POSITIVES[0]
    chat,_=_chat(reader,provider)
    events,messages=await _ask(chat,question)
    answer=messages[-1].content
    assert 'NAO confirmei' in answer and 'nao comprova' in answer
    assert name in answer and expected in answer
    assert provider.calls==0
    reader._discard_index()


@pytest.mark.asyncio
async def test_chat_hard_negative_abstains_without_model_generation(source):
    provider=CountingProvider()
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    chat,_=_chat(reader,provider)
    _events,messages=await _ask(chat,HARD_NEGATIVES[0][1])
    answer=messages[-1].content
    assert 'Não encontrei na biblioteca local' in answer
    assert 'Fonte' not in answer and 'HALLUCINATION' not in answer
    assert provider.calls==0
    reader._discard_index()


@pytest.mark.asyncio
async def test_two_agents_share_one_guarded_candidate(source):
    provider=CountingProvider()
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    chat,_=_chat(reader,provider)
    _,question,_,name,expected=GUARDED_POSITIVES[0]
    events,history=await _ask(chat,'Morgana e Todd, '+question,group=True)
    answers=[m.content for m in history if m.agent_id]
    assert [e.agent_id for e in events if e.type=='speaker_start']==['morgana','todd']
    assert len(answers)==2 and answers[0]==answers[1]
    assert all(name in a and expected in a and 'NAO confirmei' in a for a in answers)
    assert reader.semantic_build_count==1 and provider.calls==0
    reader._discard_index()


def test_evaluator_does_not_modify_synthetic_sqlite_and_preserves_fts5():
    report=run(engine='fixture',min_similarity=.50)
    assert report['user_sqlite_accessed'] is False
    assert report['internet_authorized'] is False
    assert report['temporary_sqlite_unchanged'] is True
    assert report['original_documents_grounded']==20
    assert report['fts5_variations_grounded']==6
    assert report['raw_synonym_queries']['correct_top']==5
    assert report['raw_synonym_queries']['shown_to_user']==0
    assert report['explicit_answerable_queries']['lexical_misses']==5
    assert report['explicit_answerable_queries']['correct_cited_candidates']==5
    assert report['explicit_answerable_queries']['not_promoted']==5
    assert report['hard_same_topic_negatives']['without_citation']==12
    assert report['hard_same_topic_negatives']['without_fact_claim']==12
    assert report['semantic_entailment']=='NOT_MEASURED'


def test_evaluator_process_frees_sqlite_for_windows(tmp_path):
    path=tmp_path/'inc3b2_report.json'
    result=subprocess.run([
        sys.executable,str(ROOT/'tools/eval_fase4_inc3b2.py'),
        '--engine','fixture','--report',str(path),
    ],cwd=ROOT,text=True,capture_output=True,timeout=60)
    assert result.returncode==0, result.stdout+'\n'+result.stderr
    assert 'negativos_sem_trecho=12/12' in result.stdout
    assert path.is_file()
    report=json.loads(path.read_text(encoding='utf-8'))
    assert report['temporary_sqlite_unchanged']


def test_semantic_index_is_ram_only_and_source_database_unchanged(source):
    before=sha256(source.db.read_bytes()).digest()
    reader=HybridLocalLibrary(source.db,embeddings=FixtureEmbeddings(),min_similarity=.50)
    for _id,q,subject,_name,_fragment in GUARDED_POSITIVES:
        reader.search(q,subject=subject)
    assert sha256(source.db.read_bytes()).digest()==before
    assert reader.semantic_build_count==1
    reader._discard_index()


@pytest.mark.asyncio
@pytest.mark.parametrize('case_id,question,subject', HARD_NEGATIVES)
async def test_all_hard_negatives_reach_chat_as_abstention(source, case_id, question, subject):
    # These same-topic prompts used to expose misleading semantic suggestions
    # when cosine alone selected a passage. Each must now fail closed in chat.
    provider = CountingProvider()
    reader = HybridLocalLibrary(source.db, embeddings=FixtureEmbeddings(),
                                min_similarity=.50)
    chat, _ = _chat(reader, provider)
    _events, messages = await _ask(chat, question)
    answer = messages[-1].content
    assert 'Não encontrei na biblioteca local' in answer, case_id
    assert 'Fonte' not in answer and 'HALLUCINATION' not in answer, case_id
    assert provider.calls == 0, case_id
    reader._discard_index()
