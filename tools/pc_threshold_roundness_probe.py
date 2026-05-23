#!/usr/bin/env python3
"""Probe the threshold clean-side reformulation of fixed-order cR."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    cycle_metric,
    equal_distance_instance,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    find_bad_side_precircular_cR_violation,
    find_threshold_clean_side_violation,
    is_precircular_order_cR,
    passes_bad_side_precircular_cR,
    passes_threshold_clean_side_condition,
    threshold_common_neighborhood,
)


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "random",
    "equal",
    "paired_farthest",
    "four_local_non_cr",
    "five_local_non_cr",
)


def _parse_ints(raw: str) -> list[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    return values


def _parse_strings(raw: str) -> list[str]:
    values = [part.strip() for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one value")
    return values


def _histogram(values: Sequence[int | str]) -> dict[str, int]:
    counts = Counter(str(value) for value in values)
    return {key: counts[key] for key in sorted(counts, key=str)}


def _instance(kind: str, n: int, *, seed: int):
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3, 4), rng=random.Random(seed))
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "four_local_non_cr":
        return padded_four_local_non_cr(n)
    if kind == "five_local_non_cr":
        return padded_five_local_non_cr(n)
    raise ValueError(f"unsupported instance kind: {kind}")


def _is_applicable(kind: str, n: int) -> bool:
    if kind == "four_local_non_cr":
        return n >= 5
    if kind == "five_local_non_cr":
        return n >= 6
    return n >= 1


def _repeat_count(kind: str, repeats: int) -> int:
    return repeats if kind in {"paired_farthest", "random"} else 1


def _active_pairs_by_level(D) -> dict[str, int]:
    n = len(D)
    counts: Counter[str] = Counter()
    for a in range(n):
        for b in range(a + 1, n):
            clean = threshold_common_neighborhood(D, a, b)
            bad_count = n - 2 - len(clean)
            if bad_count >= 2:
                counts[str(D[a][b])] += 1
    return {level: counts[level] for level in sorted(counts, key=str)}


def _row(
    *,
    n: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    order_limit: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    orders = list(all_circular_orders(n))
    truncated = len(orders) > order_limit
    checked_orders = orders[:order_limit]

    mismatch_examples = []
    threshold_positive = 0
    bad_side_positive = 0
    direct_positive = 0
    for order in checked_orders:
        threshold = passes_threshold_clean_side_condition(D, order)
        bad_side = passes_bad_side_precircular_cR(D, order)
        direct = is_precircular_order_cR(D, order)
        threshold_positive += int(threshold)
        bad_side_positive += int(bad_side)
        direct_positive += int(direct)
        if threshold != bad_side or threshold != direct:
            mismatch_examples.append(
                {
                    "order": list(order),
                    "threshold": threshold,
                    "bad_side": bad_side,
                    "direct": direct,
                    "threshold_violation": find_threshold_clean_side_violation(D, order),
                    "bad_side_violation": find_bad_side_precircular_cR_violation(D, order),
                }
            )

    return {
        "n": n,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "total_circular_orders": len(orders),
        "checked_orders": len(checked_orders),
        "order_limit": order_limit,
        "truncated": truncated,
        "threshold_positive_orders": threshold_positive,
        "bad_side_positive_orders": bad_side_positive,
        "direct_positive_orders": direct_positive,
        "mismatch_count": len(mismatch_examples),
        "mismatch_examples": mismatch_examples[:3],
        "distance_level_count": len(
            {D[i][j] for i in range(n) for j in range(i + 1, n)}
        ),
        "active_pairs_by_level": _active_pairs_by_level(D),
        "seconds": time.perf_counter() - start,
    }


def run_threshold_roundness_probe(
    *,
    sizes: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 5,
    seed: int = 20260620,
    order_limit: int = 5000,
) -> dict:
    rows = []
    skipped = []
    for n in sizes:
        if n <= 0:
            raise ValueError("sizes must be positive")
        for kind_index, kind in enumerate(instance_kinds):
            if not _is_applicable(kind, n):
                skipped.append({"n": n, "instance_kind": kind, "reason": "not_applicable"})
                continue
            for repeat in range(_repeat_count(kind, repeats)):
                row_seed = seed + 1009 * n + 9176 * kind_index + repeat
                rows.append(
                    _row(
                        n=n,
                        instance_kind=kind,
                        repeat=repeat,
                        seed=row_seed,
                        order_limit=order_limit,
                    )
                )

    summary = {
        "rows": len(rows),
        "sizes": list(sizes),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "checked_orders": sum(row["checked_orders"] for row in rows),
        "truncated_rows": sum(1 for row in rows if row["truncated"]),
        "mismatch_rows": sum(1 for row in rows if row["mismatch_count"]),
        "mismatch_count": sum(row["mismatch_count"] for row in rows),
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "distance_level_count_histogram": _histogram(
            [row["distance_level_count"] for row in rows]
        ),
        "interpretation": (
            "This probe compares the threshold clean-side predicate, the "
            "bad-side fixed-order predicate, and the direct cR quadruple "
            "predicate. It is a fixed-order equivalence check, not an "
            "existence solver for a PC-tree."
        ),
    }
    return {
        "method": "threshold_clean_side_fixed_order_probe",
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[4, 5, 6, 7])
    parser.add_argument(
        "--instance-kinds", type=_parse_strings, default=list(DEFAULT_INSTANCE_KINDS)
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260620)
    parser.add_argument("--order-limit", type=int, default=5000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_threshold_roundness_probe(
        sizes=args.sizes,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        order_limit=args.order_limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
