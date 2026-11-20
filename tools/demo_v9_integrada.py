"""Reproducible offline V9 + V9.1 demonstration using invented test data.

Does NOT validate any rules of the actual Ordem Paranormal book and does not
contact Ollama or access any installed/user databases.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from campanario.brains import BrainExecutor, BrainRequest, BrainRegistry, CapabilityRouter
from campanario.brains.builds import AgentBuild, select_talents
from campanario.brains.store import BuildStore
from campanario.chat.document_intent import DocumentRequest
from campanario.chat.fact_sheet import build_turn_fact_sheet
from campanario.chat.canonical_answer import build_canonical
from campanario.chat.grounded_expression import validate_expression
from campanario.storage.database import Base, build_session_factory
from campanario.storage import models  # noqa
from sqlalchemy import create_engine
from campanario.utilities.service import UtilityService


async def run_demo() -> dict:
    with tempfile.TemporaryDirectory(prefix='campanario-v9-demo-') as tmp:
        util = UtilityService(Path(tmp) / 'utilidades')
        reference = util.roots[0] / 'Ordem Paranormal — FICÇÃO DE TESTE.md'
        reference.write_text('# Exemplo de teste\n\n## Ocultista 20% de NEX\n\n'
                             'No exercício fictício, Ocultista recebe Marca Exemplo B2.\n', encoding='utf-8')
        imported = util.run('library.import', {'path': str(reference), 'confirm': True})
        assert imported['status'] == 'success', imported
        csv = util.roots[0] / 'faturamento.csv'
        csv.write_text('produto,faturamento\nA,100\nB,200\n', encoding='utf8')
        assert util.run('library.import', {'path': str(csv), 'confirm': True})['status'] == 'success'
        engine = create_engine(f'sqlite:///{Path(tmp) / "chat.db"}')
        Base.metadata.create_all(engine)
        store = BuildStore(build_session_factory(engine))
        store.save(AgentBuild(agent_id='morgana', mode='archetype',
                              primary_archetype='oraculo', talents=('leitura_profunda',)))
        store.save(AgentBuild(agent_id='todd', mode='archetype',
                              primary_archetype='investigador', talents=('olhar_investigativo',)))
        executor = BrainExecutor(BrainRegistry.local(util.db), audit=store.record_run)
        router = CapabilityRouter()

        question = 'O que Ocultista ganha em 20% de NEX?'
        plan = router.plan(question, document_request=DocumentRequest(question, 'Ordem Paranormal'))
        request = BrainRequest(uuid4(), None, question, plan.intent,
                               document_hint='Ordem Paranormal', trace_id=plan.trace_id)
        start = perf_counter()
        doc_run, = await executor.execute(plan, request)
        doc_ms = round((perf_counter() - start)*1000, 2)
        sheet = build_turn_fact_sheet(request.request_id, question, doc_run.guard, fact_lookup_requested=True)
        answer = build_canonical(sheet, doc_run.guard, brain_ids=('knowledge',))
        assert doc_run.evidence_refs and answer.sources and answer.brain_ids
        altered = validate_expression(answer, 'O Ocultista recebe 999 poderes irreais.')

        question2 = 'Calcule o faturamento total desta planilha.'
        plan2 = router.plan(question2)
        request2 = BrainRequest(uuid4(), None, question2, plan2.intent, trace_id=plan2.trace_id)
        start = perf_counter()
        data_run, = await executor.execute(plan2, request2)
        data_ms = round((perf_counter() - start)*1000, 2)
        sheet2 = build_turn_fact_sheet(request2.request_id, question2, data_run.guard, fact_lookup_requested=True)
        answer2 = build_canonical(sheet2, data_run.guard, brain_ids=('analysis',))
        assert data_run.guard and '300' in data_run.guard.verified_answer
        assert not validate_expression(answer2, 'O total calculado é 900.').accepted
        return {
            'dataset': 'FICTICIO — marcas e números criados somente para testar o software',
            'model_invoked': False,
            'knowledge': {'status': answer.status.value, 'brain': doc_run.public(),
                          'source_file': doc_run.evidence_refs[0].title,
                          'page': doc_run.evidence_refs[0].page,
                          'excerpt': doc_run.evidence_refs[0].excerpt,
                          'canonical_answer': answer.canonical_answer,
                          'hallucination_rejected': not altered.accepted,
                          'measured_wall_ms': doc_ms},
            'analysis': {'status': answer2.status.value, 'brain': data_run.public(),
                         'canonical_answer': answer2.canonical_answer,
                         'measured_wall_ms': data_ms},
            'builds': {agent: {'primary': store.get(agent).primary_archetype,
                               'active_talents': [t.id for t in select_talents(
                                   store.get(agent), intent='document_lookup', text=question)]}
                       for agent in ('morgana', 'todd')},
            'recorded_runs': store.runs(),
            'caveat': 'Sem Ollama real, arquivo real de Ordem Paranormal, nem Windows/mobile físico.',
        }


if __name__ == '__main__':
    print(json.dumps(asyncio.run(run_demo()), indent=2, ensure_ascii=False))
