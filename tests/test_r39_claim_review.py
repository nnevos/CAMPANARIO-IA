"""R3.9: literal-source claim reading must never become a truth oracle."""
import hashlib
import pytest
from campanario.brains.case_claims import review_claims
from campanario.brains.casework import CaseWorkspace
from campanario.brains.case_investigation_pipeline import investigate_case
from campanario.brains.casework_dialogue import prepare_case_answer


def snippet(eid, text, line=1):
    return {'evidence_id': eid, 'filename': eid + '.txt', 'line': line,
            'sha256': hashlib.sha256(text.encode()).hexdigest(), 'quote': text}


def test_explicit_opposition_between_independent_files():
    result = review_claims([snippet('e1', 'O pagamento foi aprovado.'),
                            snippet('e2', 'O pagamento não foi aprovado.')])
    assert len(result['textual_oppositions']) == 1
    assert all(c['status'] == 'source_statement_not_verified' for c in result['claims'])


def test_hypothesis_versus_fact_never_produces_conflict():
    result = review_claims([snippet('e1', 'O pagamento teria sido aprovado.'),
                            snippet('e2', 'O pagamento não foi aprovado.')])
    assert result['claims'][0]['reading'] == 'uncertain_or_hypothetical'
    assert result['textual_oppositions'] == []


def test_attribution_is_not_treated_as_independent_verified_fact():
    result = review_claims([snippet('e1', 'Segundo o operador, o pagamento foi aprovado.'),
                            snippet('e2', 'O pagamento não foi aprovado.')])
    assert result['claims'][0]['reading'] == 'attributed_statement'
    assert not result['textual_oppositions']


def test_negation_in_different_sentence_not_conflict():
    result = review_claims([snippet('e1', 'O pagamento foi aprovado sem auditoria.'),
                            snippet('e2', 'O pagamento não foi aprovado.')])
    assert not result['textual_oppositions']


def test_no_cross_document_conflict_inside_same_file():
    assert review_claims([snippet('e1', 'O pagamento foi aprovado.', 1),
                          snippet('e1', 'O pagamento não foi aprovado.', 2)])['textual_oppositions'] == []


def test_bound_and_empty_sources():
    assert not review_claims([{'quote': 'O prazo foi alterado.'}])['claims']
    assert len(review_claims([snippet(str(i), 'O prazo foi alterado.') for i in range(40)])['claims']) == 16


@pytest.fixture
def case(tmp_path):
    db = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    db.mkdir(parents=True)
    ws = CaseWorkspace(db)
    cid = ws.create('Aprovação fictícia', 'Testar as afirmações', 'operador')
    for name, text in [('afirma.txt', 'O pagamento foi aprovado.'),
                       ('nega.txt', 'O pagamento não foi aprovado.')]:
        file = tmp_path / name
        file.write_text(text, encoding='utf8')
        ws.add_evidence(cid, file, 'registro sintético', 'operador')
    return ws, cid


def test_end_to_end_integrity_and_canonical_expression(case):
    ws, cid = case
    output = investigate_case(ws, cid, 'pagamento aprovado')
    assert output['status'] == 'reviewable'
    assert output['claim_review']['textual_oppositions']
    assert len(output['claim_review']['claims']) >= 2
    answer = prepare_case_answer(ws, cid, 'Todd investigue pagamento aprovado', 'todd')['answer']
    assert 'Oposição textual explícita' in answer
    assert 'não comprova qual fonte está correta' in answer
    assert 'foi aprovado' in answer


def test_hash_tampering_blocks_claims(case):
    ws, cid = case
    entry = ws.read(cid)['evidence'][0]
    (ws._dir(cid) / 'originals' / entry['stored_as']).write_text('adulterado', encoding='utf8')
    review = investigate_case(ws, cid, 'pagamento aprovado')
    assert review['status'] == 'integrity_failed'
    assert 'claim_review' not in review
    assert not review['citations']


def test_natural_question_about_evidence_claims_uses_content_review(case):
    ws, cid = case
    output = prepare_case_answer(ws, cid, 'O que as evidências afirmam sobre pagamento?', 'morgana')
    assert output['intent'] == 'contents'
    assert 'Leitura textual' in output['answer']
    assert 'Oposição textual explícita' in output['answer']
