#!/usr/bin/env python3
"""T085 probe: bounded formalization of the handwritten 4-block gadget.

The source sketch is ambiguous.  This probe does not assume one exact reading:
it searches small three-level dissimilarities on four two-leaf blocks and
compares a free P-node over the blocks with fixed C-node block orders.
"""

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

from pc_circular.pc_tree import (  # noqa: E402
    c_node,
    enumerate_frontiers,
    leaf,
    p_node,
)
from pc_circular.predicates import (  # noqa: E402
    all_circular_orders,
    canonical_circular_order,
    passes_bad_side_precircular_cR,
    validate_dissimilarity,
)
from pc_circular.solvers.local_constraints import (  # noqa: E402
    project_bad_side_obligations_to_pc_nodes,
    project_farthest_sets_to_pc_nodes,
)
from pc_circular.solvers.width4_experiments import (  # noqa: E402
    induced_child_circular_order,
)


BLOCK_NAMES = ("A", "B", "C", "D")
BLOCKS = ((0, 1), (2, 3), (4, 5), (6, 7))
LABEL_NAMES = {
    label: f"{BLOCK_NAMES[block_index]}{leaf_index}"
    for block_index, block in enumerate(BLOCKS)
    for leaf_index, label in enumerate(block)
}
LABEL_BY_NAME = {name: label for label, name in LABEL_NAMES.items()}
BLOCK_OF = {
    label: block_index
    for block_index, block in enumerate(BLOCKS)
    for label in block
}

# Best-effort transcription of the visible high-distance notes in the image.
# The middle note is ambiguous in the photo; A1-C1 is the conservative
# four-block/two-leaf interpretation used as a seed, not as a claim.
SKETCH_SEED_HIGH_PAIRS = (
    (LABEL_BY_NAME["A0"], LABEL_BY_NAME["D1"]),
    (LABEL_BY_NAME["A1"], LABEL_BY_NAME["C1"]),
    (LABEL_BY_NAME["B0"], LABEL_BY_NAME["C0"]),
)
SKETCH_BLOCK_PAIR_PATTERN = ((0, 3), (0, 2), (1, 2))
DISTANCE_PROFILES = {
    "sketch_flat_2_2_3": {
        "within_block": 2,
        "base_inter_block": 2,
        "selected_high_pair": 3,
    },
    "block_low_control_1_2_3": {
        "within_block": 1,
        "base_inter_block": 2,
        "selected_high_pair": 3,
    },
}


def _zero_matrix(n: int) -> list[list[int]]:
    return [[0 for _ in range(n)] for _ in range(n)]


def _canonical_pair(pair: tuple[int, int]) -> tuple[int, int]:
    left, right = pair
    if left == right:
        raise ValueError("high pairs must contain two distinct labels")
    return (left, right) if left < right else (right, left)


def _canonical_high_pairs(high_pairs) -> tuple[tuple[int, int], ...]:
    canonical = tuple(sorted({_canonical_pair(tuple(pair)) for pair in high_pairs}))
    for left, right in canonical:
        if BLOCK_OF[left] == BLOCK_OF[right]:
            raise ValueError("high pairs must be inter-block pairs in this probe")
    return canonical


def pair_name(pair: tuple[int, int]) -> str:
    left, right = _canonical_pair(pair)
    return f"{LABEL_NAMES[left]}-{LABEL_NAMES[right]}"


def branch_order_name(order) -> str:
    order = canonical_circular_order(tuple(order))
    return "".join(BLOCK_NAMES[index] for index in order)


def make_block_gadget_matrix(
    high_pairs=(),
    *,
    within_value: int = 2,
    base_value: int = 2,
    high_value: int = 3,
) -> list[list[int]]:
    """Build the three-level 4-block/two-leaf dissimilarity."""

    if not (within_value <= base_value < high_value):
        raise ValueError("expected within_value <= base_value < high_value")

    high_pair_set = set(_canonical_high_pairs(high_pairs))
    n = sum(len(block) for block in BLOCKS)
    D = _zero_matrix(n)
    for left in range(n):
        for right in range(left + 1, n):
            if BLOCK_OF[left] == BLOCK_OF[right]:
                value = within_value
            elif (left, right) in high_pair_set:
                value = high_value
            else:
                value = base_value
            D[left][right] = D[right][left] = value
    validate_dissimilarity(D)
    return D


def all_inter_block_pairs() -> tuple[tuple[int, int], ...]:
    return tuple(
        (left, right)
        for left in range(8)
        for right in range(left + 1, 8)
        if BLOCK_OF[left] != BLOCK_OF[right]
    )


def iter_sketch_pattern_high_pair_sets():
    """Enumerate all leaf-endpoint readings of the visible block-pair pattern."""

    choices = []
    for left_block, right_block in SKETCH_BLOCK_PAIR_PATTERN:
        choices.append(
            tuple(
                (left, right)
                for left in BLOCKS[left_block]
                for right in BLOCKS[right_block]
            )
        )
    for first in choices[0]:
        for second in choices[1]:
            for third in choices[2]:
                yield _canonical_high_pairs((first, second, third))


def block_p_tree():
    return p_node([p_node([leaf(label) for label in block]) for block in BLOCKS])


def block_c_tree(branch_order=(0, 1, 2, 3)):
    return c_node(
        [
            p_node([leaf(label) for label in BLOCKS[branch_index]])
            for branch_index in branch_order
        ]
    )


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _accepted_frontiers(D, frontiers) -> tuple[tuple[int, ...], ...]:
    return tuple(order for order in frontiers if passes_bad_side_precircular_cR(D, order))


def _ix_projection_silent(D, T) -> bool:
    report = project_farthest_sets_to_pc_nodes(D, T)
    return all(
        node["circular_ones_compatible"] is True
        and node["proper_nontrivial_count"] == 0
        and node["laminar_violation_count"] == 0
        and node["declared_order_interval_violation_count"] == 0
        for node in report["nodes"]
    )


def _root_bad_side_summary(D, T) -> dict:
    report = project_bad_side_obligations_to_pc_nodes(D, T)
    root = report["nodes"][0]
    return {
        "obligation_count": report["obligation_count"],
        "multi_level_obligation_count": report["multi_level_obligation_count"],
        "root_projection_hit_count": root["projection_hit_count"],
        "root_full_projection_count": root["full_projection_count"],
        "root_full_distinct_four_branch_count": root["full_distinct_four_branch_count"],
        "root_declared_order_violation_count": root["declared_order_violation_count"],
        "root_role_pattern_histogram": root["role_pattern_histogram"],
        "root_forbidden_chord_pair_count": root["forbidden_chord_pair_count"],
        "root_forbidden_chord_pairs": root["forbidden_chord_pairs"],
        "root_max_branch_interface_load": root["max_branch_interface_load"],
        "root_examples": root["examples"][:3],
    }


def _fixed_order_reports(D, fixed_frontiers_by_order: dict[tuple[int, ...], tuple]) -> dict:
    reports = {}
    for branch_order, frontiers in fixed_frontiers_by_order.items():
        accepted = _accepted_frontiers(D, frontiers)
        reports[branch_order_name(branch_order)] = {
            "exists": bool(accepted),
            "frontier_count": len(frontiers),
            "accepted_frontier_count": len(accepted),
            "witness_order": accepted[0] if accepted else None,
        }
    return reports


def evaluate_high_pair_set(
    high_pairs,
    *,
    profile_name: str = "sketch_flat_2_2_3",
    free_frontiers=None,
    fixed_frontiers_by_order=None,
) -> dict:
    high_pairs = _canonical_high_pairs(high_pairs)
    profile = DISTANCE_PROFILES[profile_name]
    D = make_block_gadget_matrix(
        high_pairs,
        within_value=profile["within_block"],
        base_value=profile["base_inter_block"],
        high_value=profile["selected_high_pair"],
    )
    free_T = block_p_tree()
    free_frontiers = tuple(free_frontiers or enumerate_frontiers(free_T, canonical=True))
    fixed_frontiers_by_order = fixed_frontiers_by_order or {
        tuple(order): tuple(enumerate_frontiers(block_c_tree(order), canonical=True))
        for order in all_circular_orders(4)
    }

    free_accepted = _accepted_frontiers(D, free_frontiers)
    child_label_sets = tuple(frozenset(block) for block in BLOCKS)
    accepted_branch_orders = tuple(
        sorted(
            {
                order
                for order in (
                    induced_child_circular_order(frontier, child_label_sets)
                    for frontier in free_accepted
                )
                if order is not None
            }
        )
    )
    accepted_branch_order_names = tuple(
        branch_order_name(order) for order in accepted_branch_orders
    )
    all_branch_order_names = tuple(branch_order_name(order) for order in all_circular_orders(4))
    rejected_branch_order_names = tuple(
        name for name in all_branch_order_names if name not in accepted_branch_order_names
    )
    fixed_reports = _fixed_order_reports(D, fixed_frontiers_by_order)
    free_exists = bool(free_accepted)
    fixed_abcd = fixed_reports[branch_order_name((0, 1, 2, 3))]
    root_bad_side = _root_bad_side_summary(D, free_T)
    ix_silent = _ix_projection_silent(D, free_T)

    flags = {
        "sketch_seed": high_pairs == _canonical_high_pairs(SKETCH_SEED_HIGH_PAIRS),
        "free_positive": free_exists,
        "free_negative": not free_exists,
        "free_positive_some_fixed_negative": free_exists
        and any(not item["exists"] for item in fixed_reports.values()),
        "free_positive_fixed_abcd_negative": free_exists and not fixed_abcd["exists"],
        "accepted_branch_order_not_full": free_exists
        and len(accepted_branch_order_names) < len(all_branch_order_names),
        "single_accepted_branch_order": len(accepted_branch_order_names) == 1,
        "ix_silent_bad_side_active": ix_silent and root_bad_side["obligation_count"] > 0,
        "root_has_four_branch_obligation": (
            root_bad_side["root_full_distinct_four_branch_count"] > 0
        ),
    }

    return {
        "profile": profile_name,
        "distance_levels": profile,
        "high_pair_count": len(high_pairs),
        "high_pairs": high_pairs,
        "high_pair_names": tuple(pair_name(pair) for pair in high_pairs),
        "free_p": {
            "exists": free_exists,
            "frontier_count": len(free_frontiers),
            "accepted_frontier_count": len(free_accepted),
            "witness_order": free_accepted[0] if free_accepted else None,
            "accepted_branch_order_count": len(accepted_branch_order_names),
            "accepted_branch_orders": accepted_branch_order_names,
            "rejected_branch_orders": rejected_branch_order_names,
        },
        "fixed_c_orders": fixed_reports,
        "farthest_projection_silent": ix_silent,
        "bad_side_projection": root_bad_side,
        "flags": flags,
    }


def iter_high_pair_sets(
    *,
    max_high_pairs: int,
    include_sketch_seed: bool = True,
    include_sketch_pattern: bool = True,
):
    if max_high_pairs < 0:
        raise ValueError("max_high_pairs must be non-negative")

    seen: set[tuple[tuple[int, int], ...]] = set()
    if include_sketch_seed:
        seed = _canonical_high_pairs(SKETCH_SEED_HIGH_PAIRS)
        seen.add(seed)
        yield seed

    if include_sketch_pattern:
        for high_pairs in iter_sketch_pattern_high_pair_sets():
            if high_pairs in seen:
                continue
            seen.add(high_pairs)
            yield high_pairs

    pairs = all_inter_block_pairs()
    for size in range(max_high_pairs + 1):
        for combo in combinations(pairs, size):
            high_pairs = _canonical_high_pairs(combo)
            if high_pairs in seen:
                continue
            seen.add(high_pairs)
            yield high_pairs


def _interesting_score(row: dict) -> tuple[int, int, int, int]:
    flags = row["flags"]
    return (
        int(flags["free_positive_fixed_abcd_negative"])
        + int(flags["single_accepted_branch_order"])
        + int(flags["ix_silent_bad_side_active"])
        + int(flags["root_has_four_branch_obligation"]),
        int(flags["free_positive_some_fixed_negative"]),
        row["bad_side_projection"]["root_full_distinct_four_branch_count"],
        row["bad_side_projection"]["obligation_count"],
    )


def run_handwritten_gadget_probe(
    *,
    max_high_pairs: int = 2,
    include_sketch_seed: bool = True,
    include_sketch_pattern: bool = True,
    profiles: tuple[str, ...] = tuple(DISTANCE_PROFILES),
    max_rows: int | None = None,
    max_examples: int = 20,
) -> dict:
    start = time.perf_counter()
    free_T = block_p_tree()
    free_frontiers = tuple(enumerate_frontiers(free_T, canonical=True))
    fixed_frontiers_by_order = {
        tuple(order): tuple(enumerate_frontiers(block_c_tree(order), canonical=True))
        for order in all_circular_orders(4)
    }

    rows = []
    index = 0
    for profile_name in profiles:
        if profile_name not in DISTANCE_PROFILES:
            raise ValueError(f"unknown distance profile: {profile_name}")
        for high_pairs in iter_high_pair_sets(
            max_high_pairs=max_high_pairs,
            include_sketch_seed=include_sketch_seed,
            include_sketch_pattern=include_sketch_pattern,
        ):
            if max_rows is not None and index >= max_rows:
                break
            rows.append(
                evaluate_high_pair_set(
                    high_pairs,
                    profile_name=profile_name,
                    free_frontiers=free_frontiers,
                    fixed_frontiers_by_order=fixed_frontiers_by_order,
                )
            )
            index += 1
        if max_rows is not None and index >= max_rows:
            break

    interesting_rows = sorted(rows, key=_interesting_score, reverse=True)[:max_examples]
    summary = {
        "rows": len(rows),
        "free_positive_rows": sum(1 for row in rows if row["flags"]["free_positive"]),
        "free_negative_rows": sum(1 for row in rows if row["flags"]["free_negative"]),
        "free_positive_some_fixed_negative_rows": sum(
            1 for row in rows if row["flags"]["free_positive_some_fixed_negative"]
        ),
        "free_positive_fixed_abcd_negative_rows": sum(
            1 for row in rows if row["flags"]["free_positive_fixed_abcd_negative"]
        ),
        "single_accepted_branch_order_rows": sum(
            1 for row in rows if row["flags"]["single_accepted_branch_order"]
        ),
        "ix_silent_bad_side_active_rows": sum(
            1 for row in rows if row["flags"]["ix_silent_bad_side_active"]
        ),
        "root_four_branch_obligation_rows": sum(
            1 for row in rows if row["flags"]["root_has_four_branch_obligation"]
        ),
        "max_obligation_count": max(
            (row["bad_side_projection"]["obligation_count"] for row in rows), default=0
        ),
        "max_root_four_branch_obligation_count": max(
            (
                row["bad_side_projection"]["root_full_distinct_four_branch_count"]
                for row in rows
            ),
            default=0,
        ),
        "seconds": time.perf_counter() - start,
        "interpretation": (
            "bounded diagnostic only; absence of a row is not a proof against "
            "the handwritten idea"
        ),
    }
    sketch_rows = [row for row in rows if row["flags"]["sketch_seed"]]
    return {
        "method": "t085_handwritten_4block_gadget_probe",
        "parameters": {
            "max_high_pairs": max_high_pairs,
            "include_sketch_seed": include_sketch_seed,
            "include_sketch_pattern": include_sketch_pattern,
            "profiles": profiles,
            "max_rows": max_rows,
            "max_examples": max_examples,
            "blocks": {
                BLOCK_NAMES[index]: tuple(LABEL_NAMES[label] for label in block)
                for index, block in enumerate(BLOCKS)
            },
            "sketch_seed_high_pairs": tuple(pair_name(pair) for pair in SKETCH_SEED_HIGH_PAIRS),
            "distance_profiles": DISTANCE_PROFILES,
        },
        "summary": summary,
        "sketch_seed_rows": sketch_rows,
        "interesting_rows": interesting_rows,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-high-pairs", type=int, default=2)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--max-examples", type=int, default=20)
    parser.add_argument("--no-sketch-seed", action="store_true")
    parser.add_argument("--no-sketch-pattern", action="store_true")
    parser.add_argument(
        "--profiles",
        default=",".join(DISTANCE_PROFILES),
        help="Comma-separated distance profile names",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_handwritten_gadget_probe(
        max_high_pairs=args.max_high_pairs,
        include_sketch_seed=not args.no_sketch_seed,
        include_sketch_pattern=not args.no_sketch_pattern,
        profiles=tuple(part for part in args.profiles.split(",") if part),
        max_rows=args.max_rows,
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
