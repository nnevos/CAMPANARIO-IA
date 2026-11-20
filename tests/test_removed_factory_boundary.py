"""Guard the user-requested removal of the abandoned automation experiment."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_experimental_factory_files_removed():
    for rel in (
        'src/campanario/renpy_factory',
        'src/campanario/web/renpy_factory.html',
        'tools/windows/ABRIR_FABRICA_RENPY.bat',
        'docs/manual/31_FABRICA_RENPY.md',
        'tests/test_renpy_factory.py',
    ):
        assert not (ROOT / rel).exists(), rel
    assert not list((ROOT / 'docs/adr').glob('*renpy*'))


def test_chat_and_memory_untouched_by_removal():
    assert (ROOT / 'src/campanario/web/index.html').is_file()
    assert (ROOT / 'src/campanario/chat/service.py').is_file()
    assert (ROOT / 'src/campanario/runtime/experience.py').is_file()
    assert (ROOT / 'tools/windows/INICIAR_CAMPANARIO.bat').is_file()
    html = (ROOT / 'src/campanario/web/index.html').read_text(encoding='utf-8')
    assert 'newConversation' in html
    assert 'newSessionPanel' in html
    api = (ROOT / 'src/campanario/api.py').read_text(encoding='utf-8')
    assert '@v1_router.get("/memory")' in api
    assert '/renpy-factory' not in api
    assert '/renpy-factory' not in html
