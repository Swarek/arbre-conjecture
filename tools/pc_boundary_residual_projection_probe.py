#!/usr/bin/env python3
"""T090 probe: boundary residual relations after hiding internal branches.

T088/T089 measured the exact relation on all internal branch choices of a
fixed-focus P-node.  A composed-patch DP would often eliminate some internal
choices and keep only a boundary relation.  This probe projects the exact
accepted relation onto boundary subsets and asks whether the projected relation
is still determined by unary/binary projections.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from itertools import combinations, product
from math import prod
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.predicates import passes_bad_side_precircular_cR  # noqa: E402
from pc_circular.solvers.interface_experiments import (  # noqa: E402
    _closure_from_projection_arity,
    _compose_context_order,
    _unique_linear_frontiers,
)
from tools.pc_residual_interface_probe import two_level_high_pair_matrix  # noqa: E402
from tools.pc_residual_interface_stress_probe import branch_size_focus  # noqa: E402


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _all_pairs(n: int) -> tuple[tuple[int, int], ...]:
    return tuple((left, right) for left in range(n) for right in range(left + 1, n))


def _random_matrix(n: int, rng: random.Random, values: tuple[int, ...]) -> list[list[int]]:
    D = [[0 for _ in range(n)] for _ in range(n)]
    for left in range(n):
        for right in range(left + 1, n):
            value = rng.choice(values)
            D[left][right] = D[right][left] = value
    return D


def _accepted_relation(D, branch_sizes: tuple[int, ...]) -> tuple[set[tuple[int, ...]], tuple[int, ...]]:
    focus, used_labels = branch_size_focus(branch_sizes)
    branch_options = tuple(_unique_linear_frontiers(child) for child in focus.children)
    option_counts = tuple(len(options) for options in branch_options)
    domains = tuple(range(count) for count in option_counts)
    branch_order = tuple(range(len(branch_sizes)))

    accepted: set[tuple[int, ...]] = set()
    for option_tuple in product(*domains):
        order = _compose_context_order(
            branch_options,
            branch_order,
            option_tuple,
            (used_labels,),
            (used_labels + 1,),
        )
        if passes_bad_side_precircular_cR(D, order):
            accepted.add(tuple(option_tuple))
    return accepted, option_counts


def _project_relation(relation: set[tuple[int, ...]], boundary: tuple[int, ...]) -> set[tuple[int, ...]]:
    return {tuple(item[index] for index in boundary) for item in relation}


def _minimal_projection_arity(
    relation: set[tuple[int, ...]],
    option_counts: tuple[int, ...],
    *,
    max_candidates: int,
) -> tuple[int | None, dict[int, dict]]:
    if not option_counts:
        return 0, {}
    if not relation:
        return 0, {}

    domains = tuple(range(count) for count in option_counts)
    closure_by_arity = {}
    for arity in range(1, len(option_counts) + 1):
        closure, truncated = _closure_from_projection_arity(
            relation,
            domains,
            arity,
            max_candidates=max_candidates,
        )
        closure_by_arity[arity] = {
            "truncated": truncated,
            "closure_tuple_count": None if closure is None else len(closure),
            "exact": closure == relation if closure is not None else False,
            "false_tuple_count": None if closure is None else len(closure - relation),
        }
        if closure == relation:
            return arity, closure_by_arity
    return None, closure_by_arity


def boundary_projection_rows(
    *,
    case: str,
    D,
    branch_sizes: tuple[int, ...],
    high_pairs=(),
    min_boundary_size: int = 3,
    max_candidates: int = 1_000_000,
    max_examples: int = 5,
) -> dict:
    if min_boundary_size < 1:
        raise ValueError("min_boundary_size must be positive")

    accepted, option_counts = _accepted_relation(D, branch_sizes)
    full_product_count = prod(option_counts)
    full_min_arity, full_closure = _minimal_projection_arity(
        accepted,
        option_counts,
        max_candidates=max_candidates,
    )

    boundary_rows = []
    arity_histogram: dict[int, int] = {}
    nontrivial_boundary_projection_count = 0
    max_boundary_minimal_arity = 0
    first_beyond_binary = None
    best_non_unary = None

    degree = len(option_counts)
    for boundary_size in range(min_boundary_size, degree):
        for boundary in combinations(range(degree), boundary_size):
            projected = _project_relation(accepted, boundary)
            boundary_counts = tuple(option_counts[index] for index in boundary)
            boundary_product_count = prod(boundary_counts)
            if len(projected) in (0, boundary_product_count):
                continue
            nontrivial_boundary_projection_count += 1
            minimal_arity, closure_by_arity = _minimal_projection_arity(
                projected,
                boundary_counts,
                max_candidates=max_candidates,
            )
            arity_key = minimal_arity or 0
            arity_histogram[arity_key] = arity_histogram.get(arity_key, 0) + 1
            max_boundary_minimal_arity = max(max_boundary_minimal_arity, arity_key)
            row = {
                "boundary": boundary,
                "hidden": tuple(index for index in range(degree) if index not in boundary),
                "boundary_option_counts": boundary_counts,
                "boundary_product_count": boundary_product_count,
                "projected_tuple_count": len(projected),
                "projected_tuples": tuple(sorted(projected))[:max_examples],
                "minimal_projection_arity": minimal_arity,
                "closure_by_arity": closure_by_arity,
            }
            if minimal_arity and minimal_arity > 1:
                if (
                    best_non_unary is None
                    or minimal_arity > (best_non_unary["minimal_projection_arity"] or 0)
                    or (
                        minimal_arity == (best_non_unary["minimal_projection_arity"] or 0)
                        and len(projected) < best_non_unary["projected_tuple_count"]
                    )
                ):
                    best_non_unary = row
            if minimal_arity and minimal_arity > 2 and first_beyond_binary is None:
                first_beyond_binary = row
            boundary_rows.append(row)

    return {
        "case": case,
        "branch_sizes": branch_sizes,
        "n": sum(branch_sizes) + 2,
        "high_pairs": tuple(tuple(pair) for pair in high_pairs),
        "option_counts": option_counts,
        "full_product_count": full_product_count,
        "accepted_tuple_count": len(accepted),
        "accepted_density": None if full_product_count == 0 else len(accepted) / full_product_count,
        "full_minimal_projection_arity": full_min_arity,
        "full_closure_by_arity": full_closure,
        "nontrivial_boundary_projection_count": nontrivial_boundary_projection_count,
        "boundary_minimal_arity_histogram": arity_histogram,
        "max_boundary_minimal_arity": max_boundary_minimal_arity,
        "found_beyond_binary": first_beyond_binary is not None,
        "first_beyond_binary": first_beyond_binary,
        "best_non_unary": best_non_unary,
        "boundary_rows": tuple(boundary_rows[:max_examples]),
        "interpretation": (
            "exact accepted relation projected to boundary variables after "
            "hiding at least one branch; diagnostic only"
        ),
    }


def _scan_sparse_two_level(
    *,
    case: str,
    branch_sizes: tuple[int, ...],
    max_high_pairs: int,
    max_cases: int,
    min_boundary_size: int,
    max_examples: int,
) -> dict:
    if max_high_pairs < 0:
        raise ValueError("max_high_pairs must be non-negative")
    if max_cases <= 0:
        raise ValueError("max_cases must be positive")

    n = sum(branch_sizes) + 2
    all_pairs = _all_pairs(n)
    searched = 0
    complete = True
    relation_kind_counts = {"empty": 0, "full": 0, "nontrivial": 0}
    boundary_arity_histogram: dict[int, int] = {}
    first_beyond_binary = None
    best_non_unary = None
    max_boundary_minimal_arity = 0

    for high_pair_count in range(1, max_high_pairs + 1):
        for high_pairs in combinations(all_pairs, high_pair_count):
            if searched >= max_cases:
                complete = False
                break
            searched += 1
            D = two_level_high_pair_matrix(n, high_pairs)
            row = boundary_projection_rows(
                case=f"{case}_high_{high_pair_count}",
                D=D,
                branch_sizes=branch_sizes,
                high_pairs=high_pairs,
                min_boundary_size=min_boundary_size,
                max_examples=max_examples,
            )
            accepted = row["accepted_tuple_count"]
            product_count = row["full_product_count"]
            if accepted == 0:
                relation_kind_counts["empty"] += 1
            elif accepted == product_count:
                relation_kind_counts["full"] += 1
            else:
                relation_kind_counts["nontrivial"] += 1

            for arity, count in row["boundary_minimal_arity_histogram"].items():
                boundary_arity_histogram[arity] = boundary_arity_histogram.get(arity, 0) + count
            max_boundary_minimal_arity = max(
                max_boundary_minimal_arity,
                row["max_boundary_minimal_arity"],
            )
            if row["best_non_unary"] is not None:
                candidate = {
                    "row": row,
                    "searched_case_index": searched,
                }
                if (
                    best_non_unary is None
                    or row["max_boundary_minimal_arity"]
                    > best_non_unary["row"]["max_boundary_minimal_arity"]
                ):
                    best_non_unary = candidate
            if row["found_beyond_binary"]:
                first_beyond_binary = {
                    "row": row,
                    "searched_case_index": searched,
                }
                complete = True
                break
        if first_beyond_binary is not None or not complete:
            break

    return {
        "case": case,
        "branch_sizes": branch_sizes,
        "max_high_pairs": max_high_pairs,
        "max_cases": max_cases,
        "complete": complete,
        "cases_searched": searched,
        "relation_kind_counts": relation_kind_counts,
        "boundary_minimal_arity_histogram": boundary_arity_histogram,
        "max_boundary_minimal_arity": max_boundary_minimal_arity,
        "found_beyond_binary": first_beyond_binary is not None,
        "first_beyond_binary": first_beyond_binary,
        "best_non_unary": best_non_unary,
    }


def _scan_random_multilevel(
    *,
    case: str,
    branch_sizes: tuple[int, ...],
    trials: int,
    seed: int,
    values: tuple[int, ...],
    min_boundary_size: int,
    max_examples: int,
) -> dict:
    rng = random.Random(seed)
    nontrivial_boundary_projection_count = 0
    boundary_arity_histogram: dict[int, int] = {}
    first_beyond_binary = None
    best_non_unary = None

    for trial in range(trials):
        D = _random_matrix(sum(branch_sizes) + 2, rng, values)
        row = boundary_projection_rows(
            case=f"{case}_trial_{trial}",
            D=D,
            branch_sizes=branch_sizes,
            min_boundary_size=min_boundary_size,
            max_examples=max_examples,
        )
        nontrivial_boundary_projection_count += row["nontrivial_boundary_projection_count"]
        for arity, count in row["boundary_minimal_arity_histogram"].items():
            boundary_arity_histogram[arity] = boundary_arity_histogram.get(arity, 0) + count
        if row["best_non_unary"] is not None and best_non_unary is None:
            best_non_unary = {"row": row, "trial": trial}
        if row["found_beyond_binary"]:
            first_beyond_binary = {"row": row, "trial": trial}
            break

    return {
        "case": case,
        "branch_sizes": branch_sizes,
        "trials_requested": trials,
        "trials_completed": trials if first_beyond_binary is None else first_beyond_binary["trial"] + 1,
        "seed": seed,
        "values": values,
        "nontrivial_boundary_projection_count": nontrivial_boundary_projection_count,
        "boundary_minimal_arity_histogram": boundary_arity_histogram,
        "found_beyond_binary": first_beyond_binary is not None,
        "first_beyond_binary": first_beyond_binary,
        "best_non_unary": best_non_unary,
    }


def run_boundary_residual_projection_probe(
    *,
    p2x4_max_high_pairs: int = 4,
    p2x4_max_cases: int = 20000,
    p2x5_max_high_pairs: int = 3,
    p2x5_max_cases: int = 20000,
    random_trials: int = 500,
    seed: int = 20260600,
    min_boundary_size: int = 3,
    max_examples: int = 4,
) -> dict:
    start = time.perf_counter()
    controls = [
        boundary_projection_rows(
            case="p2x4_binary_projection_seed",
            D=two_level_high_pair_matrix(10, ((0, 2), (1, 3))),
            branch_sizes=(2, 2, 2, 2),
            high_pairs=((0, 2), (1, 3)),
            min_boundary_size=min_boundary_size,
            max_examples=max_examples,
        ),
    ]
    sparse_scans = [
        _scan_sparse_two_level(
            case="p2x4_sparse_projection",
            branch_sizes=(2, 2, 2, 2),
            max_high_pairs=p2x4_max_high_pairs,
            max_cases=p2x4_max_cases,
            min_boundary_size=min_boundary_size,
            max_examples=max_examples,
        ),
        _scan_sparse_two_level(
            case="p2x5_sparse_projection",
            branch_sizes=(2, 2, 2, 2, 2),
            max_high_pairs=p2x5_max_high_pairs,
            max_cases=p2x5_max_cases,
            min_boundary_size=min_boundary_size,
            max_examples=max_examples,
        ),
    ]
    random_scans = [
        _scan_random_multilevel(
            case="p2x4_random_multilevel_projection",
            branch_sizes=(2, 2, 2, 2),
            trials=random_trials,
            seed=seed,
            values=(1, 2, 3, 4),
            min_boundary_size=min_boundary_size,
            max_examples=max_examples,
        )
    ]
    found_beyond_binary = (
        any(row["found_beyond_binary"] for row in controls)
        or any(scan["found_beyond_binary"] for scan in sparse_scans)
        or any(scan["found_beyond_binary"] for scan in random_scans)
    )
    max_boundary_minimal_arity = max(
        [row["max_boundary_minimal_arity"] for row in controls]
        + [scan["max_boundary_minimal_arity"] for scan in sparse_scans],
        default=0,
    )
    summary = {
        "controls": len(controls),
        "sparse_scans": len(sparse_scans),
        "random_scans": len(random_scans),
        "found_beyond_binary": found_beyond_binary,
        "max_boundary_minimal_arity": max_boundary_minimal_arity,
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "bounded boundary-residual projection probe; absence of arity>2 "
            "after hiding branches is experimental evidence only"
        ),
    }
    return {
        "method": "t090_boundary_residual_projection_probe",
        "parameters": {
            "p2x4_max_high_pairs": p2x4_max_high_pairs,
            "p2x4_max_cases": p2x4_max_cases,
            "p2x5_max_high_pairs": p2x5_max_high_pairs,
            "p2x5_max_cases": p2x5_max_cases,
            "random_trials": random_trials,
            "seed": seed,
            "min_boundary_size": min_boundary_size,
            "max_examples": max_examples,
        },
        "summary": summary,
        "controls": controls,
        "sparse_scans": sparse_scans,
        "random_scans": random_scans,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p2x4-max-high-pairs", type=int, default=4)
    parser.add_argument("--p2x4-max-cases", type=int, default=20000)
    parser.add_argument("--p2x5-max-high-pairs", type=int, default=3)
    parser.add_argument("--p2x5-max-cases", type=int, default=20000)
    parser.add_argument("--random-trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260600)
    parser.add_argument("--min-boundary-size", type=int, default=3)
    parser.add_argument("--max-examples", type=int, default=4)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_boundary_residual_projection_probe(
        p2x4_max_high_pairs=args.p2x4_max_high_pairs,
        p2x4_max_cases=args.p2x4_max_cases,
        p2x5_max_high_pairs=args.p2x5_max_high_pairs,
        p2x5_max_cases=args.p2x5_max_cases,
        random_trials=args.random_trials,
        seed=args.seed,
        min_boundary_size=args.min_boundary_size,
        max_examples=args.max_examples,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "method": report["method"],
                "output": str(output),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
