"""Conversation-audit evidence helpers.

These helpers summarize observable transcript properties. They do not decide persona,
memory authority or model behavior.
"""

from collections.abc import Sequence

from campanario.chat.models import Message, MessageRole
from campanario.chat.turns import ConversationTurnInterpreter

def _assistant_trace(
    history: Sequence[Message],
    interpreter: ConversationTurnInterpreter,
    limit: int = 12,
) -> str:
    completed = [message for message in history if message.status == "completed"]
    pairs: list[tuple[str, Message]] = []
    latest_user = "(pedido anterior indisponivel)"
    for message in completed:
        if message.role == MessageRole.USER:
            latest_user = " ".join(message.content.split())
        elif message.role == MessageRole.ASSISTANT:
            pairs.append((latest_user, message))
    pairs = pairs[-limit:]
    if not pairs:
        return "Nenhuma resposta anterior do assistant esta disponivel no contexto de auditoria."

    rows: list[str] = []
    for index, (user_request, message) in enumerate(pairs, start=1):
        compact = " ".join(message.content.split())
        request_excerpt = user_request[:220] + ("..." if len(user_request) > 220 else "")
        response_excerpt = compact[:320] + ("..." if len(compact) > 320 else "")
        interpretation = interpreter.interpret_text(user_request)
        expected_mode = interpretation.mode.value
        continuation_semantics = (
            interpretation.continuation_kind.value if interpretation.continuation_kind else "nao_aplicavel"
        )
        pragmatic_acts = ",".join(act.value for act in interpretation.pragmatic_acts) or "unknown"
        rows.append(
            f"- troca {index}: modo_pedido={expected_mode!r}; "
            f"atos_pragmaticos={pragmatic_acts!r}; "
            f"semantica_continuacao={continuation_semantics!r}; pedido={request_excerpt!r}; "
            f"resposta={response_excerpt!r}; palavras={len(message.content.split())}; "
            f"termina_com_pergunta={'sim' if compact.endswith('?') else 'nao'}"
        )
    return "\n".join(rows)


def _observable_signals(history: Sequence[Message], limit: int = 12) -> str:
    messages = [
        message for message in history if message.role == MessageRole.ASSISTANT and message.status == "completed"
    ][-limit:]
    if not messages:
        return "- nenhum sinal observavel"

    signals: list[str] = []
    question_count = sum(" ".join(m.content.split()).endswith("?") for m in messages)
    long_count = sum(len(m.content.split()) > 90 for m in messages)
    if question_count:
        signals.append(f"- {question_count} de {len(messages)} respostas terminaram com pergunta")
    if long_count:
        signals.append(f"- {long_count} de {len(messages)} respostas passaram de 90 palavras")

    normalized_responses = [" ".join(m.content.casefold().split()) for m in messages]
    duplicate_count = sum(
        1 for index in range(1, len(normalized_responses))
        if normalized_responses[index] and normalized_responses[index] == normalized_responses[index - 1]
    )
    if duplicate_count:
        signals.append(
            f"- {duplicate_count} resposta(s) repetiram integralmente a resposta imediatamente anterior"
        )

    english_markers = ("blue whale", "by the way", "what is", "they are", "good at")
    mixed = []
    for m in messages:
        low = m.content.casefold()
        found = [marker for marker in english_markers if marker in low]
        if found:
            mixed.extend(found)
    if mixed:
        signals.append("- possivel mistura de idioma detectada: " + ", ".join(sorted(set(mixed))))

    return "\n".join(signals) if signals else "- nenhum sinal mecanico forte; revise mesmo assim o conteudo concreto"
