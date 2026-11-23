"""R3.13 regression: personal chat attachment is usable even when V9 is enabled."""
from types import SimpleNamespace
from fastapi.testclient import TestClient
import campanario.utilities.api as api
from campanario.main import app
from campanario.utilities.service import UtilityService


def setup(monkeypatch, tmp_path, *, secure=False):
    utility = UtilityService(tmp_path / 'dados')
    monkeypatch.setattr(api, 'service', lambda: utility)
    monkeypatch.setattr('campanario.config.get_settings', lambda: SimpleNamespace(brains_v9_enabled=True))
    monkeypatch.setattr(api, '_identities', lambda: {'pf6-user:alice': object()} if secure else {})
    monkeypatch.setattr(api, '_owner_enabled', lambda: False)
    return TestClient(app), utility


def test_local_personal_stream_succeeds_without_pf6(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    url = '/api/v1/utilities/upload-stream?filename=relatorio.pdf'
    data = b'%PDF-1.7\nlocal evidence'
    response = client.post(url, content=data, headers={'Content-Type': 'application/octet-stream'})
    assert response.status_code == 200, response.text
    assert (utility.roots[0] / 'relatorio.pdf').read_bytes() == data
    assert client.post(url, content=b'overwrite', headers={'Content-Type': 'application/octet-stream'}).status_code == 409


def test_personal_legacy_upload_and_docx(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    r = client.post('/api/v1/utilities/upload', json={'filename': 'notas.txt', 'content_base64': 'b2s='})
    assert r.status_code == 200, r.text
    assert (utility.roots[0] / 'notas.txt').read_bytes() == b'ok'
    r = client.post('/api/v1/utilities/upload-stream?filename=carta.docx', content=b'PK-test', headers={'content-type':'application/octet-stream'})
    assert r.status_code == 200, r.text


def test_personal_upload_does_not_allow_other_writes(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    r = client.post('/api/v1/utilities/invoke', json={'tool': 'notes.save', 'arguments': {'title': 'no', 'confirm': True}})
    assert r.status_code in (403, 503)
    assert not list(utility.roots[0].iterdir())


def test_personal_upload_remains_local_and_scoped(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    url = '/api/v1/utilities/upload-stream?filename=ok.pdf'
    headers = {'content-type': 'application/octet-stream'}
    assert client.post(url, content=b'a', headers={**headers, 'Origin': 'https://outside.example'}).status_code == 403
    assert client.post(url, content=b'a', headers={**headers, 'Sec-Fetch-Site': 'cross-site'}).status_code == 403
    assert client.post('/api/v1/utilities/upload-stream?filename=wrong.exe', content=b'a', headers=headers).status_code == 400
    assert client.post(url, content=b'', headers=headers).status_code == 400
    assert not (utility.roots[0] / 'ok.pdf').exists()


def test_configured_pf6_never_falls_back_to_solo(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path, secure=True)
    r = client.post('/api/v1/utilities/upload-stream?filename=protected.pdf', content=b'a', headers={'content-type': 'application/octet-stream'})
    assert r.status_code in (401, 403, 503), r.text
    assert not (utility.roots[0] / 'protected.pdf').exists()


def test_malformed_identities_fail_closed(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    monkeypatch.setattr(api, '_identities', lambda: (_ for _ in ()).throw(ValueError('bad json')))
    r = client.post('/api/v1/utilities/upload-stream?filename=protected.pdf', content=b'a', headers={'content-type': 'application/octet-stream'})
    assert r.status_code == 503
    assert not (utility.roots[0] / 'protected.pdf').exists()
