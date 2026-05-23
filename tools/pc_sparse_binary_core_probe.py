#!/usr/bin/env python3
"""Inspect sparse binary zero components and constant suppression."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict, deque
from itertools import combinations, product
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
    _instance,
    _parse_ints,
    _parse_strings,
)
from tools.pc_relation_chain_probe import DEFAULT_INSTANCE_KINDS  # noqa: E402
from tools.pc_relation_unsat_core_probe import (  # noqa: E402
    _first_satisfying_assignment,
    _relation_with_removed_source_quartet,
    _source_quartet_rows_by_key,
)
from tools.pc_sparse_matching_conflict_probe import (  # noqa: E402
    _accepted_index_tuples,
    _count_assignments,
    _domain_product,
    _histogram,
    _path_key,
    _relation_shape,
    _signature_accepts,
    _sparse_relation_summary,
)


def _assignment_indices(domains: dict, assignment: dict) -> dict[str, int]:
    return {
        _path_key(path): domains[path].index(assignment[path])
        for path in sorted(assignment)
    }


def _component_assignments(domains: dict, variables: Sequence[tuple[int, ...]]) -> list[dict]:
    return [
        dict(zip(variables, values))
        for values in product(*(domains[variable] for variable in variables))
    ]


def _sparse_relation_indices(relations: Sequence[dict]) -> list[int]:
    indices = []
    for index, relation in enumerate(relations):
        shape, _tags, _profile = _relation_shape(relation)
        if shape == "sparse_partial_matching":
            indices.append(index)
    return indices


def _sparse_components_with_indices(
    *,
    domains: dict,
    relations: Sequence[dict],
    sparse_indices: Sequence[int],
    component_product_limit: int,
) -> tuple[list[dict], bool]:
    adjacency: dict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    edges = []
    for index in sparse_indices:
        relation = relations[index]
        left, right = relation["scope"]
        adjacency[left].add(right)
        adjacency[right].add(left)
        edges.append((left, right, index))

    components = []
    incomplete = False
    seen: set[tuple[int, ...]] = set()
    for start in sorted(adjacency):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        nodes = []
        while queue:
            node = queue.popleft()
            nodes.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        node_set = set(nodes)
        component_indices = [
            index for left, right, index in edges if left in node_set and right in node_set
        ]
        variables = sorted(nodes)
        domain_product = _domain_product(domains, variables)
        component_incomplete = domain_product > component_product_limit
        accept_count = None
        if component_incomplete:
            incomplete = True
        else:
            assignments = _component_assignments(domains, variables)
            accept_count = _count_assignments(
                assignments,
                [relations[index] for index in component_indices],
            )

        components.append(
            {
                "variables_raw": variables,
                "relation_indices": component_indices,
                "node_count": len(variables),
                "edge_count": len(component_indices),
                "domain_product": domain_product,
                "incomplete": component_incomplete,
                "accept_count": accept_count,
                "zero_accept": accept_count == 0 if accept_count is not None else False,
            }
        )
    return components, incomplete


def _projection_for_relation(domains: dict, relation: dict, variable: tuple[int, ...]) -> list[int]:
    raw_tuples = _accepted_index_tuples(domains, relation)
    side = relation["scope"].index(variable)
    return sorted({values[side] for values in raw_tuples})


def _shared_projection_conflicts(domains: dict, relations: Sequence[dict]) -> list[dict]:
    conflicts = []
    for left_index, right_index in combinations(range(len(relations)), 2):
        left = relations[left_index]
        right = relations[right_index]
        for variable in sorted(set(left["scope"]) & set(right["scope"])):
            left_projection = _projection_for_relation(domains, left, variable)
            right_projection = _projection_for_relation(domains, right, variable)
            intersection = sorted(set(left_projection) & set(right_projection))
            conflicts.append(
                {
                    "left_component_relation_index": left_index,
                    "right_component_relation_index": right_index,
                    "variable": _path_key(variable),
                    "left_relation_index": left["relation_index_for_probe"],
                    "right_relation_index": right["relation_index_for_probe"],
                    "left_projection_indices": left_projection,
                    "right_projection_indices": right_projection,
                    "intersection_indices": intersection,
                    "intersection_size": len(intersection),
                    "status": "empty_intersection" if not intersection else "non_empty",
                }
            )
    return conflicts


def _first_assignment_count(
    assignments: Sequence[dict],
    domains: dict,
    relations: Sequence[dict],
) -> dict | None:
    witness = _first_satisfying_assignment(assignments, domains, relations)
    if witness is not None:
        return witness
    for assignment in assignments:
        if all(_signature_accepts(relation, assignment) for relation in relations):
            return _assignment_indices(domains, assignment)
    return None


def _proper_relation_removal_checks(
    *,
    assignments: Sequence[dict],
    domains: dict,
    relations: Sequence[dict],
) -> list[dict]:
    checks = []
    for local_index, relation in enumerate(relations):
        reduced = [other for index, other in enumerate(relations) if index != local_index]
        count = _count_assignments(assignments, reduced)
        checks.append(
            {
                "removed_component_relation_index": local_index,
                "removed_relation_index": relation["relation_index_for_probe"],
                "satisfying_assignment_count": count,
                "sample_assignment": _first_assignment_count(assignments, domains, reduced),
            }
        )
    return checks


def _source_quartet_removal_checks(
    *,
    assignments: Sequence[dict],
    domains: dict,
    relation_report: dict,
    all_relations: Sequence[dict],
    component_indices: Sequence[int],
) -> list[dict]:
    quartet_rows = _source_quartet_rows_by_key(relation_report)
    component_relations = [all_relations[index] for index in component_indices]
    checks = []
    for local_index, relation_index in enumerate(component_indices):
        relation = all_relations[relation_index]
        for quartet in relation["quartets"]:
            replacement = _relation_with_removed_source_quartet(
                domains=domains,
                relation=relation,
                quartet_rows=quartet_rows,
                removed_quartet=tuple(quartet),
            )
            reduced = [
                replacement if index == local_index else component_relations[index]
                for index in range(len(component_relations))
            ]
            count = _count_assignments(assignments, reduced)
            checks.append(
                {
                    "relation_index": relation_index,
                    "component_relation_index": local_index,
                    "removed_quartet": list(quartet),
                    "satisfying_assignment_count": count,
                    "sample_assignment": _first_assignment_count(assignments, domains, reduced),
                }
            )
    return checks


def _zero_component_details(
    *,
    domains: dict,
    relation_report: dict,
    relations: Sequence[dict],
    component: dict,
) -> dict:
    variables = component["variables_raw"]
    component_indices = component["relation_indices"]
    assignments = _component_assignments(domains, variables)
    component_relations = []
    for index in component_indices:
        relation = dict(relations[index])
        relation["relation_index_for_probe"] = index
        component_relations.append(relation)

    projection_conflicts = _shared_projection_conflicts(domains, component_relations)
    relation_removal_checks = _proper_relation_removal_checks(
        assignments=assignments,
        domains=domains,
        relations=component_relations,
    )
    quartet_removal_checks = _source_quartet_removal_checks(
        assignments=assignments,
        domains=domains,
        relation_report=relation_report,
        all_relations=relations,
        component_indices=component_indices,
    )
    return {
        "nodes": [_path_key(variable) for variable in variables],
        "node_count": component["node_count"],
        "edge_count": component["edge_count"],
        "domain_product": component["domain_product"],
        "accept_count": component["accept_count"],
        "zero_accept": component["zero_accept"],
        "relation_indices": list(component_indices),
        "empty_shared_projection_conflict_count": sum(
            1 for conflict in projection_conflicts if conflict["status"] == "empty_intersection"
        ),
        "proper_relation_removal_all_sat": all(
            check["satisfying_assignment_count"] > 0 for check in relation_removal_checks
        ),
        "source_quartet_removal_restores_some": any(
            check["satisfying_assignment_count"] > 0 for check in quartet_removal_checks
        ),
        "shared_projection_conflicts": projection_conflicts,
        "proper_relation_removal_checks": relation_removal_checks,
        "source_quartet_removal_checks": quartet_removal_checks,
        "relations": [
            _sparse_relation_summary(domains, index, relations[index])
            for index in component_indices
        ],
    }


def _row_class(*, zero_count: int, constant_reject_count: int) -> str:
    if zero_count == 0:
        return "no_sparse_zero_component"
    if constant_reject_count:
        return "sparse_zero_with_constant_reject"
    return "sparse_zero_without_constant_reject"


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
    sparse_indices = _sparse_relation_indices(relations)
    components, component_incomplete = _sparse_components_with_indices(
        domains=domains,
        relations=relations,
        sparse_indices=sparse_indices,
        component_product_limit=component_product_limit,
    )
    zero_components_raw = [
        component
        for component in components
        if component["zero_accept"] and not component["incomplete"]
    ]
    zero_components = [
        _zero_component_details(
            domains=domains,
            relation_report=relation_report,
            relations=relations,
            component=component,
        )
        for component in zero_components_raw
    ]

    constant_reject_count = sum(
        1 for relation in relations if relation["relation_kind"] == "constant_reject"
    )
    constant_relations = [
        relation for relation in relations if relation["relation_kind"] == "constant_reject"
    ]
    non_constant_relations = [
        relation for relation in relations if relation["relation_kind"] != "constant_reject"
    ]
    sparse_relations = [relations[index] for index in sparse_indices]
    assignment_space = _domain_product(domains, list(domains))
    assignment_incomplete = assignment_space > assignment_limit
    full_accept_count = None
    no_constant_accept_count = None
    constants_only_accept_count = None
    sparse_accept_count = None
    if not assignment_incomplete:
        assignments = list(iter_local_assignments(relation_report["encoding"]))
        full_accept_count = _count_assignments(assignments, relations)
        no_constant_accept_count = _count_assignments(assignments, non_constant_relations)
        constants_only_accept_count = _count_assignments(assignments, constant_relations)
        sparse_accept_count = _count_assignments(assignments, sparse_relations)

    row_class = _row_class(
        zero_count=len(zero_components),
        constant_reject_count=constant_reject_count,
    )
    return {
        **base,
        "row_class": row_class,
        "assignment_space": assignment_space,
        "assignment_incomplete": assignment_incomplete,
        "full_accept_count": full_accept_count,
        "no_constant_accept_count": no_constant_accept_count,
        "constants_only_accept_count": constants_only_accept_count,
        "sparse_accept_count": sparse_accept_count,
        "sparse_relation_count": len(sparse_indices),
        "sparse_component_count": len(components),
        "sparse_component_incomplete": component_incomplete,
        "sparse_zero_component_count": len(zero_components),
        "constant_reject_count": constant_reject_count,
        "non_constant_relation_count": len(non_constant_relations),
        "zero_component_edge_histogram": _histogram(
            [str(component["edge_count"]) for component in zero_components]
        ),
        "zero_component_all_relation_removal_sat": all(
            component["proper_relation_removal_all_sat"] for component in zero_components
        )
        if zero_components
        else None,
        "zero_component_has_empty_shared_projection": any(
            component["empty_shared_projection_conflict_count"] > 0
            for component in zero_components
        ),
        "zero_components": zero_components,
        "promise_status": "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D",
        "interpretation": (
            "Sparse binary core diagnostic in the materialized relation CSP only; "
            "constant-free zero components would be gadget candidates, not proofs."
        ),
    }


def run_sparse_binary_core_probe(
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

    zero_rows = [row for row in rows if row.get("sparse_zero_component_count", 0) > 0]
    row_classes = [row.get("row_class", "incomplete") for row in rows]
    by_instance_kind = {}
    for instance_kind in instance_kinds:
        kind_rows = [row for row in rows if row["instance_kind"] == instance_kind]
        by_instance_kind[instance_kind] = {
            "rows": len(kind_rows),
            "zero_sparse_component_rows": sum(
                1 for row in kind_rows if row.get("sparse_zero_component_count", 0) > 0
            ),
            "constant_free_zero_sparse_rows": sum(
                1
                for row in kind_rows
                if row.get("sparse_zero_component_count", 0) > 0
                and row.get("constant_reject_count", 0) == 0
            ),
            "constant_reject_rows": sum(
                1 for row in kind_rows if row.get("constant_reject_count", 0) > 0
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
        "rows_with_sparse_zero_component": len(zero_rows),
        "zero_sparse_component_instances": sum(
            row.get("sparse_zero_component_count", 0) for row in rows
        ),
        "constant_free_zero_sparse_rows": sum(
            1 for row in zero_rows if row.get("constant_reject_count", 0) == 0
        ),
        "zero_sparse_rows_with_constant_reject": sum(
            1 for row in zero_rows if row.get("constant_reject_count", 0) > 0
        ),
        "zero_sparse_rows_no_constant_unsat": sum(
            1
            for row in zero_rows
            if row.get("no_constant_accept_count") == 0
            and not row.get("assignment_incomplete")
        ),
        "zero_sparse_components_with_empty_shared_projection": sum(
            1
            for row in rows
            for component in row.get("zero_components", [])
            if component["empty_shared_projection_conflict_count"] > 0
        ),
        "zero_sparse_components_all_relation_removal_sat": sum(
            1
            for row in rows
            for component in row.get("zero_components", [])
            if component["proper_relation_removal_all_sat"]
        ),
        "max_zero_component_edges": max(
            (
                component["edge_count"]
                for row in rows
                for component in row.get("zero_components", [])
            ),
            default=0,
        ),
        "row_class_histogram": _histogram(row_classes),
        "by_instance_kind": by_instance_kind,
        "promise_caveat": (
            "The probe uses scaffold PC-trees; it does not prove these are the "
            "Hsu/McConnell quasi-circular PC-tree for D."
        ),
        "interpretation": (
            "A constant-free sparse zero component would be a stronger gadget "
            "candidate. Components accompanied by constant_reject remain "
            "diagnostics, not hardness evidence."
        ),
    }
    return {
        "method": "p3_block_sparse_binary_core_probe",
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
    parser.add_argument("--output", default="reports/sparse_binary_core_probe.json")
    args = parser.parse_args(argv)

    report = run_sparse_binary_core_probe(
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
