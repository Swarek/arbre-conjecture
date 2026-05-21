"""Initial candidate API for the research loop.

The current implementation is deliberately conservative:

* for n <= 8 it calls the exact brute-force baseline;
* for larger instances it tries a small deterministic set of represented
  orders and returns ``complete=False``.

This is not a solution to the general problem.  Future goals should replace
the large-n placeholder with a proved algorithm or a clearly scoped sub-case.
"""

from __future__ import annotations

from itertools import islice
from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers
from pc_circular.predicates import is_precircular_order_cR, validate_dissimilarity
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

    tried = 0
    for order in _sample_orders(n, quasi_orders, pc_tree):
        tried += 1
        if is_precircular_order_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": False,
                "solver": "candidate_large_n_placeholder",
                "tried_orders": tried,
                "note": "witness found by incomplete deterministic sampling",
            }

    return {
        "exists": False,
        "order": None,
        "complete": False,
        "solver": "candidate_large_n_placeholder",
        "tried_orders": tried,
        "note": "no sampled witness found; this is not a proof of non-existence",
    }
