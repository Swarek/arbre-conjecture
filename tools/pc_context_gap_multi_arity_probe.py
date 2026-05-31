#!/usr/bin/env python3
"""T099 probe: arity of gap relations across multiple obligations."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.solvers.partial_obligation_experiments import (  # noqa: E402
    pnode_context_gap_multi_obligation_arity_report,
)
from tools.pc_context_gap_arity_probe import (  # noqa: E402
    DEFAULT_INSTANCE_KINDS,
    DEFAULT_PC_TREES,
    _instance,
    _is_applicable,
    _json_ready,
    _merge_histogram,
    _parse_ints,
    _parse_strings,
    _pc_tree,
    _repeat_count,
    _stable_offset,
)


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    projection_tuple_size: int,
    min_distinct_obligations: int,
    scope: str,
    max_projection_tuples: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    report = pnode_context_gap_multi_obligation_arity_report(
        D,
        T,
        frontier_limit=frontier_limit,
        projection_tuple_size=projection_tuple_size,
        min_distinct_obligations=min_distinct_obligations,
        scope=scope,
        max_projection_tuples=max_projection_tuples,
        max_examples=max_examples,
    )
    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": (
            not report["frontier_truncated"]
            and not report["projection_tuple_limit_reached"]
        ),
        "frontiers_seen": report["frontiers_seen"],
        "frontier_truncated": report["frontier_truncated"],
        "projection_tuple_limit_reached": report["projection_tuple_limit_reached"],
        "pnode_count": report["pnode_count"],
        "open_obligation_projection_count": report[
            "open_obligation_projection_count"
        ],
        "skipped_same_obligation_tuple_count": report[
            "skipped_same_obligation_tuple_count"
        ],
        "projection_tuple_count": report["projection_tuple_count"],
        "relation_case_count": report["relation_case_count"],
        "unary_sufficient_case_count": report["unary_sufficient_case_count"],
        "binary_sufficient_case_count": report["binary_sufficient_case_count"],
        "higher_order_case_count": report["higher_order_case_count"],
        "product_false_case_count": report["product_false_case_count"],
        "pairwise_false_case_count": report["pairwise_false_case_count"],
        "product_false_tuple_count": report["product_false_tuple_count"],
        "pairwise_false_tuple_count": report["pairwise_false_tuple_count"],
        "max_product_size": report["max_product_size"],
        "max_pairwise_closure_size": report["max_pairwise_closure_size"],
        "max_actual_relation_size": report["max_actual_relation_size"],
        "max_pairwise_false_count": report["max_pairwise_false_count"],
        "min_required_arity_histogram": report["min_required_arity_histogram"],
        "actual_relation_size_histogram": report["actual_relation_size_histogram"],
        "product_size_histogram": report["product_size_histogram"],
        "pairwise_closure_size_histogram": report[
            "pairwise_closure_size_histogram"
        ],
        "pairwise_false_size_histogram": report["pairwise_false_size_histogram"],
        "tuple_pattern_histogram": report["tuple_pattern_histogram"],
        "distinct_obligation_count_histogram": report[
            "distinct_obligation_count_histogram"
        ],
        "binary_sufficient_examples": report["binary_sufficient_examples"],
        "higher_order_examples": report["higher_order_examples"],
        "interpretation": "multi-obligation gap-arity diagnostic only; not a solver",
    }


def run_probe(
    *,
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    projection_tuple_size: int,
    min_distinct_obligations: int,
    scope: str,
    max_projection_tuples: int,
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
                            projection_tuple_size=projection_tuple_size,
                            min_distinct_obligations=min_distinct_obligations,
                            scope=scope,
                            max_projection_tuples=max_projection_tuples,
                            max_examples=max_examples,
                        )
                    )

    min_required_arity_histogram = {}
    actual_relation_size_histogram = {}
    product_size_histogram = {}
    pairwise_closure_size_histogram = {}
    pairwise_false_size_histogram = {}
    tuple_pattern_histogram = {}
    distinct_obligation_count_histogram = {}
    for row in rows:
        _merge_histogram(
            min_required_arity_histogram,
            row["min_required_arity_histogram"],
        )
        _merge_histogram(
            actual_relation_size_histogram,
            row["actual_relation_size_histogram"],
        )
        _merge_histogram(product_size_histogram, row["product_size_histogram"])
        _merge_histogram(
            pairwise_closure_size_histogram,
            row["pairwise_closure_size_histogram"],
        )
        _merge_histogram(
            pairwise_false_size_histogram,
            row["pairwise_false_size_histogram"],
        )
        _merge_histogram(tuple_pattern_histogram, row["tuple_pattern_histogram"])
        _merge_histogram(
            distinct_obligation_count_histogram,
            row["distinct_obligation_count_histogram"],
        )

    summary = {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "truncated_rows": sum(1 for row in rows if row["frontier_truncated"]),
        "tuple_limit_rows": sum(
            1 for row in rows if row["projection_tuple_limit_reached"]
        ),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "open_obligation_projection_count": sum(
            row["open_obligation_projection_count"] for row in rows
        ),
        "projection_tuple_count": sum(row["projection_tuple_count"] for row in rows),
        "relation_case_count": sum(row["relation_case_count"] for row in rows),
        "unary_sufficient_case_count": sum(
            row["unary_sufficient_case_count"] for row in rows
        ),
        "binary_sufficient_case_count": sum(
            row["binary_sufficient_case_count"] for row in rows
        ),
        "higher_order_case_count": sum(
            row["higher_order_case_count"] for row in rows
        ),
        "product_false_case_count": sum(
            row["product_false_case_count"] for row in rows
        ),
        "pairwise_false_case_count": sum(
            row["pairwise_false_case_count"] for row in rows
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
        "max_product_size": max((row["max_product_size"] for row in rows), default=0),
        "max_pairwise_closure_size": max(
            (row["max_pairwise_closure_size"] for row in rows),
            default=0,
        ),
        "max_actual_relation_size": max(
            (row["max_actual_relation_size"] for row in rows),
            default=0,
        ),
        "max_pairwise_false_count": max(
            (row["max_pairwise_false_count"] for row in rows),
            default=0,
        ),
        "min_required_arity_histogram": dict(
            sorted(min_required_arity_histogram.items())
        ),
        "actual_relation_size_histogram": dict(
            sorted(actual_relation_size_histogram.items())
        ),
        "product_size_histogram": dict(sorted(product_size_histogram.items())),
        "pairwise_closure_size_histogram": dict(
            sorted(pairwise_closure_size_histogram.items())
        ),
        "pairwise_false_size_histogram": dict(
            sorted(pairwise_false_size_histogram.items())
        ),
        "distinct_obligation_count_histogram": dict(
            sorted(distinct_obligation_count_histogram.items())
        ),
        "tuple_pattern_histogram": dict(sorted(tuple_pattern_histogram.items())),
        "interpretation": (
            "T099 mixes open projections from several same-side obligations. "
            "Higher-order cases would refute binary reconstruction for this "
            "bounded relation; zero higher-order cases is not a proof."
        ),
    }
    return {
        "method": "t099_context_gap_multi_obligation_arity_probe",
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "projection_tuple_size": projection_tuple_size,
        "min_distinct_obligations": min_distinct_obligations,
        "scope": scope,
        "max_projection_tuples": max_projection_tuples,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="5,6,7,8", type=_parse_ints)
    parser.add_argument("--pc-trees", default="mixed", type=_parse_strings)
    parser.add_argument(
        "--instance-kinds",
        default="cycle,paired_farthest,random,padded_five_local_non_cr",
        type=_parse_strings,
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument("--projection-tuple-size", type=int, default=3)
    parser.add_argument("--min-distinct-obligations", type=int, default=2)
    parser.add_argument(
        "--scope",
        choices=("all_open", "support_open", "projection_only_open"),
        default="all_open",
    )
    parser.add_argument("--max-projection-tuples", type=int, default=10000)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260690)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_multi_arity_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        projection_tuple_size=args.projection_tuple_size,
        min_distinct_obligations=args.min_distinct_obligations,
        scope=args.scope,
        max_projection_tuples=args.max_projection_tuples,
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
