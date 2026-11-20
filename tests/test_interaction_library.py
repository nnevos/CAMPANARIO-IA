from campanario.agents.interaction_library import render_interaction_examples


def test_nonexistent_database_fails_closed(tmp_path):
    assert render_interaction_examples('morgana', 'projeto frustrante', db_path=tmp_path/'missing.sqlite') == ''


def test_unknown_agent_has_no_examples():
    assert render_interaction_examples('unknown', 'projeto frustrante') == ''


def test_only_simulation_lessons_not_dialogue_or_memory():
    result = render_interaction_examples('morgana', 'frustração com projeto')
    assert 'SIM-' in result
    assert 'NAO SAO MEMORIAS' in result
    assert 'PAT-' not in result
    assert len(result) < 1500


def test_can_disable(monkeypatch):
    monkeypatch.setenv('CAMPANARIO_INTERACTION_EXAMPLES', '0')
    assert render_interaction_examples('todd', 'frustração com projeto') == ''
