#!/usr/bin/env python3
"""Catalog non-boolean effective quartet relations on small P-block PC-trees."""

from __future__ import annotations

import argparse
import hashlib
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
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.pc_tree import p3_block_tree  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    quartet_effective_relation_report,
)


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _instance(kind: str, n: int, *, seed: int) -> list[list[int]]:
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=random.Random(seed))
    if kind == "random":
        return random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
    if kind == "equal":
        return equal_distance_instance(n)
    if kind == "four_local_non_cr":
        return padded_four_local_non_cr(n)
    if kind == "five_local_non_cr":
        return padded_five_local_non_cr(n)
    raise ValueError(f"unsupported relation-catalog instance kind: {kind}")


def _stable_hash(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _canonical_binary_catalog_key(key):
    """Canonicalize a binary relation key across equal-size scope reversal."""

    domain_sizes, accepted_indices = key
    accepted = tuple(tuple(pair) for pair in accepted_indices)
    if len(domain_sizes) == 2 and domain_sizes[0] == domain_sizes[1]:
        swapped = tuple(sorted((right, left) for left, right in accepted))
        forward = tuple(sorted(accepted))
        accepted = min(forward, swapped)
    return (tuple(domain_sizes), accepted)


def _path_to_string(path: Sequence[int]) -> str:
    return "root" if not path else ".".join(str(part) for part in path)


def _degree_histogram(values: Sequence[int]) -> dict[str, int]:
    histogram: dict[int, int] = {}
    for value in values:
        histogram[value] = histogram.get(value, 0) + 1
    return {str(key): histogram[key] for key in sorted(histogram)}


def _binary_relation_profile(relation: dict) -> dict:
    key = _canonical_binary_catalog_key(relation["relation_catalog_key"])
    domain_sizes, accepted_indices = key
    left_size, right_size = domain_sizes
    left_degrees = [0 for _ in range(left_size)]
    right_degrees = [0 for _ in range(right_size)]
    for left, right in accepted_indices:
        left_degrees[left] += 1
        right_degrees[right] += 1

    accepted_count = len(accepted_indices)
    all_indices = {
        (left, right)
        for left in range(left_size)
        for right in range(right_size)
    }
    rejected_indices = tuple(sorted(all_indices - set(accepted_indices)))
    profile = {
        "scope": [_path_to_string(path) for path in relation["scope"]],
        "domain_sizes": list(domain_sizes),
        "domain_product": relation["domain_product"],
        "accepted_signature_count": relation["accepted_signature_count"],
        "rejected_signature_count": relation["rejected_signature_count"],
        "density": relation["density"],
        "rejected_tuple_ratio": (
            relation["rejected_signature_count"] / relation["domain_product"]
            if relation["domain_product"]
            else 0.0
        ),
        "quartet_count": relation["quartet_count"],
        "catalog_hash": _stable_hash(key),
        "left_degree_histogram": _degree_histogram(left_degrees),
        "right_degree_histogram": _degree_histogram(right_degrees),
        "left_total": all(degree > 0 for degree in left_degrees),
        "right_total": all(degree > 0 for degree in right_degrees),
        "left_functional": all(degree <= 1 for degree in left_degrees),
        "right_functional": all(degree <= 1 for degree in right_degrees),
        "permutation_like": (
            left_size == right_size
            and accepted_count == left_size
            and all(degree == 1 for degree in left_degrees)
            and all(degree == 1 for degree in right_degrees)
        ),
        "complete_bipartite": accepted_count == left_size * right_size,
        "empty": accepted_count == 0,
    }
    if len(accepted_indices) <= 64:
        profile["accepted_index_tuples"] = [list(pair) for pair in accepted_indices]
    if len(rejected_indices) <= 64:
        profile["rejected_index_tuples"] = [list(pair) for pair in rejected_indices]
    return profile


def _histogram(values: Sequence[int]) -> dict[str, int]:
    histogram: dict[int, int] = {}
    for value in values:
        histogram[value] = histogram.get(value, 0) + 1
    return {str(key): histogram[key] for key in sorted(histogram)}


def _row_from_report(
    *,
    block_count: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    relation_seconds: float,
    relation_report: dict,
) -> dict:
    counts = relation_report["counts"]
    primal = relation_report["primal_graph"]
    domains = relation_report["encoding"]["domains"]
    binary_profiles = [
        _binary_relation_profile(relation)
        for relation in relation_report["merged_relations"]
        if relation["relation_kind"] == "binary_non_boolean_catalog"
    ]
    binary_hashes = sorted({profile["catalog_hash"] for profile in binary_profiles})
    relation_kind_histogram = counts["merged_relation_kind_histogram"]
    parasite_constant_reject_count = relation_kind_histogram.get("constant_reject", 0)
    parasite_constant_accept_count = relation_kind_histogram.get("constant_accept", 0)
    parasite_unary_non_boolean_count = relation_kind_histogram.get("unary_non_boolean", 0)
    parasite_unary_boolean_count = relation_kind_histogram.get("unary_boolean", 0)
    parasite_relation_count = (
        parasite_constant_reject_count
        + parasite_constant_accept_count
        + parasite_unary_non_boolean_count
        + parasite_unary_boolean_count
        + counts["merged_relation_high_arity_count"]
    )
    restrictive_parasite_constraint_count = (
        parasite_constant_reject_count
        + parasite_unary_non_boolean_count
        + parasite_unary_boolean_count
        + counts["merged_relation_high_arity_count"]
    )
    relation_domain_products = [
        relation["domain_product"] for relation in relation_report["merged_relations"]
    ]
    relation_rejected_ratios = [
        relation["rejected_signature_count"] / relation["domain_product"]
        for relation in relation_report["merged_relations"]
        if relation["domain_product"]
    ]
    active_domain_sizes = [
        len(domains[tuple(path)])
        for relation in relation_report["merged_relations"]
        for path in relation["scope"]
    ]
    domain_sizes = [len(domain) for domain in domains.values()]
    arities = [relation["arity"] for relation in relation_report["merged_relations"]]

    return {
        "block_count": block_count,
        "n": 3 * block_count,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "relation_seconds": relation_seconds,
        "complete": relation_report["complete"],
        "row_class": relation_report["row_class"],
        "validation_mismatch_count": counts["validation_mismatch_count"],
        "relation_accept_assignments": counts["relation_accept_assignments"],
        "direct_cr_assignments": counts["direct_cr_assignments"],
        "variable_count": len(domains),
        "domain_size_histogram": _histogram(domain_sizes),
        "active_domain_size_histogram": _histogram(active_domain_sizes),
        "max_domain_size": max(domain_sizes, default=0),
        "domain_materialized": True,
        "domain_compact_representation": "none",
        "merged_relation_scope_count": counts["merged_relation_scope_count"],
        "scope_size_histogram": _histogram(arities),
        "unary_scope_count": sum(1 for arity in arities if arity == 1),
        "binary_scope_count": sum(1 for arity in arities if arity == 2),
        "high_arity_scope_count": sum(1 for arity in arities if arity > 2),
        "merged_relation_kind_histogram": relation_kind_histogram,
        "relation_count": len(relation_report["merged_relations"]),
        "binary_boolean_relation_count": counts["merged_relation_binary_boolean_count"],
        "binary_non_boolean_relation_count": len(binary_profiles),
        "high_arity_relation_count": counts["merged_relation_high_arity_count"],
        "binary_non_boolean_catalog_hashes": binary_hashes,
        "binary_non_boolean_relations": binary_profiles,
        "parasite_relation_count": parasite_relation_count,
        "restrictive_parasite_constraint_count": restrictive_parasite_constraint_count,
        "parasite_kind_histogram": {
            key: relation_kind_histogram[key]
            for key in sorted(
                {
                    "constant_accept",
                    "constant_reject",
                    "unary_boolean",
                    "unary_non_boolean",
                    "high_arity",
                }
                & set(relation_kind_histogram)
            )
        },
        "parasite_free_gadget_candidate": (
            len(binary_profiles) > 0 and restrictive_parasite_constraint_count == 0
        ),
        "parasite_constant_reject_count": parasite_constant_reject_count,
        "parasite_constant_accept_count": parasite_constant_accept_count,
        "parasite_unary_non_boolean_count": parasite_unary_non_boolean_count,
        "parasite_unary_boolean_count": parasite_unary_boolean_count,
        "max_relation_domain_product": counts["max_relation_domain_product"],
        "relation_domain_product_histogram": _histogram(relation_domain_products),
        "merged_relation_domain_product_total": counts[
            "merged_relation_domain_product_total"
        ],
        "merged_relation_accepted_signature_total": counts[
            "merged_relation_accepted_signature_total"
        ],
        "merged_relation_rejected_signature_total": counts[
            "merged_relation_rejected_signature_total"
        ],
        "rejected_tuple_ratio": (
            counts["merged_relation_rejected_signature_total"]
            / counts["merged_relation_domain_product_total"]
            if counts["merged_relation_domain_product_total"]
            else 0.0
        ),
        "min_relation_rejected_tuple_ratio": min(relation_rejected_ratios, default=0.0),
        "max_relation_rejected_tuple_ratio": max(relation_rejected_ratios, default=0.0),
        "primal_active_variable_count": primal["active_variable_count"],
        "primal_edge_count": primal["edge_count"],
        "primal_max_degree": primal["max_degree"],
        "primal_treewidth_upper_bound": primal["treewidth_upper_bound"],
        "promise_status": (
            "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D"
        ),
        "negative_certificate_status": (
            "relation_unsat_only"
            if relation_report["complete"] and counts["relation_accept_assignments"] == 0
            else "none"
        ),
        "witness_reconstructed": False,
        "witness_validated": False,
        "witness_is_cr": None,
        "witness_failure_reason": "catalog_only_no_solver_call",
        "complexity_claim_allowed": (
            "two_sat_after_relation_build"
            if relation_report["row_class"] == "two_sat_candidate"
            else "fpt_q_w"
            if relation_report["row_class"] == "non_boolean_relation_catalog"
            else "none"
        ),
    }


def run_relation_catalog(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str],
    repeats: int = 3,
    seed: int = 20260523,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
) -> dict:
    rows = []
    for block_count in block_counts:
        if block_count <= 0:
            raise ValueError("block counts must be positive")
        n = 3 * block_count
        T = p3_block_tree(block_count)
        for kind_index, instance_kind in enumerate(instance_kinds):
            repeat_count = repeats if instance_kind in {"random", "paired_farthest"} else 1
            for repeat in range(repeat_count):
                row_seed = seed + 1009 * block_count + 9176 * kind_index + repeat
                D = _instance(instance_kind, n, seed=row_seed)
                relation_start = time.perf_counter()
                relation_report = quartet_effective_relation_report(
                    D,
                    T,
                    max_p_degree=max_p_degree,
                    validate=block_count <= validate_until_blocks,
                    store_full_relations=True,
                )
                relation_seconds = time.perf_counter() - relation_start
                rows.append(
                    _row_from_report(
                        block_count=block_count,
                        instance_kind=instance_kind,
                        repeat=repeat,
                        seed=row_seed,
                        relation_seconds=relation_seconds,
                        relation_report=relation_report,
                    )
                )

    row_class_histogram = {
        row_class: sum(1 for row in rows if row["row_class"] == row_class)
        for row_class in sorted({row["row_class"] for row in rows})
    }
    all_binary_hashes = sorted(
        {
            relation_hash
            for row in rows
            for relation_hash in row["binary_non_boolean_catalog_hashes"]
        }
    )
    densities = [
        relation["density"]
        for row in rows
        for relation in row["binary_non_boolean_relations"]
    ]
    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "row_class_histogram": row_class_histogram,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "binary_non_boolean_rows": sum(
            1 for row in rows if row["binary_non_boolean_relation_count"] > 0
        ),
        "binary_non_boolean_relation_instances": sum(
            row["binary_non_boolean_relation_count"] for row in rows
        ),
        "unique_binary_non_boolean_catalog_hashes": len(all_binary_hashes),
        "binary_non_boolean_catalog_hashes": all_binary_hashes,
        "rows_with_constant_reject_parasite": sum(
            1 for row in rows if row["parasite_constant_reject_count"] > 0
        ),
        "rows_with_unary_non_boolean_parasite": sum(
            1 for row in rows if row["parasite_unary_non_boolean_count"] > 0
        ),
        "max_primal_treewidth_upper_bound": max(
            (row["primal_treewidth_upper_bound"] for row in rows),
            default=0,
        ),
        "max_relation_domain_product": max(
            (row["max_relation_domain_product"] for row in rows),
            default=0,
        ),
        "max_binary_relation_density": max(densities, default=0.0),
        "min_binary_relation_density": min(densities, default=0.0),
        "zero_accept_rows": sum(
            1 for row in rows if row["complete"] and row["relation_accept_assignments"] == 0
        ),
        "promise_caveat": (
            "The catalog uses scaffold PC-trees; it does not prove that these "
            "trees are exactly the Hsu/McConnell quasi-circular PC-tree for D."
        ),
    }
    return {
        "method": "p3_block_relation_catalog",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3")
    parser.add_argument(
        "--instance-kinds",
        default="cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--output", default="reports/relation_catalog.json")
    args = parser.parse_args(argv)

    report = run_relation_catalog(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
