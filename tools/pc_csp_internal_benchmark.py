#!/usr/bin/env python3
"""Internal benchmark for Piste C CSP/nogood experiments.

This tool is intentionally separate from the candidate benchmark.  It measures
the experimental CSP machinery without changing the public solver contract.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import instance_by_kind  # noqa: E402
from pc_circular.pc_tree import balanced_pc_tree  # noqa: E402
from pc_circular.solvers.sat_like_experiments import (  # noqa: E402
    accepted_frontiers_by_csp,
    bad_side_grouped_support_outcome_profile,
    compile_bad_side_nogoods_grouped_first_hit_support_local,
    compile_bad_side_nogoods_grouped_support_local,
    compile_bad_side_nogoods_support_local,
    compile_cr_nogoods,
    component_mask_quotient_context_collision_profile,
    component_mask_open_boundary_profile,
    quartet_pc_scope_report,
    solve_pruned_nogood_csp_from_compilation,
)


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _pc_tree(kind: str, n: int):
    if kind == "balanced":
        return balanced_pc_tree(n, kind="C")
    if kind == "mixed":
        return balanced_pc_tree(n, kind="mixed")
    raise ValueError(f"unsupported internal CSP pc-tree kind: {kind}")


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def _signature_set(compilation: dict) -> set[tuple]:
    return {
        tuple((path, tuple(choice)) for path, choice in nogood["signature"])
        for nogood in compilation["nogoods"]
    }


def _aggregate_component_mask_quotients(rows: Sequence[dict]) -> dict:
    aggregate: dict[str, dict] = {}
    total_assignments = sum(
        row["profile_hit_assignments"] + row["profile_no_hit_assignments"] for row in rows
    )
    for row in rows:
        for name, quotient in row["profile_component_mask_quotients"].items():
            target = aggregate.setdefault(
                name,
                {
                    "state_count": 0,
                    "hit_state_count": 0,
                    "no_hit_state_count": 0,
                    "mixed_count": 0,
                    "max_bucket_size": 0,
                    "ratio": 0.0,
                    "average_bucket_size": 0.0,
                },
            )
            target["state_count"] += quotient["state_count"]
            target["hit_state_count"] += quotient["hit_state_count"]
            target["no_hit_state_count"] += quotient["no_hit_state_count"]
            target["mixed_count"] += quotient["mixed_count"]
            target["max_bucket_size"] = max(target["max_bucket_size"], quotient["max_bucket_size"])
    for quotient in aggregate.values():
        if total_assignments:
            quotient["ratio"] = quotient["state_count"] / total_assignments
        if quotient["state_count"]:
            quotient["average_bucket_size"] = total_assignments / quotient["state_count"]
    return dict(sorted(aggregate.items()))


def _aggregate_quotient_context_collisions(rows: Sequence[dict]) -> dict:
    aggregate: dict[str, dict] = {}
    total_assignments = sum(row["context_collision_assignments_seen"] for row in rows)
    for row in rows:
        for name, quotient in row["context_collision_quotients"].items():
            target = aggregate.setdefault(
                name,
                {
                    "state_count": 0,
                    "mixed_count": 0,
                    "max_bucket_size": 0,
                    "ratio": 0.0,
                    "average_bucket_size": 0.0,
                    "mixed_ratio": 0.0,
                },
            )
            target["state_count"] += quotient["state_count"]
            target["mixed_count"] += quotient["mixed_count"]
            target["max_bucket_size"] = max(target["max_bucket_size"], quotient["max_bucket_size"])
    for quotient in aggregate.values():
        if total_assignments:
            quotient["ratio"] = quotient["state_count"] / total_assignments
        if quotient["state_count"]:
            quotient["average_bucket_size"] = total_assignments / quotient["state_count"]
            quotient["mixed_ratio"] = quotient["mixed_count"] / quotient["state_count"]
    return dict(sorted(aggregate.items()))


def _aggregate_open_boundary_states(rows: Sequence[dict]) -> dict:
    aggregate: dict[str, dict] = {}
    total_assignments = sum(row["open_boundary_local_assignments_seen"] for row in rows)
    for row in rows:
        for name, state in row["open_boundary_states"].items():
            target = aggregate.setdefault(
                name,
                {
                    "state_count": 0,
                    "max_bucket_size": 0,
                    "ratio": 0.0,
                    "average_bucket_size": 0.0,
                    "boundary_mixed_count": 0,
                    "boundary_mixed_ratio": 0.0,
                    "local_hit_mixed_count": 0,
                    "local_hit_mixed_ratio": 0.0,
                },
            )
            target["state_count"] += state["state_count"]
            target["max_bucket_size"] = max(target["max_bucket_size"], state["max_bucket_size"])
            target["boundary_mixed_count"] += state.get("boundary_mixed_count", 0)
            target["local_hit_mixed_count"] += state.get("local_hit_mixed_count", 0)
    for state in aggregate.values():
        if total_assignments:
            state["ratio"] = state["state_count"] / total_assignments
        if state["state_count"]:
            state["average_bucket_size"] = total_assignments / state["state_count"]
            state["boundary_mixed_ratio"] = state["boundary_mixed_count"] / state["state_count"]
            state["local_hit_mixed_ratio"] = state["local_hit_mixed_count"] / state["state_count"]
    return dict(sorted(aggregate.items()))


def _sum_histograms(rows: Sequence[dict], field: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        for key, value in row[field].items():
            text_key = str(key)
            result[text_key] = result.get(text_key, 0) + value
    return dict(sorted(result.items(), key=lambda item: int(item[0])))


def run_benchmark(
    *,
    sizes: Sequence[int],
    repeats: int,
    instance_kinds: Sequence[str],
    pc_trees: Sequence[str],
    max_p_degree: int,
    seed: int,
    validate: bool,
) -> dict:
    rng = random.Random(seed)
    rows: list[dict] = []

    for n in sizes:
        for tree_kind in pc_trees:
            T = _pc_tree(tree_kind, n)
            for instance_kind in instance_kinds:
                for repeat in range(repeats):
                    D = instance_by_kind(n, kind=instance_kind, rng=rng, values=(1, 2, 3))

                    compile_start = time.perf_counter()
                    compilation = compile_cr_nogoods(D, T, max_p_degree=max_p_degree)
                    compile_seconds = time.perf_counter() - compile_start

                    solve_start = time.perf_counter()
                    solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    solve_seconds = time.perf_counter() - solve_start

                    support_compile_start = time.perf_counter()
                    support_compilation = compile_bad_side_nogoods_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    support_compile_seconds = time.perf_counter() - support_compile_start

                    support_solve_start = time.perf_counter()
                    support_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        support_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    support_solve_seconds = time.perf_counter() - support_solve_start

                    grouped_compile_start = time.perf_counter()
                    grouped_compilation = compile_bad_side_nogoods_grouped_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    grouped_compile_seconds = time.perf_counter() - grouped_compile_start

                    grouped_solve_start = time.perf_counter()
                    grouped_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        grouped_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    grouped_solve_seconds = time.perf_counter() - grouped_solve_start

                    first_hit_compile_start = time.perf_counter()
                    first_hit_compilation = compile_bad_side_nogoods_grouped_first_hit_support_local(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    first_hit_compile_seconds = time.perf_counter() - first_hit_compile_start

                    profile_start = time.perf_counter()
                    support_outcome_profile = bad_side_grouped_support_outcome_profile(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                        max_groups=3,
                    )
                    profile_seconds = time.perf_counter() - profile_start

                    context_collision_start = time.perf_counter()
                    context_collision_profile = component_mask_quotient_context_collision_profile(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                        max_pairs=20,
                    )
                    context_collision_seconds = time.perf_counter() - context_collision_start

                    open_boundary_start = time.perf_counter()
                    open_boundary_profile = component_mask_open_boundary_profile(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                        max_pairs=20,
                    )
                    open_boundary_seconds = time.perf_counter() - open_boundary_start

                    quartet_scope_start = time.perf_counter()
                    quartet_scope_profile = quartet_pc_scope_report(
                        D,
                        T,
                        max_p_degree=max_p_degree,
                    )
                    quartet_scope_seconds = time.perf_counter() - quartet_scope_start

                    first_hit_solve_start = time.perf_counter()
                    first_hit_solve_result = solve_pruned_nogood_csp_from_compilation(
                        D,
                        T,
                        first_hit_compilation,
                        max_p_degree=max_p_degree,
                        validate_against_direct=False,
                    )
                    first_hit_solve_seconds = time.perf_counter() - first_hit_solve_start

                    direct_seconds = None
                    mismatch = False
                    support_mismatch = False
                    grouped_mismatch = False
                    first_hit_mismatch = False
                    if validate and not solve_result["unsupported"]:
                        direct_start = time.perf_counter()
                        direct = accepted_frontiers_by_csp(
                            D,
                            T,
                            source="cr",
                            max_p_degree=max_p_degree,
                        )
                        direct_seconds = time.perf_counter() - direct_start
                        actual = {tuple(order) for order in solve_result["accepted_frontiers"]}
                        support_actual = {
                            tuple(order) for order in support_solve_result["accepted_frontiers"]
                        }
                        grouped_actual = {
                            tuple(order) for order in grouped_solve_result["accepted_frontiers"]
                        }
                        first_hit_actual = {
                            tuple(order) for order in first_hit_solve_result["accepted_frontiers"]
                        }
                        mismatch = actual != direct
                        support_mismatch = support_actual != direct
                        grouped_mismatch = grouped_actual != direct
                        first_hit_mismatch = first_hit_actual != direct

                    counts = solve_result["counts"]
                    compile_counts = compilation["counts"]
                    support_counts = support_solve_result["counts"]
                    support_compile_counts = support_compilation["counts"]
                    grouped_counts = grouped_solve_result["counts"]
                    grouped_compile_counts = grouped_compilation["counts"]
                    first_hit_counts = first_hit_solve_result["counts"]
                    first_hit_compile_counts = first_hit_compilation["counts"]
                    profile_counts = support_outcome_profile["counts"]
                    context_collision_counts = context_collision_profile["counts"]
                    open_boundary_counts = open_boundary_profile["counts"]
                    quartet_scope_counts = quartet_scope_profile["counts"]
                    signatures = _signature_set(compilation)
                    support_signatures = _signature_set(support_compilation)
                    grouped_signatures = _signature_set(grouped_compilation)
                    first_hit_signatures = _signature_set(first_hit_compilation)
                    old_scan_work = counts["full_assignment_space"] * max(1, len(support_compilation["atoms"]))
                    support_vs_old_scan_ratio = (
                        support_compile_counts["support_product_total"] / old_scan_work
                        if old_scan_work
                        else 0.0
                    )
                    rows.append(
                        {
                            "n": n,
                            "pc_tree": tree_kind,
                            "instance_kind": instance_kind,
                            "repeat": repeat,
                            "supported": not solve_result["unsupported"],
                            "complete": solve_result["complete"],
                            "mismatch": mismatch,
                            "support_mismatch": support_mismatch,
                            "grouped_mismatch": grouped_mismatch,
                            "first_hit_mismatch": first_hit_mismatch,
                            "compile_seconds": compile_seconds,
                            "solve_seconds": solve_seconds,
                            "support_compile_seconds": support_compile_seconds,
                            "support_solve_seconds": support_solve_seconds,
                            "grouped_compile_seconds": grouped_compile_seconds,
                            "grouped_solve_seconds": grouped_solve_seconds,
                            "first_hit_compile_seconds": first_hit_compile_seconds,
                            "support_outcome_profile_seconds": profile_seconds,
                            "context_collision_profile_seconds": context_collision_seconds,
                            "open_boundary_profile_seconds": open_boundary_seconds,
                            "quartet_scope_report_seconds": quartet_scope_seconds,
                            "first_hit_solve_seconds": first_hit_solve_seconds,
                            "direct_seconds": direct_seconds,
                            "atoms": len(compilation["atoms"]),
                            "unique_nogoods": compile_counts["unique_nogoods"],
                            "support_atoms": len(support_compilation["atoms"]),
                            "support_unique_nogoods": support_compile_counts["unique_nogoods"],
                            "grouped_atoms": len(grouped_compilation["atoms"]),
                            "grouped_unique_nogoods": grouped_compile_counts["unique_nogoods"],
                            "first_hit_atoms": len(first_hit_compilation["atoms"]),
                            "first_hit_unique_nogoods": first_hit_compile_counts["unique_nogoods"],
                            "effective_nogood_signatures": len(signatures),
                            "support_effective_nogood_signatures": len(support_signatures),
                            "grouped_effective_nogood_signatures": len(grouped_signatures),
                            "first_hit_effective_nogood_signatures": len(first_hit_signatures),
                            "same_effective_signatures": signatures == support_signatures,
                            "same_grouped_effective_signatures": signatures == grouped_signatures,
                            "same_support_and_grouped_signatures": support_signatures == grouped_signatures,
                            "same_first_hit_effective_signatures": signatures == first_hit_signatures,
                            "same_grouped_and_first_hit_signatures": grouped_signatures == first_hit_signatures,
                            "support_assignments_seen": support_compile_counts["support_assignments_seen"],
                            "support_product_total": support_compile_counts["support_product_total"],
                            "support_max_product": support_compile_counts["max_support_product"],
                            "support_vs_old_scan_ratio": support_vs_old_scan_ratio,
                            "grouped_support_assignments_seen": grouped_compile_counts[
                                "grouped_support_assignments_seen"
                            ],
                            "grouped_support_product_total": grouped_compile_counts[
                                "grouped_support_product_total"
                            ],
                            "grouped_support_product_total_if_ungrouped": grouped_compile_counts[
                                "support_product_total_if_ungrouped"
                            ],
                            "grouped_atom_checks": grouped_compile_counts["atom_checks"],
                            "grouped_support_group_count": grouped_compile_counts["support_group_count"],
                            "grouped_max_atoms_per_support": grouped_compile_counts["max_atoms_per_support"],
                            "grouped_vs_ungrouped_support_ratio": grouped_compile_counts[
                                "grouped_vs_ungrouped_support_ratio"
                            ],
                            "first_hit_support_assignments_seen": first_hit_compile_counts[
                                "grouped_support_assignments_seen"
                            ],
                            "first_hit_support_product_total": first_hit_compile_counts[
                                "grouped_support_product_total"
                            ],
                            "first_hit_atom_checks": first_hit_compile_counts["atom_checks"],
                            "first_hit_atom_checks_if_exhaustive": first_hit_compile_counts[
                                "atom_checks_if_exhaustive"
                            ],
                            "first_hit_atom_checks_if_exhaustive_seen": first_hit_compile_counts[
                                "atom_checks_if_exhaustive_seen"
                            ],
                            "first_hit_atom_checks_saved": first_hit_compile_counts[
                                "atom_checks_saved_by_first_hit"
                            ],
                            "first_hit_assignments": first_hit_compile_counts["first_hit_assignments"],
                            "first_hit_no_hit_assignments": first_hit_compile_counts[
                                "first_hit_no_hit_assignments"
                            ],
                            "first_hit_max_position": first_hit_compile_counts["first_hit_max_position"],
                            "first_hit_position_sum": first_hit_compile_counts[
                                "first_hit_position_sum"
                            ],
                            "first_hit_average_position": first_hit_compile_counts[
                                "first_hit_average_position"
                            ],
                            "first_hit_checks_spent_on_no_hit": first_hit_compile_counts[
                                "first_hit_checks_spent_on_no_hit"
                            ],
                            "first_hit_checks_saved_on_hits": first_hit_compile_counts[
                                "first_hit_checks_saved_on_hits"
                            ],
                            "first_hit_position_histogram": first_hit_compile_counts[
                                "first_hit_position_histogram"
                            ],
                            "profile_complete": support_outcome_profile["complete"],
                            "profile_support_group_count": profile_counts["support_group_count"],
                            "profile_groups_profiled": profile_counts["groups_profiled"],
                            "profile_hit_assignments": profile_counts["hit_assignments"],
                            "profile_no_hit_assignments": profile_counts["no_hit_assignments"],
                            "profile_classification_atom_checks": profile_counts[
                                "classification_atom_checks"
                            ],
                            "profile_exhaustive_atom_checks_seen": profile_counts[
                                "exhaustive_atom_checks_seen"
                            ],
                            "profile_no_hit_exhaustive_atom_checks": profile_counts[
                                "no_hit_exhaustive_atom_checks"
                            ],
                            "profile_unary_no_hit_certified_assignments": profile_counts[
                                "unary_no_hit_certified_assignments"
                            ],
                            "profile_pair_side_split_hit_assignments": profile_counts[
                                "pair_side_split_hit_assignments"
                            ],
                            "profile_pair_side_split_no_hit_assignments": profile_counts[
                                "pair_side_split_no_hit_assignments"
                            ],
                            "profile_pair_side_split_checks": profile_counts[
                                "pair_side_split_checks"
                            ],
                            "profile_pair_side_split_side_checks": profile_counts[
                                "pair_side_split_side_checks"
                            ],
                            "profile_pair_side_split_side_cache_hits": profile_counts[
                                "pair_side_split_side_cache_hits"
                            ],
                            "profile_pair_side_split_side_cache_misses": profile_counts[
                                "pair_side_split_side_cache_misses"
                            ],
                            "profile_pair_side_split_component_checks": profile_counts[
                                "pair_side_split_component_checks"
                            ],
                            "profile_pair_side_split_component_witness_checks": profile_counts[
                                "pair_side_split_component_witness_checks"
                            ],
                            "profile_pair_side_split_cached_checks": profile_counts[
                                "pair_side_split_cached_checks"
                            ],
                            "profile_pair_side_split_bitset_cached_checks": profile_counts[
                                "pair_side_split_bitset_cached_checks"
                            ],
                            "profile_pair_side_split_bitset_hit_assignments": profile_counts[
                                "pair_side_split_bitset_hit_assignments"
                            ],
                            "profile_pair_side_split_bitset_no_hit_assignments": profile_counts[
                                "pair_side_split_bitset_no_hit_assignments"
                            ],
                            "profile_pair_side_split_bitset_checks": profile_counts[
                                "pair_side_split_bitset_checks"
                            ],
                            "profile_pair_side_split_bitset_component_checks": profile_counts[
                                "pair_side_split_bitset_component_checks"
                            ],
                            "profile_pair_side_split_bitset_component_cache_hits": profile_counts[
                                "pair_side_split_bitset_component_cache_hits"
                            ],
                            "profile_pair_side_split_bitset_component_cache_misses": profile_counts[
                                "pair_side_split_bitset_component_cache_misses"
                            ],
                            "profile_pair_side_split_bitset_witness_visits": profile_counts[
                                "pair_side_split_bitset_witness_visits"
                            ],
                            "profile_pair_side_split_bitset_side_cache_hits": profile_counts[
                                "pair_side_split_bitset_side_cache_hits"
                            ],
                            "profile_pair_side_split_bitset_side_cache_misses": profile_counts[
                                "pair_side_split_bitset_side_cache_misses"
                            ],
                            "profile_pair_side_split_bitset_projection_checks": profile_counts[
                                "pair_side_split_bitset_projection_checks"
                            ],
                            "profile_pair_side_split_bitset_mismatches": profile_counts[
                                "pair_side_split_bitset_mismatches"
                            ],
                            "profile_pair_side_split_mismatches": profile_counts[
                                "pair_side_split_mismatches"
                            ],
                            "profile_pair_side_split_work_ratio": profile_counts[
                                "pair_side_split_work_ratio"
                            ],
                            "profile_pair_side_split_cached_work_ratio": profile_counts[
                                "pair_side_split_cached_work_ratio"
                            ],
                            "profile_pair_side_split_bitset_cached_work_ratio": profile_counts[
                                "pair_side_split_bitset_cached_work_ratio"
                            ],
                            "profile_pair_side_split_bitset_work_ratio": profile_counts[
                                "pair_side_split_bitset_work_ratio"
                            ],
                            "profile_pair_side_split_bitset_projection_work_ratio": profile_counts[
                                "pair_side_split_bitset_projection_work_ratio"
                            ],
                            "profile_component_mask_state_count": profile_counts[
                                "component_mask_state_count"
                            ],
                            "profile_component_mask_state_hit_count": profile_counts[
                                "component_mask_state_hit_count"
                            ],
                            "profile_component_mask_state_no_hit_count": profile_counts[
                                "component_mask_state_no_hit_count"
                            ],
                            "profile_component_mask_state_mixed_count": profile_counts[
                                "component_mask_state_mixed_count"
                            ],
                            "profile_component_mask_state_mismatches": profile_counts[
                                "component_mask_state_mismatches"
                            ],
                            "profile_component_mask_state_max_bucket_size": profile_counts[
                                "component_mask_state_max_bucket_size"
                            ],
                            "profile_component_mask_state_ratio": profile_counts[
                                "component_mask_state_ratio"
                            ],
                            "profile_component_mask_state_average_bucket_size": profile_counts[
                                "component_mask_state_average_bucket_size"
                            ],
                            "profile_component_mask_state_component_masks": profile_counts[
                                "component_mask_state_component_masks"
                            ],
                            "profile_component_mask_state_witness_visits": profile_counts[
                                "component_mask_state_witness_visits"
                            ],
                            "profile_component_mask_state_side_cache_hits": profile_counts[
                                "component_mask_state_side_cache_hits"
                            ],
                            "profile_component_mask_state_side_cache_misses": profile_counts[
                                "component_mask_state_side_cache_misses"
                            ],
                            "profile_component_mask_state_work_ratio": profile_counts[
                                "component_mask_state_work_ratio"
                            ],
                            "profile_component_mask_state_projection_work_ratio": profile_counts[
                                "component_mask_state_projection_work_ratio"
                            ],
                            "profile_component_mask_quotients": profile_counts[
                                "component_mask_quotients"
                            ],
                            "context_collision_complete": context_collision_profile["complete"],
                            "context_collision_support_group_count": context_collision_counts[
                                "support_group_count"
                            ],
                            "context_collision_pair_count": context_collision_counts[
                                "context_pair_count"
                            ],
                            "context_collision_pairs_profiled": context_collision_counts[
                                "pairs_profiled"
                            ],
                            "context_collision_assignments_seen": context_collision_counts[
                                "context_assignments_seen"
                            ],
                            "context_collision_max_context_support_product": (
                                context_collision_counts["max_context_support_product"]
                            ),
                            "context_collision_quotients": context_collision_profile["quotients"],
                            "open_boundary_complete": open_boundary_profile["complete"],
                            "open_boundary_support_group_count": open_boundary_counts[
                                "support_group_count"
                            ],
                            "open_boundary_context_pair_count": open_boundary_counts[
                                "context_pair_count"
                            ],
                            "open_boundary_pairs_profiled": open_boundary_counts[
                                "pairs_profiled"
                            ],
                            "open_boundary_local_assignments_seen": open_boundary_counts[
                                "local_assignments_seen"
                            ],
                            "open_boundary_response_checks": open_boundary_counts[
                                "boundary_response_checks"
                            ],
                            "open_boundary_entries_total": open_boundary_counts[
                                "boundary_entries_total"
                            ],
                            "open_boundary_max_boundary_entries_per_assignment": (
                                open_boundary_counts["max_boundary_entries_per_assignment"]
                            ),
                            "open_boundary_average_boundary_entries_per_assignment": (
                                open_boundary_counts["average_boundary_entries_per_assignment"]
                            ),
                            "open_boundary_max_context_support_product": open_boundary_counts[
                                "max_context_support_product"
                            ],
                            "open_boundary_states": open_boundary_profile["states"],
                            "quartet_scope_complete": quartet_scope_profile["complete"],
                            "quartet_scope_quartet_count": quartet_scope_counts["quartet_count"],
                            "quartet_scope_quartets_profiled": quartet_scope_counts[
                                "quartets_profiled"
                            ],
                            "quartet_scope_support_assignments_seen": quartet_scope_counts[
                                "support_assignments_seen"
                            ],
                            "quartet_scope_support_scope_gt_2_count": quartet_scope_counts[
                                "support_scope_gt_2_count"
                            ],
                            "quartet_scope_effective_type_scope_gt_2_count": (
                                quartet_scope_counts["effective_type_scope_gt_2_count"]
                            ),
                            "quartet_scope_effective_acceptance_scope_gt_2_count": (
                                quartet_scope_counts["effective_acceptance_scope_gt_2_count"]
                            ),
                            "quartet_scope_two_sat_candidate_quartet_count": (
                                quartet_scope_counts["two_sat_candidate_quartet_count"]
                            ),
                            "quartet_scope_non_boolean_effective_acceptance_scope_count": (
                                quartet_scope_counts["non_boolean_effective_acceptance_scope_count"]
                            ),
                            "quartet_scope_projection_mismatch_count": quartet_scope_counts[
                                "projection_mismatch_count"
                            ],
                            "quartet_scope_allowed_type_total": quartet_scope_counts[
                                "allowed_type_total"
                            ],
                            "quartet_scope_realisable_type_total": quartet_scope_counts[
                                "realisable_type_total"
                            ],
                            "quartet_scope_accepted_signature_total": quartet_scope_counts[
                                "accepted_signature_total"
                            ],
                            "quartet_scope_rejected_signature_total": quartet_scope_counts[
                                "rejected_signature_total"
                            ],
                            "quartet_scope_max_support_size": quartet_scope_counts[
                                "max_support_size"
                            ],
                            "quartet_scope_max_effective_type_scope_size": quartet_scope_counts[
                                "max_effective_type_scope_size"
                            ],
                            "quartet_scope_max_effective_acceptance_scope_size": (
                                quartet_scope_counts["max_effective_acceptance_scope_size"]
                            ),
                            "quartet_scope_max_support_domain_product": quartet_scope_counts[
                                "max_support_domain_product"
                            ],
                            "quartet_scope_support_size_histogram": quartet_scope_counts[
                                "support_size_histogram"
                            ],
                            "quartet_scope_effective_type_scope_size_histogram": (
                                quartet_scope_counts["effective_type_scope_size_histogram"]
                            ),
                            "quartet_scope_effective_acceptance_scope_size_histogram": (
                                quartet_scope_counts["effective_acceptance_scope_size_histogram"]
                            ),
                            "profile_ambiguous_no_hit_assignments": profile_counts[
                                "ambiguous_no_hit_assignments"
                            ],
                            "profile_unary_hit_certified_assignments": profile_counts[
                                "unary_hit_certified_assignments"
                            ],
                            "profile_ambiguous_hit_assignments": profile_counts[
                                "ambiguous_hit_assignments"
                            ],
                            "profile_unary_no_hit_coverage_ratio": profile_counts[
                                "unary_no_hit_coverage_ratio"
                            ],
                            "profile_ambiguous_no_hit_ratio": profile_counts[
                                "ambiguous_no_hit_ratio"
                            ],
                            "profile_no_hit_assignment_ratio": profile_counts[
                                "no_hit_assignment_ratio"
                            ],
                            "profile_max_group_no_hit_exhaustive_atom_checks": profile_counts[
                                "max_group_no_hit_exhaustive_atom_checks"
                            ],
                            "atoms_with_nogoods": compile_counts["atoms_with_nogoods"],
                            "max_support_size": compile_counts["max_support_size"],
                            "support_size_histogram": compile_counts["support_size_histogram"],
                            "full_assignment_space": counts["full_assignment_space"],
                            "leaf_assignments_seen": counts["leaf_assignments_seen"],
                            "branches_considered": counts["branches_considered"],
                            "branches_pruned": counts["branches_pruned"],
                            "pruning_rate": counts.get("pruning_rate", 0.0),
                            "accepted_frontiers": counts["accepted_frontiers"],
                            "support_leaf_assignments_seen": support_counts["leaf_assignments_seen"],
                            "support_branches_pruned": support_counts["branches_pruned"],
                            "support_accepted_frontiers": support_counts["accepted_frontiers"],
                            "grouped_leaf_assignments_seen": grouped_counts["leaf_assignments_seen"],
                            "grouped_branches_pruned": grouped_counts["branches_pruned"],
                            "grouped_accepted_frontiers": grouped_counts["accepted_frontiers"],
                            "first_hit_leaf_assignments_seen": first_hit_counts["leaf_assignments_seen"],
                            "first_hit_branches_pruned": first_hit_counts["branches_pruned"],
                            "first_hit_accepted_frontiers": first_hit_counts["accepted_frontiers"],
                        }
                    )

    supported_rows = [row for row in rows if row["supported"]]
    return {
        "config": {
            "sizes": list(sizes),
            "repeats": repeats,
            "instance_kinds": list(instance_kinds),
            "pc_trees": list(pc_trees),
            "max_p_degree": max_p_degree,
            "seed": seed,
            "validate": validate,
        },
        "summary": {
            "rows": len(rows),
            "supported_rows": len(supported_rows),
            "mismatches": sum(1 for row in rows if row["mismatch"]),
            "support_mismatches": sum(1 for row in rows if row["support_mismatch"]),
            "grouped_mismatches": sum(1 for row in rows if row["grouped_mismatch"]),
            "first_hit_mismatches": sum(1 for row in rows if row["first_hit_mismatch"]),
            "signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_effective_signatures"]
            ),
            "grouped_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_grouped_effective_signatures"]
            ),
            "support_grouped_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_support_and_grouped_signatures"]
            ),
            "first_hit_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_first_hit_effective_signatures"]
            ),
            "grouped_first_hit_signature_mismatches": sum(
                1 for row in rows if row["supported"] and not row["same_grouped_and_first_hit_signatures"]
            ),
            "median_compile_seconds": _median([row["compile_seconds"] for row in supported_rows]),
            "median_support_compile_seconds": _median(
                [row["support_compile_seconds"] for row in supported_rows]
            ),
            "median_grouped_compile_seconds": _median(
                [row["grouped_compile_seconds"] for row in supported_rows]
            ),
            "median_first_hit_compile_seconds": _median(
                [row["first_hit_compile_seconds"] for row in supported_rows]
            ),
            "median_support_outcome_profile_seconds": _median(
                [row["support_outcome_profile_seconds"] for row in supported_rows]
            ),
            "median_context_collision_profile_seconds": _median(
                [row["context_collision_profile_seconds"] for row in supported_rows]
            ),
            "median_open_boundary_profile_seconds": _median(
                [row["open_boundary_profile_seconds"] for row in supported_rows]
            ),
            "median_quartet_scope_report_seconds": _median(
                [row["quartet_scope_report_seconds"] for row in supported_rows]
            ),
            "median_solve_seconds": _median([row["solve_seconds"] for row in supported_rows]),
            "median_support_solve_seconds": _median(
                [row["support_solve_seconds"] for row in supported_rows]
            ),
            "median_grouped_solve_seconds": _median(
                [row["grouped_solve_seconds"] for row in supported_rows]
            ),
            "median_first_hit_solve_seconds": _median(
                [row["first_hit_solve_seconds"] for row in supported_rows]
            ),
            "median_direct_seconds": _median(
                [row["direct_seconds"] for row in supported_rows if row["direct_seconds"] is not None]
            ),
            "total_unique_nogoods": sum(row["unique_nogoods"] for row in supported_rows),
            "total_support_unique_nogoods": sum(row["support_unique_nogoods"] for row in supported_rows),
            "total_grouped_unique_nogoods": sum(row["grouped_unique_nogoods"] for row in supported_rows),
            "total_first_hit_unique_nogoods": sum(
                row["first_hit_unique_nogoods"] for row in supported_rows
            ),
            "total_support_assignments_seen": sum(
                row["support_assignments_seen"] for row in supported_rows
            ),
            "total_support_product": sum(row["support_product_total"] for row in supported_rows),
            "total_grouped_support_assignments_seen": sum(
                row["grouped_support_assignments_seen"] for row in supported_rows
            ),
            "total_grouped_support_product": sum(
                row["grouped_support_product_total"] for row in supported_rows
            ),
            "total_grouped_atom_checks": sum(row["grouped_atom_checks"] for row in supported_rows),
            "total_first_hit_atom_checks": sum(row["first_hit_atom_checks"] for row in supported_rows),
            "total_first_hit_atom_checks_saved": sum(
                row["first_hit_atom_checks_saved"] for row in supported_rows
            ),
            "total_first_hit_atom_checks_if_exhaustive_seen": sum(
                row["first_hit_atom_checks_if_exhaustive_seen"] for row in supported_rows
            ),
            "total_first_hit_assignments": sum(row["first_hit_assignments"] for row in supported_rows),
            "total_first_hit_no_hit_assignments": sum(
                row["first_hit_no_hit_assignments"] for row in supported_rows
            ),
            "total_first_hit_position_sum": sum(
                row["first_hit_position_sum"] for row in supported_rows
            ),
            "total_first_hit_checks_spent_on_no_hit": sum(
                row["first_hit_checks_spent_on_no_hit"] for row in supported_rows
            ),
            "total_first_hit_checks_saved_on_hits": sum(
                row["first_hit_checks_saved_on_hits"] for row in supported_rows
            ),
            "total_profile_no_hit_exhaustive_atom_checks": sum(
                row["profile_no_hit_exhaustive_atom_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_checks": sum(
                row["profile_pair_side_split_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_side_checks": sum(
                row["profile_pair_side_split_side_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_side_cache_hits": sum(
                row["profile_pair_side_split_side_cache_hits"] for row in supported_rows
            ),
            "total_profile_pair_side_split_side_cache_misses": sum(
                row["profile_pair_side_split_side_cache_misses"] for row in supported_rows
            ),
            "total_profile_pair_side_split_component_checks": sum(
                row["profile_pair_side_split_component_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_component_witness_checks": sum(
                row["profile_pair_side_split_component_witness_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_cached_checks": sum(
                row["profile_pair_side_split_cached_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_cached_checks": sum(
                row["profile_pair_side_split_bitset_cached_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_checks": sum(
                row["profile_pair_side_split_bitset_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_component_checks": sum(
                row["profile_pair_side_split_bitset_component_checks"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_component_cache_hits": sum(
                row["profile_pair_side_split_bitset_component_cache_hits"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_component_cache_misses": sum(
                row["profile_pair_side_split_bitset_component_cache_misses"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_witness_visits": sum(
                row["profile_pair_side_split_bitset_witness_visits"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_side_cache_hits": sum(
                row["profile_pair_side_split_bitset_side_cache_hits"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_side_cache_misses": sum(
                row["profile_pair_side_split_bitset_side_cache_misses"] for row in supported_rows
            ),
            "total_profile_pair_side_split_bitset_projection_checks": sum(
                row["profile_pair_side_split_bitset_projection_checks"] for row in supported_rows
            ),
            "profile_pair_side_split_mismatches": sum(
                row["profile_pair_side_split_mismatches"] for row in supported_rows
            ),
            "profile_pair_side_split_bitset_mismatches": sum(
                row["profile_pair_side_split_bitset_mismatches"] for row in supported_rows
            ),
            "total_profile_component_mask_state_count": sum(
                row["profile_component_mask_state_count"] for row in supported_rows
            ),
            "total_profile_component_mask_state_hit_count": sum(
                row["profile_component_mask_state_hit_count"] for row in supported_rows
            ),
            "total_profile_component_mask_state_no_hit_count": sum(
                row["profile_component_mask_state_no_hit_count"] for row in supported_rows
            ),
            "profile_component_mask_state_mixed_count": sum(
                row["profile_component_mask_state_mixed_count"] for row in supported_rows
            ),
            "profile_component_mask_state_mismatches": sum(
                row["profile_component_mask_state_mismatches"] for row in supported_rows
            ),
            "max_profile_component_mask_state_max_bucket_size": max(
                [row["profile_component_mask_state_max_bucket_size"] for row in supported_rows],
                default=0,
            ),
            "total_profile_component_mask_state_component_masks": sum(
                row["profile_component_mask_state_component_masks"] for row in supported_rows
            ),
            "total_profile_component_mask_state_witness_visits": sum(
                row["profile_component_mask_state_witness_visits"] for row in supported_rows
            ),
            "total_profile_component_mask_state_side_cache_hits": sum(
                row["profile_component_mask_state_side_cache_hits"] for row in supported_rows
            ),
            "total_profile_component_mask_state_side_cache_misses": sum(
                row["profile_component_mask_state_side_cache_misses"] for row in supported_rows
            ),
            "profile_component_mask_state_ratio": (
                sum(row["profile_component_mask_state_count"] for row in supported_rows)
                / sum(row["profile_hit_assignments"] + row["profile_no_hit_assignments"] for row in supported_rows)
                if sum(row["profile_hit_assignments"] + row["profile_no_hit_assignments"] for row in supported_rows)
                else 0.0
            ),
            "profile_component_mask_state_average_bucket_size": (
                sum(row["profile_hit_assignments"] + row["profile_no_hit_assignments"] for row in supported_rows)
                / sum(row["profile_component_mask_state_count"] for row in supported_rows)
                if sum(row["profile_component_mask_state_count"] for row in supported_rows)
                else 0.0
            ),
            "profile_component_mask_state_work_ratio": (
                sum(
                    row["profile_component_mask_state_component_masks"]
                    + row["profile_component_mask_state_witness_visits"]
                    for row in supported_rows
                )
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_component_mask_state_projection_work_ratio": (
                sum(
                    row["profile_component_mask_state_component_masks"]
                    + row["profile_component_mask_state_side_cache_misses"]
                    for row in supported_rows
                )
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_component_mask_quotients": _aggregate_component_mask_quotients(
                supported_rows
            ),
            "context_collision_quotients": _aggregate_quotient_context_collisions(
                supported_rows
            ),
            "context_collision_assignments_seen": sum(
                row["context_collision_assignments_seen"] for row in supported_rows
            ),
            "context_collision_pairs_profiled": sum(
                row["context_collision_pairs_profiled"] for row in supported_rows
            ),
            "context_collision_incomplete_rows": sum(
                1 for row in supported_rows if not row["context_collision_complete"]
            ),
            "open_boundary_states": _aggregate_open_boundary_states(supported_rows),
            "open_boundary_local_assignments_seen": sum(
                row["open_boundary_local_assignments_seen"] for row in supported_rows
            ),
            "open_boundary_response_checks": sum(
                row["open_boundary_response_checks"] for row in supported_rows
            ),
            "open_boundary_pairs_profiled": sum(
                row["open_boundary_pairs_profiled"] for row in supported_rows
            ),
            "open_boundary_incomplete_rows": sum(
                1 for row in supported_rows if not row["open_boundary_complete"]
            ),
            "open_boundary_average_boundary_entries_per_assignment": (
                sum(row["open_boundary_entries_total"] for row in supported_rows)
                / sum(row["open_boundary_local_assignments_seen"] for row in supported_rows)
                if sum(row["open_boundary_local_assignments_seen"] for row in supported_rows)
                else 0.0
            ),
            "quartet_scope_incomplete_rows": sum(
                1 for row in supported_rows if not row["quartet_scope_complete"]
            ),
            "quartet_scope_quartets_profiled": sum(
                row["quartet_scope_quartets_profiled"] for row in supported_rows
            ),
            "quartet_scope_support_assignments_seen": sum(
                row["quartet_scope_support_assignments_seen"] for row in supported_rows
            ),
            "quartet_scope_support_scope_gt_2_count": sum(
                row["quartet_scope_support_scope_gt_2_count"] for row in supported_rows
            ),
            "quartet_scope_effective_type_scope_gt_2_count": sum(
                row["quartet_scope_effective_type_scope_gt_2_count"] for row in supported_rows
            ),
            "quartet_scope_effective_acceptance_scope_gt_2_count": sum(
                row["quartet_scope_effective_acceptance_scope_gt_2_count"]
                for row in supported_rows
            ),
            "quartet_scope_two_sat_candidate_quartet_count": sum(
                row["quartet_scope_two_sat_candidate_quartet_count"] for row in supported_rows
            ),
            "quartet_scope_non_boolean_effective_acceptance_scope_count": sum(
                row["quartet_scope_non_boolean_effective_acceptance_scope_count"]
                for row in supported_rows
            ),
            "quartet_scope_projection_mismatches": sum(
                row["quartet_scope_projection_mismatch_count"] for row in supported_rows
            ),
            "quartet_scope_accepted_signature_total": sum(
                row["quartet_scope_accepted_signature_total"] for row in supported_rows
            ),
            "quartet_scope_rejected_signature_total": sum(
                row["quartet_scope_rejected_signature_total"] for row in supported_rows
            ),
            "quartet_scope_max_support_domain_product": max(
                [row["quartet_scope_max_support_domain_product"] for row in supported_rows],
                default=0,
            ),
            "quartet_scope_support_size_histogram": _sum_histograms(
                supported_rows, "quartet_scope_support_size_histogram"
            ),
            "quartet_scope_effective_type_scope_size_histogram": _sum_histograms(
                supported_rows, "quartet_scope_effective_type_scope_size_histogram"
            ),
            "quartet_scope_effective_acceptance_scope_size_histogram": _sum_histograms(
                supported_rows, "quartet_scope_effective_acceptance_scope_size_histogram"
            ),
            "profile_pair_side_split_work_ratio": (
                sum(row["profile_pair_side_split_checks"] for row in supported_rows)
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_pair_side_split_cached_work_ratio": (
                sum(row["profile_pair_side_split_cached_checks"] for row in supported_rows)
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_pair_side_split_bitset_cached_work_ratio": (
                sum(row["profile_pair_side_split_bitset_cached_checks"] for row in supported_rows)
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_pair_side_split_bitset_work_ratio": (
                sum(row["profile_pair_side_split_bitset_checks"] for row in supported_rows)
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "profile_pair_side_split_bitset_projection_work_ratio": (
                sum(row["profile_pair_side_split_bitset_projection_checks"] for row in supported_rows)
                / sum(row["profile_classification_atom_checks"] for row in supported_rows)
                if sum(row["profile_classification_atom_checks"] for row in supported_rows)
                else 0.0
            ),
            "total_profile_unary_no_hit_certified_assignments": sum(
                row["profile_unary_no_hit_certified_assignments"] for row in supported_rows
            ),
            "total_profile_ambiguous_no_hit_assignments": sum(
                row["profile_ambiguous_no_hit_assignments"] for row in supported_rows
            ),
            "total_profile_unary_hit_certified_assignments": sum(
                row["profile_unary_hit_certified_assignments"] for row in supported_rows
            ),
            "total_profile_ambiguous_hit_assignments": sum(
                row["profile_ambiguous_hit_assignments"] for row in supported_rows
            ),
            "profile_unary_no_hit_coverage_ratio": (
                sum(row["profile_unary_no_hit_certified_assignments"] for row in supported_rows)
                / sum(row["profile_no_hit_assignments"] for row in supported_rows)
                if sum(row["profile_no_hit_assignments"] for row in supported_rows)
                else 0.0
            ),
            "profile_ambiguous_no_hit_ratio": (
                sum(row["profile_ambiguous_no_hit_assignments"] for row in supported_rows)
                / sum(row["profile_no_hit_assignments"] for row in supported_rows)
                if sum(row["profile_no_hit_assignments"] for row in supported_rows)
                else 0.0
            ),
            "profile_unary_hit_coverage_ratio": (
                sum(row["profile_unary_hit_certified_assignments"] for row in supported_rows)
                / sum(row["profile_hit_assignments"] for row in supported_rows)
                if sum(row["profile_hit_assignments"] for row in supported_rows)
                else 0.0
            ),
            "max_profile_group_no_hit_exhaustive_atom_checks": max(
                [row["profile_max_group_no_hit_exhaustive_atom_checks"] for row in supported_rows],
                default=0,
            ),
            "max_first_hit_position": max(
                [row["first_hit_max_position"] for row in supported_rows],
                default=0,
            ),
            "median_first_hit_average_position": _median(
                [
                    row["first_hit_average_position"]
                    for row in supported_rows
                    if row["first_hit_assignments"]
                ]
            ),
            "first_hit_no_hit_assignment_ratio": (
                sum(row["first_hit_no_hit_assignments"] for row in supported_rows)
                / sum(row["first_hit_support_assignments_seen"] for row in supported_rows)
                if sum(row["first_hit_support_assignments_seen"] for row in supported_rows)
                else 0.0
            ),
            "median_support_vs_old_scan_ratio": _median(
                [row["support_vs_old_scan_ratio"] for row in supported_rows]
            ),
            "median_grouped_vs_ungrouped_support_ratio": _median(
                [row["grouped_vs_ungrouped_support_ratio"] for row in supported_rows]
            ),
            "total_branches_pruned": sum(row["branches_pruned"] for row in supported_rows),
            "total_leaf_assignments_seen": sum(row["leaf_assignments_seen"] for row in supported_rows),
            "total_full_assignment_space": sum(row["full_assignment_space"] for row in supported_rows),
        },
        "rows": rows,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--instance-kinds", default="random,cycle,block,ultrametric,equal,non_strict")
    parser.add_argument("--pc-trees", default="balanced,mixed")
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260522)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--output", default="reports/csp_internal_benchmark_quick.json")
    args = parser.parse_args(argv)

    report = run_benchmark(
        sizes=_parse_ints(args.sizes),
        repeats=args.repeats,
        instance_kinds=_parse_strings(args.instance_kinds),
        pc_trees=_parse_strings(args.pc_trees),
        max_p_degree=args.max_p_degree,
        seed=args.seed,
        validate=not args.no_validate,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return (
        2
        if report["summary"]["mismatches"]
        or report["summary"]["support_mismatches"]
        or report["summary"]["grouped_mismatches"]
        or report["summary"]["first_hit_mismatches"]
        or report["summary"]["signature_mismatches"]
        or report["summary"]["grouped_signature_mismatches"]
        or report["summary"]["support_grouped_signature_mismatches"]
        or report["summary"]["first_hit_signature_mismatches"]
        or report["summary"]["grouped_first_hit_signature_mismatches"]
        or report["summary"]["profile_pair_side_split_mismatches"]
        or report["summary"]["quartet_scope_projection_mismatches"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
