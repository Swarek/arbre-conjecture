#!/usr/bin/env python3
"""T084 probe: empirical width-4 closure for P-node branch orders."""

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
from pc_circular.solvers.width4_experiments import (  # noqa: E402
    pnode_width4_frontier_projection_report,
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


def _stable_offset(*parts: str) -> int:
    text = "\x1f".join(parts)
    return sum((index + 1) * ord(char) for index, char in enumerate(text)) % 100000


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
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    report = pnode_width4_frontier_projection_report(
        D,
        T,
        frontier_limit=frontier_limit,
        max_branch_degree=max_branch_degree,
    )
    seconds = time.perf_counter() - start
    refuted_nodes = [node for node in report["nodes"] if node["status"] == "refuted"]
    tested_nodes = [node for node in report["nodes"] if node["status"] in {"holds", "refuted"}]
    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": seconds,
        "complete": not report["frontier_truncated"],
        "frontiers_seen": report["frontiers_seen"],
        "frontier_truncated": report["frontier_truncated"],
        "accepted_frontier_count": report["accepted_frontier_count"],
        "tested_node_count": report["tested_node_count"],
        "refuted_node_count": report["refuted_node_count"],
        "unsupported_node_count": report["unsupported_node_count"],
        "incomplete_node_count": report["incomplete_node_count"],
        "max_missing_order_count": report["max_missing_order_count"],
        "node_summaries": [
            {
                "path": node["path"],
                "degree": node["degree"],
                "status": node["status"],
                "complete_for_width4_decision": node["complete_for_width4_decision"],
                "truncation_reasons": node["truncation_reasons"],
                "frontier_child_order_count": node["frontier_child_order_count"],
                "accepted_branch_order_count": node["accepted_branch_order_count"],
                "closure": node["closure"],
            }
            for node in tested_nodes[:10]
        ],
        "refutation_examples": [
            {
                "path": node["path"],
                "degree": node["degree"],
                "closure": node["closure"],
            }
            for node in refuted_nodes[:5]
        ],
        "interpretation": "empirical width-4 diagnostic only; not a solver",
    }


def run_probe(
    *,
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    max_branch_degree: int,
    seed: int,
    include_high_girth_n9: bool,
) -> dict:
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
                        )
                    )

    if include_high_girth_n9:
        rows.append(
            _row(
                n=9,
                pc_tree_kind="star",
                instance_kind="even_high_cycle_low_hub",
                repeat=0,
                seed=seed + 909,
                frontier_limit=max(frontier_limit, 25000),
                max_branch_degree=max(max_branch_degree, 9),
            )
        )

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "truncated_rows": sum(1 for row in rows if not row["complete"]),
        "tested_node_rows": sum(1 for row in rows if row["tested_node_count"] > 0),
        "refuted_rows": sum(1 for row in rows if row["refuted_node_count"] > 0),
        "refuted_node_count": sum(row["refuted_node_count"] for row in rows),
        "unsupported_node_count": sum(row["unsupported_node_count"] for row in rows),
        "incomplete_node_count": sum(row["incomplete_node_count"] for row in rows),
        "max_missing_order_count": max(
            (row["max_missing_order_count"] for row in rows), default=0
        ),
        "max_frontiers_seen": max((row["frontiers_seen"] for row in rows), default=0),
        "interpretation": "diagnostic only; absence of refutation is not a proof",
    }
    return {
        "method": "t084_pnode_width4_probe",
        "parameters": {
            "sizes": sizes,
            "pc_trees": pc_trees,
            "instance_kinds": instance_kinds,
            "repeats": repeats,
            "frontier_limit": frontier_limit,
            "max_branch_degree": max_branch_degree,
            "seed": seed,
            "include_high_girth_n9": include_high_girth_n9,
        },
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="5,6,7,8")
    parser.add_argument("--pc-trees", default=",".join(DEFAULT_PC_TREES))
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--frontier-limit", type=int, default=10000)
    parser.add_argument("--max-branch-degree", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260670)
    parser.add_argument("--include-high-girth-n9", action="store_true")
    parser.add_argument("--output", default="reports/pnode_width4_probe.json")
    args = parser.parse_args()

    report = run_probe(
        sizes=_parse_ints(args.sizes),
        pc_trees=_parse_strings(args.pc_trees),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        max_branch_degree=args.max_branch_degree,
        seed=args.seed,
        include_high_girth_n9=args.include_high_girth_n9,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
