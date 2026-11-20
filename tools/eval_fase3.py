#!/usr/bin/env python3
"""Baseline Fase 3 - non-invasive evaluation of the Campanario core.

One-command evaluation of versioned corpus in offline AND online modes.
Without an available local Ollama this is a *structural probe*, NEVER a model benchmark.
Only sandbox directories from tempfile are written. The user's Campanario DBs are not read.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import socket
import statistics
import sys
import tempfile
from time import perf_counter
from typing import Any
from unittest.mock import patch

DATASET = Path(__file__).resolve().parent.parent / 'eval' / 'v1'
FAKE_TEXT = '__EVAL_STUB__NAO_E_RESPOSTA_DO_MODELO__'
ABSTENTION = re.compile(r"\b(n[aã]o sei|n[aã]o consegui|n[aã]o consigo|n[aã]o encontrei|"
                      r"n[aã]o tenho (?:fontes?|informa[cç][aã]o|evid[eê]ncia)|"
                      r"n[aã]o posso confirmar|sem fontes?|fora (?:da|de) minha base)\b", re.I)


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def validate_corpus() -> tuple[dict[str, Any], list, list, list]:
    manifest = json.loads((DATASET/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        got = hashlib.sha256((DATASET/name).read_bytes()).hexdigest()
        if got != expected:
            raise ValueError(f'Corpus alterado: {name} (SHA-256 divergente)')
    facts, docs, group = (jsonl(DATASET/f) for f in ('factual.jsonl', 'documentos.jsonl', 'grupo.jsonl'))
    if (len(facts), len(docs), len(group)) != (50, 20, 12):
        raise ValueError('Contagem do corpus v1 incorreta')
    negatives=jsonl(DATASET/'intent_negatives.jsonl')
    if len(negatives)!=15: raise ValueError('Corpus de negativos deve ter 15 itens')
    all_ids = [x['id'] for x in facts + docs + group + negatives]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError('IDs duplicados')
    for doc in docs:
        content = (DATASET/'fixtures'/doc['document']).read_text(encoding='utf-8')
        if doc['expected_quote'] not in content or doc['lookup_term'] not in doc['expected_quote']:
            raise ValueError(f'Gabarito nao corresponde ao arquivo: {doc["id"]}')
    return manifest, facts, docs, group


def add_project_path(project_root: Path) -> None:
    package = project_root/'src'/'campanario'
    if not package.exists():
        raise FileNotFoundError(f'Nao foi encontrado src/campanario em {project_root}')
    sys.path.insert(0, str(project_root/'src'))


@contextmanager
def network_gate(offline: bool):
    """Block non-loopback TCP sockets in-process. NOT proof of OS-level egress isolation."""
    attempted: list[str] = []
    if not offline:
        yield attempted
        return
    original_connect, original_connect_ex = socket.socket.connect, socket.socket.connect_ex
    def is_loopback(sock, address):
        if sock.family == socket.AF_UNIX:
            return True
        if not isinstance(address, tuple) or not address:
            return False
        host = address[0]
        if host == 'localhost':
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except (ValueError, TypeError):
            return False
    def checked_connect(sock, address):
        if not is_loopback(sock, address):
            attempted.append(repr(address))
            raise OSError('FASE3_OFFLINE_NON_LOOPBACK_BLOCKED')
        return original_connect(sock, address)
    def checked_connect_ex(sock, address):
        if not is_loopback(sock, address):
            attempted.append(repr(address))
            return 101
        return original_connect_ex(sock, address)
    with patch.object(socket.socket, 'connect', checked_connect), \
         patch.object(socket.socket, 'connect_ex', checked_connect_ex):
        yield attempted


class Sessions:
    def __init__(self):
        self.items = {}
    def create(self, session):
        self.items[session.id] = session
        return session
    def get(self, key):
        return self.items.get(key)
    def list(self):
        return list(self.items.values())
    def delete(self, key):
        return self.items.pop(key, None) is not None
    def set_primary_agent(self, session_id, agent_id):
        value = self.items.get(session_id)
        if value is None:
            return None
        new = replace(value, primary_agent_id=agent_id)
        self.items[session_id] = new
        return new


class Messages:
    def __init__(self):
        self.items = []
    def append(self, msg):
        self.items.append(msg)
        return msg
    def list_by_session(self, session_id):
        return [x for x in self.items if x.session_id == session_id]


class ProbeProvider:
    """Instrumented stub. No model intelligence is claimed or scored."""
    def __init__(self, response: str = FAKE_TEXT):
        self.response = response
        self.requests = []
    async def health(self):
        return True
    async def stream(self, request):
        from campanario.model.protocol import ModelChunk
        self.requests.append(request)
        yield ModelChunk(text=self.response)
        yield ModelChunk(text='', done=True)


def make_chat(provider, model='stub', registry=None, web=False):
    from campanario.chat.service import ChatService
    from campanario.chat.context import RecentMessagesContextManager
    return ChatService(Sessions(), Messages(), provider, RecentMessagesContextManager(20),
                       model, agent_registry=registry, low_latency_mode=True,
                       live_streaming=False, web_auto_search=web,
                       participation_provider=None, experience=None)


async def turn(chat, question, *, agent_id=None, independent=False, session=None):
    session = session or chat.create_session(agent_id=agent_id)
    start = perf_counter()
    first_ms = None
    chunks, speakers = [], []
    try:
        async for ev in chat.stream_turn(session.id, question, independent_group_turn=independent):
            if ev.type == 'speaker_start':
                speakers.append(ev.agent_id)
            if ev.type == 'token':
                if first_ms is None:
                    first_ms = round((perf_counter()-start)*1000, 2)
                chunks.append((ev.agent_id,ev.text))
        return {'status':'completed', 'speakers':speakers,
                'text_by_speaker':{s:''.join(x for a,x in chunks if a==s) for s in speakers},
                'first_visible_ms':first_ms,'total_ms':round((perf_counter()-start)*1000,2),
                'session':session}
    except Exception as exc:
        return {'status':'exception','error_type':type(exc).__name__,
                'error_message':str(exc)[:250], 'speakers':speakers,
                'first_visible_ms':first_ms,'total_ms':round((perf_counter()-start)*1000,2),
                'session':session}


def public_turn(out):
    """Strip session object and never serialize private/free-form answers by default."""
    return {k:v for k,v in out.items() if k not in ('session','text_by_speaker')}


def probe_intent(facts):
    from campanario.utilities.web_intent import direct_decision
    outcomes = []
    for case in facts:
        dec = direct_decision(case['question'])
        outcomes.append({'id':case['id'],'category':case['category'],
                         'regex_would_search':bool(dec and dec.search),
                         'actual_subject':None if dec is None else dec.subject})
    negatives = jsonl(DATASET/'intent_negatives.jsonl')
    negative_rows=[]
    for case in negatives:
        dec=direct_decision(case['question'])
        negative_rows.append({'id':case['id'],'regex_would_search':bool(dec and dec.search)})
    tp=sum(x['regex_would_search'] for x in outcomes)
    fp=sum(x['regex_would_search'] for x in negative_rows)
    return {'cases':outcomes,'negative_cases':negative_rows,'regex_coverage':tp,
            'regex_confusion':{'TP':tp,'FN':len(facts)-tp,'FP':fp,'TN':len(negatives)-fp},
            'always_local':{'status':'design_simulation_not_integrated',
                'confusion_if_all_turns_consulted':{'TP':len(facts),'FN':0,'FP':len(negatives),'TN':0}},
            'tool_calling':{'status':'not_executed_requires_local_model_and_native_tool_interface'}}


def isolated_utilities(base: Path):
    """Own/close every evaluator SQLite handle before Windows temp cleanup.

    sqlite3.Connection.__exit__ commits or rolls back but does NOT close the
    connection. Holding and explicitly closing evaluation-only handles avoids
    WinError 32 in TemporaryDirectory on Windows without changing the core.
    """
    from campanario.utilities.service import UtilityService

    class EvaluationUtilityService(UtilityService):
        def __init__(self, path):
            self._eval_connections = []
            super().__init__(path)

        def connect(self):
            connection = super().connect()
            self._eval_connections.append(connection)
            return connection

        def close(self):
            try:
                for connection in reversed(self._eval_connections):
                    connection.close()
            finally:
                self._eval_connections.clear()

    return EvaluationUtilityService(base)


async def run_probe(mode, facts, docs, group, sandbox, project_root):
    from campanario.utilities import integration
    from campanario.agents.profiles import AgentRegistry, default_agent_registry
    util = isolated_utilities(sandbox/'isolated_utilities')
    imported = {}
    for name in sorted({c['document'] for c in docs}):
        target = util.roots[0]/name
        target.write_bytes((DATASET/'fixtures'/name).read_bytes())
        item = util.run('library.import',{'path':str(target),'confirm':True,'category':'evaluation_fixture'})
        imported[name] = item['status'] == 'success' and item['result'].get('imported') is True
    # Use a test-only utility service for every library or web tool call.
    previous_service = integration.service
    integration.service = lambda *args, **kwargs: util
    try:
        factual = probe_intent(facts)
        lib_rows = []
        for case in docs:
            found = util.run('library.search',{'query':case['lookup_term']})
            candidates = found.get('result',{}).get('documents',[])
            matching = [d for d in candidates if d['name']==case['document']
                        and any(case['expected_quote'] in m['excerpt'] for m in d.get('matches',[]))]
            provider = ProbeProvider()
            response = await turn(make_chat(provider),case['question'])
            context_text = '\n'.join(m.content for req in provider.requests for m in req.messages)
            lib_rows.append({'id':case['id'],'document':case['document'],
                'imported_fixture':imported[case['document']],
                'library_exact_excerpt_retrievable':bool(matching),
                'source_quote_in_model_prompt':case['expected_quote'] in context_text,
                'chat_status':response['status'],
                'response_model':'stub_not_evaluated'})
        factual_rows = []
        for case in facts:
            provider = ProbeProvider()
            response = await turn(make_chat(provider),case['question'])
            texts = list(response.get('text_by_speaker',{}).values())
            emitted = ''.join(texts)
            factual_rows.append({'id':case['id'],'category':case['category'],
                'chat_status':response['status'],
                'provider_called':bool(provider.requests),
                'abstained_in_rule_path':bool(ABSTENTION.search(emitted)) and FAKE_TEXT not in emitted,
                'raw_model_factual_accuracy':'not_measured_stub'})
        group_rows=[]
        probes={x['category']:x for x in group}
        for category in ('dois_agentes_fato','dois_agentes_inexistente','um_agente','todd_cotidiano'):
            scenario=probes[category]
            response=await turn(make_chat(ProbeProvider()),scenario['question'],independent=True)
            group_rows.append({'id':scenario['id'],'category':category,**public_turn(response),
                'expected_two':category.startswith('dois_agentes'),
                'speaker_count_ok':len(response['speakers'])==(2 if category.startswith('dois_agentes') else 1),
                'semantic_quality':'not_measured_stub'})
        # Do not treat an agent reply as source; measure whether the next model prompt
        # is contaminated by the first (with and without independent_group_turn).
        for independent in (False,True):
            provider=ProbeProvider('FATO_INVENTADO_DO_AGENTE_ALFA')
            r=await turn(make_chat(provider), 'Morgana e Todd, opinem sobre planejamento semanal.',
                         independent=independent)
            second = '\n'.join(m.content for m in provider.requests[1].messages) if len(provider.requests)>1 else ''
            group_rows.append({'id':'P_HISTORY_ISOLATED' if independent else 'P_HISTORY_DEFAULT',
                'status':r['status'], 'speaker_count':len(r['speakers']),
                'first_agent_unverified_text_in_second_prompt':'FATO_INVENTADO_DO_AGENTE_ALFA' in second,
                'independent_group_turn':independent,
                'note':'Prompt contamination is NOT proof of belief adoption.'})
        registry=default_agent_registry()
        template=registry.list()[0]
        third=replace(template,id='terceiro_eval',name='Terceiro de Teste',is_default=False)
        three=AgentRegistry((*registry.list(),third),default_id=registry.default_id)
        third_out=await turn(make_chat(ProbeProvider(),registry=three),'Terceiro, olá!',agent_id=third.id)
        group_rows.append({'id':'P_THIRD_PROFILE','status':third_out['status'],
                           'error_type':third_out.get('error_type'),
                           'in_memory_profile_supported':third_out['status']=='completed',
                           'file_only_profile_supported':'not_tested_no_profile_file_loader',
                           'note':'In-memory registry is stronger than file-only loader; if this fails, file-only cannot work.'})
        neutral=make_chat(ProbeProvider()).create_session(agent_id=None)
        group_rows.append({'id':'P_NO_AGENT','chat_without_agent_supported':neutral.primary_agent_id is None,
                           'actual_primary':neutral.primary_agent_id,
                           'library_without_agent_supported':all(imported.values())})
        # Simulated loss of the network at retrieval, only inside this subprocess.
        if mode=='online':
            import campanario.utilities.web_chat as web_chat
            old_research=web_chat.research_entity
            def broken_network(*_args,**_kwargs):
                raise OSError('NETWORK_DOWN_TEST_INJECTION')
            web_chat.research_entity=broken_network
            try:
                response=await turn(make_chat(ProbeProvider(),web=True),'Morgana e Todd, quem foi Ada Lovelace?',independent=True)
            finally:
                web_chat.research_entity=old_research
            group_rows.append({'id':'P_NETWORK_DOWN','status':response['status'],
                'speakers':response['speakers'],'exception_type':response.get('error_type'),
                'injection':'research_entity_raises_OSError_before_response',
                'note':'Not a real mid-stream disconnection.'})
        # Coverage accounting: all 12 scenarios have an explicit disposition.
        outcome_by_id={x['id']:x for x in group_rows if x.get('id','').startswith('G')}
        history_default=next(x for x in group_rows if x['id']=='P_HISTORY_DEFAULT')
        history_independent=next(x for x in group_rows if x['id']=='P_HISTORY_ISOLATED')
        third_probe=next(x for x in group_rows if x['id']=='P_THIRD_PROFILE')
        neutral_probe=next(x for x in group_rows if x['id']=='P_NO_AGENT')
        dispositions=[]
        for scenario in group:
            category=scenario['category']
            if scenario['id'] in outcome_by_id:
                item={'id':scenario['id'],'status':'machine_probe_executed',
                      'observed':outcome_by_id[scenario['id']],
                      'semantic_score':'not_measured_stub'}
            elif category=='erro_agente':
                item={'id':scenario['id'],'status':'machine_probe_executed',
                      'default_second_context_contains_unverified_first_reply':history_default['first_agent_unverified_text_in_second_prompt'],
                      'independent_second_context_contains_unverified_first_reply':history_independent['first_agent_unverified_text_in_second_prompt'],
                      'second_agent_believed_claim':'not_measured_stub'}
            elif category=='sem_agente':
                item={'id':scenario['id'],'status':'machine_probe_executed',
                      'neutral_chat_supported':neutral_probe['chat_without_agent_supported'],
                      'neutral_library_supported':neutral_probe['library_without_agent_supported']}
            elif category=='terceiro_agente':
                item={'id':scenario['id'],'status':'machine_probe_executed',
                      'in_memory_third_profile_supported':third_probe['in_memory_profile_supported'],
                      'file_only_profile_supported':'not_implemented_or_not_exercisable'}
            elif category=='queda_rede' and mode=='online':
                r=next(x for x in group_rows if x['id']=='P_NETWORK_DOWN')
                item={'id':scenario['id'],'status':'injected_failure_probe_executed',
                      'turn_completed':r['status']=='completed',
                      'real_mid_stream_drop':'not_tested'}
            elif category=='troca_persona':
                item={'id':scenario['id'],'status':'structural_gap',
                      'shared_factsheet_available':False,
                      'persona_factual_consistency':'not_measured_stub'}
            elif category=='correcao_usuario':
                item={'id':scenario['id'],'status':'pending_real_multi_turn_semantics',
                      'reason':'Independent correction to BOTH speakers requires meaningful model outputs.'}
            elif category=='divergencia_sem_consenso':
                item={'id':scenario['id'],'status':'pending_real_semantic_review',
                      'reason':'Synthetic provider does not generate opinions.'}
            elif category=='latencia_comparada':
                item={'id':scenario['id'],'status':'pending_real_model_latency',
                      'reason':'Stub millisecond values cannot represent real LLM latency.'}
            else:
                item={'id':scenario['id'],'status':'pending',
                      'reason':'Case needs a real local model or network-drop environment.'}
            dispositions.append(item)
        return {'evaluation_engine':'probe_instrumented_stub', 'model_accuracy':'not_measured','group_dispositions':dispositions,
             'factual_intent':factual,'factual_turns':factual_rows,
             'document_turns':lib_rows,'group_turns':group_rows,
             'summary':{'factual_cases':len(factual_rows),'docs_cases':len(lib_rows),
                 'docs_search_exact_excerpts':sum(x['library_exact_excerpt_retrievable'] for x in lib_rows),
                 'docs_source_in_model_context':sum(x['source_quote_in_model_prompt'] for x in lib_rows),
                 'regex_search_triggered':factual['regex_coverage'],
                 'factual_guard_abstentions':sum(x['abstained_in_rule_path'] for x in factual_rows),
                 'group_cases_from_dataset':len(group),
                 'group_scenarios_automated':len([x for x in group_rows if x['id'].startswith('G')]),
                 'group_scenarios_not_automated':sum(x['status'].startswith('pending') for x in dispositions),
                 'group_scenarios_with_machine_evidence':sum(x['status'] in ('machine_probe_executed','injected_failure_probe_executed','structural_gap') for x in dispositions)}}
    finally:
        integration.service=previous_service
        util.close()


async def check_ollama(url, model):
    """Never download models. Only inspect already-installed loopback Ollama."""
    import httpx
    from urllib.parse import urlsplit
    parsed=urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost','::1'):
        return 'invalid_endpoint_non_loopback', []
    try:
        async with httpx.AsyncClient(timeout=3,trust_env=False) as client:
            res=await client.get(url.rstrip('/')+'/api/tags')
            res.raise_for_status()
            names=[x.get('name','') for x in res.json().get('models',[]) if isinstance(x,dict)]
            if model not in names:
                return 'model_not_installed',names
            return 'ready', names
    except (httpx.HTTPError, ValueError,KeyError) as exc:
        return f'ollama_unavailable_{type(exc).__name__}', []


async def run_real(mode, model, facts, docs, group, tempdir, allow_web, url, max_cases, timeout, include_responses):
    # The model is local, but web lookup in ONLINE mode requires an explicit flag.
    status, models=await check_ollama(url,model)
    if status!='ready':
        return {'evaluation_engine':'ollama','model':model,'status':'not_executed',
                'reason':status,'detected_model_names':models,
                'metric_values':None,'model_outputs':'not_available'}
    from campanario.model.adapters.ollama import OllamaProvider
    from campanario.utilities import integration
    import campanario.utilities.web_chat as web_chat
    util=isolated_utilities(tempdir/'real_utilities')
    for p in (DATASET/'fixtures').glob('*.md'):
        local=util.roots[0]/p.name;local.write_bytes(p.read_bytes())
        util.run('library.import',{'path':str(local),'confirm':True,'category':'fixture'})
    # In ONLINE mode avoid accessing real utility data or introducing new cached sources.
    original = integration.service
    integration.service=lambda *args,**kwargs:util
    try:
        provider=OllamaProvider(url,timeout_seconds=timeout, context_window=4096,
                                temperature=0.0,max_output_tokens=450,think=False)
        web=mode=='online' and allow_web
        fact_rows=[];doc_rows=[];group_rows=[]
        selected_facts=facts if max_cases is None else facts[:max_cases]
        selected_docs=docs if max_cases is None else docs[:max_cases]
        for case in selected_facts:
            r=await turn(make_chat(provider,model,web=web),case['question'])
            text=' '.join(r.get('text_by_speaker',{}).values())
            fact_rows.append({'id':case['id'],**public_turn(r),
              'abstention_detected':bool(ABSTENTION.search(text)),
              'has_http_citation':bool(re.search(r'https?://\S+',text)),
              'claim_grounding_verified':False,
              'ground_truth_review':'pending_manual_review',
              'invention_count':'not_measurable_by_regex_without_evidence',
              'response_sha256':hashlib.sha256(text.encode()).hexdigest(),
              **({'response_text':text} if include_responses else {})})
        for case in selected_docs:
            r=await turn(make_chat(provider,model,web=web),case['question'])
            text=' '.join(r.get('text_by_speaker',{}).values())
            doc_rows.append({'id':case['id'],**public_turn(r),
              'expected_document_mentioned':case['document'].casefold() in text.casefold(),
              'expected_quote_exact':case['expected_quote'].casefold() in text.casefold(),
              'document_citation_verified':False,
              'ground_truth_review':'pending_manual_review',
              'response_sha256':hashlib.sha256(text.encode()).hexdigest(),
              **({'response_text':text} if include_responses else {})})
        for category in ('dois_agentes_fato','dois_agentes_inexistente','um_agente','todd_cotidiano'):
            case=next(x for x in group if x['category']==category)
            r=await turn(make_chat(provider,model,web=web),case['question'],independent=True)
            group_rows.append({'id':case['id'],**public_turn(r),
               'perspective_distinction':'pending_manual_review',
               'factual_consistency':'not_evaluable_without_shared_factsheet'})
        firsts=[x['first_visible_ms'] for x in fact_rows+doc_rows+group_rows if x.get('first_visible_ms') is not None]
        return {'evaluation_engine':'ollama','model':model,'status':'executed',
            'external_web_authorized':web,'case_count':len(fact_rows)+len(doc_rows)+len(group_rows),
            'factual':fact_rows,'documents':doc_rows,'group':group_rows,
            'summary':{'first_visible_p50_ms':statistics.median(firsts) if firsts else None,
            'first_visible_p95_ms':sorted(firsts)[int((len(firsts)-1)*.95)] if firsts else None,
            'known_inventions_confirmed':'not_scored_requires_claim_source_annotation',
            'source_correctness':'not_scored_requires_citation_review',
            'gpu_vram_peak_mb':'not_measured',
            'notes':('Response texts saved for manual review; claims and sources remain unscored.'
                     if include_responses else
                     'No response texts saved; only hashes and structural metrics. Sources must be manually checked.')}}
    finally:
        integration.service=original
        util.close()


async def mode_eval(mode,args,facts,docs,group,manifest):
    is_offline=mode=='offline'
    # Even in online-probe mode, no external internet is needed or permitted.
    block_outbound=is_offline or args.engine=='probe' or not args.allow_web
    with tempfile.TemporaryDirectory(prefix=f'campanario_fase3_{mode}_') as temp:
        with network_gate(block_outbound) as blocked_attempts:
            if args.engine=='probe':
                execution=await run_probe(mode,facts,docs,group,Path(temp),args.project_root)
            else:
                execution=await run_real(mode,args.model,facts,docs,group,Path(temp),
                                         args.allow_web,args.ollama_url,args.max_cases,args.timeout,
                                         args.include_responses)
        return {'schema_version':'1.0.0','mode':mode,'engine':args.engine,
            'timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'project_root_omitted_for_privacy':True,
            'dataset_version':manifest['schema_version'],
            'dataset_hash_sha256':hashlib.sha256((DATASET/'manifest.json').read_bytes()).hexdigest(),
            'python':platform.python_version(),'platform':platform.platform(),
            'model':args.model if args.engine=='ollama' else None,
            'internet_opt_in':bool(mode=='online' and args.allow_web),
            'network_guard_in_process':block_outbound,
            'blocked_external_socket_attempts':blocked_attempts,
            'isolation':'temporary_test_data_no_user_sqlite',
            'execution':execution}


def parse_args():
    p=argparse.ArgumentParser(description='Fase 3 do Campanario - baseline, nao altera nucleo')
    p.add_argument('--mode', choices=('offline','online','both'), default='both')
    p.add_argument('--engine',choices=('probe','ollama'),default='probe',
                   help='probe testa fluxos com stub; ollama executa geracao REAL local')
    p.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--model',default='qwen3.5:9b')
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434')
    p.add_argument('--allow-web',action='store_true',
                   help='opt-in explicito; SOMENTE em online+ollama, nunca no offline')
    p.add_argument('--max-cases',type=int,default=None,
                   help='amostra por classe para smoke test real; omitido = conjunto completo')
    p.add_argument('--timeout',type=float,default=120.0)
    p.add_argument('--include-responses',action='store_true',
                   help='Salvar texto de respostas reais no relatorio para revisao humana')
    p.add_argument('--report-dir',type=Path,default=Path('reports')/'fase3')
    return p.parse_args()


async def main():
    args=parse_args()
    if args.max_cases is not None and args.max_cases<1:
        raise SystemExit('--max-cases deve ser >= 1')
    if args.mode=='offline' and args.allow_web:
        raise SystemExit('Offline e --allow-web sao incompativeis')
    if args.allow_web and args.engine!='ollama':
        raise SystemExit('Use --allow-web somente com --engine ollama')
    manifest,facts,docs,group=validate_corpus()
    add_project_path(args.project_root.resolve())
    modes=('offline','online') if args.mode=='both' else (args.mode,)
    args.report_dir.mkdir(parents=True,exist_ok=True)
    for mode in modes:
        outcome=await mode_eval(mode,args,facts,docs,group,manifest)
        suffix=args.model.replace(':','_').replace('/','_') if args.engine=='ollama' else 'stub'
        output=args.report_dir/f'baseline_{mode}_{args.engine}_{suffix}.json'
        output.write_text(json.dumps(outcome,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
        summary=outcome['execution'].get('summary',{})
        print(f'{mode.upper()}: {outcome["execution"].get("status","probe_executed")}; '
              f'engine={args.engine}; {summary}; relatório={output}')
        if outcome['blocked_external_socket_attempts']:
            print('ATENCAO: tentativas de conexao externa bloqueadas:',outcome['blocked_external_socket_attempts'])
    print('Observacao: resultados com stub NAO sao notas de factualidade/precisao do Qwen/Gemma.')


if __name__=='__main__':
    asyncio.run(main())
