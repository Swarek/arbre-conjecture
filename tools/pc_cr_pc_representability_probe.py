#!/usr/bin/env python3
"""Probe whether all cR orders of D are scaffold-PC representable."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
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
from pc_circular.pc_tree_learning import find_scaffold_pc_representation  # noqa: E402
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    passes_bad_side_precircular_cR,
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


def _instance(kind: str, n: int, *, seed: int):
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
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


def _row(
    *,
    n: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    max_families_per_subset: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    orders = list(all_circular_orders(n))
    cr_orders = [order for order in orders if passes_bad_side_precircular_cR(D, order)]
    report = find_scaffold_pc_representation(
        range(n), cr_orders, max_families_per_subset=max_families_per_subset
    )
    informative_counterexample = (
        report.complete
        and not report.representable
        and not report.empty_target
        and 0 < report.target_size < report.all_order_count
    )
    return {
        "n": n,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "circular_order_count": len(orders),
        "cr_order_count": len(cr_orders),
        "cr_orders": [list(order) for order in cr_orders],
        "representable": report.representable,
        "complete": report.complete,
        "witness": report.witness,
        "empty_target": report.empty_target,
        "all_order_count": report.all_order_count,
        "linear_family_count": report.linear_family_count,
        "canonical_family_count": report.canonical_family_count,
        "overflow_subsets": [list(values) for values in report.overflow_subsets],
        "subset_family_counts": report.subset_family_counts,
        "informative_counterexample": informative_counterexample,
        "D": D,
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "Scaffold-PC representability is checked only inside the rooted "
            "PCNode grammar of this repository. A complete negative row is a "
            "counterexample to this scaffold learner, not yet to full "
            "Hsu/McConnell PC-tree representability."
        ),
    }


def run_cr_pc_representability_probe(
    *,
    sizes: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 5,
    seed: int = 20260630,
    max_families_per_subset: int = 50_000,
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
                        max_families_per_subset=max_families_per_subset,
                    )
                )

    complete_rows = [row for row in rows if row["complete"]]
    counterexamples = [row for row in rows if row["informative_counterexample"]]
    summary = {
        "rows": len(rows),
        "complete_rows": len(complete_rows),
        "incomplete_rows": len(rows) - len(complete_rows),
        "representable_rows": sum(1 for row in rows if row["representable"]),
        "empty_target_rows": sum(1 for row in rows if row["empty_target"]),
        "informative_counterexample_rows": len(counterexamples),
        "sizes": list(sizes),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "max_families_per_subset": max_families_per_subset,
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "first_counterexamples": counterexamples[:3],
        "interpretation": (
            "This is a bounded exact search in the repository scaffold. "
            "Incomplete rows cannot support negative conclusions. Non-empty "
            "proper complete counterexamples should be minimized and then "
            "checked against a fuller PC-tree model before any theorem claim."
        ),
    }
    return {
        "method": "cr_orders_scaffold_pc_representability",
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[4, 5, 6])
    parser.add_argument(
        "--instance-kinds", type=_parse_strings, default=list(DEFAULT_INSTANCE_KINDS)
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--max-families-per-subset", type=int, default=50_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_cr_pc_representability_probe(
        sizes=args.sizes,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        max_families_per_subset=args.max_families_per_subset,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
