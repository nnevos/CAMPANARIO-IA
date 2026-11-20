#!/usr/bin/env python3
"""Fase 4 Inc.3B.1: literal answerability, factual guard and regression.

Only five synthetic Markdown documents in a fresh, temporary SQLite file.
No Ollama, persistent embeddings, internet, or user databases are accessed.
A document assertion is not a verified external fact.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import socket
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

from campanario.chat.context import RecentMessagesContextManager
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.models import MessageRole
from campanario.chat.service import ChatService
from campanario.model.protocol import ModelChunk
from eval_fase4_inc1 import _TemporaryUtilityService, evaluate as evaluate_original_chat
from eval_fase4_inc3 import VARIATIONS
from eval_fase4_inc3b_calibracao import HARD_NEGATIVES


class Sessions:
    def __init__(self):
        self.rows = {}

    def create(self, row):
        self.rows[row.id] = row
        return row

    def get(self, key):
        return self.rows.get(key)

    def set_primary_agent(self, key, agent_id):
        self.rows[key] = replace(self.rows[key], primary_agent_id=agent_id)
        return self.rows[key]

    def list(self):
        return list(self.rows.values())


class Messages:
    def __init__(self):
        self.rows = []

    def append(self, row):
        self.rows.append(row)
        return row

    def list_by_session(self, key):
        return [row for row in self.rows if row.session_id == key]


class GuardProvider:
    def __init__(self):
        self.calls = 0

    async def health(self):
        return True

    async def stream(self, request):
        self.calls += 1
        yield ModelChunk(text='HALLUCINATION_CANARY_NEVER_SHOULD_APPEAR')
        yield ModelChunk(text='', done=True)


async def evaluate() -> dict:
    source_root = ROOT / 'eval' / 'v1'
    cases = [json.loads(line) for line in (source_root / 'documentos.jsonl').read_text(
        encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 20 or len(HARD_NEGATIVES) != 12:
        raise ValueError('Corpus incompleto; avaliação interrompida')
    with TemporaryDirectory(prefix='campanario_inc3b1_') as folder:
        util = _TemporaryUtilityService(Path(folder) / 'util')
        for filename in sorted({case['document'] for case in cases}):
            source = source_root / 'fixtures' / filename
            target = util.roots[0] / filename
            target.write_bytes(source.read_bytes())
            if util.run('library.import', {'path': str(target), 'confirm': True})['status'] != 'success':
                raise RuntimeError('Falha importando ' + filename)
        before = sha256(util.db.read_bytes()).hexdigest()
        reader = ReadOnlyLocalLibrary(util.db)
        docs = []
        variants = []
        negatives = []
        provider = GuardProvider()
        chat = ChatService(Sessions(), Messages(), provider,
                           RecentMessagesContextManager(10), 'stub',
                           local_library=reader, low_latency_mode=True, grounded_synthesis=False,
                           web_auto_search=False)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
            for case in cases:
                hit = reader.search(case['question'])
                sheet = build_turn_fact_sheet(uuid4(), case['question'], hit,
                                              fact_lookup_requested=True)
                docs.append({
                    'id': case['id'],
                    'correct_cited_quote': bool(hit and sheet.status == 'supported' and
                        hit.quote.name == case['document'] and
                        case['expected_quote'] in hit.quote.excerpt),
                })
            for case_id, question, filename, fragment in VARIATIONS:
                hit = reader.search(question)
                variants.append({'id': case_id,
                                 'correct_cited_quote': bool(hit and
                                     hit.quote.name == filename and fragment in hit.quote.excerpt)})
            for case_id, question, subject in HARD_NEGATIVES:
                hit = reader.search(question, subject=subject)
                session = chat.create_session()
                events = [ev async for ev in chat.stream_turn(session.id, question)]
                answer = ''.join(ev.text for ev in events if ev.type == 'token')
                negatives.append({
                    'id': case_id,
                    'no_cited_claim': hit is None,
                    'chat_abstained': 'Não encontrei na biblioteca local' in answer and
                        'Fonte:' not in answer and
                        'HALLUCINATION_CANARY_NEVER_SHOULD_APPEAR' not in answer,
                })
        unchanged = sha256(util.db.read_bytes()).hexdigest() == before
        reader._discard_index()
    original_chat = await evaluate_original_chat()
    return {
        'stage': 'fase4_inc3b1_suficiencia_extrativa',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'dataset_sha256': sha256((source_root/'documentos.jsonl').read_bytes()).hexdigest(),
        'uses_user_sqlite': False, 'internet_attempts': 'blocked',
        'user_memories_accessed': False, 'ollama_called': False,
        'temporary_sqlite_byte_identical': unchanged,
        'documents': {'correct': sum(x['correct_cited_quote'] for x in docs),
                      'total': len(docs), 'cases': docs},
        'variants': {'correct': sum(x['correct_cited_quote'] for x in variants),
                     'total': len(variants), 'cases': variants},
        'hard_negatives': {'no_cited_claim': sum(x['no_cited_claim'] for x in negatives),
                           'chat_abstained': sum(x['chat_abstained'] for x in negatives),
                           'total': len(negatives), 'cases': negatives},
        'legacy_chat': {'correct_quote_and_citation': original_chat['exact_quotes_and_citations'],
                        'total': original_chat['documents_cases'],
                        'model_stub_calls': original_chat['model_calls_for_document_answers']},
        'hard_negative_model_stub_calls': provider.calls,
        'semantic_entailment': 'NOT_MEASURED',
        'external_truth': 'NOT_MEASURED',
        'semantic_embedding_model': 'NOT_USED',
        'known_limitations': ('A gate checks explicit attribute and topic; cannot prove logical entailment. '
                              'Semantic candidates remain non-factual; Kiwix pending.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default='reports/fase4_inc3b1/baseline_suficiencia.json')
    args = parser.parse_args()
    result = asyncio.run(evaluate())
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    d, v, n, c = (result[k] for k in ('documents', 'variants', 'hard_negatives', 'legacy_chat'))
    print(f'3B.1: documentos={d["correct"]}/{d["total"]}; '
          f'variacoes={v["correct"]}/{v["total"]}; '
          f'negativos_sem_citacao={n["no_cited_claim"]}/{n["total"]}; '
          f'chat_absteve={n["chat_abstained"]}/{n["total"]}; '
          f'chat_documental={c["correct_quote_and_citation"]}/{c["total"]}; '
          f'modelo_simulado={result["hard_negative_model_stub_calls"]}; relatorio={target}')
    if not (d['correct'] == 20 and v['correct'] == 6 and
            n['no_cited_claim'] == n['chat_abstained'] == 12 and
            c['correct_quote_and_citation'] == 20 and
            c['model_stub_calls'] == result['hard_negative_model_stub_calls'] == 0 and
            result['temporary_sqlite_byte_identical']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
