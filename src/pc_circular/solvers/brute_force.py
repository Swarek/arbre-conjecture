"""Exact brute-force baseline.

This solver is only a small-instance oracle/baseline.  It enumerates orders and
therefore is not a proposed general solution to the PC-tree existence problem.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR, validate_dissimilarity


def _orders(D, quasi_orders: Optional[Iterable[Sequence[int]]], pc_tree: Optional[PCNode]):
    n = validate_dissimilarity(D)
    if quasi_orders is not None:
        return (tuple(order) for order in quasi_orders)
    if pc_tree is not None:
        return iter(enumerate_frontiers(pc_tree, canonical=True))
    return all_circular_orders(n)


def solve(D, quasi_orders=None, pc_tree=None):
    for order in _orders(D, quasi_orders, pc_tree):
        if is_precircular_order_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "solver": "brute_force",
            }
    return {
        "exists": False,
        "order": None,
        "complete": True,
        "solver": "brute_force",
    }
