"""Loopback-restricted browser adapter; intentionally independent of Ollama."""
import os
import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import UUID
from campanario.utilities.pf6_sessions import owner_sessions, SESSION_TTL_SECONDS
from campanario.utilities.pf6_identities import load_identities, identities_fingerprint
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from campanario.utilities.integration import service
from campanario.utilities.service import OPERATIONS, WRITE

# PDFs maiores devem ser enviados diretamente do navegador, em fluxo, nunca
# transformados em uma string Base64 inteira na memoria do processo.
MAX_UPLOAD_BYTES = 1_073_741_824  # 1 GiB, streamed (prevents accidental disk exhaustion)
_ALLOWED_UPLOAD_EXT = frozenset(('.txt', '.md', '.pdf', '.csv', '.json', '.log', '.docx', '.xlsx'))

router=APIRouter(prefix='/api/v1/utilities',tags=['utilidades'])

def local(request):
 host=request.client.host if request.client else ''
 if host not in ('127.0.0.1','::1','localhost','testclient'):
  raise HTTPException(403,'Utilidades exigem acesso local; autenticação remota não está configurada')
 # Browser Fetch Metadata: reject cross-site and opaque origins on all routes.
 fetch_site=request.headers.get('sec-fetch-site','').lower()
 if fetch_site and fetch_site not in ('same-origin','none'):
  raise HTTPException(403,'Requisição entre origens não autorizada')
 origin=request.headers.get('origin')
 if origin:
  from urllib.parse import urlsplit
  parsed=urlsplit(origin)
  if parsed.scheme not in ('http','https') or parsed.netloc.lower()!=request.headers.get('host','').lower():
   raise HTTPException(403,'Origem não autorizada')

def _operation_scope(tool: str, arguments: dict) -> str:
    # Canonical UTF-8 fingerprint binds PF6 approval to the full operation.
    payload = json.dumps({'tool': tool, 'arguments': arguments}, sort_keys=True,
                         separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return 'operation:sha256:' + hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _owner_secret() -> str:
    from campanario.config import get_settings
    return os.environ.get('CAMPANARIO_PF6_OWNER_TOKEN') or getattr(get_settings(), 'pf6_owner_token', '')


def _pf6_mode() -> bool:
    from campanario.config import get_settings
    return bool(get_settings().brains_v9_enabled and not getattr(get_settings(), "local_personal_mode", False))


def _identities():
    # Invalid explicit configuration must fail closed, never fall back to owner secret.
    from campanario.config import get_settings
    return load_identities(os.environ.get('CAMPANARIO_PF6_USERS_JSON') or getattr(get_settings(), 'pf6_users_json', ''))


def _owner_enabled() -> bool:
    key = _owner_secret()
    return len(key) >= 32 and len(key) <= 256 and not key.isspace()


def _bearer(request: Request) -> str:
    value = request.headers.get('authorization', '')
    if not value.startswith('Bearer ') or len(value) > 256:
        raise HTTPException(401, 'Sessão PF6 necessária')
    return value[7:]


def _owner_session(request: Request):
    try:
        enabled = bool(_identities()) or _owner_enabled()
    except ValueError:
        raise HTTPException(503, 'Configuração PF6 individual inválida') from None
    if not enabled:
        raise HTTPException(503, 'Aprovação PF6 não configurada no servidor')
    try:
        records = _identities()
    except ValueError:
        raise HTTPException(503, 'Configuração PF6 individual inválida') from None
    verifier = identities_fingerprint(records) if records else None
    session = owner_sessions.authenticate(_bearer(request), _owner_secret(), verifier=verifier)
    if session is None:
        raise HTTPException(401, 'Sessão PF6 inválida ou expirada')
    return session


class OwnerLogin(BaseModel):
    username: str | None = Field(default=None, max_length=32)
    credential: str = Field(min_length=1, max_length=512)


@router.post('/sessions/login')
def login_owner(request: Request, body: OwnerLogin):
    local(request)
    from campanario.config import get_settings
    try:
        records = _identities()
    except ValueError:
        raise HTTPException(503, 'Configuração PF6 individual inválida') from None
    if not get_settings().brains_v9_enabled or not (records or _owner_enabled()):
        raise HTTPException(503, 'Sessões PF6 indisponíveis')
    try:
        client = request.client.host if request.client else ''
        if records:
            result = owner_sessions.login_identity(body.username or '', body.credential, records, client=client)
        else:
            if body.username:
                raise HTTPException(401, 'Credencial inválida')
            result = owner_sessions.login(body.credential, _owner_secret(), client=client)
    except PermissionError:
        raise HTTPException(429, 'Muitas tentativas; aguarde antes de tentar novamente') from None
    except OverflowError:
        raise HTTPException(503, 'Limite de sessões PF6 atingido') from None
    if result is None:
        raise HTTPException(401, 'Credencial inválida')
    token, session = result
    return {'session_token': token, 'session_id': str(session.session_id), 'principal_id': session.principal_id,
            'expires_in_seconds': SESSION_TTL_SECONDS}


@router.post('/sessions/logout')
def logout_owner(request: Request):
    local(request)
    _owner_session(request)
    owner_sessions.revoke(_bearer(request))
    return {'revoked': True}


def _individual_write_gate(session, tool: str) -> None:
    """R2.8 additional deny-only gate; never substitutes central permission.

    A configured set of individual identities must have an explicit allowlist
    for each write tool; unconfigured/malformed ACLs fail closed. Legacy owner
    mode preserves the R2.7 behavior.
    """
    if not session.principal_id.startswith('pf6-user:'):
        return
    from campanario.utilities.pf6_acl import can_write
    try:
        authorized = can_write(session.principal_id, tool,
                               os.environ.get('CAMPANARIO_PF6_WRITE_ACL_JSON', ''), WRITE)
    except ValueError:
        raise HTTPException(503, 'Lista de permissões PF6 inválida') from None
    if not authorized:
        raise HTTPException(403, 'Esta ferramenta não está autorizada para o usuário')


def _policy():
    from campanario.bootstrap import get_runtime
    return get_runtime().permissions


def _solo_local_upload() -> bool:
    """R3.13: the personal local uploader needs no PF6 when none is configured.

    This exception applies only to the bounded upload endpoints; it must never
    authorize arbitrary utility writes, case edits, or access from another origin.
    """
    from campanario.config import get_settings
    if getattr(get_settings(), "local_personal_mode", False):
        return True
    try:
        return not _identities() and not _owner_enabled()
    except ValueError:
        raise HTTPException(503, 'Configuração de identidades locais inválida') from None


def _v9_permission(request: Request, *, write: bool, capability: str,
                   scope: str | None = None, confirmation_token: str | None = None) -> None:
    """R1 bridge: never trust a browser-provided confirmation as PF6 approval.

    This is a conservative local-only bridge, not completed R1 authorization.
    In V9 opt-in, writes require a PF6 confirmation flow that the browser
    adapter does not yet expose, and therefore fail closed.
    """
    from campanario.config import get_settings
    if getattr(get_settings(), "local_personal_mode", False) or not get_settings().brains_v9_enabled:
        return  # Local personal mode: no central PF6 approval for browser utilities.
    from campanario.runtime.permissions import AuthorizationContext, PermissionDecision
    try:
        permissions = _policy()
        session = _owner_session(request) if write and confirmation_token else None
        if session is not None:
            _individual_write_gate(session, capability)
        checked = permissions.check(
            'utilities.write' if write else 'utilities.read',
            AuthorizationContext(principal_kind='local_browser',
                                 principal_id=session.principal_id if session else 'loopback-utilities', session_active=True,
                                 session_id=session.session_id if session else None,
                                 confirmation_token=confirmation_token),
            capability=capability, scope=scope if scope is not None else capability,
        )
    except HTTPException:
        raise
    except Exception:
        # Runtime/permission store unavailable: no fallback to an internal
        # principal and no direct access to the utility service.
        raise HTTPException(503, 'Política de permissões indisponível') from None
    if checked.decision != PermissionDecision.ALLOW:
        raise HTTPException(403, 'Permissão não concedida pela política central')


class Invoke(BaseModel):
 tool:str=Field(min_length=1,max_length=128)
 arguments:dict=Field(default_factory=dict)
 confirmation_token:str|None=Field(default=None,max_length=128)


class Approval(BaseModel):
 confirmation_id: UUID
 tool: str = Field(min_length=1, max_length=128)
 arguments: dict = Field(default_factory=dict)
 acknowledged: bool = False


@router.post('/confirmations/request')
def request_confirmation(request: Request, body: Invoke):
    local(request)
    from campanario.config import get_settings
    if not get_settings().brains_v9_enabled:
        raise HTTPException(503, 'Aprovação PF6 indisponível')
    session = _owner_session(request)
    if body.tool not in WRITE or body.tool not in OPERATIONS:
        raise HTTPException(400, 'Confirmação permitida somente para operações de escrita conhecidas')
    _individual_write_gate(session, body.tool)
    if body.confirmation_token:
        raise HTTPException(400, 'Não forneça token ao solicitar confirmação')
    try:
        from campanario.runtime.permissions import AuthorizationContext, PermissionDecision
        policy = _policy()
        result = policy.check('utilities.write', AuthorizationContext(
            principal_kind='local_browser', principal_id=session.principal_id,
            session_id=session.session_id, session_active=True),
            capability=body.tool, scope=_operation_scope(body.tool, body.arguments))
    except (TypeError, ValueError):
        raise HTTPException(400, 'Argumentos inválidos para confirmação') from None
    except Exception:
        raise HTTPException(503, 'Política PF6 indisponível') from None
    if result.decision != PermissionDecision.CONFIRM or not result.confirmation_id:
        raise HTTPException(403, 'Política não requer ou não permite aprovação')
    return {'confirmation_id': str(result.confirmation_id), 'tool': body.tool,
            'arguments': body.arguments, 'expires_in_seconds': 300}


@router.post('/confirmations/approve')
def approve_confirmation(request: Request, body: Approval):
    local(request)
    from campanario.config import get_settings
    if not get_settings().brains_v9_enabled:
        raise HTTPException(403, 'Aprovação exclusiva do modo V9')
    session = _owner_session(request)
    if not body.acknowledged or body.tool not in WRITE or body.tool not in OPERATIONS:
        raise HTTPException(403, 'Consentimento explícito necessário')
    _individual_write_gate(session, body.tool)
    try:
        policy = _policy()
        # Inspect before approving: no arbitrary ID / changed arguments.
        with policy._confirmation_lock:
            policy._prune_confirmations(datetime.now(UTC))
            item = policy._confirmations.get(body.confirmation_id)
            if (item is None or item.permission != 'utilities.write'
                    or item.principal_id != session.principal_id
                    or item.capability != body.tool
                    or item.scope != _operation_scope(body.tool, body.arguments)
                    or item.device_id is not None or item.session_id != session.session_id):
                raise HTTPException(403, 'Confirmação não corresponde à operação')
            token = policy.approve(body.confirmation_id, principal_id=session.principal_id)
    except HTTPException:
        raise
    except (KeyError, ValueError, TypeError):
        raise HTTPException(403, 'Confirmação expirada ou inválida') from None
    except Exception:
        raise HTTPException(503, 'Política PF6 indisponível') from None
    return {'confirmation_token': token}


@router.get('/catalog')
def catalog(request:Request):
 local(request)
 from campanario.config import get_settings
 return [{'id':n,'description':d,'requires_confirmation':n in WRITE and not getattr(get_settings(), "local_personal_mode", False),'available':True,'offline':not n.startswith('web.')} for n,d in OPERATIONS.items()]

@router.post('/invoke')
def invoke(request:Request,body:Invoke):
 local(request)
 if body.tool not in OPERATIONS:raise HTTPException(404,'Ferramenta desconhecida')
 _v9_permission(request, write=body.tool in WRITE, capability=body.tool,
                scope=_operation_scope(body.tool, body.arguments) if body.tool in WRITE else None,
                confirmation_token=body.confirmation_token if body.tool in WRITE else None)
 from campanario.config import get_settings
 arguments = dict(body.arguments)
 if getattr(get_settings(), 'local_personal_mode', False) and body.tool in WRITE:
  arguments['confirm'] = True  # Browser explicitly invoked this tool in local personal mode.
 return service().run(body.tool,arguments)


@router.get('/status')
def status(request:Request):
 local(request)
 util=service()
 from campanario.config import get_settings
 return {'authorized_roots':[str(p) for p in util.roots], 'offline_tools':True,'pf6_mode':_pf6_mode(),'personal_mode':getattr(get_settings(), 'local_personal_mode', False),'model_required':False,'modules':10}

class Upload(BaseModel):
 filename:str=Field(min_length=1,max_length=240)
 content_base64:str=Field(min_length=1,max_length=28000000)


def _check_upload_filename(filename: str) -> str:
    if (not filename or len(filename) > 240 or filename in ('.', '..')
            or Path(filename).name != filename or '/' in filename
            or '\\' in filename or filename.startswith('.')
            or '\x00' in filename or ':' in filename
            or any(char in filename for char in '<>"|?*')):
        raise HTTPException(400, 'Nome de arquivo inválido')
    if Path(filename).suffix.lower() not in _ALLOWED_UPLOAD_EXT:
        raise HTTPException(400, 'Formato não permitido')
    return filename


@router.post('/upload-stream')
async def upload_stream(request: Request, filename: str, index: bool = False):
    """Save a bounded local upload incrementally, without Base64 or overwrite.

    The workspace and its roots are provided by UtilityService, not by the
    browser. A failed/interrupted upload is deleted, and existing files never
    get replaced. Explicit index=true imports searchable files after upload.
    """
    local(request)
    _check_upload_filename(filename)
    if not _solo_local_upload():
        _v9_permission(request, write=True, capability='utilities.upload-stream')
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/octet-stream':
        raise HTTPException(415, 'Envie dados binários (application/octet-stream)')
    length = request.headers.get('content-length')
    if length is not None:
        if not length.isascii() or not length.isdecimal():
            raise HTTPException(400, 'Content-Length inválido')
        if int(length) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, 'Arquivo acima da capacidade de 1 GiB')
    util = service()
    target = util.roots[0] / filename
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    except FileExistsError:
        raise HTTPException(409, 'Já existe um arquivo com esse nome')
    total = 0
    try:
        with os.fdopen(fd, 'wb') as output:
            async for chunk in request.stream():
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, 'Arquivo acima da capacidade de 1 GiB')
                output.write(chunk)
        if not total:
            raise HTTPException(400, 'Arquivo vazio')
        if length is not None and total != int(length):
            raise HTTPException(400, 'Tamanho recebido não confere com Content-Length')
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    result = {'path': str(target), 'bytes': total, 'indexed': False}
    if index:
        if target.suffix.lower() not in {'.pdf','.docx','.txt','.md','.csv','.xlsx','.json','.log'}:
            result['index_error'] = 'Formato não indexável; arquivo preservado na pasta autorizada'
        else:
            try:
                imported = await asyncio.to_thread(
                    util.run, 'library.import',
                    {'path': str(target), 'category': 'anexos-chat', 'confirm': True})
                if imported['status'] != 'success':
                    result['index_error'] = imported.get('result',{}).get('error','Falha ao importar')
                else:
                    outcome = imported['result']
                    result['document_id'] = outcome.get('id') or outcome.get('duplicate_id')
                    with util.connect() as db:
                        sections = db.execute(
                            'SELECT count(*) FROM document_sections WHERE document_id=?',
                            (result['document_id'],)).fetchone()[0]
                    result['indexed'] = outcome.get('state') != 'error' and sections > 0
                    result['indexed_sections'] = sections
                    result['index_state'] = outcome.get('state','duplicate')
                    if not result['indexed']:
                        result['index_error'] = '; '.join(outcome.get('warnings',[])) or 'Nenhum trecho textual recuperado; verifique OCR'
            except Exception as exc:
                result['index_error'] = f'{type(exc).__name__}: {str(exc)[:160]}'
    return result

@router.post('/upload')
def upload(request:Request,body:Upload):
 """Upload into the confined workspace, never overwrite an existing file."""
 local(request)
 import base64, binascii
 filename=_check_upload_filename(body.filename)
 if not _solo_local_upload():
  _v9_permission(request, write=True, capability='utilities.upload')
 try: contents=base64.b64decode(body.content_base64,validate=True)
 except (ValueError,binascii.Error):raise HTTPException(400,'Arquivo codificado incorretamente')
 if len(contents)>20_000_000:raise HTTPException(413,'Arquivo acima do limite de 20 MB')
 util=service()
 target=util.roots[0]/filename
 try:
  descriptor=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
 except FileExistsError:raise HTTPException(409,'Já existe um arquivo com esse nome')
 try:
  with os.fdopen(descriptor,'wb') as output:output.write(contents)
 except Exception:
  target.unlink(missing_ok=True)
  raise
 return {'path':str(target),'bytes':len(contents)}


@router.get('/documents/{document_id}/original')
def document_original(request: Request, document_id: str):
    """Read-only original preview/download, restricted to the user's local machine."""
    local(request)
    _v9_permission(request, write=False, capability='utilities.document-original')
    from fastapi.responses import FileResponse
    from campanario.utilities.document_v8 import document_info
    util = service()
    try:
        info = document_info(util, document_id)
    except ValueError:
        raise HTTPException(404, 'Documento não encontrado') from None
    original = util.docs / (info['id'] + Path(info['name']).suffix.lower())
    if not original.is_file() or not original.resolve().is_relative_to(util.docs.resolve()):
        raise HTTPException(404, 'Arquivo original não encontrado')
    return FileResponse(original, filename=info['name'], media_type=info['type'])
