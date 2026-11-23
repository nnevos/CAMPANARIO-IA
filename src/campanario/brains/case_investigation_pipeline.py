"""R3.6: bounded multi-stage, source-first investigation inside Case Manager.

No autonomous file/network actions. A hypothesis is not a factual claim.
The result is a review *of the available records*, not a finding of guilt,
causation or external truth. All cited text is copied from hash-checked files.
"""
from __future__ import annotations

from campanario.brains.casework import CaseWorkspace
from campanario.brains.casework_sources import search_case_evidence, numeric_disagreements
from campanario.brains.case_reasoning import prioritize_checks, relation_matrix, hypothesis_matrix
from campanario.brains.case_claims import review_claims
from campanario.brains.case_semantic_review import review_semantic_relations


def investigate_case(workspace: CaseWorkspace, case_id: str, question: str) -> dict:
    """Return review steps and traceable citations; never modify case metadata."""
    doc = workspace.read(case_id)
    verified = workspace.verify(case_id)
    if not verified['integrity_ok']:
        return {'status': 'integrity_failed', 'steps': [], 'citations': [],
                'hypotheses': [], 'conflicts': [], 'next_checks': ['Comparar os originais e hashes'],
                'limitations': ['Integridade falhou; análise não realizada']}
    # R3.8: prioritize registered checks adaptively *after* observing whether
    # the original question has citations. No model-generated questions.
    queries = [question]
    selected_checks = []
    citations = []
    primary_support = False
    seen = set()
    rounds = []
    unsupported = []
    semantic_notes = []
    total_searched = 0
    round_no = 0
    while queries and round_no < 3:
        query = queries.pop(0)
        round_no += 1
        matches = search_case_evidence(workspace, case_id, query)
        if not matches['integrity_ok']:
            return {'status': 'integrity_failed', 'steps': [], 'citations': [],
                    'hypotheses': [], 'conflicts': [], 'rounds': [],
                    'next_checks': ['Rever integridade'],
                    'limitations': ['Integridade mudou durante a leitura']}
        total_searched = max(total_searched, matches['searched'])
        unsupported.extend(matches['unsupported'])
        if matches.get('semantic_note'):
            semantic_notes.append(matches['semantic_note'])
        added = 0
        for item in matches['snippets']:
            key = (item['evidence_id'], item['line'], item['sha256'])
            if key in seen:
                continue
            seen.add(key)
            citations.append({'evidence_id': item['evidence_id'], 'filename': item['filename'],
                              'line': item['line'], 'quote': item['quote'], 'sha256': item['sha256']})
            added += 1
            if len(citations) >= 16:
                break
        if round_no == 1:
            primary_support = bool(matches['snippets'])
        rounds.append({'round': round_no, 'question': query, 'new_citations': added,
                       'status': 'retrieved' if added else 'no_new_evidence'})
        if round_no == 1:
            selected_checks = prioritize_checks(question, doc['hypotheses'], primary_supported=primary_support)
            queries.extend(x['question'] for x in selected_checks[:2])
        if len(citations) >= 16:
            break
    stop_reason = ('citation_limit' if len(citations) >= 16 else
                   'no_more_registered_checks' if round_no < 3 else 'round_limit')
    # Integrity is checked once more after the multi-round retrieval.
    if not workspace.verify(case_id)['integrity_ok']:
        return {'status': 'integrity_failed', 'steps': [], 'citations': [],
                'hypotheses': [], 'conflicts': [], 'rounds': [],
                'next_checks': ['Rever integridade'],
                'limitations': ['Integridade mudou após a leitura']}
    # Each hypothesis remains in the operator's original words. Reference counts
    # are coverage metrics, never probabilities or a truth score.
    known = {e['id'] for e in doc['evidence']}
    hypotheses = []
    for hypothesis in doc['hypotheses'][:16]:
        supporting = [e for e in hypothesis['supporting'] if e in known]
        opposing = [e for e in hypothesis['opposing'] if e in known]
        hypotheses.append({'statement': hypothesis['statement'],
                           'supporting': supporting, 'opposing': opposing,
                           'support_count': len(supporting), 'opposing_count': len(opposing),
                           'next_check': hypothesis['next_check'], 'status': 'unverified'})
    conflicts = numeric_disagreements(workspace, case_id)
    claim_review = review_claims(citations)
    semantic_review = review_semantic_relations(citations)
    relations = relation_matrix(doc, citations)
    hypothesis_review = hypothesis_matrix(doc, citations)
    from campanario.brains.casework_vision import local_visual_leads
    visual = local_visual_leads(workspace, case_id)
    steps = [
        {'stage': 'integrity', 'result': 'hashes atuais conferidos; origem externa não autenticada'},
        {'stage': 'retrieval', 'result': f"{len(citations)} trecho(s) rastreável(is) de {total_searched} arquivo(s) legível(is)"},
        {'stage': 'chronology', 'result': f"{len(doc['events'])} evento(s) declarados no cadastro; nenhuma causalidade inferida"},
        {'stage': 'comparison', 'result': f"{len(conflicts)} possível(is) divergência(s) numérica(s) estrita(s)"},
        {'stage': 'hypotheses', 'result': f"{len(hypotheses)} hipótese(s) cadastrada(s), sem escolha automática"},
    ]
    next_checks = [h['next_check'] for h in hypotheses if h['next_check']][:8]
    if conflicts:
        next_checks.insert(0, 'Verificar versão, contexto e origem independente dos números divergentes')
    if not primary_support:
        next_checks.insert(0, 'Fornecer ou identificar documento que trate diretamente da pergunta')
    if unsupported:
        next_checks.append('Examinar manualmente os formatos indisponíveis para extração')
    return {'status': 'reviewable' if primary_support else 'insufficient_evidence',
            'steps': steps, 'citations': citations, 'hypotheses': hypotheses,
            'conflicts': conflicts[:8], 'rounds': rounds, 'stop_reason': stop_reason,
            'relations': relations, 'hypothesis_review': hypothesis_review,
            'claim_review': claim_review, 'semantic_review': semantic_review,
            'verification_queue': selected_checks,
            'primary_question_supported': primary_support, 'visual_leads': visual['leads'],
            'visual_status': visual['status'], 'next_checks': next_checks[:10],
            'limitations': ['Pistas visuais, se disponíveis, são inferências não verificadas',
                            'Dados importados podem estar errados; hash não verifica autenticidade',
                            'Hipóteses não provam culpa, intenção nem nexo causal',
                            'Vínculos lexicais ou cadastrados não provam relações causais',
                            'Leitura de proposições por padrões não prova implicação ou verdade semântica',
                            'Relações semânticas de modelo são apenas pistas não verificadas',
                            'Investigação limitada aos materiais acessíveis e às verificações determinísticas',
                            *[u['evidence_id'] + ': ' + u['reason'] for u in unsupported[:8]],
                            *list(dict.fromkeys(semantic_notes))[:2]]}
