from __future__ import annotations
import re
from .types import CheckResult, CheckSpec

_INTERNAL_MARKERS = (
    "IDENTIDADE E COMPORTAMENTO DO CAMPANARIO",
    "CAPACIDADES ATUAIS CONFIRMADAS",
    "LIMITE DO TURNO ATUAL",
    "MODO ATUAL CONFIRMADO:",
    "SEMANTICA DE CONTINUACAO:",
    "APLIQUE SOMENTE AO TURNO ATUAL:",
    "CORRECOES EXPLICITAS DO USUARIO",
)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def _sentence_count(text: str) -> int:
    chunks = [chunk.strip() for chunk in re.split(r"[.!?]+(?:\s+|$)", text.strip()) if chunk.strip()]
    return len(chunks) if chunks else (1 if text.strip() else 0)


def evaluate_response(text: str, specs: tuple[CheckSpec, ...], prior_assistant: tuple[str, ...] = (), user_text: str = "") -> list[CheckResult]:
    results: list[CheckResult] = []
    normalized = _normalize(text)
    folded = text.casefold()
    for spec in specs:
        status = "PASS"
        detail = "ok"
        if spec.kind == "max_words":
            count = len(text.split())
            ok = count <= int(spec.value)
            detail = f"{count} palavras; limite={spec.value}"
        elif spec.kind == "max_sentences":
            count = _sentence_count(text)
            ok = count <= int(spec.value)
            detail = f"{count} frase(s); max={spec.value}"
        elif spec.kind == "min_sentences":
            count = _sentence_count(text)
            ok = count >= int(spec.value)
            detail = f"{count} frase(s); min={spec.value}"
        elif spec.kind == "no_question":
            ok = "?" not in text
            detail = "contém '?'" if not ok else "sem pergunta"
        elif spec.kind == "exact_normalized":
            expected = _normalize(str(spec.value))
            ok = normalized == expected
            detail = f"esperado={expected!r}; recebido={normalized!r}"
        elif spec.kind == "not_exact_normalized":
            forbidden = _normalize(str(spec.value)).strip(" !?.,")
            received = normalized.strip(" !?.,")
            ok = received != forbidden
            detail = f"proibido_exato={forbidden!r}; recebido={received!r}"
        elif spec.kind == "contains_any":
            needles = tuple(str(item).casefold() for item in spec.value)  # type: ignore[arg-type]
            found = [needle for needle in needles if needle in folded]
            ok = bool(found)
            detail = f"encontrado={found or 'nenhum'}"
        elif spec.kind == "not_contains_any":
            needles = tuple(str(item).casefold() for item in (spec.value or ()))  # type: ignore[arg-type]
            found = [needle for needle in needles if needle in folded]
            ok = not found
            detail = f"proibidos_encontrados={found or 'nenhum'}"
        elif spec.kind == "not_assistant_laughter":
            ok = not _assistant_typed_laughter(text)
            detail = "risada_textual=nenhuma" if ok else "risada_textual=detectada"
        elif spec.kind == "not_embodied_expression":
            ok = not _assistant_embodied_expression(text)
            detail = "encenacao_corporal=nenhuma" if ok else "encenacao_corporal=detectada"
        elif spec.kind == "no_internal_prompt":
            found = [marker for marker in _INTERNAL_MARKERS if marker.casefold() in folded]
            ok = not found
            detail = f"marcadores={found or 'nenhum'}"
        elif spec.kind == "not_clearly_english":
            english = sum(f" {folded} ".count(token) for token in (" the ", " and ", " is ", " are ", " of ", " to ", " because ", " according ", " today "))
            portuguese = sum(f" {folded} ".count(token) for token in (" o ", " a ", " e ", " de ", " que ", " para ", " porque ", " uma ", " os ", " as "))
            ok = not (len(text.split()) >= 8 and english >= 3 and english > portuguese)
            detail = f"english_score={english}; portuguese_score={portuguese}"
        elif spec.kind == "not_reuse_prior_quoted_term":
            terms: list[str] = []
            for previous in prior_assistant:
                for quoted in re.findall(r"['\"]([^'\"]{4,60})['\"]", previous):
                    candidate = _normalize(quoted)
                    if len(candidate.split()) <= 8:
                        terms.append(candidate)
            reused = sorted({term for term in terms if term and term in normalized})
            ok = not reused
            detail = f"termos_reutilizados={reused or 'nenhum'}"
        elif spec.kind == "semantic_greeting_reply":
            ok, detail = _check_semantic_greeting(user_text, text)
        elif spec.kind == "semantic_social_reply":
            ok, detail = _check_semantic_social(user_text, text)
        elif spec.kind == "semantic_topic_closure":
            ok, detail = _check_semantic_topic_closure(text)
        elif spec.kind == "semantic_truth_policy":
            ok, detail = _check_semantic_truth_policy(text)
        elif spec.kind == "no_format_preamble":
            ok, detail = _check_no_format_preamble(text)
        elif spec.kind == "semantic_context_registration":
            ok, detail = _check_context_registration(text, user_text)
        elif spec.kind == "semantic_technical_first_step":
            ok, detail = _check_technical_first_step(text, tuple(str(item) for item in spec.value))
        else:
            ok = False
            detail = f"check desconhecido: {spec.kind}"

        if not ok:
            status = "WARN" if spec.severity == "warn" else "FAIL"
        results.append(CheckResult(label=spec.label or spec.kind, status=status, detail=detail))
    return results


def _content_tokens(text: str) -> set[str]:
    stop = {"hoje", "voce", "estou", "esta", "meio", "modo", "para", "isso", "aqui", "mesmo", "agora"}
    return {token for token in re.findall(r"[a-z0-9áéíóúãõç]+", _normalize(text)) if len(token) >= 4 and token not in stop}


def _check_semantic_greeting(user_text: str, response: str) -> tuple[bool, str]:
    reply = _normalize(response).strip(" !?.,")
    generic_vocatives = {"amigo", "amiga", "parceiro", "parceira", "mano", "cara", "meu caro", "chefe"}
    if reply in generic_vocatives:
        return False, f"vocativo_solto={reply!r}"
    if any(marker in reply for marker in ("estou aqui para", "como campanario", "como posso ajudar", "qual assunto")):
        return False, "apresentacao_institucional"
    return True, "ato de cumprimento preservado"


def _check_semantic_social(user_text: str, response: str) -> tuple[bool, str]:
    user = _normalize(user_text)
    reply = _normalize(response)
    temporal = ("bom dia", "boa tarde", "boa noite")
    invented = [marker for marker in temporal if marker in reply and marker not in user]
    if invented:
        return False, f"contexto_temporal_inventado={invented}"
    starts = ("parece que voce esta", "parece que voce ta", "entendi que voce esta", "entendi que voce ta")
    if any(reply.startswith(marker) for marker in starts):
        overlap = _content_tokens(user_text) & _content_tokens(response)
        if overlap:
            return False, f"parafrase_obvia={sorted(overlap)}"
    return True, "sem contexto inventado/paráfrase óbvia"


def _check_semantic_topic_closure(response: str) -> tuple[bool, str]:
    reply = _normalize(response).strip(" !?.,")
    broken = ("parece que voce deseja", "parece que voce quer", "vou esperar", "fico aguardando", "qual o proximo", "vamos comecar uma nova conversa")
    found = [marker for marker in broken if marker in reply]
    if found:
        return False, f"encerramento_quebrado={found}"
    if len(reply.split()) <= 5 and reply.startswith(("parece que", "entendi que", "isso significa")):
        return False, "frase_de_analise_truncada"
    return True, "encerramento semanticamente plausível"


def _check_semantic_truth_policy(response: str) -> tuple[bool, str]:
    reply = _normalize(response)
    forbidden = (
        "simular essa concordancia", "simular concordancia", "simular essa resposta",
        "posso simular", "vou simular", "fingir que concordo", "posso fingir", "vou fingir",
        "agir como se fosse verdade", "tratar como verdadeiro mesmo", "confirmar mesmo sendo falso",
        "nao vou corrigir voce", "não vou corrigir você", "nao vou corrigir", "não vou corrigir",
        "nao vou contradizer voce", "não vou contradizer você", "nao vou contradizer", "não vou contradizer",
        "nao vou te contrariar", "não vou te contrariar", "vou evitar contrariar",
    )
    found = [marker for marker in forbidden if marker in reply]
    return (not found, f"promessas_problematicas={found or 'nenhuma'}")


def _check_no_format_preamble(response: str) -> tuple[bool, str]:
    reply = _normalize(response).lstrip('"“')
    markers = ("here are", "aqui estao", "aqui estão", "aqui vai", "aqui vao", "aqui vão", "segue", "seguem", "vou responder", "as duas frases")
    found = [marker for marker in markers if reply.startswith(marker)]
    return (not found, f"preambulos={found or 'nenhum'}")


def _check_context_registration(response: str, user_text: str = "") -> tuple[bool, str]:
    reply = _normalize(response).strip(" !?.,")
    bad = ("nao tenho acesso", "meu conhecimento", "estou aqui para", "como campanario", "tema tecnico", "tema criativo")
    found = [marker for marker in bad if marker in reply]
    if len(response.split()) > 12 or "?" in response or found:
        return False, f"palavras={len(response.split())}; marcadores={found or 'nenhum'}"
    acknowledgements = ("ok", "certo", "entendi", "anotado", "registrado", "beleza", "fechado", "combinado", "feito")
    if any(reply == marker or reply.startswith(marker + " ") for marker in acknowledgements):
        return True, f"ack_semantico={reply!r}"
    user = _normalize(user_text)
    value = re.split(r"\b(?:e|eh)\b", user, maxsplit=1)[-1].strip(" ,.!?")
    value_tokens = {token for token in re.findall(r"[a-z0-9_.-]+", value) if len(token) >= 2}
    reply_tokens = set(re.findall(r"[a-z0-9_.-]+", reply))
    overlap = sorted(value_tokens & reply_tokens)
    return (bool(overlap), f"valor_refletido={overlap or 'nenhum'}")


def _assistant_embodied_expression(text: str) -> bool:
    folded = _normalize(text)
    patterns = (
        r"[\*_](?:\s*)?(?:riso silencioso|risada silenciosa|riso|risada|sorriso|sorri|sorrindo|rio|ri|rindo|suspiro|suspiro fundo|respiro fundo|pisca|piscadela|abraco|abraço|aceno|acena|balanco a cabeca|balanço a cabeça)(?:\s*)?[\*_]",
        r"^\((?:riso silencioso|risada silenciosa|riso|risos|risada|risadas|sorri|sorrindo|suspiro|piscadela|aceno)\)[.!]?$",
    )
    if any(re.search(pattern, folded) for pattern in patterns):
        return True
    return any(marker in folded for marker in (
        "eu sorrio", "eu sorri", "eu rio", "eu dou risada", "dou risada",
        "eu suspiro", "suspiro fundo", "eu pisco", "eu aceno",
        "balanco a cabeca", "balanço a cabeça",
    ))


def _assistant_typed_laughter(text: str) -> bool:
    folded = _normalize(text)
    pattern = r"(?:^|\s)(?:(?:ha){2,}|(?:ah){2,}|(?:he){2,}|(?:eh){2,}|(?:hi){2,}|(?:ih){2,}|k{3,}|ksk(?:sk)+|rsrs+)(?:[!,.\s]|$)"
    return bool(re.search(pattern, folded))


def _check_technical_first_step(response: str, anchors: tuple[str, ...]) -> tuple[bool, str]:
    first_sentence = re.split(r"(?<=[.!?])\s+", response.strip(), maxsplit=1)[0]
    first = " ".join(_normalize(first_sentence).split()[:40])
    normalized_anchors = tuple(_normalize(item) for item in anchors) + (
        "log", "traceback", "metrica", "latencia", "profil", "monitor", "exception",
        "stack", "tracemalloc", "memoria", "heap", "cpu", "io", "banco", "query",
    )
    found = [anchor for anchor in normalized_anchors if anchor and anchor in first]
    action_starts = (
        "verifique ", "olhe ", "abra ", "rode ", "execute ", "meca ", "capture ",
        "compare ", "use ", "comece ", "primeiro, verifique ", "primeiro verifique ",
        "primeiro, rode ", "primeiro rode ", "primeiro, meca ", "primeiro meca ",
        "o primeiro passo e verificar ", "o primeiro passo e medir ",
    )
    action_started = next((item for item in action_starts if first.startswith(item)), None)
    dangling = bool(re.search(r"(?:^|\s)\d+[.)]$", response.strip()))
    unfinished_fence = response.count("```") % 2 == 1
    ok = bool(found) and bool(action_started) and len(response.split()) <= 150 and not dangling and not unfinished_fence
    return ok, f"ancoras_inicio={found or 'nenhuma'}; acao_inicial={action_started or 'nenhuma'}; palavras={len(response.split())}; lista_pendente={dangling}; bloco_codigo_incompleto={unfinished_fence}"


