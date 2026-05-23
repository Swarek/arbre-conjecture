#!/usr/bin/env python3
"""Probe exact non-cR frontier obstructions through PC-tree supports."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    cycle_metric,
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    paired_farthest_matching,
    random_dissimilarity,
)
from pc_circular.pc_tree import (  # noqa: E402
    balanced_pc_tree,
    enumerate_frontiers,
    pc_tree_from_kind,
)
from pc_circular.predicates import passes_bad_side_precircular_cR  # noqa: E402
from pc_circular.solvers.dp_experiments import bad_witness_arc_order_report  # noqa: E402
from pc_circular.solvers.local_constraints import (  # noqa: E402
    classify_order_obstructions,
    measure_obstruction_support,
    project_farthest_sets_to_pc_nodes,
)
from pc_circular.solvers.sat_like_experiments import quartet_support_paths  # noqa: E402
from tools.pc_relation_catalog import _parse_ints, _parse_strings  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "paired_farthest",
    "random",
    "equal",
    "four_local_non_cr",
    "five_local_non_cr",
    "even_high_cycle_low_hub",
)
DEFAULT_PC_TREES = ("star", "balanced", "mixed")


def _histogram(values: Sequence[int | str]) -> dict[str, int]:
    counts = Counter(str(value) for value in values)
    return {key: counts[key] for key in sorted(counts, key=str)}


def _path_key(path: tuple[int, ...]) -> str:
    return "root" if not path else ".".join(str(part) for part in path)


def _instance(kind: str, n: int, *, seed: int):
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
    if kind == "even_high_cycle_low_hub":
        return even_high_cycle_plus_low_hub(n)
    raise ValueError(f"unsupported instance kind: {kind}")


def _pc_tree(kind: str, n: int):
    if kind == "balanced_c":
        return balanced_pc_tree(n, kind="C")
    return pc_tree_from_kind(kind, n)


def _repeat_count(instance_kind: str, repeats: int) -> int:
    return repeats if instance_kind in {"paired_farthest", "random"} else 1


def _is_applicable(instance_kind: str, n: int) -> bool:
    if instance_kind == "four_local_non_cr":
        return n >= 5
    if instance_kind == "five_local_non_cr":
        return n >= 6
    if instance_kind == "even_high_cycle_low_hub":
        return n >= 7 and (n - 1) % 2 == 0
    return n >= 1


def _ix_silent(D, T) -> tuple[bool, dict]:
    report = project_farthest_sets_to_pc_nodes(D, T)
    silent = all(
        node["circular_ones_compatible"] is True
        and node["proper_nontrivial_count"] == 0
        and node["laminar_violation_count"] == 0
        and node["declared_order_interval_violation_count"] == 0
        for node in report["nodes"]
    )
    return silent, report


def _profile_non_cr_order(D, T, order) -> dict:
    diagnostics = classify_order_obstructions(D, order)
    support_report = measure_obstruction_support(D, T, order)
    cr_obstruction = next(
        item for item in support_report["obstructions"] if item["type"] == "cr"
    )
    points = tuple(cr_obstruction["points"])
    support_paths = quartet_support_paths(T, points)
    full_projections = [
        projection
        for projection in cr_obstruction["node_projections"]
        if len(projection["contained_points"]) == len(points)
    ]
    root_projection = next(
        (
            projection
            for projection in cr_obstruction["node_projections"]
            if projection["path"] == ()
        ),
        None,
    )
    arc_report = bad_witness_arc_order_report(D, order)
    return {
        "order": list(order),
        "quadruple": list(points),
        "lhs_pair": list(diagnostics["cr_violation"]["lhs_pair"]),
        "support_paths": [_path_key(path) for path in support_paths],
        "support_path_count": len(support_paths),
        "requires_multi_level_correlation": len(support_paths) > 1,
        "root_support_size": root_projection["support_size"] if root_projection else None,
        "full_node_support_sizes": [
            projection["support_size"] for projection in full_projections
        ],
        "full_node_paths": [_path_key(projection["path"]) for projection in full_projections],
        "bad_witness_set_arc": arc_report["bad_witness_set_arc"],
        "bad_witness_with_endpoints_arc": arc_report[
            "bad_witness_with_endpoints_arc"
        ],
        "bad_witness_one_side": arc_report["bad_witness_one_side"],
    }


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    max_non_cr_orders: int,
) -> dict:
    start = time.perf_counter()
    T = _pc_tree(pc_tree_kind, n)
    D = _instance(instance_kind, n, seed=seed)
    ix_silent, ix_report = _ix_silent(D, T)
    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = raw_frontiers[:frontier_limit]

    cr_frontiers = 0
    non_cr_frontiers = 0
    profiled = []
    support_path_counts = []
    root_support_sizes = []
    full_node_support_sizes = []
    multi_level_count = 0
    set_arc_true_non_cr = 0
    with_endpoints_true_non_cr = 0
    one_side_true_non_cr = 0
    set_arc_mismatches = 0
    with_endpoints_mismatches = 0

    for order in frontiers:
        is_cr = passes_bad_side_precircular_cR(D, order)
        arc_report = bad_witness_arc_order_report(D, order)
        if arc_report["bad_witness_set_arc"] != is_cr:
            set_arc_mismatches += 1
        if arc_report["bad_witness_with_endpoints_arc"] != is_cr:
            with_endpoints_mismatches += 1

        if is_cr:
            cr_frontiers += 1
            continue
        non_cr_frontiers += 1
        if len(profiled) >= max_non_cr_orders:
            continue
        profile = _profile_non_cr_order(D, T, order)
        profiled.append(profile)
        support_path_counts.append(profile["support_path_count"])
        root_support_sizes.append(profile["root_support_size"])
        full_node_support_sizes.extend(profile["full_node_support_sizes"])
        if profile["requires_multi_level_correlation"]:
            multi_level_count += 1
        if profile["bad_witness_set_arc"]:
            set_arc_true_non_cr += 1
        if profile["bad_witness_with_endpoints_arc"]:
            with_endpoints_true_non_cr += 1
        if profile["bad_witness_one_side"]:
            one_side_true_non_cr += 1

    seconds = time.perf_counter() - start
    return {
        "n": n,
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "complete": not frontier_truncated,
        "frontier_truncated": frontier_truncated,
        "cr_frontiers": cr_frontiers,
        "non_cr_frontiers": non_cr_frontiers,
        "profiled_non_cr_frontiers": len(profiled),
        "ix_projection_silent": ix_silent,
        "ix_node_count": ix_report["node_count"],
        "ix_silent_but_non_cr_frontiers": non_cr_frontiers if ix_silent else 0,
        "multi_level_profiled_obstruction_count": multi_level_count,
        "single_support_profiled_obstruction_count": len(profiled) - multi_level_count,
        "support_path_count_histogram": _histogram(support_path_counts),
        "root_support_size_histogram": _histogram(
            [value for value in root_support_sizes if value is not None]
        ),
        "full_node_support_size_histogram": _histogram(full_node_support_sizes),
        "set_arc_true_non_cr_profiled": set_arc_true_non_cr,
        "with_endpoints_true_non_cr_profiled": with_endpoints_true_non_cr,
        "one_side_true_non_cr_profiled": one_side_true_non_cr,
        "set_arc_precircular_mismatches": set_arc_mismatches,
        "with_endpoints_precircular_mismatches": with_endpoints_mismatches,
        "examples": profiled[:5],
        "interpretation": (
            "Exact frontier obstruction support diagnostic. Truncated rows are "
            "not complete evidence; first-obstruction supports are local "
            "signals, not a solver."
        ),
    }


def run_frontier_obstruction_support_probe(
    *,
    sizes: Sequence[int],
    pc_trees: Sequence[str] = DEFAULT_PC_TREES,
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 2,
    seed: int = 20260590,
    frontier_limit: int = 5000,
    max_non_cr_orders: int = 200,
) -> dict:
    rows = []
    skipped = []
    for n in sizes:
        if n <= 0:
            raise ValueError("sizes must be positive")
        for pc_tree_kind in pc_trees:
            for kind_index, instance_kind in enumerate(instance_kinds):
                if not _is_applicable(instance_kind, n):
                    skipped.append(
                        {
                            "n": n,
                            "pc_tree_kind": pc_tree_kind,
                            "instance_kind": instance_kind,
                            "reason": "instance_not_defined_for_size",
                        }
                    )
                    continue
                for repeat in range(_repeat_count(instance_kind, repeats)):
                    row_seed = seed + 1009 * n + 9176 * kind_index + repeat
                    rows.append(
                        _row(
                            n=n,
                            pc_tree_kind=pc_tree_kind,
                            instance_kind=instance_kind,
                            repeat=repeat,
                            seed=row_seed,
                            frontier_limit=frontier_limit,
                            max_non_cr_orders=max_non_cr_orders,
                        )
                    )

    summary = {
        "rows": len(rows),
        "sizes": list(sizes),
        "pc_trees": list(pc_trees),
        "instance_kinds": list(instance_kinds),
        "repeats_for_random_and_paired_farthest": repeats,
        "skipped_rows": len(skipped),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "truncated_rows": sum(1 for row in rows if row["frontier_truncated"]),
        "frontiers_seen": sum(row["frontiers_seen"] for row in rows),
        "cr_frontiers": sum(row["cr_frontiers"] for row in rows),
        "non_cr_frontiers": sum(row["non_cr_frontiers"] for row in rows),
        "profiled_non_cr_frontiers": sum(
            row["profiled_non_cr_frontiers"] for row in rows
        ),
        "ix_silent_rows": sum(1 for row in rows if row["ix_projection_silent"]),
        "ix_silent_but_non_cr_frontiers": sum(
            row["ix_silent_but_non_cr_frontiers"] for row in rows
        ),
        "multi_level_profiled_obstruction_count": sum(
            row["multi_level_profiled_obstruction_count"] for row in rows
        ),
        "single_support_profiled_obstruction_count": sum(
            row["single_support_profiled_obstruction_count"] for row in rows
        ),
        "set_arc_true_non_cr_profiled": sum(
            row["set_arc_true_non_cr_profiled"] for row in rows
        ),
        "with_endpoints_true_non_cr_profiled": sum(
            row["with_endpoints_true_non_cr_profiled"] for row in rows
        ),
        "one_side_true_non_cr_profiled": sum(
            row["one_side_true_non_cr_profiled"] for row in rows
        ),
        "set_arc_precircular_mismatches": sum(
            row["set_arc_precircular_mismatches"] for row in rows
        ),
        "with_endpoints_precircular_mismatches": sum(
            row["with_endpoints_precircular_mismatches"] for row in rows
        ),
        "support_path_count_histogram": _histogram(
            key
            for row in rows
            for key, count in row["support_path_count_histogram"].items()
            for _ in range(count)
        ),
        "root_support_size_histogram": _histogram(
            key
            for row in rows
            for key, count in row["root_support_size_histogram"].items()
            for _ in range(count)
        ),
        "max_seconds": max((row["seconds"] for row in rows), default=0.0),
        "interpretation": (
            "Counts exact represented frontiers under a limit and profiles first "
            "cR obstructions. It is a local-structure diagnostic, not a proof "
            "or candidate solver."
        ),
    }
    return {
        "method": "frontier_obstruction_support_probe",
        "rows": rows,
        "skipped": skipped,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7,8")
    parser.add_argument("--pc-trees", default=",".join(DEFAULT_PC_TREES))
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260590)
    parser.add_argument("--frontier-limit", type=int, default=5000)
    parser.add_argument("--max-non-cr-orders", type=int, default=200)
    parser.add_argument("--output", default="reports/frontier_obstruction_support_probe.json")
    args = parser.parse_args(argv)

    report = run_frontier_obstruction_support_probe(
        sizes=_parse_ints(args.sizes),
        pc_trees=_parse_strings(args.pc_trees),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        frontier_limit=args.frontier_limit,
        max_non_cr_orders=args.max_non_cr_orders,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output.resolve()), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
