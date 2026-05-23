#!/usr/bin/env python3
"""Find minimal interaction UNSAT cores in materialized relation CSPs."""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    _path_to_string,
)
from tools.pc_relation_chain_probe import (  # noqa: E402
    DEFAULT_INSTANCE_KINDS,
    _count_assignments,
    _domain_product,
    _relation_shape,
    _signature_accepts,
)


def _path_key(path: tuple[int, ...]) -> str:
    return _path_to_string(path)


def _signature_indices(domains: dict, scope: Sequence[tuple[int, ...]], signature) -> list[int]:
    by_path = dict(signature)
    return [domains[path].index(by_path[path]) for path in scope]


def _all_scope_signatures(domains: dict, scope: Sequence[tuple[int, ...]]) -> set:
    return {
        tuple(zip(scope, values))
        for values in product(*(domains[path] for path in scope))
    }


def _raw_accepted_index_tuples(domains: dict, relation: dict) -> list[list[int]]:
    return [
        _signature_indices(domains, relation["scope"], signature)
        for signature in relation.get("accepted_signatures", ())
    ]


def _assignment_indices(domains: dict, assignment: dict) -> dict[str, int]:
    return {
        _path_key(path): domains[path].index(assignment[path])
        for path in sorted(assignment)
    }


def _first_satisfying_assignment(
    assignments: Sequence[dict],
    domains: dict,
    relations,
) -> dict | None:
    for assignment in assignments:
        if all(_signature_accepts(relation, assignment) for relation in relations):
            return _assignment_indices(domains, assignment)
    return None


def _relation_summary(domains: dict, index: int, relation: dict) -> dict:
    shape, tags, profile = _relation_shape(relation)
    row = {
        "relation_index": index,
        "relation_kind": relation["relation_kind"],
        "shape": shape,
        "shape_tags": tags,
        "scope": [_path_key(path) for path in relation["scope"]],
        "arity": relation["arity"],
        "domain_sizes": [len(domains[path]) for path in relation["scope"]],
        "domain_product": relation["domain_product"],
        "accepted_signature_count": relation["accepted_signature_count"],
        "rejected_signature_count": relation["rejected_signature_count"],
        "quartet_count": relation["quartet_count"],
        "quartets": [list(quartet) for quartet in relation["quartets"]],
        "accepted_index_tuples": _raw_accepted_index_tuples(domains, relation),
    }
    if profile is not None:
        row.update(
            {
                "catalog_hash": profile["catalog_hash"],
                "density": profile["density"],
                "left_functional": profile["left_functional"],
                "right_functional": profile["right_functional"],
                "canonical_accepted_index_tuples": profile.get("accepted_index_tuples"),
            }
        )
    return row


def _proper_subsets_satisfiable(
    *,
    assignments: Sequence[dict],
    relations: Sequence[dict],
    core: Sequence[int],
) -> bool:
    if len(core) <= 1:
        return True
    for size in range(1, len(core)):
        for subset in combinations(core, size):
            if _count_assignments(assignments, [relations[index] for index in subset]) == 0:
                return False
    return True


def _projection_conflicts(
    domains: dict,
    relations: Sequence[dict],
    core: Sequence[int],
) -> list[dict]:
    conflicts = []
    core_relations = {index: relations[index] for index in core}
    unary_by_path = {
        (index, relation["scope"][0]): {
            values[0] for values in _raw_accepted_index_tuples(domains, relation)
        }
        for index, relation in core_relations.items()
        if relation["arity"] == 1
    }
    for binary_index, binary in core_relations.items():
        if binary["arity"] != 2:
            continue
        raw_tuples = _raw_accepted_index_tuples(domains, binary)
        for side, path in enumerate(binary["scope"]):
            projection = {values[side] for values in raw_tuples}
            for (unary_index, unary_path), unary_values in unary_by_path.items():
                if unary_path != path:
                    continue
                intersection = sorted(projection & unary_values)
                if len(intersection) == 0:
                    status = "empty_intersection"
                elif len(intersection) == len(projection):
                    status = "binary_projection_contained_in_unary"
                else:
                    status = "partial_intersection"
                conflicts.append(
                    {
                        "binary_relation_index": binary_index,
                        "unary_relation_index": unary_index,
                        "variable": _path_key(path),
                        "side": side,
                        "binary_projection_indices": sorted(projection),
                        "unary_accepted_indices": sorted(unary_values),
                        "intersection_indices": intersection,
                        "intersection_size": len(intersection),
                        "status": status,
                    }
                )
    return conflicts


def _source_quartet_rows_by_key(relation_report: dict) -> dict:
    rows = {}
    for relation in relation_report["quartet_relations"]:
        if "accepted_signatures" not in relation:
            continue
        rows[(tuple(relation["scope"]), tuple(relation["quartet"]))] = relation
    return rows


def _relation_with_removed_source_quartet(
    *,
    domains: dict,
    relation: dict,
    quartet_rows: dict,
    removed_quartet: tuple[int, ...],
) -> dict:
    scope = tuple(relation["scope"])
    source_quartets = [
        tuple(quartet)
        for quartet in relation["quartets"]
        if tuple(quartet) != removed_quartet
    ]
    if source_quartets:
        accepted = _all_scope_signatures(domains, scope)
        for quartet in source_quartets:
            source = quartet_rows[(scope, quartet)]
            accepted &= set(source["accepted_signatures"])
    else:
        accepted = _all_scope_signatures(domains, scope)

    replacement = dict(relation)
    replacement["accepted_signatures"] = tuple(sorted(accepted))
    replacement["accepted_signature_count"] = len(accepted)
    replacement["rejected_signature_count"] = replacement["domain_product"] - len(accepted)
    replacement["quartets"] = tuple(source_quartets)
    replacement["quartet_count"] = len(source_quartets)
    return replacement


def _quartet_removal_checks(
    *,
    assignments: Sequence[dict],
    domains: dict,
    relation_report: dict,
    relations: Sequence[dict],
    core: Sequence[int],
) -> list[dict]:
    quartet_rows = _source_quartet_rows_by_key(relation_report)
    checks = []
    for relation_index in core:
        relation = relations[relation_index]
        for quartet in relation["quartets"]:
            replacement = _relation_with_removed_source_quartet(
                domains=domains,
                relation=relation,
                quartet_rows=quartet_rows,
                removed_quartet=tuple(quartet),
            )
            reduced = [
                replacement if index == relation_index else relations[index]
                for index in core
            ]
            count = _count_assignments(assignments, reduced)
            checks.append(
                {
                    "relation_index": relation_index,
                    "removed_quartet": list(quartet),
                    "satisfying_assignment_count": count,
                    "sample_assignment": _first_satisfying_assignment(
                        assignments,
                        domains,
                        reduced,
                    ),
                }
            )
    return checks


def _minimal_unsat_cores(
    *,
    assignments: Sequence[dict],
    relations: Sequence[dict],
    max_core_size: int,
    max_cores: int,
) -> list[tuple[int, ...]]:
    restrictive_indices = [
        index
        for index, relation in enumerate(relations)
        if relation["accepted_signature_count"] < relation["domain_product"]
    ]
    for size in range(1, min(max_core_size, len(restrictive_indices)) + 1):
        cores = []
        for candidate in combinations(restrictive_indices, size):
            subset = [relations[index] for index in candidate]
            if _count_assignments(assignments, subset) == 0:
                cores.append(candidate)
                if len(cores) >= max_cores:
                    return cores
        if cores:
            return cores
    return []


def _row_from_relation_report(
    *,
    block_count: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    seconds: float,
    relation_report: dict,
    assignment_limit: int,
    max_core_size: int,
    max_cores_per_row: int,
) -> dict:
    domains = relation_report["encoding"]["domains"]
    relations = relation_report["merged_relations"]
    base = {
        "block_count": block_count,
        "n": 3 * block_count,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": relation_report["complete"],
        "row_class": relation_report["row_class"],
        "validation_mismatch_count": relation_report["counts"]["validation_mismatch_count"],
    }
    if not relation_report["complete"]:
        return {**base, "incomplete_reason": relation_report["row_class"]}

    assignment_space = _domain_product(domains, list(domains))
    if assignment_space > assignment_limit:
        return {
            **base,
            "assignment_space": assignment_space,
            "assignment_limit": assignment_limit,
            "assignment_incomplete": True,
            "minimal_core_count": 0,
        }

    assignments = list(iter_local_assignments(relation_report["encoding"]))
    binary_non_boolean = [
        relation for relation in relations if relation["relation_kind"] == "binary_non_boolean_catalog"
    ]
    parasite_relations = [
        relation for relation in relations if relation["relation_kind"] != "binary_non_boolean_catalog"
    ]
    constant_reject_count = sum(
        1 for relation in relations if relation["relation_kind"] == "constant_reject"
    )
    full_accept_count = _count_assignments(assignments, relations)
    binary_accept_count = _count_assignments(assignments, binary_non_boolean)
    parasite_accept_count = _count_assignments(assignments, parasite_relations)
    interaction_unsat = (
        full_accept_count == 0
        and constant_reject_count == 0
        and binary_accept_count > 0
        and parasite_accept_count > 0
    )

    cores = []
    if interaction_unsat:
        for core in _minimal_unsat_cores(
            assignments=assignments,
            relations=relations,
            max_core_size=max_core_size,
            max_cores=max_cores_per_row,
        ):
            core_relations = [relations[index] for index in core]
            removal_checks = []
            for index in core:
                reduced = [relations[other] for other in core if other != index]
                removal_checks.append(
                    {
                        "removed_relation_index": index,
                        "satisfying_assignment_count": _count_assignments(assignments, reduced),
                        "sample_assignment": _first_satisfying_assignment(
                            assignments,
                            domains,
                            reduced,
                        ),
                    }
                )
            cores.append(
                {
                    "relation_indices": list(core),
                    "size": len(core),
                    "variables": sorted(
                        {
                            _path_key(path)
                            for index in core
                            for path in relations[index]["scope"]
                        }
                    ),
                    "variable_count": len(
                        {
                            path
                            for index in core
                            for path in relations[index]["scope"]
                        }
                    ),
                    "core_assignment_space": _domain_product(
                        domains,
                        sorted(
                            {
                                path
                                for index in core
                                for path in relations[index]["scope"]
                            }
                        ),
                    ),
                    "core_quartet_count": sum(
                        relations[index]["quartet_count"] for index in core
                    ),
                    "relation_kinds": [relations[index]["relation_kind"] for index in core],
                    "relation_shapes": [_relation_shape(relations[index])[0] for index in core],
                    "core_accept_count": _count_assignments(assignments, core_relations),
                    "proper_subsets_satisfiable": _proper_subsets_satisfiable(
                        assignments=assignments,
                        relations=relations,
                        core=core,
                    ),
                    "projection_conflicts": _projection_conflicts(domains, relations, core),
                    "proper_removal_checks": removal_checks,
                    "source_quartet_removal_checks": _quartet_removal_checks(
                        assignments=assignments,
                        domains=domains,
                        relation_report=relation_report,
                        relations=relations,
                        core=core,
                    ),
                    "relations": [
                        _relation_summary(domains, index, relations[index])
                        for index in core
                    ],
                }
            )

    return {
        **base,
        "assignment_space": assignment_space,
        "assignment_limit": assignment_limit,
        "assignment_incomplete": False,
        "relation_count": len(relations),
        "constant_reject_count": constant_reject_count,
        "full_accept_count": full_accept_count,
        "binary_non_boolean_accept_count": binary_accept_count,
        "parasite_accept_count": parasite_accept_count,
        "interaction_unsat": interaction_unsat,
        "minimal_core_count": len(cores),
        "minimal_core_size": min((core["size"] for core in cores), default=None),
        "minimal_cores": cores,
        "promise_status": "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D",
        "interpretation": (
            "Minimal core in the materialized relation CSP only; not a global "
            "negative certificate for PC-tree circular Robinson existence."
        ),
    }


def run_relation_unsat_core_probe(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str],
    repeats: int = 8,
    seed: int = 20260550,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
    assignment_limit: int = 250000,
    max_core_size: int = 6,
    max_cores_per_row: int = 3,
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
                        max_core_size=max_core_size,
                        max_cores_per_row=max_cores_per_row,
                    )
                )

    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "assignment_incomplete_rows": sum(1 for row in rows if row.get("assignment_incomplete")),
        "interaction_unsat_rows": sum(1 for row in rows if row.get("interaction_unsat")),
        "rows_with_minimal_core": sum(1 for row in rows if row.get("minimal_core_count", 0) > 0),
        "min_core_size": min(
            (
                row["minimal_core_size"]
                for row in rows
                if row.get("minimal_core_size") is not None
            ),
            default=None,
        ),
        "constant_reject_rows": sum(1 for row in rows if row.get("constant_reject_count", 0) > 0),
        "promise_caveat": (
            "The probe uses scaffold PC-trees; it does not prove these are "
            "the Hsu/McConnell quasi-circular PC-tree for D."
        ),
        "interpretation": (
            "This report minimizes UNSAT cores in the materialized relation CSP "
            "only. It does not prove NP-hardness, polynomiality, or global "
            "solver correctness."
        ),
    }
    return {
        "method": "p3_block_relation_unsat_core_probe",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3")
    parser.add_argument(
        "--instance-kinds",
        default=",".join(DEFAULT_INSTANCE_KINDS),
    )
    parser.add_argument("--repeats", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260550)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--assignment-limit", type=int, default=250000)
    parser.add_argument("--max-core-size", type=int, default=6)
    parser.add_argument("--max-cores-per-row", type=int, default=3)
    parser.add_argument("--output", default="reports/relation_unsat_core_probe.json")
    args = parser.parse_args(argv)

    report = run_relation_unsat_core_probe(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
        assignment_limit=args.assignment_limit,
        max_core_size=args.max_core_size,
        max_cores_per_row=args.max_cores_per_row,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
