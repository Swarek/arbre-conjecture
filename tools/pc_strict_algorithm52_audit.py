#!/usr/bin/env python3
"""Bounded audit of strict Algorithm 5.2 candidates against exact orders."""

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
    permuted_cycle_metric,
    random_dissimilarity,
)
from pc_circular.pc_tree import (  # noqa: E402
    enumerate_frontiers,
    labels,
    pc_tree_from_kind,
)
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    canonical_circular_order,
    is_strict_circular_robinson_order,
    is_strict_precircular_order_cR,
    is_strict_quasi_circular_order,
)
from pc_circular.solvers.strict_experiments import strict_algorithm52_report  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "fig22",
    "strict_t024",
    "cycle",
    "permuted_cycle",
    "random",
    "equal",
)
DEFAULT_PC_TREES = ("none", "star", "balanced", "mixed")


def _parse_ints(raw: str) -> list[int]:
    values = [int(part) for part in raw.split(",") if part]
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


def _fig22_matrix() -> list[list[int]]:
    return [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]


def _strict_t024_matrix() -> list[list[int]]:
    return [
        [0, 3, 1, 3, 1],
        [3, 0, 2, 2, 3],
        [1, 2, 0, 3, 3],
        [3, 2, 3, 0, 1],
        [1, 3, 3, 1, 0],
    ]


def _is_applicable(instance_kind: str, n: int) -> bool:
    if instance_kind == "fig22":
        return n == 4
    if instance_kind == "strict_t024":
        return n == 5
    return n >= 1


def _repeat_count(instance_kind: str, repeats: int) -> int:
    return repeats if instance_kind in {"permuted_cycle", "random"} else 1


def _instance(kind: str, n: int, *, seed: int):
    if kind == "fig22":
        return _fig22_matrix()
    if kind == "strict_t024":
        return _strict_t024_matrix()
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "permuted_cycle":
        return permuted_cycle_metric(n, rng=random.Random(seed))
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    if kind == "equal":
        return equal_distance_instance(n)
    raise ValueError(f"unsupported instance kind: {kind}")


def _pc_tree(kind: str, n: int):
    if kind == "none":
        return None
    return pc_tree_from_kind(kind, n)


def _exact_orders(D, T, *, frontier_limit: int | None) -> tuple[bool, list[tuple[int, ...]], list[str]]:
    n = len(D)
    incomplete_reasons: list[str] = []
    if T is None:
        orders = list(all_circular_orders(n))
        return True, orders, incomplete_reasons

    if set(labels(T)) != set(range(n)):
        raise ValueError("pc_tree labels must be exactly 0..n-1")

    probe_limit = frontier_limit + 1 if frontier_limit is not None else None
    orders = enumerate_frontiers(T, canonical=True, limit=probe_limit)
    if frontier_limit is not None and len(orders) > frontier_limit:
        orders = orders[:frontier_limit]
        incomplete_reasons.append("frontier_limit reached")
    return not incomplete_reasons, orders, incomplete_reasons


def _strict_sets(D, orders: Sequence[Sequence[int]]) -> dict[str, set[tuple[int, ...]]]:
    exact = {
        "strict_quasi": set(),
        "strict_precircular": set(),
        "strict_circular": set(),
    }
    for order in orders:
        canonical = canonical_circular_order(order)
        if is_strict_quasi_circular_order(D, canonical):
            exact["strict_quasi"].add(canonical)
        if is_strict_precircular_order_cR(D, canonical):
            exact["strict_precircular"].add(canonical)
        if is_strict_circular_robinson_order(D, canonical):
            exact["strict_circular"].add(canonical)
    return exact


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    max_candidates: int,
    frontier_limit: int | None,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, n)
    exact_complete, orders, incomplete_reasons = _exact_orders(
        D, T, frontier_limit=frontier_limit
    )
    exact = _strict_sets(D, orders)
    algorithm = strict_algorithm52_report(D, T, max_candidates=max_candidates)
    algorithm_sets = {
        "strict_quasi": set(algorithm["strict_quasi_orders"]),
        "strict_precircular": set(algorithm["strict_precircular_orders"]),
        "strict_circular": set(algorithm["strict_circular_orders"]),
    }

    comparisons = {}
    mismatch_total = 0
    for key in ("strict_quasi", "strict_precircular", "strict_circular"):
        missing = sorted(exact[key] - algorithm_sets[key])
        excess = sorted(algorithm_sets[key] - exact[key])
        mismatch_total += len(missing) + len(excess)
        comparisons[key] = {
            "exact_count": len(exact[key]),
            "algorithm_count": len(algorithm_sets[key]),
            "missing_count": len(missing),
            "excess_count": len(excess),
            "missing_examples": missing[:3],
            "excess_examples": excess[:3],
        }

    if not algorithm["complete"]:
        incomplete_reasons.append("algorithm_candidate_limit_hit")
    complete = exact_complete and algorithm["complete"]
    return {
        "n": n,
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": complete,
        "incomplete_reasons": incomplete_reasons,
        "order_count": len(orders),
        "algorithm_candidate_count": algorithm["candidate_count"],
        "represented_candidate_count": algorithm["represented_candidate_count"],
        "algorithm_complete": algorithm["complete"],
        "mismatch_total": mismatch_total,
        "comparisons": comparisons,
        "matrix_if_mismatch": D if mismatch_total else None,
        "interpretation": (
            "Bounded exact audit of strict Algorithm 5.2 candidates. "
            "A clean row is experimental evidence only, not a proof of "
            "general completeness."
        ),
    }


def run_strict_algorithm52_audit(
    *,
    sizes: Sequence[int],
    pc_trees: Sequence[str] = DEFAULT_PC_TREES,
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 10,
    seed: int = 20260600,
    max_candidates: int = 20_000,
    frontier_limit: int | None = None,
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
                            frontier_limit=frontier_limit,
                        )
                    )

    mismatch_rows = [row for row in rows if row["mismatch_total"]]
    summary = {
        "rows": len(rows),
        "sizes": list(sizes),
        "pc_trees": list(pc_trees),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_permuted_cycle": repeats,
        "skipped_rows": len(skipped),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "incomplete_rows": sum(1 for row in rows if not row["complete"]),
        "mismatch_rows": len(mismatch_rows),
        "mismatch_total": sum(row["mismatch_total"] for row in rows),
        "strict_quasi_missing_total": sum(
            row["comparisons"]["strict_quasi"]["missing_count"] for row in rows
        ),
        "strict_precircular_missing_total": sum(
            row["comparisons"]["strict_precircular"]["missing_count"] for row in rows
        ),
        "strict_circular_missing_total": sum(
            row["comparisons"]["strict_circular"]["missing_count"] for row in rows
        ),
        "strict_circular_exact_positive_rows": sum(
            1 for row in rows if row["comparisons"]["strict_circular"]["exact_count"]
        ),
        "algorithm_limit_hit_rows": sum(
            1 for row in rows if not row["algorithm_complete"]
        ),
        "order_count_histogram": _histogram([row["order_count"] for row in rows]),
        "candidate_count_histogram": _histogram(
            [row["algorithm_candidate_count"] for row in rows]
        ),
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "interpretation": (
            "No mismatch means Algorithm 5.2 candidates matched exact strict "
            "orders on this bounded sweep only. It does not close the proof "
            "obligations for arbitrary PC-trees or non-strict instances."
        ),
    }
    return {
        "method": "strict_algorithm52_exact_audit",
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
        "mismatch_examples": mismatch_rows[:5],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=_parse_ints, default=[4, 5, 6, 7])
    parser.add_argument("--pc-trees", type=_parse_strings, default=list(DEFAULT_PC_TREES))
    parser.add_argument(
        "--instance-kinds",
        type=_parse_strings,
        default=list(DEFAULT_INSTANCE_KINDS),
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260600)
    parser.add_argument("--max-candidates", type=int, default=20_000)
    parser.add_argument("--frontier-limit", type=int, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    report = run_strict_algorithm52_audit(
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        seed=args.seed,
        max_candidates=args.max_candidates,
        frontier_limit=args.frontier_limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["mismatch_rows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
