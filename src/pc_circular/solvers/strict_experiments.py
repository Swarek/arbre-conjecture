"""Experimental helpers for strict circular Robinson sub-cases.

These functions enumerate fixed orders on small instances.  They are research
instrumentation for Piste F, not a general solver and not used by candidate.py.
"""

from __future__ import annotations

from pc_circular.pc_tree import PCNode, enumerate_frontiers, represents_order
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
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
