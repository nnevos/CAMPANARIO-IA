"""Loopback-restricted browser adapter; intentionally independent of Ollama."""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from campanario.utilities.integration import service
from campanario.utilities.service import OPERATIONS, WRITE

# PDFs maiores devem ser enviados diretamente do navegador, em fluxo, nunca
# transformados em uma string Base64 inteira na memoria do processo.
MAX_UPLOAD_BYTES = 200_000_000
_ALLOWED_UPLOAD_EXT = frozenset(('.txt', '.md', '.pdf', '.csv', '.json', '.log', '.docx', '.xlsx'))

router=APIRouter(prefix='/api/v1/utilities',tags=['utilidades'])

def local(request):
 host=request.client.host if request.client else ''
 if host not in ('127.0.0.1','::1','localhost','testclient'):
  raise HTTPException(403,'Utilidades exigem acesso local; autenticação remota não está configurada')
 origin=request.headers.get('origin')
 if origin:
  from urllib.parse import urlsplit
  if urlsplit(origin).netloc.lower()!=request.headers.get('host','').lower():raise HTTPException(403,'Origem não autorizada')

class Invoke(BaseModel):
 tool:str=Field(min_length=1,max_length=128)
 arguments:dict=Field(default_factory=dict)

@router.get('/catalog')
def catalog(request:Request):
 local(request)
 return [{'id':n,'description':d,'requires_confirmation':n in WRITE,'available':True,'offline':not n.startswith('web.')} for n,d in OPERATIONS.items()]

@router.post('/invoke')
def invoke(request:Request,body:Invoke):
 local(request)
 if body.tool not in OPERATIONS:raise HTTPException(404,'Ferramenta desconhecida')
 return service().run(body.tool,body.arguments)


@router.get('/status')
def status(request:Request):
 local(request)
 util=service()
 return {'authorized_roots':[str(p) for p in util.roots], 'offline_tools':True,'model_required':False,'modules':10}

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
async def upload_stream(request: Request, filename: str):
    """Save a bounded local upload incrementally, without Base64 or overwrite.

    The workspace and its roots are provided by UtilityService, not by the
    browser. A failed/interrupted upload is deleted, and existing files never
    get replaced. This route intentionally does not ingest documents silently.
    """
    local(request)
    _check_upload_filename(filename)
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/octet-stream':
        raise HTTPException(415, 'Envie dados binários (application/octet-stream)')
    length = request.headers.get('content-length')
    if length is not None:
        if not length.isascii() or not length.isdecimal():
            raise HTTPException(400, 'Content-Length inválido')
        if int(length) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, 'Arquivo acima do limite de 200 MB')
    target = service().roots[0] / filename
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
                    raise HTTPException(413, 'Arquivo acima do limite de 200 MB')
                output.write(chunk)
        if not total:
            raise HTTPException(400, 'Arquivo vazio')
        if length is not None and total != int(length):
            raise HTTPException(400, 'Tamanho recebido não confere com Content-Length')
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {'path': str(target), 'bytes': total}

@router.post('/upload')
def upload(request:Request,body:Upload):
 """Upload into the confined workspace, never overwrite an existing file."""
 local(request)
 import base64, binascii
 filename=_check_upload_filename(body.filename)
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
