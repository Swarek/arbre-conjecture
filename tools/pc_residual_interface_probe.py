#!/usr/bin/env python3
"""T088 probe: exact residual interface relation arity diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import leaf, p_node  # noqa: E402
from pc_circular.solvers.interface_experiments import (  # noqa: E402
    fixed_context_interface_product_report,
)
from tools.pc_pnode_context_interface_probe import (  # noqa: E402
    context_coupling_seed_matrix,
)


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def p2_focus(branch_count: int):
    if branch_count <= 0:
        raise ValueError("branch_count must be positive")
    return p_node(
        [
            p_node([leaf(2 * branch), leaf(2 * branch + 1)])
            for branch in range(branch_count)
        ]
    )


def two_level_high_pair_matrix(
    n: int,
    high_pairs=(),
    *,
    base_value: int = 2,
    high_value: int = 3,
) -> list[list[int]]:
    if n <= 1:
        raise ValueError("n must be at least 2")
    if base_value >= high_value:
        raise ValueError("base_value must be below high_value")

    high_pair_set = {
        tuple(sorted((int(left), int(right))))
        for left, right in high_pairs
    }
    D = [[0 for _ in range(n)] for _ in range(n)]
    for left in range(n):
        for right in range(left + 1, n):
            value = high_value if (left, right) in high_pair_set else base_value
            D[left][right] = D[right][left] = value
    return D


def residual_row(
    *,
    case: str,
    D,
    focus,
    branch_order: tuple[int, ...],
    context_before=(),
    context_after=(),
    high_pairs=(),
    max_examples: int = 4,
) -> dict:
    report = fixed_context_interface_product_report(
        D,
        focus,
        branch_order=branch_order,
        context_before=context_before,
        context_after=context_after,
        max_examples=max_examples,
    )
    product_tuple_count = report["product_tuple_count"]
    accepted_tuple_count = report["accepted_tuple_count"]
    return {
        "case": case,
        "complete": report["complete"],
        "branch_order": report["branch_order"],
        "context_before": report["context_before"],
        "context_after": report["context_after"],
        "degree": report["degree"],
        "branch_option_counts": report["branch_option_counts"],
        "product_tuple_count": product_tuple_count,
        "accepted_tuple_count": accepted_tuple_count,
        "accepted_density": (
            None if product_tuple_count == 0 else accepted_tuple_count / product_tuple_count
        ),
        "accepted_tuples": report["accepted_tuples"],
        "minimal_coupling_support_size": report["minimal_coupling_support_size"],
        "closure_by_arity": report["closure_by_arity"],
        "false_product_count": report["false_product_count"],
        "false_product_examples": report["false_product_examples"],
        "high_pairs": tuple(tuple(pair) for pair in high_pairs),
        "interpretation": (
            "exact residual relation for this fixed focus/order/context; "
            "diagnostic only, not a PC-tree decision procedure"
        ),
    }


def run_residual_interface_probe(
    *,
    max_high_pairs: int = 4,
    max_search_cases: int = 25000,
    max_examples: int = 4,
) -> dict:
    if max_high_pairs < 0:
        raise ValueError("max_high_pairs must be non-negative")
    if max_search_cases <= 0:
        raise ValueError("max_search_cases must be positive")

    start = time.perf_counter()
    rows = []
    rows.append(
        residual_row(
            case="t087_context_coupling_seed",
            D=context_coupling_seed_matrix(),
            focus=p2_focus(2),
            branch_order=(0, 1),
            context_before=(4,),
            context_after=(5,),
            max_examples=max_examples,
        )
    )

    focus = p2_focus(3)
    n = 8
    all_pairs = tuple((left, right) for left in range(n) for right in range(left + 1, n))
    searched = 0
    complete = True
    relation_kind_counts = {
        "empty": 0,
        "full": 0,
        "nontrivial": 0,
    }
    minimal_arity_histogram: dict[int, int] = {}
    best_non_unary = None
    first_beyond_binary = None

    for high_pair_count in range(1, max_high_pairs + 1):
        for high_pairs in combinations(all_pairs, high_pair_count):
            if searched >= max_search_cases:
                complete = False
                break
            searched += 1
            D = two_level_high_pair_matrix(n, high_pairs)
            row = residual_row(
                case=f"two_level_p2x3_high_{high_pair_count}",
                D=D,
                focus=focus,
                branch_order=(0, 1, 2),
                context_before=(6,),
                context_after=(7,),
                high_pairs=high_pairs,
                max_examples=max_examples,
            )

            accepted = row["accepted_tuple_count"]
            product_count = row["product_tuple_count"]
            if accepted == 0:
                relation_kind_counts["empty"] += 1
            elif accepted == product_count:
                relation_kind_counts["full"] += 1
            else:
                relation_kind_counts["nontrivial"] += 1

            arity = row["minimal_coupling_support_size"] or 0
            minimal_arity_histogram[arity] = minimal_arity_histogram.get(arity, 0) + 1
            if accepted not in (0, product_count) and arity > 1 and best_non_unary is None:
                best_non_unary = row
            if accepted not in (0, product_count) and arity > 2:
                first_beyond_binary = row
                complete = True
                break
        if first_beyond_binary is not None or not complete:
            break

    summary = {
        "rows": len(rows),
        "two_level_search_complete": complete,
        "two_level_cases_searched": searched,
        "two_level_max_high_pairs": max_high_pairs,
        "two_level_max_search_cases": max_search_cases,
        "two_level_relation_kind_counts": relation_kind_counts,
        "two_level_minimal_arity_histogram": minimal_arity_histogram,
        "two_level_found_beyond_binary": first_beyond_binary is not None,
        "two_level_max_minimal_coupling_support_size": max(
            minimal_arity_histogram.keys(), default=0
        ),
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "bounded exact residual-relation arity probe; no beyond-binary "
            "case is only experimental evidence for this search family"
        ),
    }
    return {
        "method": "t088_residual_interface_probe",
        "parameters": {
            "max_high_pairs": max_high_pairs,
            "max_search_cases": max_search_cases,
            "max_examples": max_examples,
        },
        "summary": summary,
        "control_rows": rows,
        "best_non_unary_two_level": best_non_unary,
        "first_beyond_binary_two_level": first_beyond_binary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-high-pairs", type=int, default=4)
    parser.add_argument("--max-search-cases", type=int, default=25000)
    parser.add_argument("--max-examples", type=int, default=4)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_residual_interface_probe(
        max_high_pairs=args.max_high_pairs,
        max_search_cases=args.max_search_cases,
        max_examples=args.max_examples,
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
