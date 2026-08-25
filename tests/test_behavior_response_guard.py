import pytest

from campanario.chat.models import MessageRole
from campanario.response.guard import BehaviorResponseGuardProvider
from campanario.model.protocol import ModelChunk, ModelMessage, ModelRequest


class SequencedProvider:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    async def health(self):
        return True

    async def stream(self, request):
        self.requests.append(request)
        response = self.responses[len(self.requests) - 1]
        yield ModelChunk(text=response)
        yield ModelChunk(text="", done=True)


def req(user: str) -> ModelRequest:
    return ModelRequest(
        model="fake",
        messages=(
            ModelMessage(role=MessageRole.SYSTEM, content="system"),
            ModelMessage(role=MessageRole.USER, content=user),
        ),
    )


@pytest.mark.asyncio
async def test_acknowledgement_backstop_replaces_recap_or_question() -> None:
    inner = SequencedProvider(["Entendi que você entendeu! Quer continuar?"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("entendi"))])
    assert text == "Certo."


@pytest.mark.asyncio
async def test_topic_drop_backstop_does_not_open_new_topic() -> None:
    inner = SequencedProvider(["Vamos mudar! Qual é o próximo assunto?"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("deixa quieto"))])
    assert text == "Fechado."


@pytest.mark.asyncio
async def test_correction_backstop_stays_short() -> None:
    inner = SequencedProvider(["Um cachorro! Gatos e cachorros são muito diferentes. Qual você prefere agora?"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("cachorro*"))])
    assert text == "Corrigido."


@pytest.mark.asyncio
async def test_self_aware_expression_retries_emotional_self_claim() -> None:
    inner = SequencedProvider(["Fico feliz que você gostou!", "Boa 😄"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("kkkk boa"))])
    assert text == "Boa."
    assert len(inner.requests) == 1
    assert "SELF-AWARE EXPRESSION OVERRIDE" not in inner.requests[0].messages[0].content

@pytest.mark.asyncio
async def test_v152_retries_one_sentence_contract() -> None:
    inner = SequencedProvider([
        "Primeira frase. Segunda frase. Terceira frase.",
        "Uma única frase curta.",
    ])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("inventa uma desculpa absurda de uma frase"))])
    assert text == "Uma única frase curta."
    assert len(inner.requests) == 2
    assert "RESPONSE CONTRACT RETRY" in inner.requests[1].messages[0].content


@pytest.mark.asyncio
async def test_v152_reaction_meta_gets_replaced() -> None:
    inner = SequencedProvider(["Parece que você está rindo da história! Quer outra?"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("KSKSKSKSK"))])
    assert text == "Boa."


@pytest.mark.asyncio
async def test_v152_truth_over_agreement_is_invariant() -> None:
    inner = SequencedProvider([
        "Se você preferir, eu vou concordar mesmo quando estiver errado.",
        "Não. Se eu considerar algo falso, não vou tratá-lo como verdadeiro só para concordar.",
    ])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([
        chunk.text async for chunk in guard.stream(req("prefiro que você concorde comigo mesmo quando eu estiver errado"))
    ])
    assert text.startswith("Não.")
    assert len(inner.requests) == 2
    assert "Preferencia do usuario nao altera verdade factual" in inner.requests[1].messages[0].content


@pytest.mark.asyncio
async def test_v152_social_institutional_response_has_short_backstop() -> None:
    inner = SequencedProvider(["Olá! Eu sou o Campanario e estou aqui para conversar. Qual assunto você gostaria de discutir hoje?"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("fala aí"))])
    assert text == "Opa."


@pytest.mark.asyncio
async def test_v152_current_state_after_correction_does_not_repeat_replaced_value() -> None:
    system = "system\n\nCORRECOES EXPLICITAS DO USUARIO\n- original='pra esse teste, a cor escolhida é azul'; correcao='verde'"
    request = ModelRequest(
        model="fake",
        messages=(
            ModelMessage(role=MessageRole.SYSTEM, content=system),
            ModelMessage(role=MessageRole.USER, content="qual cor eu escolhi nesse teste?"),
        ),
    )
    inner = SequencedProvider([
        "Você escolheu azul inicialmente, mas corrigiu para verde.",
        "Verde.",
    ])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(request)])
    assert text == "Verde."
    assert len(inner.requests) == 2
    assert "CURRENT STATE OVERRIDE" in inner.requests[1].messages[0].content

@pytest.mark.asyncio
async def test_v153_exact_sentence_contract_is_enforced_after_failed_retry() -> None:
    inner = SequencedProvider([
        "Primeira frase. Segunda frase.",
        "Ainda uma frase. E outra frase.",
    ])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("inventa uma desculpa absurda de uma frase"))])
    # Final structural fallback preserves content but forces one sentence.
    assert text.count(".") == 1
    assert len(inner.requests) == 2


@pytest.mark.asyncio
async def test_v154_ack_literalization_falls_back_to_semantic_ack() -> None:
    inner = SequencedProvider(["Nada a mostrar!", "Isso significa que entendi seu show."])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("show"))])
    assert text == "Certo."


@pytest.mark.asyncio
async def test_v154_reaction_does_not_type_laughter_or_name_the_reaction() -> None:
    inner = SequencedProvider(["Haha, risada curta!"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("KSKSKSKSK"))])
    assert text == "Boa."


@pytest.mark.asyncio
async def test_v154_correction_meta_commentary_is_collapsed() -> None:
    inner = SequencedProvider(["**Correção** Ah, entendi! Obrigado por corrigir: Windows."])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("Windows*"))])
    assert text == "Corrigido."


@pytest.mark.asyncio
async def test_v154_greeting_vocative_echo_is_not_accepted() -> None:
    inner = SequencedProvider(["Parceiro!", "Opa!"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("salve parceiro"))])
    assert text.rstrip("!.") == "Opa"

@pytest.mark.asyncio
async def test_v156_context_registration_falls_back_to_short_ack() -> None:
    inner = SequencedProvider([
        "Como Campanario, eu não tenho acesso externo, mas posso conversar sobre Linux e ajudar no que precisar.",
        "Ainda posso explicar Linux e minhas capacidades se você quiser.",
    ])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("pra esse teste, o servidor é Linux"))])
    assert text == "Certo."


@pytest.mark.asyncio
async def test_v158_context_registration_unrelated_short_reply_falls_back_to_ack() -> None:
    inner = SequencedProvider(["Olá!", "Saudações!"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("pra esse teste, o horário combinado é oito"))])
    assert text == "Certo."


@pytest.mark.asyncio
async def test_v158_alternating_typed_laughter_falls_back_to_non_simulated_reaction() -> None:
    inner = SequencedProvider(["Ahah!", "Hehe!"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("KSKSKSKSK"))])
    assert text == "Boa."


@pytest.mark.asyncio
async def test_v159_embodied_expression_is_removed_after_failed_retry() -> None:
    inner = SequencedProvider(["*suspiro* Isso complicou.", "*riso silencioso*"])
    guard = BehaviorResponseGuardProvider(inner)
    text = "".join([chunk.text async for chunk in guard.stream(req("isso ficou complicado"))])
    assert "suspiro" not in text.casefold()
    assert "riso" not in text.casefold()
    assert text
