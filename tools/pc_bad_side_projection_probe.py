#!/usr/bin/env python3
"""R004 probe: project exact bad-side obligations onto PC-tree nodes."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    instance_by_kind,
    matching_high_graph_plus_low_hub,
    odd_high_cycle_plus_low_hub,
    random_dissimilarity,
)
from pc_circular.pc_tree import (  # noqa: E402
    balanced_pc_tree,
    enumerate_frontiers,
    leaf,
    p_node,
    pc_tree_from_kind,
)
from pc_circular.predicates import passes_bad_side_precircular_cR  # noqa: E402
from pc_circular.solvers.local_constraints import (  # noqa: E402
    project_bad_side_obligations_to_pc_nodes,
    project_farthest_sets_to_pc_nodes,
)


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "equal",
    "paired_farthest",
    "random",
    "padded_four_local_non_cr",
    "padded_five_local_non_cr",
    "even_high_cycle_low_hub",
    "odd_high_cycle_low_hub",
)
DEFAULT_PC_TREES = ("star", "balanced", "mixed")


def _parse_ints(value: str) -> list[int]:
    return [int(part) for part in value.split(",") if part]


def _parse_strings(value: str) -> list[str]:
    return [part for part in value.split(",") if part]


def _histogram(values) -> dict[str, int]:
    counts = Counter(str(value) for value in values)
    return {key: counts[key] for key in sorted(counts, key=str)}


def _stable_offset(*parts: str) -> int:
    text = "\x1f".join(parts)
    return sum((index + 1) * ord(char) for index, char in enumerate(text)) % 100000


def _path_key(path: tuple[int, ...]) -> str:
    return "root" if not path else ".".join(str(part) for part in path)


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _instance(kind: str, n: int, *, seed: int):
    rng = random.Random(seed)
    if kind == "random4":
        return random_dissimilarity(n, values=(1, 2, 3, 4), rng=rng)
    if kind == "even_high_cycle_low_hub":
        return even_high_cycle_plus_low_hub(n)
    if kind == "odd_high_cycle_low_hub":
        return odd_high_cycle_plus_low_hub(n)
    return instance_by_kind(n, kind=kind, rng=rng)


def _pc_tree(kind: str, n: int):
    if kind == "balanced_c":
        return balanced_pc_tree(n, kind="C")
    if kind == "t046_nested_matching":
        if n != 5:
            raise ValueError("t046_nested_matching is defined only for n=5")
        return p_node([p_node([leaf(1), leaf(3)]), p_node([leaf(2), leaf(4)]), leaf(0)])
    return pc_tree_from_kind(kind, n)


def _is_applicable(instance_kind: str, pc_tree_kind: str, n: int) -> bool:
    if pc_tree_kind == "t046_nested_matching":
        return n == 5 and instance_kind == "t046_matching_low_hub"
    if instance_kind == "t046_matching_low_hub":
        return pc_tree_kind == "t046_nested_matching" and n == 5
    if instance_kind in {"padded_four_local_non_cr", "four_local_non_cr"}:
        return n >= 5
    if instance_kind in {"padded_five_local_non_cr", "five_local_non_cr"}:
        return n >= 6
    if instance_kind == "even_high_cycle_low_hub":
        return n >= 7 and (n - 1) % 2 == 0
    if instance_kind == "odd_high_cycle_low_hub":
        return n >= 6 and (n - 1) % 2 == 1
    return n >= 1


def _repeat_count(instance_kind: str, repeats: int) -> int:
    return repeats if instance_kind in {"random", "random4", "paired_farthest"} else 1


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


def _frontier_stats(D, T, *, frontier_limit: int) -> dict:
    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = raw_frontiers[:frontier_limit]
    cr_count = sum(1 for order in frontiers if passes_bad_side_precircular_cR(D, order))
    return {
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "cr_frontiers_seen": cr_count,
        "non_cr_frontiers_seen": len(frontiers) - cr_count,
    }


def _projection_summary(report: dict) -> dict:
    nodes = report["nodes"]
    active_nodes = [node for node in nodes if node["projection_hit_count"]]
    support_nodes = [node for node in nodes if node["support_node_hit_count"]]
    full_nodes = [node for node in nodes if node["full_projection_count"]]
    four_branch_nodes = [node for node in nodes if node["full_distinct_four_branch_count"]]
    return {
        "obligation_count": report["obligation_count"],
        "atom_count": report["atom_count"],
        "obligations_truncated": report["obligations_truncated"],
        "multi_level_obligation_count": report["multi_level_obligation_count"],
        "support_path_count_histogram": report["support_path_count_histogram"],
        "node_count": report["node_count"],
        "active_node_count": len(active_nodes),
        "support_node_count": len(support_nodes),
        "full_projection_node_count": len(full_nodes),
        "four_branch_node_count": len(four_branch_nodes),
        "declared_order_violation_count": sum(
            node["declared_order_violation_count"] for node in nodes
        ),
        "max_projection_hit_count": max((node["projection_hit_count"] for node in nodes), default=0),
        "max_support_node_hit_count": max(
            (node["support_node_hit_count"] for node in nodes), default=0
        ),
        "max_full_distinct_four_branch_count": max(
            (node["full_distinct_four_branch_count"] for node in nodes), default=0
        ),
        "max_forbidden_chord_pair_count": max(
            (node["forbidden_chord_pair_count"] for node in nodes), default=0
        ),
        "max_branch_interface_load": max(
            (node["max_branch_interface_load"] for node in nodes), default=0
        ),
        "node_kind_histogram": _histogram(node["kind"] for node in nodes),
        "active_node_paths": [_path_key(node["path"]) for node in active_nodes[:20]],
        "support_node_paths": [_path_key(node["path"]) for node in support_nodes[:20]],
        "examples": [
            {
                "path": _path_key(node["path"]),
                "kind": node["kind"],
                "degree": node["degree"],
                "projection_hit_count": node["projection_hit_count"],
                "support_node_hit_count": node["support_node_hit_count"],
                "support_size_histogram": node["support_size_histogram"],
                "role_pattern_histogram": node["role_pattern_histogram"],
                "examples": node["examples"][:3],
            }
            for node in active_nodes[:5]
        ],
    }


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    max_obligations: int | None,
) -> dict:
    start = time.perf_counter()
    if instance_kind == "t046_matching_low_hub":
        D = matching_high_graph_plus_low_hub(5)
    else:
        D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    ix_silent, ix_report = _ix_silent(D, T)
    projection = project_bad_side_obligations_to_pc_nodes(
        D,
        T,
        max_obligations=max_obligations,
    )
    frontier = _frontier_stats(D, T, frontier_limit=frontier_limit)
    seconds = time.perf_counter() - start
    projection_summary = _projection_summary(projection)
    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": not frontier["frontier_truncated"] and not projection["obligations_truncated"],
        "frontier": frontier,
        "farthest_projection": {
            "ix_projection_silent": ix_silent,
            "node_count": ix_report["node_count"],
        },
        "bad_side_projection": projection_summary,
        "ix_silent_bad_side_active": ix_silent and projection["obligation_count"] > 0,
        "interpretation": (
            "R004 diagnostic only: obligations projected to PC-tree nodes do "
            "not decide existence."
        ),
    }


def run_probe(
    *,
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    max_obligations: int | None,
    seed: int,
) -> dict:
    rows = []
    skipped = []

    for n in sizes:
        for pc_tree_kind in pc_trees:
            for instance_kind in instance_kinds:
                if not _is_applicable(instance_kind, pc_tree_kind, n):
                    skipped.append(
                        {
                            "n": n,
                            "pc_tree_kind": pc_tree_kind,
                            "instance_kind": instance_kind,
                            "reason": "not_applicable",
                        }
                    )
                    continue
                for repeat in range(_repeat_count(instance_kind, repeats)):
                    row_seed = (
                        seed
                        + 1009 * n
                        + 101 * repeat
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
                            max_obligations=max_obligations,
                        )
                    )

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "truncated_rows": sum(1 for row in rows if not row["complete"]),
        "ix_silent_bad_side_active_rows": sum(
            1 for row in rows if row["ix_silent_bad_side_active"]
        ),
        "multi_level_obligation_rows": sum(
            1
            for row in rows
            if row["bad_side_projection"]["multi_level_obligation_count"] > 0
        ),
        "four_branch_node_rows": sum(
            1 for row in rows if row["bad_side_projection"]["four_branch_node_count"] > 0
        ),
        "declared_order_violation_rows": sum(
            1
            for row in rows
            if row["bad_side_projection"]["declared_order_violation_count"] > 0
        ),
        "max_obligation_count": max(
            (row["bad_side_projection"]["obligation_count"] for row in rows), default=0
        ),
        "max_multi_level_obligation_count": max(
            (
                row["bad_side_projection"]["multi_level_obligation_count"]
                for row in rows
            ),
            default=0,
        ),
        "max_branch_interface_load": max(
            (row["bad_side_projection"]["max_branch_interface_load"] for row in rows),
            default=0,
        ),
        "frontier_truncated_rows": sum(
            1 for row in rows if row["frontier"]["frontier_truncated"]
        ),
        "obligations_truncated_rows": sum(
            1
            for row in rows
            if row["bad_side_projection"]["obligations_truncated"]
        ),
        "interpretation": "diagnostic only; not a candidate.py rule",
    }
    return {
        "method": "r004_bad_side_pc_node_projection_probe",
        "parameters": {
            "sizes": sizes,
            "pc_trees": pc_trees,
            "instance_kinds": instance_kinds,
            "repeats": repeats,
            "frontier_limit": frontier_limit,
            "max_obligations": max_obligations,
            "seed": seed,
        },
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="5,6,7,8,9")
    parser.add_argument("--pc-trees", default="star,balanced,mixed,t046_nested_matching")
    parser.add_argument(
        "--instance-kinds",
        default=",".join(("t046_matching_low_hub", *DEFAULT_INSTANCE_KINDS)),
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--frontier-limit", type=int, default=512)
    parser.add_argument("--max-obligations", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260660)
    parser.add_argument("--output", default="reports/r004_bad_side_pc_node_projection_probe.json")
    args = parser.parse_args()

    report = run_probe(
        sizes=_parse_ints(args.sizes),
        pc_trees=_parse_strings(args.pc_trees),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        max_obligations=args.max_obligations,
        seed=args.seed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
