#!/usr/bin/env python3
"""Probe permutation-like P3/P3 relations against exact small quasi orders."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import enumerate_frontiers, p3_block_tree  # noqa: E402
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    canonical_circular_order,
    is_precircular_order_cR,
    is_quasi_circular_order,
)
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    frontier_from_assignment,
    iter_local_assignments,
    quartet_effective_relation_report,
)
from tools.pc_relation_chain_probe import _signature_accepts  # noqa: E402
from tools.pc_relation_chain_probe import run_relation_chain_probe  # noqa: E402
from tools.pc_relation_catalog import _instance, _parse_ints  # noqa: E402


def _canonical_set(orders) -> set[tuple[int, ...]]:
    return {tuple(canonical_circular_order(order)) for order in orders}


def _exact_quasi_sets(D, T, *, exact_quasi_max_n: int) -> tuple[dict, set, set, set]:
    n = len(D)
    frontiers = _canonical_set(enumerate_frontiers(T))
    row = {
        "exact_quasi_checked": n <= exact_quasi_max_n,
        "exact_quasi_max_n": exact_quasi_max_n,
        "scaffold_frontier_count": len(frontiers),
    }
    if n > exact_quasi_max_n:
        metrics = {
            **row,
            "scaffold_quasi_count": None,
            "scaffold_non_quasi_count": None,
            "scaffold_cr_count": None,
            "exact_quasi_order_count": None,
            "exact_cr_order_count": None,
            "scaffold_quasi_intersection_count": None,
            "missing_quasi_order_count": None,
            "scaffold_sound_for_quasi": None,
            "scaffold_complete_for_quasi": None,
            "scaffold_subset_exact_quasi": None,
            "exact_quasi_subset_scaffold": None,
            "scaffold_matches_exact_quasi_orders": None,
        }
        return metrics, frontiers, set(), set()

    all_orders = list(all_circular_orders(n))
    exact_quasi = _canonical_set(
        order for order in all_orders if is_quasi_circular_order(D, order)
    )
    exact_cr = _canonical_set(
        order for order in all_orders if is_precircular_order_cR(D, order)
    )
    scaffold_quasi = {order for order in frontiers if is_quasi_circular_order(D, order)}
    scaffold_cr = {order for order in frontiers if is_precircular_order_cR(D, order)}
    metrics = {
        **row,
        "promise_check_method": "exact_quasi_order_enumeration",
        "all_circular_order_count": len(all_orders),
        "scaffold_quasi_count": len(scaffold_quasi),
        "scaffold_non_quasi_count": len(frontiers - exact_quasi),
        "scaffold_cr_count": len(scaffold_cr),
        "exact_quasi_order_count": len(exact_quasi),
        "exact_cr_order_count": len(exact_cr),
        "scaffold_quasi_intersection_count": len(frontiers & exact_quasi),
        "missing_quasi_order_count": len(exact_quasi - frontiers),
        "scaffold_sound_for_quasi": frontiers <= exact_quasi,
        "scaffold_complete_for_quasi": exact_quasi <= frontiers,
        "scaffold_subset_exact_quasi": frontiers <= exact_quasi,
        "exact_quasi_subset_scaffold": exact_quasi <= frontiers,
        "scaffold_matches_exact_quasi_orders": frontiers == exact_quasi,
        "scaffold_cr_subset_exact_cr": scaffold_cr <= exact_cr,
        "exact_cr_intersect_scaffold_count": len(exact_cr & frontiers),
    }
    return metrics, frontiers, exact_quasi, exact_cr


def _relation_accept_quasi_metrics(D, T, relation_report: dict, exact_quasi: set) -> dict:
    encoding = relation_report["encoding"]
    relations = relation_report["merged_relations"]
    accepted_orders = []
    quasi_count = 0
    cr_count = 0
    for assignment in iter_local_assignments(encoding):
        if not all(_signature_accepts(relation, assignment) for relation in relations):
            continue
        order = tuple(canonical_circular_order(frontier_from_assignment(T, assignment)))
        accepted_orders.append(order)
        if order in exact_quasi:
            quasi_count += 1
        if is_precircular_order_cR(D, order):
            cr_count += 1
    accepted_count = len(accepted_orders)
    non_quasi_count = accepted_count - quasi_count if exact_quasi else None
    return {
        "relation_accept_assignment_count": accepted_count,
        "relation_accept_quasi_count": quasi_count if exact_quasi else None,
        "relation_accept_non_quasi_count": non_quasi_count,
        "relation_accept_cr_count": cr_count,
        "relation_accept_quasi_fraction": (
            quasi_count / accepted_count
            if accepted_count and exact_quasi
            else None
        ),
        "shape_stable_under_quasi_filter": (
            accepted_count == quasi_count if exact_quasi else None
        ),
    }


def _permutation_profiles(row: dict) -> list[dict]:
    return [
        profile
        for profile in row.get("binary_relation_profiles", [])
        if profile["shape"] == "permutation_like"
    ]


def _permutation_details(profile: dict) -> dict:
    mapping = {left: right for left, right in profile["accepted_index_tuples"]}
    inverse = {right: left for left, right in profile["accepted_index_tuples"]}
    domain_product = 1
    for size in profile["domain_sizes"]:
        domain_product *= size
    accepted_count = profile["accepted_signature_count"]
    seen: set[int] = set()
    cycles = []
    for start in sorted(mapping):
        if start in seen:
            continue
        cycle = []
        current = start
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = mapping[current]
        cycles.append(cycle)
    cycle_type = sorted(len(cycle) for cycle in cycles)
    return {
        "catalog_hash": profile["catalog_hash"],
        "scope": profile["scope"],
        "accepted_index_tuples": profile["accepted_index_tuples"],
        "map_left_to_right": {str(key): mapping[key] for key in sorted(mapping)},
        "inverse_map": {str(key): inverse[key] for key in sorted(inverse)},
        "cycle_decomposition": cycles,
        "cycle_type": cycle_type,
        "quartets": profile.get("quartets"),
        "quartet_count": profile.get("quartet_count"),
        "domain_sizes": profile["domain_sizes"],
        "domain_product": profile.get("domain_product", domain_product),
        "accepted_signature_count": accepted_count,
        "rejected_signature_count": profile.get(
            "rejected_signature_count",
            domain_product - accepted_count,
        ),
        "density": profile["density"],
        "shape_tags": profile["shape_tags"],
    }


def _row_category(row: dict, quasi_metrics: dict) -> str:
    has_permutation = bool(_permutation_profiles(row))
    parasite_free = (
        row.get("constant_reject_count", 0) == 0
        and row.get("unary_restrictive_count", 0) == 0
        and row.get("high_arity_count", 0) == 0
    )
    exact_match = quasi_metrics.get("scaffold_matches_exact_quasi_orders")
    if has_permutation and parasite_free and exact_match:
        return "permutation_like_parasite_free_exact_quasi_scaffold"
    if has_permutation and parasite_free:
        return "permutation_like_parasite_free_without_exact_quasi_scaffold"
    if has_permutation:
        return "permutation_like_with_restrictive_parasite"
    if exact_match:
        return "exact_quasi_scaffold_without_permutation_like"
    return "no_permutation_like"


def run_permutation_like_probe(
    *,
    repeats: int = 128,
    seed: int = 20260550,
    block_count: int = 2,
    exact_quasi_max_n: int = 8,
    assignment_limit: int = 250000,
) -> dict:
    """Run a small promise-aware diagnostic for permutation-like relations."""

    chain_report = run_relation_chain_probe(
        block_counts=[block_count],
        instance_kinds=["paired_farthest"],
        repeats=repeats,
        seed=seed,
        assignment_limit=assignment_limit,
    )
    T = p3_block_tree(block_count)
    rows = []
    hash_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    anomalies = []

    for chain_row in chain_report["rows"]:
        D = _instance("paired_farthest", chain_row["n"], seed=chain_row["seed"])
        quasi_metrics, _frontiers, exact_quasi, _exact_cr = _exact_quasi_sets(
            D,
            T,
            exact_quasi_max_n=exact_quasi_max_n,
        )
        relation_report = quartet_effective_relation_report(
            D,
            T,
            max_p_degree=3,
            validate=chain_row["block_count"] <= 3,
            store_full_relations=True,
        )
        accept_quasi_metrics = _relation_accept_quasi_metrics(
            D,
            T,
            relation_report,
            exact_quasi,
        )
        profiles = _permutation_profiles(chain_row)
        for profile in profiles:
            hash_counts[profile["catalog_hash"]] += 1

        category = _row_category(chain_row, quasi_metrics)
        category_counts[category] += 1
        has_permutation = bool(profiles)
        parasite_free = (
            chain_row.get("constant_reject_count", 0) == 0
            and chain_row.get("unary_restrictive_count", 0) == 0
            and chain_row.get("high_arity_count", 0) == 0
        )
        exact_match = quasi_metrics.get("scaffold_matches_exact_quasi_orders")
        anomaly_reasons = []
        if has_permutation and not parasite_free:
            anomaly_reasons.append("permutation_like_has_restrictive_parasite")
        if has_permutation and exact_match is False:
            anomaly_reasons.append("permutation_like_without_exact_quasi_scaffold")
        if exact_match is True and not has_permutation:
            anomaly_reasons.append("exact_quasi_scaffold_without_permutation_like")

        row = {
            "block_count": chain_row["block_count"],
            "n": chain_row["n"],
            "repeat": chain_row["repeat"],
            "seed": chain_row["seed"],
            "complete": chain_row["complete"],
            "validation_mismatch_count": chain_row["validation_mismatch_count"],
            "row_category": category,
            "has_permutation_like": has_permutation,
            "permutation_like_count": len(profiles),
            "permutation_like_profiles": [
                _permutation_details(profile) for profile in profiles
            ],
            "parasite_free": parasite_free,
            "constant_reject_count": chain_row.get("constant_reject_count"),
            "unary_restrictive_count": chain_row.get("unary_restrictive_count"),
            "high_arity_count": chain_row.get("high_arity_count"),
            "full_accept_count": chain_row.get("full_accept_count"),
            "functional_accept_count": chain_row.get("functional_accept_count"),
            "binary_non_boolean_accept_count": chain_row.get(
                "binary_non_boolean_accept_count"
            ),
            "parasite_accept_count": chain_row.get("parasite_accept_count"),
            "direct_cr_assignments": chain_row.get("direct_cr_assignments"),
            "full_unsat_explanation": chain_row.get("full_unsat_explanation"),
            "shape_histogram": chain_row.get("shape_histogram"),
            "relation_count": chain_row.get("relation_count"),
            "exact_quasi_metrics": quasi_metrics,
            "relation_accept_quasi_metrics": accept_quasi_metrics,
            "anomaly_reasons": anomaly_reasons,
            "promise_status": (
                "exact_small_quasi_order_match"
                if exact_match is True
                else "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D"
            ),
            "interpretation": (
                "Permutation-like local relation diagnostic only; not a solver, "
                "not a hardness proof, and not a general Hsu/McConnell promise proof."
            ),
        }
        if anomaly_reasons:
            anomalies.append(row)
        rows.append(row)

    summary = {
        "rows": len(rows),
        "block_count": block_count,
        "n": 3 * block_count,
        "repeats": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "permutation_like_rows": sum(1 for row in rows if row["has_permutation_like"]),
        "parasite_free_permutation_like_rows": sum(
            1
            for row in rows
            if row["has_permutation_like"] and row["parasite_free"]
        ),
        "permutation_like_exact_quasi_scaffold_rows": sum(
            1
            for row in rows
            if row["has_permutation_like"]
            and row["exact_quasi_metrics"].get("scaffold_matches_exact_quasi_orders")
            is True
        ),
        "exact_quasi_scaffold_rows": sum(
            1
            for row in rows
            if row["exact_quasi_metrics"].get("scaffold_matches_exact_quasi_orders")
            is True
        ),
        "anomaly_count": len(anomalies),
        "category_histogram": dict(sorted(category_counts.items())),
        "permutation_like_hash_histogram": dict(sorted(hash_counts.items())),
        "exact_quasi_checked_rows": sum(
            1 for row in rows if row["exact_quasi_metrics"]["exact_quasi_checked"]
        ),
        "promise_caveat": (
            "Exact quasi-order comparison is only done for small n by exhaustive "
            "enumeration. It is not a general Hsu/McConnell reconstruction."
        ),
        "interpretation": (
            "A parasite-free permutation_like profile indicates a local bijection "
            "between two P3 domains in this materialized scaffold. It does not prove "
            "NP-hardness, polynomiality, composability, or solver correctness."
        ),
    }
    return {
        "method": "paired_farthest_permutation_like_promise_probe",
        "chain_summary": chain_report["summary"],
        "rows": rows,
        "anomalies": anomalies,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20260550)
    parser.add_argument("--block-count", type=int, default=2)
    parser.add_argument("--target-seeds", default="")
    parser.add_argument("--exact-quasi-max-n", type=int, default=8)
    parser.add_argument("--assignment-limit", type=int, default=250000)
    parser.add_argument("--output", default="reports/permutation_like_probe.json")
    args = parser.parse_args(argv)

    target_seeds = _parse_ints(args.target_seeds)
    if target_seeds:
        reports = [
            run_permutation_like_probe(
                repeats=1,
                seed=target_seed - 1009 * args.block_count,
                block_count=args.block_count,
                exact_quasi_max_n=args.exact_quasi_max_n,
                assignment_limit=args.assignment_limit,
            )
            for target_seed in target_seeds
        ]
        rows = [report["rows"][0] for report in reports]
        report = {
            "method": "paired_farthest_permutation_like_promise_probe_targets",
            "rows": rows,
            "anomalies": [row for row in rows if row["anomaly_reasons"]],
            "summary": {
                "rows": len(rows),
                "target_seeds": target_seeds,
                "complete_rows": sum(1 for row in rows if row["complete"]),
                "validation_mismatches": sum(
                    row["validation_mismatch_count"] for row in rows
                ),
                "permutation_like_rows": sum(
                    1 for row in rows if row["has_permutation_like"]
                ),
                "parasite_free_permutation_like_rows": sum(
                    1
                    for row in rows
                    if row["has_permutation_like"] and row["parasite_free"]
                ),
                "anomaly_count": sum(1 for row in rows if row["anomaly_reasons"]),
                "promise_caveat": (
                    "Exact quasi-order comparison is only done for small n by "
                    "exhaustive enumeration. It is not a general Hsu/McConnell "
                    "reconstruction."
                ),
                "interpretation": (
                    "Targeted rows are local scaffold diagnostics only; not a "
                    "solver or hardness proof."
                ),
            },
        }
    else:
        report = run_permutation_like_probe(
            repeats=args.repeats,
            seed=args.seed,
            block_count=args.block_count,
            exact_quasi_max_n=args.exact_quasi_max_n,
            assignment_limit=args.assignment_limit,
        )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
