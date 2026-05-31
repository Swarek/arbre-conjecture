#!/usr/bin/env python3
"""T092 probe: partial bad-side obligations around local P-node chords."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.generators import (  # noqa: E402
    even_high_cycle_plus_low_hub,
    instance_by_kind,
    odd_high_cycle_plus_low_hub,
    random_dissimilarity,
)
from pc_circular.pc_tree import balanced_pc_tree, pc_tree_from_kind, star_pc_tree  # noqa: E402
from pc_circular.solvers.partial_obligation_experiments import (  # noqa: E402
    pnode_partial_obligation_report,
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


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _stable_offset(*parts: str) -> int:
    text = "\x1f".join(parts)
    return sum((index + 1) * ord(char) for index, char in enumerate(text)) % 100000


def _merge_histogram(target: dict, source: dict) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


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
    if kind == "star":
        return star_pc_tree(n)
    if kind == "balanced_c":
        return balanced_pc_tree(n, kind="C")
    return pc_tree_from_kind(kind, n)


def _is_applicable(instance_kind: str, n: int) -> bool:
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


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    max_branch_degree: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    report = pnode_partial_obligation_report(
        D,
        T,
        frontier_limit=frontier_limit,
        max_branch_degree=max_branch_degree,
        max_examples=max_examples,
    )
    interesting_nodes = [
        node
        for node in report["nodes"]
        if node["has_partial_or_multilevel_info"]
        or node["status"] in {"global_not_contained", "local_strict_superset", "local_unsat"}
    ]
    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": not report["frontier_truncated"] and not report["obligations_truncated"],
        "frontiers_seen": report["frontiers_seen"],
        "frontier_truncated": report["frontier_truncated"],
        "accepted_frontier_count": report["accepted_frontier_count"],
        "obligation_count": report["obligation_count"],
        "pnode_count": report["pnode_count"],
        "tested_pnode_count": report["tested_pnode_count"],
        "status_histogram": report["status_histogram"],
        "partial_kind_histogram": report["partial_kind_histogram"],
        "role_pattern_histogram": report["role_pattern_histogram"],
        "fine_role_pattern_histogram": report["fine_role_pattern_histogram"],
        "nodes_with_partial_or_multilevel_info": report[
            "nodes_with_partial_or_multilevel_info"
        ],
        "nodes_with_open_obligations": report["nodes_with_open_obligations"],
        "vacuous_local_superset_count": report["vacuous_local_superset_count"],
        "vacuous_local_superset_with_partial_info_count": report[
            "vacuous_local_superset_with_partial_info_count"
        ],
        "vacuous_local_superset_without_partial_info_count": report[
            "vacuous_local_superset_without_partial_info_count"
        ],
        "constrained_local_superset_count": report["constrained_local_superset_count"],
        "constrained_local_superset_with_partial_info_count": report[
            "constrained_local_superset_with_partial_info_count"
        ],
        "constrained_local_superset_without_partial_info_count": report[
            "constrained_local_superset_without_partial_info_count"
        ],
        "global_not_contained_count": report["global_not_contained_count"],
        "max_non_chord_obligation_count": report["max_non_chord_obligation_count"],
        "max_open_obligation_count": report["max_open_obligation_count"],
        "max_multi_level_hit_count": report["max_multi_level_hit_count"],
        "max_support_boundary_obligation_count": report[
            "max_support_boundary_obligation_count"
        ],
        "max_projection_only_obligation_count": report[
            "max_projection_only_obligation_count"
        ],
        "node_summaries": [
            {
                "path": node["path"],
                "degree": node["degree"],
                "status": node["status"],
                "partial_kind": node["partial_kind"],
                "projection_hit_count": node["projection_hit_count"],
                "fully_visible_four_branch_obligation_count": node[
                    "fully_visible_four_branch_obligation_count"
                ],
                "forbidden_chord_pair_count": node["forbidden_chord_pair_count"],
                "non_chord_obligation_count": node["non_chord_obligation_count"],
                "open_obligation_count": node["open_obligation_count"],
                "multi_level_hit_count": node["multi_level_hit_count"],
                "support_boundary_obligation_count": node[
                    "support_boundary_obligation_count"
                ],
                "projection_only_obligation_count": node["projection_only_obligation_count"],
                "local_extra_order_count": node["local_extra_order_count"],
                "role_pattern_histogram": node["role_pattern_histogram"],
                "fine_role_pattern_histogram": node["fine_role_pattern_histogram"],
            }
            for node in interesting_nodes[:max_examples]
        ],
        "interpretation": "partial bad-side obligation diagnostic only; not a solver",
    }


def run_probe(
    *,
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    max_branch_degree: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
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
                            max_branch_degree=max_branch_degree,
                            max_examples=max_examples,
                        )
                    )

    role_pattern_histogram: dict = {}
    fine_role_pattern_histogram: dict = {}
    partial_kind_histogram: dict = {}
    status_histogram: dict = {}
    for row in rows:
        _merge_histogram(role_pattern_histogram, row["role_pattern_histogram"])
        _merge_histogram(fine_role_pattern_histogram, row["fine_role_pattern_histogram"])
        _merge_histogram(partial_kind_histogram, row["partial_kind_histogram"])
        _merge_histogram(status_histogram, row["status_histogram"])

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "rows_with_partial_or_multilevel_info": sum(
            1 for row in rows if row["nodes_with_partial_or_multilevel_info"]
        ),
        "rows_with_open_obligations": sum(1 for row in rows if row["nodes_with_open_obligations"]),
        "global_not_contained_rows": sum(1 for row in rows if row["global_not_contained_count"]),
        "vacuous_local_superset_nodes": sum(
            row["vacuous_local_superset_count"] for row in rows
        ),
        "vacuous_local_superset_with_partial_info_nodes": sum(
            row["vacuous_local_superset_with_partial_info_count"] for row in rows
        ),
        "vacuous_local_superset_without_partial_info_nodes": sum(
            row["vacuous_local_superset_without_partial_info_count"] for row in rows
        ),
        "constrained_local_superset_nodes": sum(
            row["constrained_local_superset_count"] for row in rows
        ),
        "constrained_local_superset_with_partial_info_nodes": sum(
            row["constrained_local_superset_with_partial_info_count"] for row in rows
        ),
        "constrained_local_superset_without_partial_info_nodes": sum(
            row["constrained_local_superset_without_partial_info_count"] for row in rows
        ),
        "max_non_chord_obligation_count": max(
            (row["max_non_chord_obligation_count"] for row in rows),
            default=0,
        ),
        "max_open_obligation_count": max(
            (row["max_open_obligation_count"] for row in rows),
            default=0,
        ),
        "max_multi_level_hit_count": max(
            (row["max_multi_level_hit_count"] for row in rows),
            default=0,
        ),
        "max_support_boundary_obligation_count": max(
            (row["max_support_boundary_obligation_count"] for row in rows),
            default=0,
        ),
        "max_projection_only_obligation_count": max(
            (row["max_projection_only_obligation_count"] for row in rows),
            default=0,
        ),
        "role_pattern_histogram": dict(sorted(role_pattern_histogram.items())),
        "fine_role_pattern_histogram": dict(sorted(fine_role_pattern_histogram.items())),
        "partial_kind_histogram": dict(sorted(partial_kind_histogram.items())),
        "status_histogram": dict(sorted(status_histogram.items())),
        "interpretation": (
            "T092 measures local bad-side information ignored by fully visible "
            "branch-chord noncrossing constraints; not a solver."
        ),
    }
    return {
        "method": "t092_partial_obligation_lab_probe",
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "max_branch_degree": max_branch_degree,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7,8", type=_parse_ints)
    parser.add_argument("--pc-trees", default=",".join(DEFAULT_PC_TREES), type=_parse_strings)
    parser.add_argument(
        "--instance-kinds",
        default=",".join(DEFAULT_INSTANCE_KINDS),
        type=_parse_strings,
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument("--max-branch-degree", type=int, default=8)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260620)
    parser.add_argument("--output", type=Path, default=Path("reports/partial_obligation_lab_probe.json"))
    args = parser.parse_args(argv)

    report = run_probe(
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        max_branch_degree=args.max_branch_degree,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n")
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
