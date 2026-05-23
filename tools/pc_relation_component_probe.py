#!/usr/bin/env python3
"""Probe multi-edge components of all non-boolean binary P3 relations."""

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


DEFAULT_INSTANCE_KINDS = ("paired_farthest",)
UNARY_RESTRICTIVE_KINDS = {"unary_boolean", "unary_non_boolean"}


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _path_key(path: tuple[int, ...]) -> str:
    return _path_to_string(path)


def _relation_accepts(relation: dict, assignment: dict[tuple[int, ...], tuple[int, ...]]) -> bool:
    signature = tuple((path, assignment[path]) for path in relation["scope"])
    return signature in relation["accepted_signatures"]


def _domain_product(domains: dict, variables: Sequence[tuple[int, ...]]) -> int:
    value = 1
    for variable in variables:
        value *= len(domains[variable])
    return value


def _relation_summary(relation: dict) -> dict:
    profile = _binary_relation_profile(relation)
    shape, tags = classify_relation_shape(profile)
    return {
        "scope": [_path_key(path) for path in relation["scope"]],
        "shape": shape,
        "shape_tags": tags,
        "catalog_hash": profile["catalog_hash"],
        "domain_sizes": profile["domain_sizes"],
        "accepted_signature_count": profile["accepted_signature_count"],
        "density": profile["density"],
        "accepted_index_tuples": profile.get("accepted_index_tuples"),
        "quartet_count": relation["quartet_count"],
        "quartets": [list(quartet) for quartet in relation["quartets"]],
    }


def _binary_components(
    *,
    domains: dict,
    relations: Sequence[dict],
    component_product_limit: int,
) -> tuple[list[dict], bool]:
    adjacency: dict[tuple[int, ...], set[tuple[int, ...]]] = defaultdict(set)
    edges: list[tuple[tuple[int, ...], tuple[int, ...], dict]] = []
    for relation in relations:
        left, right = relation["scope"]
        adjacency[left].add(right)
        adjacency[right].add(left)
        edges.append((left, right, relation))

    incomplete = False
    components = []
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
        component_relations = [
            relation
            for left, right, relation in edges
            if left in node_set and right in node_set
        ]
        relation_summaries = [_relation_summary(relation) for relation in component_relations]
        shape_histogram = _histogram([item["shape"] for item in relation_summaries])
        domain_product = _domain_product(domains, nodes)
        component_incomplete = domain_product > component_product_limit
        accept_count = None
        if component_incomplete:
            incomplete = True
        else:
            accept_count = 0
            for values in product(*(domains[node] for node in nodes)):
                assignment = dict(zip(nodes, values))
                if all(_relation_accepts(relation, assignment) for relation in component_relations):
                    accept_count += 1

        components.append(
            {
                "nodes": [_path_key(node) for node in sorted(nodes)],
                "node_count": len(nodes),
                "edge_count": len(component_relations),
                "multi_edge": len(component_relations) >= 2,
                "cycle_like": len(component_relations) >= len(nodes),
                "domain_product": domain_product,
                "accept_count": accept_count,
                "zero_accept": accept_count == 0 if accept_count is not None else False,
                "incomplete": component_incomplete,
                "shape_histogram": shape_histogram,
                "shapes": sorted(shape_histogram),
                "relations": relation_summaries,
            }
        )
    return components, incomplete


def _row_class(
    *,
    has_binary: bool,
    has_multi_edge: bool,
    parasite_free: bool,
    full_accept_count: int | None,
) -> str:
    if not has_binary:
        return "no_binary_nonboolean_relations"
    if has_multi_edge and parasite_free and (full_accept_count or 0) > 0:
        return "multi_edge_parasite_free_sat"
    if has_multi_edge and parasite_free:
        return "multi_edge_parasite_free_unsat"
    if has_multi_edge:
        return "multi_edge_blocked_by_parasite"
    if parasite_free:
        return "isolated_binary_parasite_free"
    return "isolated_binary_blocked_by_parasite"


def _row_from_relation_report(
    *,
    block_count: int,
    instance_kind: str,
    repeat: int,
    seed: int,
    seconds: float,
    relation_report: dict,
    component_product_limit: int,
) -> dict:
    if not relation_report["complete"]:
        return {
            "block_count": block_count,
            "n": 3 * block_count,
            "instance_kind": instance_kind,
            "repeat": repeat,
            "seed": seed,
            "seconds": seconds,
            "complete": False,
            "validation_mismatch_count": relation_report["counts"][
                "validation_mismatch_count"
            ],
            "row_class": relation_report["row_class"],
            "incomplete_reason": relation_report["row_class"],
        }

    domains = relation_report["encoding"]["domains"]
    relations = relation_report["merged_relations"]
    binary_relations = [
        relation
        for relation in relations
        if relation["relation_kind"] == "binary_non_boolean_catalog"
    ]
    constant_reject_count = sum(
        1 for relation in relations if relation["relation_kind"] == "constant_reject"
    )
    unary_restrictive_count = sum(
        1 for relation in relations if relation["relation_kind"] in UNARY_RESTRICTIVE_KINDS
    )
    high_arity_count = sum(1 for relation in relations if relation["arity"] > 2)
    parasite_free = (
        constant_reject_count == 0
        and unary_restrictive_count == 0
        and high_arity_count == 0
    )
    components, component_incomplete = _binary_components(
        domains=domains,
        relations=binary_relations,
        component_product_limit=component_product_limit,
    )
    multi_components = [component for component in components if component["multi_edge"]]
    relation_summaries = [_relation_summary(relation) for relation in binary_relations]
    shape_histogram = _histogram([item["shape"] for item in relation_summaries])
    full_accept_count = relation_report["counts"]["relation_accept_assignments"]
    row_class = _row_class(
        has_binary=bool(binary_relations),
        has_multi_edge=bool(multi_components),
        parasite_free=parasite_free,
        full_accept_count=full_accept_count,
    )

    return {
        "block_count": block_count,
        "n": 3 * block_count,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": True,
        "validation_mismatch_count": relation_report["counts"]["validation_mismatch_count"],
        "row_class": row_class,
        "source_row_class": relation_report["row_class"],
        "relation_accept_assignments": full_accept_count,
        "direct_cr_assignments": relation_report["counts"]["direct_cr_assignments"],
        "binary_nonboolean_relation_count": len(binary_relations),
        "shape_histogram": shape_histogram,
        "component_count": len(components),
        "multi_edge_component_count": len(multi_components),
        "max_component_edges": max((component["edge_count"] for component in components), default=0),
        "max_component_nodes": max((component["node_count"] for component in components), default=0),
        "component_incomplete": component_incomplete,
        "zero_accept_component_count": sum(1 for component in components if component["zero_accept"]),
        "zero_accept_multi_edge_component_count": sum(
            1 for component in multi_components if component["zero_accept"]
        ),
        "parasite_free": parasite_free,
        "constant_reject_count": constant_reject_count,
        "unary_restrictive_count": unary_restrictive_count,
        "high_arity_count": high_arity_count,
        "components": components,
        "promise_status": (
            "scaffold_pc_tree_not_verified_as_hsu_mcconnell_output_for_D"
        ),
        "interpretation": (
            "All-binary-component diagnostic in the materialized scaffold only; "
            "not a proof of gadget composability, hardness, or promise validity."
        ),
    }


def run_relation_component_probe(
    *,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 64,
    seed: int = 20260550,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
    component_product_limit: int = 1_000_000,
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
                        component_product_limit=component_product_limit,
                    )
                )

    shape_counter: Counter[str] = Counter()
    component_shape_counter: Counter[str] = Counter()
    for row in rows:
        shape_counter.update(row.get("shape_histogram", {}))
        for component in row.get("components", []):
            if component["multi_edge"]:
                component_shape_counter.update(component["shape_histogram"])

    by_block = {}
    for block_count in block_counts:
        block_rows = [row for row in rows if row["block_count"] == block_count]
        by_block[str(block_count)] = {
            "rows": len(block_rows),
            "complete_rows": sum(1 for row in block_rows if row["complete"]),
            "binary_relation_rows": sum(
                1 for row in block_rows if row.get("binary_nonboolean_relation_count", 0) > 0
            ),
            "multi_edge_component_rows": sum(
                1 for row in block_rows if row.get("multi_edge_component_count", 0) > 0
            ),
            "parasite_free_rows": sum(1 for row in block_rows if row.get("parasite_free")),
            "parasite_free_multi_edge_rows": sum(
                1
                for row in block_rows
                if row.get("parasite_free") and row.get("multi_edge_component_count", 0) > 0
            ),
            "constant_reject_rows": sum(
                1 for row in block_rows if row.get("constant_reject_count", 0) > 0
            ),
            "max_component_edges": max(
                (row.get("max_component_edges", 0) for row in block_rows),
                default=0,
            ),
        }

    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row.get("validation_mismatch_count", 0) for row in rows),
        "component_incomplete_rows": sum(1 for row in rows if row.get("component_incomplete")),
        "binary_relation_rows": sum(
            1 for row in rows if row.get("binary_nonboolean_relation_count", 0) > 0
        ),
        "binary_nonboolean_relation_instances": sum(
            row.get("binary_nonboolean_relation_count", 0) for row in rows
        ),
        "multi_edge_component_rows": sum(
            1 for row in rows if row.get("multi_edge_component_count", 0) > 0
        ),
        "multi_edge_component_instances": sum(
            row.get("multi_edge_component_count", 0) for row in rows
        ),
        "parasite_free_rows": sum(1 for row in rows if row.get("parasite_free")),
        "parasite_free_multi_edge_rows": sum(
            1
            for row in rows
            if row.get("parasite_free") and row.get("multi_edge_component_count", 0) > 0
        ),
        "sat_parasite_free_multi_edge_rows": sum(
            1
            for row in rows
            if row.get("parasite_free")
            and row.get("multi_edge_component_count", 0) > 0
            and row.get("relation_accept_assignments", 0) > 0
        ),
        "rows_with_constant_reject": sum(
            1 for row in rows if row.get("constant_reject_count", 0) > 0
        ),
        "max_component_edges": max(
            (row.get("max_component_edges", 0) for row in rows),
            default=0,
        ),
        "max_component_nodes": max(
            (row.get("max_component_nodes", 0) for row in rows),
            default=0,
        ),
        "row_class_histogram": _histogram([row.get("row_class", "incomplete") for row in rows]),
        "shape_histogram": {key: shape_counter[key] for key in sorted(shape_counter)},
        "multi_edge_component_shape_histogram": {
            key: component_shape_counter[key] for key in sorted(component_shape_counter)
        },
        "by_block_count": by_block,
        "promise_caveat": (
            "The probe uses scaffold PC-trees; it does not prove these are the "
            "Hsu/McConnell quasi-circular PC-tree for D."
        ),
        "interpretation": (
            "A missing parasite-free multi-edge component is a negative signal "
            "for this scaffold sweep only, not a proof that no clean gadget exists."
        ),
    }
    return {
        "method": "p3_block_all_binary_relation_component_probe",
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3,4")
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260550)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--component-product-limit", type=int, default=1_000_000)
    parser.add_argument("--output", default="reports/relation_component_probe.json")
    args = parser.parse_args(argv)

    report = run_relation_component_probe(
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
        component_product_limit=args.component_product_limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
