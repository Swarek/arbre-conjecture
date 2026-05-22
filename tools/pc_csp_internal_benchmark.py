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

                    direct_seconds = None
                    mismatch = False
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
                        mismatch = actual != direct

                    counts = solve_result["counts"]
                    compile_counts = compilation["counts"]
                    rows.append(
                        {
                            "n": n,
                            "pc_tree": tree_kind,
                            "instance_kind": instance_kind,
                            "repeat": repeat,
                            "supported": not solve_result["unsupported"],
                            "complete": solve_result["complete"],
                            "mismatch": mismatch,
                            "compile_seconds": compile_seconds,
                            "solve_seconds": solve_seconds,
                            "direct_seconds": direct_seconds,
                            "atoms": len(compilation["atoms"]),
                            "unique_nogoods": compile_counts["unique_nogoods"],
                            "atoms_with_nogoods": compile_counts["atoms_with_nogoods"],
                            "max_support_size": compile_counts["max_support_size"],
                            "support_size_histogram": compile_counts["support_size_histogram"],
                            "full_assignment_space": counts["full_assignment_space"],
                            "leaf_assignments_seen": counts["leaf_assignments_seen"],
                            "branches_considered": counts["branches_considered"],
                            "branches_pruned": counts["branches_pruned"],
                            "pruning_rate": counts.get("pruning_rate", 0.0),
                            "accepted_frontiers": counts["accepted_frontiers"],
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
            "median_compile_seconds": _median([row["compile_seconds"] for row in supported_rows]),
            "median_solve_seconds": _median([row["solve_seconds"] for row in supported_rows]),
            "median_direct_seconds": _median(
                [row["direct_seconds"] for row in supported_rows if row["direct_seconds"] is not None]
            ),
            "total_unique_nogoods": sum(row["unique_nogoods"] for row in supported_rows),
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
    return 2 if report["summary"]["mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
