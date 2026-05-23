"""Experimental helpers for strict circular Robinson sub-cases.

These functions enumerate fixed orders on small instances.  They are research
instrumentation for Piste F, not a general solver and not used by candidate.py.
"""

from __future__ import annotations

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels, represents_order
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    farthest_sets,
    is_arc,
    is_precircular_order_cR,
    is_quasi_circular_order,
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


def strict_ball_circular_ones_report(
    D,
    pc_tree: PCNode | None = None,
    *,
    max_n: int = 8,
    frontier_limit: int | None = None,
) -> dict:
    """Enumerate small orders and compare ball-arc constraints to predicates.

    This is a bounded Piste D diagnostic.  It tests the circular-ones view of
    quasi-circularity by requiring every proper metric ball to be an arc in the
    order, then compares that count to the direct quasi/cR strict predicates.
    """

    n = validate_dissimilarity(D)
    balls = _proper_metric_balls(D)
    modules = _ball_membership_modules(n, balls)
    base_report = {
        "implemented": True,
        "method": "bounded_strict_ball_circular_ones_frontier_report",
        "n": n,
        "max_n": max_n,
        "pc_tree_provided": pc_tree is not None,
        "frontier_limit": frontier_limit,
        "ball_count": len(balls),
        "module_count": len(modules),
        "modules": modules,
    }
    if n > max_n:
        return {
            **base_report,
            "complete": False,
            "incomplete_reasons": ["n exceeds max_n"],
            "reason": "n exceeds strict_ball_circular_ones_report max_n",
            "order_source": None,
            "counts": None,
            "exists": {"ball_arc": None, "quasi": None, "strict_circular": None},
        }

    if pc_tree is None:
        order_source = "all_circular_orders"
        orders = list(all_circular_orders(n))
    else:
        if set(labels(pc_tree)) != set(range(n)):
            raise ValueError("pc_tree labels must be exactly 0..n-1")
        order_source = "pc_tree_frontiers"
        orders = enumerate_frontiers(pc_tree, canonical=True, limit=frontier_limit)

    ball_arc_orders = []
    quasi_orders = []
    strict_quasi_orders = []
    precircular_orders = []
    strict_precircular_orders = []
    strict_circular_orders = []
    first_ball_quasi_mismatch = None
    representation_mismatch_count = 0
    first_representation_mismatch = None

    for order in orders:
        canonical = canonical_circular_order(order)
        if pc_tree is not None and not represents_order(pc_tree, canonical):
            representation_mismatch_count += 1
            if first_representation_mismatch is None:
                first_representation_mismatch = canonical
        ball_arc = _all_balls_are_arcs(canonical, balls)
        quasi = is_quasi_circular_order(D, canonical)
        if ball_arc:
            ball_arc_orders.append(canonical)
        if quasi:
            quasi_orders.append(canonical)
        if ball_arc != quasi and first_ball_quasi_mismatch is None:
            first_ball_quasi_mismatch = {
                "order": canonical,
                "ball_arc": ball_arc,
                "quasi": quasi,
                "first_bad_ball": _first_non_arc_ball(canonical, balls),
            }
        if is_strict_quasi_circular_order(D, canonical):
            strict_quasi_orders.append(canonical)
        if is_precircular_order_cR(D, canonical):
            precircular_orders.append(canonical)
        if is_strict_precircular_order_cR(D, canonical):
            strict_precircular_orders.append(canonical)
        if is_strict_circular_robinson_order(D, canonical):
            if pc_tree is None or represents_order(pc_tree, canonical):
                strict_circular_orders.append(canonical)

    incomplete_reasons = []
    if frontier_limit is not None and len(orders) >= frontier_limit:
        incomplete_reasons.append("frontier_limit reached")
    if representation_mismatch_count:
        incomplete_reasons.append("enumerated frontier failed represents_order sanity check")
    complete = not incomplete_reasons
    counts = {
        "orders_seen": len(orders),
        "ball_arc": len(ball_arc_orders),
        "quasi": len(quasi_orders),
        "strict_quasi": len(strict_quasi_orders),
        "precircular": len(precircular_orders),
        "strict_precircular": len(strict_precircular_orders),
        "strict_circular": len(strict_circular_orders),
        "ball_quasi_mismatch": 1 if first_ball_quasi_mismatch is not None else 0,
        "representation_mismatch": representation_mismatch_count,
    }
    exists = {
        "ball_arc": True if ball_arc_orders else (False if complete else None),
        "quasi": True if quasi_orders else (False if complete else None),
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
        "ball_arc_count": len(ball_arc_orders),
        "quasi_count": len(quasi_orders),
        "strict_quasi_count": len(strict_quasi_orders),
        "precircular_count": len(precircular_orders),
        "strict_precircular_count": len(strict_precircular_orders),
        "strict_circular_count": len(strict_circular_orders),
        "ball_arc_witness": ball_arc_orders[0] if ball_arc_orders else None,
        "quasi_witness": quasi_orders[0] if quasi_orders else None,
        "strict_quasi_witness": strict_quasi_orders[0] if strict_quasi_orders else None,
        "strict_circular_witness": strict_circular_orders[0] if strict_circular_orders else None,
        "first_ball_quasi_mismatch": first_ball_quasi_mismatch,
        "first_representation_mismatch": first_representation_mismatch,
        "ball_arc_orders": ball_arc_orders,
        "quasi_orders": quasi_orders,
        "strict_quasi_orders": strict_quasi_orders,
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


def _proper_metric_balls(D) -> list[tuple[int, tuple[int, ...]]]:
    n = len(D)
    balls: set[tuple[int, tuple[int, ...]]] = set()
    for center in range(n):
        for radius in sorted(set(D[center])):
            ball = tuple(point for point in range(n) if D[center][point] <= radius)
            if 1 < len(ball) < n:
                balls.add((center, ball))
    return sorted(balls)


def _all_balls_are_arcs(order: tuple[int, ...], balls: list[tuple[int, tuple[int, ...]]]) -> bool:
    return all(is_arc(order, ball) for _, ball in balls)


def _first_non_arc_ball(order: tuple[int, ...], balls: list[tuple[int, tuple[int, ...]]]) -> dict | None:
    for center, ball in balls:
        if not is_arc(order, ball):
            return {"center": center, "ball": ball}
    return None


def _ball_membership_modules(n: int, balls: list[tuple[int, tuple[int, ...]]]) -> list[dict]:
    buckets: dict[tuple[bool, ...], list[int]] = {}
    ball_sets = [set(ball) for _, ball in balls]
    for point in range(n):
        signature = tuple(point in ball for ball in ball_sets)
        buckets.setdefault(signature, []).append(point)
    modules = []
    for signature, labels in sorted(buckets.items(), key=lambda item: (item[1][0], item[1])):
        modules.append(
            {
                "labels": tuple(labels),
                "size": len(labels),
                "ball_ids": tuple(idx for idx, present in enumerate(signature) if present),
                "signature": signature,
                "signature_weight": sum(signature),
            }
        )
    return modules
