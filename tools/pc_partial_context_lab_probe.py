#!/usr/bin/env python3
"""T093 probe: context dependence of partial P-node obligations."""

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
    pnode_partial_context_dependency_report,
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
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    report = pnode_partial_context_dependency_report(
        D,
        T,
        frontier_limit=frontier_limit,
        max_examples=max_examples,
    )
    interesting_nodes = [
        node
        for node in report["nodes"]
        if node["mixed_group_count"]
        or node["support_boundary_obligation_count"]
        or node["fully_visible_mixed_group_count"]
    ]
    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": not report["frontier_truncated"],
        "frontiers_seen": report["frontiers_seen"],
        "frontier_truncated": report["frontier_truncated"],
        "pnode_count": report["pnode_count"],
        "obligation_projection_count": report["obligation_projection_count"],
        "support_obligation_count": report["support_obligation_count"],
        "support_boundary_obligation_count": report["support_boundary_obligation_count"],
        "fully_visible_obligation_count": report["fully_visible_obligation_count"],
        "projection_only_obligation_count": report["projection_only_obligation_count"],
        "context_group_count": report["context_group_count"],
        "mixed_group_count": report["mixed_group_count"],
        "support_boundary_mixed_group_count": report["support_boundary_mixed_group_count"],
        "fully_visible_mixed_group_count": report["fully_visible_mixed_group_count"],
        "nodes_with_mixed_groups": report["nodes_with_mixed_groups"],
        "nodes_with_support_boundary_mixed_groups": report[
            "nodes_with_support_boundary_mixed_groups"
        ],
        "fine_role_pattern_histogram": report["fine_role_pattern_histogram"],
        "mixed_fine_role_pattern_histogram": report["mixed_fine_role_pattern_histogram"],
        "max_mixed_group_count": report["max_mixed_group_count"],
        "max_support_boundary_mixed_group_count": report[
            "max_support_boundary_mixed_group_count"
        ],
        "node_summaries": [
            {
                "path": node["path"],
                "degree": node["degree"],
                "support_boundary_obligation_count": node[
                    "support_boundary_obligation_count"
                ],
                "fully_visible_obligation_count": node["fully_visible_obligation_count"],
                "context_group_count": node["context_group_count"],
                "mixed_group_count": node["mixed_group_count"],
                "support_boundary_mixed_group_count": node[
                    "support_boundary_mixed_group_count"
                ],
                "fully_visible_mixed_group_count": node["fully_visible_mixed_group_count"],
                "mixed_fine_role_pattern_histogram": node[
                    "mixed_fine_role_pattern_histogram"
                ],
                "mixed_examples": node["mixed_examples"],
            }
            for node in interesting_nodes[:max_examples]
        ],
        "interpretation": "partial context-dependency diagnostic only; not a solver",
    }


def run_probe(
    *,
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
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
                            max_examples=max_examples,
                        )
                    )

    fine_role_pattern_histogram: dict = {}
    mixed_fine_role_pattern_histogram: dict = {}
    for row in rows:
        _merge_histogram(fine_role_pattern_histogram, row["fine_role_pattern_histogram"])
        _merge_histogram(
            mixed_fine_role_pattern_histogram,
            row["mixed_fine_role_pattern_histogram"],
        )

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "rows_with_support_boundary_obligations": sum(
            1 for row in rows if row["support_boundary_obligation_count"]
        ),
        "rows_with_mixed_groups": sum(1 for row in rows if row["mixed_group_count"]),
        "rows_with_support_boundary_mixed_groups": sum(
            1 for row in rows if row["support_boundary_mixed_group_count"]
        ),
        "rows_with_fully_visible_mixed_groups": sum(
            1 for row in rows if row["fully_visible_mixed_group_count"]
        ),
        "support_boundary_obligation_count": sum(
            row["support_boundary_obligation_count"] for row in rows
        ),
        "fully_visible_obligation_count": sum(row["fully_visible_obligation_count"] for row in rows),
        "context_group_count": sum(row["context_group_count"] for row in rows),
        "mixed_group_count": sum(row["mixed_group_count"] for row in rows),
        "support_boundary_mixed_group_count": sum(
            row["support_boundary_mixed_group_count"] for row in rows
        ),
        "fully_visible_mixed_group_count": sum(
            row["fully_visible_mixed_group_count"] for row in rows
        ),
        "max_mixed_group_count": max((row["max_mixed_group_count"] for row in rows), default=0),
        "max_support_boundary_mixed_group_count": max(
            (row["max_support_boundary_mixed_group_count"] for row in rows),
            default=0,
        ),
        "fine_role_pattern_histogram": dict(sorted(fine_role_pattern_histogram.items())),
        "mixed_fine_role_pattern_histogram": dict(
            sorted(mixed_fine_role_pattern_histogram.items())
        ),
        "interpretation": (
            "T093 tests whether local P-node branch order decides projected "
            "same-side obligations. Mixed groups are context-dependency "
            "witnesses, not solver decisions."
        ),
    }
    return {
        "method": "t093_partial_context_lab_probe",
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
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
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--output", type=Path, default=Path("reports/partial_context_lab_probe.json"))
    args = parser.parse_args(argv)

    report = run_probe(
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
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
