"""Conservative, deterministic *answerability* gate for local literal extracts.

A retrieved passage merely sharing a topic with the question is NOT evidence
that it answers the requested attribute. This small gate recognizes explicit
question-focus words within the exact passage. It is intentionally incomplete:
when unsure, it refuses to promote the passage to a supported source assertion.

It is NOT a general semantic entailment model, nor verification of external truth.
It never accesses the network, a model, a database, or the user's memory.
"""
from __future__ import annotations

from dataclasses import dataclass

from campanario.chat.local_library import _WORD, _fold, _inflections, _tokens

# Structural/query labels do not identify the relation the user asked about.
# This is a bounded set of grammatical terms, not a growing entity allow-list.
_STRUCTURE = frozenset({
    'qual', 'quais', 'quanto', 'quantos', 'quanta', 'quantas',
    'projeto', 'protocolo', 'guia', 'manual', 'diario', 'documento',
    'teste', 'sistema', 'ficticio', 'ficticia', 'sintetico', 'sintetica',
    'morgana', 'todd', 'campanario',
})
_QUESTION_STOP = frozenset({
    'de', 'do', 'dos', 'da', 'das', 'no', 'na', 'nas', 'nos', 'em', 'pelo',
    'pela', 'um', 'uma', 'uns', 'umas', 'a', 'o', 'as', 'os', 'que',
    'é', 'e', 'foi', 'quem', 'qual', 'quais', 'onde', 'quando', 'como',
    'por', 'para', 'tem', 'teve', 'usa', 'usam', 'ficam', 'fica',
})
# Weekdays are a closed answer *format*, not a purported source of knowledge.
_WEEKDAYS = frozenset({'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo'})
_COLORS = frozenset({'azul', 'vermelho', 'vermelha', 'verde', 'branco', 'branca',
                     'preto', 'preta', 'amarelo', 'amarela', 'roxo', 'roxa',
                     'cinza', 'laranja', 'marfim', 'rosa', 'dourado', 'prateado'})


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    sufficient: bool
    reason: str
    requested_attribute: str = ''


def _surface_matches(word: str, source_words: set[str]) -> bool:
    return word in source_words or bool(_inflections(word) & source_words)


def assess_explicit_answer(question: str, subject: str, excerpt: str,
                           document_name: str = '') -> EvidenceAssessment:
    """Confirm query focus + its requested relation are present *literally*.

    This checks a necessary condition for extractive use, not sufficient logical
    entailment. It fails closed on ambiguous attribute names or absent focus.
    The parent retriever still handles topic match, conflict and provenance.
    """
    # Do not use the retriever's STOP list here: terms such as 'atualizado'
    # may be irrelevant for ranking but are crucial to matching a predicate.
    source = set(_WORD.findall(_fold(excerpt)))
    if not source:
        return EvidenceAssessment(False, 'empty_excerpt')
    # A name in the imported file's title identifies the topic, never the
    # *attribute* being asked for. 'senha' in an unrelated filename must not
    # grant support because the source text itself has no password.
    # Entity planners may include the asked attribute in `subject` (e.g.
    # 'observadora do diario Aurora'); removing all those words would erase
    # the evidence question. Only the document title is a safe topic hint.
    topic = _tokens(document_name.replace('_', ' ').replace('.', ' '))
    words = [_fold(w) for w in _WORD.findall(question)]
    focus = []
    for word in words:
        if (len(word) < 3 or word in _QUESTION_STOP or word in topic or
                word in _STRUCTURE and word != 'arquivo'):
            continue
        focus.append(word)
    if not focus:
        return EvidenceAssessment(False, 'question_has_no_testable_attribute')
    head = focus[0]
    # A question asking for a NAME can be explicitly answered by "se chama",
    # or by the word 'nome'. A question asking for a DAY can be explicitly
    # answered by a weekday. Neither shortcut establishes external truth.
    if head == 'nome':
        present = ('nome' in source or 'chama' in source or 'chamado' in source)
    elif head == 'dia':
        present = 'dia' in source or bool(source & _WEEKDAYS)
    elif head == 'cor':
        present = 'cor' in source or bool(source & _COLORS)
    else:
        present = _surface_matches(head, source)
    if not present:
        return EvidenceAssessment(False, 'requested_attribute_absent', head)
    # Requiring a qualifying term (if supplied) blocks cases such as 'cor do
    # uniforme' being answered with the cor da etiqueta. Auxiliary verbs are
    # not enough to establish a relation, but their omission must not turn a
    # grounded source into a refusal. This is deliberately conservative.
    qualifiers = [w for w in focus[1:] if w not in {
        'responde', 'contem', 'possui', 'existe', 'existem', 'ocorre',
        'acontece', 'acontecem', 'atualmente', 'original',
    }]
    if qualifiers and not any(_surface_matches(word, source) for word in qualifiers):
        return EvidenceAssessment(False, 'requested_qualifier_absent', head)
    return EvidenceAssessment(True, 'explicit_attribute_matched', head)


def is_explicit_fact_question(question: str) -> bool:
    """Small grammatical gate for objective, source-seeking questions.

    Only used by the offline chat fallback, *after* local retrieval. Opinions,
    advice, open-ended conversation and personal recollection keep their own
    paths. It is not a universal fact/question classifier.
    """
    words = [_fold(w) for w in _WORD.findall(question[:500])]
    if '?' not in question or not words:
        return False
    while words and words[0] in {'morgana', 'todd', 'campanario', 'ei', 'ola', 'e'}:
        words.pop(0)
    if not words:
        return False
    if set(words) & {'opiniao', 'opinioes', 'acha', 'acham', 'pensa',
                     'pensam', 'gosta', 'gostaria', 'prefere', 'preferem',
                     'melhor', 'recomenda', 'sugere', 'devo', 'podemos'}:
        return False
    return (words[0] in {'qual', 'quais', 'quem', 'quando', 'onde',
                         'quantos', 'quantas', 'quanta', 'quanto'}
            or words[:2] == ['em', 'qual']
            or words[:3] == ['a', 'que', 'horas'])
