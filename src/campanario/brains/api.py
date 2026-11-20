"""Loopback-only V9 brain control, Forja and safe declarative packages."""
from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from campanario.app.security import require_local
from campanario.bootstrap import get_runtime
from campanario.brains import BrainRegistry, BrainRequest, BrainExecutor, CapabilityRouter, ResourceBudget
from campanario.brains.builds import AgentBuild, ARCHETYPES, TALENTS, select_talents
from campanario.brains.package import export_package, import_package
from campanario.brains.store import BuildConflict
from campanario.config import get_settings
from campanario.chat.document_intent import DocumentRequest

router = APIRouter(prefix='/api/v1/brains', dependencies=[Depends(require_local)], tags=['V9 brains'])


@router.get('/environment')
def environment_preflight():
    """R0 read-only checks, also available while the V9 flag is disabled."""
    from campanario.brains.environment import inspect_current_environment
    # Settings() avoids get_settings()'s mkdir side effect on this diagnostic path.
    from campanario.config import Settings
    return inspect_current_environment(Settings())


def _service():
    if not get_settings().brains_v9_enabled:
        raise HTTPException(409, 'Arquitetura V9 desativada. Ative CAMPANARIO_BRAINS_V9_ENABLED.')
    service = get_runtime().conversation
    if getattr(service, '_brain_executor', None) is None:
        raise HTTPException(503, 'Cérebros não inicializados')
    return service


def _known_agent(service, agent_id: str):
    if agent_id not in {p.id for p in service.list_agents()}:
        raise HTTPException(404, 'Agente não registrado')


@router.get('/catalog')
def catalog():
    settings = get_settings()
    if not settings.brains_v9_enabled:
        return {'enabled': False, 'brains': [], 'archetypes': ARCHETYPES,
                'talents': [t.model_dump() for t in TALENTS.values()]}
    service = _service()
    return {'enabled': True,
            'brains': service._brain_executor.registry.catalog(),
            'archetypes': ARCHETYPES,
            'talents': [t.model_dump() for t in TALENTS.values()],
            'agents': [{'id': p.id, 'name': p.name} for p in service.list_agents()]}


@router.get('/runs')
def runs(limit: int = 30):
    try:
        return {'items': _service()._build_store.runs(limit)}
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Migração 0010 pendente') from exc


@router.get('/builds/{agent_id}')
def get_build(agent_id: str):
    service = _service()
    _known_agent(service, agent_id)
    try:
        return service._build_store.get(agent_id)
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Migração 0010 pendente') from exc


class BuildUpdate(BaseModel):
    build: AgentBuild
    expected_revision: int | None = Field(default=None, ge=1)


@router.put('/builds/{agent_id}')
def save_build(agent_id: str, body: BuildUpdate):
    service = _service()
    _known_agent(service, agent_id)
    if body.build.agent_id != agent_id:
        raise HTTPException(422, 'Identificador da ficha não corresponde ao agente')
    try:
        return service._build_store.save(body.build, expected_revision=body.expected_revision)
    except BuildConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Migração 0010 pendente') from exc


@router.post('/agents', status_code=201)
def create_agent(build: AgentBuild):
    service = _service()
    if build.agent_id in {p.id for p in service.list_agents()}:
        raise HTTPException(409, 'ID de agente já registrado')
    from campanario.brains.agents import make_agent_profile
    try:
        profile = make_agent_profile(build)
        saved = service._build_store.save(build, expected_revision=1)
        service._agents.register(profile)
    except (ValueError, BuildConflict) as exc:
        raise HTTPException(422, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Migração 0010 pendente') from exc
    return {'build': saved.model_dump(mode='json'), 'agent_id': profile.id,
            'model_shared': True}


class PreviewRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1200)
    brain_id: str | None = None
    agent_id: str = 'morgana'
    document_hint: str = Field(default='', max_length=85)


@router.post('/preview')
async def preview(body: PreviewRequest):
    service = _service()
    _known_agent(service, body.agent_id)
    if body.brain_id not in (None, 'knowledge', 'analysis'):
        raise HTTPException(422, 'Somente cérebros realmente instalados podem ser testados')
    # No arbitrary code, no direct filesystem paths, no externally supplied tools.
    plan = service._capability_router.plan(
        body.query,
        document_request=DocumentRequest(body.query, body.document_hint)
        if body.brain_id == 'knowledge' else None,
        data_request=True if body.brain_id == 'analysis' else None)
    request = BrainRequest(request_id=uuid4(), conversation_id=None,
                           query=body.query, intent=plan.intent,
                           document_hint=body.document_hint,
                           budget=ResourceBudget(timeout_seconds=service._brain_timeout,
                                                 max_memory_mb=service._brain_max_memory_mb),
                           trace_id=plan.trace_id)
    from campanario.runtime.permissions import AuthorizationContext
    outcomes = await service._brain_executor.execute(
        plan, request, authorization=AuthorizationContext(
            principal_kind='local_user', principal_id='campanario-local-preview',
            session_active=True))
    build = service._build_store.get(body.agent_id)
    active = select_talents(build, intent=plan.intent, text=body.query)
    return {'plan': {'intent': plan.intent, 'brain_ids': plan.brain_ids,
                     'reasons': plan.reasons, 'trace_id': str(plan.trace_id)},
            'runs': [out.public() for out in outcomes],
            'evidence': [
                {'id': src.source_id, 'title': src.title, 'document_id': src.document_id,
                 'page': src.page, 'section': src.section, 'excerpt': src.excerpt}
                for out in outcomes for src in out.evidence_refs],
            'computed_answer': next((r.guard.verified_answer for r in outcomes
                                     if r.guard is not None and hasattr(r.guard, 'verified_answer')), None),
            'talents': [t.__dict__ if hasattr(t, '__dict__') else {
                'id': t.id, 'trigger': t.trigger, 'effect': t.effect} for t in active]}


@router.get('/builds/{agent_id}/export')
def export_build(agent_id: str):
    service = _service()
    _known_agent(service, agent_id)
    try:
        raw = export_package(service._build_store.get(agent_id))
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Migração 0010 pendente') from exc
    return Response(raw, media_type='application/octet-stream', headers={
        'Content-Disposition': f'attachment; filename="{agent_id}.campagent"',
        'X-Content-Type-Options': 'nosniff'})


@router.post('/package/inspect')
async def inspect_package(request: Request):
    _service()
    if int(request.headers.get('content-length') or 0) > 4_000_000:
        raise HTTPException(413, 'Pacote excede 4MB')
    raw = await request.body()
    try:
        build = import_package(raw)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    # Preview only: importing never silently grants permissions or creates agents.
    return {'build': build.model_dump(mode='json'), 'imported': False,
            'note': 'Validado; configure a ficha por ação explícita na Forja.'}
