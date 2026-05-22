"""Scratch space for local P/C-node constraint experiments."""

from __future__ import annotations

from pc_circular.predicates import (
    farthest_sets,
    find_farthest_crossing_violation,
    find_precircular_cR_violation,
    validate_dissimilarity,
)
from pc_circular.pc_tree import PCNode, labels


def summarize_farthest_degrees(D):
    """Return small diagnostics useful before adding real local constraints."""

    n = validate_dissimilarity(D)
    farthest = farthest_sets(D)
    return {
        "n": n,
        "min_farthest_degree": min((len(v) for v in farthest.values()), default=0),
        "max_farthest_degree": max((len(v) for v in farthest.values()), default=0),
    }


def classify_order_obstructions(D, order):
    """Return side-by-side cR and farthest diagnostics for one order."""

    cr_violation = find_precircular_cR_violation(D, order)
    farthest_violation = find_farthest_crossing_violation(D, order)
    return {
        "is_circular_robinson": cr_violation is None,
        "passes_farthest_crossing": farthest_violation is None,
        "cr_violation": cr_violation,
        "farthest_violation": farthest_violation,
    }


def iter_internal_node_child_labels(node: PCNode, path=()):
    """Yield internal nodes with child label sets for obstruction projection."""

    if node.kind == "leaf":
        return
    child_label_sets = tuple(frozenset(labels(child)) for child in node.children)
    yield {
        "path": tuple(path),
        "kind": node.kind,
        "child_label_sets": child_label_sets,
    }
    for index, child in enumerate(node.children):
        yield from iter_internal_node_child_labels(child, (*path, index))


def _obstruction_points(obstruction):
    if obstruction is None:
        return ()
    if "quadruple" in obstruction:
        return tuple(obstruction["quadruple"])
    if "chords" in obstruction:
        return tuple(point for chord in obstruction["chords"] for point in chord)
    raise ValueError("unknown obstruction shape")


def project_points_to_node(points, child_label_sets):
    """Project obstruction labels to child indices for one internal node."""

    projected = []
    for point in points:
        for index, child_labels in enumerate(child_label_sets):
            if point in child_labels:
                projected.append((point, index))
                break
    support = sorted({index for _, index in projected})
    return {
        "projected": tuple(projected),
        "support": tuple(support),
        "support_size": len(support),
        "contained_points": tuple(point for point, _ in projected),
    }


def measure_obstruction_support(D, T: PCNode, order):
    """Measure where first cR/farthest obstructions appear in a PC-tree.

    This is diagnostic instrumentation for Piste A.  It does not decide the
    existence problem; it shows whether a witnessed obstruction is visible at
    local P/C nodes and with what branch support size.
    """

    validate_dissimilarity(D)
    diagnostics = classify_order_obstructions(D, order)
    result = {
        "order": tuple(order),
        "is_circular_robinson": diagnostics["is_circular_robinson"],
        "passes_farthest_crossing": diagnostics["passes_farthest_crossing"],
        "obstructions": [],
    }
    for obstruction_type, obstruction in (
        ("cr", diagnostics["cr_violation"]),
        ("farthest", diagnostics["farthest_violation"]),
    ):
        if obstruction is None:
            continue
        points = _obstruction_points(obstruction)
        node_projections = []
        for node_info in iter_internal_node_child_labels(T):
            projection = project_points_to_node(points, node_info["child_label_sets"])
            if len(projection["contained_points"]) < 2:
                continue
            node_projections.append(
                {
                    "path": node_info["path"],
                    "kind": node_info["kind"],
                    **projection,
                }
            )
        result["obstructions"].append(
            {
                "type": obstruction_type,
                "points": points,
                "witness": obstruction,
                "node_projections": node_projections,
            }
        )
    return result
