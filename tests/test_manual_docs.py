from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_manual_redirects_to_current_version():
    text=(ROOT/'docs/manual/README.md').read_text(encoding='utf-8')
    assert 'LEIA-ME-V08' in text
    assert (ROOT/'docs/history/manual-v07/29_HOST_VOICE_F5C.md').exists()
    assert not (ROOT/'docs/manual/29_HOST_VOICE_F5C.md').exists()

def test_historical_behavior_manuals_are_archived_not_active():
    archive=ROOT/'docs/history/manual_evolution'
    assert (archive/'20_RESPONSE_CONTRACT_PIPELINE.md').exists()
    assert (archive/'21_MODELOS_E_PORTABILIDADE.md').exists()

def test_current_manual_distinguishes_providers_from_contracts():
    text=(ROOT/'docs/current/ARQUITETURA_V08.md').read_text(encoding='utf-8')
    assert 'Morgana' in text and 'Todd' in text
    assert 'TTS' in text and 'GPS' in text
    assert 'nao implementados' in text
