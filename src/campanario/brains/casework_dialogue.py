"""R3.4: evidence-preserving, read-only conversational case briefing.

Factual answers remain literal ledger fields and hash-backed source quotations.
R3.10 may optionally send up to eight selected quotes to a loopback Ollama
classifier; only non-authoritative labels survive validation, never new facts.
Instructions embedded in evidence are untrusted and never executed.
"""
from __future__ import annotations

import re
from typing import Any

from campanario.brains.casework import CaseWorkspace


def _intent(question: str) -> str:
    folded = question.casefold()
    if re.search(r'hip[oó]tes|suspeit|teoria|alternativ', folded):
        return 'hypotheses'
    if re.search(r'cronolog|linha do tempo|hor[aá]ri|quando|sequ[eê]ncia|interval', folded):
        return 'timeline'
    if re.search(r'pr[oó]xim|plano|estrat[eé]g|como investig|verific|passo', folded):
        return 'strategy'
    if re.search(r'(?:afirm|nega[cç]|contradi[cç]|alega[cç]|proposi[cç]|o que .*diz)', folded):
        return 'contents'
    # R3.10: explicit investigation requests take precedence over generic
    # file-list words, e.g. 'investigue os documentos deste caso'.
    if re.search(r'investigue|investigar|analise|analisar|cruze|apure|compare|contradi[cç]', folded):
        return 'contents'
    if re.search(r'evid[eê]nci|document|fontes?|arquivo|integridade|hash', folded):
        return 'evidence'
    if re.search(r'conte[uú]do|trecho|diz|consta|cita|pesquis|compare|diverg|contradi|valor|quant|pagamento|contrato|relat[oó]rio|investigue|investigar|analise|analisar|cruze|procure|o que aconteceu', folded):
        return 'contents'
    return 'overview'


def _limit(value: Any, n: int = 220) -> str:
    # Ledger entries are untrusted records: render plain text, bounded per item.
    return ' '.join(str(value).split())[:n]


def prepare_case_answer(workspace: CaseWorkspace, case_id: str, question: str,
                        agent_id: str = 'morgana') -> dict:
    if not isinstance(question, str) or not question.strip() or len(question) > 600:
        raise ValueError('Pergunta obrigatória, até 600 caracteres')
    if agent_id not in ('morgana', 'todd'):
        raise ValueError('Agente inválido')
    doc = workspace.read(case_id)
    check = workspace.verify(case_id)
    intent = _intent(question)
    status = 'limited' if not check['integrity_ok'] else 'reported_only'
    intro = ('Vamos conferir os registros do caso.' if agent_id == 'morgana'
             else 'Vou separar registros, hipóteses e o que falta comprovar.')
    lines = [intro, f"Caso: {_limit(doc['title'], 180)}."]
    if not check['integrity_ok']:
        lines.append('ALERTA: a integridade de pelo menos uma evidência falhou. '
                     'Não vou fundamentar conclusões em registros potencialmente alterados.')
        lines.append('Próximo passo: verificar os arquivos originais e comparar os hashes no Cofre de Evidências.')
        return {'case_id': case_id, 'agent_id': agent_id, 'intent': intent, 'status': status,
                'answer': '\n'.join(lines), 'evidence_ids': [], 'source': 'casework_verified_ledger',
                'limitations': ['integrity_failed', 'no_llm_generated_facts']}
    known = {e['id']: e for e in doc['evidence']}
    selected: list[str] = []

    def ref(eid: str) -> str:
        if eid in known and eid not in selected:
            selected.append(eid)
        return '[' + _limit(eid, 22) + ']' if eid in known else '[fonte desconhecida]'

    if intent == 'contents':
        from campanario.brains.casework_sources import search_case_evidence
        findings = search_case_evidence(workspace, case_id, question)
        if not findings['integrity_ok']:
            lines.append('ALERTA: integridade alterada durante a leitura. Nenhuma citação foi utilizada.')
            return {'case_id': case_id, 'agent_id': agent_id, 'intent': intent, 'status': 'limited',
                    'answer': '\n'.join(lines), 'evidence_ids': [], 'source': 'casework_verified_ledger',
                    'limitations': ['integrity_failed', 'no_llm_generated_facts']}
        if findings['snippets']:
            lines.append('Trechos literais encontrados nos originais (não são conclusões):')
            for item in findings['snippets']:
                lines.append(f"{ref(item['evidence_id'])} {_limit(item['filename'], 100)} linha {item['line']}: “{_limit(item['quote'], 500)}”")
            lines.append('Esses trechos têm correspondência lexical com a pergunta; confira o contexto antes de concluir algo.')
        else:
            lines.append('Não encontrei trechos com correspondência textual nos arquivos examináveis para esta pergunta.')
        if findings['unsupported']:
            lines.append('Arquivos não examinados integralmente: ' + '; '.join(
                f"{_limit(x['evidence_id'], 24)} ({_limit(x['reason'], 100)})"
                for x in findings['unsupported'][:10]))
        lines.append(f"Arquivos com texto examinado: {findings['searched']}. Busca limitada; não representa revisão semântica completa.")
        if re.search(r'compare|diverg|contradi|conflit', question.casefold()):
            from campanario.brains.casework_sources import numeric_disagreements
            differences = numeric_disagreements(workspace, case_id)
            if differences:
                lines.append('Possíveis divergências numéricas entre arquivos (não determina a fonte correta):')
                for pair in differences:
                    for side in ('first', 'second'):
                        item = pair[side]
                        lines.append(f"{ref(item['evidence_id'])} linha {item['line']}: “{_limit(item['quote'], 350)}”")
            else:
                lines.append('Nenhuma divergência numérica no padrão estrito foi identificada; isso não exclui outros conflitos.')
    if intent == 'contents' and re.search(r'investigue|investigar|analise|analisar|cruze|apure|hip[oó]teses concorrentes|afirm|contradi[cç]|nega[cç]', question.casefold()):
        from campanario.brains.case_investigation_pipeline import investigate_case
        review = investigate_case(workspace, case_id, question)
        if review['status'] == 'integrity_failed':
            lines.append('Investigação multietapa bloqueada: integridade de evidência comprometida.')
            status = 'limited'
        else:
            lines.append('Revisão multietapa do caso (sem conclusão autônoma):')
            for stage in review['steps']:
                lines.append(f"{stage['stage']}: {stage['result']}")
            for round_item in review.get('rounds', [])[:3]:
                lines.append(f"Rodada {round_item['round']}: {_limit(round_item['question'], 160)}; "
                             f"{round_item['new_citations']} nova(s) citação(ões).")
            lines.append('Parada da revisão: ' + _limit(review.get('stop_reason', 'limite'), 100) + '.')
            for hypothesis in review['hypotheses'][:6]:
                lines.append(f"Hipótese NÃO CONFIRMADA: {_limit(hypothesis['statement'])}; "
                             f"{hypothesis['support_count']} referência(s) favorável(is), "
                             f"{hypothesis['opposing_count']} contrária(s). "
                             f"Próxima verificação: {_limit(hypothesis['next_check'])}.")
            for h in review.get('hypothesis_review', [])[:6]:
                lines.append(f"Revisão de hipótese [{_limit(h['hypothesis_id'], 24)}]: "
                             f"{h['review_state']}; referências recuperadas pró: "
                             f"{', '.join(h['retrieved_supporting']) or 'nenhuma'}; "
                             f"contra: {', '.join(h['retrieved_opposing']) or 'nenhuma'}. "
                             'Classificação cadastrada, NÃO é comprovação.')
            reading = review.get('claim_review', {})
            for claim in reading.get('claims', [])[:6]:
                lines.append(f"Leitura textual [{_limit(claim['evidence_id'], 24)}] linha {claim['line']}: "
                             f"{claim['reading']}; conteúdo da fonte, NÃO verdade verificada: "
                             f"\"{_limit(claim['quote'], 350)}\"")
            for opposition in reading.get('textual_oppositions', [])[:4]:
                left, right = opposition['first'], opposition['second']
                lines.append(f"Oposição textual explícita para revisão: "
                             f"[{_limit(left['evidence_id'], 24)}] linha {left['line']} versus "
                             f"[{_limit(right['evidence_id'], 24)}] linha {right['line']}; "
                             'não comprova qual fonte está correta.')
            semantic = review.get('semantic_review', {})
            for span in semantic.get('spans', [])[:5]:
                lines.append(f"Anotação semântica NÃO VERIFICADA ({span['role']}): "
                             f"[{_limit(span['evidence_id'], 24)}] linha {span['line']}: "
                             f"{_limit(span['quote'], 300)}. Rótulo provisório, não é fato comprovado.")
            for suggestion in semantic.get('suggestions', [])[:4]:
                left, right = suggestion['first'], suggestion['second']
                lines.append(f"Possível relação semântica NÃO VERIFICADA ({suggestion['kind']}): "
                             f"[{_limit(left['evidence_id'], 24)}] linha {left['line']} "
                             f"{_limit(left['quote'], 250)} versus "
                             f"[{_limit(right['evidence_id'], 24)}] linha {right['line']} "
                             f"{_limit(right['quote'], 250)}. "
                             'Interpretação provisória; não prova verdade, autoria ou causa.')
            for edge in review.get('relations', {}).get('cross_document_hints', [])[:4]:
                left, right = edge['first'], edge['second']
                lines.append(f"Relação lexical a revisar: [{_limit(left['evidence_id'], 24)}] "
                             f"linha {left['line']} e [{_limit(right['evidence_id'], 24)}] "
                             f"linha {right['line']} compartilham termos; não implica causa.")
            for task in review.get('verification_queue', [])[:2]:
                lines.append('Próxima checagem priorizada, não executada: ' + _limit(task['question'], 250))
            for lead in review.get('visual_leads', [])[:2]:
                lines.append(f"PISTA VISUAL AUTOMÁTICA NÃO VERIFICADA [{_limit(lead['evidence_id'], 24)}]: "
                             + _limit(lead['description'], 900))
                ref(lead['evidence_id'])
            for next_check in review['next_checks'][:6]:
                lines.append('Verificação sugerida (não executada): ' + _limit(next_check, 300))
            if review['status'] == 'insufficient_evidence':
                status = 'limited'
            lines.append('Limitações da revisão: ' + '; '.join(_limit(x, 180) for x in review['limitations'][:6]))

    if intent == 'contents' and re.search(r'investigue|investigar|analise|analisar|cruze', question.casefold()):
        # Reuse the already implemented, pure Investigation report builder over
        # verified case excerpts; do NOT start the library worker against a
        # different repository or grant any extra permissions.
        from campanario.brains.contracts import EvidenceRef
        from campanario.brains.investigation import structured_report
        from campanario.brains.casework_sources import search_case_evidence
        matches = search_case_evidence(workspace, case_id, question)
        if matches['integrity_ok'] and matches['snippets']:
            refs = tuple(EvidenceRef(source_id=e['evidence_id'], document_id=e['evidence_id'],
                                     title=e['filename'], excerpt=e['quote'])
                         for e in matches['snippets'])
            lines.extend(structured_report('investigation', refs))
    if intent in ('overview', 'evidence'):
        lines.append(f"O registro contém {len(doc['evidence'])} evidência(s), "
                     f"{len(doc['events'])} evento(s) declarado(s) e "
                     f"{len(doc['hypotheses'])} hipótese(s) ainda não confirmada(s).")
        for item in doc['evidence'][:12]:
            lines.append(f"{ref(item['id'])} {_limit(item['filename'], 140)}; "
                         f"origem declarada: {_limit(item['origin'], 150)}; "
                         f"SHA-256: {_limit(item['sha256'], 64)}.")
        if len(doc['evidence']) > 12:
            lines.append('Lista parcial; consulte o Cofre para as demais evidências.')
    if intent in ('overview', 'timeline'):
        for ev in sorted(doc['events'], key=lambda x: x['date_time'])[:20]:
            references = ', '.join(ref(eid) for eid in ev['evidence_ids'])
            lines.append(f"{_limit(ev['date_time'], 45)} — registro declarado: "
                         f"{_limit(ev['description'], 220)}. Fonte(s): {references}.")
        if not doc['events']:
            lines.append('Não há eventos cronológicos registrados neste caso.')
        elif len(doc['events']) > 20:
            lines.append('Cronologia parcial; consulte a Central de Casos para a lista completa.')
        if intent == 'timeline':
            review = workspace.review(case_id)
            for delta in review['intervals'][:12]:
                lines.append(f"Intervalo declarado {delta['before']} → {delta['after']}: "
                             f"{delta['elapsed_minutes']} minuto(s); isso não prova causalidade.")
    if intent in ('overview', 'hypotheses'):
        for h in doc['hypotheses'][:12]:
            support = ', '.join(ref(x) for x in h['supporting']) or 'nenhuma'
            opposing = ', '.join(ref(x) for x in h['opposing']) or 'nenhuma'
            lines.append(f"Hipótese NÃO VERIFICADA: {_limit(h['statement'])}. "
                         f"A favor: {support}; contra: {opposing}. "
                         f"Verificar: {_limit(h['next_check'])}.")
        if not doc['hypotheses']:
            lines.append('Não há hipóteses cadastradas.')
    if intent == 'strategy':
        from campanario.brains.casework_sources import search_case_evidence
        from campanario.brains.investigation import structured_report
        from campanario.brains.contracts import EvidenceRef
        matches = search_case_evidence(workspace, case_id, question)
        if matches['integrity_ok'] and matches['snippets']:
            refs = tuple(EvidenceRef(source_id=e['evidence_id'], document_id=e['evidence_id'],
                                     title=e['filename'], excerpt=e['quote']) for e in matches['snippets'])
            lines.extend(structured_report('strategy', refs))
            for item in matches['snippets']:
                ref(item['evidence_id'])
        lines.append('Plano condicional de leitura e verificação (nenhuma ação executada):')
        lines.append('1. Conferir origem, completude, fuso horário e autenticidade dos registros.')
        for h in doc['hypotheses'][:8]:
            refs = ', '.join(ref(x) for x in (h['supporting'] + h['opposing']))
            lines.append(f"Verificação para hipótese não confirmada {_limit(h['statement'], 110)}: "
                         f"{_limit(h['next_check'])}. Referências: {refs or 'a obter'}.")
        lines.append('2. Procurar evidência independente para cada afirmação e resolver divergências.')
        lines.append('Critério de parada: dados insuficientes, contradição ou falta de permissão.')
    lines.append('Limite: os registros são declarações e arquivos importados; a integridade '
                 'dos bytes não autentica sua origem, nem comprova ocorrência, intenção, autoria ou culpa.')
    return {'case_id': case_id, 'agent_id': agent_id, 'intent': intent, 'status': status,
            'answer': '\n'.join(lines), 'evidence_ids': selected,
            'source': 'casework_verified_ledger',
            'limitations': ['records_not_external_truth', 'no_llm_generated_facts', 'read_only']}
