"""Web module regression tests. No calls to the live internet."""
import json
from pathlib import Path
import socket

import pytest
import httpx
from fastapi.testclient import TestClient
from campanario.utilities.service import UtilityService, OPERATIONS, WRITE
from campanario.utilities import web_research as web


@pytest.fixture
def service(tmp_path):
    return UtilityService(tmp_path / 'local')


def test_registry_and_no_automatic_network(service):
    assert set(('web.search','web.read','web.research','web.save','web.history')) <= set(OPERATIONS)
    assert 'web.save' in WRITE
    assert service.run('web.history',{})['result']['sources']==[]


def test_prevents_internal_urls(service):
    for url in ['http://127.0.0.1/private','http://169.254.169.254/latest/meta-data/',
                'http://localhost:8000','file:///etc/passwd','http://user:pw@example.com/',
                'http://10.10.0.5/','http://192.168.1.1:8080/']:
        result=service.run('web.read',{'url':url})
        assert result['status']=='failed',url
    assert service.run('web.save',{'source_id':'missing','confirm':True})['status']=='failed'
    assert service.run('web.save',{'source_id':'missing'})['status']=='failed'


def test_extraction_saved_with_provenance_and_searchable_offline(monkeypatch,service):
    def mock_get(url,**kwargs):
        return '<html><head><title>Manual técnico</title></head><body><main><h1>Eletrônica básica</h1><p>O texto do documento fala sobre voltagem e corrente elétrica.</p></main><script>ignore this</script></body></html>'
    monkeypatch.setattr(web,'public_url',lambda url:url)
    monkeypatch.setattr(web,'request',mock_get)
    loaded=service.run('web.read',{'url':'https://docs.example.org/manual'})
    assert loaded['status']=='success'
    doc=loaded['result']
    assert doc['url']=='https://docs.example.org/manual'
    assert 'voltagem' in doc['content']
    assert 'ignore this' not in doc['content']
    assert len(service.run('web.history',{})['result']['sources'])==1
    saved=service.run('web.save',{'source_id':doc['source_id'],'confirm':True})
    assert saved['status']=='success' and saved['result']['saved']
    result=service.run('library.search',{'query':'voltagem'})['result']
    assert len(result['documents'])==1
    assert doc['url'] in Path(saved['result']['workspace_file']).read_text()
    service2=UtilityService(service.base)
    assert len(service2.run('library.search',{'query':'voltagem'})['result']['documents'])==1
    assert len(service2.run('web.history',{})['result']['sources'])==1


def test_search_brave_json_and_provenance(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_BRAVE_API_KEY','demo-fake-test-key')
    monkeypatch.delenv('CAMPANARIO_SEARXNG_URL',raising=False)
    monkeypatch.setattr(web,'request', lambda *a,**k: json.dumps({'web':{'results':[
        {'title':'Documentação Python','url':'https://docs.python.org/3/','description':'Guia oficial'},
        {'title':'Duplicate','url':'https://docs.python.org/3/','description':''},
    ]}}))
    result=web.search_results('Python docs',limit=5)
    assert result['provider']=='Brave Search API'
    assert result['count']==1 and result['results'][0]['snippet']=='Guia oficial'


def test_search_searx_requires_local_service(monkeypatch):
    monkeypatch.delenv('CAMPANARIO_BRAVE_API_KEY',raising=False)
    monkeypatch.setenv('CAMPANARIO_SEARXNG_URL','https://example.com/search')
    with pytest.raises(ValueError,match='máquina local'):
        web.search_results('termo')


def test_search_fallback_html(monkeypatch):
    monkeypatch.delenv('CAMPANARIO_BRAVE_API_KEY',raising=False)
    monkeypatch.delenv('CAMPANARIO_SEARXNG_URL',raising=False)
    page='<div><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fpython.org%2F">Python site</a></div>'
    monkeypatch.setattr(web,'request',lambda *a,**k:page)
    monkeypatch.setattr(web,'public_url',lambda url:url)
    found=web.search_results('Python')
    assert found['count']==1 and found['results'][0]['url']=='https://python.org/'


def test_url_rejects_private_dns_resolution(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(None,None,None,None,('10.0.0.3',443))])
    with pytest.raises(PermissionError):web.public_url('https://malicious.example/')
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(None,None,None,None,('8.8.8.8',443))])
    assert web.public_url('https://public.example/path#fragment')=='https://public.example/path'


def test_lookup_api_catalog_and_actual_failure(tmp_path,monkeypatch):
    from campanario.utilities import api
    from campanario.main import app
    util=UtilityService(tmp_path/'api_data')
    monkeypatch.setattr(api,'service',lambda:util)
    with TestClient(app) as client:
        cat=client.get('/api/v1/utilities/catalog')
        assert cat.status_code==200
        assert any(c['id']=='web.search' and not c['offline'] for c in cat.json())
        r=client.post('/api/v1/utilities/invoke',json={'tool':'web.read','arguments':{'url':'http://127.0.0.1/'}})
        assert r.status_code==200 and r.json()['status']=='failed'
        assert client.get('/ferramentas').status_code==200
        assert 'Pesquisa Web' in client.get('/ferramentas.js').text


def test_tool_does_not_follow_redirect_or_read_binary(monkeypatch):
    monkeypatch.setattr(web,'public_url',lambda url:url)
    transport=httpx.MockTransport(lambda req:httpx.Response(302,headers={'location':'http://127.0.0.1/private'}))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(PermissionError,match='Redirecionamento'):
            web.request('https://example.com/',client=client)
    transport=httpx.MockTransport(lambda req:httpx.Response(200,headers={'content-type':'application/octet-stream'},content=b'evil'))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError,match='texto'):
            web.request('https://example.com/',client=client)


def test_explicit_chat_research_note_records_real_sources_and_failure(monkeypatch,service):
    from campanario.utilities import web_chat
    monkeypatch.setattr('campanario.utilities.integration.service',lambda:service)
    monkeypatch.setattr(web,'search_results',lambda q,limit=4:{'results':[{'title':'Python Docs','url':'https://python.org/','snippet':'Documentação real'}], 'provider':'Test provider'})
    monkeypatch.setattr(web,'public_url',lambda url:url)
    monkeypatch.setattr(web,'request',lambda url,**k:'<html><title>Python Docs</title><p>Documentação técnica do Python e sua linguagem.</p></html>')
    note=web_chat.research_note('Python documentação')
    assert 'PÁGINA LIDA' in note
    assert 'https://python.org/' in note
    assert 'Documentação técnica do Python' in note
    assert len(service.run('web.history',{})['result']['sources'])==1
    monkeypatch.setattr(web,'search_results',lambda q,limit=4: (_ for _ in ()).throw(ConnectionError('sem rede')))
    failed=web_chat.research_note('pesquisa sem conexão')
    assert 'NÃO REALIZADA' in failed and 'sem rede' in failed


def test_deep_research_reads_sources_with_partial_failures(monkeypatch,service):
    monkeypatch.setattr(web,'search_results',lambda q,limit=5:{'query':q,'provider':'mock','results':[
        {'title':'Fonte A','url':'https://example.org/a','snippet':''},
        {'title':'Fonte B','url':'https://example.org/b','snippet':''}], 'count':2})
    monkeypatch.setattr(web,'public_url',lambda url:url)
    def fake_page(url):
        if url.endswith('/b'):raise ConnectionError('site indisponível')
        return '<html><title>Fonte A</title><p>Documento original com informações verificáveis.</p></html>'
    monkeypatch.setattr(web,'request',fake_page)
    result=service.run('web.research',{'query':'documentação'})
    assert result['status']=='success'
    assert result['result']['partial'] is True
    assert [x['status'] for x in result['result']['sources']]==['read','unavailable']
    assert len(service.run('web.history',{})['result']['sources'])==1


@pytest.mark.asyncio
async def test_explicit_chat_command_calls_retrieval_without_changing_other_chat(monkeypatch):
    from uuid import uuid4
    from campanario.chat.service import ChatService
    from campanario.utilities import web_chat
    captured=[]
    monkeypatch.setattr(web_chat,'research_note',lambda query: 'CONFIRMADO: '+query)
    class Stub:
        _telemetry=None
        async def _stream_turn_impl(self,session,text,**kwargs):
            captured.append((text,kwargs.get('turn_system_note')))
            if False:yield None
    stub=Stub()
    async for _ in ChatService.stream_turn(stub,uuid4(),'/pesquisar vida em marte'):pass
    async for _ in ChatService.stream_turn(stub,uuid4(),'olá'):pass
    assert captured[0][1]=='CONFIRMADO: vida em marte'
    assert captured[1][1] is None
