"""Scratch space for dynamic-programming experiments on PC-trees.

Nothing here is a general solver.  The helpers in this module expose exact
fixed-order diagnostics that can later be used to design and falsify DP states.
"""

from __future__ import annotations

from itertools import combinations
from math import log2
from typing import Callable, Iterable, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels, represents_order
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    find_precircular_cR_violation,
    is_arc,
    is_precircular_order_cR,
    is_strict_circular_robinson_order,
    is_strict_precircular_order_cR,
    validate_dissimilarity,
)


Matrix = Sequence[Sequence[float]]
Order = Sequence[int]
BlockSignature = tuple[
    str,
    tuple[int, ...],
    tuple[int, ...],
    tuple[int, int],
    tuple[tuple[int, int, int], ...],
    tuple[tuple[int, int, int], ...],
]


def not_implemented_status():
    return {
        "implemented": False,
        "reason": "DP state and sufficiency proof obligations are still open",
    }


def is_bad_witness(D: Matrix, a: int, b: int, w: int) -> bool:
    """Return whether ``w`` violates the one-side cR bound for pair ``{a,b}``."""

    n = validate_dissimilarity(D)
    if not (0 <= a < n and 0 <= b < n and 0 <= w < n):
        raise ValueError("a, b and w must be labels in 0..n-1")
    if len({a, b, w}) < 3:
        return False
    return max(D[a][w], D[w][b]) > D[a][b]


def bad_witnesses_by_pair(D: Matrix) -> dict[tuple[int, int], tuple[int, ...]]:
    """Return all bad witnesses for every unordered pair of endpoints."""

    n = validate_dissimilarity(D)
    result: dict[tuple[int, int], tuple[int, ...]] = {}
    for a, b in combinations(range(n), 2):
        witnesses = tuple(w for w in range(n) if is_bad_witness(D, a, b, w))
        result[(a, b)] = witnesses
    return result


def _validated_order(D: Matrix, order: Order) -> tuple[int, ...]:
    n = validate_dissimilarity(D)
    seq = tuple(order)
    if len(seq) != n or set(seq) != set(range(n)):
        raise ValueError("order must be a permutation of 0..n-1")
    return seq


def _open_clockwise_arc(seq: tuple[int, ...], start_pos: int, end_pos: int) -> tuple[int, ...]:
    n = len(seq)
    result = []
    pos = (start_pos + 1) % n
    while pos != end_pos:
        result.append(seq[pos])
        pos = (pos + 1) % n
    return tuple(result)


def bad_side_signature(D: Matrix, order: Order) -> dict[tuple[int, int], dict[str, tuple[int, ...]]]:
    """Return bad witnesses on each open arc for every endpoint pair.

    For key ``(a,b)`` with ``a < b``, ``a_to_b`` is the clockwise open arc from
    label ``a`` to label ``b`` in the provided order, and ``b_to_a`` is the
    opposite open arc.  Witness tuples keep their circular order.
    """

    seq = _validated_order(D, order)
    position = {label: idx for idx, label in enumerate(seq)}
    signature: dict[tuple[int, int], dict[str, tuple[int, ...]]] = {}
    for a, b in combinations(range(len(seq)), 2):
        arc_a_to_b = _open_clockwise_arc(seq, position[a], position[b])
        arc_b_to_a = _open_clockwise_arc(seq, position[b], position[a])
        signature[(a, b)] = {
            "a_to_b": tuple(w for w in arc_a_to_b if is_bad_witness(D, a, b, w)),
            "b_to_a": tuple(w for w in arc_b_to_a if is_bad_witness(D, a, b, w)),
        }
    return signature


def find_bad_side_cr_violation(D: Matrix, order: Order) -> dict | None:
    """Return a cR violation expressed as bad witnesses on both arcs.

    The certificate is equivalent to a cyclic quadruple ``a, y, b, t`` with
    ``max(d(a,y), d(y,b)) > d(a,b)`` and
    ``max(d(a,t), d(t,b)) > d(a,b)``.
    """

    seq = _validated_order(D, order)
    position = {label: idx for idx, label in enumerate(seq)}

    for a, b in combinations(range(len(seq)), 2):
        arc_a_to_b = _open_clockwise_arc(seq, position[a], position[b])
        arc_b_to_a = _open_clockwise_arc(seq, position[b], position[a])
        bad_a_to_b = tuple(w for w in arc_a_to_b if is_bad_witness(D, a, b, w))
        bad_b_to_a = tuple(w for w in arc_b_to_a if is_bad_witness(D, a, b, w))
        if not bad_a_to_b or not bad_b_to_a:
            continue

        y = bad_a_to_b[0]
        t = bad_b_to_a[0]
        lhs = D[a][b]
        return {
            "pair": (a, b),
            "quadruple": (a, y, b, t),
            "positions": (position[a], position[y], position[b], position[t]),
            "a_to_b_witness": y,
            "b_to_a_witness": t,
            "a_to_b_bad_value": max(D[a][y], D[y][b]),
            "b_to_a_bad_value": max(D[a][t], D[t][b]),
            "lhs": lhs,
            "rhs": min(max(D[a][y], D[y][b]), max(D[a][t], D[t][b])),
            "a_to_b_bad_witnesses": bad_a_to_b,
            "b_to_a_bad_witnesses": bad_b_to_a,
        }
    return None


def passes_bad_side_cr_test(D: Matrix, order: Order) -> bool:
    """Return whether the bad-side fixed-order diagnostic finds no violation."""

    return find_bad_side_cr_violation(D, order) is None


def _bad_witness_constraint_stats(D: Matrix) -> dict:
    by_pair = bad_witnesses_by_pair(D)
    histogram: dict[int, int] = {}
    total = 0
    constraints = []
    for pair, witnesses in by_pair.items():
        count = len(witnesses)
        histogram[count] = histogram.get(count, 0) + 1
        total += count
        if witnesses:
            constraints.append({"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": count})
    return {
        "bad_pair_count": len(by_pair),
        "nonempty_bad_pair_count": sum(1 for witnesses in by_pair.values() if witnesses),
        "nontrivial_bad_pair_count": sum(1 for witnesses in by_pair.values() if len(witnesses) >= 2),
        "bad_witness_total": total,
        "bad_witness_histogram": dict(sorted(histogram.items())),
        "constraints": constraints,
    }


def bad_witness_arc_order_report(D: Matrix, order: Order) -> dict:
    seq = canonical_circular_order(_validated_order(D, order))
    by_pair = bad_witnesses_by_pair(D)
    side_signature = bad_side_signature(D, seq)

    first_one_side_violation = None
    first_set_arc_violation = None
    first_with_endpoints_arc_violation = None
    all_one_side = True
    all_set_arc = True
    all_with_endpoints_arc = True

    for pair, witnesses in by_pair.items():
        side = side_signature[pair]
        one_side = not (side["a_to_b"] and side["b_to_a"])
        if not one_side:
            all_one_side = False
            if first_one_side_violation is None:
                first_one_side_violation = {
                    "pair": pair,
                    "bad_witnesses": witnesses,
                    "a_to_b_bad_witnesses": side["a_to_b"],
                    "b_to_a_bad_witnesses": side["b_to_a"],
                    "cr_violation": find_bad_side_cr_violation(D, seq),
                }

        if not is_arc(seq, witnesses):
            all_set_arc = False
            if first_set_arc_violation is None:
                first_set_arc_violation = {
                    "pair": pair,
                    "bad_witnesses": witnesses,
                    "tested_set": witnesses,
                }

        with_endpoints = tuple(sorted(set(witnesses) | set(pair)))
        if not is_arc(seq, with_endpoints):
            all_with_endpoints_arc = False
            if first_with_endpoints_arc_violation is None:
                first_with_endpoints_arc_violation = {
                    "pair": pair,
                    "bad_witnesses": witnesses,
                    "tested_set": with_endpoints,
                }

    precircular = is_precircular_order_cR(D, seq)
    strict_precircular = is_strict_precircular_order_cR(D, seq)
    strict_circular = is_strict_circular_robinson_order(D, seq)
    return {
        "order": seq,
        "bad_witness_one_side": all_one_side,
        "bad_witness_set_arc": all_set_arc,
        "bad_witness_with_endpoints_arc": all_with_endpoints_arc,
        "precircular": precircular,
        "strict_precircular": strict_precircular,
        "strict_circular": strict_circular,
        "first_bad_witness_one_side_violation": first_one_side_violation,
        "first_bad_witness_set_arc_violation": first_set_arc_violation,
        "first_bad_witness_with_endpoints_arc_violation": first_with_endpoints_arc_violation,
        "one_side_precircular_mismatch": all_one_side != precircular,
        "set_arc_precircular_mismatch": all_set_arc != precircular,
        "with_endpoints_precircular_mismatch": all_with_endpoints_arc != precircular,
    }


def bad_witness_arc_constraints_report(
    D: Matrix,
    pc_tree: PCNode | None = None,
    *,
    max_n: int = 8,
    frontier_limit: int | None = None,
) -> dict:
    """Enumerate small orders and compare bad-witness arc constraints.

    This is a bounded Piste D/E diagnostic, not a solver.  The exact fixed-order
    cR reformulation is ``bad_witness_one_side``: every bad-witness set
    ``B(a,b)`` must lie on one of the two open arcs cut by endpoints ``a,b``.
    The standalone arc variants are deliberately reported separately because
    they are only candidate circular-ones-style approximations.
    """

    n = validate_dissimilarity(D)
    constraint_stats = _bad_witness_constraint_stats(D)
    base_report = {
        "implemented": True,
        "method": "bounded_bad_witness_arc_constraints_frontier_report",
        "n": n,
        "max_n": max_n,
        "pc_tree_provided": pc_tree is not None,
        "frontier_limit": frontier_limit,
        **constraint_stats,
    }
    if n > max_n:
        unknown = {
            "bad_witness_one_side": None,
            "bad_witness_set_arc": None,
            "bad_witness_with_endpoints_arc": None,
            "precircular": None,
            "strict_circular": None,
        }
        return {
            **base_report,
            "complete": False,
            "incomplete_reasons": ["n exceeds max_n"],
            "reason": "n exceeds bad_witness_arc_constraints_report max_n",
            "order_source": None,
            "order_count": None,
            "counts": None,
            "exists": unknown,
        }

    if pc_tree is None:
        order_source = "all_circular_orders"
        orders = list(all_circular_orders(n))
        frontier_limit_reached = False
    else:
        if set(labels(pc_tree)) != set(range(n)):
            raise ValueError("pc_tree labels must be exactly 0..n-1")
        order_source = "pc_tree_frontiers"
        probe_limit = frontier_limit + 1 if frontier_limit is not None else None
        orders = enumerate_frontiers(pc_tree, canonical=True, limit=probe_limit)
        frontier_limit_reached = frontier_limit is not None and len(orders) > frontier_limit
        if frontier_limit_reached:
            orders = orders[:frontier_limit]

    one_side_orders = []
    set_arc_orders = []
    with_endpoints_arc_orders = []
    precircular_orders = []
    strict_precircular_orders = []
    strict_circular_orders = []
    first_one_side_precircular_mismatch = None
    first_set_arc_precircular_mismatch = None
    first_with_endpoints_precircular_mismatch = None
    first_bad_witness_one_side_violation = None
    first_bad_witness_set_arc_violation = None
    first_bad_witness_with_endpoints_arc_violation = None
    representation_mismatch_count = 0
    first_representation_mismatch = None

    for order in orders:
        canonical = canonical_circular_order(order)
        if pc_tree is not None and not represents_order(pc_tree, canonical):
            representation_mismatch_count += 1
            if first_representation_mismatch is None:
                first_representation_mismatch = canonical

        order_report = bad_witness_arc_order_report(D, canonical)
        if order_report["bad_witness_one_side"]:
            one_side_orders.append(canonical)
        elif first_bad_witness_one_side_violation is None:
            first_bad_witness_one_side_violation = order_report["first_bad_witness_one_side_violation"]

        if order_report["bad_witness_set_arc"]:
            set_arc_orders.append(canonical)
        elif first_bad_witness_set_arc_violation is None:
            first_bad_witness_set_arc_violation = order_report["first_bad_witness_set_arc_violation"]

        if order_report["bad_witness_with_endpoints_arc"]:
            with_endpoints_arc_orders.append(canonical)
        elif first_bad_witness_with_endpoints_arc_violation is None:
            first_bad_witness_with_endpoints_arc_violation = order_report[
                "first_bad_witness_with_endpoints_arc_violation"
            ]

        if order_report["precircular"]:
            precircular_orders.append(canonical)
        if order_report["strict_precircular"]:
            strict_precircular_orders.append(canonical)
        if order_report["strict_circular"]:
            strict_circular_orders.append(canonical)

        if order_report["one_side_precircular_mismatch"] and first_one_side_precircular_mismatch is None:
            first_one_side_precircular_mismatch = order_report
        if order_report["set_arc_precircular_mismatch"] and first_set_arc_precircular_mismatch is None:
            first_set_arc_precircular_mismatch = order_report
        if (
            order_report["with_endpoints_precircular_mismatch"]
            and first_with_endpoints_precircular_mismatch is None
        ):
            first_with_endpoints_precircular_mismatch = order_report

    incomplete_reasons = []
    if frontier_limit_reached:
        incomplete_reasons.append("frontier_limit reached")
    if representation_mismatch_count:
        incomplete_reasons.append("enumerated frontier failed represents_order sanity check")
    complete = not incomplete_reasons

    counts = {
        "orders_seen": len(orders),
        "bad_witness_one_side": len(one_side_orders),
        "bad_witness_set_arc": len(set_arc_orders),
        "bad_witness_with_endpoints_arc": len(with_endpoints_arc_orders),
        "precircular": len(precircular_orders),
        "strict_precircular": len(strict_precircular_orders),
        "strict_circular": len(strict_circular_orders),
        "one_side_precircular_mismatch": 1 if first_one_side_precircular_mismatch is not None else 0,
        "set_arc_precircular_mismatch": 1 if first_set_arc_precircular_mismatch is not None else 0,
        "with_endpoints_precircular_mismatch": 1 if first_with_endpoints_precircular_mismatch is not None else 0,
        "representation_mismatch": representation_mismatch_count,
    }
    exists = {
        "bad_witness_one_side": True if one_side_orders else (False if complete else None),
        "bad_witness_set_arc": True if set_arc_orders else (False if complete else None),
        "bad_witness_with_endpoints_arc": True if with_endpoints_arc_orders else (False if complete else None),
        "precircular": True if precircular_orders else (False if complete else None),
        "strict_circular": True if strict_circular_orders else (False if complete else None),
    }

    return {
        **base_report,
        "complete": complete,
        "incomplete_reasons": incomplete_reasons,
        "order_source": order_source,
        "order_count": len(orders),
        "counts": counts,
        "exists": exists,
        "bad_witness_one_side_orders": one_side_orders,
        "bad_witness_set_arc_orders": set_arc_orders,
        "bad_witness_with_endpoints_arc_orders": with_endpoints_arc_orders,
        "precircular_orders": precircular_orders,
        "strict_precircular_orders": strict_precircular_orders,
        "strict_circular_orders": strict_circular_orders,
        "first_bad_witness_one_side_violation": first_bad_witness_one_side_violation,
        "first_bad_witness_set_arc_violation": first_bad_witness_set_arc_violation,
        "first_bad_witness_with_endpoints_arc_violation": first_bad_witness_with_endpoints_arc_violation,
        "first_one_side_precircular_mismatch": first_one_side_precircular_mismatch,
        "first_set_arc_precircular_mismatch": first_set_arc_precircular_mismatch,
        "first_with_endpoints_precircular_mismatch": first_with_endpoints_precircular_mismatch,
        "first_representation_mismatch": first_representation_mismatch,
    }


def _validated_block(
    D: Matrix,
    block_order: Order,
    universe: Iterable[int] | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    n = validate_dissimilarity(D)
    if universe is None:
        universe_seq = tuple(range(n))
    else:
        universe_seq = tuple(universe)
    if len(universe_seq) != len(set(universe_seq)):
        raise ValueError("universe must not contain duplicates")
    if any(label < 0 or label >= n for label in universe_seq):
        raise ValueError("universe labels must be in 0..n-1")

    seq = tuple(block_order)
    if not seq:
        raise ValueError("block_order must not be empty")
    if len(seq) != len(set(seq)):
        raise ValueError("block_order must not contain duplicates")
    if not set(seq).issubset(set(universe_seq)):
        raise ValueError("block_order must be contained in universe")
    return seq, universe_seq


def _side_mask_for_linear_position(D: Matrix, a: int, b: int, seq: tuple[int, ...], pos: int) -> int:
    left_has_bad = any(is_bad_witness(D, a, b, w) for w in seq[:pos])
    right_has_bad = any(is_bad_witness(D, a, b, w) for w in seq[pos + 1 :])
    return (1 if left_has_bad else 0) | (2 if right_has_bad else 0)


def _side_mask_for_block_pair(D: Matrix, a: int, b: int, seq: tuple[int, ...], position: dict[int, int]) -> int:
    lo, hi = sorted((position[a], position[b]))
    between = seq[lo + 1 : hi]
    through_boundary = seq[:lo] + seq[hi + 1 :]
    between_has_bad = any(is_bad_witness(D, a, b, w) for w in between)
    through_boundary_has_bad = any(is_bad_witness(D, a, b, w) for w in through_boundary)
    return (1 if between_has_bad else 0) | (2 if through_boundary_has_bad else 0)


def block_bad_side_signature(
    D: Matrix,
    block_order: Order,
    *,
    universe: Iterable[int] | None = None,
) -> BlockSignature:
    """Return a coarse oriented-block signature for future DP falsification.

    The signature is for experiments only.  It assumes ``block_order`` will
    appear as a contiguous oriented block in a larger circular order.  In the
    ``inside/inside`` section, mask bit 1 means a bad witness appears between
    the two endpoints inside the linear block, and bit 2 means a bad witness
    appears on the side that passes through the block boundary and future
    external context.
    """

    seq, universe_seq = _validated_block(D, block_order, universe)
    block = set(seq)
    outside = tuple(label for label in universe_seq if label not in block)
    position = {label: idx for idx, label in enumerate(seq)}

    ei_masks: list[tuple[int, int, int]] = []
    for a in sorted(block):
        for e in outside:
            mask = _side_mask_for_linear_position(D, a, e, seq, position[a])
            ei_masks.append((a, e, mask))

    ii_masks: list[tuple[int, int, int]] = []
    for a, b in combinations(sorted(block), 2):
        mask = _side_mask_for_block_pair(D, a, b, seq, position)
        ii_masks.append((a, b, mask))

    return (
        "block_bad_side_v1",
        tuple(sorted(block)),
        universe_seq,
        (seq[0], seq[-1]),
        tuple(ei_masks),
        tuple(ii_masks),
    )


def forced_bad_side_pairs_in_block(
    D: Matrix,
    block_order: Order,
    *,
    universe: Iterable[int] | None = None,
) -> dict[str, tuple[tuple[int, int], ...]]:
    """Return endpoint pairs already forced bad on both block sides."""

    signature = block_bad_side_signature(D, block_order, universe=universe)
    ei_pairs = tuple((a, e) for a, e, mask in signature[4] if mask == 3)
    ii_pairs = tuple((a, b) for a, b, mask in signature[5] if mask == 3)
    return {"inside_external": ei_pairs, "inside_inside": ii_pairs}


def block_signature_bucket_report(
    D: Matrix,
    block_frontiers: Iterable[Order],
    *,
    universe: Iterable[int] | None = None,
) -> dict:
    """Group block frontiers by signature and report compression metrics."""

    frontiers = [tuple(frontier) for frontier in block_frontiers]
    if not frontiers:
        return {
            "frontier_count": 0,
            "signature_count": 0,
            "signature_ratio": 0.0,
            "frontiers_per_signature": 0.0,
            "median_bucket_size": 0.0,
            "log2_signature_count": 0.0,
            "collision_bucket_count": 0,
            "largest_bucket_size": 0,
            "forced_reject_frontiers": 0,
            "endpoint_conditioned": [],
            "example_collision_bucket": None,
        }

    buckets: dict[BlockSignature, list[tuple[int, ...]]] = {}
    frontier_signatures: dict[tuple[int, ...], BlockSignature] = {}
    forced_reject_frontiers = 0
    for frontier in frontiers:
        signature = block_bad_side_signature(D, frontier, universe=universe)
        frontier_signatures[frontier] = signature
        buckets.setdefault(signature, []).append(frontier)
        if any(mask == 3 for _, _, mask in signature[4]) or any(mask == 3 for _, _, mask in signature[5]):
            forced_reject_frontiers += 1

    collision_buckets = [items for items in buckets.values() if len(items) > 1]
    bucket_sizes = sorted(len(items) for items in buckets.values())
    largest_bucket = bucket_sizes[-1]
    midpoint = len(bucket_sizes) // 2
    if len(bucket_sizes) % 2:
        median_bucket_size = float(bucket_sizes[midpoint])
    else:
        median_bucket_size = (bucket_sizes[midpoint - 1] + bucket_sizes[midpoint]) / 2

    endpoint_buckets: dict[tuple[int, int], list[tuple[int, ...]]] = {}
    for frontier in frontiers:
        endpoint_buckets.setdefault((frontier[0], frontier[-1]), []).append(frontier)
    endpoint_conditioned = []
    for endpoints, items in sorted(endpoint_buckets.items()):
        signatures = {frontier_signatures[item] for item in items}
        endpoint_conditioned.append(
            {
                "endpoints": endpoints,
                "frontiers": len(items),
                "signatures": len(signatures),
                "signature_ratio": len(signatures) / len(items),
            }
        )

    example = None
    if collision_buckets:
        bucket = max(collision_buckets, key=len)
        example = {"bucket_size": len(bucket), "frontiers": bucket[:3]}

    return {
        "frontier_count": len(frontiers),
        "signature_count": len(buckets),
        "signature_ratio": len(buckets) / len(frontiers),
        "frontiers_per_signature": len(frontiers) / len(buckets),
        "median_bucket_size": median_bucket_size,
        "log2_signature_count": log2(len(buckets)),
        "collision_bucket_count": len(collision_buckets),
        "largest_bucket_size": largest_bucket,
        "forced_reject_frontiers": forced_reject_frontiers,
        "endpoint_conditioned": endpoint_conditioned,
        "example_collision_bucket": example,
    }


def find_signature_collision(
    D: Matrix,
    block_frontiers: Iterable[Order],
    contexts: Iterable[Order],
    *,
    universe: Iterable[int] | None = None,
    signature_func: Callable[[tuple[int, ...]], object] | None = None,
    max_pairs_per_signature: int | None = None,
) -> dict | None:
    """Find two equal-signature blocks that differ in one external context."""

    frontiers = [tuple(frontier) for frontier in block_frontiers]
    if not frontiers:
        return None
    _, universe_seq = _validated_block(D, frontiers[0], universe)
    context_list = [tuple(context) for context in contexts]
    if max_pairs_per_signature is not None and max_pairs_per_signature < 0:
        raise ValueError("max_pairs_per_signature must be non-negative or None")

    def default_signature(frontier: tuple[int, ...]) -> object:
        return block_bad_side_signature(D, frontier, universe=universe_seq)

    make_signature = signature_func or default_signature
    buckets: dict[object, list[tuple[int, ...]]] = {}
    for frontier in frontiers:
        _validated_block(D, frontier, universe_seq)
        buckets.setdefault(make_signature(frontier), []).append(frontier)

    universe_set = set(universe_seq)
    for signature, bucket in buckets.items():
        if len(bucket) < 2:
            continue
        checked_pairs = 0
        for left_index in range(len(bucket)):
            for right_index in range(left_index + 1, len(bucket)):
                if max_pairs_per_signature is not None and checked_pairs >= max_pairs_per_signature:
                    break
                checked_pairs += 1
                sigma = bucket[left_index]
                tau = bucket[right_index]
                if set(sigma) != set(tau):
                    continue
                outside = universe_set - set(sigma)
                for context in context_list:
                    if set(context) != outside or len(context) != len(outside):
                        raise ValueError("each context must contain exactly the labels outside the block")
                    order_sigma = sigma + context
                    order_tau = tau + context
                    cr_sigma = is_precircular_order_cR(D, order_sigma)
                    cr_tau = is_precircular_order_cR(D, order_tau)
                    if cr_sigma != cr_tau:
                        return {
                            "signature": signature,
                            "frontier_a": sigma,
                            "frontier_b": tau,
                            "context": context,
                            "order_a": order_sigma,
                            "order_b": order_tau,
                            "cr_a": cr_sigma,
                            "cr_b": cr_tau,
                            "violation_a": find_precircular_cR_violation(D, order_sigma),
                            "violation_b": find_precircular_cR_violation(D, order_tau),
                        }
            if max_pairs_per_signature is not None and checked_pairs >= max_pairs_per_signature:
                break
    return None
