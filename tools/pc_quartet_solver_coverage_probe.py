#!/usr/bin/env python3
"""Measure positive-only coverage of quartet 2-SAT/treewidth solvers."""

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

from pc_circular.pc_tree import p3_block_tree, represents_order  # noqa: E402
from pc_circular.solvers import candidate  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    quartet_effective_relation_report,
    solve_quartet_2sat,
    solve_quartet_treewidth_csp,
)
from tools.pc_relation_catalog import _instance, _parse_ints, _parse_strings  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "paired_farthest",
    "random",
    "equal",
    "four_local_non_cr",
    "five_local_non_cr",
)


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _repeat_count(instance_kind: str, repeats: int) -> int:
    return repeats if instance_kind in {"paired_farthest", "random"} else 1


def _safe_positive(result: dict) -> bool:
    return (
        result.get("complete") is True
        and result.get("exists") is True
        and result.get("counts", {}).get("witness_is_cr") is True
    )


def _safe_false(result: dict) -> bool:
    return result.get("complete") is True and result.get("exists") is False


def _row(
    *,
    block_count: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    max_p_degree: int,
    validate: bool,
    max_treewidth: int,
    max_exact_width_variables: int,
) -> dict:
    n = 3 * block_count
    T = p3_block_tree(block_count)
    D = _instance(instance_kind, n, seed=seed)

    candidate_start = time.perf_counter()
    candidate_result = candidate.solve(D, pc_tree=T)
    candidate_seconds = time.perf_counter() - candidate_start

    relation_start = time.perf_counter()
    relation_report = quartet_effective_relation_report(
        D,
        T,
        max_p_degree=max_p_degree,
        validate=validate,
        store_full_relations=True,
    )
    relation_seconds = time.perf_counter() - relation_start

    two_sat_start = time.perf_counter()
    two_sat = solve_quartet_2sat(
        D,
        T,
        max_p_degree=max_p_degree,
        relation_report=relation_report,
    )
    two_sat_seconds = time.perf_counter() - two_sat_start

    treewidth_start = time.perf_counter()
    treewidth = solve_quartet_treewidth_csp(
        D,
        T,
        max_p_degree=max_p_degree,
        relation_report=relation_report,
        max_treewidth=max_treewidth,
        max_exact_width_variables=max_exact_width_variables,
    )
    treewidth_seconds = time.perf_counter() - treewidth_start

    candidate_positive = candidate_result.get("exists") is True
    two_sat_positive = _safe_positive(two_sat)
    treewidth_positive = _safe_positive(treewidth)
    any_quartet_positive = two_sat_positive or treewidth_positive
    new_positive = any_quartet_positive and not candidate_positive
    witness_order = (
        treewidth.get("order")
        if treewidth_positive
        else two_sat.get("order")
        if two_sat_positive
        else None
    )
    relation_counts = relation_report["counts"]
    return {
        "block_count": block_count,
        "n": n,
        "tree_kind": "p3_block_tree",
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "validate": validate,
        "candidate_seconds": candidate_seconds,
        "candidate_exists": candidate_result.get("exists"),
        "candidate_complete": candidate_result.get("complete"),
        "candidate_solver": candidate_result.get("solver"),
        "relation_seconds": relation_seconds,
        "relation_complete": relation_report["complete"],
        "relation_row_class": relation_report["row_class"],
        "relation_validation_mismatches": relation_counts["validation_mismatch_count"],
        "relation_accept_assignments": relation_counts.get("relation_accept_assignments"),
        "direct_cr_assignments": relation_counts.get("direct_cr_assignments"),
        "relation_scope_count": relation_counts["merged_relation_scope_count"],
        "relation_kind_histogram": relation_counts["merged_relation_kind_histogram"],
        "primal_treewidth_upper_bound": relation_report["primal_graph"][
            "treewidth_upper_bound"
        ],
        "max_relation_domain_product": relation_counts["max_relation_domain_product"],
        "two_sat_seconds": two_sat_seconds,
        "two_sat_complete": two_sat["complete"],
        "two_sat_exists": two_sat["exists"],
        "two_sat_reason": two_sat["reason"],
        "two_sat_witness_is_cr": two_sat["counts"]["witness_is_cr"],
        "two_sat_inactive_variables_defaulted": two_sat["counts"].get(
            "inactive_variables_defaulted",
            0,
        ),
        "treewidth_seconds": treewidth_seconds,
        "treewidth_complete": treewidth["complete"],
        "treewidth_exists": treewidth["exists"],
        "treewidth_reason": treewidth["reason"],
        "treewidth_exact": treewidth["counts"]["treewidth_exact"],
        "treewidth_active_variables": treewidth["counts"]["active_variables"],
        "treewidth_max_domain_size": treewidth["counts"]["max_domain_size"],
        "treewidth_non_boolean_variables": treewidth["counts"]["non_boolean_variables"],
        "treewidth_witness_is_cr": treewidth["counts"]["witness_is_cr"],
        "witness_order": witness_order,
        "witness_represents_tree": (
            represents_order(T, witness_order) if witness_order is not None else None
        ),
        "quartet_positive_solver": (
            "treewidth"
            if treewidth_positive
            else "two_sat"
            if two_sat_positive
            else None
        ),
        "quartet_safe_positive": any_quartet_positive,
        "quartet_new_positive_over_candidate": new_positive,
        "quartet_safe_false_diagnostic": _safe_false(two_sat) or _safe_false(treewidth),
        "integration_status": (
            "positive_candidate"
            if new_positive
            else "already_found_by_candidate"
            if any_quartet_positive
            else "no_positive_witness"
        ),
        "interpretation": (
            "Positive-only coverage probe. True witnesses are directly checked "
            "by fixed-order cR; False results are diagnostics, not candidate "
            "integration permissions."
        ),
    }


def run_quartet_solver_coverage_probe(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 8,
    seed: int = 20260580,
    max_p_degree: int = 3,
    validate_until_blocks: int = 4,
    max_treewidth: int = 5,
    max_exact_width_variables: int = 16,
) -> dict:
    rows = []
    for block_count in block_counts:
        if block_count <= 0:
            raise ValueError("block counts must be positive")
        for kind_index, instance_kind in enumerate(instance_kinds):
            for repeat in range(_repeat_count(instance_kind, repeats)):
                row_seed = seed + 1009 * block_count + 9176 * kind_index + repeat
                rows.append(
                    _row(
                        block_count=block_count,
                        instance_kind=instance_kind,
                        repeat=repeat,
                        seed=row_seed,
                        max_p_degree=max_p_degree,
                        validate=block_count <= validate_until_blocks,
                        max_treewidth=max_treewidth,
                        max_exact_width_variables=max_exact_width_variables,
                    )
                )

    new_positive_rows = [
        row for row in rows if row["quartet_new_positive_over_candidate"]
    ]
    by_block_count = {}
    for block_count in block_counts:
        block_rows = [row for row in rows if row["block_count"] == block_count]
        by_block_count[str(block_count)] = {
            "rows": len(block_rows),
            "candidate_positive_rows": sum(1 for row in block_rows if row["candidate_exists"] is True),
            "quartet_safe_positive_rows": sum(1 for row in block_rows if row["quartet_safe_positive"]),
            "new_positive_rows": sum(
                1 for row in block_rows if row["quartet_new_positive_over_candidate"]
            ),
            "treewidth_incomplete_rows": sum(1 for row in block_rows if not row["treewidth_complete"]),
        }

    by_instance_kind = {}
    for instance_kind in instance_kinds:
        kind_rows = [row for row in rows if row["instance_kind"] == instance_kind]
        by_instance_kind[instance_kind] = {
            "rows": len(kind_rows),
            "candidate_positive_rows": sum(1 for row in kind_rows if row["candidate_exists"] is True),
            "quartet_safe_positive_rows": sum(1 for row in kind_rows if row["quartet_safe_positive"]),
            "new_positive_rows": sum(
                1 for row in kind_rows if row["quartet_new_positive_over_candidate"]
            ),
            "safe_false_diagnostic_rows": sum(
                1 for row in kind_rows if row["quartet_safe_false_diagnostic"]
            ),
        }

    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "relation_complete_rows": sum(1 for row in rows if row["relation_complete"]),
        "relation_validation_mismatches": sum(
            row["relation_validation_mismatches"] for row in rows
        ),
        "candidate_positive_rows": sum(1 for row in rows if row["candidate_exists"] is True),
        "candidate_incomplete_rows": sum(1 for row in rows if row["candidate_complete"] is False),
        "two_sat_complete_rows": sum(1 for row in rows if row["two_sat_complete"]),
        "two_sat_safe_positive_rows": sum(
            1 for row in rows if row["two_sat_complete"] and row["two_sat_witness_is_cr"]
        ),
        "treewidth_complete_rows": sum(1 for row in rows if row["treewidth_complete"]),
        "treewidth_incomplete_rows": sum(1 for row in rows if not row["treewidth_complete"]),
        "treewidth_safe_positive_rows": sum(
            1 for row in rows if row["treewidth_complete"] and row["treewidth_witness_is_cr"]
        ),
        "quartet_safe_positive_rows": sum(1 for row in rows if row["quartet_safe_positive"]),
        "new_positive_rows": len(new_positive_rows),
        "safe_false_diagnostic_rows": sum(
            1 for row in rows if row["quartet_safe_false_diagnostic"]
        ),
        "witness_failures": sum(
            1
            for row in rows
            if (row["two_sat_exists"] is True and not row["two_sat_witness_is_cr"])
            or (row["treewidth_exists"] is True and not row["treewidth_witness_is_cr"])
            or (
                row["quartet_safe_positive"]
                and row["witness_represents_tree"] is not True
            )
        ),
        "max_seconds": max(
            (
                max(row["candidate_seconds"], row["relation_seconds"], row["treewidth_seconds"])
                for row in rows
            ),
            default=0.0,
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
        "two_sat_reason_histogram": _histogram([str(row["two_sat_reason"]) for row in rows]),
        "treewidth_reason_histogram": _histogram([str(row["treewidth_reason"]) for row in rows]),
        "integration_status_histogram": _histogram(
            [row["integration_status"] for row in rows]
        ),
        "by_block_count": by_block_count,
        "by_instance_kind": by_instance_kind,
        "new_positive_examples": [
            {
                "block_count": row["block_count"],
                "instance_kind": row["instance_kind"],
                "repeat": row["repeat"],
                "seed": row["seed"],
                "solver": row["quartet_positive_solver"],
                "candidate_solver": row["candidate_solver"],
                "treewidth_exact": row["treewidth_exact"],
                "treewidth_max_domain_size": row["treewidth_max_domain_size"],
            }
            for row in new_positive_rows[:20]
        ],
        "interpretation": (
            "Counts only validated True witnesses as possible positive-only "
            "coverage. False or UNSAT rows are not candidate decisions without "
            "additional proof obligations."
        ),
    }
    return {
        "method": "p3_block_quartet_solver_positive_coverage_probe",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3,4,5")
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260580)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=4)
    parser.add_argument("--max-treewidth", type=int, default=5)
    parser.add_argument("--max-exact-width-variables", type=int, default=16)
    parser.add_argument("--output", default="reports/quartet_solver_coverage_probe.json")
    args = parser.parse_args(argv)

    report = run_quartet_solver_coverage_probe(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
        max_treewidth=args.max_treewidth,
        max_exact_width_variables=args.max_exact_width_variables,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["relation_validation_mismatches"] or report["summary"]["witness_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
