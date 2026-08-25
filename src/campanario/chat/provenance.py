"""Source authority and correction handling for conversation context."""

from collections.abc import Sequence

from campanario.chat.models import Message, MessageRole
from campanario.chat.pragmatics import PragmaticAct, PragmaticInterpreter
from campanario.chat.turns import ConversationTurnInterpreter, TurnInterpretation, TurnMode
from campanario.model.protocol import ModelMessage

def _explicit_user_corrections(history: Sequence[Message], limit: int = 8) -> str:
    """Build deterministic correction notes without mutating the persisted transcript."""
    completed = [message for message in history if message.status == "completed"]
    corrections: list[tuple[str, str]] = []
    previous_user: str | None = None
    pragmatic = PragmaticInterpreter()
    for message in completed:
        if message.role != MessageRole.USER:
            continue
        raw = message.content.strip()
        acts = pragmatic.interpret(raw).acts
        if PragmaticAct.CORRECT_PREVIOUS in acts and previous_user:
            corrected = raw.rstrip().rstrip("*").strip()
            if corrected:
                corrections.append((previous_user, corrected))
            continue
        previous_user = raw
    if not corrections:
        return ""
    rows = [
        "CORRECOES EXPLICITAS DO USUARIO",
        "Estas correcoes prevalecem sobre o valor/termo anterior quando houver conflito.",
        "Ao lembrar o enunciado, use a versao corrigida e nao trate o valor substituido como fato atual.",
        "Se o usuario perguntar pelo estado/valor atual, responda pela versao corrigida sem recitar o valor substituido, salvo se ele pedir o historico da correcao.",
    ]
    for original, corrected in corrections[-limit:]:
        original_compact = " ".join(original.split())[:260]
        corrected_compact = " ".join(corrected.split())[:120]
        rows.append(f"- original={original_compact!r}; correcao={corrected_compact!r}")
    return "\n".join(rows)


def _context_provenance(
    history: Sequence[Message],
    interpreter: ConversationTurnInterpreter,
    limit: int = 12,
) -> tuple[str, set[str]]:
    """Describe source authority of recent assistant output without changing persistence.

    Assistant creative output is explicitly non-factual. On factual/technical turns its raw text can
    be omitted from the model context while the persisted transcript remains untouched for audit.
    """
    completed = [message for message in history if message.status == "completed"]
    rows: list[str] = []
    creative_assistant_texts: set[str] = set()
    latest_user: Message | None = None
    pairs: list[tuple[Message, Message]] = []
    for message in completed:
        if message.role == MessageRole.USER:
            latest_user = message
        elif message.role == MessageRole.ASSISTANT and latest_user is not None:
            pairs.append((latest_user, message))

    for user_message, assistant_message in pairs[-limit:]:
        interpreted = interpreter.interpret_text(user_message.content)
        if interpreted.mode == TurnMode.CREATIVE:
            authority = "assistant_fiction_nonfactual"
            creative_assistant_texts.add(assistant_message.content)
        else:
            authority = "assistant_generated_unverified"
        excerpt = " ".join(user_message.content.split())[:120]
        rows.append(
            f"- origem=assistant; autoridade={authority}; modo_origem={interpreted.mode.value}; "
            f"pedido_origem={excerpt!r}"
        )

    if not rows:
        return "", creative_assistant_texts
    note = (
        "PROVENIENCIA DO CONTEXTO RECENTE\n"
        "Mensagens do usuario sao evidencia do que o usuario declarou. Respostas do assistant sao "
        "conteudo gerado e nao ganham autoridade factual por estarem no historico. Conteudo marcado "
        "assistant_fiction_nonfactual foi inventado sob pedido criativo e NUNCA pode ser usado como "
        "explicacao, fonte ou evidencia em turno factual posterior.\n"
        + "\n".join(rows)
    )
    return note, creative_assistant_texts


def _sanitize_context_by_provenance(
    context: tuple[ModelMessage, ...],
    interpretation: TurnInterpretation,
    creative_assistant_texts: set[str],
) -> tuple[ModelMessage, ...]:
    if interpretation.mode not in {TurnMode.FACTUAL_SIMPLE, TurnMode.TECHNICAL} or not creative_assistant_texts:
        return context
    sanitized: list[ModelMessage] = []
    for message in context:
        if message.role == MessageRole.ASSISTANT and message.content in creative_assistant_texts:
            sanitized.append(
                ModelMessage(
                    role=MessageRole.ASSISTANT,
                    content="[conteudo criativo anterior omitido deste turno factual por proveniencia]",
                )
            )
        else:
            sanitized.append(message)
    return tuple(sanitized)
