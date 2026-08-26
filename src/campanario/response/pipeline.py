import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from campanario.chat.turns import ContinuationKind, ConversationTurnInterpreter, TurnInterpretation, TurnMode
from campanario.chat.models import MessageRole
from campanario.chat.pragmatics import PragmaticAct
from campanario.model.protocol import ModelMessage, ModelProvider, ModelRequest
from campanario.response.contract import ContractViolation, ResponseContract, ResponseContractPolicy, ResponseKind

logger = logging.getLogger(__name__)

_SELF_AWARE_RETRY = """SELF-AWARE EXPRESSION OVERRIDE

Voce sabe que e uma inteligencia artificial. Nao declare sentimentos, sensacoes ou experiencias
subjetivas humanas como se fossem estados internos reais. Compreender o estado emocional do usuario
nao significa fingir sentir o mesmo. Mantenha personalidade, humor, opiniao e naturalidade sem
antropomorfizacao emocional. Emojis podem sinalizar tom de forma paralinguistica quando fizer sentido.
"""

_EMOTIONAL_SELF_CLAIMS = (
    "estou feliz", "fico feliz", "eu sinto muito", "sinto muito", "eu adoro", "eu amo",
    "eu sabia que voce iria gostar", "eu sabia que você iria gostar", "eu tambem achei engraçado",
    "eu também achei engraçado", "eu tambem estou rindo", "eu também estou rindo",
    "conexao emocional", "conexão emocional",
)

_INSTITUTIONAL_SOCIAL = (
    "como campanario", "como campanário", "eu sou o campanario", "eu sou o campanário",
    "qual assunto", "qual e o seu tom", "qual é o seu tom", "como posso ajudar",
)


@dataclass(frozen=True, slots=True)
class ResponseTurnPlan:
    user_text: str
    recent_user_context: str
    interpretation: TurnInterpretation
    contract: ResponseContract


@dataclass(frozen=True, slots=True)
class PipelineAttempt:
    stage: str
    text: str
    violations: tuple[ContractViolation, ...]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    text: str
    attempts: tuple[PipelineAttempt, ...]


class ResponseContractPipeline:
    """Explicit response pipeline: plan -> generate -> validate -> repair -> finalize.

    The model owns open-ended content. The pipeline owns objective conversational contracts and
    deterministic closed-class repairs. This keeps behavior rules out of an ever-growing prompt-only
    strategy and makes each stage independently testable.
    """

    _CLOSED_CLASS_CODES = {
        "reaction_meta", "simulated_laughter", "embodied_expression", "ack_literalization",
        "greeting_mirror", "topic_drop_semantics", "context_registration",
    }

    def __init__(
        self,
        inner: ModelProvider,
        *,
        interpreter: ConversationTurnInterpreter | None = None,
        contracts: ResponseContractPolicy | None = None,
    ) -> None:
        self._inner = inner
        self._interpreter = interpreter or ConversationTurnInterpreter()
        self._contracts = contracts or ResponseContractPolicy()

    async def health(self) -> bool:
        return await self._inner.health()

    async def execute(self, request: ModelRequest) -> PipelineResult:
        plan = self.compile_plan(request)
        if not plan.user_text:
            text = await self._collect(request)
            return PipelineResult(text=text, attempts=(PipelineAttempt("generate", text, ()),))

        attempts: list[PipelineAttempt] = []
        initial_request = self._append_system_override(
            request,
            self._contracts.initial_instruction(plan.contract, plan.interpretation),
        )
        draft = await self._collect(initial_request)

        # Current-state correction is a dedicated semantic stage. Historical text remains persisted,
        # but when the user asks for the current value we first ask the model to answer only with the
        # corrected state; deterministic fallback is used only if it still recites the replaced value.
        pair = self._latest_correction_pair(request)
        if pair and self._asks_current_state(plan.user_text) and self._mentions_replaced_value(draft, pair):
            state_request = self._append_system_override(
                initial_request,
                "CURRENT STATE OVERRIDE\nResponda apenas com o estado/valor corrigido vigente. Nao mencione o valor substituido, salvo se o usuario pedir historico.",
            )
            state_text = await self._collect(state_request)
            state_violations = self._validate(plan, state_text)
            attempts.append(PipelineAttempt("current_state_repair", state_text, state_violations))
            if self._mentions_replaced_value(state_text, pair):
                state_text = pair[1]
            if not state_violations:
                return PipelineResult(state_text, tuple(attempts))
            draft = state_text

        violations = self._validate(plan, draft)
        attempts.append(PipelineAttempt("generate", draft, violations))
        if not violations:
            return PipelineResult(draft, tuple(attempts))

        closed = self._closed_class_repair(draft, plan, violations)
        if closed is not None:
            closed_violations = self._validate(plan, closed)
            attempts.append(PipelineAttempt("deterministic_repair", closed, closed_violations))
            if not closed_violations:
                return PipelineResult(self._resolve_current_state(request, plan, closed), tuple(attempts))

        logger.info(
            "response_pipeline_repair codes=%s mode=%s",
            ",".join(item.code for item in violations),
            plan.interpretation.mode.value,
        )
        repair_override = self._contracts.retry_instruction(plan.contract, violations)
        if any(item.code == "emotional_self_claim" for item in violations):
            repair_override = f"{_SELF_AWARE_RETRY.strip()}\n\n{repair_override}"
        repair_request = self._append_system_override(initial_request, repair_override)
        repaired = await self._collect(repair_request)
        repaired_violations = self._validate(plan, repaired)
        attempts.append(PipelineAttempt("model_repair", repaired, repaired_violations))
        if not repaired_violations:
            return PipelineResult(self._resolve_current_state(request, plan, repaired), tuple(attempts))

        enforced = self._contracts.enforce_after_retry(repaired, plan.contract, repaired_violations)
        enforced_violations = self._validate(plan, enforced)
        attempts.append(PipelineAttempt("structural_enforcement", enforced, enforced_violations))
        if not enforced_violations:
            return PipelineResult(self._resolve_current_state(request, plan, enforced), tuple(attempts))

        fallback = self._safe_fallback(enforced, plan, enforced_violations)
        fallback_violations = self._validate(plan, fallback)
        attempts.append(PipelineAttempt("safe_fallback", fallback, fallback_violations))
        return PipelineResult(self._resolve_current_state(request, plan, fallback), tuple(attempts))

    def compile_plan(self, request: ModelRequest) -> ResponseTurnPlan:
        current = self._latest_user_text(request)
        interpretation = self._interpreter.interpret_text(current) if current else self._interpreter.interpret_text("")
        context = self._recent_user_context(request)
        contract = self._contracts.derive(current, interpretation, context_text=context)
        return ResponseTurnPlan(
            user_text=current,
            recent_user_context=context,
            interpretation=interpretation,
            contract=contract,
        )

    def _validate(self, plan: ResponseTurnPlan, text: str) -> tuple[ContractViolation, ...]:
        violations = list(self._contracts.validate(plan.user_text, text, plan.contract))
        if (
            plan.contract.kind in {
                ResponseKind.SELF_AWARE, ResponseKind.OPEN, ResponseKind.SOCIAL_SHARE,
                ResponseKind.TRUTH_DISCUSSION, ResponseKind.REACTION, ResponseKind.GREETING,
                ResponseKind.ACKNOWLEDGEMENT, ResponseKind.TOPIC_DROP, ResponseKind.CONTEXT_REGISTRATION,
            }
            and self._has_emotional_self_claim(text)
        ):
            violations.append(ContractViolation("emotional_self_claim", "assistant_claimed_human_emotion"))
        return tuple(violations)

    async def _collect(self, request: ModelRequest) -> str:
        parts: list[str] = []
        async for chunk in self._inner.stream(request):
            if chunk.text:
                parts.append(chunk.text)
            if chunk.done:
                break
        return "".join(parts).strip()

    def _closed_class_repair(
        self,
        text: str,
        plan: ResponseTurnPlan,
        violations: tuple[ContractViolation, ...],
    ) -> str | None:
        codes = {item.code for item in violations}
        kind = plan.contract.kind

        # Typed repairs: a turn can only use a repair compatible with its compiled response kind.
        if kind == ResponseKind.CONTEXT_REGISTRATION:
            return "Certo."
        if kind == ResponseKind.CORRECTION:
            return "Corrigido."
        if kind == ResponseKind.GREETING:
            return "Opa."
        if kind == ResponseKind.REACTION:
            return "Boa."
        if kind == ResponseKind.ACKNOWLEDGEMENT:
            return "Certo."
        if kind == ResponseKind.TOPIC_DROP:
            return "Fechado."

        # Self-awareness remains open-ended enough to deserve one model repair. It must never hijack
        # creative/factual/technical turns merely because generated prose contains first-person words.
        if kind == ResponseKind.SELF_AWARE:
            return None

        if "embodied_expression" in codes and kind in {ResponseKind.OPEN, ResponseKind.SOCIAL_SHARE, ResponseKind.TRUTH_DISCUSSION}:
            cleaned = self._strip_embodied_stage_directions(text)
            if cleaned and not self._contracts.validate(plan.user_text, cleaned, plan.contract):
                return cleaned
        return None

    def _safe_fallback(
        self,
        text: str,
        plan: ResponseTurnPlan,
        violations: tuple[ContractViolation, ...],
    ) -> str:
        codes = {item.code for item in violations}
        compact = " ".join(text.split())
        kind = plan.contract.kind

        typed_fallbacks = {
            ResponseKind.TRUTH_DISCUSSION: "Não. Se eu considerar algo falso, não vou tratá-lo nem simulá-lo como verdadeiro só para concordar com você.",
            ResponseKind.SELF_AWARE: "Sou o Campanario, uma IA. Posso reconhecer o tom da conversa e responder de forma compatível, mas não sinto emoções como uma pessoa.",
            ResponseKind.CONTEXT_REGISTRATION: "Certo.",
            ResponseKind.CORRECTION: "Corrigido.",
            ResponseKind.GREETING: "Opa.",
            ResponseKind.REACTION: "Boa.",
            ResponseKind.ACKNOWLEDGEMENT: "Certo.",
            ResponseKind.TOPIC_DROP: "Fechado.",
            ResponseKind.SOCIAL_SHARE: "Entendi.",
        }
        if kind in typed_fallbacks:
            return typed_fallbacks[kind]

        if "meta_preamble" in codes:
            cleaned = self._strip_meta_preamble(compact)
            if cleaned and cleaned != compact:
                return cleaned

        # Creative, factual and technical fallbacks never borrow social/self-awareness templates.
        # Returning the repaired content makes model limitations visible to E2E rather than replacing
        # them with a semantically unrelated canned answer.
        return compact

    def _resolve_current_state(self, request: ModelRequest, plan: ResponseTurnPlan, text: str) -> str:
        pair = self._latest_correction_pair(request)
        if not pair or not self._asks_current_state(plan.user_text):
            return text
        if not self._mentions_replaced_value(text, pair):
            return text
        return pair[1]

    @staticmethod
    def _append_system_override(request: ModelRequest, override: str) -> ModelRequest:
        if not override.strip():
            return request
        messages = list(request.messages)
        if messages and messages[0].role == MessageRole.SYSTEM:
            messages[0] = ModelMessage(
                role=MessageRole.SYSTEM,
                content=f"{messages[0].content.rstrip()}\n\n{override.strip()}\n",
            )
        else:
            messages.insert(0, ModelMessage(role=MessageRole.SYSTEM, content=override.strip()))
        return ModelRequest(model=request.model, messages=tuple(messages), response_format=request.response_format, temperature=request.temperature, max_output_tokens=request.max_output_tokens, context_window=request.context_window)

    @staticmethod
    def _recent_user_context(request: ModelRequest, limit: int = 3) -> str:
        texts = [message.content for message in request.messages if message.role == MessageRole.USER]
        return "\n".join(texts[-limit:])

    @staticmethod
    def _latest_user_text(request: ModelRequest) -> str:
        for message in reversed(request.messages):
            if message.role == MessageRole.USER:
                return message.content
        return ""

    @staticmethod
    def _has_emotional_self_claim(text: str) -> bool:
        folded = " ".join(text.casefold().split())
        return any(marker in folded for marker in _EMOTIONAL_SELF_CLAIMS)

    @staticmethod
    def _latest_correction_pair(request: ModelRequest) -> tuple[str, str] | None:
        if not request.messages or request.messages[0].role != MessageRole.SYSTEM:
            return None
        matches = list(
            re.finditer(
                r"- original=(?P<q>['\"])(?P<original>.*?)(?P=q); correcao=(?P<cq>['\"])(?P<corrected>.*?)(?P=cq)",
                request.messages[0].content,
            )
        )
        if not matches:
            return None
        match = matches[-1]
        return match.group("original"), match.group("corrected")

    @staticmethod
    def _asks_current_state(text: str) -> bool:
        folded = " ".join(text.casefold().split())
        return any(marker in folded for marker in ("qual ", "o que ficou", "qual ficou", "defini", "escolhi", "combinado"))

    @staticmethod
    def _mentions_replaced_value(text: str, pair: tuple[str, str]) -> bool:
        original, corrected = pair
        folded = text.casefold()
        stop = {
            "pra", "para", "esse", "essa", "teste", "o", "a", "é", "e", "foi", "fica", "ficou",
            "servidor", "cor", "horário", "horario", "sistema", "escolhida", "escolhido", "combinado",
        }
        tokens = [token.strip(".,:;!?()[]{}\"'").casefold() for token in original.split()]
        candidates = [token for token in tokens if len(token) >= 3 and token not in stop]
        corrected_folded = corrected.casefold()
        return any(token in folded and token not in corrected_folded for token in candidates[-3:])

    @staticmethod
    def _strip_embodied_stage_directions(text: str) -> str:
        cleaned = text
        patterns = (
            r"[\*_]\s*(?:riso silencioso|risada silenciosa|riso|risada|sorriso|sorri|sorrindo|rio|ri|rindo|suspiro|suspiro fundo|respiro fundo|pisca|piscadela|abraco|abraço|aceno|acena|balanco a cabeca|balanço a cabeça)\s*[\*_]",
            r"^\s*\((?:riso silencioso|risada silenciosa|riso|risos|risada|risadas|sorri|sorrindo|suspiro|piscadela|aceno)\)\s*",
        )
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return " ".join(cleaned.split()).strip(" -—:;,")

    @staticmethod
    def _strip_meta_preamble(text: str) -> str:
        compact = " ".join(text.split()).strip()
        compact = re.sub(r"^(?:\*\*)?(?:resposta tecnica|correcao|correção)(?:\*\*)?\s*[:.-]?\s*", "", compact, flags=re.IGNORECASE)
        compact = re.sub(
            r"^(?:here are|aqui (?:estao|estão|vai|vao|vão)|seguem?|vou responder)[^:]{0,90}:\s*",
            "", compact, flags=re.IGNORECASE,
        )
        parts = re.split(r"(?<=[.!?])\s+", compact, maxsplit=1)
        if len(parts) == 2:
            folded = parts[0].casefold()
            markers = (
                "excelente escolha", "excelente pergunta", "ótima pergunta", "otima pergunta",
                "interessante pergunta", "vou ajudar", "vamos falar sério", "vamos falar serio",
                "agora sim", "como campanario", "entendi melhor agora", "obrigado por corrigir",
                "um problema técnico", "um problema tecnico",
            )
            if any(marker in folded for marker in markers):
                return parts[1].strip()
        return compact
