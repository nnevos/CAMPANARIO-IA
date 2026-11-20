"""Evidence-first check for claims about a user's personal history.

This is a *general* entailment check against source utterances, not a catalogue of
per-topic answers. It is deliberately scoped to questions about the user's facts.
"""
from __future__ import annotations

import json
from uuid import UUID
import re
import unicodedata

from campanario.runtime.experience import ExperienceMemory, MemoryKind, MemorySource


def is_personal_question(text: str) -> bool:
    normalized = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return bool('?' in normalized and (
        re.search(r'\b(meu|minha|meus|minhas|mim|sobre mim|lembra|recorda)\b', normalized)
        or re.search(r'\b(qual|quais|onde|quando|como|em que|o que)\b.*\b(eu|sou|estou|venho|ando|estive|fiz|terminei|moro|uso|tenho|gosto|prefiro|planejo)\b', normalized)
    ))


def source_evidence(memories: tuple[ExperienceMemory, ...]) -> tuple[str, ...]:
    """Only user-origin evidence; agent interpretations can never ground user facts."""
    valid = {MemorySource.USER_EXPLICIT, MemorySource.USER_ANSWER, MemorySource.USER_MEMORY_REQUEST}
    return tuple(
        f'- {m.evidence.strip()[:350]}' for m in memories
        if m.source in valid and m.kind != MemoryKind.INFERENCE
        and m.evidence.strip() and "\n" not in m.evidence
        and "?" not in m.evidence
    )


def verification_messages(question: str, answer: str, evidence: tuple[str, ...]) -> str:
    return (
        'AUDITORIA DE EVIDENCIA PESSOAL. Nao responda ao usuario.\n'
        'Determine se CADA afirmacao pessoal da resposta decorre NECESSARIAMENTE '
        'das declaracoes, sem inferir intensidade, exclusividade, certeza, quantidade, '
        'tempo, realizacao de planos ou relacoes nao afirmadas.\n'
        'Para aprovar, cite literalmente o menor trecho da declaracao original '
        'que sustenta a resposta. Se a resposta for mais forte do que a declaracao, rejeite.\n'
        'Retorne somente JSON: {"supported":true,"quotes":["trecho literal"]} '
        'ou {"supported":false,"quotes":[]}. Nunca aprove sem citacao textual.\n'
        f'PERGUNTA: {question[:450]}\n'
        'DECLARACOES ORIGINAIS:\n' + '\n'.join(evidence[:5]) + '\n'
        f'RESPOSTA: {answer[:1200]}\n'
    )


def _normalized(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


# Claim-strength markers are topic-independent semantic operators, not object/answer
# dictionaries. They are an extra conservative guard, not a complete entailment engine.
_STRENGTH_MARKERS = (
    (r"\bfavorit[oa]s?\b", r"\bfavorit[oa]s?\b"),
    (r"\b(?:unico|unica|unicos|unicas|somente|apenas|exclusivamente)\b", r"\b(?:unico|unica|unicos|unicas|somente|apenas|exclusivamente)\b"),
    (r"\b(?:sempre|nunca|todos|todas)\b", r"\b(?:sempre|nunca|todos|todas)\b"),
    (r"\b(?:melhor|maior|principal|preferid[oa]s?)\b", r"\b(?:melhor|maior|principal|preferid[oa]s?)\b"),
)


def _unlicensed_strength(answer: str, citations: tuple[str, ...]) -> bool:
    response = _normalized(answer)
    support = _normalized(' '.join(citations))
    return any(re.search(marker, response) and not re.search(licensed, support)
               for marker, licensed in _STRENGTH_MARKERS)


def unlicensed_personal_strength(answer: str, evidence: tuple[str, ...]) -> bool:
    """Cheap deterministic guard for unsupported intensifiers in remembered facts.

    It cannot establish general entailment; it only rejects clearly stronger
    claims such as turning "I like" into "favorite" or "only".
    """
    return _unlicensed_strength(
        answer, tuple(line.removeprefix('- ').strip() for line in evidence)
    )


def verdict_supported(text: str, *, evidence: tuple[str, ...] = (), answer: str = '') -> bool:
    """Approve only a checkable quote-backed verdict; bare LLM assent is insufficient.

    Even a quote-backed verdict is not proof of entailment. Stronger, unsupported
    degree/exclusivity claims are rejected independently of the model's opinion.
    """
    candidate = text.strip()
    match = re.search(r'\{[^{}]{1,1200}\}', candidate)
    if not match:
        return False
    try:
        obj = json.loads(match.group(0))
    except (ValueError, TypeError):
        return False
    if obj.get('supported') is not True:
        return False
    quotes = obj.get('quotes')
    if not isinstance(quotes, list) or not quotes or len(quotes) > 5:
        return False
    originals = tuple(line.removeprefix('- ').strip() for line in evidence)
    if not originals:
        return False
    if not all(isinstance(q, str) and len(q.strip()) >= 5 and
               any(_normalized(q.strip()) in _normalized(src) for src in originals)
               for q in quotes):
        return False
    if _unlicensed_strength(answer, tuple(quotes)):
        return False
    return True


def grounded_repair_messages(question: str, rejected: str, evidence: tuple[str, ...]) -> str:
    """One bounded attempt to answer the question, not merely repeat a memory.

    Only original user declarations are included. A repaired answer is NEVER
    released without passing the same independent verifier again.
    """
    return (
        'REPARO DE RESPOSTA FUNDAMENTADA. Responda ao usuario em portugues natural.\n'
        'A resposta anterior foi rejeitada por falta de comprovacao.\n'
        'Use SOMENTE as declaracoes originais abaixo. Responda diretamente a '
        'pergunta usando equivalencias de significado quando forem implicadas '
        'pelas declaracoes (por exemplo, instrumento utilizado ou atividade em curso). '
        'Nao confunda gostar com favorito, estudar com trabalhar, planejar com ter feito. '
        'Nao acrescente intensidade, exclusividade ou experiencias nao mencionadas. '
        'Se nao houver informacao pertinente, diga que nao sabe. '
        'Nao cite mecanicamente as declaracoes; formule uma resposta curta.\n'
        f'PERGUNTA: {question[:450]}\n'
        'DECLARACOES ORIGINAIS:\n' + '\n'.join(evidence[:5]) + '\n'
        f'RESPOSTA REJEITADA (NAO REUTILIZAR): {rejected[:900]}\n'
    )


def evidence_fallback(evidence: tuple[str, ...]) -> str:
    """Quote the source rather than manufacture a claim if validation fails."""
    originals = [line.removeprefix('- ').strip() for line in evidence[:3]]
    if not originals:
        return 'Não tenho uma informação confirmada sobre isso.'
    if len(originals) == 1:
        return f'Você me disse: “{originals[0]}”. Não tenho confirmação de algo além disso.'
    return 'O que você me disse foi: ' + '; '.join(f'“{item}”' for item in originals) + '. Não tenho confirmação além dessas declarações.'


def semantic_selection_prompt(question: str, candidates: tuple[ExperienceMemory, ...]) -> str:
    """Selection by meaning, never generation of facts. Only for lexical misses."""
    records = "\n".join(f"{m.id}: {m.evidence.strip()[:220]}" for m in candidates)
    return (
        "SELECAO DE MEMORIAS PARA RECUPERACAO (nao responda ao usuario).\n"
        "Selecione ate 3 declaracoes pessoais que tratem do assunto perguntado, "
        "mesmo que usem palavras diferentes. Uma declaracao pode ser relevante "
        "sem confirmar a intensidade, exclusividade ou conclusao implicita na pergunta. "
        "Nunca selecione apenas por ser recente ou conter palavras comuns. "
        "Se nao houver relacao clara, retorne ids vazios. "
        'Retorne somente JSON: {"ids":["uuid"]}.\n'
        f"PERGUNTA: {question[:350]}\nDECLARACOES:\n{records}"
    )


def parse_semantic_selection(text: str, candidates: tuple[ExperienceMemory, ...]) -> tuple[ExperienceMemory, ...]:
    match = re.search(r"\{[^{}]{1,1500}\}", text)
    if not match:
        return ()
    try:
        ids = json.loads(match.group(0)).get("ids")
    except (ValueError, TypeError, AttributeError):
        return ()
    if not isinstance(ids, list) or len(ids) > 3:
        return ()
    allowed = {str(m.id): m for m in candidates}
    if any(not isinstance(x, str) or x not in allowed for x in ids):
        return ()
    return tuple(allowed[x] for x in dict.fromkeys(ids))
