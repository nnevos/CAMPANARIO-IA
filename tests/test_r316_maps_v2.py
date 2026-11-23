"""Maps V2 contract tests: real geometry fixtures, fake local HTTP services and GPS trajectories.
No tests claim to be a road test or real sensor verification.
"""
import asyncio
from datetime import datetime, timezone
import json

import httpx
import pytest
from campanario.app.navigation_v2 import (
    NavigationService, coords, meters, route_distance, route_from_osrm,
    resolve_places, category_for, nearby_places, search_local, _loopback_url,
)

A={"lat":-25.4284,"lon":-49.2733}
B={"lat":-25.4270,"lon":-49.2700}


def fixture_route():
    return {"route_id":"local-test", "distance":600.0,"duration":80.0,"mode":"driving",
            "points":[A,B],"steps":[{"type":"depart","location":[A['lon'],A['lat']],"modifier":"","name":"Origem"},
                                      {"type":"turn","modifier":"right","location":[B['lon'],B['lat']],"name":"Rua B"},
                                      {"type":"arrive","location":[B['lon'],B['lat']],"name":"Destino"}]}


def test_route_real_graph_payload(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_MAPS_ROUTER_URL','http://127.0.0.1:5000')
    body={"code":"Ok","routes":[{"distance":600,"duration":80,
           "geometry":{"coordinates":[[A['lon'],A['lat']],[B['lon'],B['lat']]]},
           "legs":[{"steps":[{"name":"Rua B","distance":600,"maneuver":{"type":"turn","modifier":"right","location":[B['lon'],B['lat']]}}]}]}]}
    async def handler(request):
        assert request.url.host=='127.0.0.1'
        assert request.url.path.startswith('/route/v1/driving/')
        assert request.url.params['steps']=='true'
        return httpx.Response(200,json=body)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await route_from_osrm(A,B,client=client)
    result=asyncio.run(run())
    assert result['distance']==600 and result['steps'][0]['name']=='Rua B'
    assert len(result['points'])==2 and not result['traffic_live']


def test_walking_separate_graph(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_MAPS_WALK_ROUTER_URL','http://localhost:5001')
    async def handler(request):
        assert request.url.port==5001 and '/foot/' in request.url.path
        return httpx.Response(200,json={"code":"NoRoute","routes":[]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await route_from_osrm(A,B,'walking',client=client)
    with pytest.raises(ValueError,match='não encontrou'):
        asyncio.run(run())


def test_nearby_local_osm_category(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_MAPS_OVERPASS_URL','http://127.0.0.1:12345')
    async def handler(request):
        assert request.method=='POST' and request.url.host=='127.0.0.1'
        assert b'supermarket' in request.content
        return httpx.Response(200,json={'elements':[{'id':1,'type':'node','lat':A['lat'],'lon':A['lon'],'tags':{'name':'Mercado A'}},
                                                    {'id':2,'type':'way','center':B,'tags':{'name':'Mercado B'}}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await nearby_places('mercado mais próximo',A,client=client)
    items=asyncio.run(run())
    assert len(items)==2 and items[0]['name']=='Mercado A' and items[0]['air_distance_m']==0
    assert category_for('farmácia aberta')==('amenity','pharmacy')
    assert category_for('aeroporto de Guarulhos') is None


def test_named_search_context(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_MAPS_GEOCODER_URL','http://localhost:8088')
    async def handler(request):
        assert request.url.params.get('viewbox') and request.url.params['limit']=='8'
        assert request.url.params.get('bounded') is None
        return httpx.Response(200,json=[{"lat":str(B['lat']),"lon":str(B['lon']),"display_name":"Mercado Central, Paraná","type":"supermarket"}])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await search_local('Mercado Central',A,client=client)
    assert asyncio.run(run())[0]['name'].startswith('Mercado')


def test_reject_remote_provider_url(monkeypatch):
    for value in ['https://example.com','http://example.com:5000','http://localhost:5000/userinfo','http://user@localhost:5000','file:///tmp/a']:
        monkeypatch.setenv('CAMPANARIO_MAPS_ROUTER_URL',value)
        with pytest.raises(ValueError):_loopback_url('CAMPANARIO_MAPS_ROUTER_URL','')


def test_resolution_ambiguity_and_nearby():
    nearby=[{**A,"name":"Mercado A"},{**B,"name":"Mercado B"}]
    assert resolve_places(nearby,'Mercado',A)['needs_confirmation']
    assert resolve_places(nearby[:1],'Mercado',A)['selected']['name']=='Mercado A'
    far={"lat":40,"lon":-70,"name":"Mercado"}
    assert not resolve_places([far],'Mercado',A)['candidates']
    assert resolve_places([far],'Mercado',A,explicit_distant=True)['candidates']


def test_distance_and_no_extrapolation():
    assert meters(A,A)==0
    assert 100<meters(A,B)<500
    assert route_distance(A,[A,B])<1
    assert route_distance({"lat":-25.45,"lon":-49.3},[A,B])>1000
    for bad in [(91,0),(0,181),('bad',2)]:
        with pytest.raises(ValueError):coords(*bad)


def test_state_transitions():
    n=NavigationService()
    with pytest.raises(ValueError): n.command('start')
    assert n.ready(fixture_route(),B)['state']=='READY'
    assert n.command('start')['state']=='NAVIGATING'
    assert n.command('pause')['state']=='PAUSED'
    assert n.command('resume')['state']=='NAVIGATING'
    assert n.command('stop')['state']=='STOPPED'
    assert n.status()['route'] is None
    with pytest.raises(ValueError):n.command('resume')


def test_gps_quality_freshness_and_nonrepeating():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    for lat,lon,accuracy,stamp in [(A['lat'],A['lon'],150,1000),(A['lat'],A['lon'],10,970),(A['lat'],A['lon'],10,1006)]:
        with pytest.raises(ValueError):n.position_fix(lat,lon,accuracy,stamp,now=1000)
    n.position_fix(A['lat'],A['lon'],10,1000,now=1000)
    with pytest.raises(ValueError):n.position_fix(A['lat'],A['lon'],10,1000,now=1000)


def test_no_offroute_on_single_bad_reading():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    other={"lat":-25.45,"lon":-49.3}
    first=n.position_fix(**other,accuracy=8,timestamp=1000,now=1000)
    assert first['state']=='NAVIGATING' and first['off_route_fixes']==1
    second=n.position_fix(**A,accuracy=8,timestamp=1001,now=1001)
    assert second['state']=='NAVIGATING' and second['off_route_fixes']==0


def test_confirmed_deviation_reroute_and_failure():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    other={"lat":-25.45,"lon":-49.3}
    for i in range(3):
        value=n.position_fix(**other,accuracy=8,timestamp=1000+i,now=1000+i)
    assert value['state']=='RECALCULATING'
    assert n.replace_route(fixture_route())['state']=='NAVIGATING'
    assert n.status()['off_route_fixes']==0
    # Failure keeps the old route but labels it unsuitable for guidance.
    n.session.state='RECALCULATING'
    assert n.reroute_error()['state']=='OFF_ROUTE'


def test_arrival_not_fake():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    far=n.position_fix(**A,accuracy=5,timestamp=1000,now=1000)
    assert far['state']!='ARRIVED'
    at=n.position_fix(**B,accuracy=5,timestamp=1001,now=1001)
    assert at['state']=='ARRIVED'


def test_voice_events_not_repeated():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    value=n.position_fix(**A,accuracy=5,timestamp=1000,now=1000)
    k=value['voice_event_seq']
    value=n.position_fix(**A,accuracy=5,timestamp=1001,now=1001)
    assert value['voice_event_seq']==k


def test_no_persistent_location_after_stop():
    n=NavigationService();n.ready(fixture_route(),B);n.command('start')
    n.position_fix(**A,accuracy=5,timestamp=1000,now=1000)
    assert n.status()['position'] is not None
    n.command('stop')
    assert n.status()['position'] is None


def test_http_navigation_lifecycle(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.main import app
    from campanario.app import api as app_api
    async def route(*args,**kwargs):return fixture_route()
    monkeypatch.setattr(app_api,'route_from_osrm',route)
    app_api.maps_v2_session.command('stop')
    client=TestClient(app)
    r=client.post('/api/app/navigation/v2/route',json={
        'start_lat':A['lat'],'start_lon':A['lon'],'end_lat':B['lat'],'end_lon':B['lon'],
        'destination_name':'Destino confirmado','mode':'driving'})
    assert r.status_code==200,r.text
    assert r.json()['state']=='READY' and r.json()['target']['name']=='Destino confirmado'
    assert client.post('/api/app/navigation/v2/command/start').status_code==200
    assert client.get('/api/app/navigation/v2/status').json()['state']=='NAVIGATING'
    assert client.post('/api/app/navigation/v2/command/pause').json()['state']=='PAUSED'
    assert client.post('/api/app/navigation/v2/command/resume').json()['state']=='NAVIGATING'
    assert client.post('/api/app/navigation/v2/command/stop').json()['state']=='STOPPED'
    assert client.get('/api/app/navigation/v2/status').json()['route'] is None


def test_http_invalid_fix_and_private_boundary(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.main import app
    client=TestClient(app)
    assert client.post('/api/app/navigation/v2/command/delete-all').status_code==404
    remote=TestClient(app,base_url='http://public.example.org')
    assert remote.get('/api/app/navigation/v2/status').status_code==403
    assert client.post('/api/app/navigation/v2/fix',json={
        'lat':A['lat'],'lon':A['lon'],'accuracy':10,'timestamp':0}).status_code==422


def test_http_category_requires_real_overpass(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.main import app
    from campanario.app import api as app_api
    async def fake_places(q,near):
        assert near==A
        return [{**A,'name':'Mercado A','air_distance_m':0},{**B,'name':'Mercado B','air_distance_m':380}]
    async def fake_route(start,end,mode):
        route=fixture_route()
        route['distance']=500 if end['lat']==A['lat'] else 1100
        return route
    monkeypatch.setattr(app_api,'nearby_places',fake_places)
    monkeypatch.setattr(app_api,'route_from_osrm',fake_route)
    result=TestClient(app).post('/api/app/navigation/v2/resolve',json={
        'query':'mercado mais próximo','near_lat':A['lat'],'near_lon':A['lon']})
    assert result.status_code==200,result.text
    assert result.json()['selected']['name']=='Mercado A'
    assert result.json()['ranking'].startswith('distância por rota real')


def test_http_nearby_ambiguity_requires_choice(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.main import app
    from campanario.app import api as app_api
    async def fake_places(q,near):return [{**A,'name':'Mercado A','air_distance_m':0},{**B,'name':'Mercado B','air_distance_m':380}]
    async def fake_route(start,end,mode):
        r=fixture_route()
        r['distance']=500 if end['lat']==A['lat'] else 510
        return r
    monkeypatch.setattr(app_api,'nearby_places',fake_places)
    monkeypatch.setattr(app_api,'route_from_osrm',fake_route)
    result=TestClient(app).post('/api/app/navigation/v2/resolve',json={
        'query':'mercado mais próximo','near_lat':A['lat'],'near_lon':A['lon']}).json()
    assert result['ambiguous'] and result['selected'] is None


def test_ui_maps_v2_loaded():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'src/campanario/web/index.html').read_text()
    js=(root/'src/campanario/web/static/navigation-v2.js').read_text()
    map_js=(root/'src/campanario/web/static/gps-map.js').read_text()
    workspace=(root/'src/campanario/web/static/workspaces.js').read_text()
    assert 'navigation-v2.js?v=' in html
    assert 'CampanarioNavigationV2?.bindUI()' in map_js
    assert 'mapsV2Mode' in workspace
    assert 'mapsOnlineTiles' in workspace
    assert 'campanario:navigation-request' in js
    assert 'watchPosition' in js and 'window.speechSynthesis' in js


def test_mobile_maps_https_paired_sessions(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.app.remote import create_companion_app
    from campanario.companion import api as mobile_api
    from campanario.companion import store as store_module
    # A test-only identity substitute exercises the existing protected boundary.
    def authenticate(token):
        if token=='a'*40:return {'id':'device-a','chat':True}
        if token=='b'*40:return {'id':'device-b','chat':True}
        raise PermissionError('not paired')
    # Replace only the store factory in the companion API.
    class FakeStore: pass
    fake=FakeStore()
    fake.authenticate=authenticate
    monkeypatch.setattr(mobile_api,'get_store',lambda:fake)
    async def fake_route(*args,**kwargs):return fixture_route()
    monkeypatch.setattr(mobile_api,'maps_route',fake_route)
    client=TestClient(create_companion_app(),base_url='https://testserver')
    ha={'Authorization':'Bearer '+'a'*40}
    hb={'Authorization':'Bearer '+'b'*40}
    route_body={'start_lat':A['lat'],'start_lon':A['lon'],'end_lat':B['lat'],'end_lon':B['lon'],'name':'Destino A'}
    a=client.post('/api/companion/v1/maps/v2/route',json=route_body,headers=ha)
    assert a.status_code==200,a.text
    assert a.json()['state']=='READY'
    assert client.get('/api/companion/v1/maps/v2/status',headers=hb).json()['state']=='IDLE'
    assert client.get('/api/companion/v1/maps/v2/status',headers=ha).json()['target']['name']=='Destino A'
    assert client.post('/api/companion/v1/maps/v2/command/start',headers=ha).json()['state']=='NAVIGATING'
    assert client.post('/api/companion/v1/maps/v2/command/stop',headers=ha).json()['state']=='STOPPED'


def test_mobile_maps_requires_pairing_https(monkeypatch):
    from fastapi.testclient import TestClient
    from campanario.app.remote import create_companion_app
    https=TestClient(create_companion_app(),base_url='https://testserver')
    http=TestClient(create_companion_app(),base_url='http://testserver')
    assert https.get('/api/companion/v1/maps/v2/status').status_code==401
    assert http.get('/api/companion/v1/maps/v2/status').status_code==403


def test_mobile_maps_ui_and_native_voice_contract():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'apps/mobile/www/index.html').read_text()
    js=(root/'apps/mobile/www/app.mjs').read_text()
    java=(root/'apps/mobile/android/app/src/main/java/org/campanario/mobile/MainActivity.java').read_text()
    assert 'mobileMapsDestination' in html and 'mobileMapsPlot' in html
    assert "request(state.connection,'maps/v2/route'" in js
    assert 'mapsTimer=setInterval(mapsLoop,5000)' in js
    assert 'speakInstruction' in java and 'TextToSpeech' in java
    assert 'onDestroy()' in java and 'navigationSpeech.shutdown()' in java
