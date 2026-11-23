"""R3.8 contractual tests: evidence-only, adaptive, bounded investigation."""
from pathlib import Path
import pytest
from campanario.brains.casework import CaseWorkspace
from campanario.brains.case_investigation_pipeline import investigate_case
from campanario.brains.case_reasoning import relation_matrix, hypothesis_matrix, prioritize_checks
from campanario.brains.casework_dialogue import prepare_case_answer


@pytest.fixture
def investigation(tmp_path):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    ws = CaseWorkspace(data)
    cid = ws.create('Exemplo sintético', 'Conferir contratos', 'operador')
    for name, content in [('a.txt', 'O contrato informa prazo de 20 dias.\nRevisão em andamento.'),
                          ('b.txt', 'O contrato informa prazo de 30 dias.\nRevisão em andamento.'),
                          ('c.txt', 'O arquivo informa despesas sem confirmação.')]:
        src = tmp_path / name
        src.write_text(content, encoding='utf8')
        ws.add_evidence(cid, src, 'exemplo sintético', 'operador')
    return ws, cid


def test_adaptive_prioritizes_question_relevant_registered_checks(investigation):
    ws, cid = investigation
    ids = [e['id'] for e in ws.read(cid)['evidence']]
    ws.add_hypothesis(cid, 'Despesa não verificada', [ids[2]], [], 'Rever despesas da equipe')
    ws.add_hypothesis(cid, 'Prazo de contrato diferente', [ids[0]], [ids[1]], 'Verificar prazo contratual em cada cópia')
    result = investigate_case(ws, cid, 'investigue prazo contratual')
    assert result['rounds'][1]['question'] == 'Verificar prazo contratual em cada cópia'
    assert result['verification_queue'][0]['reason'] == 'referências pró e contra cadastradas'
    assert result['hypothesis_review'][1]['status'] == 'unverified'
    assert result['relations']['registered_links']


def test_relation_does_not_imply_truth_or_causality(investigation):
    ws, cid = investigation
    result = investigate_case(ws, cid, 'contrato prazo')
    hints = result['relations']['cross_document_hints']
    assert hints and hints[0]['status'] == 'lexical_overlap_only'
    assert 'não demonstram causalidade' in result['relations']['warning']
    assert result['status'] == 'reviewable'
    assert result['conflicts']  # comparison is a disagreement, not a resolution


def test_followup_never_promotes_unrelated_primary(investigation):
    ws, cid = investigation
    ws.add_hypothesis(cid, 'Uma hipótese qualquer', [], [], 'Verificar prazo contratual')
    result = investigate_case(ws, cid, 'quem foi o culpado pelo sumiço')
    assert result['primary_question_supported'] is False
    assert result['status'] == 'insufficient_evidence'
    assert result['rounds'][1]['new_citations'] >= 1


def test_registered_support_is_not_semantic_validation(investigation):
    ws, cid = investigation
    ids = [e['id'] for e in ws.read(cid)['evidence']]
    ws.add_hypothesis(cid, 'A empresa teria fraude', [ids[0]], [ids[1]], 'Revisar provas')
    review = investigate_case(ws, cid, 'contrato prazo')
    assert review['hypothesis_review'][0]['review_state'] == 'mixed_registered_positions'
    assert review['hypothesis_review'][0]['status'] == 'unverified'
    assert 'NÃO CONFIRMADA' in prepare_case_answer(ws, cid, 'Todd investigue contrato prazo', 'todd')['answer']


def test_no_writes_to_ledger(investigation):
    ws, cid = investigation
    ledger = ws._dir(cid) / 'case.json'
    before = ledger.read_bytes()
    investigate_case(ws, cid, 'contrato')
    assert ledger.read_bytes() == before


def test_tampering_blocks_all_relations(investigation):
    ws, cid = investigation
    entry = ws.read(cid)['evidence'][0]
    (ws._dir(cid) / 'originals' / entry['stored_as']).write_text('alterado')
    review = investigate_case(ws, cid, 'prazo')
    assert review['status'] == 'integrity_failed'
    assert not review['citations']
    assert 'relations' not in review


def test_prioritization_deduplicates_and_limits():
    h = [{'id': str(i), 'statement': 'prazo', 'next_check': 'Verificar prazo'} for i in range(30)]
    assert len(prioritize_checks('prazo', h, primary_supported=False)) == 1


def test_no_fabricated_edges():
    doc = {'evidence': [{'id': 'E1'}], 'events': [], 'hypotheses': []}
    out = relation_matrix(doc, [{'evidence_id': 'E1', 'line': 1, 'quote': 'Somente uma frase'}])
    assert out['cross_document_hints'] == []
    assert hypothesis_matrix(doc, []) == []
