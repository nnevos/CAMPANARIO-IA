import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class PragmaticAct(StrEnum):
    """What a user message is doing in the conversation, independent of persona voice."""

    GREET = "greet"
    ACKNOWLEDGE = "acknowledge"
    AGREE = "agree"
    DISAGREE = "disagree"
    REACT = "react"
    JOKE_OR_PLAY = "joke_or_play"
    CORRECT_PREVIOUS = "correct_previous"
    CONTINUE_THOUGHT = "continue_thought"
    CHANGE_TOPIC = "change_topic"
    CLOSE_TOPIC = "close_topic"
    VENT_OR_SHARE = "vent_or_share"
    ASK_INFO = "ask_info"
    ASK_OPINION = "ask_opinion"
    REQUEST_ACTION = "request_action"
    PLAN = "plan"
    CLARIFY = "clarify"
    THINK_ALOUD = "think_aloud"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PragmaticInterpretation:
    acts: tuple[PragmaticAct, ...]
    informal: bool
    contains_laughter: bool
    fragment_like: bool
    confidence: float


class PragmaticInterpreter:
    """Deterministic first-pass pragmatics.

    This layer interprets user input only. It does not select a persona, decide truth,
    infer private traits, or prescribe the wording of the answer. Lexical markers are
    grouped by conversational function and backed by pattern rules so the runtime is
    not tied to one test transcript.
    """

    _ACK_PHRASES = {
        "ok", "aham", "uhum", "entendi", "saquei", "certo", "blz", "beleza",
        "show", "fechou", "valeu", "boa", "massa", "certinho", "justo", "tranquilo",
        "suave", "pode crer", "faz sentido", "e isso", "ta bom", "tudo certo",
    }
    _AGREE = {"sim", "verdade", "real", "realmente", "pse", "pois e", "pode ser"}
    _DISAGREE_PREFIXES = ("nao concordo", "discordo", "acho que nao", "na verdade nao")
    _CLOSE_MARKERS = (
        "deixa isso pra la", "deixa isso para la", "esquece isso", "deixa pra depois",
        "deixa para depois", "deixa quieto", "muda de assunto", "vamos mudar de assunto",
        "deixa pra outra hora", "deixa para outra hora", "nao precisa mais", "larga esse assunto",
        "larga mao disso", "depois eu vejo isso",
    )
    _CHANGE_MARKERS = ("mudando de assunto", "mudando total", "alias", "outra coisa", "agora outra coisa")
    _OPINION_MARKERS = ("o que voce acha", "qual sua opiniao", "voce concorda", "na sua opiniao")
    _ACTION_MARKERS = (
        "faz isso", "faz pra mim", "faz para mim", "resolve isso", "verifica isso",
        "procura isso", "me ajuda a",
    )
    _PLAN_MARKERS = ("bora ", "vamos ", "sabado", "domingo", "amanha", "marcar", "combinar")
    _VENT_MARKERS = (
        "to cansado", "to exausto", "deu merda", "ta foda", "e complicado", "to puto",
        "to triste", "sem vontade", "modo economia de energia", "so existindo",
        "cabeça demorou", "cabeca demorou", "acordei meio", "to largado", "tô largado",
    )
    _THINK_MARKERS = ("acho que", "talvez", "sei la", "nao sei mas", "pensando aqui")
    _INFO_STARTS = (
        "quem ", "o que ", "qual ", "quanto ", "quando ", "onde ", "por que ", "porque ",
        "como ", "me explica", "explique", "me diga", "diga ",
    )

    def interpret(self, text: str) -> PragmaticInterpretation:
        compact = re.sub(r"\s+", " ", _normalize(text.strip())).strip()
        if not compact:
            return PragmaticInterpretation(
                acts=(PragmaticAct.UNKNOWN,), informal=False, contains_laughter=False,
                fragment_like=True, confidence=0.2,
            )

        acts: list[PragmaticAct] = []
        laughter = _contains_laughter(compact)
        informal = laughter or _contains_informal_marker(compact)

        if _looks_like_greeting(compact):
            acts.append(PragmaticAct.GREET)
        if _looks_like_correction(text, compact):
            acts.append(PragmaticAct.CORRECT_PREVIOUS)
        if any(marker in compact for marker in self._CLOSE_MARKERS):
            acts.append(PragmaticAct.CLOSE_TOPIC)
        if any(marker in compact for marker in self._CHANGE_MARKERS):
            acts.append(PragmaticAct.CHANGE_TOPIC)
        if _looks_like_acknowledgement(compact, self._ACK_PHRASES):
            acts.append(PragmaticAct.ACKNOWLEDGE)
        if compact in self._AGREE or any(compact.startswith(prefix) for prefix in ("concordo", "sim,")):
            acts.append(PragmaticAct.AGREE)
        if any(compact.startswith(prefix) for prefix in self._DISAGREE_PREFIXES):
            acts.append(PragmaticAct.DISAGREE)
        if laughter:
            acts.append(PragmaticAct.REACT)
        if laughter and any(marker in compact for marker in ("boa", "genial", "mt bom", "muito bom")):
            acts.append(PragmaticAct.JOKE_OR_PLAY)
        if any(marker in compact for marker in self._OPINION_MARKERS):
            acts.append(PragmaticAct.ASK_OPINION)
        elif compact.endswith("?") or compact.startswith(self._INFO_STARTS):
            acts.append(PragmaticAct.ASK_INFO)
        if any(marker in compact for marker in self._ACTION_MARKERS):
            acts.append(PragmaticAct.REQUEST_ACTION)
        if any(marker in compact for marker in self._VENT_MARKERS) or _looks_like_personal_state_share(compact):
            acts.append(PragmaticAct.VENT_OR_SHARE)
        if any(marker in compact for marker in self._PLAN_MARKERS):
            acts.append(PragmaticAct.PLAN)
        if any(marker in compact for marker in self._THINK_MARKERS):
            acts.append(PragmaticAct.THINK_ALOUD)
        if _looks_like_clarification(compact):
            acts.append(PragmaticAct.CLARIFY)

        fragment_like = _is_fragment_like(compact)
        if fragment_like and not acts:
            acts.append(PragmaticAct.CONTINUE_THOUGHT)

        acts = _dedupe(acts) or [PragmaticAct.UNKNOWN]
        confidence = 0.9 if acts != [PragmaticAct.UNKNOWN] else 0.35
        if len(acts) > 1:
            confidence = 0.85
        return PragmaticInterpretation(
            acts=tuple(acts), informal=informal, contains_laughter=laughter,
            fragment_like=fragment_like, confidence=confidence,
        )


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _looks_like_greeting(text: str) -> bool:
    # Greeting is a conversational function, not one fixed phrase. Optional vocatives are allowed.
    return bool(
        re.fullmatch(
            r"(?:oi|ola|opa|salve|eae|e ai|fala(?: ai)?|bom dia|boa tarde|boa noite)"
            r"(?:[ ,]+(?:mano|meu caro|parceiro|amigo|amg|vei|cara))?[!?.]*",
            text,
        )
    )


def _looks_like_acknowledgement(text: str, phrases: set[str]) -> bool:
    if text.rstrip().endswith("?"):
        return False
    cleaned = text.strip(" !?.,")
    if cleaned in phrases:
        return True
    # Common intensifiers do not change the conversational act.
    cleaned = re.sub(r"^(?:ah+|po+|mano|slk)\s+", "", cleaned).strip()
    cleaned = re.sub(r"\s+(?:mesmo|entao)$", "", cleaned).strip()
    return cleaned in phrases


def _contains_laughter(text: str) -> bool:
    if re.search(r"(?:k{3,}|ksk(?:sk)+|ha(?:ha)+|he(?:he)+|rsrs+)", text):
        return True
    for token in re.findall(r"[a-z]{8,}", text):
        vowels = sum(char in "aeiou" for char in token)
        smash_chars = sum(char in "ksxjwh" for char in token)
        if (len(token) >= 12 and vowels / len(token) < 0.35) or (
            len(token) >= 8 and vowels == 0 and smash_chars / len(token) >= 0.75
        ):
            return True
    return False


def _contains_informal_marker(text: str) -> bool:
    markers = ("mano", "vei", "tlgd", "slk", "seloco", "pprt", "pse", "amg", "gnt", "krl", "pqp")
    return any(re.search(rf"(?:^|\s){re.escape(marker)}(?:$|\s|[?!,.])", text) for marker in markers)


def _looks_like_personal_state_share(text: str) -> bool:
    if text.endswith("?") or len(text.split()) > 14:
        return False
    return bool(
        re.search(
            r"^(?:mano\s+)?(?:hoje\s+)?(?:eu\s+)?(?:to|tô|estou|tava|acordei|fiquei|ando)\b",
            text,
        )
    )


def _looks_like_correction(original: str, normalized: str) -> bool:
    stripped = original.strip()
    return stripped.endswith("*") and len(normalized.split()) <= 5


def _looks_like_clarification(text: str) -> bool:
    return text.startswith(("quer dizer", "quis dizer", "tipo assim", "melhor dizendo"))


def _is_fragment_like(text: str) -> bool:
    words = text.split()
    if len(words) <= 3 and not text.endswith(("?", ".", "!")):
        return True
    return False


def _dedupe(items: list[PragmaticAct]) -> list[PragmaticAct]:
    return list(dict.fromkeys(items))
