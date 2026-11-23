from pathlib import Path
from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from campanario.app.security import require_local
from campanario.app.status import system_status
from campanario.companion.store import get_store

router = APIRouter(prefix="/api/app", dependencies=[Depends(require_local)])


@router.get("/status")
async def status():
    return await system_status()


class PairCode(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    allow_chat: bool = False


@router.post("/pairing")
def pairing(body: PairCode):
    return get_store().create_pair_code(body.name.strip(), body.allow_chat)


@router.get("/devices")
def devices():
    return get_store().list_devices()


class Confirmation(BaseModel):
    confirmation: str


@router.post("/devices/{device_id}/revoke")
def revoke(device_id: UUID, body: Confirmation):
    if body.confirmation != "REVOGAR":
        raise HTTPException(422, "Digite REVOGAR")
    try:
        get_store().revoke(str(device_id))
    except KeyError:
        raise HTTPException(404, "Dispositivo inexistente")
    return {"revoked": True, "offline_copies_erased": False}


class Publish(BaseModel):
    memory_ids: list[UUID] = Field(default_factory=list, max_length=100)
    session_ids: list[UUID] = Field(default_factory=list, max_length=30)
    confirmation: str


@router.post("/devices/{device_id}/snapshot")
def publish(device_id: UUID, body: Publish):
    if body.confirmation != "COMPARTILHAR":
        raise HTTPException(422, "Digite COMPARTILHAR")
    from campanario.api import list_messages
    from campanario.bootstrap import get_runtime
    runtime = get_runtime()
    available = {m.id: m for m in runtime.experience.list_memories(limit=1000)}
    sessions = {s.id: s for s in runtime.conversation.list_sessions()}
    if any(mid not in available for mid in body.memory_ids) or any(sid not in sessions for sid in body.session_ids):
        raise HTTPException(409, "Selecao nao encontrada; atualize a lista")
    items = []
    for mid in dict.fromkeys(body.memory_ids):
        m = available[mid]
        items.append({"id": str(mid), "kind": "memory", "title": str(m.key), "text": m.value, "source": "Memoria selecionada no PC"})
    for sid in dict.fromkeys(body.session_ids):
        transcript = list_messages(sid)
        text = "\n\n".join(f"{m['agent_id'] or m['role']}: {m['content']}" for m in transcript)
        items.append({"id": str(sid), "kind": "conversation", "title": sessions[sid].title or "Conversa", "text": text, "source": "Conversa selecionada no PC"})
    try:
        return get_store().publish(str(device_id), items)
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc


@router.get("/devices/{device_id}/notes")
def notes(device_id: UUID):
    try:
        return get_store().sync_notes(str(device_id), [])
    except PermissionError as exc:
        raise HTTPException(404, str(exc)) from exc


class RemoteStart(BaseModel):
    host: str = Field(default="0.0.0.0", pattern=r"^\d{1,3}(?:\.\d{1,3}){3}$")
    port: int = Field(default=8443, ge=1024, le=65535)
    certificate: str = Field(min_length=1, max_length=1024)
    private_key: str = Field(min_length=1, max_length=1024)
    confirmation: str


@router.get("/remote")
def remote_status():
    from campanario.app.remote import listener
    return listener.status()


@router.post("/remote/start")
def remote_start(body: RemoteStart):
    from campanario.app.remote import listener
    if body.confirmation != "ATIVAR ACESSO MOBILE":
        raise HTTPException(422, "Confirmacao necessaria")
    try:
        return listener.start(body.host, body.port, Path(body.certificate), Path(body.private_key))
    except (OSError, ValueError) as exc:
        raise HTTPException(400, f"Nao foi possivel iniciar o listener TLS: {exc}") from exc


@router.post("/remote/stop")
def remote_stop():
    from campanario.app.remote import listener
    return listener.stop()


@router.get("/updates")
async def updates():
    from campanario.config import get_settings
    from campanario.app.updates import check_release
    repo = get_settings().update_repository
    if not repo:
        return {"configured": False, "message": "Configure CAMPANARIO_UPDATE_REPOSITORY=dono/repositorio no .env"}
    try:
        return {"configured": True, **(await check_release(repo))}
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(502, "Nao foi possivel verificar uma release estavel nesse repositorio") from exc


@router.get("/gps/tracks")
def local_gps_tracks():
    return get_store().list_gps_tracks()


@router.post("/gps/tracks/{device_id}/{track_id}/delete")
def local_delete_gps_track(device_id: UUID, track_id: UUID, body: Confirmation):
    if body.confirmation != "APAGAR GPS":
        raise HTTPException(422, "Digite APAGAR GPS")
    return {"deleted": get_store().delete_gps_track(str(device_id), str(track_id))}


# Optional offline cartography. Import a legally obtained raster MBTiles file manually.
@router.get("/maps/status")
def maps_status():
    from campanario.app.maps import map_status
    return map_status()

@router.get("/maps/tiles/{z}/{x}/{y}.png")
def map_tile(z: int, x: int, y: int):
    from campanario.app.maps import read_tile
    from fastapi import Response
    payload = read_tile(z, x, y)
    if payload is None:
        raise HTTPException(404, "Tile não encontrado no pacote offline")
    return Response(payload, media_type="image/png", headers={"Cache-Control":"private, max-age=86400", "X-Content-Type-Options":"nosniff"})


# Maps V2: explicit local OSRM/Nominatim integration and a shared in-process
# navigation session. The browser/device owns GPS and only sends authorized fixes.
from campanario.app.navigation_v2 import (
    navigator as maps_v2_session, route_from_osrm, search_local, resolve_places,
    local_provider_status, coords, nearby_places, category_for,
)

class MapsV2RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    mode: str = "driving"
    destination_name: str = Field(default="", max_length=250)

class MapsV2Fix(BaseModel):
    lat: float = Field(allow_inf_nan=False)
    lon: float = Field(allow_inf_nan=False)
    accuracy: float = Field(gt=0, le=100, allow_inf_nan=False)
    timestamp: float = Field(allow_inf_nan=False)

class MapsV2Resolve(BaseModel):
    query: str = Field(min_length=3, max_length=140)
    near_lat: float | None = None
    near_lon: float | None = None
    explicit_distant: bool = False

@router.get("/navigation/v2/providers")
def navigation_v2_providers():
    try:
        return local_provider_status()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/navigation/v2/resolve")
async def navigation_v2_resolve(body: MapsV2Resolve):
    try:
        near = coords(body.near_lat, body.near_lon) if body.near_lat is not None and body.near_lon is not None else None
        if (body.near_lat is None) != (body.near_lon is None):
            raise ValueError("Origem incompleta")
        generic_nearby = bool(near and not body.explicit_distant and category_for(body.query))
        if generic_nearby:
            try:
                items = await nearby_places(body.query, near)
            except (httpx.HTTPError, OSError):
                items = []
            if not items:
                raise HTTPException(503, "Nenhum estabelecimento retornado pelo índice OSM local/público para esta categoria")
            # Nearby category matches are already verified by OSM tags, not the
            # literal name of the establishment.
            items.sort(key=lambda v:v['air_distance_m'])
            candidates=[]
            for item in items[:6]:
                try:
                    r=await route_from_osrm(near,item,"driving")
                    candidates.append({**item,"route_distance_m":round(r['distance']),"route_duration_s":round(r['duration'])})
                except (httpx.HTTPError, ValueError, OSError):
                    continue
            if not candidates:
                raise HTTPException(503, "Nenhum roteador disponível para comparar distâncias por rota")
            candidates.sort(key=lambda v:v['route_distance_m'])
            nearest=candidates[0]
            clear=len(candidates)==1 or candidates[1]['route_distance_m']>=nearest['route_distance_m']*1.18+100
            return {"candidates":candidates,"selected":nearest if clear else None,
                    "ambiguous":not clear,"needs_confirmation":not clear,
                    "ranking":"distância por rota real; sem trânsito ao vivo"}
        items = await search_local(body.query, near)
        return resolve_places(items, body.query, near, explicit_distant=body.explicit_distant)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (httpx.HTTPError, OSError) as exc:
        raise HTTPException(503, "Geocodificação indisponível (local e fallback público). Verifique conexão e configuração.") from exc

@router.post("/navigation/v2/route")
async def navigation_v2_route(body: MapsV2RouteRequest):
    try:
        origin, end = coords(body.start_lat,body.start_lon),coords(body.end_lat,body.end_lon)
        result = await route_from_osrm(origin,end,body.mode)
        maps_v2_session.ready(result,{**end,"name":body.destination_name[:250]})
        return maps_v2_session.status()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (httpx.HTTPError, OSError) as exc:
        raise HTTPException(503, "Roteamento indisponível (local e fallback público). Confira conexão ou instale OSRM local") from exc

@router.get("/navigation/v2/status")
def navigation_v2_status():
    return maps_v2_session.status()

@router.post("/navigation/v2/command/{action}")
def navigation_v2_action(action: str):
    if action not in ("start", "pause", "resume", "stop"):
        raise HTTPException(404, "Comando inexistente")
    try:
        return maps_v2_session.command(action)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@router.post("/navigation/v2/fix")
def navigation_v2_fix(body: MapsV2Fix):
    try:
        return maps_v2_session.position_fix(body.lat,body.lon,body.accuracy,body.timestamp)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/navigation/v2/recalculate")
async def navigation_v2_recalculate():
    s = maps_v2_session.status()
    if s["state"] != "RECALCULATING" or not s.get("position") or not s.get("target"):
        raise HTTPException(409, "Recálculo não solicitado por desvio confirmado")
    try:
        result = await route_from_osrm(s["position"],s["target"],s["route"].get("mode","driving"))
        # Protect against an old asynchronous reroute overwriting a newer session.
        if maps_v2_session.status()["id"] != s["id"]:
            raise HTTPException(409, "Sessão de navegação alterada")
        return maps_v2_session.replace_route(result)
    except (httpx.HTTPError, OSError, ValueError) as exc:
        maps_v2_session.reroute_error()
        raise HTTPException(503, "Recálculo local falhou; siga sinalização e pare em local seguro") from exc


# Navigation v1.2: requests to fixed public providers, only after explicit user action.
# Public demo services are best-effort and must not be used as a safety-critical navigator.
@router.get("/navigation/search")
async def navigation_search(q: str, near_lat: float | None = None, near_lon: float | None = None):
    if not 3 <= len(q.strip()) <= 140:
        raise HTTPException(422, "Informe um destino de 3 a 140 caracteres")
    params = {"q": q.strip(), "format": "jsonv2", "limit": 5}
    if near_lat is not None or near_lon is not None:
        if near_lat is None or near_lon is None or not (-85 <= near_lat <= 85 and -180 <= near_lon <= 180):
            raise HTTPException(422, "Origem inválida")
        # Bounded geocoding avoids matching vague Portuguese phrases to distant countries.
        span_lat = 0.5
        span_lon = min(1.0, 0.5 / max(0.2, __import__('math').cos(__import__('math').radians(near_lat))))
        params.update({"viewbox": f"{max(-180, near_lon-span_lon)},{min(85, near_lat+span_lat)},{min(180, near_lon+span_lon)},{max(-85, near_lat-span_lat)}", "bounded": 1})
    try:
        async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "CampanarioNavigation/1.2 (local personal app)"}) as client:
            response = await client.get("https://nominatim.openstreetmap.org/search", params=params)
            response.raise_for_status()
            return [{"name": r.get("display_name", ""), "lat": float(r["lat"]), "lon": float(r["lon"])} for r in response.json()[:5]]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(502, "Busca online indisponível; informe coordenadas") from exc


@router.get("/navigation/route")
async def navigation_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    if not (-85 <= start_lat <= 85 and -85 <= end_lat <= 85 and -180 <= start_lon <= 180 and -180 <= end_lon <= 180):
        raise HTTPException(422, "Coordenadas inválidas")
    coords = f"{start_lon:.6f},{start_lat:.6f};{end_lon:.6f},{end_lat:.6f}"
    try:
        async with httpx.AsyncClient(timeout=18) as client:
            response = await client.get(f"https://router.project-osrm.org/route/v1/driving/{coords}", params={"overview":"full", "geometries":"geojson", "steps":"true"})
            response.raise_for_status()
            payload = response.json()
        if payload.get("code") != "Ok" or not payload.get("routes"):
            raise HTTPException(404, "Não há rota rodoviária para esses pontos")
        r = payload["routes"][0]
        geometry = r["geometry"]["coordinates"]
        if len(geometry) > 15000:
            raise HTTPException(413, "Rota grande demais para exibição")
        steps = []
        for leg in r.get("legs", []):
            for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                steps.append({"type": maneuver.get("type", ""), "modifier": maneuver.get("modifier", ""), "name": step.get("name", ""), "distance": step.get("distance", 0), "location": maneuver.get("location", [])})
        return {"distance":r["distance"], "duration":r["duration"], "points":[{"lat":v[1], "lon":v[0]} for v in geometry], "steps":steps[:500], "provider":"OSRM public demo; roteamento online"}
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Roteamento online indisponível") from exc
