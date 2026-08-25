import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from campanario.chat.models import ContextSummary, Message, MessageRole
from campanario.chat.repositories import ContextSummaryRepository
from campanario.model.protocol import ModelMessage, ModelProvider, ModelProviderError, ModelRequest

logger = logging.getLogger(__name__)

_SUMMARY_VERSION = 1
_SUMMARY_LIST_FIELDS = (
    "user_facts",
    "user_preferences",
    "user_plans",
    "user_constraints",
    "conversation_topics",
    "assistant_context",
)


class ContextManager(Protocol):
    async def build(self, history: Sequence[Message]) -> tuple[ModelMessage, ...]: ...


class RecentMessagesContextManager:
    """Select a deterministic recent-message window for the model request."""

    def __init__(self, max_messages: int) -> None:
        if max_messages < 1:
            raise ValueError("max_messages must be at least 1")
        self._max_messages = max_messages

    def select(self, history: Sequence[Message]) -> tuple[Message, ...]:
        completed = [message for message in history if message.status == "completed"]
        selected = completed[-self._max_messages :]
        if len(completed) > len(selected) and selected and selected[0].role == MessageRole.ASSISTANT:
            selected = selected[1:]
        return tuple(selected)

    async def build(self, history: Sequence[Message]) -> tuple[ModelMessage, ...]:
        selected = self.select(history)
        completed_count = sum(message.status == "completed" for message in history)
        logger.debug(
            "context_selected total_completed=%d selected=%d max_messages=%d",
            completed_count,
            len(selected),
            self._max_messages,
        )
        return tuple(ModelMessage(role=message.role, content=message.content) for message in selected)


class SummarizingContextManager:
    """Persist a source-aware summary of old chat while retaining a recent window verbatim."""

    def __init__(
        self,
        max_messages: int,
        summaries: ContextSummaryRepository,
        model_provider: ModelProvider,
        model: str,
        max_summary_chars: int = 4000,
    ) -> None:
        self._recent = RecentMessagesContextManager(max_messages)
        self._summaries = summaries
        self._provider = model_provider
        self._model = model
        self._max_summary_chars = max_summary_chars

    async def build(self, history: Sequence[Message]) -> tuple[ModelMessage, ...]:
        completed = [message for message in history if message.status == "completed"]
        recent = self._recent.select(completed)
        if len(completed) <= len(recent):
            return tuple(ModelMessage(role=m.role, content=m.content) for m in recent)

        recent_ids = {message.id for message in recent}
        old = [message for message in completed if message.id not in recent_ids]
        if not old:
            return tuple(ModelMessage(role=m.role, content=m.content) for m in recent)

        session_id = completed[0].session_id
        current = self._summaries.get(session_id)
        first_user_message = next(
            (m.content.strip() for m in completed if m.role == MessageRole.USER and m.content.strip()),
            "",
        )

        current_data = self._parse_summary(current.content) if current is not None else None
        legacy_summary = current is not None and current_data is None

        if legacy_summary:
            # Resumos livres antigos podem conter contaminacao do assistant. Reconstroi o trecho
            # antigo inteiro usando o formato source-aware em vez de promovê-lo a evidencia.
            new_old = old
            previous_summary = None
        else:
            already_covered_index = -1
            if current is not None:
                for index, message in enumerate(old):
                    if message.id == current.through_message_id:
                        already_covered_index = index
                        break
            new_old = old[already_covered_index + 1 :]
            previous_summary = current_data

        if new_old:
            try:
                summary_data = await self._summarize(previous_summary, new_old, first_user_message)
                summary_text = self._serialize_summary(summary_data)
                saved = ContextSummary(
                    session_id=session_id,
                    content=summary_text,
                    through_message_id=old[-1].id,
                    updated_at=datetime.now(UTC),
                )
                self._summaries.upsert(saved)
                current = saved
                current_data = summary_data
            except ModelProviderError:
                logger.warning("context_summary_update_failed session_id=%s", session_id, exc_info=True)

        result: list[ModelMessage] = []
        if current_data is not None:
            result.append(
                ModelMessage(
                    role=MessageRole.SYSTEM,
                    content=self._context_message(current_data),
                )
            )
        result.extend(ModelMessage(role=m.role, content=m.content) for m in recent)
        logger.debug(
            "context_summary_selected total_completed=%d summarized_old=%d recent=%d "
            "has_summary=%s legacy_rebuilt=%s",
            len(completed),
            len(old),
            len(recent),
            current_data is not None,
            legacy_summary,
        )
        return tuple(result)

    async def _summarize(
        self,
        previous_summary: dict[str, object] | None,
        messages: Sequence[Message],
        first_user_message: str,
    ) -> dict[str, object]:
        user_messages = [m.content for m in messages if m.role == MessageRole.USER]
        assistant_messages = [m.content for m in messages if m.role == MessageRole.ASSISTANT]
        other_messages = [
            f"{m.role.value}: {m.content}"
            for m in messages
            if m.role not in (MessageRole.USER, MessageRole.ASSISTANT)
        ]

        previous_user = self._authoritative_projection(previous_summary, first_user_message)
        user_prompt = f"""Atualize SOMENTE os campos autoritativos derivados de mensagens USER.

REGRAS OBRIGATORIAS:
1. Voce NAO recebera mensagens ASSISTANT nesta etapa. Nao invente o que elas possam ter dito.
2. Extraia apenas fatos pessoais, preferencias, planos, escolhas, identificadores e restricoes
   explicitamente declarados pelo USER.
3. Nao transforme perguntas em fatos. Preserve codigos, nomes, numeros e listas exatamente.
4. Se o resumo anterior e uma nova mensagem USER entrarem em conflito, a declaracao USER mais
   recente pode atualizar o fato.
5. Retorne SOMENTE JSON valido no schema completo abaixo; deixe assistant_context vazio.

SCHEMA:
{{
  "version": 1,
  "first_user_message": "...",
  "user_facts": ["..."],
  "user_preferences": ["..."],
  "user_plans": ["..."],
  "user_constraints": ["..."],
  "conversation_topics": ["..."],
  "assistant_context": []
}}

RESUMO USER ANTERIOR:
{json.dumps(previous_user, ensure_ascii=False, separators=(",", ":"))}

PRIMEIRA MENSAGEM USER (ancora deterministica):
{first_user_message}

NOVAS MENSAGENS USER:
{json.dumps(user_messages, ensure_ascii=False)}

OUTRAS MENSAGENS NAO-ASSISTANT:
{json.dumps(other_messages, ensure_ascii=False)}

Mantenha o JSON conciso e dentro de {self._max_summary_chars} caracteres."""
        user_data = await self._request_structured_summary(user_prompt)
        user_data["first_user_message"] = first_user_message

        previous_assistant = self._assistant_projection(previous_summary)
        assistant_prompt = f"""Atualize SOMENTE contexto antigo produzido pelo ASSISTANT.

REGRAS OBRIGATORIAS:
1. Esta etapa NAO recebe fatos/preferencias/planos do USER e NAO pode produzir autoridade sobre eles.
2. Guarde em assistant_context apenas respostas/explicacoes antigas uteis para continuidade.
3. Texto do assistant pode estar errado; nao o promova a fato do usuario.
4. Retorne SOMENTE JSON valido no schema completo; mantenha todos os campos user_* vazios.

SCHEMA:
{{
  "version": 1,
  "first_user_message": "",
  "user_facts": [],
  "user_preferences": [],
  "user_plans": [],
  "user_constraints": [],
  "conversation_topics": ["..."],
  "assistant_context": ["..."]
}}

CONTEXTO ASSISTANT ANTERIOR:
{json.dumps(previous_assistant, ensure_ascii=False, separators=(",", ":"))}

NOVAS MENSAGENS ASSISTANT:
{json.dumps(assistant_messages, ensure_ascii=False)}

Mantenha o JSON conciso e dentro de {self._max_summary_chars} caracteres."""
        try:
            assistant_data = await self._request_structured_summary(assistant_prompt)
        except ModelProviderError:
            logger.warning("assistant_context_summary_failed", exc_info=True)
            assistant_data = previous_assistant

        merged = {
            "version": _SUMMARY_VERSION,
            "first_user_message": first_user_message,
            "user_facts": user_data["user_facts"],
            "user_preferences": user_data["user_preferences"],
            "user_plans": user_data["user_plans"],
            "user_constraints": user_data["user_constraints"],
            "conversation_topics": self._dedupe(
                [
                    *user_data["conversation_topics"],
                    *assistant_data["conversation_topics"],
                ]
            ),
            "assistant_context": assistant_data["assistant_context"],
        }
        return self._fit_summary(merged)

    async def _request_structured_summary(self, prompt: str) -> dict[str, object]:
        request = ModelRequest(
            model=self._model,
            messages=(ModelMessage(role=MessageRole.SYSTEM, content=prompt),),
        )
        parts: list[str] = []
        async for chunk in self._provider.stream(request):
            if chunk.text:
                parts.append(chunk.text)
        raw = "".join(parts).strip()
        if not raw:
            raise ModelProviderError("summary model returned empty content")
        parsed = self._parse_summary(raw)
        if parsed is None:
            raise ModelProviderError("summary model returned invalid structured content")
        return parsed

    def _authoritative_projection(
        self, previous_summary: dict[str, object] | None, first_user_message: str
    ) -> dict[str, object]:
        if previous_summary is None:
            previous_summary = {}
        return {
            "version": _SUMMARY_VERSION,
            "first_user_message": first_user_message,
            "user_facts": list(previous_summary.get("user_facts", [])),
            "user_preferences": list(previous_summary.get("user_preferences", [])),
            "user_plans": list(previous_summary.get("user_plans", [])),
            "user_constraints": list(previous_summary.get("user_constraints", [])),
            "conversation_topics": list(previous_summary.get("conversation_topics", [])),
            "assistant_context": [],
        }

    def _assistant_projection(
        self, previous_summary: dict[str, object] | None
    ) -> dict[str, object]:
        if previous_summary is None:
            previous_summary = {}
        return {
            "version": _SUMMARY_VERSION,
            "first_user_message": "",
            "user_facts": [],
            "user_preferences": [],
            "user_plans": [],
            "user_constraints": [],
            "conversation_topics": list(previous_summary.get("conversation_topics", [])),
            "assistant_context": list(previous_summary.get("assistant_context", [])),
        }

    def _dedupe(self, values: Sequence[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = value.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    def _parse_summary(self, content: str) -> dict[str, object] | None:
        try:
            data = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict) or data.get("version") != _SUMMARY_VERSION:
            return None
        if not isinstance(data.get("first_user_message"), str):
            return None
        for field in _SUMMARY_LIST_FIELDS:
            values = data.get(field)
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                return None
        return {
            "version": _SUMMARY_VERSION,
            "first_user_message": data["first_user_message"].strip(),
            **{
                field: [item.strip() for item in data[field] if item.strip()]
                for field in _SUMMARY_LIST_FIELDS
            },
        }

    def _serialize_summary(self, data: dict[str, object]) -> str:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    def _fit_summary(self, data: dict[str, object]) -> dict[str, object]:
        fitted = {
            "version": _SUMMARY_VERSION,
            "first_user_message": str(data.get("first_user_message", "")),
            **{field: list(data.get(field, [])) for field in _SUMMARY_LIST_FIELDS},
        }
        prune_order = (
            "assistant_context",
            "conversation_topics",
            "user_constraints",
            "user_plans",
            "user_preferences",
            "user_facts",
        )
        while len(self._serialize_summary(fitted)) > self._max_summary_chars:
            pruned = False
            for field in prune_order:
                values = fitted[field]
                if isinstance(values, list) and values:
                    values.pop()
                    pruned = True
                    break
            if not pruned:
                first = str(fitted["first_user_message"])
                if not first:
                    break
                fitted["first_user_message"] = first[:-1]
        return fitted

    def _context_message(self, summary: dict[str, object]) -> str:
        serialized = json.dumps(summary, ensure_ascii=False, indent=2)
        return (
            "CONTEXTO PERSISTIDO ESTRUTURADO DE PARTES ANTERIORES DESTA CONVERSA.\n"
            "Hierarquia obrigatoria: campos user_* e first_user_message derivam do usuario e "
            "tem prioridade sobre assistant_context. assistant_context e apenas continuidade e "
            "pode conter erros antigos; nunca o use para sobrescrever fatos do usuario. Se algo "
            "nao estiver neste contexto nem nas mensagens recentes, diga que nao tem essa "
            "informacao em vez de inventar. Este contexto foi carregado do armazenamento da "
            "sessao e pode sobreviver a reinicios; nao alegue perda de contexto apenas porque o "
            "programa foi reiniciado.\n\n"
            + serialized
        )
