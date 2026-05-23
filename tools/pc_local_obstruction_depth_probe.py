#!/usr/bin/env python3
"""Measure local-to-global cR obstruction depth on selected families."""

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
    five_local_non_cr_core,
    four_local_non_cr_core,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.local_obstructions import local_obstruction_profile  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "equal",
    "random",
    "paired_farthest",
    "four_local_non_cr",
    "padded_four_local_non_cr",
    "five_local_non_cr",
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
    return n >= 1


def _repeat_count(kind: str, repeats: int) -> int:
    return repeats if kind in {"random", "paired_farthest"} else 1


def _instance(kind: str, n: int, *, seed: int):
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "four_local_non_cr":
        return four_local_non_cr_core()
    if kind == "padded_four_local_non_cr":
        return padded_four_local_non_cr(n)
    if kind == "five_local_non_cr":
        return five_local_non_cr_core()
    if kind == "padded_five_local_non_cr":
        return padded_five_local_non_cr(n)
    raise ValueError(f"unsupported instance kind: {kind}")


def _row(
    *,
    n: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    max_subset_size: int,
    max_global_n: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    profile = local_obstruction_profile(
        D, max_subset_size=max_subset_size, max_global_n=max_global_n
    )
    profile.update(
        {
            "instance_kind": instance_kind,
            "repeat": repeat,
            "seed": seed,
            "seconds": time.perf_counter() - start,
        }
    )
    return profile


def run_local_obstruction_depth_probe(
    *,
    sizes: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 5,
    seed: int = 20260640,
    max_subset_size: int = 6,
    max_global_n: int = 8,
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
                        max_subset_size=max_subset_size,
                        max_global_n=max_global_n,
                    )
                )

    negative_rows = [row for row in rows if row["global_exists"] is False]
    high_depth_rows = [
        row
        for row in negative_rows
        if row["min_negative_subset_size"] is not None
        and row["min_negative_subset_size"] >= 5
    ]
    cap_invisible_negative_rows = [
        row
        for row in negative_rows
        if row["global_reason"] == "exact_global_oracle"
        and row["min_negative_subset_size"] is None
    ]
    summary = {
        "rows": len(rows),
        "skipped_rows": len(skipped),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "negative_rows": len(negative_rows),
        "high_depth_negative_rows": len(high_depth_rows),
        "cap_invisible_negative_rows": len(cap_invisible_negative_rows),
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
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "first_high_depth_examples": high_depth_rows[:5],
        "interpretation": (
            "A negative row with min_negative_subset_size=k proves that all "
            "smaller induced subsets are cR-positive while the full instance "
            "is negative by hereditary restriction. This is a local-to-global "
            "obstruction diagnostic, not a solver integration."
        ),
    }
    return {
        "method": "local_obstruction_depth_probe",
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[5, 6, 7, 8, 9])
    parser.add_argument(
        "--instance-kinds", type=_parse_strings, default=list(DEFAULT_INSTANCE_KINDS)
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260640)
    parser.add_argument("--max-subset-size", type=int, default=6)
    parser.add_argument("--max-global-n", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_local_obstruction_depth_probe(
        sizes=args.sizes,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        max_subset_size=args.max_subset_size,
        max_global_n=args.max_global_n,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
