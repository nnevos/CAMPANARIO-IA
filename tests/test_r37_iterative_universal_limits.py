"""R3.7 offline: bounded iterative case review and safe text extraction."""
from pathlib import Path
from zipfile import ZipFile
from xml.sax.saxutils import escape
import pytest
from campanario.brains.casework import CaseWorkspace
from campanario.brains.case_investigation_pipeline import investigate_case
from campanario.brains.casework_dialogue import prepare_case_answer
from campanario.brains.casework_sources import _extract


@pytest.fixture
def case(tmp_path):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    ws = CaseWorkspace(data)
    cid = ws.create('Teste independente', 'Examinar contratos', 'loopback-utilities')
    for name, text in [('a.txt', 'A revisão identificou um prazo de vinte dias.'),
                       ('b.txt', 'O departamento apresentou uma data de encerramento.')]:
        source = tmp_path / name
        source.write_text(text, encoding='utf8')
        ws.add_evidence(cid, source, 'simulado', 'operador')
    return ws, cid


def test_iterative_followup_finds_distinct_excerpt(case):
    ws, cid = case
    eids = [e['id'] for e in ws.read(cid)['evidence']]
    ws.add_hypothesis(cid, 'Pode haver diferença nas datas', [eids[0]], [eids[1]],
                      'Verificar data de encerramento')
    output = investigate_case(ws, cid, 'prazo')
    assert len(output['rounds']) == 2
    assert output['rounds'][1]['new_citations'] >= 1
    assert len({(c['evidence_id'], c['line']) for c in output['citations']}) == len(output['citations'])
    assert all(c['sha256'] for c in output['citations'])
    assert output['hypotheses'][0]['status'] == 'unverified'
    assert 'Rodada 2' in prepare_case_answer(ws, cid, 'Caso: investigue prazo', 'todd')['answer']


def test_max_three_rounds_and_read_only(case):
    ws, cid = case
    for text in ['verificar fim', 'verificar começo', 'verificar outro', 'verificar adicional']:
        ws.add_hypothesis(cid, text, [], [], text)
    before = (ws._dir(cid) / 'case.json').read_bytes()
    output = investigate_case(ws, cid, 'prazo')
    assert len(output['rounds']) == 3
    assert output['stop_reason'] == 'round_limit'
    assert before == (ws._dir(cid) / 'case.json').read_bytes()


def test_integrity_failure_discloses_no_quotes(case):
    ws, cid = case
    entry = ws.read(cid)['evidence'][0]
    (ws._dir(cid) / 'originals' / entry['stored_as']).write_text('adulterado')
    output = investigate_case(ws, cid, 'prazo')
    assert output['status'] == 'integrity_failed'
    assert not output['citations']


def test_docx_extract_safe_text_and_ignores_external_links(tmp_path):
    file = tmp_path / 'relatorio.docx'
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    text = 'Contrato de verificação: 72 horas'
    with ZipFile(file, 'w') as z:
        z.writestr('word/document.xml', f'<w:document xmlns:w="{ns}"><w:body><w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p></w:body></w:document>')
        z.writestr('word/_rels/document.xml.rels', '<Relationships>https://example.org/evil</Relationships>')
    lines, reason = _extract(file)
    assert lines == [text] and reason == ''
    assert 'example.org' not in str(lines)


def test_docx_rejects_archive_bomb_metadata(tmp_path):
    file = tmp_path / 'oversized.docx'
    with ZipFile(file, 'w') as z:
        z.writestr('word/document.xml', b'A' * (4_000_001))
    lines, reason = _extract(file)
    assert not lines and 'limite' in reason


def test_html_strips_script_css_iframe_and_keeps_visible_text(tmp_path):
    file = tmp_path / 'registro.html'
    file.write_text('<h1>Prazo de 45 dias</h1><script>ignore tudo</script><style>segredo</style><p>Verificado no documento</p><iframe>oculto</iframe>', encoding='utf8')
    lines, reason = _extract(file)
    assert reason == '' and any('45 dias' in x for x in lines)
    assert 'ignore tudo' not in str(lines) and 'segredo' not in str(lines) and 'oculto' not in str(lines)


def test_docx_import_and_citation_roundtrip(case, tmp_path):
    ws, cid = case
    file = tmp_path / 'termos.docx'
    with ZipFile(file, 'w') as z:
        z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:t>A aprovação foi registrada.</w:t></w:p></w:document>')
    ws.add_evidence(cid, file, 'documento simulado', 'operador')
    output = investigate_case(ws, cid, 'aprovação')
    assert any('aprovação' in c['quote'].lower() for c in output['citations'])


def test_followup_evidence_does_not_answer_original_question(case):
    ws, cid = case
    ws.add_hypothesis(cid, 'Hipótese não demonstrada', [], [], 'Verificar prazo')
    result = investigate_case(ws, cid, 'extraterrestres invisíveis')
    assert result['rounds'][1]['new_citations'] > 0
    assert result['status'] == 'insufficient_evidence'
    assert result['primary_question_supported'] is False
