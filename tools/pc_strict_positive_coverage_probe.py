#!/usr/bin/env python3
"""Measure positive-only coverage of strict Algorithm 5.2 candidates."""

from __future__ import annotations

import argparse
import json
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

from pc_circular.pc_tree import pc_tree_from_kind, represents_order  # noqa: E402
from pc_circular.predicates import (  # noqa: E402
    is_strict_circular_robinson_order,
    passes_bad_side_precircular_cR,
)
from pc_circular.solvers import candidate  # noqa: E402
from pc_circular.solvers.strict_experiments import strict_algorithm52_report  # noqa: E402
from tools.pc_strict_algorithm52_audit import (  # noqa: E402
    DEFAULT_INSTANCE_KINDS,
    _instance,
    _is_applicable,
    _parse_ints,
    _parse_strings,
    _repeat_count,
)


DEFAULT_PC_TREES = ("none", "star", "balanced", "mixed")


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _pc_tree(kind: str, n: int):
    if kind == "none":
        return None
    return pc_tree_from_kind(kind, n)


def _valid_strict_witnesses(D, T, orders: Sequence[Sequence[int]]) -> list[tuple[int, ...]]:
    witnesses = []
    for order in orders:
        seq = tuple(order)
        if not is_strict_circular_robinson_order(D, seq):
            continue
        if not passes_bad_side_precircular_cR(D, seq):
            continue
        if T is not None and not represents_order(T, seq):
            continue
        witnesses.append(seq)
    return witnesses


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    max_candidates: int,
) -> dict:
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, n)

    candidate_start = time.perf_counter()
    candidate_result = candidate.solve(D, pc_tree=T)
    candidate_seconds = time.perf_counter() - candidate_start

    strict_start = time.perf_counter()
    strict_report = strict_algorithm52_report(D, T, max_candidates=max_candidates)
    strict_seconds = time.perf_counter() - strict_start

    witnesses = _valid_strict_witnesses(D, T, strict_report["strict_circular_orders"])
    strict_positive = bool(witnesses)
    candidate_positive = candidate_result.get("exists") is True
    new_positive = strict_positive and not candidate_positive
    witness = witnesses[0] if witnesses else None
    return {
        "n": n,
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "candidate_seconds": candidate_seconds,
        "candidate_exists": candidate_result.get("exists"),
        "candidate_complete": candidate_result.get("complete"),
        "candidate_solver": candidate_result.get("solver"),
        "strict_seconds": strict_seconds,
        "strict_complete": strict_report["complete"],
        "strict_candidate_count": strict_report["candidate_count"],
        "strict_represented_candidate_count": strict_report["represented_candidate_count"],
        "strict_circular_count": strict_report["strict_circular_count"],
        "strict_valid_witness_count": len(witnesses),
        "strict_unrepresented_circular_count": strict_report[
            "unrepresented_strict_circular_count"
        ],
        "strict_positive": strict_positive,
        "strict_new_positive_over_candidate": new_positive,
        "strict_witness": witness,
        "strict_witness_represents_tree": (
            represents_order(T, witness) if T is not None and witness is not None else None
        ),
        "integration_status": (
            "positive_candidate"
            if new_positive
            else "already_found_by_candidate"
            if strict_positive
            else "no_strict_positive_witness"
        ),
        "interpretation": (
            "Positive-only strict coverage probe. Strict witnesses are "
            "revalidated by strict circular cR, bad-side cR and PC-tree "
            "membership when applicable. Missing witnesses or candidate-limit "
            "hits are never negative certificates."
        ),
    }


def run_strict_positive_coverage_probe(
    *,
    sizes: Sequence[int],
    pc_trees: Sequence[str] = DEFAULT_PC_TREES,
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 10,
    seed: int = 20260610,
    max_candidates: int = 20_000,
) -> dict:
    rows = []
    skipped = []
    for n in sizes:
        if n <= 0:
            raise ValueError("sizes must be positive")
        for pc_tree_kind in pc_trees:
            for kind_index, instance_kind in enumerate(instance_kinds):
                if not _is_applicable(instance_kind, n):
                    skipped.append(
                        {
                            "n": n,
                            "pc_tree_kind": pc_tree_kind,
                            "instance_kind": instance_kind,
                            "reason": "instance_not_defined_for_size",
                        }
                    )
                    continue
                for repeat in range(_repeat_count(instance_kind, repeats)):
                    row_seed = seed + 1009 * n + 9176 * kind_index + repeat
                    rows.append(
                        _row(
                            n=n,
                            pc_tree_kind=pc_tree_kind,
                            instance_kind=instance_kind,
                            repeat=repeat,
                            seed=row_seed,
                            max_candidates=max_candidates,
                        )
                    )

    new_positive_rows = [row for row in rows if row["strict_new_positive_over_candidate"]]
    strict_positive_rows = [row for row in rows if row["strict_positive"]]
    summary = {
        "rows": len(rows),
        "sizes": list(sizes),
        "pc_trees": list(pc_trees),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_permuted_cycle": repeats,
        "skipped_rows": len(skipped),
        "candidate_positive_rows": sum(1 for row in rows if row["candidate_exists"] is True),
        "candidate_incomplete_rows": sum(
            1 for row in rows if row["candidate_complete"] is not True
        ),
        "strict_positive_rows": len(strict_positive_rows),
        "strict_new_positive_rows": len(new_positive_rows),
        "strict_limit_hit_rows": sum(1 for row in rows if not row["strict_complete"]),
        "strict_unrepresented_circular_rows": sum(
            1 for row in rows if row["strict_unrepresented_circular_count"]
        ),
        "strict_witness_failure_rows": sum(
            1
            for row in rows
            if row["strict_circular_count"] != row["strict_valid_witness_count"]
        ),
        "max_strict_candidate_count": max(
            (row["strict_candidate_count"] for row in rows), default=0
        ),
        "max_candidate_seconds": max((row["candidate_seconds"] for row in rows), default=0.0),
        "max_strict_seconds": max((row["strict_seconds"] for row in rows), default=0.0),
        "candidate_solver_histogram": _histogram(
            [str(row["candidate_solver"]) for row in rows]
        ),
        "integration_status_histogram": _histogram(
            [row["integration_status"] for row in rows]
        ),
        "new_positive_examples": new_positive_rows[:5],
        "interpretation": (
            "This report only measures whether strict Algorithm 5.2 would add "
            "validated True witnesses over candidate.py. It never authorizes "
            "False decisions."
        ),
    }
    return {
        "method": "strict_algorithm52_positive_only_coverage",
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[5, 6, 8, 9, 10, 12, 16, 20])
    parser.add_argument("--pc-trees", type=_parse_strings, default=list(DEFAULT_PC_TREES))
    parser.add_argument(
        "--instance-kinds",
        type=_parse_strings,
        default=list(DEFAULT_INSTANCE_KINDS),
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--max-candidates", type=int, default=20_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    report = run_strict_positive_coverage_probe(
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        max_candidates=args.max_candidates,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output.resolve()), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
