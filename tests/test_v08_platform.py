"""v0.8 platform tests. No real credentials, models, LAN or user databases."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import json
import sqlite3
import time
import pytest
from fastapi.testclient import TestClient
from campanario.companion.store import CompanionStore, Conflict
from campanario.app.remote import create_companion_app
from campanario.app.security import LocalOnlyBoundary
from campanario.app.updates import version_tuple
from campanario.app.instance import InstanceLock
from campanario.app.schema import prepare_schema, backup_sqlite
from campanario.config import Settings


@pytest.fixture
def store(tmp_path):
    return CompanionStore(tmp_path / 'companion.db')


def paired(store, chat=False):
    code = store.create_pair_code('Test phone', chat)
    return store.redeem(code['code'])


def mutation(**kw):
    return {'id': str(uuid4()), 'mutation_id': str(uuid4()), 'base_revision': 0,
            'title': 'Offline', 'body': 'My note', 'deleted': False, **kw}


def test_pair_code_single_use(store):
    code=store.create_pair_code('Phone')
    result=store.redeem(code['code'])
    assert store.authenticate(result['token'])['id']==result['device_id']
    with pytest.raises(PermissionError):store.redeem(code['code'])


def test_expired_pair_code_denied(store):
    code=store.create_pair_code('Phone')
    with store.connect() as db:db.execute('UPDATE pair_codes SET expires=?',(time.time()-1,))
    with pytest.raises(PermissionError):store.redeem(code['code'])


def test_secrets_not_persisted(store):
    code=store.create_pair_code('Phone');result=store.redeem(code['code'])
    raw=store.path.read_bytes()
    assert code['code'].encode() not in raw
    assert result['token'].encode() not in raw


def test_concurrent_pair_code_can_only_be_redeemed_once(store):
    code=store.create_pair_code('Phone')['code']
    def attempt(_):
        try:store.redeem(code);return True
        except PermissionError:return False
    with ThreadPoolExecutor(4) as pool:assert sum(pool.map(attempt, range(4)))==1


def test_device_revocation(store):
    device=paired(store);store.revoke(device['device_id'])
    with pytest.raises(PermissionError):store.authenticate(device['token'])
    with pytest.raises(PermissionError):store.sync_notes(device['device_id'],[])


def test_snapshot_is_device_scoped_and_opt_in(store):
    a,b=paired(store),paired(store)
    assert store.snapshot(a['device_id'])['items']==[]
    store.publish(a['device_id'],[{'id':'a','title':'Selected','text':'private'}])
    assert store.snapshot(b['device_id'])['items']==[]
    assert store.snapshot(a['device_id'])['items'][0]['text']=='private'
    store.publish(a['device_id'],[])
    assert store.snapshot(a['device_id'])['revision']==2
    assert store.snapshot(a['device_id'])['items']==[]


def test_snapshot_size_limit(store):
    device=paired(store)
    with pytest.raises(ValueError):store.publish(device['device_id'],[{'text':'x'*2_000_001}])


def test_note_idempotency(store):
    device=paired(store)['device_id'];m=mutation()
    first=store.sync_notes(device,[m]);second=store.sync_notes(device,[m])
    assert first==second
    assert second['notes'][0]['revision']==1


def test_idempotency_key_cannot_change_content(store):
    device=paired(store)['device_id'];m=mutation();store.sync_notes(device,[m])
    with pytest.raises(Conflict):store.sync_notes(device,[{**m,'body':'different'}])


def test_note_conflicts_preserve_server_version(store):
    device=paired(store)['device_id'];m=mutation();store.sync_notes(device,[m])
    clash={**m,'mutation_id':str(uuid4()),'body':'offline edit','base_revision':0}
    response=store.sync_notes(device,[clash])
    assert response['results'][0]['status']=='conflict'
    assert response['notes'][0]['body']=='My note'


def test_deleted_note_is_not_resurrected_by_stale_device(store):
    device=paired(store)['device_id'];m=mutation();store.sync_notes(device,[m])
    deleted={**m,'mutation_id':str(uuid4()),'base_revision':1,'deleted':True,'body':''}
    store.sync_notes(device,[deleted])
    stale={**m,'mutation_id':str(uuid4()),'base_revision':1,'body':'old'}
    response=store.sync_notes(device,[stale])
    assert response['results'][0]['status']=='conflict'
    assert response['notes'][0]['deleted']==1


def test_notes_scoped_to_device(store):
    a,b=paired(store)['device_id'],paired(store)['device_id']
    m=mutation();store.sync_notes(a,[m])
    assert store.sync_notes(b,[])['notes']==[]


def test_sessions_have_owner(store):
    a,b=paired(store)['device_id'],paired(store)['device_id'];sid=str(uuid4());client=str(uuid4())
    assert store.session(a,client,lambda:sid)==sid
    assert store.session(a,client,lambda:pytest.fail('duplicate session'))==sid
    assert store.owns_session(a,sid)
    assert not store.owns_session(b,sid)


def test_turn_retries_never_run_twice(store):
    device=paired(store)['device_id'];rid=str(uuid4());payload={'session':'x','message':'hi'}
    assert store.begin_turn(device,rid,payload)['state']=='new'
    assert store.begin_turn(device,rid,payload)['state']=='pending'
    store.finish_turn(device,rid,'done',{'messages':['hello']})
    assert store.begin_turn(device,rid,payload)['result']=={'messages':['hello']}
    with pytest.raises(Conflict):store.begin_turn(device,rid,{'message':'other'})


@pytest.fixture
def remote(store, monkeypatch):
    monkeypatch.setattr('campanario.companion.api.get_store',lambda:store)
    return TestClient(create_companion_app(),base_url='https://testserver')


def auth(token):return {'Authorization':'Bearer '+token}


def test_mobile_requires_https_even_with_valid_token(store):
    dev=paired(store)
    with TestClient(create_companion_app(),base_url='http://testserver') as client:
        assert client.get('/api/companion/v1/status',headers=auth(dev['token'])).status_code==403


def test_unauthenticated_mobile_denied(remote):
    assert remote.get('/api/companion/v1/snapshot').status_code==401


def test_remote_does_not_expose_legacy_admin_routes(remote):
    assert remote.get('/api/v1/memory').status_code==404
    assert remote.get('/api/app/devices').status_code==404
    assert remote.get('/docs').status_code==404


def test_mobile_pair_end_to_end(remote,store):
    code=store.create_pair_code('Phone')['code']
    response=remote.post('/api/companion/v1/pair',json={'code':code})
    assert response.status_code==200
    payload=response.json()
    status=remote.get('/api/companion/v1/status',headers=auth(payload['token']))
    assert status.json()['chat_allowed'] is False


def test_pair_rate_limit(remote):
    from campanario.companion.api import _attempts
    _attempts.clear()
    for _ in range(10):assert remote.post('/api/companion/v1/pair',json={'code':'invalid'*5}).status_code==401
    assert remote.post('/api/companion/v1/pair',json={'code':'invalid'*5}).status_code==429
    _attempts.clear()


def test_mobile_cors_only_bundled_origin(remote):
    ok=remote.options('/api/companion/v1/status',headers={'Origin':'https://appassets.androidplatform.net','Access-Control-Request-Method':'GET'})
    assert ok.headers['access-control-allow-origin']=='https://appassets.androidplatform.net'
    bad=remote.options('/api/companion/v1/status',headers={'Origin':'https://evil.example','Access-Control-Request-Method':'GET'})
    assert 'access-control-allow-origin' not in bad.headers


def test_remote_payload_size_limit(remote):
    response=remote.post('/api/companion/v1/pair',content=b'x'*2_000_001)
    assert response.status_code==413


def test_mobile_note_sync_http(remote,store):
    dev=paired(store);m=mutation()
    response=remote.post('/api/companion/v1/notes/sync',headers=auth(dev['token']),json={'mutations':[m]})
    assert response.status_code==200
    assert response.json()['results'][0]['status']=='accepted'


def test_chat_permission_is_explicit(remote,store):
    dev=paired(store)
    response=remote.post('/api/companion/v1/sessions',headers=auth(dev['token']),json={'client_id':str(uuid4())})
    assert response.status_code==403


def test_mobile_session_uses_actual_chat_signature(remote,store,monkeypatch):
    dev=paired(store,chat=True);sid=uuid4()
    class Conversation:
        def create_session(self,title=None,agent_id=None):
            assert agent_id=='morgana'
            return SimpleNamespace(id=sid)
    monkeypatch.setattr('campanario.bootstrap.get_runtime',lambda:SimpleNamespace(conversation=Conversation()))
    body={'client_id':str(uuid4())}
    response=remote.post('/api/companion/v1/sessions',headers=auth(dev['token']),json=body)
    assert response.status_code==200
    assert response.json()['id']==str(sid)
    assert remote.post('/api/companion/v1/sessions',headers=auth(dev['token']),json=body).json()==response.json()


def test_mobile_cannot_read_other_session(remote,store):
    dev=paired(store,chat=True)
    assert remote.get(f'/api/companion/v1/sessions/{uuid4()}/messages',headers=auth(dev['token'])).status_code==404


@pytest.mark.parametrize('headers',[
    {'Host':'evil.example'}, {'Origin':'https://evil.example'},
    {'X-Forwarded-For':'10.0.0.5'}, {'Forwarded':'for=10.0.0.5'},
    {'X-Forwarded-Host':'public.example'},
])
def test_local_boundary_blocks_cross_site_and_proxy(headers):
    from campanario.main import app
    assert TestClient(app).get('/api/app/devices',headers=headers).status_code==403


def test_local_boundary_denies_remote_peer():
    from campanario.app.security import local_request
    assert not local_request({'client':('192.168.1.20',10),'headers':[(b'host',b'127.0.0.1:8000')]})


def test_lock_never_kills_existing_process(tmp_path):
    a=InstanceLock(tmp_path/'lock').acquire()
    try:
        with pytest.raises(RuntimeError):InstanceLock(tmp_path/'lock').acquire()
    finally:a.release()
    InstanceLock(tmp_path/'lock').acquire().release()


def test_schema_only_upgrades_if_needed(tmp_path):
    settings=Settings(data_dir=tmp_path,semantic_memory_enabled=False,_env_file=None)
    first=prepare_schema(settings)
    assert first['changed']
    with sqlite3.connect(settings.database_path) as con:
        con.execute('CREATE TABLE sentinel(value TEXT)');con.execute("INSERT INTO sentinel VALUES('keep')")
    second=prepare_schema(settings)
    assert not second['changed']
    with sqlite3.connect(settings.database_path) as con:assert con.execute('SELECT value FROM sentinel').fetchone()==('keep',)


def test_sqlite_backup_keeps_content(tmp_path):
    source=tmp_path/'source.db';backup=tmp_path/'backups/copy.db'
    with sqlite3.connect(source) as con:con.execute('CREATE TABLE x(value TEXT)');con.execute("INSERT INTO x VALUES('private')")
    backup_sqlite(source,backup)
    with sqlite3.connect(backup) as con:assert con.execute('SELECT value FROM x').fetchone()==('private',)


@pytest.mark.parametrize('value,expected',[('v0.8.0',(0,8,0)),('1.10.2',(1,10,2))])
def test_release_semver(value,expected):assert version_tuple(value)==expected


@pytest.mark.parametrize('value',['main','v0.8.0-beta','../../evil','0.8','0.8.0;rm'])
def test_release_rejects_unstable_or_invalid_tag(value):
    with pytest.raises(ValueError):version_tuple(value)


def test_legacy_implementation_not_on_active_import_path():
    root=Path(__file__).resolve().parents[1]
    assert not (root/'voice').exists()
    assert not (root/'src/campanario/renpy_factory').exists()
    assert not (root/'src/campanario/runtime/host_voice.py').exists()
    assert 'uv sync' not in (root/'src/campanario/app/desktop.py').read_text()
    assert 'taskkill' not in (root/'CAMPANARIO.bat').read_text()


def test_future_audio_provider_is_explicitly_unconfigured():
    from campanario.modules.audio import build_voice_media
    media=build_voice_media(Settings(_env_file=None))
    assert media is not None


def test_frontend_is_local_and_modular():
    from campanario.main import app
    client=TestClient(app)
    html=client.get('/').text
    assert '/static/chat.js' in html
    assert 'localStorage.removeItem' in client.get('/static/chat.js').text
    assert 'server.url' not in (Path('apps/mobile/android/app/src/main/java/org/campanario/mobile/MainActivity.java').read_text())
    assert 'setAllowFileAccess(false)' in Path('apps/mobile/android/app/src/main/java/org/campanario/mobile/MainActivity.java').read_text()


@pytest.fixture
def real_mobile_chat(remote,store,monkeypatch):
    from test_api_chat import InMemorySessions, InMemoryMessages
    from campanario.chat.context import RecentMessagesContextManager
    from campanario.chat.service import ChatService
    from campanario.model.protocol import FakeModelProvider
    service=ChatService(InMemorySessions(),InMemoryMessages(),FakeModelProvider("Resposta de teste"),RecentMessagesContextManager(20),"fake")
    runtime=SimpleNamespace(conversation=service)
    monkeypatch.setattr('campanario.bootstrap.get_runtime',lambda:runtime)
    monkeypatch.setattr('campanario.api.get_runtime',lambda:runtime)
    dev=paired(store,chat=True)
    sid=remote.post('/api/companion/v1/sessions',headers=auth(dev['token']),json={'client_id':str(uuid4())}).json()['id']
    return remote,dev,sid


def test_mobile_turn_uses_real_chat_and_retry_does_not_duplicate(real_mobile_chat):
    remote,dev,sid=real_mobile_chat;headers=auth(dev['token'])
    body={'request_id':str(uuid4()),'message':'Ola'}
    first=remote.post(f'/api/companion/v1/sessions/{sid}/turn',headers=headers,json=body)
    assert first.status_code==200,first.text
    assert [m['content'] for m in first.json()['messages']]==['Ola','Resposta de teste']
    second=remote.post(f'/api/companion/v1/sessions/{sid}/turn',headers=headers,json=body)
    assert second.json()==first.json()
    assert len(remote.get(f'/api/companion/v1/sessions/{sid}/messages',headers=headers).json())==2
    assert remote.get('/api/companion/v1/turns/'+body['request_id'],headers=headers).json()['state']=='done'


def test_mobile_turn_request_id_cannot_change_payload(real_mobile_chat):
    remote,dev,sid=real_mobile_chat;headers=auth(dev['token'])
    body={'request_id':str(uuid4()),'message':'Ola'}
    assert remote.post(f'/api/companion/v1/sessions/{sid}/turn',headers=headers,json=body).status_code==200
    body['message']='Mensagem diferente'
    assert remote.post(f'/api/companion/v1/sessions/{sid}/turn',headers=headers,json=body).status_code==409


def test_revoked_device_cannot_recover_chat(real_mobile_chat,store):
    remote,dev,sid=real_mobile_chat
    store.revoke(dev['device_id'])
    assert remote.get(f'/api/companion/v1/sessions/{sid}/messages',headers=auth(dev['token'])).status_code==401


def test_schema_failure_preserves_unknown_database_and_backup(tmp_path):
    settings=Settings(data_dir=tmp_path,semantic_memory_enabled=False,_env_file=None)
    settings.database_path.parent.mkdir(parents=True)
    with sqlite3.connect(settings.database_path) as con:
        con.execute('CREATE TABLE alembic_version(version_num TEXT)')
        con.execute("INSERT INTO alembic_version VALUES('unknown_revision')")
        con.execute('CREATE TABLE private_note(body TEXT)')
        con.execute("INSERT INTO private_note VALUES('Preserve this')")
    with pytest.raises(Exception):prepare_schema(settings)
    with sqlite3.connect(settings.database_path) as con:
        assert con.execute('SELECT body FROM private_note').fetchone()[0]=='Preserve this'
    backups=list((settings.database_path.parent/'backups').glob('*.db'))
    assert len(backups)==1
    with sqlite3.connect(backups[0]) as con:
        assert con.execute('SELECT body FROM private_note').fetchone()[0]=='Preserve this'
