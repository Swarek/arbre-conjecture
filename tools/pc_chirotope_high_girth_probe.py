#!/usr/bin/env python3
"""Search for local-to-global cR obstructions with same-side chirotopes."""

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

from pc_circular.cyclic_order_sat import (  # noqa: E402
    local_chirotope_obstruction_profile,
    solve_bad_side_chirotope,
)
from pc_circular.generators import (  # noqa: E402
    cycle_metric,
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    five_local_non_cr_core,
    four_local_non_cr_core,
    odd_high_cycle_plus_low_hub,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.oracle import exact_oracle_all_orders  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "equal",
    "random",
    "random4",
    "paired_farthest",
    "even_high_cycle_low_hub",
    "odd_high_cycle_low_hub",
    "padded_four_local_non_cr",
    "padded_five_local_non_cr",
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


def _is_applicable(kind: str, n: int) -> bool:
    if kind == "four_local_non_cr":
        return n == 5
    if kind == "five_local_non_cr":
        return n == 6
    if kind == "padded_four_local_non_cr":
        return n >= 5
    if kind == "padded_five_local_non_cr":
        return n >= 6
    if kind == "even_high_cycle_low_hub":
        return n >= 7 and (n - 1) % 2 == 0
    if kind == "odd_high_cycle_low_hub":
        return n >= 6 and (n - 1) % 2 == 1
    return n >= 1


def _repeat_count(kind: str, repeats: int) -> int:
    return repeats if kind in {"random", "random4", "paired_farthest"} else 1


def _instance(kind: str, n: int, *, seed: int):
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    if kind == "random4":
        return random_dissimilarity(n, values=(1, 2, 3, 4), rng=random.Random(seed))
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "even_high_cycle_low_hub":
        return even_high_cycle_plus_low_hub(n)
    if kind == "odd_high_cycle_low_hub":
        return odd_high_cycle_plus_low_hub(n)
    if kind == "four_local_non_cr":
        return four_local_non_cr_core()
    if kind == "five_local_non_cr":
        return five_local_non_cr_core()
    if kind == "padded_four_local_non_cr":
        return padded_four_local_non_cr(n)
    if kind == "padded_five_local_non_cr":
        return padded_five_local_non_cr(n)
    raise ValueError(f"unsupported instance kind: {kind}")


def _row(
    *,
    n: int,
    kind: str,
    repeat: int,
    seed: int,
    max_subset_size: int,
    max_global_n: int,
    max_orders: int | None,
    oracle_crosscheck_n: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(kind, n, seed=seed)
    profile = local_chirotope_obstruction_profile(
        D,
        max_subset_size=max_subset_size,
        max_global_n=max_global_n,
        max_orders=max_orders,
    )
    global_result = solve_bad_side_chirotope(D, max_orders=max_orders)
    profile.update(
        {
            "instance_kind": kind,
            "repeat": repeat,
            "seed": seed,
            "seconds": time.perf_counter() - start,
            "global_chirotope_exists": global_result["exists"],
            "global_chirotope_complete": global_result["complete"],
            "global_chirotope_reason": global_result["reason"],
            "global_chirotope_checked_orders": global_result["checked_orders"],
        }
    )
    if n <= oracle_crosscheck_n:
        oracle = exact_oracle_all_orders(D)
        profile["oracle_exists"] = oracle["exists"]
        profile["oracle_mismatch"] = (
            global_result["complete"] and global_result["exists"] != oracle["exists"]
        )
    else:
        profile["oracle_exists"] = None
        profile["oracle_mismatch"] = False
    profile["high_girth_candidate"] = (
        profile["global_chirotope_exists"] is False
        and profile["min_negative_subset_size"] is None
        and profile["all_subsets_positive_up_to"] >= max_subset_size
    )
    return profile


def run_chirotope_high_girth_probe(
    *,
    sizes: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 10,
    seed: int = 20260650,
    max_subset_size: int = 6,
    max_global_n: int = 9,
    max_orders: int | None = 250000,
    oracle_crosscheck_n: int = 8,
) -> dict:
    rows = []
    skipped = []
    for n in sizes:
        for kind_index, kind in enumerate(instance_kinds):
            if not _is_applicable(kind, n):
                skipped.append({"n": n, "instance_kind": kind, "reason": "not_applicable"})
                continue
            for repeat in range(_repeat_count(kind, repeats)):
                row_seed = seed + 1009 * n + 9176 * kind_index + repeat
                rows.append(
                    _row(
                        n=n,
                        kind=kind,
                        repeat=repeat,
                        seed=row_seed,
                        max_subset_size=max_subset_size,
                        max_global_n=max_global_n,
                        max_orders=max_orders,
                        oracle_crosscheck_n=oracle_crosscheck_n,
                    )
                )

    candidates = [row for row in rows if row["high_girth_candidate"]]
    summary = {
        "rows": len(rows),
        "skipped_rows": len(skipped),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "oracle_mismatches": sum(1 for row in rows if row["oracle_mismatch"]),
        "negative_rows": sum(1 for row in rows if row["global_chirotope_exists"] is False),
        "high_girth_candidates": len(candidates),
        "max_all_subsets_positive_up_to": max(
            (row["all_subsets_positive_up_to"] for row in rows), default=0
        ),
        "max_min_negative_subset_size": max(
            (
                row["min_negative_subset_size"]
                for row in rows
                if row["min_negative_subset_size"] is not None
            ),
            default=None,
        ),
        "max_constraint_count": max((row["constraint_count"] for row in rows), default=0),
        "max_checked_orders": max(
            (row["global_chirotope_checked_orders"] for row in rows), default=0
        ),
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "first_high_girth_candidates": candidates[:5],
        "interpretation": (
            "The chirotope solver is exact only when complete is true.  A "
            "high_girth_candidate is globally negative while all induced "
            "subsets up to the chosen cap were positive; it is a red-team "
            "target, not a candidate.py rule."
        ),
    }
    return {
        "method": "chirotope_high_girth_probe",
        "parameters": {
            "sizes": list(sizes),
            "instance_kinds": list(instance_kinds),
            "repeats": repeats,
            "seed": seed,
            "max_subset_size": max_subset_size,
            "max_global_n": max_global_n,
            "max_orders": max_orders,
            "oracle_crosscheck_n": oracle_crosscheck_n,
        },
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[6, 7, 8, 9])
    parser.add_argument(
        "--instance-kinds", type=_parse_strings, default=list(DEFAULT_INSTANCE_KINDS)
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260650)
    parser.add_argument("--max-subset-size", type=int, default=6)
    parser.add_argument("--max-global-n", type=int, default=9)
    parser.add_argument("--max-orders", type=int, default=250000)
    parser.add_argument("--oracle-crosscheck-n", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_chirotope_high_girth_probe(
        sizes=args.sizes,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        max_subset_size=args.max_subset_size,
        max_global_n=args.max_global_n,
        max_orders=args.max_orders,
        oracle_crosscheck_n=args.oracle_crosscheck_n,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
