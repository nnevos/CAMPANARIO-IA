"""Regressoes do diagnostico isolado: nao mede embeddinggemma real."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from diagnostico_fase4_inc3b import run


def test_fixture_evidences_and_negatives_are_reported():
    report = run('fixture', 'embeddinggemma', timeout=30, threshold=0.72)
    assert report['positive_expected_top_accepted'] == 5
    assert report['positive_total'] == 5
    assert report['negatives_with_accepted_candidate'] == 0
    assert report['indexed_segments'] >= 12
    assert all(r['expected_similarity'] == 1.0 for r in report['positive'])


def test_high_threshold_does_not_pretend_to_measure_real_model():
    report = run('fixture', 'embeddinggemma', timeout=30, threshold=0.99)
    assert report['engine'] == 'fixture'
    assert report['source'] == 'APENAS corpus sintetico eval/v1/fixtures'
    assert all(r['cause_if_no_candidate'] == 'candidate_exists' for r in report['positive'])
