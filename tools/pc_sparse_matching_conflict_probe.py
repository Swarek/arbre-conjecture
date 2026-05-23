#!/usr/bin/env python3
"""Probe sparse-partial-matching relations and unary projection conflicts."""

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
from tools.pc_relation_chain_probe import DEFAULT_INSTANCE_KINDS  # noqa: E402
from tools.pc_relation_shape_search import classify_relation_shape  # noqa: E402


UNARY_KINDS = {"unary_boolean", "unary_non_boolean"}


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _path_key(path: tuple[int, ...]) -> str:
    return _path_to_string(path)


def _signature_accepts(relation: dict, assignment: dict) -> bool:
    signature = tuple((path, assignment[path]) for path in relation["scope"])
    return signature in relation["accepted_signatures"]


def _count_assignments(assignments: Sequence[dict], relations: Sequence[dict]) -> int:
    if not relations:
        return len(assignments)
    count = 0
    for assignment in assignments:
        if all(_signature_accepts(relation, assignment) for relation in relations):
            count += 1
    return count


def _domain_product(domains: dict, variables: Sequence[tuple[int, ...]]) -> int:
    value = 1
    for variable in variables:
        value *= len(domains[variable])
    return value


def _accepted_index_tuples(domains: dict, relation: dict) -> list[list[int]]:
    tuples = []
    for signature in relation.get("accepted_signatures", ()):
        by_path = dict(signature)
        tuples.append(
            [domains[path].index(by_path[path]) for path in relation["scope"]]
        )
    return tuples


def _unary_accepted_indices(domains: dict, relation: dict) -> set[int]:
    return {values[0] for values in _accepted_index_tuples(domains, relation)}


def _relation_shape(relation: dict) -> tuple[str, list[str], dict | None]:
    if relation["relation_kind"] != "binary_non_boolean_catalog":
        return relation["relation_kind"], [], None
    profile = _binary_relation_profile(relation)
    shape, tags = classify_relation_shape(profile)
    return shape, tags, profile


def _sparse_relation_summary(domains: dict, index: int, relation: dict) -> dict:
    shape, tags, profile = _relation_shape(relation)
    assert profile is not None
    raw_tuples = _accepted_index_tuples(domains, relation)
    projections = []
    for side, path in enumerate(relation["scope"]):
        projections.append(
            {
                "variable": _path_key(path),
                "side": side,
                "indices": sorted({values[side] for values in raw_tuples}),
            }
        )
    return {
        "relation_index": index,
        "shape": shape,
        "shape_tags": tags,
        "catalog_hash": profile["catalog_hash"],
        "scope": [_path_key(path) for path in relation["scope"]],
        "domain_sizes": profile["domain_sizes"],
        "accepted_signature_count": profile["accepted_signature_count"],
        "density": profile["density"],
        "accepted_index_tuples": raw_tuples,
        "canonical_accepted_index_tuples": profile.get("accepted_index_tuples"),
        "projections": projections,
        "quartet_count": relation["quartet_count"],
        "quartets": [list(quartet) for quartet in relation["quartets"]],
    }


def _unary_summary(domains: dict, index: int, relation: dict) -> dict:
    return {
        "relation_index": index,
        "relation_kind": relation["relation_kind"],
        "variable": _path_key(relation["scope"][0]),
        "accepted_indices": sorted(_unary_accepted_indices(domains, relation)),
        "domain_size": len(domains[relation["scope"][0]]),
        "accepted_signature_count": relation["accepted_signature_count"],
        "quartet_count": relation["quartet_count"],
        "quartets": [list(quartet) for quartet in relation["quartets"]],
    }


def _sparse_unary_conflicts(
    *,
    domains: dict,
    sparse_relations: Sequence[tuple[int, dict]],
    unary_relations: Sequence[tuple[int, dict]],
) -> list[dict]:
    unaries_by_path: dict[tuple[int, ...], list[tuple[int, dict, set[int]]]] = defaultdict(list)
    for index, relation in unary_relations:
        unaries_by_path[relation["scope"][0]].append(
            (index, relation, _unary_accepted_indices(domains, relation))
        )

    conflicts = []
    for sparse_index, sparse in sparse_relations:
        raw_tuples = _accepted_index_tuples(domains, sparse)
        for side, path in enumerate(sparse["scope"]):
            projection = {values[side] for values in raw_tuples}
            for unary_index, unary, unary_values in unaries_by_path.get(path, []):
                intersection = sorted(projection & unary_values)
                if not intersection:
                    status = "empty_intersection"
                elif len(intersection) == len(projection):
                    status = "projection_contained_in_unary"
                else:
                    status = "partial_intersection"
                conflicts.append(
                    {
                        "sparse_relation_index": sparse_index,
                        "unary_relation_index": unary_index,
                        "variable": _path_key(path),
                        "side": side,
                        "sparse_projection_indices": sorted(projection),
                        "unary_accepted_indices": sorted(unary_values),
                        "intersection_indices": intersection,
                        "intersection_size": len(intersection),
                        "status": status,
                        "sparse_relation": _sparse_relation_summary(
                            domains,
                            sparse_index,
                            sparse,
                        ),
                        "unary_relation": _unary_summary(domains, unary_index, unary),
                    }
                )
    return conflicts


def _sparse_components(
    *,
    domains: dict,
    sparse_relations: Sequence[tuple[int, dict]],
    component_product_limit: int,
) -> tuple[list[dict], bool]:
    adjacency: dict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    edges: list[tuple[tuple[int, ...], tuple[int, ...], int, dict]] = []
    for index, relation in sparse_relations:
        left, right = relation["scope"]
        adjacency[left].add(right)
        adjacency[right].add(left)
        edges.append((left, right, index, relation))

    components = []
    incomplete = False
    seen: set[tuple[int, ...]] = set()
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
        component_edges = [
            (index, relation)
            for left, right, index, relation in edges
            if left in node_set and right in node_set
        ]
        domain_product = _domain_product(domains, nodes)
        component_incomplete = domain_product > component_product_limit
        accept_count = None
        if component_incomplete:
            incomplete = True
        else:
            accept_count = 0
            for values in product(*(domains[node] for node in nodes)):
                assignment = dict(zip(nodes, values))
                if all(_signature_accepts(relation, assignment) for _, relation in component_edges):
                    accept_count += 1

        components.append(
            {
                "nodes": [_path_key(node) for node in sorted(nodes)],
                "node_count": len(nodes),
                "edge_count": len(component_edges),
                "multi_edge": len(component_edges) >= 2,
                "domain_product": domain_product,
                "accept_count": accept_count,
                "zero_accept": accept_count == 0 if accept_count is not None else False,
                "incomplete": component_incomplete,
                "relations": [
                    _sparse_relation_summary(domains, index, relation)
                    for index, relation in component_edges
                ],
            }
        )
    return components, incomplete


def _row_class(
    *,
    sparse_count: int,
    empty_conflict_count: int,
    sparse_zero_component_count: int,
    constant_reject_count: int,
) -> str:
    if sparse_count == 0:
        return "no_sparse_partial_matching"
    if sparse_zero_component_count:
        return "sparse_binary_component_unsat"
    if empty_conflict_count and constant_reject_count == 0:
        return "sparse_unary_empty_conflict_without_constant"
    if empty_conflict_count:
        return "sparse_unary_empty_conflict_with_constant"
    return "sparse_without_empty_unary_conflict"


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
    base = {
        "block_count": block_count,
        "n": 3 * block_count,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": relation_report["complete"],
        "source_row_class": relation_report["row_class"],
        "validation_mismatch_count": relation_report["counts"]["validation_mismatch_count"],
    }
    if not relation_report["complete"]:
        return {**base, "row_class": relation_report["row_class"]}

    domains = relation_report["encoding"]["domains"]
    relations = relation_report["merged_relations"]
    sparse_relations = []
    binary_non_boolean = []
    shape_counter: Counter[str] = Counter()
    for index, relation in enumerate(relations):
        shape, _tags, _profile = _relation_shape(relation)
        if relation["relation_kind"] == "binary_non_boolean_catalog":
            binary_non_boolean.append((index, relation))
            shape_counter[shape] += 1
        if shape == "sparse_partial_matching":
            sparse_relations.append((index, relation))

    unary_relations = [
        (index, relation)
        for index, relation in enumerate(relations)
        if relation["relation_kind"] in UNARY_KINDS
    ]
    constant_reject_count = sum(
        1 for relation in relations if relation["relation_kind"] == "constant_reject"
    )
    high_arity_count = sum(1 for relation in relations if relation["arity"] > 2)
    conflicts = _sparse_unary_conflicts(
        domains=domains,
        sparse_relations=sparse_relations,
        unary_relations=unary_relations,
    )
    empty_conflicts = [
        conflict for conflict in conflicts if conflict["status"] == "empty_intersection"
    ]
    components, component_incomplete = _sparse_components(
        domains=domains,
        sparse_relations=sparse_relations,
        component_product_limit=component_product_limit,
    )
    zero_components = [
        component
        for component in components
        if component["zero_accept"] and not component["incomplete"]
    ]
    assignment_space = _domain_product(domains, list(domains))
    assignment_incomplete = assignment_space > assignment_limit
    full_accept_count = None
    sparse_accept_count = None
    unary_accept_count = None
    if not assignment_incomplete:
        assignments = list(iter_local_assignments(relation_report["encoding"]))
        full_accept_count = _count_assignments(assignments, relations)
        sparse_accept_count = _count_assignments(
            assignments,
            [relation for _index, relation in sparse_relations],
        )
        unary_accept_count = _count_assignments(
            assignments,
            [relation for _index, relation in unary_relations],
        )

    row_class = _row_class(
        sparse_count=len(sparse_relations),
        empty_conflict_count=len(empty_conflicts),
        sparse_zero_component_count=len(zero_components),
        constant_reject_count=constant_reject_count,
    )

    return {
        **base,
        "row_class": row_class,
        "assignment_space": assignment_space,
        "assignment_incomplete": assignment_incomplete,
        "full_accept_count": full_accept_count,
        "sparse_accept_count": sparse_accept_count,
        "unary_accept_count": unary_accept_count,
        "binary_nonboolean_relation_count": len(binary_non_boolean),
        "binary_shape_histogram": {key: shape_counter[key] for key in sorted(shape_counter)},
        "sparse_relation_count": len(sparse_relations),
        "sparse_catalog_hashes": sorted(
            {
                _sparse_relation_summary(domains, index, relation)["catalog_hash"]
                for index, relation in sparse_relations
            }
        ),
        "unary_restrictive_count": len(unary_relations),
        "constant_reject_count": constant_reject_count,
        "high_arity_count": high_arity_count,
        "sparse_unary_conflict_count": len(conflicts),
        "empty_projection_conflict_count": len(empty_conflicts),
        "partial_projection_conflict_count": sum(
            1 for conflict in conflicts if conflict["status"] == "partial_intersection"
        ),
        "contained_projection_conflict_count": sum(
            1
            for conflict in conflicts
            if conflict["status"] == "projection_contained_in_unary"
        ),
        "sparse_component_count": len(components),
        "sparse_multi_edge_component_count": sum(
            1 for component in components if component["multi_edge"]
        ),
        "sparse_zero_component_count": len(zero_components),
        "sparse_component_incomplete": component_incomplete,
        "max_sparse_component_edges": max(
            (component["edge_count"] for component in components),
            default=0,
        ),
        "sparse_relations": [
            _sparse_relation_summary(domains, index, relation)
            for index, relation in sparse_relations
        ],
        "unary_relations": [
            _unary_summary(domains, index, relation)
            for index, relation in unary_relations
        ],
        "sparse_unary_conflicts": conflicts,
        "sparse_components": components,
        "promise_status": "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D",
        "interpretation": (
            "Sparse matching conflict diagnostic in the materialized scaffold only; "
            "not a proof of gadget composability, hardness, or promise validity."
        ),
    }


def run_sparse_matching_conflict_probe(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 8,
    seed: int = 20260550,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
    assignment_limit: int = 250_000,
    component_product_limit: int = 250_000,
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

    row_classes = [row.get("row_class", "incomplete") for row in rows]
    sparse_hashes = sorted(
        {
            catalog_hash
            for row in rows
            for catalog_hash in row.get("sparse_catalog_hashes", [])
        }
    )
    by_kind = {}
    for instance_kind in instance_kinds:
        kind_rows = [row for row in rows if row["instance_kind"] == instance_kind]
        by_kind[instance_kind] = {
            "rows": len(kind_rows),
            "sparse_rows": sum(1 for row in kind_rows if row.get("sparse_relation_count", 0) > 0),
            "empty_projection_conflict_rows": sum(
                1 for row in kind_rows if row.get("empty_projection_conflict_count", 0) > 0
            ),
            "constant_reject_rows": sum(
                1 for row in kind_rows if row.get("constant_reject_count", 0) > 0
            ),
            "sparse_zero_component_rows": sum(
                1 for row in kind_rows if row.get("sparse_zero_component_count", 0) > 0
            ),
        }

    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "assignment_incomplete_rows": sum(1 for row in rows if row.get("assignment_incomplete")),
        "sparse_rows": sum(1 for row in rows if row.get("sparse_relation_count", 0) > 0),
        "sparse_relation_instances": sum(row.get("sparse_relation_count", 0) for row in rows),
        "unique_sparse_hashes": len(sparse_hashes),
        "sparse_hashes": sparse_hashes,
        "rows_with_empty_projection_conflict": sum(
            1 for row in rows if row.get("empty_projection_conflict_count", 0) > 0
        ),
        "empty_projection_conflict_instances": sum(
            row.get("empty_projection_conflict_count", 0) for row in rows
        ),
        "rows_with_sparse_multi_edge_component": sum(
            1 for row in rows if row.get("sparse_multi_edge_component_count", 0) > 0
        ),
        "rows_with_sparse_zero_component": sum(
            1 for row in rows if row.get("sparse_zero_component_count", 0) > 0
        ),
        "max_sparse_component_edges": max(
            (row.get("max_sparse_component_edges", 0) for row in rows),
            default=0,
        ),
        "rows_with_constant_reject": sum(
            1 for row in rows if row.get("constant_reject_count", 0) > 0
        ),
        "row_class_histogram": _histogram(row_classes),
        "by_instance_kind": by_kind,
        "promise_caveat": (
            "The probe uses scaffold PC-trees; it does not prove these are the "
            "Hsu/McConnell quasi-circular PC-tree for D."
        ),
        "interpretation": (
            "Sparse matching conflicts are diagnostics in the materialized CSP. "
            "Unary-projection conflicts do not prove a composable hard gadget."
        ),
    }
    return {
        "method": "p3_block_sparse_partial_matching_conflict_probe",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3")
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260550)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--assignment-limit", type=int, default=250_000)
    parser.add_argument("--component-product-limit", type=int, default=250_000)
    parser.add_argument("--output", default="reports/sparse_matching_conflict_probe.json")
    args = parser.parse_args(argv)

    report = run_sparse_matching_conflict_probe(
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
