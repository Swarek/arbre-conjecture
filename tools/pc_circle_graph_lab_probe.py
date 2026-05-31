#!/usr/bin/env python3
"""T091 probe: local circle/interlacement lab for same-side constraints."""

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
from pc_circular.solvers.circle_graph_experiments import (  # noqa: E402
    pnode_circle_graph_local_report,
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
    report = pnode_circle_graph_local_report(
        D,
        T,
        frontier_limit=frontier_limit,
        max_branch_degree=max_branch_degree,
        max_examples=max_examples,
    )
    interesting_nodes = [
        node
        for node in report["nodes"]
        if node["forbidden_chord_pair_count"]
        or node["global_cr_branch_order_count"]
        or node["status"] in {"global_not_contained", "local_unsat", "local_strict_superset"}
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
        "global_not_contained_count": report["global_not_contained_count"],
        "local_unsat_count": report["local_unsat_count"],
        "local_strict_superset_count": report["local_strict_superset_count"],
        "constrained_local_strict_superset_count": report[
            "constrained_local_strict_superset_count"
        ],
        "vacuous_local_strict_superset_count": report[
            "vacuous_local_strict_superset_count"
        ],
        "local_matches_global_seen_count": report["local_matches_global_seen_count"],
        "max_local_extra_order_count": report["max_local_extra_order_count"],
        "max_forbidden_chord_pair_count": report["max_forbidden_chord_pair_count"],
        "node_summaries": [
            {
                "path": node["path"],
                "degree": node["degree"],
                "status": node["status"],
                "forbidden_chord_pair_count": node["forbidden_chord_pair_count"],
                "active_chord_count": node["active_chord_count"],
                "forced_noncross_chord_component_sizes": node[
                    "forced_noncross_chord_component_sizes"
                ],
                "branch_interaction_component_sizes": node[
                    "branch_interaction_component_sizes"
                ],
                "declared_order_crossing_violation_count": node[
                    "declared_order_crossing_violation_count"
                ],
                "frontier_child_order_count": node["frontier_child_order_count"],
                "global_cr_branch_order_count": node["global_cr_branch_order_count"],
                "local_order_count": node["local_order_count"],
                "local_extra_order_count": node["local_extra_order_count"],
                "local_missing_global_order_count": node["local_missing_global_order_count"],
            }
            for node in interesting_nodes[:max_examples]
        ],
        "interpretation": "local circle/interlacement diagnostic only; not a solver",
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

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "truncated_rows": sum(1 for row in rows if not row["complete"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "rows_with_local_constraints": sum(
            1 for row in rows if row["max_forbidden_chord_pair_count"] > 0
        ),
        "global_not_contained_rows": sum(
            1 for row in rows if row["global_not_contained_count"] > 0
        ),
        "local_unsat_rows": sum(1 for row in rows if row["local_unsat_count"] > 0),
        "local_strict_superset_rows": sum(
            1 for row in rows if row["local_strict_superset_count"] > 0
        ),
        "constrained_local_strict_superset_rows": sum(
            1 for row in rows if row["constrained_local_strict_superset_count"] > 0
        ),
        "vacuous_local_strict_superset_rows": sum(
            1 for row in rows if row["vacuous_local_strict_superset_count"] > 0
        ),
        "max_local_extra_order_count": max(
            (row["max_local_extra_order_count"] for row in rows),
            default=0,
        ),
        "max_forbidden_chord_pair_count": max(
            (row["max_forbidden_chord_pair_count"] for row in rows),
            default=0,
        ),
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "bounded circle/interlacement lab; local constraints are necessary "
            "only and not a decision procedure"
        ),
    }
    return {
        "method": "t091_circle_graph_lab_probe",
        "parameters": {
            "sizes": sizes,
            "pc_trees": pc_trees,
            "instance_kinds": instance_kinds,
            "repeats": repeats,
            "frontier_limit": frontier_limit,
            "max_branch_degree": max_branch_degree,
            "max_examples": max_examples,
            "seed": seed,
        },
        "summary": summary,
        "rows": rows,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="4,5,6,7,8")
    parser.add_argument("--pc-trees", default=",".join(DEFAULT_PC_TREES))
    parser.add_argument("--instance-kinds", default=",".join(DEFAULT_INSTANCE_KINDS))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument("--max-branch-degree", type=int, default=8)
    parser.add_argument("--max-examples", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_probe(
        sizes=_parse_ints(args.sizes),
        pc_trees=_parse_strings(args.pc_trees),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        max_branch_degree=args.max_branch_degree,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "method": report["method"],
                "output": str(output),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
