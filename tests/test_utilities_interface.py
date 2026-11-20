"""HTTP/UI integration contract for the human-facing Campanario tools."""
import base64
from fastapi.testclient import TestClient
from campanario.main import app
from campanario.utilities.service import UtilityService


def test_ui_pages_and_state(monkeypatch, tmp_path):
    import campanario.utilities.api as backend
    util=UtilityService(tmp_path/'utilities')
    monkeypatch.setattr(backend, 'service', lambda: util)
    client=TestClient(app)
    assert client.get('/ferramentas').status_code==200
    html=client.get('/ferramentas').text
    assert 'id="modules"' in html and 'id="view"' in html
    js=client.get('/ferramentas.js')
    assert js.status_code==200 and 'views.biblioteca' in js.text
    css=client.get('/ferramentas.css')
    assert css.status_code==200 and '.sidebar' in css.text
    status=client.get('/api/v1/utilities/status').json()
    assert status['authorized_roots']==[str(util.roots[0])]
    assert status['model_required'] is False
    assert any(x['id']=='backup.list' for x in client.get('/api/v1/utilities/catalog').json())


def test_browser_upload_then_import_delete_and_backup(monkeypatch,tmp_path):
    import campanario.utilities.api as backend
    util=UtilityService(tmp_path/'utilities')
    monkeypatch.setattr(backend,'service',lambda:util)
    client=TestClient(app)
    data={'filename':'teste.md','content_base64':base64.b64encode('Fonte local. Texto da biblioteca.'.encode()).decode()}
    p=client.post('/api/v1/utilities/upload',json=data)
    assert p.status_code==200 and (util.roots[0]/'teste.md').is_file()
    assert client.post('/api/v1/utilities/upload',json=data).status_code==409
    assert client.post('/api/v1/utilities/upload',json={**data,'filename':'../invasao.md'}).status_code==400
    assert client.post('/api/v1/utilities/upload',json={**data,'filename':'comando.exe'}).status_code==400
    def action(tool,arguments):
        r=client.post('/api/v1/utilities/invoke',json={'tool':tool,'arguments':arguments})
        assert r.status_code==200
        return r.json()
    doc=action('library.import',{'path':p.json()['path'],'category':'manual','confirm':True})
    assert doc['status']=='success'
    assert action('library.search',{'query':'Fonte local'})['result']['count']==1
    emergency=action('emergency.save',{'title':'Contato','category':'contact','confirm':True})
    assert emergency['status']=='success'
    uid=emergency['result']['id']
    assert action('emergency.delete',{'id':uid})['status']=='failed'
    assert action('emergency.delete',{'id':uid,'confirm':True})['result']['deleted']
    backup=action('backup.create',{})
    assert backup['status']=='success'
    assert action('backup.list',{})['result']['items']
    assert action('backup.verify',{'filename':backup['result']['path'].split('/')[-1]})['result']['valid']
