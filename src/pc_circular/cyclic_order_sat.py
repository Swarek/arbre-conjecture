"""SAT-like cyclic-order experiments for bad-side constraints.

This module does not implement a scalable SAT solver.  It exposes the
chirotope-style variables that matter for cR constraints, then solves the
resulting same-side system by exact circular-order enumeration on small
instances.  The goal is to make local-to-global obstruction searches explicit.
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from .local_obstructions import induced_submatrix
from .predicates import all_circular_orders, validate_dissimilarity
from .solvers.dp_experiments import bad_witnesses_by_pair


Order = Sequence[int]
SameSideConstraint = tuple[int, int, int, int]


def _validate_constraint(n: int, constraint: SameSideConstraint) -> None:
    if len(set(constraint)) != 4:
        raise ValueError("same-side constraints require four distinct labels")
    if not set(constraint).issubset(set(range(n))):
        raise ValueError("constraint labels must lie in 0..n-1")


def is_on_clockwise_open_arc(order: Order, start: int, end: int, point: int) -> bool:
    """Return whether ``point`` lies on the clockwise open arc start -> end."""

    seq = tuple(order)
    if len(seq) != len(set(seq)):
        raise ValueError("order must not contain duplicate labels")
    if len({start, end, point}) != 3:
        raise ValueError("start, end and point must be distinct")
    position = {label: idx for idx, label in enumerate(seq)}
    if {start, end, point} - set(position):
        raise ValueError("labels must occur in order")
    n = len(seq)
    return 0 < (position[point] - position[start]) % n < (position[end] - position[start]) % n


def same_side_constraint_satisfied(order: Order, constraint: SameSideConstraint) -> bool:
    """Return whether two witnesses are on the same side of an endpoint chord.

    A constraint ``(a, c, b, d)`` means that witnesses ``b`` and ``d`` must be
    on the same open arc between endpoints ``a`` and ``c``.
    """

    a, c, b, d = constraint
    return is_on_clockwise_open_arc(order, a, c, b) is is_on_clockwise_open_arc(
        order, a, c, d
    )


def order_satisfies_same_side_system(
    order: Order, constraints: Sequence[SameSideConstraint]
) -> bool:
    """Return whether ``order`` satisfies every same-side constraint."""

    return all(same_side_constraint_satisfied(order, constraint) for constraint in constraints)


def same_side_constraints_from_dissimilarity(D) -> tuple[SameSideConstraint, ...]:
    """Return exact bad-side constraints induced by ``D``.

    For pair ``{a,c}``, every pair of bad witnesses ``b,d`` creates the
    constraint that ``b`` and ``d`` must lie on the same side of chord ``ac``.
    """

    validate_dissimilarity(D)
    constraints: list[SameSideConstraint] = []
    for (a, c), witnesses in bad_witnesses_by_pair(D).items():
        for b, d in combinations(witnesses, 2):
            constraints.append((a, c, b, d))
    return tuple(constraints)


def solve_same_side_system(
    n: int,
    constraints: Sequence[SameSideConstraint],
    *,
    max_orders: int | None = None,
) -> dict:
    """Solve a same-side cyclic-order system by exact order enumeration."""

    if n < 0:
        raise ValueError("n must be non-negative")
    for constraint in constraints:
        _validate_constraint(n, constraint)

    checked = 0
    for order in all_circular_orders(n):
        checked += 1
        if order_satisfies_same_side_system(order, constraints):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "checked_orders": checked,
                "constraint_count": len(constraints),
                "reason": "witness_found",
            }
        if max_orders is not None and checked >= max_orders:
            return {
                "exists": None,
                "order": None,
                "complete": False,
                "checked_orders": checked,
                "constraint_count": len(constraints),
                "reason": "order_limit_exceeded",
            }

    return {
        "exists": False,
        "order": None,
        "complete": True,
        "checked_orders": checked,
        "constraint_count": len(constraints),
        "reason": "exhausted_all_orders",
    }


def solve_bad_side_chirotope(D, *, max_orders: int | None = None) -> dict:
    """Solve cR existence for ``T=star`` through same-side chirotope constraints."""

    n = validate_dissimilarity(D)
    constraints = same_side_constraints_from_dissimilarity(D)
    result = solve_same_side_system(n, constraints, max_orders=max_orders)
    result["n"] = n
    return result


def local_chirotope_obstruction_profile(
    D,
    *,
    max_subset_size: int = 6,
    max_global_n: int = 9,
    max_orders: int | None = None,
) -> dict:
    """Find the smallest induced non-cR subset visible to the chirotope solver."""

    n = validate_dissimilarity(D)
    max_k = min(n, max_subset_size)
    checked_by_size: dict[str, int] = {}

    for k in range(4, max_k + 1):
        checked = 0
        for subset in combinations(range(n), k):
            checked += 1
            submatrix = induced_submatrix(D, subset)
            result = solve_bad_side_chirotope(submatrix, max_orders=max_orders)
            if not result["complete"]:
                checked_by_size[str(k)] = checked
                return {
                    "n": n,
                    "complete": False,
                    "global_exists": None,
                    "global_reason": "subset_order_limit_exceeded",
                    "min_negative_subset_size": None,
                    "negative_subset": None,
                    "all_subsets_positive_up_to": k - 1,
                    "checked_by_size": checked_by_size,
                    "global_checked_exactly": False,
                    "constraint_count": len(same_side_constraints_from_dissimilarity(D)),
                }
            if result["exists"] is False:
                checked_by_size[str(k)] = checked
                return {
                    "n": n,
                    "complete": True,
                    "global_exists": False,
                    "global_reason": "negative_induced_subset",
                    "min_negative_subset_size": k,
                    "negative_subset": list(subset),
                    "all_subsets_positive_up_to": k - 1,
                    "checked_by_size": checked_by_size,
                    "global_checked_exactly": False,
                    "constraint_count": len(same_side_constraints_from_dissimilarity(D)),
                }
        checked_by_size[str(k)] = checked

    if n <= max_global_n:
        global_result = solve_bad_side_chirotope(D, max_orders=max_orders)
        return {
            "n": n,
            "complete": bool(global_result["complete"]),
            "global_exists": global_result["exists"],
            "global_reason": global_result["reason"],
            "min_negative_subset_size": None,
            "negative_subset": None,
            "all_subsets_positive_up_to": max_k,
            "checked_by_size": checked_by_size,
            "global_checked_exactly": bool(global_result["complete"]),
            "checked_orders": global_result["checked_orders"],
            "constraint_count": global_result["constraint_count"],
        }

    return {
        "n": n,
        "complete": False,
        "global_exists": None,
        "global_reason": "not_checked_beyond_subset_cap",
        "min_negative_subset_size": None,
        "negative_subset": None,
        "all_subsets_positive_up_to": max_k,
        "checked_by_size": checked_by_size,
        "global_checked_exactly": False,
        "constraint_count": len(same_side_constraints_from_dissimilarity(D)),
    }
