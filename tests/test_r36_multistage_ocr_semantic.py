"""R3.6 offline tests: no internet, no personal records, all sources synthetic."""
from pathlib import Path
import pytest
from campanario.brains.casework import CaseWorkspace
from campanario.brains import casework_sources as sources
from campanario.brains.case_investigation_pipeline import investigate_case
from campanario.brains.casework_dialogue import prepare_case_answer


@pytest.fixture
def item(tmp_path):
    d = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    d.mkdir(parents=True)
    ws = CaseWorkspace(d)
    cid = ws.create('Teste de hipóteses', 'Investigar discrepância', 'loopback-utilities')
    for name, content in [('a.txt', 'O valor do contrato é 20 reais.\nO vigilante abriu o portão às 18h.'),
                          ('b.txt', 'O valor do contrato é 30 reais.\nO relatório menciona revisão do contrato.')]:
        f = tmp_path / name
        f.write_text(content, encoding='utf8')
        ws.add_evidence(cid, f, 'simulação', 'operador')
    return ws, cid


def test_multistage_keeps_competing_hypotheses(item):
    ws, cid = item
    doc = ws.read(cid)
    eids = [e['id'] for e in doc['evidence']]
    ws.add_hypothesis(cid, 'A divergência decorre de versões diferentes', [eids[0]], [eids[1]], 'Conferir versões')
    result = investigate_case(ws, cid, 'investigue valor contrato')
    assert result['status'] == 'reviewable'
    assert len(result['steps']) == 5
    assert result['conflicts']
    assert result['hypotheses'][0]['status'] == 'unverified'
    assert result['hypotheses'][0]['support_count'] == 1
    assert 'Conferir versões' in result['next_checks']
    answer = prepare_case_answer(ws, cid, 'Caso: investigue valor contrato', 'todd')
    assert 'Revisão multietapa' in answer['answer']
    assert 'NÃO CONFIRMADA' in answer['answer']


def test_pipeline_does_not_touch_originals_or_ledger(item):
    ws, cid = item
    base = ws._dir(cid)
    before = {str(x): x.read_bytes() for x in base.rglob('*') if x.is_file()}
    investigate_case(ws, cid, 'contrato')
    assert before == {str(x): x.read_bytes() for x in base.rglob('*') if x.is_file()}


def test_tampered_evidence_blocks_pipeline(item):
    ws, cid = item
    entry = ws.read(cid)['evidence'][0]
    (ws._dir(cid) / 'originals' / entry['stored_as']).write_text('novo texto')
    result = investigate_case(ws, cid, 'contrato')
    assert result['status'] == 'integrity_failed'
    assert not result['citations']


def test_ocr_optional_does_not_execute_without_optin(monkeypatch, tmp_path):
    monkeypatch.delenv('CAMPANARIO_CASE_OCR_ENABLED', raising=False)
    image = tmp_path / 'test.png'
    image.write_bytes(b'not-an-image')
    rows, error = sources._extract(image)
    assert rows == [] and 'OCR' in error


def test_ocr_invalid_image_never_starts_subprocess(monkeypatch, tmp_path):
    monkeypatch.setenv('CAMPANARIO_CASE_OCR_ENABLED', '1')
    monkeypatch.setattr(sources.shutil, 'which', lambda name: '/usr/bin/tesseract')
    monkeypatch.setattr(sources.subprocess, 'run', lambda *a, **k: pytest.fail('invalid image dispatched'))
    image = tmp_path / 'test.png'
    image.write_bytes(b'not-an-image')
    rows, error = sources._extract(image)
    assert rows == [] and 'inválida' in error


def test_ocr_real_image_is_verbatim_when_dependency_present(monkeypatch, tmp_path):
    pillow = pytest.importorskip('PIL.Image')
    monkeypatch.setenv('CAMPANARIO_CASE_OCR_ENABLED', '1')
    monkeypatch.setattr(sources.shutil, 'which', lambda name: '/fake/tesseract')
    from subprocess import CompletedProcess
    monkeypatch.setattr(sources.subprocess, 'run', lambda argv, **kw: CompletedProcess(argv, 0, b'contrato 42 reais\n', b''))
    image = tmp_path / 'case.png'
    pillow.new('RGB', (40, 20)).save(image)
    rows, error = sources._extract(image)
    assert rows == ['OCR: contrato 42 reais'] and error == ''


def test_semantic_optin_only_with_stub(item, monkeypatch):
    ws, cid = item
    monkeypatch.setenv('CAMPANARIO_CASE_SEMANTIC_ENABLED', '1')
    monkeypatch.setattr(sources, '_local_embeddings', lambda texts: [[1., 0., 0., 0., 0., 0., 0., 0.]] * len(texts))
    found = sources.search_case_evidence(ws, cid, 'assunto completamente distinto')
    assert found['semantic_used']
    assert found['snippets']
    assert found['snippets'][0]['evidence_id'] in {e['id'] for e in ws.read(cid)['evidence']}


def test_semantic_unavailable_degrades_without_facts(item, monkeypatch):
    ws, cid = item
    monkeypatch.setenv('CAMPANARIO_CASE_SEMANTIC_ENABLED', '1')
    def fail(texts):
        raise OSError('ollama offline')
    monkeypatch.setattr(sources, '_local_embeddings', fail)
    found = sources.search_case_evidence(ws, cid, 'contrato')
    assert 'indisponíveis' in found['semantic_note']
    assert found['snippets']


def test_no_match_does_not_turn_hypothesis_into_fact(item):
    ws, cid = item
    result = investigate_case(ws, cid, 'alienígenas invisíveis')
    assert result['status'] == 'insufficient_evidence'
    assert not result['citations']
    assert any('documento' in s for s in result['next_checks'])


def test_vision_optin_disabled_is_nonintrusive(item, monkeypatch):
    from campanario.brains.casework_vision import local_visual_leads
    monkeypatch.delenv('CAMPANARIO_CASE_VISION_ENABLED', raising=False)
    result = local_visual_leads(*item)
    assert result['status'] == 'disabled' and not result['leads']


def test_visual_model_output_is_unverified_not_canonical_fact(item, monkeypatch, tmp_path):
    from campanario.brains.casework_vision import local_visual_leads
    image_lib = pytest.importorskip('PIL.Image')
    ws, cid = item
    picture = tmp_path / 'evidencia.png'
    image_lib.new('RGB', (48, 32)).save(picture)
    ws.add_evidence(cid, picture, 'imagem fictícia', 'operador')
    monkeypatch.setenv('CAMPANARIO_CASE_VISION_ENABLED', '1')
    class Reply:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"response":"Um objeto que pode ser uma pasta."}'
    # json.load reads from an object with read(). No actual model connection.
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == 'http://127.0.0.1:11434/api/generate'
            assert timeout == 25
            return Reply()
    import urllib.request
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *a: Opener())
    result = local_visual_leads(ws, cid)
    assert result['status'] == 'provisional'
    assert result['leads'][0]['status'] == 'unverified_visual_suggestion'
    review = investigate_case(ws, cid, 'investigue contrato')
    assert review['visual_leads'][0]['status'] == 'unverified_visual_suggestion'
    assert 'culpado' not in str(review['steps'])


def test_optional_flags_are_loaded_from_private_env_file(tmp_path):
    from campanario.config import Settings
    env = tmp_path / '.env'
    env.write_text('CAMPANARIO_CASE_OCR_ENABLED=true\n'
                   'CAMPANARIO_CASE_SEMANTIC_ENABLED=true\n'
                   'CAMPANARIO_CASE_VISION_ENABLED=true\n', encoding='utf-8')
    settings = Settings(_env_file=env)
    assert settings.case_ocr_enabled and settings.case_semantic_enabled and settings.case_vision_enabled
