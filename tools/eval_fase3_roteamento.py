#!/usr/bin/env python3
"""Optional LOCAL Ollama tool-calling intent comparison (zero external services).

Evaluates 50 positive factual queries and 15 negative social queries. This is an
experimental model/tool-call probe, NOT a patch to Campanario's core.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
from time import perf_counter
from urllib.parse import urlsplit

DATA=Path(__file__).resolve().parent.parent/'eval'/'v1'
TOOLS=[{'type':'function','function':{
    'name':'consultar_conhecimento_local',
    'description':'Consulta fontes locais verificáveis antes de responder uma pergunta factual; não acessa internet.',
    'parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}}]


def jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def args_cli():
    p=argparse.ArgumentParser(description='Comparador tool-calling de decisão factual (apenas Ollama local)')
    p.add_argument('--model',action='append',default=None,help='Repita para comparar modelos')
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434')
    p.add_argument('--max-cases',type=int,default=None)
    p.add_argument('--timeout',type=float,default=90)
    p.add_argument('--report-dir',type=Path,default=Path('reports')/'fase3')
    return p.parse_args()


async def compare(args):
    import httpx
    parsed=urlsplit(args.ollama_url)
    if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1','::1'):
        raise SystemExit('Apenas endpoints Ollama em loopback são permitidos')
    facts=jsonl(DATA/'factual.jsonl')
    negatives=jsonl(DATA/'intent_negatives.jsonl')
    rows=[(x,True) for x in facts]+[(x,False) for x in negatives]
    if args.max_cases is not None:
        rows=[(x,True) for x in facts[:args.max_cases]] + [(x,False) for x in negatives[:args.max_cases]]
    args.report_dir.mkdir(parents=True,exist_ok=True)
    for model in args.model or ['qwen3.5:9b','gemma3:12b']:
        status='executed';results=[]
        try:
            async with httpx.AsyncClient(timeout=args.timeout,trust_env=False) as client:
                ping=await client.get(args.ollama_url.rstrip('/')+'/api/tags',timeout=3)
                ping.raise_for_status()
                installed=[x.get('name') for x in ping.json().get('models',[])]
                if model not in installed:
                    status='not_executed_model_not_installed'
                else:
                    for case,positive in rows:
                        start=perf_counter()
                        try:
                            response=await client.post(args.ollama_url.rstrip('/')+'/api/chat',json={
                                'model':model,'stream':False,'think':False,
                                'messages':[
                                  {'role':'system','content':(
                                   'Você decide SOMENTE se a pergunta exige consultar uma base factual. '
                                   'Se for pergunta factual sobre pessoas, obras ou conceitos, chame a função '
                                   'consultar_conhecimento_local. Se for conversa social ou ajuda cotidiana '
                                   'sem fato externo, responda OK sem usar ferramentas. '
                                   'Nunca invente uma resposta factual nem acesse a web.')},
                                  {'role':'user','content':case['question']}],
                                'tools':TOOLS, 'options':{'temperature':0,'num_predict':100,'num_ctx':4096}
                            })
                            response.raise_for_status()
                            output=response.json()
                            calls=output.get('message',{}).get('tool_calls',[])
                            invoked=any(x.get('function',{}).get('name')=='consultar_conhecimento_local'
                                        for x in calls if isinstance(x,dict))
                            results.append({'id':case['id'],'expected_consult':positive,
                                'consulted':invoked,'time_ms':round((perf_counter()-start)*1000,2),
                                'status':'ok'})
                        except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
                            status='incomplete_error'
                            results.append({'id':case['id'],'expected_consult':positive,
                                'status':'error','error_type':type(exc).__name__})
                            if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code in (400,404):
                                status='unsupported_or_bad_model_api'
                                break
        except (httpx.HTTPError,ValueError,TypeError) as exc:
            status='not_executed_'+type(exc).__name__
        usable=[r for r in results if r['status']=='ok']
        counts={'TP':sum(r['expected_consult'] and r['consulted'] for r in usable),
                'FN':sum(r['expected_consult'] and not r['consulted'] for r in usable),
                'FP':sum(not r['expected_consult'] and r['consulted'] for r in usable),
                'TN':sum(not r['expected_consult'] and not r['consulted'] for r in usable)}
        elapsed=[r['time_ms'] for r in usable]
        result={'schema_version':'1.0.0','created_at':datetime.now(timezone.utc).isoformat(),
                'model':model,'status':status,'cases_requested':len(rows),'cases_executed':len(usable),
                'confusion':counts if status=='executed' and len(usable)==len(rows) else None,
                'p50_decision_ms':statistics.median(elapsed) if elapsed else None,
                'vram_peak_mb':'not_measured',
                'note':'Comparação isolada do tool-calling; não mede correção dos fatos nem biblioteca.',
                'results':results}
        dest=args.report_dir/f'baseline_toolcall_{model.replace(":","_").replace("/","_")}.json'
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(model,status,'testados',len(usable),'de',len(rows),'=>',dest)


if __name__=='__main__':
    asyncio.run(compare(args_cli()))
