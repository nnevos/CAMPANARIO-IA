"""Regression cases for entity identity verification before conversational opinion."""
import pytest
from campanario.utilities.web_intent import decide

@pytest.mark.asyncio
@pytest.mark.parametrize('message,expected', [
    ('guys qual a opinião de vocês sobre o Cellbit?', True),
    ('qual a opinião de vocês em relação a Hunter 350?', True),
    ('o que vocês acham de uma tecnologia chamada Zyrtex?', True),
    ('quem é Xandrel?', True),
    ('boa tarde', False),
    ('o que acha de mim?', False),
    ('não pesquise na internet, quem é Cellbit?', False),
])
async def test_entity_preflight_without_planner(message, expected):
    result = await decide(message, None, '')
    assert result.search is expected

@pytest.mark.asyncio
async def test_entity_preflight_overrides_wrong_model_confidence():
    from campanario.model.protocol import FakeModelProvider
    result = await decide('qual a opinião de vocês sobre o Cellbit?', FakeModelProvider('{"search":false,"query":""}'), 'model')
    assert result.search
    assert 'Cellbit' in result.query
