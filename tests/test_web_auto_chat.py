"""Normal-chat web selection, real execution wiring, failures and offline opt-out."""
from uuid import uuid4
import pytest

from campanario.chat.service import ChatService
from campanario.model.protocol import FakeModelProvider
from campanario.utilities.web_intent import direct_decision, decide


@pytest.mark.asyncio
async def test_explicit_request_without_slash():
    x=await decide('Morgana, pesquise os melhores modelos de IA atuais',None,'')
    assert x.search and x.reason=='pedido_explicito'
    x=await decide('Todd, quem ganhou ontem a corrida?',None,'')
    assert x.search and x.reason=='dado_potencialmente_atual'


@pytest.mark.asyncio
async def test_model_can_request_search_for_uncertain_information():
    model=FakeModelProvider('{"search":true,"query":"comparação atual modelos 16 GB VRAM"}')
    d=await decide('Quais modelos de IA são recomendados para meu computador?',model,'fake-model')
    assert d.search and d.reason=='modelo_solicitou' and 'VRAM' in d.query


@pytest.mark.asyncio
async def test_model_can_decline_and_invalid_output_is_not_executed():
    no=await decide('O que é o teorema de Pitágoras?',FakeModelProvider('{"search":false,"query":""}'),'model')
    bad=await decide('O que muda entre duas plataformas?',FakeModelProvider('execute python now'),'model')
    assert not no.search and not bad.search


@pytest.mark.asyncio
async def test_offline_conversation_and_prohibition_take_priority():
    assert not (await decide('Não pesquise na internet, responda usando seu conhecimento.',
                             FakeModelProvider('{"search":true,"query":"x"}'),'model')).search
    assert not (await decide('Olá!',FakeModelProvider('{"search":true,"query":"x"}'),'model')).search


@pytest.mark.asyncio
async def test_normal_chat_retrieves_sources_before_agent_for_both_types(monkeypatch):
    from campanario.utilities import web_chat
    fetched=[]; passed=[]
    def web(query):
        fetched.append(query)
        return 'FONTE REAL: https://docs.example.org'
    monkeypatch.setattr(web_chat,'research_note',web)
    class Stub:
        _web_auto_search=True
        _web_planner_provider=FakeModelProvider('{"search":true,"query":"documentação oficial sobre baterias"}')
        _default_model='model'
        _telemetry=None
        async def _stream_turn_impl(self,session,text,**kwargs):
            passed.append(kwargs.get('turn_system_note'))
            if False:yield None
    stub=Stub()
    async for _ in ChatService.stream_turn(stub,uuid4(),'Morgana, como funcionam baterias LiFePO4?'):pass
    async for _ in ChatService.stream_turn(stub,uuid4(),'Todd, pesquise as notícias recentes'):pass
    assert len(fetched)==2
    assert all('FONTE REAL' in note for note in passed)


@pytest.mark.asyncio
async def test_no_web_when_opted_out_or_no_reason(monkeypatch):
    from campanario.utilities import web_chat
    monkeypatch.setattr(web_chat,'research_note',lambda q: (_ for _ in ()).throw(AssertionError('network should not run')))
    class Stub:
        _web_auto_search=False
        _web_planner_provider=None
        _default_model=''
        _telemetry=None
        async def _stream_turn_impl(self,session,text,**kwargs):
            assert kwargs.get('turn_system_note') is None
            if False:yield None
    async for _ in ChatService.stream_turn(Stub(),uuid4(),'Qual a previsão para amanhã?'):pass


@pytest.mark.asyncio
async def test_search_failure_is_passed_as_failure_not_fake_evidence(monkeypatch):
    from campanario.utilities import web_chat
    monkeypatch.setattr(web_chat,'research_note',lambda q:'PESQUISA WEB NÃO REALIZADA. Falha real: offline; não invente fontes')
    class Stub:
        _web_auto_search=True
        _web_planner_provider=None
        _default_model=''
        _telemetry=None
        async def _stream_turn_impl(self,session,text,**kwargs):
            assert 'NÃO REALIZADA' in kwargs['turn_system_note']
            if False:yield None
    async for _ in ChatService.stream_turn(Stub(),uuid4(),'Pesquise sobre fontes confiáveis'):pass
