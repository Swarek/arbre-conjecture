#!/usr/bin/env python3
"""Internal benchmark for Piste C CSP/nogood experiments.

This tool is intentionally separate from the candidate benchmark.  It measures
the experimental CSP machinery without changing the public solver contract.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import instance_by_kind  # noqa: E402
from pc_circular.pc_tree import balanced_pc_tree  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    accepted_frontiers_by_csp,
    compile_bad_side_nogoods_grouped_first_hit_support_local,
    compile_bad_side_nogoods_grouped_support_local,
    compile_bad_side_nogoods_support_local,
    compile_cr_nogoods,
    solve_pruned_nogood_csp_from_compilation,
)


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _pc_tree(kind: str, n: int):
    if kind == "balanced":
        return balanced_pc_tree(n, kind="C")
    if kind == "mixed":
        return balanced_pc_tree(n, kind="mixed")
    raise ValueError(f"unsupported internal CSP pc-tree kind: {kind}")


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def _signature_set(compilation: dict) -> set[tuple]:
    return {
        tuple((path, tuple(choice)) for path, choice in nogood["signature"])
        for nogood in compilation["nogoods"]
    }


def run_benchmark(
    *,
    sizes: Sequence[int],
    repeats: int,
    instance_kinds: Sequence[str],
    pc_trees: Sequence[str],
    max_p_degree: int,
    seed: int,
    validate: bool,
) -> dict:
    rng = random.Random(seed)
    rows: list[dict] = []

    for n in sizes:
        for tree_kind in pc_trees:
            T = _pc_tree(tree_kind, n)
            for instance_kind in instance_kinds:
                for repeat in range(repeats):
                    D = instance_by_kind(n, kind=instance_kind, rng=rng, values=(1, 2, 3))

                    compile_start = time.perf_counter()
                    compilation = compile_cr_nogoods(D, T, max_p_degree=max_p_degree)
                    compile_seconds = time.perf_counter() - compile_start

                    solve_start = time.perf_counter()
                    solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    solve_seconds = time.perf_counter() - solve_start

                    support_compile_start = time.perf_counter()
                    support_compilation = compile_bad_side_nogoods_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    support_compile_seconds = time.perf_counter() - support_compile_start

                    support_solve_start = time.perf_counter()
                    support_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        support_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    support_solve_seconds = time.perf_counter() - support_solve_start

                    grouped_compile_start = time.perf_counter()
                    grouped_compilation = compile_bad_side_nogoods_grouped_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    grouped_compile_seconds = time.perf_counter() - grouped_compile_start

                    grouped_solve_start = time.perf_counter()
                    grouped_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        grouped_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    grouped_solve_seconds = time.perf_counter() - grouped_solve_start

                    first_hit_compile_start = time.perf_counter()
                    first_hit_compilation = compile_bad_side_nogoods_grouped_first_hit_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    first_hit_compile_seconds = time.perf_counter() - first_hit_compile_start

                    first_hit_solve_start = time.perf_counter()
                    first_hit_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        first_hit_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    first_hit_solve_seconds = time.perf_counter() - first_hit_solve_start

                    direct_seconds = None
                    mismatch = False
                    support_mismatch = False
                    grouped_mismatch = False
                    first_hit_mismatch = False
                    if validate and not solve_result["unsupported"]:
                        direct_start = time.perf_counter()
                        direct = accepted_frontiers_by_csp(
                            D,
                            T,
                            source="cr",
                            max_p_degree=max_p_degree,
                        )
                        direct_seconds = time.perf_counter() - direct_start
                        actual = {tuple(order) for order in solve_result["accepted_frontiers"]}
                        support_actual = {
                            tuple(order) for order in support_solve_result["accepted_frontiers"]
                        }
                        grouped_actual = {
                            tuple(order) for order in grouped_solve_result["accepted_frontiers"]
                        }
                        first_hit_actual = {
                            tuple(order) for order in first_hit_solve_result["accepted_frontiers"]
                        }
                        mismatch = actual != direct
                        support_mismatch = support_actual != direct
                        grouped_mismatch = grouped_actual != direct
                        first_hit_mismatch = first_hit_actual != direct

                    counts = solve_result["counts"]
                    compile_counts = compilation["counts"]
                    support_counts = support_solve_result["counts"]
                    support_compile_counts = support_compilation["counts"]
                    grouped_counts = grouped_solve_result["counts"]
                    grouped_compile_counts = grouped_compilation["counts"]
                    first_hit_counts = first_hit_solve_result["counts"]
                    first_hit_compile_counts = first_hit_compilation["counts"]
                    signatures = _signature_set(compilation)
                    support_signatures = _signature_set(support_compilation)
                    grouped_signatures = _signature_set(grouped_compilation)
                    first_hit_signatures = _signature_set(first_hit_compilation)
                    old_scan_work = counts["full_assignment_space"] * max(1, len(support_compilation["atoms"]))
                    support_vs_old_scan_ratio = (
                        support_compile_counts["support_product_total"] / old_scan_work
                        if old_scan_work
                        else 0.0
                    )
                    rows.append(
                        {
                            "n": n,
                            "pc_tree": tree_kind,
                            "instance_kind": instance_kind,
                            "repeat": repeat,
                            "supported": not solve_result["unsupported"],
                            "complete": solve_result["complete"],
                            "mismatch": mismatch,
                            "support_mismatch": support_mismatch,
                            "grouped_mismatch": grouped_mismatch,
                            "first_hit_mismatch": first_hit_mismatch,
                            "compile_seconds": compile_seconds,
                            "solve_seconds": solve_seconds,
                            "support_compile_seconds": support_compile_seconds,
                            "support_solve_seconds": support_solve_seconds,
                            "grouped_compile_seconds": grouped_compile_seconds,
                            "grouped_solve_seconds": grouped_solve_seconds,
                            "first_hit_compile_seconds": first_hit_compile_seconds,
                            "first_hit_solve_seconds": first_hit_solve_seconds,
                            "direct_seconds": direct_seconds,
                            "atoms": len(compilation["atoms"]),
                            "unique_nogoods": compile_counts["unique_nogoods"],
                            "support_atoms": len(support_compilation["atoms"]),
                            "support_unique_nogoods": support_compile_counts["unique_nogoods"],
                            "grouped_atoms": len(grouped_compilation["atoms"]),
                            "grouped_unique_nogoods": grouped_compile_counts["unique_nogoods"],
                            "first_hit_atoms": len(first_hit_compilation["atoms"]),
                            "first_hit_unique_nogoods": first_hit_compile_counts["unique_nogoods"],
                            "effective_nogood_signatures": len(signatures),
                            "support_effective_nogood_signatures": len(support_signatures),
                            "grouped_effective_nogood_signatures": len(grouped_signatures),
                            "first_hit_effective_nogood_signatures": len(first_hit_signatures),
                            "same_effective_signatures": signatures == support_signatures,
                            "same_grouped_effective_signatures": signatures == grouped_signatures,
                            "same_support_and_grouped_signatures": support_signatures == grouped_signatures,
                            "same_first_hit_effective_signatures": signatures == first_hit_signatures,
                            "same_grouped_and_first_hit_signatures": grouped_signatures == first_hit_signatures,
                            "support_assignments_seen": support_compile_counts["support_assignments_seen"],
                            "support_product_total": support_compile_counts["support_product_total"],
                            "support_max_product": support_compile_counts["max_support_product"],
                            "support_vs_old_scan_ratio": support_vs_old_scan_ratio,
                            "grouped_support_assignments_seen": grouped_compile_counts[
                                "grouped_support_assignments_seen"
                            ],
                            "grouped_support_product_total": grouped_compile_counts[
                                "grouped_support_product_total"
                            ],
                            "grouped_support_product_total_if_ungrouped": grouped_compile_counts[
                                "support_product_total_if_ungrouped"
                            ],
                            "grouped_atom_checks": grouped_compile_counts["atom_checks"],
                            "grouped_support_group_count": grouped_compile_counts["support_group_count"],
                            "grouped_max_atoms_per_support": grouped_compile_counts["max_atoms_per_support"],
                            "grouped_vs_ungrouped_support_ratio": grouped_compile_counts[
                                "grouped_vs_ungrouped_support_ratio"
                            ],
                            "first_hit_support_assignments_seen": first_hit_compile_counts[
                                "grouped_support_assignments_seen"
                            ],
                            "first_hit_support_product_total": first_hit_compile_counts[
                                "grouped_support_product_total"
                            ],
                            "first_hit_atom_checks": first_hit_compile_counts["atom_checks"],
                            "first_hit_atom_checks_if_exhaustive": first_hit_compile_counts[
                                "atom_checks_if_exhaustive"
                            ],
                            "first_hit_atom_checks_saved": first_hit_compile_counts[
                                "atom_checks_saved_by_first_hit"
                            ],
                            "atoms_with_nogoods": compile_counts["atoms_with_nogoods"],
                            "max_support_size": compile_counts["max_support_size"],
                            "support_size_histogram": compile_counts["support_size_histogram"],
                            "full_assignment_space": counts["full_assignment_space"],
                            "leaf_assignments_seen": counts["leaf_assignments_seen"],
                            "branches_considered": counts["branches_considered"],
                            "branches_pruned": counts["branches_pruned"],
                            "pruning_rate": counts.get("pruning_rate", 0.0),
                            "accepted_frontiers": counts["accepted_frontiers"],
                            "support_leaf_assignments_seen": support_counts["leaf_assignments_seen"],
                            "support_branches_pruned": support_counts["branches_pruned"],
                            "support_accepted_frontiers": support_counts["accepted_frontiers"],
                            "grouped_leaf_assignments_seen": grouped_counts["leaf_assignments_seen"],
                            "grouped_branches_pruned": grouped_counts["branches_pruned"],
                            "grouped_accepted_frontiers": grouped_counts["accepted_frontiers"],
                            "first_hit_leaf_assignments_seen": first_hit_counts["leaf_assignments_seen"],
                            "first_hit_branches_pruned": first_hit_counts["branches_pruned"],
                            "first_hit_accepted_frontiers": first_hit_counts["accepted_frontiers"],
                        }
                    )

    supported_rows = [row for row in rows if row["supported"]]
    return {
        "config": {
            "sizes": list(sizes),
            "repeats": repeats,
            "instance_kinds": list(instance_kinds),
            "pc_trees": list(pc_trees),
            "max_p_degree": max_p_degree,
            "seed": seed,
            "validate": validate,
        },
        "summary": {
            "rows": len(rows),
            "supported_rows": len(supported_rows),
            "mismatches": sum(1 for row in rows if row["mismatch"]),
            "support_mismatches": sum(1 for row in rows if row["support_mismatch"]),
            "grouped_mismatches": sum(1 for row in rows if row["grouped_mismatch"]),
            "first_hit_mismatches": sum(1 for row in rows if row["first_hit_mismatch"]),
            "signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_effective_signatures"]
            ),
            "grouped_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_grouped_effective_signatures"]
            ),
            "support_grouped_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_support_and_grouped_signatures"]
            ),
            "first_hit_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_first_hit_effective_signatures"]
            ),
            "grouped_first_hit_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_grouped_and_first_hit_signatures"]
            ),
            "median_compile_seconds": _median([row["compile_seconds"] for row in supported_rows]),
            "median_support_compile_seconds": _median(
                [row["support_compile_seconds"] for row in supported_rows]
            ),
            "median_grouped_compile_seconds": _median(
                [row["grouped_compile_seconds"] for row in supported_rows]
            ),
            "median_first_hit_compile_seconds": _median(
                [row["first_hit_compile_seconds"] for row in supported_rows]
            ),
            "median_solve_seconds": _median([row["solve_seconds"] for row in supported_rows]),
            "median_support_solve_seconds": _median(
                [row["support_solve_seconds"] for row in supported_rows]
            ),
            "median_grouped_solve_seconds": _median(
                [row["grouped_solve_seconds"] for row in supported_rows]
            ),
            "median_first_hit_solve_seconds": _median(
                [row["first_hit_solve_seconds"] for row in supported_rows]
            ),
            "median_direct_seconds": _median(
                [row["direct_seconds"] for row in supported_rows if row["direct_seconds"] is not None]
            ),
            "total_unique_nogoods": sum(row["unique_nogoods"] for row in supported_rows),
            "total_support_unique_nogoods": sum(row["support_unique_nogoods"] for row in supported_rows),
            "total_grouped_unique_nogoods": sum(row["grouped_unique_nogoods"] for row in supported_rows),
            "total_first_hit_unique_nogoods": sum(
                row["first_hit_unique_nogoods"] for row in supported_rows
            ),
            "total_support_assignments_seen": sum(
                row["support_assignments_seen"] for row in supported_rows
            ),
            "total_support_product": sum(row["support_product_total"] for row in supported_rows),
            "total_grouped_support_assignments_seen": sum(
                row["grouped_support_assignments_seen"] for row in supported_rows
            ),
            "total_grouped_support_product": sum(
                row["grouped_support_product_total"] for row in supported_rows
            ),
            "total_grouped_atom_checks": sum(row["grouped_atom_checks"] for row in supported_rows),
            "total_first_hit_atom_checks": sum(row["first_hit_atom_checks"] for row in supported_rows),
            "total_first_hit_atom_checks_saved": sum(
                row["first_hit_atom_checks_saved"] for row in supported_rows
            ),
            "median_support_vs_old_scan_ratio": _median(
                [row["support_vs_old_scan_ratio"] for row in supported_rows]
            ),
            "median_grouped_vs_ungrouped_support_ratio": _median(
                [row["grouped_vs_ungrouped_support_ratio"] for row in supported_rows]
            ),
            "total_branches_pruned": sum(row["branches_pruned"] for row in supported_rows),
            "total_leaf_assignments_seen": sum(row["leaf_assignments_seen"] for row in supported_rows),
            "total_full_assignment_space": sum(row["full_assignment_space"] for row in supported_rows),
        },
        "rows": rows,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--instance-kinds", default="random,cycle,block,ultrametric,equal,non_strict")
    parser.add_argument("--pc-trees", default="balanced,mixed")
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260522)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--output", default="reports/csp_internal_benchmark_quick.json")
    args = parser.parse_args(argv)

    report = run_benchmark(
        sizes=_parse_ints(args.sizes),
        repeats=args.repeats,
        instance_kinds=_parse_strings(args.instance_kinds),
        pc_trees=_parse_strings(args.pc_trees),
        max_p_degree=args.max_p_degree,
        seed=args.seed,
        validate=not args.no_validate,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return (
        2
        if report["summary"]["mismatches"]
        or report["summary"]["support_mismatches"]
        or report["summary"]["grouped_mismatches"]
        or report["summary"]["first_hit_mismatches"]
        or report["summary"]["signature_mismatches"]
        or report["summary"]["grouped_signature_mismatches"]
        or report["summary"]["support_grouped_signature_mismatches"]
        or report["summary"]["first_hit_signature_mismatches"]
        or report["summary"]["grouped_first_hit_signature_mismatches"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
