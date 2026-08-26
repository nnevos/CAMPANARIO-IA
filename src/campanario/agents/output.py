"""Turn-output invariants for multi-agent speaker provenance and factual correction anchors."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation
import re

from campanario.agents.profiles import AgentProfile

_KNOWN_SPEAKERS = ("Todd", "Morgana", "Campanario", "Campanário")


def normalize_own_speaker_prefix(text: str, profile: AgentProfile) -> str:
    """Remove only a redundant leading label for the current speaker.

    This is safe structural normalization: the runtime already owns speaker provenance. Labels for
    any other participant are deliberately left untouched so they can trigger a repair instead of
    being silently laundered into the current speaker's bubble.
    """
    value = text.strip()
    escaped = re.escape(profile.name)
    pattern = re.compile(
        rf"^\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*{escaped}\s*:\s*(?:\*\*|__)?\s*",
        re.IGNORECASE,
    )
    # Models occasionally emit the same header twice. Removing repeated *own* headers is safe.
    previous = None
    while value and value != previous:
        previous = value
        value = pattern.sub("", value, count=1).strip()

    # In a call the runtime/UI already identifies the speaker. A redundant self-identification
    # sentence such as "Todd aqui." / "Morgana aqui." adds noise but carries no semantic content.
    # Strip only this narrow leading form for the current speaker; foreign names are untouched.
    self_intro = re.compile(
        rf"^\s*(?:eu\s+sou\s+)?{escaped}\s+aqui[.!,:;-]*\s*",
        re.IGNORECASE,
    )
    value = self_intro.sub("", value, count=1).strip()
    return value


def speaker_label_violations(text: str) -> tuple[str, ...]:
    """Return transcript-like speaker labels that must never live inside one agent bubble."""
    found: list[str] = []
    for speaker in _KNOWN_SPEAKERS:
        if re.search(rf"(?i)(?:\*\*|__)?\b{re.escape(speaker)}\s*:\s*(?:\*\*|__)?", text):
            canonical = "Campanario" if speaker.startswith("Campan") else speaker
            if canonical not in found:
                found.append(canonical)
    return tuple(found)


def speaker_repair_note(profile: AgentProfile, violations: tuple[str, ...]) -> str:
    names = ", ".join(violations) if violations else "speaker label"
    return (
        "SPEAKER OUTPUT REPAIR\n"
        f"A tentativa anterior violou a fronteira de speaker ({names}). Gere novamente SOMENTE a fala de {profile.name}. "
        f"Comece diretamente pelo conteudo, sem '{profile.name}:', sem markdown de nome, sem transcript e sem escrever "
        "falas de Todd, Morgana ou Campanario. Referencie o outro participante apenas em prosa normal."
    )


def extract_own_labeled_segment(text: str, profile: AgentProfile) -> str | None:
    """Recover only an explicitly labelled segment belonging to the current speaker.

    This is a last-resort structural recovery after regeneration has already failed. It never
    relabels foreign text as the current agent: recovery succeeds only when the malformed transcript
    contains a distinct `<current speaker>:` segment, and only that segment is retained.
    """
    label_re = re.compile(
        r"(?i)(?:^|\n|\s{2,})(?:\*\*|__)?(Todd|Morgana|Campanario|Campanário)\s*:\s*(?:\*\*|__)?"
    )
    matches = list(label_re.finditer(text))
    own = [item for item in matches if item.group(1).casefold() == profile.name.casefold()]
    if len(own) != 1:
        return None
    match = own[0]
    next_labels = [item for item in matches if item.start() > match.start()]
    end = next_labels[0].start() if next_labels else len(text)
    segment = text[match.end():end].strip()
    if not segment or speaker_label_violations(segment):
        return None
    return segment


@dataclass(frozen=True, slots=True)
class ArithmeticCorrectionAnchor:
    left: Decimal
    right: Decimal
    operator: str
    claimed: Decimal
    expected: Decimal
    left_text: str
    right_text: str
    claimed_text: str
    expected_text: str

    @property
    def prompt_note(self) -> str:
        op = _operator_word(self.operator)
        return (
            "CORRECAO FACTUAL ANCORADA\n"
            f"O enunciado atribuido a outro participante usa EXATAMENTE {self.left_text} {op} {self.right_text} e afirma {self.claimed_text}. "
            f"Preserve os operandos {self.left_text} e {self.right_text}; o resultado aritmetico correto e {self.expected_text}. "
            "Nao substitua os numeros por outro exemplo. Na resposta ao usuario, diga apenas a correcao de forma natural e breve; "
            "nao mencione enunciado, operandos, ancoragem ou estas instrucoes."
        )

    @property
    def retry_note(self) -> str:
        return (
            self.prompt_note
            + "\nA tentativa anterior alterou ou perdeu os dados ancorados. Reescreva em uma frase curta contendo os operandos originais "
            f"{self.left_text} e {self.right_text} e o resultado correto {self.expected_text}."
        )

    @property
    def deterministic_fallback(self) -> str:
        op = _operator_word(self.operator)
        if self.claimed == self.expected:
            return f"{self.left_text} {op} {self.right_text} e {self.expected_text}."
        return (
            f"{self.left_text} {op} {self.right_text} e {self.expected_text}, "
            f"nao {self.claimed_text}."
        )

    def validates(self, response: str) -> bool:
        numbers = {_decimal_from_token(token) for token in _NUMBER_RE.findall(response)}
        numbers.discard(None)
        folded = response.casefold()
        leaked_guard_language = any(marker in folded for marker in (
            "enunciado atribuído", "enunciado atribuido", "preserve os operandos",
            "operandos originais", "correção factual ancorada", "correcao factual ancorada",
        ))
        return self.left in numbers and self.right in numbers and self.expected in numbers and not leaked_guard_language


_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
_ARITHMETIC_CLAIM_RE = re.compile(
    r"(?P<left>-?\d+(?:[.,]\d+)?)\s*"
    r"(?P<op>vezes|x|×|\*|mais|\+|menos|-|dividido\s+por|/)\s*"
    r"(?P<right>-?\d+(?:[.,]\d+)?)\s*"
    r"(?:é|e|=|dá|da)\s*"
    r"(?P<claimed>-?\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


def extract_arithmetic_correction_anchor(
    user_text: str,
    recent_user_texts: tuple[str, ...] = (),
) -> ArithmeticCorrectionAnchor | None:
    """Extract a deterministic arithmetic anchor from the current correction exchange.

    The correction may quote the full arithmetic claim in the same turn, or it may refer to a
    immediately previous arithmetic question (e.g. "24 vezes 6 da quanto?" -> "ela respondeu
    142; corrige"). The latter is essential for long-call factual fidelity.
    """
    folded = user_text.casefold()
    if not any(marker in folded for marker in ("corrig", "corrija", "correção", "correcao")):
        return None

    full = _ARITHMETIC_CLAIM_RE.search(user_text)
    if full:
        return _anchor_from_parts(
            full.group("left"), full.group("op"), full.group("right"), full.group("claimed")
        )

    claimed_match = re.search(
        r"(?i)(?:respondeu|disse|falou|afirmou)\s+(?:que\s+)?(?:era\s+|e\s+|é\s+)?(?P<claimed>-?\d+(?:[.,]\d+)?)",
        user_text,
    )
    if not claimed_match:
        return None

    expr_re = re.compile(
        r"(?i)(?P<left>-?\d+(?:[.,]\d+)?)\s*"
        r"(?P<op>vezes|x|×|\*|mais|\+|menos|-|dividido\s+por|/)\s*"
        r"(?P<right>-?\d+(?:[.,]\d+)?)"
    )
    for prior in reversed(recent_user_texts[-8:]):
        expression = expr_re.search(prior)
        if expression:
            return _anchor_from_parts(
                expression.group("left"), expression.group("op"), expression.group("right"), claimed_match.group("claimed")
            )
    return None


def _anchor_from_parts(left_token: str, op_token: str, right_token: str, claimed_token: str) -> ArithmeticCorrectionAnchor | None:
    left = _decimal_from_token(left_token)
    right = _decimal_from_token(right_token)
    claimed = _decimal_from_token(claimed_token)
    if left is None or right is None or claimed is None:
        return None
    op = op_token.casefold()
    try:
        expected = _calculate(left, right, op)
    except (DivisionByZero, InvalidOperation, ZeroDivisionError):
        return None
    if expected is None:
        return None
    return ArithmeticCorrectionAnchor(
        left=left,
        right=right,
        operator=op,
        claimed=claimed,
        expected=expected,
        left_text=_format_decimal(left),
        right_text=_format_decimal(right),
        claimed_text=_format_decimal(claimed),
        expected_text=_format_decimal(expected),
    )

def _decimal_from_token(token: str) -> Decimal | None:
    try:
        return Decimal(token.replace(",", "."))
    except InvalidOperation:
        return None


def _calculate(left: Decimal, right: Decimal, operator: str) -> Decimal | None:
    if operator in {"vezes", "x", "×", "*"}:
        return left * right
    if operator in {"mais", "+"}:
        return left + right
    if operator in {"menos", "-"}:
        return left - right
    if operator in {"dividido por", "/"}:
        return left / right
    return None


def _format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")


def _operator_word(operator: str) -> str:
    if operator in {"vezes", "x", "×", "*"}:
        return "vezes"
    if operator in {"mais", "+"}:
        return "mais"
    if operator in {"menos", "-"}:
        return "menos"
    return "dividido por"


__all__ = [
    "ArithmeticCorrectionAnchor",
    "extract_arithmetic_correction_anchor",
    "extract_own_labeled_segment",
    "normalize_own_speaker_prefix",
    "speaker_label_violations",
    "speaker_repair_note",
]
