#!/usr/bin/env python3
"""Width stress benchmark for P3-block PC-tree CSP relations."""

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
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    cycle_metric,
    equal_distance_instance,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.pc_tree import p3_block_tree  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    quartet_effective_relation_report,
    solve_quartet_treewidth_csp,
)


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _instance(kind: str, n: int, *, seed: int):
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    raise ValueError(f"unsupported width-stress instance kind: {kind}")


def run_width_stress(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str],
    seed: int = 20260523,
    max_p_degree: int = 3,
    max_treewidth: int = 6,
    max_exact_width_variables: int = 16,
    validate_until_blocks: int = 4,
) -> dict:
    rows = []
    for block_count in block_counts:
        if block_count <= 0:
            raise ValueError("block counts must be positive")
        n = 3 * block_count
        T = p3_block_tree(block_count)
        for kind_index, instance_kind in enumerate(instance_kinds):
            D = _instance(
                instance_kind,
                n,
                seed=seed + 1009 * block_count + 9176 * kind_index,
            )
            validate = block_count <= validate_until_blocks

            relation_start = time.perf_counter()
            relation_report = quartet_effective_relation_report(
                D,
                T,
                max_p_degree=max_p_degree,
                validate=validate,
                store_full_relations=True,
            )
            relation_seconds = time.perf_counter() - relation_start

            solve_start = time.perf_counter()
            solve_result = solve_quartet_treewidth_csp(
                D,
                T,
                max_p_degree=max_p_degree,
                relation_report=relation_report,
                max_treewidth=max_treewidth,
                max_exact_width_variables=max_exact_width_variables,
            )
            solve_seconds = time.perf_counter() - solve_start

            relation_counts = relation_report["counts"]
            primal = relation_report["primal_graph"]
            solve_counts = solve_result["counts"]
            rows.append(
                {
                    "block_count": block_count,
                    "n": n,
                    "instance_kind": instance_kind,
                    "validate": validate,
                    "relation_seconds": relation_seconds,
                    "solve_seconds": solve_seconds,
                    "relation_complete": relation_report["complete"],
                    "relation_row_class": relation_report["row_class"],
                    "relation_validation_mismatches": relation_counts[
                        "validation_mismatch_count"
                    ],
                    "relation_accept_assignments": relation_counts[
                        "relation_accept_assignments"
                    ],
                    "direct_cr_assignments": relation_counts["direct_cr_assignments"],
                    "merged_relation_scope_count": relation_counts[
                        "merged_relation_scope_count"
                    ],
                    "merged_relation_kind_histogram": relation_counts[
                        "merged_relation_kind_histogram"
                    ],
                    "merged_relation_binary_non_boolean_count": relation_counts[
                        "merged_relation_binary_non_boolean_count"
                    ],
                    "merged_relation_high_arity_count": relation_counts[
                        "merged_relation_high_arity_count"
                    ],
                    "primal_active_variable_count": primal["active_variable_count"],
                    "primal_edge_count": primal["edge_count"],
                    "primal_max_degree": primal["max_degree"],
                    "primal_treewidth_upper_bound": primal["treewidth_upper_bound"],
                    "treewidth_complete": solve_result["complete"],
                    "treewidth_exists": solve_result["exists"],
                    "treewidth_reason": solve_result["reason"],
                    "treewidth_exact": solve_counts["treewidth_exact"],
                    "treewidth_cap": solve_counts["treewidth_cap"],
                    "treewidth_max_domain_size": solve_counts["max_domain_size"],
                    "treewidth_non_boolean_variables": solve_counts[
                        "non_boolean_variables"
                    ],
                    "treewidth_max_bucket_scope_size": solve_counts.get(
                        "max_bucket_scope_size", 0
                    ),
                    "treewidth_max_generated_rows": solve_counts.get(
                        "max_generated_rows", 0
                    ),
                    "treewidth_witness_is_cr": solve_counts["witness_is_cr"],
                }
            )

    reason_histogram = {
        reason: sum(1 for row in rows if row["treewidth_reason"] == reason)
        for reason in sorted({row["treewidth_reason"] for row in rows}, key=str)
    }
    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "max_treewidth": max_treewidth,
        "max_exact_width_variables": max_exact_width_variables,
        "relation_incomplete_rows": sum(1 for row in rows if not row["relation_complete"]),
        "relation_validation_mismatches": sum(
            row["relation_validation_mismatches"] for row in rows
        ),
        "treewidth_complete_rows": sum(1 for row in rows if row["treewidth_complete"]),
        "treewidth_incomplete_rows": sum(1 for row in rows if not row["treewidth_complete"]),
        "treewidth_exists_true_rows": sum(
            1 for row in rows if row["treewidth_exists"] is True
        ),
        "treewidth_exists_false_rows": sum(
            1 for row in rows if row["treewidth_exists"] is False
        ),
        "treewidth_reason_histogram": reason_histogram,
        "max_primal_treewidth_upper_bound": max(
            (row["primal_treewidth_upper_bound"] for row in rows),
            default=0,
        ),
        "max_treewidth_exact": max(
            (
                row["treewidth_exact"]
                for row in rows
                if row["treewidth_exact"] is not None
            ),
            default=0,
        ),
        "max_domain_size": max(
            (row["treewidth_max_domain_size"] for row in rows),
            default=0,
        ),
        "non_boolean_rows": sum(1 for row in rows if row["treewidth_non_boolean_variables"]),
        "witness_failures": sum(
            1
            for row in rows
            if row["treewidth_exists"] is True and not row["treewidth_witness_is_cr"]
        ),
    }
    return {
        "method": "p3_block_tree_width_stress",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3,4,5")
    parser.add_argument("--instance-kinds", default="cycle,paired_farthest,equal")
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--max-treewidth", type=int, default=6)
    parser.add_argument("--max-exact-width-variables", type=int, default=16)
    parser.add_argument("--validate-until-blocks", type=int, default=4)
    parser.add_argument("--output", default="reports/p3_width_stress.json")
    args = parser.parse_args(argv)

    report = run_width_stress(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        max_treewidth=args.max_treewidth,
        max_exact_width_variables=args.max_exact_width_variables,
        validate_until_blocks=args.validate_until_blocks,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["witness_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
