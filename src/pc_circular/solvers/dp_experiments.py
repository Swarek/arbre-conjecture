"""Scratch space for dynamic-programming experiments on PC-trees.

Nothing here is a general solver.  The helpers in this module expose exact
fixed-order diagnostics that can later be used to design and falsify DP states.
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from pc_circular.predicates import validate_dissimilarity


Matrix = Sequence[Sequence[float]]
Order = Sequence[int]


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
