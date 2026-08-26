from __future__ import annotations

import re
import unicodedata

from .extractor import _normalize_for_match
from .models import RenPyGDD, ValidationIssue, ValidationReport


def _question_sets(gdd: RenPyGDD):
    yield "main_question", gdd.main_question, [3, 1, 0]
    for route_name, route in (("route_a", gdd.route_a), ("route_b", gdd.route_b), ("route_c", gdd.route_c)):
        for idx, question in enumerate(route.questions, start=1):
            yield f"{route_name}.questions[{idx}]", question, [2, 0]


def _normalize_evidence_lexically(text: str) -> str:
    """Normalize editorial noise without turning paraphrases into matches.

    We preserve the exact word/number sequence and only ignore differences that can
    arise from DOCX/PDF typography: punctuation, bullets, smart quotes, dashes and
    whitespace. This keeps grounding fail-closed while avoiding false negatives for
    verbatim wording rendered with different typography.
    """
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens = re.findall(r"[^\W_]+(?:['’][^\W_]+)?", normalized, flags=re.UNICODE)
    return " ".join(tokens)


def evidence_quote_present(quote: str, ebook_text: str) -> bool:
    quote_lexical = _normalize_evidence_lexically(quote)
    ebook_lexical = _normalize_evidence_lexically(ebook_text)
    return len(quote_lexical) >= 8 and quote_lexical in ebook_lexical




def explicit_question_concepts(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    concepts: set[str] = set()
    for value in re.findall(r"[\"'‘’“”]([^\"'‘’“”]{4,80})[\"'‘’“”]", normalized):
        key = _normalize_for_match(value).strip()
        if len(key) >= 5:
            concepts.add(key)
    return concepts


def _question_records(gdd: RenPyGDD):
    yield "main_question", gdd.main_question
    for route_name, route in (("route_a", gdd.route_a), ("route_b", gdd.route_b), ("route_c", gdd.route_c)):
        for idx, question in enumerate(route.questions, start=1):
            yield f"{route_name}.questions[{idx}]", question

def validate_gdd(gdd: RenPyGDD, ebook_normalized_text: str) -> ValidationReport:
    issues: list[ValidationIssue] = []
    checked = 0
    if len(gdd.route_a.questions) != 3 or len(gdd.route_b.questions) != 3 or len(gdd.route_c.questions) != 3:
        issues.append(ValidationIssue("routes", "Cada rota deve conter exatamente 3 perguntas."))

    if not 5 <= len(gdd.intro_lines) <= 6:
        issues.append(ValidationIssue("intro_lines", "A introdução deve ter 5 ou 6 falas de narrador para contextualizar regras e objetivo.", "warning"))
    intro_text = " ".join(gdd.intro_lines)
    # The fixed profile has +3/+1/0 only on the main question and +2/0 on
    # route questions. Reject wording that tells the player every correct answer
    # is worth +3, which misrepresents the actual scoring contract.
    if re.search(r"(?:cada|toda)\s+(?:resposta|escolha)[^.!?]{0,40}(?:correta|adequada)[^.!?]{0,25}(?:vale|valera|rendera|rende)\s*\+?3", intro_text, re.I):
        issues.append(ValidationIssue(
            "intro_lines",
            "A introdução descreve a pontuação de forma incorreta: +3 vale apenas para a alternativa adequada da pergunta principal; perguntas adicionais usam +2/0.",
            "warning",
        ))
    if not 2 <= len(gdd.character_intro_lines) <= 3:
        issues.append(ValidationIssue("character_intro_lines", "A apresentação do personagem deve ter 2 ou 3 falas naturais.", "warning"))
    route_titles = [_normalize_for_match(gdd.route_a.title), _normalize_for_match(gdd.route_b.title), _normalize_for_match(gdd.route_c.title)]
    if len(set(route_titles)) != 3:
        issues.append(ValidationIssue("routes.title", "As três trilhas precisam de títulos distintos.", "warning"))

    # Cross-route concept repetition: quoted pedagogical terms such as
    # "falibilidade" / "circularidade" are strong semantic anchors. If the
    # same explicit concept is asked again later, regenerate only the later stage.
    concept_owner: dict[str, str] = {}
    for qpath, question in _question_records(gdd):
        for concept in explicit_question_concepts(question.prompt):
            previous = concept_owner.get(concept)
            if previous is not None:
                issues.append(ValidationIssue(
                    qpath,
                    f"Conceito repetido em outra pergunta: '{concept}' já foi avaliado em {previous}.",
                ))
            else:
                concept_owner[concept] = qpath

    seen_prompts: set[str] = set()
    seen_choices: set[str] = set()
    for path, question, expected_scores in _question_sets(gdd):
        prompt_key = _normalize_for_match(question.prompt)
        if prompt_key in seen_prompts:
            issues.append(ValidationIssue(path, "Pergunta duplicada."))
        seen_prompts.add(prompt_key)
        scores = [choice.score for choice in question.choices]
        if scores != expected_scores:
            issues.append(ValidationIssue(path, f"Pontuação inválida: esperado {expected_scores}, recebido {scores}."))
        if len(question.choices) != len(expected_scores):
            issues.append(ValidationIssue(path, "Quantidade de alternativas inválida."))
            continue
        for cidx, choice in enumerate(question.choices, start=1):
            checked += 1
            if not evidence_quote_present(choice.evidence.quote, ebook_normalized_text):
                issues.append(ValidationIssue(f"{path}.choices[{cidx}].evidence", "A citação de evidência não foi localizada no e-book com a mesma sequência de palavras."))
            choice_key = _normalize_for_match(choice.text)
            if choice_key in seen_choices:
                issues.append(ValidationIssue(f"{path}.choices[{cidx}]", "Alternativa duplicada em outra parte do banco.", "warning"))
            seen_choices.add(choice_key)
            if re.search(r"\b(correto|certo|incorreto|errado|alternativa certa|parcialmente correto)\b", choice.feedback, re.I):
                issues.append(ValidationIssue(f"{path}.choices[{cidx}].feedback", "Feedback contém rótulo mecânico proibido.", "warning"))
            if re.search(r"[✅⚠❌✔✖]", choice.feedback):
                issues.append(ValidationIssue(f"{path}.choices[{cidx}].feedback", "Feedback contém emoji de julgamento proibido.", "warning"))
            if len(choice.feedback.split()) < 5:
                issues.append(ValidationIssue(f"{path}.choices[{cidx}].feedback", "Feedback pedagógico curto demais para explicar o conceito.", "warning"))

    errors = [issue for issue in issues if issue.severity == "error"]
    return ValidationReport(not errors, tuple(issues), checked)
