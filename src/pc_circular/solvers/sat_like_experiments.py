"""Scratch space for SAT/CSP-style encodings of cyclic constraints.

Nothing in this module is a proved general solver.  The functions below are
frontier-enumeration experiments that treat Proposition 4.5 obstructions as
nogoods on fixed orders, then compare the resulting filter with the exact cR
predicate.  This gives Piste C falsifiable data before a real variable-level
PC-tree encoding is attempted.
"""

from __future__ import annotations

from itertools import islice
from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    find_farthest_prop_4_5_obstruction,
    is_precircular_order_cR,
    is_quasi_circular_order,
    validate_dissimilarity,
)


Order = Sequence[int]


def not_implemented_status() -> dict:
    return {
        "implemented": False,
        "reason": "No sound variable-level constraint encoding has been proved sufficient yet",
    }


def _materialize_orders(
    n: int,
    *,
    quasi_orders: Optional[Iterable[Order]],
    pc_tree: Optional[PCNode],
    limit: Optional[int],
) -> tuple[list[tuple[int, ...]], bool]:
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if quasi_orders is not None and pc_tree is not None:
        raise ValueError("provide quasi_orders or pc_tree, not both")

    if pc_tree is not None:
        raw_orders = enumerate_frontiers(
            pc_tree,
            canonical=True,
            limit=None if limit is None else limit + 1,
        )
    elif quasi_orders is not None:
        raw_orders = list(islice(quasi_orders, None if limit is None else limit + 1))
    else:
        raw_orders = list(islice(all_circular_orders(n), None if limit is None else limit + 1))

    seen: set[tuple[int, ...]] = set()
    orders: list[tuple[int, ...]] = []
    truncated = False
    for raw_order in raw_orders:
        order = canonical_circular_order(raw_order)
        if len(order) != n or set(order) != set(range(n)):
            raise ValueError("orders must be permutations of 0..n-1")
        if order in seen:
            continue
        if limit is not None and len(orders) >= limit:
            truncated = True
            break
        seen.add(order)
        orders.append(order)

    return orders, truncated


def prop45_nogood_frontier_report(
    D,
    *,
    quasi_orders: Optional[Iterable[Order]] = None,
    pc_tree: Optional[PCNode] = None,
    limit: Optional[int] = None,
    require_quasi: bool = True,
) -> dict:
    """Compare the Prop. 4.5 fixed-order filter with exact cR on frontiers.

    The report is an experimental CSP scaffold: each Prop. 4.5 obstruction is
    treated as a nogood for the currently enumerated frontier.  It is still an
    enumeration-based diagnostic, not a compact PC-tree decision procedure.
    """

    n = validate_dissimilarity(D)
    orders, truncated = _materialize_orders(
        n,
        quasi_orders=quasi_orders,
        pc_tree=pc_tree,
        limit=limit,
    )

    counts = {
        "frontiers_seen": 0,
        "skipped_non_quasi": 0,
        "checked_orders": 0,
        "prop45_pass": 0,
        "prop45_fail": 0,
        "exact_cr": 0,
        "exact_non_cr": 0,
        "false_positive_prop45": 0,
        "false_negative_prop45": 0,
    }
    report = {
        "implemented": True,
        "method": "enumerated_frontier_prop45_nogood_filter",
        "complete": not truncated,
        "limit": limit,
        "require_quasi": require_quasi,
        "counts": counts,
        "witness_order": None,
        "first_rejected": None,
        "first_false_positive": None,
        "first_false_negative": None,
    }

    for order in orders:
        counts["frontiers_seen"] += 1
        if require_quasi and not is_quasi_circular_order(D, order):
            counts["skipped_non_quasi"] += 1
            continue

        counts["checked_orders"] += 1
        obstruction = find_farthest_prop_4_5_obstruction(D, order)
        prop45_passes = obstruction is None
        exact_cr = is_precircular_order_cR(D, order)

        if prop45_passes:
            counts["prop45_pass"] += 1
            if report["witness_order"] is None:
                report["witness_order"] = list(order)
        else:
            counts["prop45_fail"] += 1
            if report["first_rejected"] is None:
                report["first_rejected"] = {
                    "order": list(order),
                    "obstruction": obstruction,
                }

        if exact_cr:
            counts["exact_cr"] += 1
        else:
            counts["exact_non_cr"] += 1

        if prop45_passes and not exact_cr:
            counts["false_positive_prop45"] += 1
            if report["first_false_positive"] is None:
                report["first_false_positive"] = list(order)
        elif not prop45_passes and exact_cr:
            counts["false_negative_prop45"] += 1
            if report["first_false_negative"] is None:
                report["first_false_negative"] = {
                    "order": list(order),
                    "obstruction": obstruction,
                }

    report["prop45_exists"] = counts["prop45_pass"] > 0
    report["exact_cr_exists"] = counts["exact_cr"] > 0
    report["has_disagreement"] = bool(
        counts["false_positive_prop45"] or counts["false_negative_prop45"]
    )
    return report


def prop45_nogood_frontier_search(
    D,
    *,
    quasi_orders: Optional[Iterable[Order]] = None,
    pc_tree: Optional[PCNode] = None,
    limit: Optional[int] = None,
    require_quasi: bool = True,
) -> dict:
    """Return the first frontier accepted by the Prop. 4.5 nogood filter."""

    report = prop45_nogood_frontier_report(
        D,
        quasi_orders=quasi_orders,
        pc_tree=pc_tree,
        limit=limit,
        require_quasi=require_quasi,
    )
    return {
        "exists": report["prop45_exists"],
        "order": report["witness_order"],
        "complete": report["complete"],
        "solver": "prop45_nogood_frontier_experiment",
        "note": "experimental fixed-order nogood filter; not a proved PC-tree solver",
        "report": report,
    }
