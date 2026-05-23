#!/usr/bin/env python3
"""Probe composition of functional non-boolean relations on P3 block trees."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict, deque
from itertools import product
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import p3_block_tree  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    iter_local_assignments,
    quartet_effective_relation_report,
)
from tools.pc_relation_catalog import (  # noqa: E402
    _binary_relation_profile,
    _instance,
    _parse_ints,
    _parse_strings,
    _path_to_string,
)
from tools.pc_relation_shape_search import classify_relation_shape  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "paired_farthest",
    "random",
    "equal",
    "four_local_non_cr",
    "five_local_non_cr",
)

FUNCTIONAL_SHAPES = {
    "permutation_like",
    "sparse_partial_matching",
    "partial_bijection",
    "left_selector",
    "right_selector",
    "small_domain_bridge",
}


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _path_key(path: tuple[int, ...]) -> str:
    return _path_to_string(path)


def _signature_accepts(relation: dict, assignment: dict) -> bool:
    signature = tuple((path, assignment[path]) for path in relation["scope"])
    return signature in relation["accepted_signatures"]


def _relation_kind(relation: dict) -> str:
    return relation["relation_kind"]


def _relation_shape(relation: dict) -> tuple[str, list[str], dict | None]:
    if _relation_kind(relation) != "binary_non_boolean_catalog":
        return relation["relation_kind"], [], None
    profile = _binary_relation_profile(relation)
    shape, tags = classify_relation_shape(profile)
    return shape, tags, profile


def _domain_product(domains: dict, variables: Sequence[tuple[int, ...]]) -> int:
    product_value = 1
    for variable in variables:
        product_value *= len(domains[variable])
    return product_value


def _count_assignments(
    assignments: Sequence[dict],
    relations: Sequence[dict],
) -> int:
    if not relations:
        return len(assignments)
    count = 0
    for assignment in assignments:
        if all(_signature_accepts(relation, assignment) for relation in relations):
            count += 1
    return count


def _component_metrics(
    *,
    domains: dict,
    functional_relations: Sequence[dict],
    component_product_limit: int,
) -> tuple[list[dict], bool]:
    adjacency: dict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    edges: list[tuple[tuple[int, ...], tuple[int, ...], dict]] = []
    for relation in functional_relations:
        left, right = relation["scope"]
        adjacency[left].add(right)
        adjacency[right].add(left)
        edges.append((left, right, relation))

    seen: set[tuple[int, ...]] = set()
    components = []
    incomplete = False
    for start in sorted(adjacency):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        nodes: list[tuple[int, ...]] = []
        while queue:
            node = queue.popleft()
            nodes.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        node_set = set(nodes)
        component_relations = [
            relation
            for left, right, relation in edges
            if left in node_set and right in node_set
        ]
        edge_count = len(component_relations)
        degree_histogram = Counter(str(len(adjacency[node])) for node in nodes)
        domain_product = _domain_product(domains, nodes)
        accept_count = None
        relation_product_incomplete = domain_product > component_product_limit
        if relation_product_incomplete:
            incomplete = True
        else:
            accept_count = 0
            for values in product(*(domains[node] for node in nodes)):
                assignment = dict(zip(nodes, values))
                if all(_signature_accepts(relation, assignment) for relation in component_relations):
                    accept_count += 1

        components.append(
            {
                "nodes": [_path_key(node) for node in sorted(nodes)],
                "node_count": len(nodes),
                "edge_count": edge_count,
                "cycle_like": edge_count >= len(nodes),
                "degree_histogram": dict(sorted(degree_histogram.items())),
                "domain_product": domain_product,
                "accept_count": accept_count,
                "incomplete": relation_product_incomplete,
                "zero_accept": accept_count == 0 if accept_count is not None else False,
            }
        )
    return components, incomplete


def _row_from_relation_report(
    *,
    block_count: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    seconds: float,
    relation_report: dict,
    assignment_limit: int,
    component_product_limit: int,
) -> dict:
    domains = relation_report["encoding"]["domains"]
    relations = relation_report["merged_relations"]
    if not relation_report["complete"]:
        return {
            "block_count": block_count,
            "n": 3 * block_count,
            "instance_kind": instance_kind,
            "repeat": repeat,
            "seed": seed,
            "seconds": seconds,
            "complete": False,
            "row_class": relation_report["row_class"],
            "validation_mismatch_count": relation_report["counts"][
                "validation_mismatch_count"
            ],
            "incomplete_reason": relation_report["row_class"],
        }

    shape_histogram: Counter[str] = Counter()
    functional_relations = []
    binary_non_boolean_relations = []
    binary_relation_profiles = []
    for relation in relations:
        shape, tags, profile = _relation_shape(relation)
        if profile is None:
            continue
        binary_non_boolean_relations.append(relation)
        shape_histogram[shape] += 1
        binary_relation_profiles.append(
            {
                "scope": [_path_key(path) for path in relation["scope"]],
                "shape": shape,
                "shape_tags": tags,
                "catalog_hash": profile["catalog_hash"],
                "domain_sizes": profile["domain_sizes"],
                "accepted_signature_count": profile["accepted_signature_count"],
                "density": profile["density"],
                "left_functional": profile["left_functional"],
                "right_functional": profile["right_functional"],
                "accepted_index_tuples": profile.get("accepted_index_tuples"),
            }
        )
        if shape in FUNCTIONAL_SHAPES:
            functional_relations.append(relation)

    parasite_relations = [
        relation
        for relation in relations
        if relation not in binary_non_boolean_relations
    ]
    constant_reject_count = sum(
        1 for relation in relations if relation["relation_kind"] == "constant_reject"
    )
    unary_restrictive_count = sum(
        1
        for relation in relations
        if relation["relation_kind"] in {"unary_boolean", "unary_non_boolean"}
    )
    high_arity_count = sum(1 for relation in relations if relation["arity"] > 2)

    assignment_space = _domain_product(domains, list(domains))
    assignment_incomplete = assignment_space > assignment_limit
    assignments = []
    if not assignment_incomplete:
        assignments = list(iter_local_assignments(relation_report["encoding"]))

    if assignment_incomplete:
        full_accept_count = None
        functional_accept_count = None
        binary_non_boolean_accept_count = None
        parasite_accept_count = None
    else:
        full_accept_count = _count_assignments(assignments, relations)
        functional_accept_count = _count_assignments(assignments, functional_relations)
        binary_non_boolean_accept_count = _count_assignments(
            assignments,
            binary_non_boolean_relations,
        )
        parasite_accept_count = _count_assignments(assignments, parasite_relations)

    components, component_incomplete = _component_metrics(
        domains=domains,
        functional_relations=functional_relations,
        component_product_limit=component_product_limit,
    )
    cycle_components = [component for component in components if component["cycle_like"]]
    zero_cycle_components = [
        component
        for component in cycle_components
        if component["zero_accept"] and not component["incomplete"]
    ]

    if full_accept_count is None:
        full_unsat_explanation = "assignment_limit_exceeded"
    elif full_accept_count > 0:
        full_unsat_explanation = "sat"
    elif constant_reject_count:
        full_unsat_explanation = "constant_reject"
    elif parasite_accept_count == 0:
        full_unsat_explanation = "parasite_unsat"
    elif binary_non_boolean_accept_count == 0:
        full_unsat_explanation = "binary_non_boolean_unsat"
    else:
        full_unsat_explanation = "interaction_unsat"

    global_unsat_not_unary_or_constant = (
        full_accept_count == 0
        and constant_reject_count == 0
        and parasite_accept_count not in {None, 0}
        and binary_non_boolean_accept_count not in {None, 0}
    )
    functional_cycle_obstruction = bool(zero_cycle_components)

    return {
        "block_count": block_count,
        "n": 3 * block_count,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": relation_report["complete"],
        "row_class": relation_report["row_class"],
        "validation_mismatch_count": relation_report["counts"][
            "validation_mismatch_count"
        ],
        "variable_count": len(domains),
        "domain_size_histogram": {
            str(size): count
            for size, count in sorted(
                Counter(len(domain) for domain in domains.values()).items()
            )
        },
        "assignment_space": assignment_space,
        "assignment_limit": assignment_limit,
        "assignment_incomplete": assignment_incomplete,
        "full_accept_count": full_accept_count,
        "direct_cr_assignments": relation_report["counts"]["direct_cr_assignments"],
        "functional_accept_count": functional_accept_count,
        "binary_non_boolean_accept_count": binary_non_boolean_accept_count,
        "parasite_accept_count": parasite_accept_count,
        "full_unsat_explanation": full_unsat_explanation,
        "global_unsat_not_unary_or_constant": global_unsat_not_unary_or_constant,
        "restrictive_parasite_free_functional_candidate": (
            bool(functional_relations)
            and constant_reject_count == 0
            and unary_restrictive_count == 0
            and high_arity_count == 0
        ),
        "relation_count": len(relations),
        "binary_non_boolean_relation_count": len(binary_non_boolean_relations),
        "functional_relation_count": len(functional_relations),
        "nonfunctional_binary_non_boolean_relation_count": (
            len(binary_non_boolean_relations) - len(functional_relations)
        ),
        "constant_reject_count": constant_reject_count,
        "unary_restrictive_count": unary_restrictive_count,
        "high_arity_count": high_arity_count,
        "shape_histogram": dict(sorted(shape_histogram.items())),
        "functional_components": components,
        "functional_component_count": len(components),
        "functional_cycle_component_count": len(cycle_components),
        "functional_zero_cycle_component_count": len(zero_cycle_components),
        "functional_cycle_obstruction": functional_cycle_obstruction,
        "component_incomplete": component_incomplete,
        "binary_relation_profiles": binary_relation_profiles,
        "promise_status": (
            "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D"
        ),
        "interpretation": (
            "Experimental CSP-composition diagnostic only; not a candidate "
            "solver or a proof of hardness/tractability."
        ),
    }


def run_relation_chain_probe(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str],
    repeats: int = 3,
    seed: int = 20260523,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
    assignment_limit: int = 250000,
    component_product_limit: int = 100000,
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
                start = time.perf_counter()
                relation_report = quartet_effective_relation_report(
                    D,
                    T,
                    max_p_degree=max_p_degree,
                    validate=block_count <= validate_until_blocks,
                    store_full_relations=True,
                )
                seconds = time.perf_counter() - start
                rows.append(
                    _row_from_relation_report(
                        block_count=block_count,
                        instance_kind=instance_kind,
                        repeat=repeat,
                        seed=row_seed,
                        seconds=seconds,
                        relation_report=relation_report,
                        assignment_limit=assignment_limit,
                        component_product_limit=component_product_limit,
                    )
                )

    explanation_histogram = _histogram(
        [row.get("full_unsat_explanation", "incomplete") for row in rows]
    )
    shape_histogram: Counter[str] = Counter()
    for row in rows:
        shape_histogram.update(row.get("shape_histogram", {}))
    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "assignment_incomplete_rows": sum(
            1 for row in rows if row.get("assignment_incomplete")
        ),
        "rows_with_functional_relations": sum(
            1 for row in rows if row.get("functional_relation_count", 0) > 0
        ),
        "rows_with_functional_cycle_components": sum(
            1 for row in rows if row.get("functional_cycle_component_count", 0) > 0
        ),
        "rows_with_functional_cycle_obstruction": sum(
            1 for row in rows if row.get("functional_cycle_obstruction")
        ),
        "rows_with_global_unsat_not_unary_or_constant": sum(
            1 for row in rows if row.get("global_unsat_not_unary_or_constant")
        ),
        "rows_with_restrictive_parasite_free_functional_candidate": sum(
            1
            for row in rows
            if row.get("restrictive_parasite_free_functional_candidate")
        ),
        "rows_with_permutation_like": sum(
            1
            for row in rows
            if row.get("shape_histogram", {}).get("permutation_like", 0) > 0
        ),
        "rows_with_restrictive_parasite_free_permutation_like": sum(
            1
            for row in rows
            if row.get("restrictive_parasite_free_functional_candidate")
            and row.get("shape_histogram", {}).get("permutation_like", 0) > 0
        ),
        "rows_with_constant_reject": sum(
            1 for row in rows if row.get("constant_reject_count", 0) > 0
        ),
        "max_functional_component_nodes": max(
            (
                component["node_count"]
                for row in rows
                for component in row.get("functional_components", [])
            ),
            default=0,
        ),
        "max_functional_component_edges": max(
            (
                component["edge_count"]
                for row in rows
                for component in row.get("functional_components", [])
            ),
            default=0,
        ),
        "shape_histogram": dict(sorted(shape_histogram.items())),
        "full_unsat_explanation_histogram": explanation_histogram,
        "promise_caveat": (
            "The probe uses scaffold PC-trees; it does not prove these are "
            "the Hsu/McConnell quasi-circular PC-tree for D."
        ),
        "interpretation": (
            "This report composes observed relation profiles in the materialized "
            "CSP only. It does not prove NP-hardness, polynomiality, or global "
            "solver correctness."
        ),
    }
    return {
        "method": "p3_block_functional_relation_chain_probe",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3,4")
    parser.add_argument(
        "--instance-kinds",
        default=",".join(DEFAULT_INSTANCE_KINDS),
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--assignment-limit", type=int, default=250000)
    parser.add_argument("--component-product-limit", type=int, default=100000)
    parser.add_argument("--output", default="reports/relation_chain_probe.json")
    args = parser.parse_args(argv)

    report = run_relation_chain_probe(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
        assignment_limit=args.assignment_limit,
        component_product_limit=args.component_product_limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
