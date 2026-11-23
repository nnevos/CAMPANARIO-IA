"""R3.20 regression: local provider failure, bounded public fallback, and auto GPS UI."""
import asyncio
from pathlib import Path
import httpx
import pytest
from campanario.app import navigation_v2 as nav

A={"lat":-25.4284,"lon":-49.2733}
B={"lat":-25.4270,"lon":-49.2700}


def test_public_geocoder_after_missing_local(monkeypatch):
    monkeypatch.setenv("CAMPANARIO_MAPS_PUBLIC_FALLBACK", "true")
    called=[]
    async def public(url,**kwargs):
        called.append((url,kwargs['params']['q']))
        return [{"lat":str(B['lat']),"lon":str(B['lon']),"display_name":"Mercado Central, Curitiba, Brasil","type":"supermarket"}]
    monkeypatch.setattr(nav,'_public_json',public)
    class MissingLocal:
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def get(self,*a,**kw):raise httpx.ConnectError('Nominatim offline')
        async def aclose(self):pass
    monkeypatch.setattr(nav.httpx,'AsyncClient',lambda **kw:MissingLocal())
    items=asyncio.run(nav.search_local('Mercado Central',A))
    assert items[0]['provider']=='Nominatim público'
    assert called[0][0]=='https://nominatim.openstreetmap.org/search'
    assert called[0][1]=='Mercado Central'


def test_local_only_option_refuses_public(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_MAPS_PUBLIC_FALLBACK','false')
    async def fail(*args,**kwargs):raise httpx.ConnectError('offline')
    class MissingLocal:
        get=fail
        async def aclose(self):pass
    monkeypatch.setattr(nav.httpx,'AsyncClient',lambda **kw:MissingLocal())
    monkeypatch.setattr(nav,'_public_json',lambda *args,**kwargs:pytest.fail('external query attempted'))
    with pytest.raises(httpx.ConnectError):asyncio.run(nav.search_local('Mercado Central',A))


def test_category_public_fallback(monkeypatch):
    monkeypatch.setenv("CAMPANARIO_MAPS_PUBLIC_FALLBACK", "true")
    async def public(url,**kwargs):
        assert 'overpass-api.de' in url and 'supermarket' in kwargs['data']['data']
        return {'elements':[{'type':'node','id':10,'lat':A['lat'],'lon':A['lon'],'tags':{'name':'Mercado A'}}]}
    monkeypatch.setattr(nav,'_public_json',public)
    class MissingLocal:
        async def post(self,*args,**kwargs):raise httpx.ConnectError('offline')
        async def aclose(self):pass
    monkeypatch.setattr(nav.httpx,'AsyncClient',lambda **kw:MissingLocal())
    items=asyncio.run(nav.nearby_places('mercado mais próximo',A))
    assert items[0]['provider']=='Overpass público'


def test_car_route_public_fallback_with_real_geometry(monkeypatch):
    monkeypatch.setenv("CAMPANARIO_MAPS_PUBLIC_FALLBACK", "true")
    async def public(url,**kwargs):
        assert 'router.project-osrm.org' in url and 'driving' in url
        return {'code':'Ok','routes':[{'distance':600,'duration':80,
                'geometry':{'coordinates':[[A['lon'],A['lat']],[B['lon'],B['lat']]]},
                'legs':[{'steps':[{'name':'Rua B','maneuver':{'type':'turn','location':[B['lon'],B['lat']]}}]}]}]}
    monkeypatch.setattr(nav,'_public_json',public)
    class MissingLocal:
        async def get(self,*a,**k):raise httpx.ConnectError('offline')
        async def aclose(self):pass
    monkeypatch.setattr(nav.httpx,'AsyncClient',lambda **kw:MissingLocal())
    route=asyncio.run(nav.route_from_osrm(A,B))
    assert route['provider'].startswith('OSRM público') and route['distance']==600
    with pytest.raises(httpx.ConnectError):asyncio.run(nav.route_from_osrm(A,B,'walking'))


def test_auto_location_and_no_double_binding():
    base=Path(__file__).resolve().parents[1]/'src/campanario/web/static'
    mapjs=(base/'gps-map.js').read_text()
    navjs=(base/'navigation-v2.js').read_text()
    assert 'startAutoLocation();' in mapjs
    assert "'campanario:location-fix'" in mapjs
    assert "window.addEventListener('campanario:location-fix'" in navjs
    assert "if(!window.CampanarioNavigationV2)document.getElementById('navSearch').onclick" in mapjs
    assert 'clearWatch(locationWatch)' in mapjs
    assert 'getOrigin({precise:true})' in navjs
