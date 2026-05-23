"""Experimental helpers for strict circular Robinson sub-cases.

These functions enumerate fixed orders on small instances.  They are research
instrumentation for Piste F, not a general solver and not used by candidate.py.
"""

from __future__ import annotations

from pc_circular.pc_tree import PCNode, enumerate_frontiers, represents_order
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    farthest_sets,
    is_strict_circular_robinson_order,
    is_strict_precircular_order_cR,
    is_strict_quasi_circular_order,
    validate_dissimilarity,
)


def strict_order_report(D, pc_tree: PCNode | None = None, *, max_n: int = 8) -> dict:
    """Enumerate strict fixed-order predicates for small instances.

    The report separates strict quasi one-side, strict pre-circular and strict
    circular Robinson orders.  It is exact only while enumeration is allowed by
    ``max_n``.
    """

    n = validate_dissimilarity(D)
    if n > max_n:
        return {
            "n": n,
            "complete": False,
            "reason": "n exceeds strict_order_report max_n",
            "max_n": max_n,
        }

    if pc_tree is None:
        orders = list(all_circular_orders(n))
    else:
        orders = enumerate_frontiers(pc_tree, canonical=True)

    strict_quasi_orders = []
    strict_precircular_orders = []
    strict_circular_orders = []
    for order in orders:
        canonical = canonical_circular_order(order)
        if is_strict_quasi_circular_order(D, canonical):
            strict_quasi_orders.append(canonical)
        if is_strict_precircular_order_cR(D, canonical):
            strict_precircular_orders.append(canonical)
        if is_strict_circular_robinson_order(D, canonical):
            if pc_tree is None or represents_order(pc_tree, canonical):
                strict_circular_orders.append(canonical)

    return {
        "n": n,
        "complete": True,
        "order_count": len(orders),
        "strict_quasi_count": len(strict_quasi_orders),
        "strict_precircular_count": len(strict_precircular_orders),
        "strict_circular_count": len(strict_circular_orders),
        "strict_quasi_witness": strict_quasi_orders[0] if strict_quasi_orders else None,
        "strict_precircular_witness": strict_precircular_orders[0] if strict_precircular_orders else None,
        "strict_circular_witness": strict_circular_orders[0] if strict_circular_orders else None,
    }


def strict_algorithm52_report(D, pc_tree: PCNode | None = None, *, max_candidates: int = 10_000) -> dict:
    """Generate and verify candidates inspired by Algorithm 5.2.

    The paper's algorithm outputs a compatible order when the input is already
    strict quasi-circular.  This experimental version is deliberately defensive:
    it tries all choices of ``x`` and ``x' in F_x``, generates the two possible
    orientations of the ``N`` and ``F`` arcs in the disjoint case, and then
    verifies each generated order with the direct strict predicates.

    This is not used by ``candidate.py`` and is not a proof of completeness for
    arbitrary non-strict inputs.
    """

    n = validate_dissimilarity(D)
    candidates: set[tuple[int, ...]] = set()
    limit_hit = False
    farthest = farthest_sets(D)

    def add(order) -> None:
        nonlocal limit_hit
        order = tuple(order)
        if len(order) != n or len(set(order)) != n:
            return
        canonical = canonical_circular_order(order)
        if canonical in candidates:
            return
        if len(candidates) >= max_candidates:
            limit_hit = True
            return
        candidates.add(canonical)

    for x in range(n):
        for xp in sorted(farthest[x]):
            N = {u for u in range(n) if D[u][x] <= D[u][xp]}
            F = {u for u in range(n) if D[u][xp] <= D[u][x]}
            middle = sorted(N & F)
            if middle:
                for y in middle:
                    X1 = _strict_J(D, x, y) | _strict_J(D, y, xp)
                    X2 = set(range(n)) - X1
                    add(_sort_by_distance(D, x, X1) + _reverse_sort_by_distance(D, x, X2))
                continue

            z_choices = _argmax_by_distance(D, x, N)
            y_choices = _argmax_by_distance(D, xp, F)
            for z in z_choices:
                N_prime = _strict_J(D, x, z)
                N_orders = _segment_options(D, x, N, N_prime)
                for y in y_choices:
                    F_prime = _strict_J(D, xp, y)
                    F_orders = _segment_options(D, xp, F, F_prime)
                    for N_order in N_orders:
                        for F_order in F_orders:
                            add(N_order + F_order)
                            add(N_order + tuple(reversed(F_order)))
                    if limit_hit:
                        break
                if limit_hit:
                    break
            if limit_hit:
                break
        if limit_hit:
            break

    candidate_orders = sorted(candidates)
    if pc_tree is None:
        represented_orders = candidate_orders
        unrepresented_strict_circular = []
    else:
        represented_orders = [order for order in candidate_orders if represents_order(pc_tree, order)]
        unrepresented_strict_circular = [
            order for order in candidate_orders if order not in represented_orders and is_strict_circular_robinson_order(D, order)
        ]

    strict_quasi_orders = [order for order in represented_orders if is_strict_quasi_circular_order(D, order)]
    strict_precircular_orders = [order for order in represented_orders if is_strict_precircular_order_cR(D, order)]
    strict_circular_orders = [order for order in represented_orders if is_strict_circular_robinson_order(D, order)]

    return {
        "n": n,
        "complete": not limit_hit,
        "max_candidates": max_candidates,
        "candidate_count": len(candidate_orders),
        "represented_candidate_count": len(represented_orders),
        "strict_quasi_count": len(strict_quasi_orders),
        "strict_precircular_count": len(strict_precircular_orders),
        "strict_circular_count": len(strict_circular_orders),
        "unrepresented_strict_circular_count": len(unrepresented_strict_circular),
        "candidate_orders": candidate_orders,
        "strict_quasi_orders": strict_quasi_orders,
        "strict_precircular_orders": strict_precircular_orders,
        "strict_circular_orders": strict_circular_orders,
    }


def _strict_J(D, x: int, y: int) -> set[int]:
    if x == y:
        return {x}
    return {
        u
        for u in range(len(D))
        if u in (x, y) or D[x][y] > max(D[x][u], D[u][y])
    }


def _argmax_by_distance(D, center: int, labels: set[int]) -> list[int]:
    maximum = max(D[center][u] for u in labels)
    return sorted(u for u in labels if D[center][u] == maximum)


def _sort_by_distance(D, center: int, labels: set[int]) -> tuple[int, ...]:
    return tuple(sorted(labels, key=lambda u: (D[center][u], u)))


def _reverse_sort_by_distance(D, center: int, labels: set[int]) -> tuple[int, ...]:
    return tuple(sorted(labels, key=lambda u: (-D[center][u], u)))


def _segment_options(D, center: int, labels: set[int], first_arc: set[int]) -> list[tuple[int, ...]]:
    labels = set(labels)
    first_arc = labels & set(first_arc)
    second_arc = labels - first_arc
    options = {
        _reverse_sort_by_distance(D, center, second_arc) + _sort_by_distance(D, center, first_arc),
        _reverse_sort_by_distance(D, center, first_arc) + _sort_by_distance(D, center, second_arc),
    }
    return sorted(order for order in options if len(order) == len(labels))
