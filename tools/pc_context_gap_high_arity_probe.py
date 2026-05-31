#!/usr/bin/env python3
"""T100 probe: compare multi-obligation gap arity at tuple sizes 3 and 4."""

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

from tools.pc_context_gap_arity_probe import (  # noqa: E402
    _json_ready,
    _parse_ints,
    _parse_strings,
)
from tools.pc_context_gap_multi_arity_probe import run_probe as run_multi_probe  # noqa: E402


def _summary_projection(summary: dict) -> dict:
    keys = (
        "rows",
        "complete_rows",
        "truncated_rows",
        "tuple_limit_rows",
        "rows_with_pnodes",
        "open_obligation_projection_count",
        "projection_tuple_count",
        "relation_case_count",
        "unary_sufficient_case_count",
        "binary_sufficient_case_count",
        "higher_order_case_count",
        "product_false_case_count",
        "pairwise_false_case_count",
        "product_false_tuple_count",
        "pairwise_false_tuple_count",
        "rows_with_higher_order_cases",
        "max_product_size",
        "max_pairwise_closure_size",
        "max_actual_relation_size",
        "max_pairwise_false_count",
    )
    return {key: summary[key] for key in keys}


def run_probe(
    *,
    tuple_sizes: list[int],
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    min_distinct_obligations: int,
    scope: str,
    max_projection_tuples: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
    reports = []
    by_tuple_size = {}
    for tuple_size in tuple_sizes:
        report = run_multi_probe(
            sizes=sizes,
            pc_trees=pc_trees,
            instance_kinds=instance_kinds,
            repeats=repeats,
            frontier_limit=frontier_limit,
            projection_tuple_size=tuple_size,
            min_distinct_obligations=min_distinct_obligations,
            scope=scope,
            max_projection_tuples=max_projection_tuples,
            max_examples=max_examples,
            seed=seed + 7919 * tuple_size,
        )
        reports.append(report)
        by_tuple_size[str(tuple_size)] = _summary_projection(report["summary"])

    summaries = [report["summary"] for report in reports]
    overall = {
        "rows": sum(summary["rows"] for summary in summaries),
        "complete_rows": sum(summary["complete_rows"] for summary in summaries),
        "tuple_limit_rows": sum(summary["tuple_limit_rows"] for summary in summaries),
        "projection_tuple_count": sum(
            summary["projection_tuple_count"] for summary in summaries
        ),
        "relation_case_count": sum(summary["relation_case_count"] for summary in summaries),
        "product_false_case_count": sum(
            summary["product_false_case_count"] for summary in summaries
        ),
        "binary_sufficient_case_count": sum(
            summary["binary_sufficient_case_count"] for summary in summaries
        ),
        "higher_order_case_count": sum(
            summary["higher_order_case_count"] for summary in summaries
        ),
        "pairwise_false_case_count": sum(
            summary["pairwise_false_case_count"] for summary in summaries
        ),
        "max_product_size": max(
            (summary["max_product_size"] for summary in summaries),
            default=0,
        ),
        "max_actual_relation_size": max(
            (summary["max_actual_relation_size"] for summary in summaries),
            default=0,
        ),
        "max_pairwise_closure_size": max(
            (summary["max_pairwise_closure_size"] for summary in summaries),
            default=0,
        ),
        "tuple_sizes_with_higher_order_cases": [
            report["projection_tuple_size"]
            for report in reports
            if report["summary"]["higher_order_case_count"]
        ],
        "tuple_sizes_with_tuple_caps": [
            report["projection_tuple_size"]
            for report in reports
            if report["summary"]["tuple_limit_rows"]
        ],
        "interpretation": (
            "T100 compares the T099 multi-obligation gap relation at larger "
            "tuple sizes. A higher-order case would refute binary "
            "reconstruction in this bounded scaffold; zero higher-order cases "
            "is not a proof, especially when tuple caps are reached."
        ),
    }
    return {
        "method": "t100_context_gap_high_arity_probe",
        "tuple_sizes": tuple_sizes,
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "min_distinct_obligations": min_distinct_obligations,
        "scope": scope,
        "max_projection_tuples": max_projection_tuples,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": overall,
        "by_tuple_size": by_tuple_size,
        "reports": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuple-sizes", default="3,4", type=_parse_ints)
    parser.add_argument("--sizes", default="5,6,7", type=_parse_ints)
    parser.add_argument("--pc-trees", default="mixed", type=_parse_strings)
    parser.add_argument(
        "--instance-kinds",
        default="cycle,paired_farthest,random,padded_five_local_non_cr",
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
    parser.add_argument("--max-projection-tuples", type=int, default=3000)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260700)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_high_arity_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        tuple_sizes=args.tuple_sizes,
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        min_distinct_obligations=args.min_distinct_obligations,
        scope=args.scope,
        max_projection_tuples=args.max_projection_tuples,
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
