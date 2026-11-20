from pathlib import Path
import importlib.util


def test_handoff_is_regenerable_and_contains_core_goals():
    root = Path(__file__).resolve().parents[1]
    path = root / 'tools' / 'maintenance' / 'ATUALIZAR_CONTINUIDADE.py'
    spec = importlib.util.spec_from_file_location('campanario_continuidade', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    content = module.build_handoff()
    for required in ('Ponto Zero', 'Todd', 'Morgana', 'pesquisa web', 'desenvolvimento', 'memoria'):
        assert required.lower() in content.lower()
    assert '.env,' in content


def test_light_mode_bypasses_scripted_response_pipeline():
    root = Path(__file__).resolve().parents[1]
    source = (root / 'src/campanario/composition.py').read_text(encoding='utf-8')
    assert 'response_provider = safe_provider if settings.low_latency_mode else BehaviorResponseGuardProvider(safe_provider)' in source
