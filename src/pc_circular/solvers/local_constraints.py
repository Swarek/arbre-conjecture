"""Scratch space for local P/C-node constraint experiments."""

from __future__ import annotations

from pc_circular.predicates import farthest_sets, validate_dissimilarity


def summarize_farthest_degrees(D):
    """Return small diagnostics useful before adding real local constraints."""

    n = validate_dissimilarity(D)
    farthest = farthest_sets(D)
    return {
        "n": n,
        "min_farthest_degree": min((len(v) for v in farthest.values()), default=0),
        "max_farthest_degree": max((len(v) for v in farthest.values()), default=0),
    }
