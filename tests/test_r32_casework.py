"""Case workspace acceptance tests using ephemeral sibling DATABASE, never personal data."""
import hashlib
import json
from pathlib import Path
import pytest
from campanario.brains.casework import CaseWorkspace, CaseError


@pytest.fixture
def workspace(tmp_path):
    data = tmp_path / 'CAMPANARIO-DATABASE' / 'dados'
    data.mkdir(parents=True)
    return CaseWorkspace(data)


def test_eclipse_case_end_to_end(workspace, tmp_path):
    case = workspace.create('Operação Eclipse (FICTÍCIO)', 'Verificar cronologia sem atribuir culpa', 'Responsável fictício')
    source = tmp_path / 'logs.json'
    source.write_text(json.dumps({'timestamp': '2026-11-23T18:42:00-03:00', 'action': 'poweroff'}))
    imported = workspace.add_evidence(case, source, 'Exportação autorizada fictícia', 'Teste')
    assert imported['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    original = workspace._dir(case) / 'originals' / imported['stored_as']
    assert original.read_bytes() == source.read_bytes()
    assert workspace.verify(case)['integrity_ok']
    event = workspace.add_event(case, '2026-11-23T18:42:00-03:00', 'Registro de desligamento', [imported['id']], 'documented')
    hypothesis = workspace.add_hypothesis(case, 'Saída voluntária', [imported['id']], [], 'Verificar log de saída')
    dossier = workspace.dossier(case)
    assert event['id'] in workspace.read(case)['events'][0]['id']
    assert hypothesis['status'] == 'unresolved'
    assert imported['id'] in dossier and imported['sha256'] in dossier
    assert 'não prova fatos externos' in dossier
    # Modifying the source AFTER capture must not modify original.
    source.write_text('alterado')
    assert workspace.verify(case)['integrity_ok']
    # Tampering with original MUST be reported, never silently accepted.
    original.write_text('adulterado')
    assert not workspace.verify(case)['integrity_ok']
    assert 'FALHA' in workspace.dossier(case)


def test_reject_unknown_evidence_and_unsafe_inputs(workspace, tmp_path):
    case = workspace.create('Auditoria', 'Conferir documentos', 'Proprietário')
    with pytest.raises(CaseError):
        workspace.add_event(case, '2026-11-23T20:00:00', 'Evento sem fuso', ['E123'])
    with pytest.raises(CaseError):
        workspace.add_event(case, '2026-11-23T20:00:00-03:00', 'Sem fonte', ['E123'])
    with pytest.raises(CaseError):
        workspace.add_hypothesis(case, 'Teste', ['E123'], [], 'Revisar')
    with pytest.raises(CaseError):
        workspace.read('../escape')
    source = tmp_path / 'script.exe'
    source.write_text('executable')
    with pytest.raises(CaseError):
        workspace.add_evidence(case, source, 'Origem', 'Operador')
    bad = tmp_path / 'link.json'
    bad.symlink_to(source)
    with pytest.raises(CaseError):
        workspace.add_evidence(case, bad, 'Origem', 'Operador')


def test_no_implicit_database_creation(tmp_path):
    with pytest.raises((CaseError, FileNotFoundError)):
        CaseWorkspace(tmp_path / 'CAMPANARIO-DATABASE' / 'dados')
    wrong = tmp_path / 'CAMPANARIO-IA' / 'dados'
    wrong.mkdir(parents=True)
    with pytest.raises(CaseError):
        CaseWorkspace(wrong)


def test_independent_cases_and_no_automatic_hypothesis_verdict(workspace, tmp_path):
    first = workspace.create('A', 'Objetivo A', 'Usuário')
    second = workspace.create('B', 'Objetivo B', 'Usuário')
    f = tmp_path / 'doc.txt'; f.write_text('A credencial aparece às 19:08.')
    a = workspace.add_evidence(first, f, 'Arquivo fornecido', 'Usuário')
    b = workspace.add_evidence(second, f, 'Arquivo fornecido', 'Usuário')
    assert a['id'] != b['id']
    with pytest.raises(CaseError):
        workspace.add_hypothesis(second, 'Outro caso', [a['id']], [], 'Verificar')
    hypothesis = workspace.add_hypothesis(first, 'Uso indevido do crachá', [a['id']], [], 'Comparar logs')
    assert hypothesis['status'] == 'unresolved'
    assert 'Uso indevido' in workspace.dossier(first)
    assert 'Uso indevido' not in workspace.dossier(second)


def test_log_proposal_is_unconfirmed_and_requires_review(workspace, tmp_path):
    case = workspace.create('Logs', 'Examinar horarios', 'Operador')
    file = tmp_path / 'access.csv'
    file.write_text('timestamp,action\n2026-11-23T19:08:00-03:00,uso do cracha\n2026-11-23T19:09:00,sem fuso\n', encoding='utf-8')
    imported = workspace.add_evidence(case, file, 'Log autorizado', 'Operador')
    events = workspace.propose_log_events(case, imported['id'])
    assert len(events) == 1 and events[0]['confirmed'] is False
    assert workspace.read(case)['events'] == []
    workspace.add_event(case, events[0]['date_time'], events[0]['description'], [imported['id']])
    assert len(workspace.read(case)['events']) == 1
    original = workspace._dir(case) / 'originals' / imported['stored_as']
    original.write_text('alterado')
    with pytest.raises(CaseError):
        workspace.propose_log_events(case, imported['id'])


def test_review_elapsed_time_does_not_make_hypothesis_true(workspace, tmp_path):
    case = workspace.create('Eclipse', 'Cronologia', 'Operador')
    doc = tmp_path / 'e.json'; doc.write_text('{}')
    e = workspace.add_evidence(case, doc, 'Exportacao autorizada', 'Operador')
    workspace.add_event(case, '2026-11-23T18:42:00-03:00', 'Log desligamento', [e['id']])
    workspace.add_event(case, '2026-11-23T19:08:00-03:00', 'Log cracha', [e['id']])
    workspace.add_hypothesis(case, 'Uso por terceiro', [e['id']], [], 'Verificar identificador')
    review = workspace.review(case)
    assert review['intervals'][0]['elapsed_minutes'] == 26
    assert review['hypothesis_matrix'][0]['verdict'] == 'unresolved'
    assert review['integrity_ok']
    assert '26.0 minutos' in workspace.dossier(case)
