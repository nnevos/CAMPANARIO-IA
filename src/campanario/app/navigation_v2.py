"""Maps V2: deterministic navigation state and local-first geographical adapters.

A session is independent from the web view and from the model. No position is
collected on the server: the authorized device submits fixes while navigating.
Sessions are volatile per application process. Nothing is saved to the database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt, isfinite
from threading import RLock
from time import monotonic
from uuid import uuid4
from urllib.parse import urlsplit
import os
import asyncio
import time
from threading import Lock

import httpx

STATES = {"IDLE", "RESOLVING_DESTINATION", "CALCULATING_ROUTE", "READY", "NAVIGATING", "OFF_ROUTE", "RECALCULATING", "PAUSED", "ARRIVED", "STOPPED", "ERROR"}


def coords(lat, lon):
    try:
        a, b = float(lat), float(lon)
        if not (-85 <= a <= 85 and -180 <= b <= 180):
            raise ValueError
        return {"lat": a, "lon": b}
    except (ValueError, TypeError):
        raise ValueError("Coordenadas de localização inválidas") from None


def meters(a, b):
    p1, p2 = radians(a["lat"]), radians(b["lat"])
    dp, dl = p2 - p1, radians(b["lon"] - a["lon"])
    return 12742000 * asin(min(1, sqrt(sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2)))


def segment_distance(p, a, b):
    k = cos(radians(p["lat"]))
    ax, ay = (a["lon"]-p["lon"])*111320*k, (a["lat"]-p["lat"])*111320
    bx, by = (b["lon"]-p["lon"])*111320*k, (b["lat"]-p["lat"])*111320
    dx, dy = bx-ax, by-ay
    t = min(1, max(0, -(ax*dx+ay*dy)/max(dx*dx+dy*dy, 1e-8)))
    return sqrt((ax+t*dx)**2+(ay+t*dy)**2)


def route_distance(p, points):
    return min((segment_distance(p, points[i-1], points[i]) for i in range(1, len(points))), default=float('inf'))


def route_progress(p, points):
    """Nearest projection on an ordered route polyline; display estimate only."""
    if len(points)<2:
        return 0.0, float('inf')
    total=sum(meters(points[i-1],points[i]) for i in range(1,len(points)))
    if total<=0:
        return 0.0, float('inf')
    closest=float('inf');progress=0.0;done=0.0
    k=cos(radians(p['lat']))
    for a,b in zip(points,points[1:]):
        ax,ay=(a['lon']-p['lon'])*k*111320,(a['lat']-p['lat'])*111320
        bx,by=(b['lon']-p['lon'])*k*111320,(b['lat']-p['lat'])*111320
        dx,dy=bx-ax,by-ay
        t=min(1,max(0,-(ax*dx+ay*dy)/max(dx*dx+dy*dy,1e-8)))
        dist=sqrt((ax+dx*t)**2+(ay+dy*t)**2)
        length=meters(a,b)
        if dist<closest:
            closest=dist;progress=(done+length*t)/total
        done+=length
    return min(1,max(0,progress)),closest

def _loopback_url(env_name, default):
    # Settings reads the private .env file, unlike os.environ alone.
    from campanario.config import Settings
    value = os.getenv(env_name) or getattr(Settings(), env_name.removeprefix('CAMPANARIO_').lower(), default)
    raw = str(value).strip().rstrip('/')
    parsed = urlsplit(raw)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1") or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError(f"{env_name} precisa apontar para um serviço HTTP local sem credenciais")
    return raw



# Public services are best-effort fallback ONLY for a destination/route request.
# No background location upload or tracking. Nominatim explicitly forbids
# autocomplete, batch geocoding and >1 request/s; cache repeated lookups.
_PUBLIC_NOMINATIM = "https://nominatim.openstreetmap.org"
_PUBLIC_OVERPASS = "https://overpass-api.de"
_PUBLIC_OSRM = "https://router.project-osrm.org"
_PUBLIC_AGENT = "CampanarioMaps/3.20 (personal local navigation; contact: local operator)"
_public_lock = Lock()
_public_last_request = {}
_public_cache = {}


def public_fallback_enabled():
    from campanario.config import Settings
    return Settings().maps_public_fallback


async def _public_json(url, *, client=None, params=None, data=None, cache_key=None, ttl=600):
    key = cache_key or (url, repr(params), repr(data))
    with _public_lock:
        record = _public_cache.get(key)
        if record and time.monotonic() < record[0]:
            return record[1]
        host = urlsplit(url).hostname
        now = time.monotonic()
        wait = max(0.0, _public_last_request.get(host, 0) + 1.1 - now)
        _public_last_request[host] = now + wait
    if wait:
        await asyncio.sleep(wait)
    owned = client is None
    user_agent = os.getenv("CAMPANARIO_MAPS_USER_AGENT", _PUBLIC_AGENT)
    if "\n" in user_agent or "\r" in user_agent or len(user_agent)>240 or not user_agent.strip():
        user_agent = _PUBLIC_AGENT
    c = client or httpx.AsyncClient(timeout=14, headers={"User-Agent": user_agent})
    try:
        if data is None:
            response = await c.get(url, params=params)
        else:
            response = await c.post(url, data=data)
        response.raise_for_status()
        output = response.json()
    finally:
        if owned:
            await c.aclose()
    with _public_lock:
        if len(_public_cache) >= 128:
            _public_cache.pop(next(iter(_public_cache)))
        _public_cache[key] = (time.monotonic()+ttl, output)
    return output


def local_provider_status():
    return {"routing_url": _loopback_url("CAMPANARIO_MAPS_ROUTER_URL", "http://127.0.0.1:5000"),
            "geocoder_url": _loopback_url("CAMPANARIO_MAPS_GEOCODER_URL", "http://127.0.0.1:8088"),
            "provider": "OSRM/Nominatim/Overpass local; fallback público quando o usuário buscar e estiver habilitado",
            "public_fallback_enabled": public_fallback_enabled(),
            "offline_route": "requer grafo OSRM instalado; MBTiles raster não contém rotas"}


async def route_from_osrm(start, end, mode="driving", *, client=None):
    """Fetch an actual OSRM graph route; walking requires a separate foot graph port."""
    if mode not in {"driving", "walking"}:
        raise ValueError("Perfil não suportado")
    var = "CAMPANARIO_MAPS_WALK_ROUTER_URL" if mode == "walking" else "CAMPANARIO_MAPS_ROUTER_URL"
    base = _loopback_url(var, "http://127.0.0.1:5001" if mode == "walking" else "http://127.0.0.1:5000")
    a, b = coords(start["lat"], start["lon"]), coords(end["lat"], end["lon"])
    path = f"/route/v1/{'foot' if mode=='walking' else 'driving'}/{a['lon']:.6f},{a['lat']:.6f};{b['lon']:.6f},{b['lat']:.6f}"
    params={"overview":"full", "geometries":"geojson", "steps":"true"}
    owned = client is None
    c = client or httpx.AsyncClient(timeout=4)
    provider="OSRM local"
    try:
        try:
            resp = await c.get(base+path, params=params)
            resp.raise_for_status()
            data=resp.json()
        except (httpx.HTTPError, OSError):
            if not owned or not public_fallback_enabled() or mode != "driving":
                raise
            data=await _public_json(_PUBLIC_OSRM+path, params=params)
            provider="OSRM público (demonstração; sem garantia de disponibilidade)"
    finally:
        if owned:
            await c.aclose()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Motor de rotas não encontrou trajeto (local/público)")
    raw = data["routes"][0]
    geometry = raw.get("geometry", {}).get("coordinates", [])
    if not 2 <= len(geometry) <= 50000:
        raise ValueError("Geometria incompleta ou extensa demais")
    points = [coords(x[1],x[0]) for x in geometry]
    steps = []
    for leg in raw.get("legs", []):
        for s in leg.get("steps", []):
            m = s.get("maneuver", {})
            position = m.get("location", [])
            steps.append({"type": str(m.get("type", ""))[:40], "modifier": str(m.get("modifier", ""))[:40],
                          "name": str(s.get("name", ""))[:180], "distance": float(s.get("distance", 0)),
                          "location": [float(position[0]), float(position[1])] if len(position)==2 else []})
    if not steps or len(steps)>1000:
        raise ValueError("Motor de rotas não forneceu manobras utilizáveis")
    distance, duration = float(raw["distance"]),float(raw["duration"])
    if not isfinite(distance) or not isfinite(duration) or distance<0 or duration<0:
        raise ValueError("Métricas inválidas do roteador")
    return {"route_id":str(uuid4()), "points":points, "steps":steps, "distance":distance, "duration":duration,
            "provider":provider, "mode":mode, "traffic_live":False}


async def search_local(q, near=None, *, client=None):
    if not 3 <= len(q.strip()) <= 140:
        raise ValueError("Informe destino de 3 a 140 caracteres")
    base = _loopback_url("CAMPANARIO_MAPS_GEOCODER_URL", "http://127.0.0.1:8088")
    params={"q":q.strip(), "format":"jsonv2", "limit":8, "addressdetails":1}
    if near:
        point=coords(near["lat"],near["lon"])
        la,lo=point["lat"],point["lon"]
        span_lon=min(2.0, .4/max(.2, cos(radians(la))))
        params["viewbox"]=f"{max(-180,lo-span_lon)},{min(85,la+.4)},{min(180,lo+span_lon)},{max(-85,la-.4)}"
        # deliberately NOT bounded to allow explicitly distant named places
    owned=client is None
    c=client or httpx.AsyncClient(timeout=4)
    provider="Nominatim local"
    try:
        try:
            response=await c.get(base+"/search",params=params)
            response.raise_for_status()
            data=response.json()
        except (httpx.HTTPError, OSError):
            if not owned or not public_fallback_enabled():
                raise
            data=await _public_json(_PUBLIC_NOMINATIM+"/search",params=params)
            provider="Nominatim público"
    finally:
        if owned:
            await c.aclose()
    results=[]
    for item in data[:8]:
        try:
            point=coords(item["lat"],item["lon"])
        except (ValueError, KeyError):
            continue
        label=str(item.get("display_name", ""))[:250]
        results.append({**point,"name":label,"category":str(item.get("type", ""))[:80],
                        "place_id":str(item.get("place_id", ""))[:80], "provider":provider,
                        "air_distance_m":round(meters(near,point)) if near else None})
    return results


# Local Overpass is optional; intended for genuine category-nearby requests.
# Neither public Overpass nor an external location service is called implicitly.
CATEGORIES = {
    "mercado": ("shop", "supermarket"), "supermercado": ("shop", "supermarket"),
    "farmacia": ("amenity", "pharmacy"), "farmácia": ("amenity", "pharmacy"),
    "hospital": ("amenity", "hospital"), "posto de gasolina": ("amenity", "fuel"),
    "padaria": ("shop", "bakery"), "restaurante": ("amenity", "restaurant"),
}


def category_for(query):
    q=query.lower().strip()
    for term, category in sorted(CATEGORIES.items(),key=lambda t:-len(t[0])):
        if term in q:
            return category
    return None


async def nearby_places(query, near, *, client=None):
    category=category_for(query)
    if not category:
        return []
    base=_loopback_url("CAMPANARIO_MAPS_OVERPASS_URL", "http://127.0.0.1:12345")
    p=coords(near["lat"],near["lon"])
    key,value=category
    statement=f'[out:json][timeout:12];(nwr(around:10000,{p["lat"]:.6f},{p["lon"]:.6f})["{key}"="{value}"];);out center 40;'
    owned=client is None
    c=client or httpx.AsyncClient(timeout=4)
    provider="Overpass local"
    try:
        try:
            response=await c.post(base+"/api/interpreter", data={"data":statement})
            response.raise_for_status()
            data=response.json()
        except (httpx.HTTPError, OSError):
            if not owned or not public_fallback_enabled():
                raise
            data=await _public_json(_PUBLIC_OVERPASS+"/api/interpreter",data={"data":statement},ttl=300)
            provider="Overpass público"
    finally:
        if owned:
            await c.aclose()
    results=[]
    for item in data.get("elements",[])[:40]:
        point=item.get("center",item)
        try:
            loc=coords(point["lat"],point["lon"])
        except (ValueError, KeyError, TypeError):
            continue
        name=str(item.get("tags",{}).get("name") or value)[:180]
        results.append({**loc,"name":name,"category":value,
                        "place_id":str(item.get("type",""))+":"+str(item.get("id","")), "provider":provider,
                        "air_distance_m":round(meters(near,loc))})
    return results

def resolve_places(items, query, near=None, *, explicit_distant=False):
    """Rank known candidates; only auto-select a uniquely plausible candidate.

    Straight-line distance is used only to reject obvious distant mismatches;
    it is never presented as route distance or duration.
    """
    from unicodedata import normalize
    import re
    def norm(s):
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in normalize("NFKD",str(s).lower()) if ord(c)<128))).strip()
    query_terms=[t for t in norm(query).split() if t not in {"o","a","ao","para","mais","proximo","proxima","de","do","da","uma","um","rota","tracar","trace","me","ate","por","favor"}]
    scored=[]
    for item in items:
        label=norm(item.get("name", ""))
        match=sum(any(t==word or (len(t)>4 and word.startswith(t[:5])) for word in label.split()) for t in query_terms)/max(1,len(query_terms))
        proximity=meters(near,item) if near else None
        if near and not explicit_distant and proximity>100000:
            continue
        scored.append({**item,"relevance":round(match,3),"air_distance_m":round(proximity) if proximity is not None else None})
    scored.sort(key=lambda x:(-x["relevance"], x["air_distance_m"] if x["air_distance_m"] is not None else float("inf")))
    # Multiple plausible branches always require selection; do not silently
    # choose first place by Nominatim order or by raw air distance.
    viable=[p for p in scored if p["relevance"]>=.35]
    chosen=viable[0] if len(viable)==1 else None
    return {"candidates":scored,"selected":chosen,"ambiguous":len(viable)>1,
            "needs_confirmation":chosen is None}


@dataclass
class NavigationSession:
    id: str = field(default_factory=lambda:str(uuid4()))
    state: str = "IDLE"
    route: dict | None = None
    target: dict | None = None
    position: dict | None = None
    step_index: int = 0
    off_route_fixes: int = 0
    last_recalculation: float = -1e12
    latest_fix_timestamp: float = 0
    voice_event_seq: int = 0
    voice_key: str = ""
    instructions: list = field(default_factory=list)
    reason: str = ""

    def as_dict(self):
        return {"id":self.id,"state":self.state,"route":self.route,"target":self.target,
                "position":self.position,"step_index":self.step_index,"off_route_fixes":self.off_route_fixes,
                "instructions":self.instructions[-2:],"voice_event_seq":self.voice_event_seq,"reason":self.reason}


class NavigationService:
    """One single-user session. Concurrency is guarded for HTTP threads."""
    def __init__(self):
        self.lock=RLock()
        self.session=NavigationSession()

    def status(self):
        with self.lock:
            return self.session.as_dict()

    def ready(self, route, target):
        if not route.get("points") or not route.get("steps"):
            raise ValueError("Rota não possui geometria ou manobras")
        with self.lock:
            self.session=NavigationSession(state="READY",route=route,target=target)
            return self.status()

    def command(self, action):
        with self.lock:
            s=self.session
            if action == "start" and s.state in {"READY","PAUSED"}:
                s.state="NAVIGATING"
            elif action == "pause" and s.state in {"NAVIGATING","OFF_ROUTE"}:
                s.state="PAUSED"
            elif action == "resume" and s.state=="PAUSED":
                s.state="NAVIGATING"
            elif action=="stop":
                self.session=NavigationSession(state="STOPPED")
            else:
                raise ValueError(f"Transição não permitida: {s.state} → {action}")
            return self.status()

    def position_fix(self, lat, lon, accuracy, timestamp, *, now=None):
        point=coords(lat,lon)
        accuracy=float(accuracy)
        timestamp=float(timestamp)
        now=datetime.now(timezone.utc).timestamp() if now is None else now
        if not isfinite(accuracy) or not isfinite(timestamp) or accuracy<=0 or accuracy>100 or timestamp<now-20 or timestamp>now+5:
            raise ValueError("GPS impreciso ou desatualizado; posição rejeitada")
        with self.lock:
            s=self.session
            if s.state not in {"NAVIGATING","OFF_ROUTE","RECALCULATING"}:
                raise ValueError("Navegação não está ativa")
            if timestamp<=s.latest_fix_timestamp:
                raise ValueError("Leitura GPS repetida ou fora de ordem")
            s.latest_fix_timestamp=timestamp
            s.position={**point,"accuracy":accuracy,"timestamp":timestamp}
            fraction,deviation=route_progress(point,s.route["points"])
            # Accuracy-adjusted threshold and three successive high-quality fixes.
            threshold=max(60,accuracy*2.5)
            s.off_route_fixes = s.off_route_fixes+1 if deviation>threshold else 0
            if s.off_route_fixes>=3:
                s.state="OFF_ROUTE"
                s.reason="Três posições confiáveis consecutivas fora da rota"
                if now-s.last_recalculation>35:
                    s.last_recalculation=now
                    s.state="RECALCULATING"
            else:
                s.state="NAVIGATING"
            steps=s.route["steps"]
            # Forward-only progression: never jump backwards due to noisy GPS.
            for idx in range(s.step_index+1,min(s.step_index+5,len(steps))):
                loc=steps[idx].get("location",[])
                if len(loc)==2 and meters(point,{"lat":loc[1],"lon":loc[0]})<max(25,accuracy*1.5):
                    s.step_index=idx
            next_idx=min(s.step_index+1,len(steps)-1)
            next_step=steps[next_idx]
            loc=next_step.get("location",[])
            remaining=meters(point,{"lat":loc[1],"lon":loc[0]}) if len(loc)==2 else None
            if remaining is not None and remaining<max(30,accuracy*2) and next_step.get("type")=="arrive" and deviation<threshold:
                s.state="ARRIVED"
                s.reason="Posição confiável próxima ao destino indicado pela rota"
            # Publish a new utterance only at distance thresholds.
            if s.state=="NAVIGATING" and remaining is not None:
                stage=("now" if remaining<45 else "approach" if remaining<170 else "advance" if remaining<500 else "")
                key=f"{next_idx}:{stage}" if stage else ""
                if key and key!=s.voice_key:
                    s.voice_key=key
                    s.voice_event_seq+=1
                    s.instructions=[{"step_index":next_idx,"stage":stage,"meters":round(remaining),"maneuver":next_step}]
            result=self.status()
            # Geometry-derived progress is approximate, particularly at crossings.
            # OSRM metrics are the original authoritative route total; this is
            # never called a live traffic ETA.
            result.update({"deviation_m":round(deviation),"next_maneuver_m":round(remaining) if remaining is not None else None,
                           "remaining_distance_m_estimate":round(s.route['distance']*(1-fraction)),
                           "remaining_duration_s_estimate":round(s.route['duration']*(1-fraction))})
            return result

    def replace_route(self, route):
        with self.lock:
            if self.session.state != "RECALCULATING":
                raise ValueError("Recálculo fora de sessão")
            if not route.get("steps") or not route.get("points"):
                raise ValueError("Recálculo incompleto")
            s=self.session
            s.route=route
            s.step_index=s.off_route_fixes=0
            s.voice_key=""
            s.state="NAVIGATING"
            s.reason="Rota recalculada pelo motor local"
            return self.status()

    def reroute_error(self):
        with self.lock:
            self.session.state="OFF_ROUTE"
            self.session.reason="Recálculo indisponível; rota anterior não é orientação válida"
            return self.status()


navigator=NavigationService()
