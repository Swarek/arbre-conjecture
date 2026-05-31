#!/usr/bin/env python3
"""T104 probe: targeted parity-cycle stress for gap binary closure.

T102/T103 did not find a true binary-closure failure in broad sweeps.  This
probe stops sampling uniformly and targets high-cycle/low-hub instances with a
PC-tree whose pair blocks expose one gap bit per cycle-neighborhood obligation.
The custom ``cycle_pair_p`` tree is an adversarial stress tree; it is not claimed
to be the Hsu/McConnell tree induced by the same dissimilarity.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from itertools import combinations, product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import (  # noqa: E402
    c_node,
    enumerate_frontiers,
    labels,
    leaf,
    p_node,
    pc_tree_from_kind,
)
from pc_circular.solvers.local_constraints import (  # noqa: E402
    iter_internal_node_child_labels,
)
from pc_circular.solvers.partial_obligation_experiments import (  # noqa: E402
    _is_gap_composition_projection,
    _iter_pnode_obligation_projections,
    _missing_cyclic_gap_signature,
    _obligation_roles,
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
    _stable_offset,
)
from tools.pc_context_gap_binary_component_probe import (  # noqa: E402
    _binary_closure_stats,
    _hist_increment,
    _merge_histogram,
    _sample_index_sets,
)


CUSTOM_PC_TREE_KINDS = {"cycle_pair_p", "cycle_pair_c"}
GAP_MODES = {"current_gap", "gap_with_distance"}


def _cycle_pair_block_tree(n: int, *, root_kind: str):
    if n < 4:
        raise ValueError("cycle pair block tree needs at least 4 leaves")
    high_labels = list(range(1, n))
    children = [leaf(0)]
    for index in range(0, len(high_labels) - 1, 2):
        children.append(
            p_node((leaf(high_labels[index]), leaf(high_labels[index + 1])))
        )
    if len(high_labels) % 2:
        children.append(leaf(high_labels[-1]))
    if root_kind == "P":
        return p_node(children)
    if root_kind == "C":
        return c_node(children)
    raise ValueError(f"unknown root kind: {root_kind}")


def _pc_tree(kind: str, n: int):
    if kind == "cycle_pair_p":
        return _cycle_pair_block_tree(n, root_kind="P")
    if kind == "cycle_pair_c":
        return _cycle_pair_block_tree(n, root_kind="C")
    return pc_tree_from_kind(kind, n)


def _cycle_neighbors(vertex: int, high_count: int) -> tuple[int, int]:
    return 1 + ((vertex - 2) % high_count), 1 + (vertex % high_count)


def _target_cycle_vertex(obligation: dict, high_count: int) -> int | None:
    a, c, b, d = obligation["same_side"]
    endpoint_set = {a, c}
    witness_set = {b, d}
    for vertex in range(1, high_count + 1):
        if endpoint_set == {0, vertex} and witness_set == set(
            _cycle_neighbors(vertex, high_count)
        ):
            return vertex
    return None


def _target_cycle_rank(target_vertices: set[int], high_count: int) -> int:
    if not target_vertices:
        return 0
    edges = 0
    for vertex in target_vertices:
        if 1 + (vertex % high_count) in target_vertices:
            edges += 1
    return max(0, edges - len(target_vertices) + 1)


def _missing_cyclic_gap_signature_with_distance(
    frontier,
    same_side,
    projected_roles,
) -> tuple:
    """Like the current gap signature, but keep the cyclic distance in the gap."""

    projected_labels = {label for _, label, _ in projected_roles}
    visible_positions = sorted(frontier.index(label) for _, label, _ in projected_roles)
    if not visible_positions:
        return ()
    n = len(frontier)
    missing_items = []
    for role, label in _obligation_roles(same_side):
        if label in projected_labels:
            continue
        position = frontier.index(label)
        previous_index = len(visible_positions) - 1
        for index, visible_position in enumerate(visible_positions):
            if visible_position > position:
                previous_index = index - 1 if index > 0 else len(visible_positions) - 1
                break
        previous_position = visible_positions[previous_index]
        cyclic_distance = (position - previous_position) % n
        missing_items.append((previous_index, cyclic_distance, role, label))
    return tuple(
        (gap_index, cyclic_distance, role, label)
        for gap_index, cyclic_distance, role, label in sorted(missing_items)
    )


def _gap_signature(mode: str, frontier, same_side, projected_roles) -> tuple:
    if mode == "current_gap":
        return _missing_cyclic_gap_signature(frontier, same_side, projected_roles)
    if mode == "gap_with_distance":
        return _missing_cyclic_gap_signature_with_distance(
            frontier,
            same_side,
            projected_roles,
        )
    raise ValueError(f"unknown gap mode: {mode}")


def _histogram_sorted(histogram: dict) -> dict:
    return dict(sorted(histogram.items(), key=lambda item: str(item[0])))


def _projection_index_sets(
    *,
    rng: random.Random,
    projection_count: int,
    set_sizes: list[int],
    include_full_target_set: bool,
    sample_count: int,
    max_attempt_multiplier: int,
) -> tuple[list[dict], int, bool, int]:
    sampled: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    random_attempt_count = 0
    sample_exhausted = True
    total_set_count = 0

    if include_full_target_set and projection_count >= 2:
        full = tuple(range(projection_count))
        sampled.append(
            {
                "kind": "all_targets",
                "indices": full,
                "sample_exhausted": True,
                "random_attempt_count": 0,
                "total_set_count": 1,
            }
        )
        seen.add(full)
        total_set_count += 1

    for size in set_sizes:
        if projection_count < size:
            continue
        total = math.comb(projection_count, size)
        total_set_count += total
        max_attempts = max(sample_count, sample_count * max_attempt_multiplier)
        index_sets, attempts, exhausted = _sample_index_sets(
            rng=rng,
            count=projection_count,
            size=size,
            sample_count=sample_count,
            max_attempts=max_attempts,
        )
        random_attempt_count += attempts
        sample_exhausted = sample_exhausted and exhausted
        for index_set in index_sets:
            if index_set in seen:
                continue
            seen.add(index_set)
            sampled.append(
                {
                    "kind": f"size_{size}",
                    "indices": index_set,
                    "sample_exhausted": exhausted,
                    "random_attempt_count": attempts,
                    "total_set_count": total,
                }
            )
    return sampled, total_set_count, sample_exhausted, random_attempt_count


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    seed: int,
    frontier_limit: int,
    set_sizes: list[int],
    gap_mode: str,
    include_full_target_set: bool,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    if gap_mode not in GAP_MODES:
        raise ValueError(f"unknown gap mode: {gap_mode}")
    rng = random.Random(seed)
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
    local_order_by_path = {tuple(node_info["path"]): {} for node_info in node_infos}
    for node_info in node_infos:
        path = tuple(node_info["path"])
        child_label_sets = node_info["child_label_sets"]
        for frontier in frontiers:
            local_order_by_path[path][frontier] = induced_child_circular_order(
                frontier,
                child_label_sets,
            )

    high_count = len(D) - 1
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
    target_obligations = []
    for obligation in open_obligations:
        target_vertex = _target_cycle_vertex(obligation, high_count)
        if target_vertex is None:
            continue
        enriched = dict(obligation)
        enriched["target_cycle_vertex"] = target_vertex
        target_obligations.append(enriched)
    target_obligations = tuple(
        sorted(
            target_obligations,
            key=lambda obligation: (
                obligation["target_cycle_vertex"],
                obligation["same_side"],
                obligation["path"],
                obligation["fine_role_pattern"],
                obligation["projected_roles"],
            ),
        )
    )
    target_vertices = {
        obligation["target_cycle_vertex"] for obligation in target_obligations
    }

    sampled_index_sets, total_set_count, sample_exhausted, random_attempt_count = (
        _projection_index_sets(
            rng=rng,
            projection_count=len(target_obligations),
            set_sizes=set_sizes,
            include_full_target_set=include_full_target_set,
            sample_count=sample_count,
            max_attempt_multiplier=max_attempt_multiplier,
        )
    )

    sampled_set_count = 0
    visible_case_count = 0
    product_capped_case_count = 0
    unary_sufficient_case_count = 0
    binary_sufficient_case_count = 0
    higher_order_case_count = 0
    product_false_case_count = 0
    product_false_tuple_count = 0
    pairwise_false_tuple_count = 0
    max_product_size_seen = 0
    max_closure_size = 0
    max_actual_relation_size = 0
    max_false_count = 0
    min_higher_order_projection_count: int | None = None
    restrictive_edge_count_total = 0
    visible_cases_with_restrictive_edges = 0
    projection_set_kind_histogram: dict = {}
    min_required_arity_histogram: dict = {}
    actual_relation_size_histogram: dict = {}
    product_size_histogram: dict = {}
    closure_size_histogram: dict = {}
    restrictive_edge_histogram: dict = {}
    target_vertex_count_histogram: dict = {}
    binary_sufficient_examples = []
    higher_order_examples = []

    for sampled in sampled_index_sets:
        index_set = tuple(sampled["indices"])
        obligation_set = tuple(target_obligations[index] for index in index_set)
        if len(obligation_set) < 2:
            continue
        sampled_set_count += 1
        _hist_increment(projection_set_kind_histogram, sampled["kind"])
        selected_target_vertices = {
            obligation["target_cycle_vertex"] for obligation in obligation_set
        }
        _hist_increment(target_vertex_count_histogram, len(selected_target_vertices))

        relation_by_visible: dict[tuple, set[tuple]] = {}
        for frontier in frontiers:
            visible_parts = []
            gap_parts = []
            for index, obligation in enumerate(obligation_set):
                path = obligation["path"]
                local_order = local_order_by_path[path][frontier]
                visible_order = _visible_global_role_order_signature(
                    frontier,
                    obligation["projected_roles"],
                )
                gap_signature = _gap_signature(
                    gap_mode,
                    frontier,
                    obligation["same_side"],
                    obligation["projected_roles"],
                )
                identity = (
                    index,
                    obligation["target_cycle_vertex"],
                    obligation["same_side"],
                    path,
                )
                visible_parts.append((identity, local_order, visible_order))
                gap_parts.append((identity, gap_signature))
            relation_by_visible.setdefault(tuple(visible_parts), set()).add(
                tuple(gap_parts)
            )

        for visible_key, actual_relation in relation_by_visible.items():
            visible_case_count += 1
            actual_size = len(actual_relation)
            stats = _binary_closure_stats(
                actual_relation,
                arity=len(obligation_set),
                max_product_size=max_product_size,
            )
            product_size = stats["product_size"]
            restrictive_edge_count = stats["restrictive_edge_count"]
            restrictive_edge_count_total += restrictive_edge_count
            if restrictive_edge_count:
                visible_cases_with_restrictive_edges += 1
            max_product_size_seen = max(max_product_size_seen, product_size)
            max_actual_relation_size = max(max_actual_relation_size, actual_size)
            _hist_increment(actual_relation_size_histogram, actual_size)
            _hist_increment(product_size_histogram, product_size)
            _hist_increment(restrictive_edge_histogram, restrictive_edge_count)

            if stats["product_capped"]:
                product_capped_case_count += 1
                _hist_increment(min_required_arity_histogram, "capped")
                continue

            closure_size = stats["closure_size"]
            false_count = stats["false_count"]
            max_closure_size = max(max_closure_size, closure_size)
            max_false_count = max(max_false_count, false_count)
            _hist_increment(closure_size_histogram, closure_size)

            product_false_count = product_size - actual_size
            if product_false_count:
                product_false_case_count += 1
                product_false_tuple_count += product_false_count

            if product_size == actual_size:
                unary_sufficient_case_count += 1
                required_arity = 1
            elif false_count == 0:
                binary_sufficient_case_count += 1
                required_arity = 2
                if len(binary_sufficient_examples) < max_examples:
                    binary_sufficient_examples.append(
                        {
                            "set_kind": sampled["kind"],
                            "target_cycle_vertices": tuple(
                                obligation["target_cycle_vertex"]
                                for obligation in obligation_set
                            ),
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_set
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_set
                            ),
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "closure_size": closure_size,
                            "restrictive_edge_count": restrictive_edge_count,
                        }
                    )
            else:
                higher_order_case_count += 1
                pairwise_false_tuple_count += false_count
                required_arity = ">=3"
                if (
                    min_higher_order_projection_count is None
                    or len(obligation_set) < min_higher_order_projection_count
                ):
                    min_higher_order_projection_count = len(obligation_set)
                if len(higher_order_examples) < max_examples:
                    higher_order_examples.append(
                        {
                            "set_kind": sampled["kind"],
                            "target_cycle_vertices": tuple(
                                obligation["target_cycle_vertex"]
                                for obligation in obligation_set
                            ),
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_set
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_set
                            ),
                            "fine_role_patterns": tuple(
                                obligation["fine_role_pattern"]
                                for obligation in obligation_set
                            ),
                            "visible_key": visible_key,
                            "actual_gap_tuples": tuple(
                                sorted(actual_relation, key=repr)[:max_examples]
                            ),
                            "first_false_tuple": stats["first_false_tuple"],
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "closure_size": closure_size,
                            "false_count": false_count,
                            "restrictive_edge_count": restrictive_edge_count,
                        }
                    )
            _hist_increment(min_required_arity_histogram, required_arity)

    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "gap_mode": gap_mode,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": (
            not frontier_truncated
            and sample_exhausted
            and product_capped_case_count == 0
        ),
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "open_obligation_projection_count": len(open_obligations),
        "cycle_target_projection_count": len(target_obligations),
        "target_same_side_count": len(
            {obligation["same_side"] for obligation in target_obligations}
        ),
        "target_cycle_vertex_count": len(target_vertices),
        "target_cycle_rank": _target_cycle_rank(target_vertices, high_count),
        "target_cycle_vertices": tuple(sorted(target_vertices)),
        "total_set_count": total_set_count,
        "sampled_index_set_count": len(sampled_index_sets),
        "sampled_set_count": sampled_set_count,
        "sample_exhausted": sample_exhausted,
        "random_attempt_count": random_attempt_count,
        "visible_case_count": visible_case_count,
        "product_capped_case_count": product_capped_case_count,
        "unary_sufficient_case_count": unary_sufficient_case_count,
        "binary_sufficient_case_count": binary_sufficient_case_count,
        "higher_order_case_count": higher_order_case_count,
        "product_false_case_count": product_false_case_count,
        "product_false_tuple_count": product_false_tuple_count,
        "pairwise_false_tuple_count": pairwise_false_tuple_count,
        "max_product_size": max_product_size_seen,
        "max_closure_size": max_closure_size,
        "max_actual_relation_size": max_actual_relation_size,
        "max_false_count": max_false_count,
        "min_higher_order_projection_count": min_higher_order_projection_count,
        "restrictive_edge_count_total": restrictive_edge_count_total,
        "visible_cases_with_restrictive_edges": visible_cases_with_restrictive_edges,
        "projection_set_kind_histogram": _histogram_sorted(projection_set_kind_histogram),
        "target_vertex_count_histogram": _histogram_sorted(target_vertex_count_histogram),
        "min_required_arity_histogram": _histogram_sorted(min_required_arity_histogram),
        "actual_relation_size_histogram": dict(
            sorted(actual_relation_size_histogram.items())
        ),
        "product_size_histogram": dict(sorted(product_size_histogram.items())),
        "closure_size_histogram": dict(sorted(closure_size_histogram.items())),
        "restrictive_edge_histogram": dict(sorted(restrictive_edge_histogram.items())),
        "binary_sufficient_examples": tuple(binary_sufficient_examples),
        "higher_order_examples": tuple(higher_order_examples),
        "custom_tree_warning": (
            pc_tree_kind in CUSTOM_PC_TREE_KINDS
            and "custom stress tree; not claimed to satisfy the T=T(D) promise"
        ),
    }


def _summarize_rows(rows: list[dict]) -> dict:
    projection_set_kind_histogram: dict = {}
    target_vertex_count_histogram: dict = {}
    min_required_arity_histogram: dict = {}
    restrictive_edge_histogram: dict = {}
    min_higher_order_values = [
        row["min_higher_order_projection_count"]
        for row in rows
        if row["min_higher_order_projection_count"] is not None
    ]
    for row in rows:
        _merge_histogram(
            projection_set_kind_histogram,
            row["projection_set_kind_histogram"],
        )
        _merge_histogram(
            target_vertex_count_histogram,
            row["target_vertex_count_histogram"],
        )
        _merge_histogram(
            min_required_arity_histogram,
            row["min_required_arity_histogram"],
        )
        _merge_histogram(restrictive_edge_histogram, row["restrictive_edge_histogram"])
    return {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "frontier_truncated_rows": sum(1 for row in rows if row["frontier_truncated"]),
        "sample_exhausted_rows": sum(1 for row in rows if row["sample_exhausted"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "rows_with_cycle_targets": sum(
            1 for row in rows if row["cycle_target_projection_count"]
        ),
        "open_obligation_projection_count": sum(
            row["open_obligation_projection_count"] for row in rows
        ),
        "cycle_target_projection_count": sum(
            row["cycle_target_projection_count"] for row in rows
        ),
        "target_same_side_count": sum(row["target_same_side_count"] for row in rows),
        "total_set_count": sum(row["total_set_count"] for row in rows),
        "sampled_index_set_count": sum(row["sampled_index_set_count"] for row in rows),
        "sampled_set_count": sum(row["sampled_set_count"] for row in rows),
        "visible_case_count": sum(row["visible_case_count"] for row in rows),
        "product_capped_case_count": sum(
            row["product_capped_case_count"] for row in rows
        ),
        "unary_sufficient_case_count": sum(
            row["unary_sufficient_case_count"] for row in rows
        ),
        "binary_sufficient_case_count": sum(
            row["binary_sufficient_case_count"] for row in rows
        ),
        "higher_order_case_count": sum(row["higher_order_case_count"] for row in rows),
        "product_false_case_count": sum(
            row["product_false_case_count"] for row in rows
        ),
        "product_false_tuple_count": sum(
            row["product_false_tuple_count"] for row in rows
        ),
        "pairwise_false_tuple_count": sum(
            row["pairwise_false_tuple_count"] for row in rows
        ),
        "rows_with_higher_order_cases": sum(
            1 for row in rows if row["higher_order_case_count"]
        ),
        "rows_with_product_capping": sum(
            1 for row in rows if row["product_capped_case_count"]
        ),
        "restrictive_edge_count_total": sum(
            row["restrictive_edge_count_total"] for row in rows
        ),
        "visible_cases_with_restrictive_edges": sum(
            row["visible_cases_with_restrictive_edges"] for row in rows
        ),
        "max_product_size": max((row["max_product_size"] for row in rows), default=0),
        "max_closure_size": max((row["max_closure_size"] for row in rows), default=0),
        "max_actual_relation_size": max(
            (row["max_actual_relation_size"] for row in rows),
            default=0,
        ),
        "max_false_count": max((row["max_false_count"] for row in rows), default=0),
        "min_higher_order_projection_count": (
            min(min_higher_order_values) if min_higher_order_values else None
        ),
        "projection_set_kind_histogram": _histogram_sorted(
            projection_set_kind_histogram
        ),
        "target_vertex_count_histogram": _histogram_sorted(
            target_vertex_count_histogram
        ),
        "min_required_arity_histogram": _histogram_sorted(
            min_required_arity_histogram
        ),
        "restrictive_edge_histogram": dict(sorted(restrictive_edge_histogram.items())),
    }


def run_probe(
    *,
    set_sizes: list[int],
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    gap_modes: list[str],
    frontier_limit: int,
    include_full_target_set: bool,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
    unknown_gap_modes = set(gap_modes) - GAP_MODES
    if unknown_gap_modes:
        raise ValueError(f"unknown gap modes: {sorted(unknown_gap_modes)}")
    rows = []
    skipped = []
    for n in sizes:
        for pc_tree_kind in pc_trees:
            for instance_kind in instance_kinds:
                if not _is_applicable(instance_kind, n):
                    skipped.append(
                        {
                            "n": n,
                            "pc_tree_kind": pc_tree_kind,
                            "instance_kind": instance_kind,
                            "reason": "not_applicable",
                        }
                    )
                    continue
                for gap_mode in gap_modes:
                    row_seed = (
                        seed
                        + 1009 * n
                        + _stable_offset(pc_tree_kind, instance_kind, gap_mode)
                    )
                    rows.append(
                        _row(
                            n=n,
                            pc_tree_kind=pc_tree_kind,
                            instance_kind=instance_kind,
                            gap_mode=gap_mode,
                            seed=row_seed,
                            frontier_limit=frontier_limit,
                            set_sizes=set_sizes,
                            include_full_target_set=include_full_target_set,
                            scope=scope,
                            sample_count=sample_count,
                            max_attempt_multiplier=max_attempt_multiplier,
                            max_product_size=max_product_size,
                            max_examples=max_examples,
                        )
                    )

    by_pc_tree = {}
    for pc_tree_kind in pc_trees:
        tree_rows = [row for row in rows if row["pc_tree_kind"] == pc_tree_kind]
        by_pc_tree[pc_tree_kind] = _summarize_rows(tree_rows)
    by_instance_kind = {}
    for instance_kind in instance_kinds:
        instance_rows = [
            row for row in rows if row["instance_kind"] == instance_kind
        ]
        by_instance_kind[instance_kind] = _summarize_rows(instance_rows)
    by_gap_mode = {}
    for gap_mode in gap_modes:
        gap_rows = [row for row in rows if row["gap_mode"] == gap_mode]
        by_gap_mode[gap_mode] = _summarize_rows(gap_rows)

    summary = _summarize_rows(rows)
    summary["gap_modes_with_higher_order_cases"] = [
        gap_mode
        for gap_mode in gap_modes
        if by_gap_mode[gap_mode]["higher_order_case_count"]
    ]
    summary["interpretation"] = (
        "T104 is a targeted high-cycle/low-hub parity stress. A higher-order "
        "case in current_gap can be a quotient artifact; the stronger signal "
        "is whether it survives gap_with_distance. Custom cycle_pair_* rows are "
        "adversarial and not a proof about promised Hsu/McConnell trees."
    )

    return {
        "method": "t104_context_gap_parity_cycle_probe",
        "set_sizes": set_sizes,
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "gap_modes": gap_modes,
        "frontier_limit": frontier_limit,
        "include_full_target_set": include_full_target_set,
        "scope": scope,
        "sample_count": sample_count,
        "max_attempt_multiplier": max_attempt_multiplier,
        "max_product_size": max_product_size,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "by_pc_tree": by_pc_tree,
        "by_instance_kind": by_instance_kind,
        "by_gap_mode": by_gap_mode,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set-sizes", default="4,5,6,8", type=_parse_ints)
    parser.add_argument("--sizes", default="7,8,9,10", type=_parse_ints)
    parser.add_argument(
        "--pc-trees",
        default="cycle_pair_p,cycle_pair_c,mixed",
        type=_parse_strings,
    )
    parser.add_argument(
        "--instance-kinds",
        default="even_high_cycle_low_hub,odd_high_cycle_low_hub",
        type=_parse_strings,
    )
    parser.add_argument(
        "--gap-modes",
        default="current_gap,gap_with_distance",
        type=_parse_strings,
    )
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument(
        "--no-full-target-set",
        action="store_true",
        help="do not include the full selected cycle-target set as a tuple",
    )
    parser.add_argument(
        "--scope",
        choices=("all_open", "support_open", "projection_only_open"),
        default="all_open",
    )
    parser.add_argument("--sample-count", type=int, default=2000)
    parser.add_argument("--max-attempt-multiplier", type=int, default=20)
    parser.add_argument("--max-product-size", type=int, default=100000)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_parity_cycle_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        set_sizes=args.set_sizes,
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        gap_modes=args.gap_modes,
        frontier_limit=args.frontier_limit,
        include_full_target_set=not args.no_full_target_set,
        scope=args.scope,
        sample_count=args.sample_count,
        max_attempt_multiplier=args.max_attempt_multiplier,
        max_product_size=args.max_product_size,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
