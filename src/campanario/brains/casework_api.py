"""R3.3: native Dark Matter case workspace API; local PF6 session and per-write consent.

Never accepts server filesystem paths from the browser. Storage is anchored to the
existing CAMPANARIO-DATABASE/dados and intentionally does not create a database.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from uuid import UUID, UUID as _UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from campanario.app.security import require_local
from campanario.brains.casework import CaseWorkspace, CaseError, MAX_BYTES
from campanario.config import get_settings
from campanario.runtime.permissions import AuthorizationContext, PermissionDecision, PermissionMode
from campanario.utilities.api import _owner_session, local

router = APIRouter(prefix='/api/v1/cases', tags=['casos'])
_write_lock = RLock()
_PERMISSION = 'casework.write'
_CAPABILITY = 'casework'
_LOCAL_OWNER = 'loopback-utilities'
_LOCAL_SESSION_ID = _UUID('00000000-0000-4000-8000-000000000034')


def _solo_mode() -> bool:
    """Local personal workspace without PF6 setup; invalid PF6 config never falls back."""
    if getattr(get_settings(), 'local_personal_mode', False):
        return True
    from campanario.utilities.api import _identities, _owner_enabled
    try:
        return not _identities() and not _owner_enabled()
    except ValueError:
        # An explicit but invalid identity list is never interpreted as solo mode.
        raise HTTPException(503, 'Configuração de identidades locais inválida') from None



def _session(request: Request):
    require_local(request)
    local(request)
    if _solo_mode():
        return SimpleNamespace(principal_id=_LOCAL_OWNER, session_id=_LOCAL_SESSION_ID)
    return _owner_session(request)


def _workspace():
    try:
        return CaseWorkspace(Path(get_settings().data_dir))
    except (OSError, ValueError) as exc:
        raise HTTPException(503, 'CAMPANARIO-DATABASE/dados não configurado ou indisponível') from exc


def _owned_case(workspace, case_id: str, session):
    data = _checked(lambda: workspace.read(case_id))
    if not _solo_mode() and data.get('authorized_by') != session.principal_id:
        # Do not reveal another operator's cases or whether they exist.
        raise HTTPException(404, 'Caso não encontrado nesta identidade')
    return data


def _write_acl(session):
    # This is additional denial, never a grant over the central permission policy.
    if not session.principal_id.startswith('pf6-user:'):
        return
    from campanario.utilities.pf6_acl import can_write
    import os
    try:
        allowed = can_write(session.principal_id, 'casework',
                            os.environ.get('CAMPANARIO_CASEWORK_WRITE_ACL_JSON') or get_settings().casework_write_acl_json,
                            frozenset({'casework'}))
    except ValueError:
        raise HTTPException(503, 'ACL privada de casos inválida') from None
    if not allowed:
        raise HTTPException(403, 'Operador sem permissão de escrita de casos')


def _authorize(request: Request, operation: str, body: bytes):
    session = _session(request)
    if _solo_mode() and session.principal_id == _LOCAL_OWNER:
        # Explicitly local-only mode: no V9 switch, PF6 credential or new policy.
        # The existing LocalOnlyBoundary and origin checks still apply.
        return session
    _write_acl(session)
    from campanario.bootstrap import get_runtime
    policy = get_runtime().permissions
    policy.set_rule(_PERMISSION, PermissionMode.SCOPED_CONFIRM)
    digest = body if isinstance(body, str) else hashlib.sha256(body).hexdigest()
    scope = 'casework:' + operation + ':' + digest
    auth = AuthorizationContext(principal_kind='local_browser', principal_id=session.principal_id,
                                session_id=session.session_id, session_active=True,
                                confirmation_token=request.headers.get('x-case-confirmation') or None)
    check = policy.check(_PERMISSION, auth, capability=_CAPABILITY, scope=scope)
    if check.decision == PermissionDecision.CONFIRM:
        raise HTTPException(428, detail={'confirmation_id': str(check.confirmation_id),
                                         'message': 'Confirmação PF6 desta operação necessária'})
    if check.decision != PermissionDecision.ALLOW:
        raise HTTPException(403, 'Operação negada pela política central')
    return session


@router.get('/mode')
def case_mode(request: Request):
    _session(request)
    return {'solo_local': _solo_mode(), 'requires_pf6': not _solo_mode()}


class Approve(BaseModel):
    confirmation_id: UUID


@router.post('/approve')
def approve(request: Request, body: Approve):
    session = _session(request)
    if _solo_mode() and session.principal_id == _LOCAL_OWNER:
        raise HTTPException(409, 'Confirmações PF6 não são usadas no modo local pessoal')
    _write_acl(session)
    from campanario.bootstrap import get_runtime
    policy = get_runtime().permissions
    # Only the same session and capability may approve its own pending request.
    with policy._confirmation_lock:
        policy._prune_confirmations(__import__('datetime').datetime.now(__import__('datetime').timezone.utc))
        item = policy._confirmations.get(body.confirmation_id)
        if (item is None or item.session_id != session.session_id or
                item.principal_id != session.principal_id or item.capability != _CAPABILITY or
                item.permission != _PERMISSION or item.approved or item.consumed):
            raise HTTPException(404, 'Confirmação inexistente, expirada ou de outra sessão')
        try:
            token = policy.approve(body.confirmation_id, principal_id=session.principal_id)
        except KeyError:
            raise HTTPException(409, 'Confirmação não disponível') from None
    return {'confirmation_token': token}


class CaseQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=600)
    agent_id: str = 'morgana'


class NewCase(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    objective: str = Field(min_length=1, max_length=1000)


class NewEvent(BaseModel):
    date_time: str = Field(min_length=1, max_length=45)
    description: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1, max_length=16)
    classification: str = 'reported'


class NewHypothesis(BaseModel):
    statement: str = Field(min_length=1, max_length=500)
    supporting: list[str] = Field(default_factory=list, max_length=32)
    opposing: list[str] = Field(default_factory=list, max_length=32)
    next_check: str = Field(min_length=1, max_length=500)


def _checked(action):
    try:
        return action()
    except CaseError as exc:
        raise HTTPException(422, str(exc)) from exc


def _payload(model):
    return model.model_dump_json(exclude_none=False).encode('utf-8')


@router.get('')
def list_cases(request: Request):
    session = _session(request)
    workspace = _workspace()
    if not workspace.root.is_dir() or workspace.root.is_symlink():
        return {'items': []}
    items = []
    for path in sorted(workspace.root.iterdir(), key=lambda p: p.name):
        if path.is_dir() and not path.is_symlink():
            try:
                case = workspace.read(path.name)
                if not _solo_mode() and case.get('authorized_by') != session.principal_id:
                    continue
                items.append({'case_id': case['case_id'], 'title': case['title'],
                              'created_at': case['created_at'], 'objective': case['objective']})
            except (CaseError, KeyError, TypeError):
                continue
    return {'items': items[:4096]}


@router.post('', status_code=201)
def create(request: Request, body: NewCase):
    session = _authorize(request, 'create', _payload(body))
    with _write_lock:
        return {'case_id': _checked(lambda: _workspace().create(body.title, body.objective, session.principal_id))}


@router.get('/{case_id}')
def details(case_id: str, request: Request):
    session = _session(request)
    return _owned_case(_workspace(), case_id, session)


@router.post('/{case_id}/ask')
def ask_case(case_id: str, request: Request, body: CaseQuestion):
    # Read-only, authenticated, owner-locked. No PF6 write grant and no LLM call.
    session = _session(request)
    workspace = _workspace()
    _owned_case(workspace, case_id, session)
    from campanario.brains.casework_dialogue import prepare_case_answer
    try:
        return prepare_case_answer(workspace, case_id, body.question, body.agent_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except CaseError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/{case_id}/review')
def review(case_id: str, request: Request):
    session = _session(request)
    workspace = _workspace()
    _owned_case(workspace, case_id, session)
    return _checked(lambda: workspace.review(case_id))


@router.get('/{case_id}/dossier')
def dossier(case_id: str, request: Request):
    session = _session(request)
    workspace = _workspace()
    _owned_case(workspace, case_id, session)
    return {'markdown': _checked(lambda: workspace.dossier(case_id))}


@router.get('/{case_id}/integrity')
def integrity(case_id: str, request: Request):
    session = _session(request)
    workspace = _workspace()
    _owned_case(workspace, case_id, session)
    return _checked(lambda: workspace.verify(case_id))


@router.post('/{case_id}/events', status_code=201)
def add_event(case_id: str, request: Request, body: NewEvent):
    session = _session(request)
    _owned_case(_workspace(), case_id, session)
    _authorize(request, 'event:' + case_id, _payload(body))
    with _write_lock:
        return _checked(lambda: _workspace().add_event(case_id, body.date_time, body.description,
                                                        body.evidence_ids, body.classification))


@router.post('/{case_id}/hypotheses', status_code=201)
def add_hypothesis(case_id: str, request: Request, body: NewHypothesis):
    session = _session(request)
    _owned_case(_workspace(), case_id, session)
    _authorize(request, 'hypothesis:' + case_id, _payload(body))
    with _write_lock:
        return _checked(lambda: _workspace().add_hypothesis(case_id, body.statement,
                             body.supporting, body.opposing, body.next_check))


@router.get('/{case_id}/evidence/{evidence_id}/proposed-events')
def proposed_events(case_id: str, evidence_id: str, request: Request):
    session = _session(request)
    workspace = _workspace()
    _owned_case(workspace, case_id, session)
    return {'items': _checked(lambda: workspace.propose_log_events(case_id, evidence_id))}


@router.post('/{case_id}/evidence', status_code=201)
async def import_evidence(case_id: str, request: Request):
    session = _session(request)
    _owned_case(_workspace(), case_id, session)
    # Binary upload is whole-file with explicitly supplied extension and provenance.
    # Never receive or open client-provided local paths.
    filename = request.headers.get('x-case-filename', '')
    origin = request.headers.get('x-case-origin', '')
    from pathlib import PurePath
    from urllib.parse import unquote
    filename = unquote(filename)
    origin = unquote(origin)
    name_root = filename.split('.', 1)[0].upper()
    windows_reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if (not filename or filename != PurePath(filename).name or '\\' in filename or len(filename) > 180
            or any(c in filename for c in ':<>|?*') or any(ord(c) < 32 for c in filename)
            or filename.endswith(('.', ' ')) or name_root in windows_reserved or filename in {'.', '..'}):
        raise HTTPException(422, 'Nome de arquivo inválido')
    if not origin or len(origin) > 300:
        raise HTTPException(422, 'Origem declarada obrigatória')
    length = request.headers.get('content-length')
    if length is not None:
        if not length.isascii() or not length.isdecimal():
            raise HTTPException(400, 'Tamanho inválido')
        if int(length) > MAX_BYTES:
            raise HTTPException(413, 'Evidência excede a capacidade de 1 GiB')
    workspace = _workspace()
    # Stream into a temporary file in the EXTERNAL Database, never buffer a full
    # PDF/video-sized file in RAM. Hash binds approvals in protected mode.
    with _write_lock:
        with tempfile.TemporaryDirectory(dir=workspace.root.parent) as staging:
            target = Path(staging) / filename
            digest = hashlib.sha256()
            size = 0
            with target.open('xb') as output:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise HTTPException(413, 'Evidência excede a capacidade de 1 GiB')
                    digest.update(chunk)
                    output.write(chunk)
            if not size:
                raise HTTPException(422, 'Evidência vazia')
            if length is not None and size != int(length):
                raise HTTPException(400, 'Tamanho recebido não confere')
            _authorize(request, 'evidence:' + case_id + ':' + filename + ':' + origin, digest.hexdigest())
            return _checked(lambda: workspace.add_evidence(case_id, target, origin, session.principal_id))
