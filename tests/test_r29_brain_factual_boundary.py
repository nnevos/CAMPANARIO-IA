"""R2.9: brain facts belong to the factual compiler, never to the LLM."""
from dataclasses import replace
import pytest
from campanario.agents.profiles import MORGANA, TODD
from campanario.chat.grounded_expression import GroundedExpressionEngine, render_brain_answer
from campanario.chat.canonical_answer import AnswerMode
from test_v91_expression import canonical, ScriptedProvider


def brain_answer(text='A regra vale somente após aprovação. O valor é 20%.'):
    return canonical(text).model_copy(update={'brain_ids': ('knowledge',)})


@pytest.mark.asyncio
@pytest.mark.parametrize('profile', (MORGANA, TODD))
async def test_brain_facts_are_extractive_with_distinct_agent_style_and_no_model(profile):
    record = brain_answer()
    provider = ScriptedProvider(['Valor 90%, sem aprovação!'])
    result = await GroundedExpressionEngine(provider, model='local').express(record, profile)
    assert provider.calls == 0
    assert result.accepted and not result.fallback_used and result.attempts == ()
    assert result.text.endswith(record.canonical_answer)
    assert result.text.count(record.canonical_answer) == 1
    assert '90%' not in result.text
    assert render_brain_answer(record, MORGANA) != render_brain_answer(record, TODD)


@pytest.mark.asyncio
async def test_unavailable_brain_cannot_be_styled_into_success():
    record = brain_answer().model_copy(update={
        'status': 'not_found', 'facts': (), 'sources': (), 'tool_executions': (),
        'canonical_answer': 'Não encontrei fonte suficiente.'})
    provider = ScriptedProvider(['Eu encontrei uma prova!'])
    result = await GroundedExpressionEngine(provider, model='local').express(record, MORGANA)
    assert result.text == record.canonical_answer
    assert not result.accepted and result.fallback_used
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_legacy_nonbrain_path_keeps_existing_provider_validator():
    record = canonical('O valor é 20%.')
    provider = ScriptedProvider(['O valor é 90%.'])
    result = await GroundedExpressionEngine(provider, model='local', max_retries=0).express(record, MORGANA)
    assert provider.calls == 1
    assert result.text == record.canonical_answer
    assert result.fallback_used


def test_brain_renderer_rejects_conversational_or_unrouted_inputs():
    with pytest.raises(ValueError):
        render_brain_answer(canonical('A regra vale.'), TODD)
    with pytest.raises(ValueError):
        render_brain_answer(brain_answer().model_copy(update={'mode': AnswerMode.CONVERSATIONAL}), TODD)
