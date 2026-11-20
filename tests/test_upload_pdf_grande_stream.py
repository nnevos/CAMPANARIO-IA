"""Large PDF transport without Base64, hard size caps and private local workspace."""
from __future__ import annotations

from fastapi.testclient import TestClient

from campanario.main import app
from campanario.utilities.service import UtilityService


def setup(monkeypatch, tmp_path):
    import campanario.utilities.api as backend
    utility = UtilityService(tmp_path / 'data')
    monkeypatch.setattr(backend, 'service', lambda: utility)
    return TestClient(app), utility


def test_binary_upload_is_allowed_and_duplicate_never_overwritten(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    content = b'%PDF-1.7\n' + b'A' * 4096
    url = '/api/v1/utilities/upload-stream?filename=Ordem%20Paranormal.pdf'
    first = client.post(url, content=content, headers={'Content-Type': 'application/octet-stream'})
    assert first.status_code == 200, first.text
    assert first.json()['bytes'] == len(content)
    target = utility.roots[0] / 'Ordem Paranormal.pdf'
    assert target.read_bytes() == content
    assert client.post(url, content=b'OVERWRITE', headers={'Content-Type': 'application/octet-stream'}).status_code == 409
    assert target.read_bytes() == content


def test_legacy_20mb_limit_no_longer_blocks_stream(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    content = b'P' * 20_000_001
    response = client.post('/api/v1/utilities/upload-stream?filename=manual.pdf',
                           content=content,
                           headers={'Content-Type': 'application/octet-stream'})
    assert response.status_code == 200, response.text
    assert (utility.roots[0] / 'manual.pdf').stat().st_size == len(content)


def test_huge_file_rejected_before_disk_write(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    response = client.post('/api/v1/utilities/upload-stream?filename=manual.pdf',
                           content=b'',
                           headers={'Content-Type': 'application/octet-stream',
                                    'Content-Length': '200000001'})
    assert response.status_code == 413
    assert not (utility.roots[0] / 'manual.pdf').exists()


def test_upload_rejects_extensions_paths_origin_and_type(monkeypatch, tmp_path):
    client, utility = setup(monkeypatch, tmp_path)
    base = '/api/v1/utilities/upload-stream?filename='
    h = {'Content-Type': 'application/octet-stream'}
    assert client.post(base+'..%2Fsegredo.pdf', content=b'test', headers=h).status_code == 400
    assert client.post(base+'forjado.exe', content=b'test', headers=h).status_code == 400
    assert client.post(base+'arquivo.pdf', content=b'test', headers={'Content-Type':'text/plain'}).status_code == 415
    assert client.post(base+'arquivo.pdf', content=b'test', headers={**h,'Origin':'http://evil.test'}).status_code == 403
    assert not list(utility.roots[0].iterdir())


def test_pdf_import_uses_reader_from_path_not_entire_bytes(monkeypatch, tmp_path):
    from pypdf import PdfWriter
    client, utility = setup(monkeypatch, tmp_path)
    target = utility.roots[0] / 'livro.pdf'
    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    with target.open('wb') as f:
        w.write(f)
    result = utility.run('library.import', {'path': str(target), 'confirm': True})
    assert result['status'] == 'success'
    assert result['result']['requires_ocr']
    assert not list(utility.docs.glob('*.pdf'))
