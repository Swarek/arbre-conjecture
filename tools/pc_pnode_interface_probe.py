#!/usr/bin/env python3
"""T086 probe: fixed-branch-order interface product diagnostics."""

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

from pc_circular.generators import (  # noqa: E402
    equal_distance_instance,
    matching_high_graph_plus_low_hub,
    single_bad_side_quartet_instance,
)
from pc_circular.pc_tree import leaf, p_node  # noqa: E402
from pc_circular.predicates import all_circular_orders  # noqa: E402
from pc_circular.solvers.interface_experiments import (  # noqa: E402
    root_fixed_order_interface_product_report,
)
from tools.pc_handwritten_gadget_probe import (  # noqa: E402
    DISTANCE_PROFILES,
    SKETCH_SEED_HIGH_PAIRS,
    block_p_tree,
    make_block_gadget_matrix,
)


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _branch_order_name(branch_order: tuple[int, ...]) -> str:
    return "".join(str(item) for item in branch_order)


def _row(
    *,
    case: str,
    D,
    T,
    branch_order: tuple[int, ...],
    max_branch_options: int,
    max_product_tuples: int,
    max_examples: int,
) -> dict:
    report = root_fixed_order_interface_product_report(
        D,
        T,
        branch_order=branch_order,
        max_branch_options=max_branch_options,
        max_product_tuples=max_product_tuples,
        max_examples=max_examples,
    )
    return {
        "case": case,
        "branch_order_name": _branch_order_name(branch_order),
        "complete": report["complete"],
        "factorizes": report["factorizes"],
        "accepted_tuple_count": report["accepted_tuple_count"],
        "projection_product_count": report["projection_product_count"],
        "false_product_count": report["false_product_count"],
        "minimal_coupling_support_size": report["minimal_coupling_support_size"],
        "product_tuple_count": report["product_tuple_count"],
        "branch_option_counts": report["branch_option_counts"],
        "bad_side_projection": report["bad_side_projection"],
        "accepted_tuple_examples": report["accepted_tuple_examples"],
        "false_product_examples": report["false_product_examples"],
        "closure_by_arity": report["closure_by_arity"],
        "interpretation": report["interpretation"],
    }


def _nested_p2_tree():
    return p_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)])])


def _t046_tree():
    return p_node([p_node([leaf(1), leaf(3)]), p_node([leaf(2), leaf(4)]), leaf(0)])


def run_pnode_interface_probe(
    *,
    max_branch_options: int = 256,
    max_product_tuples: int = 200000,
    max_examples: int = 5,
) -> dict:
    start = time.perf_counter()
    rows = []

    rows.append(
        _row(
            case="equal_nested_p2_control",
            D=equal_distance_instance(4),
            T=_nested_p2_tree(),
            branch_order=(0, 1),
            max_branch_options=max_branch_options,
            max_product_tuples=max_product_tuples,
            max_examples=max_examples,
        )
    )
    rows.append(
        _row(
            case="single_bad_side_nested_p2",
            D=single_bad_side_quartet_instance(),
            T=_nested_p2_tree(),
            branch_order=(0, 1),
            max_branch_options=max_branch_options,
            max_product_tuples=max_product_tuples,
            max_examples=max_examples,
        )
    )
    rows.append(
        _row(
            case="t046_matching_low_hub_nested",
            D=matching_high_graph_plus_low_hub(5),
            T=_t046_tree(),
            branch_order=(0, 1, 2),
            max_branch_options=max_branch_options,
            max_product_tuples=max_product_tuples,
            max_examples=max_examples,
        )
    )

    for profile_name, profile in DISTANCE_PROFILES.items():
        D = make_block_gadget_matrix(
            SKETCH_SEED_HIGH_PAIRS,
            within_value=profile["within_block"],
            base_value=profile["base_inter_block"],
            high_value=profile["selected_high_pair"],
        )
        T = block_p_tree()
        for branch_order in all_circular_orders(4):
            rows.append(
                _row(
                    case=f"handwritten_seed_{profile_name}",
                    D=D,
                    T=T,
                    branch_order=tuple(branch_order),
                    max_branch_options=max_branch_options,
                    max_product_tuples=max_product_tuples,
                    max_examples=max_examples,
                )
            )

    complete_rows = [row for row in rows if row["complete"]]
    refuted_rows = [row for row in complete_rows if not row["factorizes"]]
    summary = {
        "rows": len(rows),
        "complete_rows": len(complete_rows),
        "incomplete_rows": len(rows) - len(complete_rows),
        "factorized_rows": sum(1 for row in complete_rows if row["factorizes"]),
        "refuted_rows": len(refuted_rows),
        "max_false_product_count": max(
            (row["false_product_count"] for row in complete_rows), default=0
        ),
        "max_minimal_coupling_support_size": max(
            (
                row["minimal_coupling_support_size"] or 0
                for row in complete_rows
            ),
            default=0,
        ),
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "diagnostic only; refuted rows show product-factorization failure "
            "for fixed root branch order, not a general impossibility result"
        ),
    }
    return {
        "method": "t086_pnode_interface_product_probe",
        "parameters": {
            "max_branch_options": max_branch_options,
            "max_product_tuples": max_product_tuples,
            "max_examples": max_examples,
        },
        "summary": summary,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-branch-options", type=int, default=256)
    parser.add_argument("--max-product-tuples", type=int, default=200000)
    parser.add_argument("--max-examples", type=int, default=5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_pnode_interface_probe(
        max_branch_options=args.max_branch_options,
        max_product_tuples=args.max_product_tuples,
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
