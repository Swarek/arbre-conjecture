#!/usr/bin/env python3
"""T103 probe: natural joins of insertion-gap component relations."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import enumerate_frontiers, labels  # noqa: E402
from pc_circular.solvers.local_constraints import (  # noqa: E402
    iter_internal_node_child_labels,
)
from pc_circular.solvers.partial_obligation_experiments import (  # noqa: E402
    _is_gap_composition_projection,
    _iter_pnode_obligation_projections,
    _missing_cyclic_gap_signature,
    _visible_global_role_order_signature,
)
from pc_circular.solvers.width4_experiments import (  # noqa: E402
    induced_child_circular_order,
)
from tools.pc_context_gap_arity_probe import (  # noqa: E402
    _instance,
    _is_applicable,
    _json_ready,
    _parse_ints,
    _parse_strings,
    _pc_tree,
    _repeat_count,
    _stable_offset,
)
from tools.pc_context_gap_binary_component_probe import (  # noqa: E402
    _binary_closure_stats,
)


def _hist_increment(histogram: dict, key, amount: int = 1) -> None:
    histogram[key] = histogram.get(key, 0) + amount


def _merge_histogram(target: dict, source: dict) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def _parse_decomposition_specs(value: str) -> list[tuple[int, int, int]]:
    specs = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 3:
            raise argparse.ArgumentTypeError(
                "decomposition specs must be left:right:overlap"
            )
        left_size, right_size, overlap_size = (int(field) for field in fields)
        if overlap_size <= 0:
            raise argparse.ArgumentTypeError("overlap size must be positive")
        if overlap_size > min(left_size, right_size):
            raise argparse.ArgumentTypeError("overlap cannot exceed either side")
        if left_size + right_size - overlap_size <= 0:
            raise argparse.ArgumentTypeError("invalid decomposition size")
        specs.append((left_size, right_size, overlap_size))
    return specs


def _decomposition_count(
    *, count: int, left_size: int, right_size: int, overlap_size: int
) -> int:
    union_size = left_size + right_size - overlap_size
    if count < union_size:
        return 0
    return (
        math.comb(count, union_size)
        * math.comb(union_size, overlap_size)
        * math.comb(union_size - overlap_size, left_size - overlap_size)
    )


def _sample_decompositions(
    *,
    rng: random.Random,
    count: int,
    left_size: int,
    right_size: int,
    overlap_size: int,
    sample_count: int,
    max_attempts: int,
) -> tuple[list[tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]], int, bool]:
    union_size = left_size + right_size - overlap_size
    total = _decomposition_count(
        count=count,
        left_size=left_size,
        right_size=right_size,
        overlap_size=overlap_size,
    )
    if total == 0:
        return [], 0, True

    if total <= sample_count:
        decompositions = []
        for union in combinations(range(count), union_size):
            for overlap in combinations(union, overlap_size):
                overlap_set = set(overlap)
                remainder = tuple(index for index in union if index not in overlap_set)
                for left_extra in combinations(remainder, left_size - overlap_size):
                    left_set = set(overlap) | set(left_extra)
                    right = tuple(index for index in union if index not in left_set or index in overlap_set)
                    left = tuple(index for index in union if index in left_set)
                    decompositions.append((left, right, union))
        return decompositions, 0, True

    seen = set()
    attempts = 0
    while len(seen) < sample_count and attempts < max_attempts:
        attempts += 1
        union = tuple(sorted(rng.sample(range(count), union_size)))
        overlap = tuple(sorted(rng.sample(union, overlap_size)))
        overlap_set = set(overlap)
        remainder = tuple(index for index in union if index not in overlap_set)
        left_extra = tuple(sorted(rng.sample(remainder, left_size - overlap_size)))
        left_set = overlap_set | set(left_extra)
        left = tuple(index for index in union if index in left_set)
        right = tuple(index for index in union if index not in left_set or index in overlap_set)
        seen.add((left, right, union))
    return sorted(seen), attempts, len(seen) == total


def _project_relation(relation: set[tuple], positions: tuple[int, ...]) -> set[tuple]:
    return {
        tuple(value_tuple[position] for position in positions)
        for value_tuple in relation
    }


def _natural_join(
    *,
    left_relation: set[tuple],
    right_relation: set[tuple],
    left_positions: tuple[int, ...],
    right_positions: tuple[int, ...],
    arity: int,
    max_join_pairs: int,
) -> tuple[set[tuple] | None, int, bool]:
    pair_bound = len(left_relation) * len(right_relation)
    if pair_bound > max_join_pairs:
        return None, pair_bound, True

    left_index_by_position = {
        position: index for index, position in enumerate(left_positions)
    }
    right_index_by_position = {
        position: index for index, position in enumerate(right_positions)
    }
    overlap_positions = tuple(
        sorted(set(left_positions).intersection(right_positions))
    )
    joined = set()
    for left_tuple in left_relation:
        for right_tuple in right_relation:
            if any(
                left_tuple[left_index_by_position[position]]
                != right_tuple[right_index_by_position[position]]
                for position in overlap_positions
            ):
                continue
            merged = [None] * arity
            for position in left_positions:
                merged[position] = left_tuple[left_index_by_position[position]]
            for position in right_positions:
                value = right_tuple[right_index_by_position[position]]
                if merged[position] is not None and merged[position] != value:
                    raise AssertionError("overlap disagreement after join check")
                merged[position] = value
            joined.add(tuple(merged))
    return joined, pair_bound, False


def _cross_restrictive_pair_count(
    *,
    relation: set[tuple],
    left_only_positions: tuple[int, ...],
    right_only_positions: tuple[int, ...],
) -> int:
    if not relation:
        return 0
    marginals = tuple(
        {value_tuple[index] for value_tuple in relation}
        for index in range(len(next(iter(relation))))
    )
    restrictive = 0
    for left_position in left_only_positions:
        for right_position in right_only_positions:
            pair_projection = {
                (value_tuple[left_position], value_tuple[right_position])
                for value_tuple in relation
            }
            if len(pair_projection) < (
                len(marginals[left_position]) * len(marginals[right_position])
            ):
                restrictive += 1
    return restrictive


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    decomposition_spec: tuple[int, int, int],
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_join_pairs: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    rng = random.Random(seed)
    left_size, right_size, overlap_size = decomposition_spec
    union_size = left_size + right_size - overlap_size
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    if set(labels(T)) != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")

    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = tuple(raw_frontiers[:frontier_limit])

    node_infos = [
        node_info
        for node_info in iter_internal_node_child_labels(T)
        if node_info["kind"] == "P"
    ]
    node_by_path = {tuple(node_info["path"]): node_info for node_info in node_infos}
    local_order_by_path = {path: {} for path in node_by_path}
    for path, node_info in node_by_path.items():
        child_label_sets = node_info["child_label_sets"]
        for frontier in frontiers:
            local_order_by_path[path][frontier] = induced_child_circular_order(
                frontier,
                child_label_sets,
            )

    open_obligations = tuple(
        sorted(
            (
                obligation
                for obligation in _iter_pnode_obligation_projections(D, T)
                if _is_gap_composition_projection(obligation, scope)
            ),
            key=lambda obligation: (
                obligation["same_side"],
                obligation["path"],
                obligation["fine_role_pattern"],
                obligation["projected_roles"],
            ),
        )
    )
    total_decomposition_count = _decomposition_count(
        count=len(open_obligations),
        left_size=left_size,
        right_size=right_size,
        overlap_size=overlap_size,
    )
    max_attempts = max(sample_count, sample_count * max_attempt_multiplier)
    decompositions, random_attempt_count, sample_exhausted = _sample_decompositions(
        rng=rng,
        count=len(open_obligations),
        left_size=left_size,
        right_size=right_size,
        overlap_size=overlap_size,
        sample_count=sample_count,
        max_attempts=max_attempts,
    )

    sampled_decomposition_count = 0
    skipped_same_obligation_decomposition_count = 0
    visible_case_count = 0
    join_capped_case_count = 0
    exact_join_case_count = 0
    false_join_case_count = 0
    false_join_tuple_count = 0
    false_join_full_binary_exact_case_count = 0
    nontrivial_component_case_count = 0
    cross_restrictive_pair_count_total = 0
    false_join_with_cross_restrictive_pair_count = 0
    binary_higher_order_case_count = 0
    max_actual_relation_size = 0
    max_left_relation_size = 0
    max_right_relation_size = 0
    max_join_size = 0
    max_false_join_count = 0
    max_join_pair_bound = 0
    actual_relation_size_histogram: dict = {}
    left_relation_size_histogram: dict = {}
    right_relation_size_histogram: dict = {}
    join_size_histogram: dict = {}
    false_join_size_histogram: dict = {}
    cross_restrictive_pair_histogram: dict = {}
    distinct_obligation_histogram: dict = {}
    false_join_examples = []
    exact_join_examples = []

    for left_indices, right_indices, union_indices in decompositions:
        obligation_tuple = tuple(open_obligations[index] for index in union_indices)
        distinct_same_side_count = len(
            {obligation["same_side"] for obligation in obligation_tuple}
        )
        if distinct_same_side_count < min_distinct_obligations:
            skipped_same_obligation_decomposition_count += 1
            continue
        sampled_decomposition_count += 1
        _hist_increment(distinct_obligation_histogram, distinct_same_side_count)

        union_position_by_index = {
            obligation_index: position
            for position, obligation_index in enumerate(union_indices)
        }
        left_positions = tuple(
            union_position_by_index[obligation_index]
            for obligation_index in left_indices
        )
        right_positions = tuple(
            union_position_by_index[obligation_index]
            for obligation_index in right_indices
        )
        overlap_positions = tuple(
            sorted(set(left_positions).intersection(right_positions))
        )
        left_only_positions = tuple(
            position for position in left_positions if position not in overlap_positions
        )
        right_only_positions = tuple(
            position for position in right_positions if position not in overlap_positions
        )

        relation_by_visible: dict[tuple, set[tuple]] = {}
        for frontier in frontiers:
            visible_parts = []
            gap_parts = []
            for position, obligation in enumerate(obligation_tuple):
                path = obligation["path"]
                local_order = local_order_by_path[path][frontier]
                visible_order = _visible_global_role_order_signature(
                    frontier,
                    obligation["projected_roles"],
                )
                gap_signature = _missing_cyclic_gap_signature(
                    frontier,
                    obligation["same_side"],
                    obligation["projected_roles"],
                )
                identity = (position, obligation["same_side"], path)
                visible_parts.append((identity, local_order, visible_order))
                gap_parts.append((identity, gap_signature))
            relation_by_visible.setdefault(tuple(visible_parts), set()).add(
                tuple(gap_parts)
            )

        for visible_key, actual_relation in relation_by_visible.items():
            visible_case_count += 1
            actual_size = len(actual_relation)
            left_relation = _project_relation(actual_relation, left_positions)
            right_relation = _project_relation(actual_relation, right_positions)
            if len(left_relation) > 1 and len(right_relation) > 1:
                nontrivial_component_case_count += 1

            joined_relation, join_pair_bound, join_capped = _natural_join(
                left_relation=left_relation,
                right_relation=right_relation,
                left_positions=left_positions,
                right_positions=right_positions,
                arity=union_size,
                max_join_pairs=max_join_pairs,
            )
            max_join_pair_bound = max(max_join_pair_bound, join_pair_bound)
            if join_capped:
                join_capped_case_count += 1
                continue

            join_size = len(joined_relation)
            false_join_count = len(joined_relation - actual_relation)
            cross_restrictive_pair_count = _cross_restrictive_pair_count(
                relation=actual_relation,
                left_only_positions=left_only_positions,
                right_only_positions=right_only_positions,
            )
            binary_stats = _binary_closure_stats(
                actual_relation,
                arity=union_size,
                max_product_size=max_product_size,
            )
            full_binary_exact = (
                not binary_stats["product_capped"]
                and binary_stats["false_count"] == 0
            )
            if not binary_stats["product_capped"] and binary_stats["false_count"]:
                binary_higher_order_case_count += 1

            cross_restrictive_pair_count_total += cross_restrictive_pair_count
            max_actual_relation_size = max(max_actual_relation_size, actual_size)
            max_left_relation_size = max(max_left_relation_size, len(left_relation))
            max_right_relation_size = max(max_right_relation_size, len(right_relation))
            max_join_size = max(max_join_size, join_size)
            max_false_join_count = max(max_false_join_count, false_join_count)
            _hist_increment(actual_relation_size_histogram, actual_size)
            _hist_increment(left_relation_size_histogram, len(left_relation))
            _hist_increment(right_relation_size_histogram, len(right_relation))
            _hist_increment(join_size_histogram, join_size)
            _hist_increment(false_join_size_histogram, false_join_count)
            _hist_increment(
                cross_restrictive_pair_histogram,
                cross_restrictive_pair_count,
            )

            if false_join_count:
                false_join_case_count += 1
                false_join_tuple_count += false_join_count
                if full_binary_exact:
                    false_join_full_binary_exact_case_count += 1
                if cross_restrictive_pair_count:
                    false_join_with_cross_restrictive_pair_count += 1
                if len(false_join_examples) < max_examples:
                    false_join_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_tuple
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_tuple
                            ),
                            "left_positions": left_positions,
                            "right_positions": right_positions,
                            "overlap_positions": overlap_positions,
                            "actual_relation_size": actual_size,
                            "left_relation_size": len(left_relation),
                            "right_relation_size": len(right_relation),
                            "join_size": join_size,
                            "false_join_count": false_join_count,
                            "cross_restrictive_pair_count": cross_restrictive_pair_count,
                            "full_binary_exact": full_binary_exact,
                            "visible_key": visible_key,
                            "first_false_join_tuple": tuple(
                                sorted(joined_relation - actual_relation, key=repr)[0]
                            ),
                        }
                    )
            else:
                exact_join_case_count += 1
                if len(exact_join_examples) < max_examples:
                    exact_join_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_tuple
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_tuple
                            ),
                            "actual_relation_size": actual_size,
                            "left_relation_size": len(left_relation),
                            "right_relation_size": len(right_relation),
                            "join_size": join_size,
                            "cross_restrictive_pair_count": cross_restrictive_pair_count,
                        }
                    )

    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": not frontier_truncated and sample_exhausted,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "open_obligation_projection_count": len(open_obligations),
        "decomposition_spec": decomposition_spec,
        "total_decomposition_count": total_decomposition_count,
        "random_attempt_count": random_attempt_count,
        "sample_exhausted": sample_exhausted,
        "sampled_index_decomposition_count": len(decompositions),
        "sampled_decomposition_count": sampled_decomposition_count,
        "skipped_same_obligation_decomposition_count": (
            skipped_same_obligation_decomposition_count
        ),
        "visible_case_count": visible_case_count,
        "join_capped_case_count": join_capped_case_count,
        "exact_join_case_count": exact_join_case_count,
        "false_join_case_count": false_join_case_count,
        "false_join_tuple_count": false_join_tuple_count,
        "false_join_full_binary_exact_case_count": (
            false_join_full_binary_exact_case_count
        ),
        "cross_edge_repaired_case_count": false_join_full_binary_exact_case_count,
        "cross_edge_unrepaired_case_count": (
            false_join_case_count - false_join_full_binary_exact_case_count
        ),
        "nontrivial_component_case_count": nontrivial_component_case_count,
        "cross_restrictive_pair_count_total": cross_restrictive_pair_count_total,
        "false_join_with_cross_restrictive_pair_count": (
            false_join_with_cross_restrictive_pair_count
        ),
        "binary_higher_order_case_count": binary_higher_order_case_count,
        "max_actual_relation_size": max_actual_relation_size,
        "max_left_relation_size": max_left_relation_size,
        "max_right_relation_size": max_right_relation_size,
        "max_join_size": max_join_size,
        "max_false_join_count": max_false_join_count,
        "max_join_pair_bound": max_join_pair_bound,
        "actual_relation_size_histogram": dict(
            sorted(actual_relation_size_histogram.items())
        ),
        "left_relation_size_histogram": dict(
            sorted(left_relation_size_histogram.items())
        ),
        "right_relation_size_histogram": dict(
            sorted(right_relation_size_histogram.items())
        ),
        "join_size_histogram": dict(sorted(join_size_histogram.items())),
        "false_join_size_histogram": dict(sorted(false_join_size_histogram.items())),
        "cross_restrictive_pair_histogram": dict(
            sorted(cross_restrictive_pair_histogram.items())
        ),
        "distinct_obligation_histogram": dict(
            sorted(distinct_obligation_histogram.items())
        ),
        "false_join_examples": tuple(false_join_examples),
        "exact_join_examples": tuple(exact_join_examples),
    }


def _summarize_rows(rows: list[dict]) -> dict:
    actual_relation_size_histogram: dict = {}
    false_join_size_histogram: dict = {}
    cross_restrictive_pair_histogram: dict = {}
    distinct_obligation_histogram: dict = {}
    for row in rows:
        _merge_histogram(
            actual_relation_size_histogram,
            row["actual_relation_size_histogram"],
        )
        _merge_histogram(false_join_size_histogram, row["false_join_size_histogram"])
        _merge_histogram(
            cross_restrictive_pair_histogram,
            row["cross_restrictive_pair_histogram"],
        )
        _merge_histogram(
            distinct_obligation_histogram,
            row["distinct_obligation_histogram"],
        )
    return {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "frontier_truncated_rows": sum(1 for row in rows if row["frontier_truncated"]),
        "sample_exhausted_rows": sum(1 for row in rows if row["sample_exhausted"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "open_obligation_projection_count": sum(
            row["open_obligation_projection_count"] for row in rows
        ),
        "total_decomposition_count": sum(
            row["total_decomposition_count"] for row in rows
        ),
        "sampled_index_decomposition_count": sum(
            row["sampled_index_decomposition_count"] for row in rows
        ),
        "sampled_decomposition_count": sum(
            row["sampled_decomposition_count"] for row in rows
        ),
        "visible_case_count": sum(row["visible_case_count"] for row in rows),
        "join_capped_case_count": sum(row["join_capped_case_count"] for row in rows),
        "exact_join_case_count": sum(row["exact_join_case_count"] for row in rows),
        "false_join_case_count": sum(row["false_join_case_count"] for row in rows),
        "false_join_tuple_count": sum(row["false_join_tuple_count"] for row in rows),
        "false_join_full_binary_exact_case_count": sum(
            row["false_join_full_binary_exact_case_count"] for row in rows
        ),
        "cross_edge_repaired_case_count": sum(
            row["cross_edge_repaired_case_count"] for row in rows
        ),
        "cross_edge_unrepaired_case_count": sum(
            row["cross_edge_unrepaired_case_count"] for row in rows
        ),
        "nontrivial_component_case_count": sum(
            row["nontrivial_component_case_count"] for row in rows
        ),
        "cross_restrictive_pair_count_total": sum(
            row["cross_restrictive_pair_count_total"] for row in rows
        ),
        "false_join_with_cross_restrictive_pair_count": sum(
            row["false_join_with_cross_restrictive_pair_count"] for row in rows
        ),
        "binary_higher_order_case_count": sum(
            row["binary_higher_order_case_count"] for row in rows
        ),
        "rows_with_false_join": sum(1 for row in rows if row["false_join_case_count"]),
        "max_actual_relation_size": max(
            (row["max_actual_relation_size"] for row in rows), default=0
        ),
        "max_left_relation_size": max(
            (row["max_left_relation_size"] for row in rows), default=0
        ),
        "max_right_relation_size": max(
            (row["max_right_relation_size"] for row in rows), default=0
        ),
        "max_join_size": max((row["max_join_size"] for row in rows), default=0),
        "max_false_join_count": max(
            (row["max_false_join_count"] for row in rows), default=0
        ),
        "max_join_pair_bound": max(
            (row["max_join_pair_bound"] for row in rows), default=0
        ),
        "actual_relation_size_histogram": dict(
            sorted(actual_relation_size_histogram.items())
        ),
        "false_join_size_histogram": dict(sorted(false_join_size_histogram.items())),
        "cross_restrictive_pair_histogram": dict(
            sorted(cross_restrictive_pair_histogram.items())
        ),
        "distinct_obligation_histogram": dict(
            sorted(distinct_obligation_histogram.items())
        ),
    }


def run_probe(
    *,
    decomposition_specs: list[tuple[int, int, int]],
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_join_pairs: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
    rows = []
    skipped = []
    for decomposition_spec in decomposition_specs:
        for n in sizes:
            for pc_tree_kind in pc_trees:
                for instance_kind in instance_kinds:
                    if not _is_applicable(instance_kind, n):
                        skipped.append(
                            {
                                "decomposition_spec": decomposition_spec,
                                "n": n,
                                "pc_tree_kind": pc_tree_kind,
                                "instance_kind": instance_kind,
                                "reason": "not_applicable",
                            }
                        )
                        continue
                    for repeat in range(_repeat_count(instance_kind, repeats)):
                        left_size, right_size, overlap_size = decomposition_spec
                        row_seed = (
                            seed
                            + 1000003 * left_size
                            + 100003 * right_size
                            + 1009 * overlap_size
                            + 101 * n
                            + 17 * repeat
                            + _stable_offset(pc_tree_kind, instance_kind)
                        )
                        rows.append(
                            _row(
                                n=n,
                                pc_tree_kind=pc_tree_kind,
                                instance_kind=instance_kind,
                                repeat=repeat,
                                seed=row_seed,
                                frontier_limit=frontier_limit,
                                decomposition_spec=decomposition_spec,
                                min_distinct_obligations=min_distinct_obligations,
                                scope=scope,
                                sample_count=sample_count,
                                max_attempt_multiplier=max_attempt_multiplier,
                                max_product_size=max_product_size,
                                max_join_pairs=max_join_pairs,
                                max_examples=max_examples,
                            )
                        )

    by_decomposition_spec = {}
    for decomposition_spec in decomposition_specs:
        key = ":".join(str(part) for part in decomposition_spec)
        spec_rows = [row for row in rows if row["decomposition_spec"] == decomposition_spec]
        by_decomposition_spec[key] = _summarize_rows(spec_rows)
    summary = _summarize_rows(rows)
    summary["decomposition_specs_with_false_join"] = [
        key
        for key, value in by_decomposition_spec.items()
        if value["false_join_case_count"]
    ]
    summary["interpretation"] = (
        "T103 tests natural joins of exact gap component relations. A false "
        "join means the chosen overlap does not mediate all compatibility; it "
        "does not refute T102's all-pairs binary closure result."
    )

    return {
        "method": "t103_context_gap_join_decomposition_probe",
        "decomposition_specs": decomposition_specs,
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "min_distinct_obligations": min_distinct_obligations,
        "scope": scope,
        "sample_count": sample_count,
        "max_attempt_multiplier": max_attempt_multiplier,
        "max_product_size": max_product_size,
        "max_join_pairs": max_join_pairs,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "by_decomposition_spec": by_decomposition_spec,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decomposition-specs",
        default="4:4:2,5:5:2",
        type=_parse_decomposition_specs,
    )
    parser.add_argument("--sizes", default="5,6,7", type=_parse_ints)
    parser.add_argument("--pc-trees", default="balanced,mixed", type=_parse_strings)
    parser.add_argument(
        "--instance-kinds",
        default="cycle,paired_farthest,random,random4,padded_five_local_non_cr",
        type=_parse_strings,
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument("--min-distinct-obligations", type=int, default=2)
    parser.add_argument(
        "--scope",
        choices=("all_open", "support_open", "projection_only_open"),
        default="all_open",
    )
    parser.add_argument("--sample-count", type=int, default=800)
    parser.add_argument("--max-attempt-multiplier", type=int, default=20)
    parser.add_argument("--max-product-size", type=int, default=20000)
    parser.add_argument("--max-join-pairs", type=int, default=20000)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260721)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_join_decomposition_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        decomposition_specs=args.decomposition_specs,
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        min_distinct_obligations=args.min_distinct_obligations,
        scope=args.scope,
        sample_count=args.sample_count,
        max_attempt_multiplier=args.max_attempt_multiplier,
        max_product_size=args.max_product_size,
        max_join_pairs=args.max_join_pairs,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
