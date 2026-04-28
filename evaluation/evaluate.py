"""
evaluation/evaluate.py
─────────────────────
Evaluation layer for SysWatch anomaly detection and advisor modules.

Usage:
    python evaluation/evaluate.py

This script does NOT modify any existing project files.
It imports existing functions and measures their performance.
"""

import json
import time
import sys
import os

# ── Add project root to path so we can import existing modules ──
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from advisor import get_advice


# ═══════════════════════════════════════════════════════════════
# HELPERS — build inputs that match existing function signatures
# ═══════════════════════════════════════════════════════════════

def build_current_state(case):
    """Convert a test case dict into the current_state format advisor expects."""
    cpu  = case['cpu']
    ram  = case['ram_percent']
    disk = case['disk_percent']

    return {
        'cpu' : 'CRITICAL' if cpu  > 90 else 'WARNING' if cpu  > 75 else 'OK',
        'ram' : 'CRITICAL' if ram  > 90 else 'WARNING' if ram  > 80 else 'OK',
        'disk': 'CRITICAL' if disk > 90 else 'WARNING' if disk > 75 else 'OK',
    }


def build_process_list(case):
    """Wrap the test case's top_process into a list the advisor expects."""
    return [case['top_process']]


def detect_anomaly(current_state):
    """
    Rule-based anomaly detection — mirrors the logic in snapshot.py.
    Returns 1 if any metric is WARNING or CRITICAL, else 0.
    Does NOT import snapshot.py to avoid triggering psutil calls.
    """
    for value in current_state.values():
        if value in ('WARNING', 'CRITICAL'):
            return 1
    return 0


# ═══════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════

def compute_classification_metrics(results):
    """
    Compute Precision, Recall, F1 from binary anomaly predictions.

    TP = predicted anomaly AND actual anomaly
    FP = predicted anomaly BUT no actual anomaly
    FN = no prediction BUT actual anomaly was there
    TN = correctly predicted no anomaly
    """
    tp = fp = fn = tn = 0

    for r in results:
        predicted = r['predicted_anomaly']
        actual    = r['expected_anomaly']

        if predicted == 1 and actual == 1:
            tp += 1
        elif predicted == 1 and actual == 0:
            fp += 1
        elif predicted == 0 and actual == 1:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': round(precision, 4),
        'recall'   : round(recall,    4),
        'f1_score' : round(f1,        4),
        'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn
    }


def compute_latency(latencies):
    """Compute average and max latency in milliseconds."""
    if not latencies:
        return {'avg_ms': 0, 'max_ms': 0, 'min_ms': 0}
    return {
        'avg_ms': round(sum(latencies) / len(latencies), 3),
        'max_ms': round(max(latencies), 3),
        'min_ms': round(min(latencies), 3),
    }


def compute_relevance_score(advice_list, expected_keywords):
    """
    Simple keyword-based relevance scoring.

    For each expected keyword, check if it appears in any advice message.
    Score = matched keywords / total expected keywords.
    Returns a score between 0.0 and 1.0.
    """
    if not expected_keywords or not advice_list:
        return 0.0

    # Flatten all advice text into one lowercase string
    all_advice_text = ' '.join([
        item.get('msg', '').lower() if isinstance(item, dict) else str(item).lower()
        for item in advice_list
    ])

    matched = sum(
        1 for keyword in expected_keywords
        if keyword.lower() in all_advice_text
    )

    return round(matched / len(expected_keywords), 4)


# ═══════════════════════════════════════════════════════════════
# MAIN EVALUATION RUNNER
# ═══════════════════════════════════════════════════════════════

def run_evaluation(test_cases_path='evaluation/test_cases.json'):
    print("\n" + "═" * 60)
    print("  SYSWATCH — EVALUATION REPORT")
    print("═" * 60)

    # Load test cases
    with open(test_cases_path, 'r') as f:
        test_cases = json.load(f)

    print(f"\n  Loaded {len(test_cases)} test cases\n")

    results      = []
    latencies    = []
    rel_scores   = []

    # ── Run each test case ──────────────────────────────────────
    for case in test_cases:
        current_state = build_current_state(case)
        process_list  = build_process_list(case)

        # Measure latency — time taken to run detection + advisor
        start = time.perf_counter()
        predicted_anomaly = detect_anomaly(current_state)
        advice            = get_advice(current_state, process_list)
        elapsed_ms        = (time.perf_counter() - start) * 1000

        latencies.append(elapsed_ms)

        # Relevance score for this case
        rel_score = compute_relevance_score(advice, case['expected_keywords'])
        rel_scores.append(rel_score)

        results.append({
            'id'               : case['id'],
            'description'      : case['description'],
            'predicted_anomaly': predicted_anomaly,
            'expected_anomaly' : case['expected_anomaly'],
            'latency_ms'       : round(elapsed_ms, 3),
            'relevance_score'  : rel_score,
            'advice_count'     : len(advice),
        })

    # ── Per-case breakdown ──────────────────────────────────────
    print("  PER-CASE RESULTS")
    print("  " + "-" * 56)
    header = f"  {'ID':<4} {'Description':<32} {'Pred':>4} {'Exp':>4} {'Rel':>6} {'ms':>7}"
    print(header)
    print("  " + "-" * 56)

    for r in results:
        match = "✓" if r['predicted_anomaly'] == r['expected_anomaly'] else "✗"
        print(
            f"  {r['id']:<4} {r['description'][:31]:<32} "
            f"{r['predicted_anomaly']:>4} {r['expected_anomaly']:>4} "
            f"{r['relevance_score']:>6.2f} {r['latency_ms']:>6.1f}ms  {match}"
        )

    # ── Aggregate metrics ───────────────────────────────────────
    clf    = compute_classification_metrics(results)
    lat    = compute_latency(latencies)
    avg_rel = round(sum(rel_scores) / len(rel_scores), 4) if rel_scores else 0.0

    print("\n" + "═" * 60)
    print("  ANOMALY DETECTION METRICS")
    print("  " + "-" * 56)
    print(f"  Precision  : {clf['precision']:.4f}  ({clf['tp']} TP  {clf['fp']} FP)")
    print(f"  Recall     : {clf['recall']:.4f}  ({clf['fn']} FN  {clf['tn']} TN)")
    print(f"  F1 Score   : {clf['f1_score']:.4f}")

    print("\n  LATENCY")
    print("  " + "-" * 56)
    print(f"  Average    : {lat['avg_ms']:.3f} ms")
    print(f"  Min        : {lat['min_ms']:.3f} ms")
    print(f"  Max        : {lat['max_ms']:.3f} ms")

    print("\n  ADVISOR QUALITY")
    print("  " + "-" * 56)
    print(f"  Avg Relevance Score : {avg_rel:.4f}  (keyword match rate)")
    print(f"  Scoring method      : keyword overlap with expected terms")

    # ── Verdict ─────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  VERDICT")
    print("  " + "-" * 56)

    f1  = clf['f1_score']
    rel = avg_rel

    if f1 >= 0.85 and rel >= 0.5:
        verdict = "EXCELLENT — detection and advice are accurate"
        symbol  = "✓✓"
    elif f1 >= 0.70 and rel >= 0.35:
        verdict = "GOOD — minor gaps in detection or advice quality"
        symbol  = "✓"
    elif f1 >= 0.50:
        verdict = "FAIR — detection works but advice needs improvement"
        symbol  = "~"
    else:
        verdict = "NEEDS WORK — review thresholds and advice keywords"
        symbol  = "✗"

    print(f"  {symbol}  {verdict}")
    print("═" * 60 + "\n")

    return {
        'classification': clf,
        'latency'       : lat,
        'avg_relevance' : avg_rel,
        'per_case'      : results
    }


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Support running from project root or from evaluation/ folder
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    test_cases_path = os.path.join(script_dir, 'test_cases.json')

    run_evaluation(test_cases_path)