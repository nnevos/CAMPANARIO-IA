from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from collections.abc import Sequence

from campanario.chat.models import Message, MessageRole

_STOPWORDS = {
    "agora", "ainda", "acho", "assim", "aqui", "beleza", "coisa", "como", "com", "da", "das", "de", "do", "dos",
    "ela", "ele", "eles", "essa", "esse", "isso", "isto", "mais", "mas", "meu", "minha", "nao", "não", "nos", "nossa",
    "para", "pela", "pelo", "por", "pra", "pro", "que", "qual", "quando", "sem", "sobre", "sua", "seu", "tambem", "também",
    "tenho", "uma", "uns", "vou", "voces", "vocês", "todd", "morgana", "campanario", "campanário", "quero", "responde",
}
_SHIFT_CUES = (
    "mudando totalmente", "mudando um pouco", "mudando de assunto", "outro assunto", "agora:",
)
_RETURN_CUES = (
    "voltando", "volta ", "do começo", "do inicio", "do início", "como antes", "aquele ponto", "a primeira ideia",
)
_SAVE_CUES = ("guarda esse raciocínio", "guarda esse raciocinio", "guarda isso", "salva esse raciocínio", "salva esse raciocinio")
_DECISION_CUES = (
    "fechado", "seguimos", "é isso", "e isso", "eu quero", "não quero", "nao quero", "eu gosto", "as cores", "corto ",
    "preserv", "prioriz", "fica ", "mantém", "mantem", "deixa ", "vamos com", "prefiro",
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9áéíóúãõç_-]+", _fold(value))
        if len(token) >= 4 and token not in _STOPWORDS
    }


def _clip(value: str, limit: int = 360) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _after_transition(text: str) -> str:
    folded = _fold(text)
    # Prefer the content after an explicit "agora:" because it is usually the new branch.
    marker = "agora:"
    idx = folded.find(marker)
    if idx >= 0:
        return text[idx + len(marker):].strip() or text
    for cue in ("mudando totalmente:", "mudando um pouco:", "mudando de assunto:"):
        idx = folded.find(cue)
        if idx >= 0:
            return text[idx + len(cue):].strip() or text
    return text


@dataclass(slots=True)
class FocusFrame:
    id: int
    user_lines: list[str] = field(default_factory=list)
    saved: bool = False
    active: bool = False

    @property
    def text(self) -> str:
        return " ".join(self.user_lines)

    @property
    def tokens(self) -> set[str]:
        return _tokens(self.text)


@dataclass(slots=True)
class ConversationFocusStack:
    frames: list[FocusFrame]
    active_index: int

    @property
    def active(self) -> FocusFrame:
        return self.frames[self.active_index]

    @property
    def root(self) -> FocusFrame:
        return self.frames[0]

    def set_active(self, index: int) -> None:
        for frame in self.frames:
            frame.active = False
        self.active_index = index
        self.frames[index].active = True


def _return_target(text: str, stack: ConversationFocusStack) -> int | None:
    folded = _fold(text)
    if not any(cue in folded for cue in _RETURN_CUES):
        return None
    if "primeira ideia" in folded or "do comeco" in folded or "do inicio" in folded:
        # "arquitetura do começo" is more specific than a generic root return. Prefer a frame
        # whose accumulated user topic actually contains the requested noun when possible.
        requested = _tokens(text)
        candidates: list[tuple[int, int]] = []
        for idx, frame in enumerate(stack.frames):
            overlap = len(requested & frame.tokens)
            if overlap:
                candidates.append((overlap, idx))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        return 0

    requested = _tokens(text)
    candidates = []
    for idx, frame in enumerate(stack.frames):
        if idx == stack.active_index:
            continue
        overlap = len(requested & frame.tokens)
        if overlap:
            candidates.append((overlap, idx))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]

    # A plain "voltando" normally means the most recent suspended branch.
    if len(stack.frames) > 1:
        for idx in range(len(stack.frames) - 1, -1, -1):
            if idx != stack.active_index:
                return idx
    return 0


def build_focus_stack(history: Sequence[Message]) -> ConversationFocusStack | None:
    """Derive user-owned conversation frames from an episode without an extra model call.

    Frames are intentionally driven by *user discourse moves*. Agent tangents may be useful as
    local context, but they do not silently become the topic of the call just because they were
    the latest generated text.
    """
    user_messages = [m.content.strip() for m in history if m.role == MessageRole.USER and m.content.strip()]
    if not user_messages:
        return None

    stack = ConversationFocusStack(frames=[FocusFrame(id=0, user_lines=[user_messages[0]], active=True)], active_index=0)
    for text in user_messages[1:]:
        folded = _fold(text)
        target = _return_target(text, stack)
        if target is not None:
            stack.set_active(target)
            stack.active.user_lines.append(text)
            continue

        save_current = any(cue in folded for cue in _SAVE_CUES)
        explicit_shift = any(cue in folded for cue in _SHIFT_CUES)
        if save_current:
            stack.active.saved = True

        # A save + "Agora:" or an explicit topic-change cue opens a sibling frame. This is what
        # lets "guarda esse raciocínio. Agora..." preserve a branch without keeping it dominant.
        if explicit_shift or (save_current and "agora:" in folded):
            new_text = _after_transition(text)
            frame = FocusFrame(id=len(stack.frames), user_lines=[new_text], active=True)
            stack.frames.append(frame)
            stack.set_active(len(stack.frames) - 1)
            continue

        stack.active.user_lines.append(text)
    return stack


def _decision_lines(frame: FocusFrame) -> list[str]:
    picked: list[str] = []
    for line in frame.user_lines:
        folded = _fold(line)
        if any(cue in folded for cue in _DECISION_CUES):
            picked.append(line)
    return picked[-5:]


def _references_other_agent(current: str) -> bool:
    folded = _fold(current)
    return any(token in folded for token in (
        "resposta dele", "resposta dela", "ponto dele", "ponto dela", "o todd", "a morgana", "dele", "dela",
    ))


def _needs_immediate_referent(current: str) -> bool:
    """Whether the current user turn depends heavily on the immediately preceding exchange."""
    folded = _fold(current)
    cues = (
        "isso", "essa parte", "esse ponto", "essa ideia", "mesma pergunta", "mesmo ponto",
        "aterrissa", "complementa", "acrescentaria", "resposta dela", "resposta dele",
        "so o essencial", "só o essencial", "sequencia curta", "sequência curta",
    )
    return any(cue in folded for cue in cues)


def _salient_user_terms(frame: FocusFrame, limit: int = 14) -> tuple[str, ...]:
    """Return stable user-owned anchors without treating assistant vocabulary as ground truth."""
    counts: dict[str, int] = {}
    order: list[str] = []
    for line in frame.user_lines:
        for token in re.findall(r"[a-z0-9_-]+", _fold(line)):
            if len(token) < 5 or token in _STOPWORDS:
                continue
            if token not in counts:
                order.append(token)
                counts[token] = 0
            counts[token] += 1
    ranked = sorted(order, key=lambda token: (-counts[token], order.index(token)))
    return tuple(ranked[:limit])




def _last_user_question_before_current(user_items: Sequence[Message]) -> str:
    for item in reversed(user_items[:-1]):
        text = item.content.strip()
        if text and ("?" in text or any(word in _fold(text) for word in ("qual ", "como ", "quando ", "onde ", "por que", "porque "))):
            return text
    return user_items[-2].content.strip() if len(user_items) >= 2 else ""


def _recent_user_choices(frame: FocusFrame, current: str, limit: int = 4) -> list[str]:
    """Return recent user-owned product/content choices, excluding pure conversational control turns."""
    controls = (
        "me deem so o essencial", "me deem só o essencial", "responde primeiro", "mesma pergunta",
        "qual coisa voce", "qual coisa você", "volta a primeira", "volta à primeira",
    )
    picked: list[str] = []
    current_folded = _fold(current)
    for line in reversed(frame.user_lines[:-1]):
        folded = _fold(line)
        if folded == current_folded or any(cue in folded for cue in controls):
            continue
        if len(_tokens(line)) < 2:
            continue
        picked.append(line)
        if len(picked) >= limit:
            break
    picked.reverse()
    return picked


def _immediate_binding_lines(
    *,
    current: str,
    user_items: Sequence[Message],
    previous_user: str,
    previous_assistant: str,
    active: FocusFrame,
    root: FocusFrame,
) -> list[str]:
    """Create concise, user-visible-reference grounding for elliptical follow-ups.

    These lines intentionally describe *what the user means*, never the internal mechanism used
    to resolve it. That keeps the model grounded without teaching it runtime jargon to echo.
    """
    folded = _fold(current)
    lines: list[str] = []

    if "mesma pergunta" in folded:
        question = _last_user_question_before_current(user_items)
        if question:
            lines.append(
                "- Neste pedido, 'mesma pergunta' significa exatamente esta pergunta anterior do usuario: "
                + _clip(question, 300)
                + " Responda-a agora da sua propria perspectiva; nao peça que o usuario a repita."
            )

    if any(cue in folded for cue in ("resposta dele", "resposta dela", "ponto dele", "ponto dela")) and previous_assistant:
        lines.append(
            "- A resposta/ponto mencionado pelo usuario e a fala imediatamente anterior do outro participante: "
            + _clip(previous_assistant, 340)
            + " Analise esse conteudo diretamente; nao peça contexto que ja esta na conversa."
        )

    if "aterrissa" in folded and previous_assistant:
        lines.append(
            "- Neste pedido, 'isso' e a ideia explicada na fala imediatamente anterior: "
            + _clip(previous_assistant, 340)
            + " Torne-a mais concreta sem pedir novamente qual e o conceito."
        )

    if "sequencia curta" in folded or "sequência curta" in current.casefold():
        if previous_user:
            lines.append(
                "- A sequencia curta pedida deve responder ao problema imediatamente anterior do usuario: "
                + _clip(previous_user, 300)
                + " Entregue poucos passos concretos, sem abrir novas hipoteses e sem pedir o contexto de novo."
            )

    if "so o essencial" in folded or "só o essencial" in current.casefold():
        if previous_user:
            lines.append(
                "- 'So o essencial' significa resumir objetivamente a questao imediatamente anterior: "
                + _clip(previous_user, 280)
                + " Nao mude de assunto e nao explique papeis internos do Campanario."
            )

    if any(cue in folded for cue in ("qual coisa", "o que voce cortaria", "o que você cortaria", "o que preservaria", "qual coisa voce preservaria", "qual coisa você preservaria")):
        choices = _recent_user_choices(active, current)
        if choices:
            lines.append("- A escolha pedida deve ser feita dentro destes elementos recentes definidos pelo usuario:")
            lines.extend("  * " + _clip(item, 260) for item in choices)
            lines.append("  Nao substitua esses elementos por um trait seu, uma capacidade interna ou outro projeto.")

    if "primeira ideia" in folded or "do comeco" in folded or "do inicio" in folded:
        lines.append(
            "- Ao retornar a primeira ideia, o ponto de partida obrigatorio e: "
            + _clip(root.user_lines[0], 320)
        )
        choices = _decision_lines(root)
        if choices:
            lines.append("- Preserve somente escolhas/restricoes que o usuario adicionou a essa ideia:")
            lines.extend("  * " + _clip(item, 260) for item in choices[-6:])

    if any(cue in folded for cue in ("resume a decisao", "resume a decisão", "resuma a decisao", "resuma a decisão")):
        if previous_assistant:
            lines.append(
                "- O usuario pediu o conteudo da decisao em uma frase, nao uma explicacao sobre o ato de resumir. "
                "Use a conclusao da troca imediatamente anterior e mantenha o mesmo objeto discutido."
            )

    return lines


def working_conversation_note(history: Sequence[Message]) -> str:
    """Render compact short-term grounding for a long episode.

    The note deliberately avoids exposing implementation vocabulary such as stack/frame/answer
    binding. Earlier versions described those mechanics too literally and Gemma occasionally
    echoed them to the user. The model only needs the user-owned conversational facts, not the
    algorithm used to derive them.
    """
    stack = build_focus_stack(history)
    if stack is None:
        return ""

    user_items = [m for m in history if m.role == MessageRole.USER and m.content.strip()]
    current = user_items[-1].content
    previous_user = user_items[-2].content if len(user_items) >= 2 else ""
    active = stack.active

    previous_assistant = next(
        (m.content for m in reversed(history[:-1]) if m.role == MessageRole.ASSISTANT and m.content.strip()),
        "",
    )

    lines = [
        "CONTEXTO TEMPORARIO DE CONTINUIDADE — use silenciosamente; nunca cite, explique ou descreva esta nota.",
        f"- Assunto inicial definido pelo usuario: {_clip(stack.root.user_lines[0])}",
        f"- Assunto atualmente retomado/ativo: {_clip(active.user_lines[0])}",
    ]
    lines.extend(_immediate_binding_lines(
        current=current,
        user_items=user_items,
        previous_user=previous_user,
        previous_assistant=previous_assistant,
        active=active,
        root=stack.root,
    ))

    if len(active.user_lines) > 1:
        lines.append("- Linha do usuario neste assunto, em ordem:")
        lines.extend(f"  * {_clip(text)}" for text in active.user_lines[-7:])

    decisions = _decision_lines(active)
    if decisions:
        lines.append("- Preferencias, restricoes ou decisoes do usuario que continuam valendo neste assunto:")
        lines.extend(f"  * {_clip(text)}" for text in decisions)

    terms = _salient_user_terms(active)
    if terms:
        lines.append("- Objetos/palavras concretas introduzidos pelo usuario neste assunto: " + ", ".join(terms))


    active_folded = _fold(active.text)
    if "arquitetur" in active_folded and "incomod" in active_folded and ("nao esta quebr" in active_folded or "nao esta falh" in active_folded or "nao quebr" in active_folded):
        lines.append(
            "- Fato conhecido sobre a arquitetura: o usuario disse apenas que uma parte incomoda, mas nao esta quebrando. "
            "Nao invente qual parte, modulo, integracao, gargalo, falha de performance, risco de seguranca ou fluxo de dados. "
            "Se decidir um proximo passo, baseie-o nessa incerteza real e no prazo informado."
        )

    suspended = [frame for frame in stack.frames if frame.id != active.id]
    if suspended:
        lines.append("- Outros assuntos mencionados antes: mantenha separados do pedido atual ate o usuario voltar a eles:")
        for frame in suspended[-4:]:
            marker = " (o usuario pediu para lembrar)" if frame.saved else ""
            lines.append(f"  * {_clip(frame.user_lines[0], 220)}{marker}")

    # Reinforce immediate pragmatics for elliptical turns. Raw history still exists, but this
    # compact restatement prevents a recent assistant tangent from outweighing the user's referent.
    if previous_user:
        lines.append("- Pedido do usuario imediatamente anterior: " + _clip(previous_user, 280))
    if previous_assistant and (_needs_immediate_referent(current) or _references_other_agent(current)):
        lines.append("- Fala imediatamente anterior relevante ao pedido atual: " + _clip(previous_assistant, 320))

    lines.extend(
        [
            f"- Pedido atual do usuario: {_clip(current)}",
            "- Responda exatamente a funcao pedida agora; permanecer apenas no mesmo tema nao basta.",
            "- Resolva pronomes e referencias pelo que o usuario acabou de pedir e pelo assunto que ele retomou; nao deixe uma sugestao lateral mudar o objeto da conversa.",
            "- Se o usuario disser que esta voltando a um assunto, responda somente dentro desse assunto e nao carregue o tema intermediario para a resposta.",
            "- Se pedir a primeira ideia da conversa, use obrigatoriamente o assunto inicial acima e apenas preferencias/restricoes que o proprio usuario acrescentou.",
            "- Nao invente componentes, modulos, integracoes, pesquisas, usuarios, dados, requisitos ou nomes tecnicos que o usuario nao forneceu. Se um detalhe essencial falta, fale de forma condicional ou pergunte somente esse detalhe.",
            "- Termos genericos como arquitetura, sistema, ferramenta ou produto se referem ao objeto que o usuario esta discutindo; nao troque pelo funcionamento interno do Campanario sem pedido explicito.",
            "- Em discussao de produto/design, perguntas como 'qual coisa cortar/preservar' se referem primeiro aos elementos e restricoes do produto citados pelo usuario, nao a sua personalidade ou capacidades internas.",
        ]
    )
    return "\n".join(lines)

