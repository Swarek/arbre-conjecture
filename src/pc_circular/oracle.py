"""Exact oracles for small PC-tree circular Robinson instances."""

from __future__ import annotations

from typing import Optional

from .pc_tree import PCNode, enumerate_frontiers
from .predicates import all_circular_orders, is_precircular_order_cR, validate_dissimilarity


def exact_oracle_all_orders(D):
    """Search all circular orders exactly."""

    n = validate_dissimilarity(D)
    for order in all_circular_orders(n):
        if is_precircular_order_cR(D, order):
            return {"exists": True, "order": list(order), "complete": True}
    return {"exists": False, "order": None, "complete": True}


def exact_oracle_pc_tree(D, T: Optional[PCNode]):
    """Search all frontiers represented by ``T`` exactly.

    If ``T`` is ``None``, all circular orders are considered.
    """

    n = validate_dissimilarity(D)
    orders = all_circular_orders(n) if T is None else enumerate_frontiers(T, canonical=True)
    for order in orders:
        if is_precircular_order_cR(D, order):
            return {"exists": True, "order": list(order), "complete": True}
    return {"exists": False, "order": None, "complete": True}
