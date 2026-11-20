from collections import defaultdict, deque
import logging
import time
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from campanario.companion.store import get_store, Conflict

router = APIRouter(prefix="/api/companion/v1", tags=["mobile"])
_attempts = defaultdict(deque)


def require_tls(request: Request):
    # proxy_headers=False on the listener; X-Forwarded-Proto cannot bypass this.
    if request.scope.get("scheme") != "https":
        raise HTTPException(403, "Conexao mobile exige HTTPS com certificado confiavel")


def device(request: Request, authorization: str | None = Header(default=None)) -> dict:
    require_tls(request)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Pareie este dispositivo no PC")
    token = authorization[7:]
    if not 32 <= len(token) <= 128:
        raise HTTPException(401, "Credencial invalida")
    try:
        return get_store().authenticate(token)
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc


class PairRequest(BaseModel):
    code: str = Field(min_length=20, max_length=128)


@router.post("/pair")
def pair(request: Request, body: PairRequest):
    require_tls(request)
    peer = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if peer not in _attempts and len(_attempts) >= 1024:
        raise HTTPException(429, "Tente novamente mais tarde")
    attempts = _attempts[peer]
    while attempts and attempts[0] < now - 60:
        attempts.popleft()
    if len(attempts) >= 10:
        raise HTTPException(429, "Muitas tentativas; aguarde um minuto")
    attempts.append(now)
    try:
        return get_store().redeem(body.code)
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc


@router.get("/status")
def status(who=Depends(device)):
    return {"service": "campanario-companion", "version": "0.8.0", "device_id": who["id"], "chat_allowed": who["chat"], "local_model_on_phone": False}


@router.get("/snapshot")
def snapshot(who=Depends(device)):
    return get_store().snapshot(who["id"])


class NoteMutation(BaseModel):
    id: UUID
    mutation_id: UUID
    base_revision: int = Field(ge=0)
    title: str = Field(max_length=200)
    body: str = Field(max_length=10_000)
    deleted: bool = False


class NoteBatch(BaseModel):
    mutations: list[NoteMutation] = Field(default_factory=list, max_length=100)


@router.post("/notes/sync")
def notes(body: NoteBatch, who=Depends(device)):
    try:
        return get_store().sync_notes(who["id"], [m.model_dump(mode="json") for m in body.mutations])
    except Conflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc


class MobileSession(BaseModel):
    client_id: UUID


@router.post("/sessions")
def create_session(body: MobileSession, who=Depends(device)):
    if not who["chat"]:
        raise HTTPException(403, "Chat nao autorizado para este dispositivo")
    from campanario.bootstrap import get_runtime
    sid = get_store().session(who["id"], str(body.client_id), lambda: get_runtime().conversation.create_session(title="Mobile", agent_id="morgana").id)
    return {"id": sid}


def check_session(who, sid):
    if not who["chat"] or not get_store().owns_session(who["id"], str(sid)):
        raise HTTPException(404, "Conversa nao disponivel para este dispositivo")


@router.get("/sessions/{session_id}/messages")
def messages(session_id: UUID, who=Depends(device)):
    check_session(who, session_id)
    from campanario.api import list_messages
    return list_messages(session_id)


class MobileTurn(BaseModel):
    request_id: UUID
    message: str = Field(min_length=1, max_length=10_000)


@router.post("/sessions/{session_id}/turn")
async def turn(session_id: UUID, body: MobileTurn, who=Depends(device)):
    check_session(who, session_id)
    text = body.message.strip()
    if not text:
        raise HTTPException(422, "Mensagem vazia")
    from campanario.api import list_messages
    from campanario.bootstrap import get_runtime
    from campanario.runtime.clients import ClientIdentity
    from campanario.model.protocol import ModelProviderError
    from campanario.chat.service import ModelNotConfiguredError
    store = get_store()
    try:
        outcome = store.begin_turn(who["id"], str(body.request_id), {"session": str(session_id), "message": text})
    except Conflict as exc:
        raise HTTPException(409, str(exc)) from exc
    if outcome["state"] == "done":
        return outcome["result"]
    if outcome["state"] in {"pending", "error"}:
        # At-most-once execution: do not replay an ambiguous turn after network loss.
        raise HTTPException(409, "Envio ja registrado. Consulte a conversa antes de enviar novamente")
    runtime = get_runtime()
    try:
        async for _ in runtime.conversation.stream_turn(session_id, text, client=ClientIdentity(client_id="mobile-" + who["id"])):
            pass
        result = {"messages": list_messages(session_id), "request_id": str(body.request_id)}
        store.finish_turn(who["id"], str(body.request_id), "done", result)
        return result
    except (ModelProviderError, ModelNotConfiguredError) as exc:
        store.finish_turn(who["id"], str(body.request_id), "error", {"error": "model_unavailable"})
        raise HTTPException(503, "Modelo do PC indisponivel; nao houve reenvio automatico") from exc
    except Exception as exc:
        logging.getLogger(__name__).exception("Mobile turn failed (no request content logged)")
        store.finish_turn(who["id"], str(body.request_id), "error", {"error": "turn_failed"})
        raise HTTPException(500, "Falha no processamento. Consulte a conversa antes de reenviar") from exc

@router.get("/turns/{request_id}")
def turn_state(request_id: UUID, who=Depends(device)):
    with get_store().connect() as con:
        row = con.execute("SELECT state FROM turns WHERE device_id=? AND id=?", (who["id"], str(request_id))).fetchone()
    if row is None:
        raise HTTPException(404, "Envio nao registrado; nenhum reenvio automatico foi realizado")
    return {"state": row["state"], "request_id": str(request_id)}


class GpsPoint(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)
    timestamp: int = Field(ge=946684800000, le=4102444800000)
    accuracy: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)


class GpsTrack(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=80)
    points: list[GpsPoint] = Field(min_length=1, max_length=1000)
    confirmation: str


@router.post("/gps/tracks")
def receive_gps_track(body: GpsTrack, who=Depends(device)):
    if body.confirmation != "COMPARTILHAR GPS":
        raise HTTPException(422, "Compartilhamento requer confirmacao")
    points = [p.model_dump() for p in body.points]
    if any(points[i]["timestamp"] <= points[i-1]["timestamp"] for i in range(1, len(points))):
        raise HTTPException(422, "Amostras devem estar em ordem temporal crescente")
    try:
        return get_store().save_gps_track(who["id"], str(body.id), body.name, points)
    except Conflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc
