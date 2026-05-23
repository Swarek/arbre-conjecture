#!/usr/bin/env python3
"""Single-P-node domain stress benchmark.

The point of this report is deliberately narrow: a star PC-tree has one local
``P`` variable, so a naive CSP view has primal treewidth zero, but the local
domain already has ``(n-1)!/2`` circular orders.  This keeps that failure mode
visible while staying outside ``candidate.py``.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    cycle_metric,
    equal_distance_instance,
    four_local_non_cr_core,
    paired_farthest_matching,
    random_dissimilarity,
    single_bad_side_quartet_instance,
)
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    passes_bad_side_precircular_cR,
    validate_dissimilarity,
)


def circular_order_count(n: int) -> int:
    if n <= 2:
        return 1
    return math.factorial(n - 1) // 2


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _instance(kind: str, n: int, *, seed: int) -> list[list[int]] | None:
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "single_quartet":
        return single_bad_side_quartet_instance() if n == 4 else None
    if kind == "four_local_non_cr":
        return four_local_non_cr_core() if n == 5 else None
    raise ValueError(f"unsupported single-P stress instance kind: {kind}")


def _bad_side_stats(D) -> dict:
    n = validate_dissimilarity(D)
    pair_count_histogram: dict[int, int] = {}
    nontrivial_pairs = 0
    unordered_constraints = 0
    max_bad_witness_count = 0
    first_nontrivial_pair = None
    for a in range(n):
        for c in range(a + 1, n):
            bad = [
                u
                for u in range(n)
                if u != a and u != c and max(D[a][u], D[u][c]) > D[a][c]
            ]
            count = len(bad)
            pair_count_histogram[count] = pair_count_histogram.get(count, 0) + 1
            max_bad_witness_count = max(max_bad_witness_count, count)
            if count >= 2:
                nontrivial_pairs += 1
                unordered_constraints += math.comb(count, 2)
                if first_nontrivial_pair is None:
                    first_nontrivial_pair = {
                        "pair": [a, c],
                        "bad_witnesses": bad,
                        "unordered_constraints": math.comb(count, 2),
                    }
    return {
        "pair_count_histogram": {
            str(key): pair_count_histogram[key] for key in sorted(pair_count_histogram)
        },
        "nontrivial_bad_side_pairs": nontrivial_pairs,
        "unordered_bad_side_constraints": unordered_constraints,
        "oriented_bad_side_atoms": 2 * unordered_constraints,
        "max_bad_witness_count": max_bad_witness_count,
        "first_nontrivial_pair": first_nontrivial_pair,
    }


def _count_cr_orders(D, *, frontier_limit: int) -> dict:
    n = validate_dissimilarity(D)
    domain_size = circular_order_count(n)
    complete = domain_size <= frontier_limit
    inspected = 0
    accepted = 0
    first_witness = None
    start = time.perf_counter()
    for order in all_circular_orders(n):
        if inspected >= frontier_limit:
            complete = False
            break
        inspected += 1
        if passes_bad_side_precircular_cR(D, order):
            accepted += 1
            if first_witness is None:
                first_witness = list(order)
    seconds = time.perf_counter() - start
    ratio_denominator = domain_size if complete else inspected
    ratio = accepted / ratio_denominator if ratio_denominator else 0.0
    return {
        "complete": complete,
        "inspected_orders": inspected,
        "cr_order_count": accepted,
        "cr_order_ratio": ratio,
        "first_witness": first_witness,
        "seconds": seconds,
    }


def run_single_p_domain_stress(
    *,
    sizes: Sequence[int],
    instance_kinds: Sequence[str],
    seed: int = 20260523,
    frontier_limit: int = 25000,
) -> dict:
    rows = []
    skipped = []
    for n in sizes:
        if n <= 0:
            raise ValueError("sizes must be positive")
        domain_size = circular_order_count(n)
        for kind_index, instance_kind in enumerate(instance_kinds):
            D = _instance(instance_kind, n, seed=seed + 1009 * n + 9176 * kind_index)
            if D is None:
                skipped.append({"n": n, "instance_kind": instance_kind})
                continue
            counts = _count_cr_orders(D, frontier_limit=frontier_limit)
            bad_side = _bad_side_stats(D)
            rows.append(
                {
                    "n": n,
                    "instance_kind": instance_kind,
                    "domain_model": "one_P_node_circular_orders",
                    "domain_size": domain_size,
                    "unary_primal_active_variable_count": 1 if n >= 3 else 0,
                    "unary_primal_treewidth": 0,
                    "frontier_limit": frontier_limit,
                    "exact_count_complete": counts["complete"],
                    "inspected_orders": counts["inspected_orders"],
                    "cr_order_count": counts["cr_order_count"],
                    "cr_order_ratio": counts["cr_order_ratio"],
                    "first_witness": counts["first_witness"],
                    "count_seconds": counts["seconds"],
                    "bad_side": bad_side,
                }
            )

    summary = {
        "rows": len(rows),
        "skipped_rows": len(skipped),
        "sizes": list(sizes),
        "instance_kinds": list(instance_kinds),
        "frontier_limit": frontier_limit,
        "treewidth_zero_rows": sum(
            1 for row in rows if row["unary_primal_treewidth"] == 0
        ),
        "max_domain_size": max((row["domain_size"] for row in rows), default=0),
        "max_complete_domain_size": max(
            (
                row["domain_size"]
                for row in rows
                if row["exact_count_complete"]
            ),
            default=0,
        ),
        "incomplete_exact_count_rows": sum(
            1 for row in rows if not row["exact_count_complete"]
        ),
        "max_unordered_bad_side_constraints": max(
            (
                row["bad_side"]["unordered_bad_side_constraints"]
                for row in rows
            ),
            default=0,
        ),
        "zero_cr_rows": sum(
            1
            for row in rows
            if row["exact_count_complete"] and row["cr_order_count"] == 0
        ),
        "all_cr_rows": sum(
            1
            for row in rows
            if row["exact_count_complete"]
            and row["cr_order_count"] == row["domain_size"]
        ),
        "warning": (
            "Treewidth zero is not an algorithmic guarantee when the single "
            "P-node domain has factorial size."
        ),
    }
    return {
        "method": "single_p_node_domain_stress",
        "rows": rows,
        "skipped": skipped,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7,8,9,10")
    parser.add_argument(
        "--instance-kinds",
        default="equal,cycle,random,paired_farthest,single_quartet,four_local_non_cr",
    )
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--frontier-limit", type=int, default=25000)
    parser.add_argument("--output", default="reports/single_p_domain_stress.json")
    args = parser.parse_args(argv)

    report = run_single_p_domain_stress(
        sizes=_parse_ints(args.sizes),
        instance_kinds=_parse_strings(args.instance_kinds),
        seed=args.seed,
        frontier_limit=args.frontier_limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
