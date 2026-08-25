import pytest

from campanario.chat.models import MessageRole
from campanario.model.protocol import ModelChunk, ModelMessage, ModelRequest
from campanario.response.pipeline import ResponseContractPipeline


class SequencedProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.requests: list[ModelRequest] = []

    async def health(self) -> bool:
        return True

    async def stream(self, request: ModelRequest):
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


def test_v160_compile_plan_derives_contract_before_generation() -> None:
    provider = SequencedProvider(["unused"])
    pipeline = ResponseContractPipeline(provider)
    plan = pipeline.compile_plan(req("responda somente com o resultado: 12 vezes 11"))
    assert plan.user_text.startswith("responda somente")
    assert plan.contract.active is True
    assert plan.contract.max_words is not None


@pytest.mark.asyncio
async def test_v160_first_generation_receives_compiled_turn_contract() -> None:
    provider = SequencedProvider(["144"])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(req("responda somente com o resultado: 16 vezes 9"))
    assert result.text == "144"
    assert len(provider.requests) == 1
    system = provider.requests[0].messages[0].content
    assert "CONTRATO DE RESPOSTA DO TURNO" in system
    assert "Estas regras valem somente para a resposta atual" in system


@pytest.mark.asyncio
async def test_v160_closed_class_repair_does_not_spend_second_generation() -> None:
    provider = SequencedProvider(["Risada silenciosa"])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(req("KSKSKSKSK"))
    assert result.text == "Boa."
    assert len(provider.requests) == 1
    assert [attempt.stage for attempt in result.attempts] == ["generate", "deterministic_repair"]


@pytest.mark.asyncio
async def test_v160_open_violation_uses_model_repair_stage() -> None:
    provider = SequencedProvider([
        "Esse erro pode ter várias causas. Depois verifique o log e o traceback.",
        "Verifique primeiro o log e o traceback da requisição que retornou 500.",
    ])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(req("numa API Python, por onde começo a investigar um HTTP 500?"))
    assert result.text.startswith("Verifique primeiro")
    assert len(provider.requests) == 2
    assert "RESPONSE CONTRACT RETRY" in provider.requests[1].messages[0].content
    assert [attempt.stage for attempt in result.attempts] == ["generate", "model_repair"]


@pytest.mark.asyncio
async def test_v160_current_state_is_an_explicit_pipeline_stage() -> None:
    request = ModelRequest(
        model="fake",
        messages=(
            ModelMessage(
                role=MessageRole.SYSTEM,
                content="system\n\nCORRECOES EXPLICITAS DO USUARIO\n- original='pra esse teste, a cor é azul'; correcao='verde'",
            ),
            ModelMessage(role=MessageRole.USER, content="qual cor ficou nesse teste?"),
        ),
    )
    provider = SequencedProvider([
        "Era azul, mas foi corrigida para verde.",
        "Verde.",
    ])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(request)
    assert result.text == "Verde."
    assert any(attempt.stage == "current_state_repair" for attempt in result.attempts)
    assert "CURRENT STATE OVERRIDE" in provider.requests[1].messages[0].content


def test_v160_contract_instruction_never_contains_domain_answer_key() -> None:
    provider = SequencedProvider(["unused"])
    pipeline = ResponseContractPipeline(provider)
    plan = pipeline.compile_plan(req("em uma frase, por que o céu parece azul?"))
    instruction = pipeline._contracts.initial_instruction(plan.contract, plan.interpretation).casefold()
    assert "rayleigh" not in instruction
    assert "espalhamento" not in instruction
    assert "mecanismo causal principal" in instruction


def test_v161_compile_plan_assigns_typed_response_kinds() -> None:
    from campanario.response.contract import ResponseKind

    pipeline = ResponseContractPipeline(SequencedProvider(["unused"]))
    assert pipeline.compile_plan(req("KSKSKSKSK")).contract.kind == ResponseKind.REACTION
    assert pipeline.compile_plan(req("crie exatamente duas frases sobre um gato astronauta")).contract.kind == ResponseKind.CREATIVE_EXACT
    assert pipeline.compile_plan(req("numa API Python, por onde começo a investigar um HTTP 500?")).contract.kind == ResponseKind.TECHNICAL_FIRST_STEP


@pytest.mark.asyncio
async def test_v161_creative_turn_cannot_fall_back_to_self_awareness() -> None:
    provider = SequencedProvider([
        "Eu sinto muito. A meia foi sequestrada por um buraco negro doméstico.",
        "A meia foi sequestrada por um buraco negro doméstico.",
    ])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(req("inventa uma desculpa absurda de uma frase pra eu ter perdido uma meia"))
    assert "Sou o Campanario" not in result.text
    assert "meia" in result.text.casefold()


@pytest.mark.asyncio
async def test_v161_reaction_emotional_claim_uses_reaction_repair_not_self_awareness() -> None:
    provider = SequencedProvider(["Fico feliz que você gostou!"])
    pipeline = ResponseContractPipeline(provider)
    result = await pipeline.execute(req("kkkk boa"))
    assert result.text == "Boa."
    assert "Sou o Campanario" not in result.text
