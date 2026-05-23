#!/usr/bin/env python3
"""Probe tiny unrooted PC-tree representability of selected cR-order sets."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import cycle_metric, equal_distance_instance  # noqa: E402
from pc_circular.predicates import all_circular_orders, passes_bad_side_precircular_cR  # noqa: E402
from pc_circular.unrooted_pc_tree import find_unrooted_pc_representation  # noqa: E402


T079_COUNTEREXAMPLE = [
    [0, 1, 2, 3, 1],
    [1, 0, 3, 2, 1],
    [2, 3, 0, 1, 1],
    [3, 2, 1, 0, 1],
    [1, 1, 1, 1, 0],
]


def _cr_orders(D):
    return [order for order in all_circular_orders(len(D)) if passes_bad_side_precircular_cR(D, order)]


def _row(name: str, D, *, max_candidates: int) -> dict:
    start = time.perf_counter()
    cr_orders = _cr_orders(D)
    report = find_unrooted_pc_representation(
        range(len(D)), cr_orders, max_candidates=max_candidates
    )
    return {
        "name": name,
        "n": len(D),
        "cr_order_count": len(cr_orders),
        "cr_orders": [list(order) for order in cr_orders],
        "representable": report.representable,
        "complete": report.complete,
        "witness": report.witness,
        "target_size": report.target_size,
        "candidate_count": report.candidate_count,
        "family_count": report.family_count,
        "max_candidates": report.max_candidates,
        "empty_target": report.empty_target,
        "D": D,
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "This row uses an explicit unrooted PC-tree brute-force model for "
            "tiny n. It is intended to audit scaffold counterexamples, not to "
            "scale as a solver."
        ),
    }


def run_unrooted_representability_probe(*, max_candidates: int = 500_000) -> dict:
    rows = [
        _row("cycle_n5", cycle_metric(5), max_candidates=max_candidates),
        _row("equal_n5", equal_distance_instance(5), max_candidates=max_candidates),
        _row("t079_paired_farthest_n5", T079_COUNTEREXAMPLE, max_candidates=max_candidates),
    ]
    t079 = next(row for row in rows if row["name"] == "t079_paired_farthest_n5")
    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "incomplete_rows": sum(1 for row in rows if not row["complete"]),
        "representable_rows": sum(1 for row in rows if row["representable"]),
        "t079_representable": t079["representable"],
        "t079_complete": t079["complete"],
        "t079_candidate_count": t079["candidate_count"],
        "t079_family_count": t079["family_count"],
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "interpretation": (
            "If t079_complete is true and t079_representable is false, the "
            "T079 counterexample survives this tiny unrooted PC-tree model."
        ),
    }
    return {
        "method": "tiny_unrooted_pc_representability",
        "summary": summary,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-candidates", type=int, default=500_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_unrooted_representability_probe(max_candidates=args.max_candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
