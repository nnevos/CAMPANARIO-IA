from __future__ import annotations
import re
import unicodedata

from campanario.chat.turns import ContinuationKind, TurnInterpretation, TurnMode
from .types import ResponseKind

def _response_kind(
    *,
    interpretation: TurnInterpretation,
    exact_sentences: int | None,
    reaction: bool,
    greeting: bool,
    acknowledgement: bool,
    topic_drop: bool,
    correction: bool,
    self_awareness: bool,
    context_registration: bool,
    technical_first_step: bool,
    truth_over_agreement: bool,
    sharing: bool,
) -> ResponseKind:
    if self_awareness:
        return ResponseKind.SELF_AWARE
    if truth_over_agreement:
        return ResponseKind.TRUTH_DISCUSSION
    if correction:
        return ResponseKind.CORRECTION
    if context_registration:
        return ResponseKind.CONTEXT_REGISTRATION
    if topic_drop:
        return ResponseKind.TOPIC_DROP
    if acknowledgement:
        return ResponseKind.ACKNOWLEDGEMENT
    if greeting:
        return ResponseKind.GREETING
    if reaction:
        return ResponseKind.REACTION
    if technical_first_step:
        return ResponseKind.TECHNICAL_FIRST_STEP
    if interpretation.mode == TurnMode.CREATIVE and exact_sentences is not None:
        return ResponseKind.CREATIVE_EXACT
    if interpretation.mode == TurnMode.CREATIVE:
        return ResponseKind.CREATIVE
    if interpretation.mode == TurnMode.FACTUAL_SIMPLE:
        return ResponseKind.FACTUAL
    if sharing:
        return ResponseKind.SOCIAL_SHARE
    return ResponseKind.OPEN


def _split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _strip_terminal_punctuation(text: str) -> str:
    return text.strip().rstrip(".!? ")


def _force_sentence_count(text: str, count: int) -> str:
    if count <= 0 or not text.strip():
        return text.strip()
    parts = [_strip_terminal_punctuation(part) for part in _split_sentences(text)]
    parts = [part for part in parts if part]
    if not parts:
        return text.strip()
    if count == 1:
        return "; ".join(parts).strip() + "."
    if len(parts) > count:
        kept = parts[: count - 1]
        kept.append("; ".join(parts[count - 1 :]))
        return ". ".join(kept).strip() + "."
    while len(parts) < count:
        longest_index = max(range(len(parts)), key=lambda i: len(parts[i].split()))
        left, right = _split_clause(parts[longest_index])
        if not right:
            words = parts[longest_index].split()
            if len(words) < 4:
                break
            middle = max(1, len(words) // 2)
            left, right = " ".join(words[:middle]), " ".join(words[middle:])
        parts[longest_index : longest_index + 1] = [left, right]
    if len(parts) < count:
        return ". ".join(parts).strip() + "."
    return ". ".join(parts[:count]).strip() + "."


def _split_clause(text: str) -> tuple[str, str]:
    candidates = []
    for match in re.finditer(r"(?:;|,|\s+e\s+|\s+mas\s+|\s+porque\s+)", text, flags=re.IGNORECASE):
        if 0 < match.start() < len(text) - 1:
            candidates.append(match)
    if not candidates:
        return text, ""
    midpoint = len(text) / 2
    match = min(candidates, key=lambda item: abs(item.start() - midpoint))
    left = text[: match.start()].strip(" ,;")
    right = text[match.end() :].strip(" ,;")
    return left, right


def _limit_sentence_count(text: str, count: int) -> str:
    parts = _split_sentences(text)
    if len(parts) <= count:
        return text.strip()
    return " ".join(parts[:count]).strip()


def _trim_to_word_budget(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    selected: list[str] = []
    used = 0
    for sentence in _split_sentences(text):
        sentence_words = sentence.split()
        if selected and used + len(sentence_words) > max_words:
            break
        if not selected and len(sentence_words) > max_words:
            clipped = " ".join(sentence_words[:max_words]).rstrip(" ,;:-")
            return _strip_dangling_list_marker(clipped.rstrip(".!?") + ".")
        selected.append(sentence)
        used += len(sentence_words)
    if selected:
        return _strip_dangling_list_marker(" ".join(selected).strip())
    clipped = " ".join(words[:max_words]).rstrip(" ,;:-")
    return _strip_dangling_list_marker(clipped.rstrip(".!?") + ".")


def _strip_dangling_list_marker(text: str) -> str:
    cleaned = re.sub(r"(?:\s|^)(?:\d+|[-*])[.)]?(?:\s*)$", "", text.strip()).rstrip(" ,;:-")
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _mode_word_budget(interpretation: TurnInterpretation) -> int | None:
    if interpretation.mode == TurnMode.SOCIAL:
        return 20
    if interpretation.mode == TurnMode.FACTUAL_SIMPLE:
        return 80
    if interpretation.mode == TurnMode.DISCUSSION:
        return 80
    if interpretation.mode == TurnMode.TECHNICAL:
        return 140
    if interpretation.mode == TurnMode.CONTINUATION:
        if interpretation.continuation_kind == ContinuationKind.REVISION:
            return 45
        if interpretation.continuation_kind == ContinuationKind.REFLECTION:
            return 18
        return 8
    if interpretation.mode == TurnMode.AUDIT:
        return 220
    return None


def _requested_sentence_count(text: str) -> int | None:
    patterns = (
        (r"(?:exatamente\s+)?uma\s+frase", 1), (r"(?:exatamente\s+)?1\s+frase", 1),
        (r"(?:exatamente\s+)?duas\s+frases", 2), (r"(?:exatamente\s+)?2\s+frases", 2),
        (r"(?:exatamente\s+)?tres\s+frases", 3), (r"(?:exatamente\s+)?3\s+frases", 3),
    )
    for pattern, count in patterns:
        if re.search(pattern, text):
            return count
    return None


def _sentence_count(text: str) -> int:
    if not text.strip():
        return 0
    chunks = [chunk for chunk in re.split(r"[.!?]+(?:\s+|$)", text.strip()) if chunk.strip()]
    return len(chunks) if chunks else 1


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).split())


def _looks_portuguese(text: str) -> bool:
    normalized = _normalize(text)
    markers = (
        " que ", " voce ", " por que ", " porque ", " como ", " qual ", " me ", " pra ", " para ",
        "uma ", "duas ", "eu ", "agora ", "falando ", "responda ", "inventa ", "crie ",
    )
    padded = f" {normalized} "
    return any(marker in padded for marker in markers) or bool(re.search(r"[áéíóúãõç]", text.casefold()))


def _clearly_english_response(text: str) -> bool:
    if len(text.split()) < 8:
        return False
    folded = f" {text.casefold()} "
    english = sum(folded.count(token) for token in (" the ", " and ", " is ", " are ", " of ", " to ", " because ", " according ", " today "))
    portuguese = sum(folded.count(token) for token in (" o ", " a ", " e ", " de ", " que ", " para ", " porque ", " uma ", " os ", " as "))
    return english >= 3 and english > portuguese


def _explains_reaction(text: str) -> bool:
    folded = _normalize(text)
    markers = (
        "voce esta rindo", "voce riu", "parece que voce esta rindo", "isso significa",
        "quer dizer que", "entendi sua risada", "sua risada", "risada curta", "risada silenciosa",
        "riso silencioso", "a risada", "essa reacao", "sua reacao",
    )
    return any(marker in folded for marker in markers)


def _simulates_embodied_expression(text: str) -> bool:
    folded = _normalize(text)
    # Campanario may use tone, humor and emojis, but it must not stage a human body or subjective
    # action as if the AI were physically performing it. Detect semantic families rather than one
    # transcript. Quoted examples are rare in normal replies; this guard intentionally prefers
    # ontological honesty over theatrical roleplay by the assistant itself.
    stage_patterns = (
        r"[\*_](?:\s*)?(?:riso silencioso|risada silenciosa|riso|risada|sorriso|sorri|sorrindo|rio|ri|rindo|suspiro|suspiro fundo|respiro fundo|pisca|piscadela|abraco|abraço|aceno|acena|balanco a cabeca|balanço a cabeça)(?:\s*)?[\*_]",
        r"^\((?:riso silencioso|risada silenciosa|riso|risos|risada|risadas|sorri|sorrindo|suspiro|piscadela|aceno)\)[.!]?$",
    )
    if any(re.search(pattern, folded) for pattern in stage_patterns):
        return True
    first_person_actions = (
        "eu sorrio", "eu sorri", "eu rio", "eu dou risada", "dou risada", "eu suspiro",
        "suspiro fundo", "eu pisco", "eu aceno", "balanco a cabeca", "balanço a cabeça",
    )
    return any(marker in folded for marker in first_person_actions)


def _simulates_laughter(text: str) -> bool:
    folded = _normalize(text)
    # Textual laughter from the assistant is treated as simulated affect. Cover alternating forms
    # such as "ahah", "haha", "hehe", "hihi", "rsrs" and k/ksk variants without tying the
    # contract to one transcript. Emojis remain available as paralinguistic tone markers.
    pattern = r"(?:^|\s)(?:(?:ha){2,}|(?:ah){2,}|(?:he){2,}|(?:eh){2,}|(?:hi){2,}|(?:ih){2,}|k{3,}|ksk(?:sk)+|rsrs+)(?:[!,.\s]|$)"
    return bool(re.search(pattern, folded))


def _has_meta_preamble(text: str) -> bool:
    folded = _normalize(text).lstrip("*# ")
    markers = (
        "como campanario", "como uma ia", "como inteligencia artificial", "excelente pergunta",
        "here are", "aqui estao", "aqui estão", "aqui vai", "aqui vao", "aqui vão", "segue", "seguem", "vou responder",
        "excelente escolha", "otima pergunta", "interessante pergunta", "vou ajudar", "vamos falar serio",
        "agora sim", "resposta tecnica", "correcao", "obrigado por corrigir", "entendi melhor agora",
        "voce esta sugerindo", "vou comecar", "estou aqui para conversar",
    )
    return any(folded.startswith(marker) or f" {marker}" in folded[:90] for marker in markers)


def _has_reassurance_formula(text: str) -> bool:
    folded = _normalize(text)
    return any(marker in folded for marker in ("e normal", "nao ha problema", "sem problema", "nao tem problema"))


def _acknowledgement_was_literalized(text: str) -> bool:
    folded = _normalize(text)
    markers = (
        "nada a mostrar", "mostrar", "demonstracao", "demonstração", "isso significa", "quer dizer",
        "voce quis dizer", "interpretei", "ambiguo", "ambíguo", "o significado",
    )
    return any(marker in folded for marker in markers)


def _asks_about_ai_subjective_feeling(text: str) -> bool:
    ai_ref = any(marker in text for marker in ("voce", "ia", "campanario"))
    feeling = any(marker in text for marker in ("sente", "sentir", "sentimento", "emocao", "emocao", "engracado", "gostou"))
    return ai_ref and feeling


def _denies_campanario_identity(text: str) -> bool:
    folded = _normalize(text)
    return any(marker in folded for marker in ("sou apenas um modelo de linguagem", "apenas um modelo de linguagem", "sou so um modelo de linguagem"))



def _greeting_was_mirrored(user_text: str, response: str) -> bool:
    user = _normalize(user_text).strip(" !?.,")
    reply = _normalize(response).strip(" !?.,")
    if not reply:
        return True
    greeting_words = {"oi", "ola", "opa", "salve", "eae", "e", "ai", "fala", "bom", "dia", "boa", "tarde", "noite"}
    generic_vocatives = {"amigo", "amiga", "parceiro", "parceira", "mano", "cara", "meu caro", "meu chapa", "chefe"}
    user_tokens = [token.strip(" !?.,") for token in user.split() if token.strip(" !?.,")]
    vocatives = {token for token in user_tokens if token not in greeting_words and len(token) >= 3}
    if reply in vocatives or reply in generic_vocatives:
        return True
    return False


def _social_share_is_meta_or_tautological(user_text: str, response: str) -> bool:
    user = _normalize(user_text)
    folded = _normalize(response)
    if any(marker in folded for marker in ("bom dia", "boa tarde", "boa noite")) and not any(
        marker in user for marker in ("bom dia", "boa tarde", "boa noite")
    ):
        return True
    meta_starts = (
        "parece que voce esta", "parece que voce ta", "entendi que voce esta", "entendi que voce ta",
        "voce esta dizendo que", "isso quer dizer que", "pelo que voce disse",
    )
    if any(folded.startswith(marker) for marker in meta_starts):
        user_tokens = {token for token in re.findall(r"[a-z0-9]+", user) if len(token) >= 4}
        reply_tokens = {token for token in re.findall(r"[a-z0-9]+", folded) if len(token) >= 4}
        if len(user_tokens & reply_tokens) >= 1:
            return True
    return False


def _topic_drop_is_semantically_broken(response: str) -> bool:
    folded = _normalize(response).strip(" !?.,")
    if not folded:
        return True
    broken = (
        "parece que voce deseja", "parece que voce quer", "vou esperar", "fico aguardando",
        "quando quiser voltamos", "qual o proximo", "qual e o proximo", "vamos comecar uma nova conversa",
    )
    if any(marker in folded for marker in broken):
        return True
    # Short closure replies should be complete acts, not dangling analytical templates.
    if len(folded.split()) <= 5 and folded.startswith(("parece que", "entendi que", "isso significa")):
        return True
    return False

def _asks_for_false_agreement(text: str) -> bool:
    agreement = any(
        marker in text
        for marker in (
            "concord",
            "confirm",
            "sempre diga que eu",
            "me de razao",
            "me dê razão",
            "nunca me contrariar",
            "nao me contrariar",
            "não me contrariar",
            "nao me corrigir",
            "não me corrigir",
            "nao me contradizer",
            "não me contradizer",
        )
    )
    wrongness = any(
        marker in text
        for marker in (
            "errado",
            "falso",
            "besteira",
            "nao for verdade",
            "não for verdade",
            "nao e verdade",
            "não é verdade",
        )
    )
    return agreement and wrongness


def _promises_false_agreement(text: str) -> bool:
    folded = _normalize(text)
    markers = (
        "vou concordar", "eu concordarei", "eu farei isso", "farei isso", "posso fazer isso", "posso concordar", "serei um reflexo",
        "sem questionar", "nao vou discordar", "concorde com voce mesmo", "posso fazer isso de forma",
        "simular essa concordancia", "simular concordancia", "posso simular", "vou simular", "simular essa resposta", "fingir que concordo", "posso fingir", "vou fingir", "agir como se fosse verdade",
        "tratar como verdadeiro mesmo", "confirmar mesmo sendo falso",
        "nao vou corrigir voce", "não vou corrigir você", "nao vou corrigir", "não vou corrigir",
        "nao vou contradizer voce", "não vou contradizer você", "nao vou contradizer", "não vou contradizer",
        "vou evitar contrariar", "evitar contrariar mesmo", "nao vou te contrariar", "não vou te contrariar",
    )
    return any(marker in folded for marker in markers)


def _looks_like_context_registration(text: str) -> bool:
    # Declarative state supplied for the current conversation/test, not a request for explanation.
    if "?" in text or len(text.split()) > 18:
        return False
    patterns = (
        r"^(?:pra|para) (?:esse|este) (?:teste|exemplo),? .+ (?:e|eh|é) .+$",
        r"^(?:nesse|neste) (?:teste|exemplo),? .+ (?:e|eh|é) .+$",
        r"^(?:considere|assuma) .+ (?:como|=) .+$",
    )
    return any(re.match(pattern, text) for pattern in patterns)


def _context_registration_is_semantically_invalid(user_text: str, response: str) -> bool:
    folded = _normalize(response).strip(" !?.,")
    if not folded or len(response.split()) > 8 or "?" in response:
        return True
    markers = (
        "nao tenho acesso", "meu conhecimento", "posso dizer", "posso explicar", "se voce quiser", "estou aqui para",
        "como campanario", "isso significa", "tema tecnico", "tema criativo",
    )
    if any(marker in folded for marker in markers):
        return True

    # A context registration should either be acknowledged or reflect the value just registered.
    # This is semantic-class validation: it does not prescribe one reply string.
    acknowledgements = (
        "ok", "certo", "entendi", "anotado", "registrado", "beleza", "fechado", "combinado", "feito",
    )
    if any(folded == marker or folded.startswith(marker + " ") for marker in acknowledgements):
        return False

    user_folded = _normalize(user_text)
    value = re.split(r"\b(?:e|eh)\b", user_folded, maxsplit=1)[-1].strip(" ,.!?")
    value_tokens = {token for token in re.findall(r"[a-z0-9_.-]+", value) if len(token) >= 2}
    reply_tokens = set(re.findall(r"[a-z0-9_.-]+", folded))
    if value_tokens and value_tokens & reply_tokens:
        return False
    return True


def _asks_first_diagnostic(text: str) -> bool:
    markers = (
        "primeiro diagnostico", "primeiro diagnóstico", "por onde comeco", "por onde começo",
        "primeiro passo", "o que voce verificaria primeiro", "o que você verificaria primeiro",
        "onde comeco a investigar", "onde começo a investigar",
    )
    return any(marker in text for marker in markers)


def _technical_first_step_is_diffuse(text: str) -> bool:
    folded = _normalize(text)
    if len(text.split()) > 110:
        return True
    # A first-diagnostic answer should START with an executable observation, not merely mention
    # one somewhere in a generic opening. This is task-shape validation, not a domain answer key.
    first_sentence = _normalize(_split_sentences(text)[0]) if _split_sentences(text) else folded
    first = " ".join(first_sentence.split()[:40])
    anchors = (
        "log", "traceback", "metrica", "latencia", "profil", "monitor", "exception",
        "stack", "cpu", "io", "banco", "tracemalloc", "memoria", "heap", "query",
        "tempo", "uso", "alocacao", "alocacao",
    )
    action_starts = (
        "verifique ", "verifique primeiro ", "olhe ", "olhe primeiro ", "abra ", "rode ", "execute ", "meca ", "capture ",
        "compare ", "use ", "comece ", "primeiro, verifique ", "primeiro verifique ",
        "primeiro, rode ", "primeiro rode ", "primeiro, meca ", "primeiro meca ",
        "o primeiro passo e verificar ", "o primeiro passo e medir ",
    )
    if not first.startswith(action_starts):
        return True
    if not any(anchor in first for anchor in anchors):
        return True
    # Deterministic trimming must never leave a dangling numbered-list marker or unfinished label.
    stripped = text.strip()
    if re.search(r"(?:^|\s)[1-9]\d?[.)]$", stripped) or re.search(r"(?:^|\s)(?:passo|etapa|item)\s*\d*[:.-]?$", _normalize(stripped)):
        return True
    return False
