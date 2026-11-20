"""Regression: the chat renderer must create the timestamp before updating it."""
from pathlib import Path
import re


def test_chat_turn_contains_timestamp_element():
    html = (Path(__file__).resolve().parents[1] / 'src/campanario/web/index.html').read_text(encoding='utf-8')
    html += "\n".join(f.read_text(encoding="utf-8") for f in sorted((Path(__file__).resolve().parents[1] / "src/campanario/web/static").glob("*")) if f.suffix in {".js", ".css"})
    renderer = html.split('function addTurn(', 1)[1].split('function addError(', 1)[0]
    assert '<time class="message-time"></time>' in renderer
    assert 'el.querySelector(\'.message-time\')' in renderer
    assert renderer.index('<time class="message-time"></time>') < renderer.index("el.querySelector('.message-time')")
    assert 'stamp.dateTime=parsed.toISOString()' in renderer
