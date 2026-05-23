#!/usr/bin/env python3
"""Probe whether local permutation-like P3 relations compose across blocks."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tools.pc_relation_catalog import _parse_ints  # noqa: E402
from tools.pc_relation_chain_probe import run_relation_chain_probe  # noqa: E402


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _permutation_profiles(row: dict) -> list[dict]:
    return [
        profile
        for profile in row.get("binary_relation_profiles", [])
        if profile["shape"] == "permutation_like"
    ]


def _component_rows(profiles: Sequence[dict]) -> list[dict]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    edges = []
    for profile in profiles:
        if len(profile["scope"]) != 2:
            continue
        left, right = profile["scope"]
        adjacency[left].add(right)
        adjacency[right].add(left)
        edges.append((left, right, profile))

    seen: set[str] = set()
    components = []
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
        component_profiles = [
            profile
            for left, right, profile in edges
            if left in node_set and right in node_set
        ]
        components.append(
            {
                "nodes": sorted(nodes),
                "node_count": len(nodes),
                "edge_count": len(component_profiles),
                "cycle_like": len(component_profiles) >= len(nodes),
                "catalog_hashes": sorted(
                    profile["catalog_hash"] for profile in component_profiles
                ),
                "scopes": [profile["scope"] for profile in component_profiles],
            }
        )
    return components


def _row_class(row: dict, permutation_count: int, parasite_free: bool) -> str:
    if permutation_count >= 2 and parasite_free and row.get("full_accept_count", 0) > 0:
        return "multi_permutation_composition_candidate"
    if permutation_count >= 2:
        return "multi_permutation_blocked_by_parasite_or_unsat"
    if permutation_count == 1 and parasite_free:
        return "single_permutation_only"
    if permutation_count == 1:
        return "single_permutation_blocked_by_parasite"
    if row.get("functional_relation_count", 0) > 0:
        return "functional_without_permutation_like"
    return "no_functional_relations"


def _summarize_row(row: dict) -> dict:
    profiles = _permutation_profiles(row)
    components = _component_rows(profiles)
    parasite_free = (
        row.get("constant_reject_count", 0) == 0
        and row.get("unary_restrictive_count", 0) == 0
        and row.get("high_arity_count", 0) == 0
    )
    max_component_edges = max((component["edge_count"] for component in components), default=0)
    row_class = _row_class(row, len(profiles), parasite_free)
    return {
        "block_count": row["block_count"],
        "n": row["n"],
        "repeat": row["repeat"],
        "seed": row["seed"],
        "complete": row["complete"],
        "validation_mismatch_count": row["validation_mismatch_count"],
        "row_class": row_class,
        "full_unsat_explanation": row.get("full_unsat_explanation"),
        "full_accept_count": row.get("full_accept_count"),
        "direct_cr_assignments": row.get("direct_cr_assignments"),
        "assignment_incomplete": row.get("assignment_incomplete"),
        "permutation_like_count": len(profiles),
        "permutation_like_profiles": profiles,
        "permutation_components": components,
        "max_permutation_component_edges": max_component_edges,
        "has_multi_permutation_component": max_component_edges >= 2,
        "parasite_free": parasite_free,
        "constant_reject_count": row.get("constant_reject_count"),
        "unary_restrictive_count": row.get("unary_restrictive_count"),
        "high_arity_count": row.get("high_arity_count"),
        "functional_relation_count": row.get("functional_relation_count"),
        "binary_non_boolean_relation_count": row.get("binary_non_boolean_relation_count"),
        "shape_histogram": row.get("shape_histogram"),
        "functional_component_count": row.get("functional_component_count"),
        "functional_cycle_component_count": row.get("functional_cycle_component_count"),
        "functional_cycle_obstruction": row.get("functional_cycle_obstruction"),
        "promise_status": row.get("promise_status"),
        "interpretation": (
            "Composition diagnostic in the materialized scaffold only; not a "
            "proof of gadget composability, hardness, or Hsu/McConnell promise."
        ),
    }


def run_permutation_composition_probe(
    *,
    block_counts: Sequence[int],
    repeats: int = 64,
    seed: int = 20260550,
    validate_until_blocks: int = 3,
    assignment_limit: int = 1_000_000,
    component_product_limit: int = 1_000_000,
) -> dict:
    chain_report = run_relation_chain_probe(
        block_counts=block_counts,
        instance_kinds=["paired_farthest"],
        repeats=repeats,
        seed=seed,
        validate_until_blocks=validate_until_blocks,
        assignment_limit=assignment_limit,
        component_product_limit=component_product_limit,
    )
    rows = [_summarize_row(row) for row in chain_report["rows"]]
    class_histogram = _histogram([row["row_class"] for row in rows])
    by_block = {}
    for block_count in block_counts:
        block_rows = [row for row in rows if row["block_count"] == block_count]
        by_block[str(block_count)] = {
            "rows": len(block_rows),
            "permutation_like_rows": sum(
                1 for row in block_rows if row["permutation_like_count"] > 0
            ),
            "multi_permutation_rows": sum(
                1 for row in block_rows if row["permutation_like_count"] >= 2
            ),
            "composition_candidate_rows": sum(
                1
                for row in block_rows
                if row["row_class"] == "multi_permutation_composition_candidate"
            ),
            "single_permutation_only_rows": sum(
                1 for row in block_rows if row["row_class"] == "single_permutation_only"
            ),
            "permutation_blocked_rows": sum(
                1
                for row in block_rows
                if row["row_class"] == "single_permutation_blocked_by_parasite"
                or row["row_class"] == "multi_permutation_blocked_by_parasite_or_unsat"
            ),
            "constant_reject_rows": sum(
                1 for row in block_rows if row.get("constant_reject_count", 0) > 0
            ),
            "max_permutation_component_edges": max(
                (row["max_permutation_component_edges"] for row in block_rows),
                default=0,
            ),
        }

    summary = {
        "rows": len(rows),
        "block_counts": list(block_counts),
        "repeats": repeats,
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "validation_mismatches": sum(row["validation_mismatch_count"] for row in rows),
        "assignment_incomplete_rows": sum(
            1 for row in rows if row.get("assignment_incomplete")
        ),
        "permutation_like_rows": sum(
            1 for row in rows if row["permutation_like_count"] > 0
        ),
        "permutation_like_relation_instances": sum(
            row["permutation_like_count"] for row in rows
        ),
        "multi_permutation_rows": sum(
            1 for row in rows if row["permutation_like_count"] >= 2
        ),
        "composition_candidate_rows": sum(
            1
            for row in rows
            if row["row_class"] == "multi_permutation_composition_candidate"
        ),
        "single_permutation_only_rows": sum(
            1 for row in rows if row["row_class"] == "single_permutation_only"
        ),
        "permutation_blocked_rows": sum(
            1
            for row in rows
            if row["row_class"] == "single_permutation_blocked_by_parasite"
            or row["row_class"] == "multi_permutation_blocked_by_parasite_or_unsat"
        ),
        "max_permutation_component_edges": max(
            (row["max_permutation_component_edges"] for row in rows),
            default=0,
        ),
        "class_histogram": class_histogram,
        "by_block_count": by_block,
        "promise_caveat": (
            "The probe composes local relations in scaffold PC-trees. It does "
            "not reconstruct the Hsu/McConnell quasi-circular PC-tree."
        ),
        "interpretation": (
            "Absence of clean multi-block permutation composition in this sweep "
            "is a negative experimental signal for the current gadget family, "
            "not a proof that such gadgets cannot exist."
        ),
    }
    return {
        "method": "paired_farthest_permutation_composition_probe",
        "chain_summary": chain_report["summary"],
        "rows": rows,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-counts", default="2,3,4")
    parser.add_argument("--repeats", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260550)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--assignment-limit", type=int, default=1_000_000)
    parser.add_argument("--component-product-limit", type=int, default=1_000_000)
    parser.add_argument("--output", default="reports/permutation_composition_probe.json")
    args = parser.parse_args(argv)

    report = run_permutation_composition_probe(
        block_counts=_parse_ints(args.block_counts),
        repeats=args.repeats,
        seed=args.seed,
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
