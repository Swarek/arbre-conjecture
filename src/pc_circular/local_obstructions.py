"""Local-to-global obstruction diagnostics for cR order existence."""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from .oracle import exact_oracle_all_orders
from .predicates import validate_dissimilarity


def induced_submatrix(D: Sequence[Sequence[int]], subset: Sequence[int]) -> list[list[int]]:
    """Return the induced dissimilarity matrix on ``subset`` in subset order."""

    return [[D[i][j] for j in subset] for i in subset]


def local_obstruction_profile(
    D: Sequence[Sequence[int]],
    *,
    max_subset_size: int | None = None,
    max_global_n: int = 8,
) -> dict:
    """Find the smallest induced subset with no cR order, if visible.

    If a negative induced subset is found, the full instance is also negative by
    hereditary restriction.  If none is found up to ``max_subset_size`` and the
    whole instance is small enough, the profile also computes the exact global
    oracle.
    """

    n = validate_dissimilarity(D)
    max_k = n if max_subset_size is None else min(n, max_subset_size)
    checked_by_size: dict[str, int] = {}

    for k in range(4, max_k + 1):
        checked = 0
        for subset in combinations(range(n), k):
            checked += 1
            submatrix = induced_submatrix(D, subset)
            if not exact_oracle_all_orders(submatrix)["exists"]:
                checked_by_size[str(k)] = checked
                return {
                    "n": n,
                    "max_subset_size": max_k,
                    "complete": True,
                    "global_exists": False,
                    "global_reason": "negative_induced_subset",
                    "min_negative_subset_size": k,
                    "negative_subset": list(subset),
                    "all_subsets_positive_up_to": k - 1,
                    "checked_by_size": checked_by_size,
                    "global_checked_exactly": False,
                }
        checked_by_size[str(k)] = checked

    if max_k == n:
        return {
            "n": n,
            "max_subset_size": max_k,
            "complete": True,
            "global_exists": True,
            "global_reason": "all_orders_checked_via_full_subset",
            "min_negative_subset_size": None,
            "negative_subset": None,
            "all_subsets_positive_up_to": n,
            "checked_by_size": checked_by_size,
            "global_checked_exactly": True,
        }

    if n <= max_global_n:
        global_result = exact_oracle_all_orders(D)
        return {
            "n": n,
            "max_subset_size": max_k,
            "complete": True,
            "global_exists": global_result["exists"],
            "global_reason": "exact_global_oracle",
            "min_negative_subset_size": None,
            "negative_subset": None,
            "all_subsets_positive_up_to": max_k,
            "checked_by_size": checked_by_size,
            "global_checked_exactly": True,
        }

    return {
        "n": n,
        "max_subset_size": max_k,
        "complete": False,
        "global_exists": None,
        "global_reason": "not_checked_beyond_subset_cap",
        "min_negative_subset_size": None,
        "negative_subset": None,
        "all_subsets_positive_up_to": max_k,
        "checked_by_size": checked_by_size,
        "global_checked_exactly": False,
    }
