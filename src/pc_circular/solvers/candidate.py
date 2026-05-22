"""Initial candidate API for the research loop.

The current implementation is deliberately conservative:

* for n <= 8 it calls the exact brute-force baseline;
* for a proved universal-order sub-case it returns a represented witness,
  because every circular order is circular Robinson;
* for larger instances it tries a small deterministic set of represented
  orders; a found witness proves ``exists=True``, but failure remains
  ``complete=False``.
* for star/unconstrained instances it also tries a structural minimum-distance
  cycle witness and accepts it only after direct cR verification.

This is not a solution to the general problem.  Future goals should replace
the large-n placeholder with a proved algorithm or a clearly scoped sub-case.
"""

from __future__ import annotations

from itertools import islice
from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels, sample_frontier
from pc_circular.predicates import (
    has_at_most_one_bad_witness_per_pair,
    is_precircular_order_cR,
    validate_dissimilarity,
)
from pc_circular.solvers import brute_force


EXACT_BRUTE_FORCE_LIMIT = 8


def _large_n_budget(n: int) -> int:
    if n <= 20:
        return 64
    if n <= 40:
        return 16
    return 4


def _fallback_orders(n: int) -> list[tuple[int, ...]]:
    natural = tuple(range(n))
    reversed_order = tuple(reversed(natural))
    even_odd = tuple(list(range(0, n, 2)) + list(range(1, n, 2)))
    return list(dict.fromkeys([natural, reversed_order, even_odd]))


def _is_leaf_star(pc_tree: Optional[PCNode], n: int) -> bool:
    if pc_tree is None:
        return False
    return (
        pc_tree.kind == "P"
        and all(child.kind == "leaf" for child in pc_tree.children)
        and set(labels(pc_tree)) == set(range(n))
    )


def _validate_order_shape(order: Sequence[int], n: int) -> tuple[int, ...]:
    seq = tuple(order)
    if len(seq) != n or set(seq) != set(range(n)):
        raise ValueError("order must be a permutation of 0..n-1")
    return seq


def _minimum_distance_cycle_order(D, n: int) -> tuple[int, ...] | None:
    if n < 4:
        return None

    positive_distances = [D[i][j] for i in range(n) for j in range(i + 1, n) if D[i][j] > 0]
    if not positive_distances:
        return None
    minimum = min(positive_distances)
    neighbors = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if D[i][j] == minimum:
                neighbors[i].append(j)
                neighbors[j].append(i)
    if any(len(values) != 2 for values in neighbors.values()):
        return None

    start = 0
    previous = None
    current = start
    order = []
    for _ in range(n):
        order.append(current)
        choices = sorted(neighbors[current])
        next_candidates = [value for value in choices if value != previous]
        if not next_candidates:
            return None
        nxt = next_candidates[0]
        previous, current = current, nxt
    if current != start or len(set(order)) != n:
        return None
    return tuple(order)


def _minimum_cycle_witness_result(D, n: int, pc_tree: Optional[PCNode]):
    if pc_tree is not None and not _is_leaf_star(pc_tree, n):
        return None
    order = _minimum_distance_cycle_order(D, n)
    if order is None or not is_precircular_order_cR(D, order):
        return None
    return {
        "exists": True,
        "order": list(order),
        "complete": True,
        "solver": "candidate_minimum_distance_cycle_witness",
        "note": "minimum-distance graph is a simple cycle and the reconstructed order is a verified witness",
    }


def _universal_order_result(n: int, quasi_orders, pc_tree: Optional[PCNode]):
    if quasi_orders is not None:
        iterator = iter(quasi_orders)
        try:
            order = _validate_order_shape(next(iterator), n)
        except StopIteration:
            return {
                "exists": False,
                "order": None,
                "complete": True,
                "solver": "candidate_universal_bad_witness_bound_all_orders",
                "note": "all orders would be circular Robinson, but the provided order family is empty",
            }
    elif pc_tree is not None:
        order = _validate_order_shape(sample_frontier(pc_tree), n)
    else:
        order = tuple(range(n))

    return {
        "exists": True,
        "order": list(order),
        "complete": True,
        "solver": "candidate_universal_bad_witness_bound_all_orders",
        "note": "all represented orders are circular Robinson by the bad-witness count bound",
    }


def _sample_orders(
    n: int,
    quasi_orders: Optional[Iterable[Sequence[int]]],
    pc_tree: Optional[PCNode],
) -> list[tuple[int, ...]]:
    budget = _large_n_budget(n)
    if quasi_orders is not None:
        return [tuple(order) for order in islice(quasi_orders, budget)]
    if pc_tree is not None:
        return enumerate_frontiers(pc_tree, canonical=True, limit=budget)
    return _fallback_orders(n)[:budget]


def solve(D, quasi_orders=None, pc_tree=None):
    n = validate_dissimilarity(D)
    if n <= EXACT_BRUTE_FORCE_LIMIT:
        result = brute_force.solve(D, quasi_orders=quasi_orders, pc_tree=pc_tree)
        result["solver"] = "candidate_exact_bruteforce_n_le_8"
        return result

    if has_at_most_one_bad_witness_per_pair(D):
        return _universal_order_result(n, quasi_orders, pc_tree)

    if quasi_orders is None:
        cycle_result = _minimum_cycle_witness_result(D, n, pc_tree)
        if cycle_result is not None:
            return cycle_result

    tried = 0
    for order in _sample_orders(n, quasi_orders, pc_tree):
        tried += 1
        if is_precircular_order_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "solver": "candidate_validated_sampled_witness",
                "tried_orders": tried,
                "note": "sampled represented order is a valid circular-Robinson witness",
            }

    return {
        "exists": False,
        "order": None,
        "complete": False,
        "solver": "candidate_large_n_placeholder",
        "tried_orders": tried,
        "note": "no sampled witness found; this is not a proof of non-existence",
    }
