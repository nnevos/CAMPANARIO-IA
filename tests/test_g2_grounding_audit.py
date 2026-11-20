"""Agnostic evidence verification, not question-specific replacement rules."""
from __future__ import annotations

import pytest
import campanario.composition as composition
from campanario.config import Settings
from campanario.model.protocol import ModelChunk
from campanario.chat.memory_grounding import verdict_supported, is_personal_question


class EvidenceAwareFake:
    def __init__(self, proposed, verdict):
        self.proposed = proposed
        self.verdict = verdict
        self.calls = []

    async def health(self):
        return True

    async def stream(self, request):
        self.calls.append(request)
        audit = any('AUDITORIA DE EVIDENCIA PESSOAL' in m.content for m in request.messages)
        answer = self.verdict if audit else self.proposed
        # Multiple chunks: ensure an ungrounded answer is never displayed early.
        for part in (answer[:len(answer)//2], answer[len(answer)//2:]):
            yield ModelChunk(text=part)
        yield ModelChunk(text='', done=True)


@pytest.mark.asyncio
@pytest.mark.parametrize('statement,question,unsupported', [
    ('gosto de comida tailandesa', 'qual minha comida favorita?', 'Sua favorita é comida tailandesa.'),
    ('pretendo estudar engenharia', 'qual curso eu já terminei?', 'Você se formou em engenharia.'),
    ('talvez me mude para Recife', 'onde eu moro?', 'Você mora em Recife.'),
    ('uso o editor Helix', 'qual é o único editor que eu uso?', 'Você só usa Helix.'),
    ('meu hobby é caminhar', 'em que esporte sou profissional?', 'Você é atleta profissional de caminhada.'),
])
async def test_false_claim_never_streamed_or_saved(monkeypatch, tmp_path, statement, question, unsupported):
    provider = EvidenceAwareFake(unsupported, '{"supported":false}')
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "g.db"}', create_schema=True)
    one = rt.sessions.create_session()
    _ = [x async for x in rt.conversation.stream_turn(one.id, statement)]
    two = rt.sessions.create_session()
    events = [x async for x in rt.conversation.stream_turn(two.id, question)]
    displayed = ''.join(x.text for x in events if x.type == 'token')
    assert unsupported not in displayed
    assert statement in displayed or displayed == "Não tenho uma informação confirmada sobre isso."
    assert rt.conversation.get_messages(two.id)[-1].content == displayed.strip()
    assert any('AUDITORIA DE EVIDENCIA PESSOAL' in m.content for req in provider.calls for m in req.messages)


@pytest.mark.asyncio
async def test_grounded_answer_keeps_model_voice(monkeypatch, tmp_path):
    provider = EvidenceAwareFake('Você comentou que gosta de música clássica.', '{"supported":true,"quotes":["gosto de música clássica"]}')
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "g.db"}', create_schema=True)
    one = rt.sessions.create_session()
    _ = [x async for x in rt.conversation.stream_turn(one.id, 'gosto de música clássica')]
    two = rt.sessions.create_session()
    events = [x async for x in rt.conversation.stream_turn(two.id, 'que música eu gosto?')]
    assert ''.join(x.text for x in events if x.type == 'token') == 'Você comentou que gosta de música clássica.'


def test_verdict_fail_closed():
    for output in ('', 'sim', '{"supported":"true"}', '{"supported":false}', '{invalid'):
        assert not verdict_supported(output)
    assert not verdict_supported('{"supported":true}')
    assert verdict_supported('{"supported":true,"quotes":["gosto de música clássica"]}', evidence=('- gosto de música clássica',), answer='Você gosta de música clássica.')
    assert is_personal_question('Qual é minha ferramenta de trabalho?')
    assert not is_personal_question('Como funciona o Python?')

@pytest.mark.asyncio
@pytest.mark.parametrize('statement,question,answer', [
    ('gosto do carro R34', 'qual meu carro favorito?', 'Seu carro favorito é o R34.'),
    ('gosto de jazz', 'qual meu estilo musical favorito?', 'Seu estilo musical favorito é jazz.'),
    ('uso uma bicicleta', 'qual meu único transporte?', 'Você usa somente bicicleta.'),
    ('tenho interesse em astronomia', 'qual é meu maior interesse?', 'Seu maior interesse é astronomia.'),
])
async def test_false_positive_verifier_cannot_authorize_strengthening(monkeypatch, tmp_path, statement, question, answer):
    # The verifier itself lies and approves with a real quotation. The independent
    # evidence gate must not promote a weak statement to an absolute one.
    provider = EvidenceAwareFake(answer, '{"supported":true,"quotes":["' + statement + '"]}')
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "m.db"}', create_schema=True)
    first = rt.sessions.create_session()
    _ = [event async for event in rt.conversation.stream_turn(first.id, statement)]
    second = rt.sessions.create_session()
    events = [event async for event in rt.conversation.stream_turn(second.id, question)]
    displayed = ''.join(event.text for event in events if event.type == 'token')
    assert answer not in displayed
    assert statement in displayed or displayed == "Não tenho uma informação confirmada sobre isso."
    assert rt.conversation.get_messages(second.id)[-1].content == displayed.strip()


def test_spurious_quotes_and_bare_approval_are_not_proof():
    evidence = ('- gosto de carros antigos',)
    assert not verdict_supported('{"supported":true}', evidence=evidence, answer='Você gosta de carros antigos.')
    assert not verdict_supported('{"supported":true,"quotes":["meu carro favorito"]}', evidence=evidence, answer='Seu carro favorito é antigo.')
    assert not verdict_supported('{"supported":true,"quotes":["gosto de carros antigos"]}', evidence=evidence, answer='Seu carro favorito é antigo.')
    assert verdict_supported('{"supported":true,"quotes":["gosto de carros antigos"]}', evidence=evidence, answer='Você gosta de carros antigos.')


class RepairAwareFake:
    def __init__(self, *, repair, repair_verdict):
        self.calls = []
        self.repair = repair
        self.repair_verdict = repair_verdict

    async def health(self):
        return True

    async def stream(self, request):
        self.calls.append(request)
        content = "\n".join(m.content for m in request.messages)
        if "REPARO DE RESPOSTA FUNDAMENTADA" in content:
            answer = self.repair
        elif "AUDITORIA DE EVIDENCIA PESSOAL" in content:
            audits = sum(any("AUDITORIA DE EVIDENCIA PESSOAL" in m.content for m in req.messages) for req in self.calls)
            answer = '{"supported":false,"quotes":[]}' if audits == 1 else self.repair_verdict
        else:
            answer = "Você me disse algo, mas não consigo responder."
        yield ModelChunk(text=answer)
        yield ModelChunk(text="", done=True)


@pytest.mark.asyncio
async def test_rejected_answer_can_be_repaired_by_semantic_entailment(monkeypatch, tmp_path):
    provider = RepairAwareFake(
        repair="Você está usando o Blender para estudar animação de personagens.",
        repair_verdict='{"supported":true,"quotes":["Estou estudando animação de personagens no Blender."]}',
    )
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "repair.db"}', create_schema=True)
    first = rt.sessions.create_session()
    _ = [x async for x in rt.conversation.stream_turn(first.id, 'Estou estudando animação de personagens no Blender.')]
    second = rt.sessions.create_session()
    events = [x async for x in rt.conversation.stream_turn(second.id, 'Qual ferramenta estou usando para aprender animação?')]
    displayed = ''.join(x.text for x in events if x.type == 'token')
    assert displayed == "Você está usando o Blender para estudar animação de personagens."
    assert rt.conversation.get_messages(second.id)[-1].content == displayed
    assert any('REPARO DE RESPOSTA FUNDAMENTADA' in m.content for req in provider.calls for m in req.messages)


@pytest.mark.asyncio
async def test_repair_cannot_bypass_verifier_or_strength_gate(monkeypatch, tmp_path):
    provider = RepairAwareFake(
        repair="Blender é sua única ferramenta favorita e você é animador profissional.",
        repair_verdict='{"supported":true,"quotes":["Estou estudando animação de personagens no Blender."]}',
    )
    monkeypatch.setattr(composition, 'build_model_provider', lambda _: provider)
    rt = composition.build_runtime(Settings(model_name='fake', low_latency_mode=True, live_streaming=True),
        database_url=f'sqlite:///{tmp_path / "reject.db"}', create_schema=True)
    first = rt.sessions.create_session()
    _ = [x async for x in rt.conversation.stream_turn(first.id, 'Estou estudando animação de personagens no Blender.')]
    second = rt.sessions.create_session()
    events = [x async for x in rt.conversation.stream_turn(second.id, 'Qual ferramenta estou usando para aprender animação?')]
    displayed = ''.join(x.text for x in events if x.type == 'token')
    assert 'animador profissional' not in displayed
    assert 'Estou estudando animação de personagens no Blender.' in displayed
