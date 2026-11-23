"""R3.15 source-only regression: chat attachment, library, provenance and management."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

import campanario.utilities.api as utilities_api
from campanario.main import app
from campanario.utilities.service import UtilityService
from campanario.chat.document_intent import document_request, search_document


def fixture_util(tmp_path):
    return UtilityService(tmp_path / 'utility')


def ingest(util, name, text):
    path = util.roots[0] / name
    path.write_text(text, encoding='utf-8')
    output = util.run('library.import', {'path': str(path), 'confirm': True})
    assert output['status'] == 'success', output
    return output['result']['id']


def test_upload_chat_indexes_same_database_used_by_chat(tmp_path, monkeypatch):
    util = fixture_util(tmp_path)
    monkeypatch.setattr(utilities_api, 'service', lambda: util)
    monkeypatch.setattr('campanario.config.get_settings',
                        lambda: SimpleNamespace(brains_v9_enabled=True, local_personal_mode=True))
    client = TestClient(app)
    data = 'Criatura de Morte: a mais forte deste texto fictício é a Sentinela da Névoa.'
    response = client.post('/api/v1/utilities/upload-stream?filename=Ordem%20Paranormal%20Exemplo.txt&index=true',
                           content=data.encode('utf-8'),
                           headers={'Content-Type':'application/octet-stream'})
    assert response.status_code == 200, response.text
    output = response.json()
    assert output['indexed'] and output['document_id']
    assert util.run('library.list', {})['result']['count'] == 1
    intent = document_request('procure no arquivo relacionado a ordem paranormal e me diga a criatura de morte mais forte', [])
    assert intent and intent.hint == 'ordem paranormal'
    sheet = search_document(util.db, intent)
    assert sheet and 'Sentinela da Névoa' in sheet.quote.excerpt
    assert sheet.quote.name.endswith('Exemplo.txt')


def test_upload_does_not_claim_index_on_invalid_text(tmp_path, monkeypatch):
    util=fixture_util(tmp_path)
    monkeypatch.setattr(utilities_api, 'service', lambda: util)
    monkeypatch.setattr('campanario.config.get_settings',
                        lambda: SimpleNamespace(brains_v9_enabled=True, local_personal_mode=True))
    client=TestClient(app)
    response=client.post('/api/v1/utilities/upload-stream?filename=quebrado.json&index=true',
                         content=b'{broken json', headers={'content-type':'application/octet-stream'})
    assert response.status_code == 200
    data=response.json()
    assert data['indexed'] is False and data['index_error']
    assert (util.roots[0]/'quebrado.json').is_file()
    info=util.run('library.list', {})['result']
    assert info['count']==1 and info['documents'][0]['state']=='error'


def test_rename_preserves_original_and_searches_new_name(tmp_path):
    util=fixture_util(tmp_path)
    uid=ingest(util, 'Exemplo.txt', 'O registro afirma que a porta está aberta.')
    original=util.docs/(uid+'.txt')
    before=original.read_bytes()
    renamed=util.run('library.rename', {'id':uid,'name':'Ordem Paranormal.txt','confirm':True})
    assert renamed['status']=='success'
    assert original.read_bytes()==before
    assert util.run('library.document', {'document_id':uid})['result']['name']=='Ordem Paranormal.txt'
    assert util.run('library.retrieve', {'query':'a porta está aberta', 'document_hint':'Ordem Paranormal'})['result']['evidence']
    assert util.run('library.rename', {'id':uid,'name':'other.pdf','confirm':True})['status']=='failed'
    assert util.run('library.rename', {'id':uid,'name':'../other.txt','confirm':True})['status']=='failed'


def test_reindex_restores_search_from_original_without_changing_bytes(tmp_path):
    util=fixture_util(tmp_path)
    uid=ingest(util,'manual.md','# Ordem Paranormal\n\nA Sentinela da Névoa é a mais forte criatura de Morte neste exemplo.')
    original=util.docs/(uid+'.md')
    before=original.read_bytes()
    with util.connect() as db:
        db.execute('DELETE FROM document_sections WHERE document_id=?',(uid,))
        db.execute('DELETE FROM document_fts WHERE document_id=?',(uid,))
        db.execute('UPDATE documents SET pages=?,content=? WHERE id=?',('[]','',uid))
    assert util.run('library.reindex',{'id':uid,'confirm':True})['status']=='success'
    assert original.read_bytes()==before
    out=util.run('library.retrieve', {'query':'criatura de Morte mais forte','document_hint':'Ordem Paranormal'})['result']
    # Hint appears in the original content, not the filename; do not assume file-title identity.
    assert out['status'] in ('found','not_found')
    out=util.run('library.retrieve', {'query':'criatura de Morte mais forte'})['result']
    assert any('Sentinela' in e['excerpt'] for e in out['evidence'])
    original.write_bytes(b'tampered')
    assert util.run('library.reindex',{'id':uid,'confirm':True})['status']=='failed'


def test_library_pagination_reports_full_count(tmp_path):
    util=fixture_util(tmp_path)
    with util.connect() as db:
        db.executemany('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)',
                       [(f'd{i:03}',f'Texto {i:03}.txt','geral',f'sha{i:03}',
                         'texto','[]','fixture',f'2026-01-{(i%27)+1:02d}') for i in range(105)])
    first=util.run('library.list',{})['result']
    second=util.run('library.list',{'offset':100})['result']
    assert first['total']==105 and first['count']==105 and len(first['documents'])==100
    assert first['has_more'] and len(second['documents'])==5 and not second['has_more']


def test_followup_without_question_mark_keeps_explicit_document_reference():
    from campanario.chat.models import MessageRole
    from types import SimpleNamespace
    previous=[SimpleNamespace(role=MessageRole.USER,content=
        'procure no arquivo relacionado a ordem paranormal e me diga a criatura de morte mais forte')]
    followup=document_request('no sistema de ordem paranormal qual a criatura de morte mais forte',previous)
    assert followup is not None
    assert followup.hint=='ordem paranormal'
    assert 'criatura de morte' in followup.question


def test_file_explorer_paginates_instead_of_hiding_entries(tmp_path):
    util=fixture_util(tmp_path)
    for i in range(105):
        (util.roots[0]/f'documento_{i:03d}.txt').write_text('teste')
    first=util.run('files.list',{})['result']
    second=util.run('files.list',{'offset':100})['result']
    assert first['total']==105 and len(first['items'])==100 and first['has_more']
    assert len(second['items'])==5 and not second['has_more']
