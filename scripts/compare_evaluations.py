#!/usr/bin/env python3
"""Compare two evaluation reports side-by-side.

Usage:
    python scripts/compare_evaluations.py eval_reports/baseline.json eval_reports/after_rerank.json
"""

import json
import sys
from pathlib import Path


def load_report(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def compare(path_report_a: str, path_report_b: str):
    """Print a side-by-side comparison of two evaluation reports."""
    a = load_report(path_report_a)
    b = load_report(path_report_b)
    print(f"\n{'Metric':<25} {'Report A':<12} {'Report B':<12} {'Δ':<12}")
    print("-" * 65)

    all_metrics = set(a["scores"].keys()) | set(b["scores"].keys())

    for metric in sorted(all_metrics):
        score_a = a["scores"].get(metric, 0)
        score_b = b["scores"].get(metric, 0)
        delta = score_b - score_a
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        print(f"{metric:<25} {score_a:<12.4f} {score_b:<12.4f} {arrow} {delta:<+.4f}")

    print(f"\nReport A: {path_report_a}")
    print(f"  Timestamp: {a.get('timestamp', 'unknown')}")
    print(f"  Questions: {a.get('num_questions', '?')}")
    print(f"\nReport B: {path_report_b}")
    print(f"  Timestamp: {b.get('timestamp', 'unknown')}")
    print(f"  Questions: {b.get('num_questions', '?')}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_evaluations.py <report_a.json> <report_b.json>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
