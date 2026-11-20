from pathlib import Path
import json
from campanario.utilities.service import UtilityService


def call(u, tool, **args):
    return u.run(tool, args)

def test_persistence_and_confirmation(tmp_path):
    u=UtilityService(tmp_path/'data')
    assert call(u,'notes.save',title='nota')['status']=='failed'
    result=call(u,'notes.save',title='nota',content='offline',confirm=True)
    assert result['status']=='success'
    assert UtilityService(tmp_path/'data').run('notes.list',{'query':'offline'})['result']['count']==1
    assert call(u,'tasks.save',title='tarefa',status='todo',priority='alta',confirm=True)['status']=='success'
    assert UtilityService(tmp_path/'data').run('tasks.list',{})['result']['count']==1


def test_files_scope_and_trash(tmp_path):
    u=UtilityService(tmp_path/'data');root=u.roots[0];(root/'texto.txt').write_text('material offline')
    assert call(u,'files.read',path=str(root/'texto.txt'))['status']=='success'
    assert call(u,'files.read',path=str(tmp_path/'fora.txt'))['status']=='failed'
    assert call(u,'files.read',path=str(root/'..'/'utilidades.sqlite3'))['status']=='failed'
    assert call(u,'files.find_text',path=str(root),query='offline')['result']['matches']
    assert call(u,'files.delete',path=str(root/'texto.txt'),confirm=True)['result']['reversible']
    assert not (root/'texto.txt').exists()


def test_library_search_duplicate_and_backup(tmp_path):
    u=UtilityService(tmp_path/'data');root=u.roots[0];p=root/'manual.md';p.write_text('Seção um. Conteúdo consultável offline.','utf-8')
    result=call(u,'library.import',path=str(p),category='manual',confirm=True)
    assert result['result']['imported']
    assert call(u,'library.import',path=str(p),confirm=True)['result']['duplicate_id']==result['result']['id']
    hit=call(u,'library.search',query='consultável')['result']['documents'][0]
    assert 'consultável' in hit['matches'][0]['excerpt']
    backup=call(u,'backup.create')['result']['path']
    assert call(u,'backup.verify',filename=Path(backup).name)['result']['valid']
    call(u,'notes.save',title='depois do backup',confirm=True)
    assert call(u,'backup.restore',filename=Path(backup).name)['status']=='failed'
    assert call(u,'backup.restore',filename=Path(backup).name,confirm=True)['result']['restored']
    assert UtilityService(tmp_path/'data').run('notes.list',{})['result']['count']==0


def test_math_and_routines(tmp_path):
    u=UtilityService(tmp_path/'data')
    assert call(u,'calc.evaluate',expression='(2+3)*4')['result']['result']==20
    assert call(u,'calc.evaluate',expression='__import__("os")')['status']=='failed'
    assert call(u,'calc.electricity',watts=100,hours_per_day=10,days=30)['result']['kwh']==30
    assert call(u,'calc.battery',capacity_wh=100,load_watts=50)['result']['hours']==1.7
    routine=call(u,'routines.save',title='rotina',steps=[{'tool':'notes.save','arguments':{'title':'rotina executada'}}],confirm=True)['result']['id']
    assert call(u,'routines.run',id=routine,confirm=True)['result']['completed']
    assert call(u,'notes.list',query='rotina executada')['result']['count']==1
    assert call(u,'diagnostics.system')['result']['disk']['total']>0


def test_failed_backup_and_offline_no_model(tmp_path,monkeypatch):
    u=UtilityService(tmp_path/'data')
    root=u.roots[0]
    (root/'a.txt').write_text('offline sem modelo')
    assert call(u,'library.import',path=str(root/'a.txt'),confirm=True)['status']=='success'
    assert call(u,'library.search',query='sem modelo')['result']['count']==1
    invalid=(u.base/'backups'/'bad.zip')
    invalid.parent.mkdir(parents=True)
    invalid.write_bytes(b'not a zip')
    assert call(u,'backup.verify',filename='bad.zip')['status']=='failed'
    assert call(u,'backup.restore',filename='bad.zip',confirm=True)['status']=='failed'


def test_api_utilities_page_and_loopback(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from campanario.main import app
    import campanario.utilities.api as module
    monkeypatch.setattr(module,'service',lambda:UtilityService(tmp_path/'data'))
    client=TestClient(app)
    assert client.get('/ferramentas').status_code==200
    catalog=client.get('/api/v1/utilities/catalog')
    assert catalog.status_code==200 and len(catalog.json())>30
    result=client.post('/api/v1/utilities/invoke',json={'tool':'calc.evaluate','arguments':{'expression':'5**2'}})
    assert result.status_code==200 and result.json()['result']['result']==25
    assert client.post('/api/v1/utilities/invoke',json={'tool':'notes.save','arguments':{'title':'sem confirmar'}}).json()['status']=='failed'
    assert client.post('/api/v1/utilities/invoke',headers={'Origin':'https://example.com'},json={'tool':'notes.list','arguments':{}}).status_code==403
