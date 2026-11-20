#!/usr/bin/env python3
"""Compara os registros da Fase 3 sem chamar LLM, rede ou bancos de dados.

Exemplo:
 python tools/comparar_baselines_fase3.py reports/fase3/baseline_offline_ollama_ANTES_ETAPA3.json reports/fase3/baseline_offline_ollama_qwen3.5_9b.json --output reports/fase3/comparacao_antes_depois.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median


def by_id(items, label):
    indexed = {case["id"]: case for case in items}
    if len(indexed) != len(items):
        raise ValueError(f"IDs repetidos na secao {label}")
    return indexed


def compare(before, after):
    keys = ["dataset_hash_sha256", "dataset_version", "model", "mode"]
    mismatch = {k: [before.get(k), after.get(k)] for k in keys if before.get(k) != after.get(k)}
    if mismatch:
        raise ValueError(f"Bases nao comparaveis: {mismatch}")
    delta = {"comparison_schema": "1.0.0", "provenance": {
        "dataset_version": after["dataset_version"],
        "dataset_sha256": after["dataset_hash_sha256"],
        "model": after["model"],
        "mode": after["mode"],
        "before_timestamp_utc": before["timestamp_utc"],
        "after_timestamp_utc": after["timestamp_utc"],
        "before_internet_opt_in": before.get("internet_opt_in"),
        "after_internet_opt_in": after.get("internet_opt_in"),
    }}
    be, af = before["execution"], after["execution"]
    changes = {}
    for section in ["factual", "documents", "group"]:
        bs, as_ = by_id(be[section], section), by_id(af[section], section)
        if set(bs) != set(as_):
            raise ValueError(f"IDs distintos em {section}: {sorted(set(bs)^set(as_))}")
        rows = []
        for id_ in sorted(bs):
            prev, post = bs[id_], as_[id_]
            row = {"id": id_, "status_before": prev.get("status"), "status_after": post.get("status"),
                   "first_visible_ms_before": prev.get("first_visible_ms"),
                   "first_visible_ms_after": post.get("first_visible_ms"),
                   "speakers_before": prev.get("speakers"), "speakers_after": post.get("speakers")}
            if section == "factual":
                row.update({"abstention_before": prev["abstention_detected"],
                            "abstention_after": post["abstention_detected"],
                            "response_changed": prev.get("response_sha256") != post.get("response_sha256"),
                            "grounded_before": prev.get("claim_grounding_verified"),
                            "grounded_after": post.get("claim_grounding_verified")})
            elif section == "documents":
                row.update({"response_changed": prev.get("response_sha256") != post.get("response_sha256"),
                            "citation_verified_before": prev.get("document_citation_verified"),
                            "citation_verified_after": post.get("document_citation_verified"),
                            "exact_quote_before": prev.get("expected_quote_exact"),
                            "exact_quote_after": post.get("expected_quote_exact")})
            else:
                row.update({"perspective_distinction_before": prev.get("perspective_distinction"),
                            "perspective_distinction_after": post.get("perspective_distinction"),
                            "factual_consistency_before": prev.get("factual_consistency"),
                            "factual_consistency_after": post.get("factual_consistency")})
            rows.append(row)
        changes[section] = rows
    oldf, newf = be['factual'], af['factual']
    oldd, newd = be['documents'], af['documents']
    summary = {
        "cases_per_run": be.get('case_count'),
        "factual_cases": len(oldf),
        "factual_abstentions_before": sum(x['abstention_detected'] for x in oldf),
        "factual_abstentions_after": sum(x['abstention_detected'] for x in newf),
        "new_abstentions": [r['id'] for r in changes['factual'] if not r['abstention_before'] and r['abstention_after']],
        "changed_factual_responses": [r['id'] for r in changes['factual'] if r['response_changed']],
        "factual_non_abstentions_after": [r['id'] for r in changes['factual'] if not r['abstention_after']],
        "factual_grounded_after": sum(bool(x['claim_grounding_verified']) for x in newf),
        "document_cases": len(oldd),
        "unchanged_document_responses": sum(not r['response_changed'] for r in changes['documents']),
        "document_citations_verified_before": sum(bool(x['document_citation_verified']) for x in oldd),
        "document_citations_verified_after": sum(bool(x['document_citation_verified']) for x in newd),
        "group_cases": len(be['group']),
        "group_semantic_status": list(sorted(set(x['factual_consistency'] for x in af['group']))),
        "reported_p50_ms_before": be['summary'].get('first_visible_p50_ms'),
        "reported_p50_ms_after": af['summary'].get('first_visible_p50_ms'),
        "reported_p95_ms_before": be['summary'].get('first_visible_p95_ms'),
        "reported_p95_ms_after": af['summary'].get('first_visible_p95_ms'),
        "non_abstention_first_visible_median_after_ms": median(x['first_visible_ms'] for x in newf if not x['abstention_detected']),
        "factual_response_truth_not_scored": True,
        "vram_not_measured": True,
        "external_web_not_authorized": not before['internet_opt_in'] and not after['internet_opt_in']
    }
    delta['summary'] = summary
    delta['by_case'] = changes
    return delta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('before', type=Path)
    ap.add_argument('after', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    before = json.loads(args.before.read_text(encoding='utf-8'))
    after = json.loads(args.after.read_text(encoding='utf-8'))
    obj = compare(before, after)
    rendered = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
        print(f'Comparacao gravada em {args.output}')
    print(json.dumps(obj['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
