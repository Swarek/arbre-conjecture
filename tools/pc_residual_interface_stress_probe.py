#!/usr/bin/env python3
"""T089 probe: stress richer residual interface families."""

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

from pc_circular.pc_tree import leaf, p_node  # noqa: E402
from tools.pc_residual_interface_probe import (  # noqa: E402
    residual_row,
    two_level_high_pair_matrix,
)


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def branch_size_focus(branch_sizes: tuple[int, ...]):
    if not branch_sizes or any(size <= 0 for size in branch_sizes):
        raise ValueError("branch_sizes must be positive")

    next_label = 0
    children = []
    for size in branch_sizes:
        children.append(p_node([leaf(label) for label in range(next_label, next_label + size)]))
        next_label += size
    return p_node(children), next_label


def _all_pairs(n: int) -> tuple[tuple[int, int], ...]:
    return tuple((left, right) for left in range(n) for right in range(left + 1, n))


def _sample_high_pairs(rng: random.Random, pairs, high_pair_counts) -> tuple[tuple[int, int], ...]:
    high_pair_count = int(rng.choice(tuple(high_pair_counts)))
    return tuple(sorted(rng.sample(tuple(pairs), high_pair_count)))


def _profile_row(
    *,
    case: str,
    branch_sizes: tuple[int, ...],
    high_pairs,
    max_examples: int,
) -> dict:
    focus, used_labels = branch_size_focus(branch_sizes)
    D = two_level_high_pair_matrix(used_labels + 2, high_pairs)
    return residual_row(
        case=case,
        D=D,
        focus=focus,
        branch_order=tuple(range(len(branch_sizes))),
        context_before=(used_labels,),
        context_after=(used_labels + 1,),
        high_pairs=high_pairs,
        max_examples=max_examples,
    )


def _empty_profile_summary() -> dict:
    return {
        "trials": 0,
        "relation_kind_counts": {"empty": 0, "full": 0, "nontrivial": 0},
        "minimal_arity_histogram": {},
        "max_minimal_coupling_support_size": 0,
        "found_beyond_binary": False,
        "first_beyond_binary": None,
        "best_non_unary": None,
    }


def _stress_profile(
    *,
    case: str,
    branch_sizes: tuple[int, ...],
    trials: int,
    high_pair_counts,
    seed: int,
    max_examples: int,
) -> dict:
    if trials < 0:
        raise ValueError("trials must be non-negative")
    rng = random.Random(seed)
    focus, used_labels = branch_size_focus(branch_sizes)
    n = used_labels + 2
    pairs = _all_pairs(n)
    summary = _empty_profile_summary()
    summary.update(
        {
            "case": case,
            "branch_sizes": branch_sizes,
            "seed": seed,
            "high_pair_counts": tuple(high_pair_counts),
            "trials_requested": trials,
        }
    )

    for trial in range(trials):
        high_pairs = _sample_high_pairs(rng, pairs, high_pair_counts)
        D = two_level_high_pair_matrix(n, high_pairs)
        row = residual_row(
            case=case,
            D=D,
            focus=focus,
            branch_order=tuple(range(len(branch_sizes))),
            context_before=(used_labels,),
            context_after=(used_labels + 1,),
            high_pairs=high_pairs,
            max_examples=max_examples,
        )
        accepted = row["accepted_tuple_count"]
        product_count = row["product_tuple_count"]
        if accepted == 0:
            summary["relation_kind_counts"]["empty"] += 1
        elif accepted == product_count:
            summary["relation_kind_counts"]["full"] += 1
        else:
            summary["relation_kind_counts"]["nontrivial"] += 1

        arity = row["minimal_coupling_support_size"] or 0
        histogram = summary["minimal_arity_histogram"]
        histogram[arity] = histogram.get(arity, 0) + 1
        summary["max_minimal_coupling_support_size"] = max(
            summary["max_minimal_coupling_support_size"],
            arity,
        )

        best = summary["best_non_unary"]
        if accepted not in (0, product_count) and arity > 1:
            if (
                best is None
                or arity > (best["minimal_coupling_support_size"] or 0)
                or (
                    arity == (best["minimal_coupling_support_size"] or 0)
                    and accepted < best["accepted_tuple_count"]
                )
            ):
                summary["best_non_unary"] = row

        if accepted not in (0, product_count) and arity > 2:
            summary["found_beyond_binary"] = True
            summary["first_beyond_binary"] = row
            summary["trials"] = trial + 1
            return summary

    summary["trials"] = trials
    return summary


def run_residual_interface_stress_probe(
    *,
    p2x4_trials: int = 5000,
    p3x3_trials: int = 1500,
    seed: int = 20260593,
    max_examples: int = 4,
) -> dict:
    start = time.perf_counter()

    controls = [
        _profile_row(
            case="p2x4_binary_seed",
            branch_sizes=(2, 2, 2, 2),
            high_pairs=((0, 2), (1, 3)),
            max_examples=max_examples,
        ),
        _profile_row(
            case="p3x3_binary_seed",
            branch_sizes=(3, 3, 3),
            high_pairs=((0, 4), (0, 5), (1, 7), (2, 6)),
            max_examples=max_examples,
        ),
    ]
    profiles = [
        _stress_profile(
            case="p2x4_sparse_two_level_random",
            branch_sizes=(2, 2, 2, 2),
            trials=p2x4_trials,
            high_pair_counts=range(1, 9),
            seed=seed,
            max_examples=max_examples,
        ),
        _stress_profile(
            case="p3x3_sparse_two_level_random",
            branch_sizes=(3, 3, 3),
            trials=p3x3_trials,
            high_pair_counts=range(1, 9),
            seed=seed,
            max_examples=max_examples,
        ),
    ]
    found_beyond_binary = any(profile["found_beyond_binary"] for profile in profiles)
    max_arity = max(
        [control["minimal_coupling_support_size"] or 0 for control in controls]
        + [profile["max_minimal_coupling_support_size"] for profile in profiles],
        default=0,
    )
    summary = {
        "control_rows": len(controls),
        "profiles": len(profiles),
        "found_beyond_binary": found_beyond_binary,
        "max_minimal_coupling_support_size": max_arity,
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "bounded stress of richer residual interfaces; absence of "
            "beyond-binary relations is not a proof"
        ),
    }
    return {
        "method": "t089_residual_interface_stress_probe",
        "parameters": {
            "p2x4_trials": p2x4_trials,
            "p3x3_trials": p3x3_trials,
            "seed": seed,
            "max_examples": max_examples,
        },
        "summary": summary,
        "control_rows": controls,
        "profiles": profiles,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p2x4-trials", type=int, default=5000)
    parser.add_argument("--p3x3-trials", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=20260593)
    parser.add_argument("--max-examples", type=int, default=4)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_residual_interface_stress_probe(
        p2x4_trials=args.p2x4_trials,
        p3x3_trials=args.p3x3_trials,
        seed=args.seed,
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
