"""Contract tests for the optional static GitHub Pages frontend."""
from pathlib import Path
import os
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_static_site_is_self_contained_and_no_private_files():
    site = ROOT / 'pages'
    for f in ('index.html','map.html','map.js','map.css','sw.js','manifest.webmanifest','app.mjs','transport.mjs','store.mjs','icon.png'):
        assert (site/f).is_file(), f
    names = {p.name for p in site.rglob('*') if p.is_file()}
    assert '.env' not in names and 'uv.lock' not in names
    assert not any(n.endswith(('.db','.sqlite','.sqlite3','.pem','.key','.jks')) for n in names)
    assert 'navigator.geolocation' in (site/'map.js').read_text()
    assert 'nominatim.openstreetmap.org' in (site/'map.js').read_text()
    assert 'router.project-osrm.org' in (site/'map.js').read_text()
    assert 'sessionStorage' in (site/'store.mjs').read_text()
    assert 'window.CampanarioNative' in (site/'app.mjs').read_text()  # Android fallback still compatible


def test_pages_deployment_is_only_static_site():
    workflow=(ROOT/'.github/workflows/publicar-field-pages.yml').read_text()
    assert 'path: pages' in workflow
    assert 'actions/deploy-pages' in workflow
    assert 'CAMPANARIO-DATABASE' not in workflow


def test_companion_cors_is_exact_opt_in(monkeypatch):
    from campanario.app.remote import create_companion_app
    monkeypatch.delenv('CAMPANARIO_FIELD_PAGES_ORIGIN', raising=False)
    client=TestClient(create_companion_app())
    def preflight(origin):
        return client.options('/api/companion/v1/status', headers={
            'Origin':origin,'Access-Control-Request-Method':'GET',
            'Access-Control-Request-Headers':'authorization'})
    assert preflight('https://somebody.github.io').headers.get('access-control-allow-origin') is None
    assert preflight('https://appassets.androidplatform.net').headers.get('access-control-allow-origin')=='https://appassets.androidplatform.net'
    monkeypatch.setenv('CAMPANARIO_FIELD_PAGES_ORIGIN','https://campanario.github.io')
    client=TestClient(create_companion_app())
    assert preflight('https://campanario.github.io').headers.get('access-control-allow-origin')=='https://campanario.github.io'
    assert preflight('https://evil.github.io').headers.get('access-control-allow-origin') is None


def test_invalid_pages_origin_fails_closed(monkeypatch):
    from campanario.app.remote import create_companion_app
    for origin in ('*', 'https://evil.com', 'http://user.github.io', 'https://user.github.io/path', 'https://user.github.io.evil.net'):
        monkeypatch.setenv('CAMPANARIO_FIELD_PAGES_ORIGIN',origin)
        with pytest.raises(ValueError):
            create_companion_app()
