"""R2.6: same-origin enforcement and conservative PF6 UI invariants."""
from pathlib import Path
from fastapi.testclient import TestClient
from campanario.main import app


def test_browser_cross_site_rejected_for_mutation_and_read():
    client = TestClient(app)
    for method, path in [('post', '/api/v1/utilities/sessions/login'),
                         ('post', '/api/v1/utilities/invoke'),
                         ('get', '/api/v1/utilities/catalog')]:
        response = getattr(client, method)(path, headers={'sec-fetch-site': 'cross-site'}, **({'json': ({'credential': 'bad'} if path.endswith('/login') else {'tool': 'notes.list', 'arguments': {}})} if method == 'post' else {}))
        assert response.status_code == 403
        response = getattr(client, method)(path, headers={'sec-fetch-site': 'same-site'}, **({'json': ({'credential': 'bad'} if path.endswith('/login') else {'tool': 'notes.list', 'arguments': {}})} if method == 'post' else {}))
        assert response.status_code == 403


def test_origin_must_match_local_host_and_not_be_opaque():
    client = TestClient(app)
    for origin in ['null', 'https://attacker.invalid', 'file://', 'http://testclient.evil']:
        assert client.get('/api/v1/utilities/catalog', headers={'Origin': origin}).status_code == 403
    assert client.get('/api/v1/utilities/catalog', headers={'Origin': 'http://testserver'}).status_code == 200
    assert client.get('/api/v1/utilities/catalog', headers={'sec-fetch-site': 'same-origin'}).status_code == 200


def test_consent_modal_escapes_server_supplied_values_and_never_stores_token():
    web = Path(__file__).resolve().parents[1] / 'src/campanario/web'
    js = (web / 'ferramentas.js').read_text(encoding='utf-8')
    html = (web / 'ferramentas.html').read_text(encoding='utf-8')
    assert '<dialog id="pf6-dialog"' in html
    assert 'type="password"' in html
    assert "details.textContent=login?'':" in js
    assert 'pf6Review({tool:pending.tool,args:pending.arguments})' in js
    assert "const credentials=await pf6Review({login:true})" in js
    assert 'prompt(\'Credencial PF6' not in js
    assert 'localStorage.setItem' not in js
    assert 'sessionStorage.setItem' not in js


def test_utilities_page_is_framing_and_inline_script_protected():
    response = TestClient(app).get('/ferramentas')
    assert response.status_code == 200
    csp = response.headers['content-security-policy']
    assert "script-src 'self'" in csp
    assert "'unsafe-inline'" not in csp.split('script-src ')[1].split(';')[0]
    assert "frame-ancestors 'none'" in csp
    assert response.headers['cache-control'] == 'no-store'
