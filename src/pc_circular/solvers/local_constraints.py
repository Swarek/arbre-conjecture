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


def _is_circular_interval(indices, degree: int) -> bool:
    selected = set(indices)
    if len(selected) <= 1 or len(selected) == degree:
        return True
    transitions = 0
    for idx in range(degree):
        current = idx in selected
        nxt = ((idx + 1) % degree) in selected
        if current != nxt:
            transitions += 1
    return transitions <= 2


def _is_circular_interval_in_order(branch_order, indices) -> bool:
    position = {branch: idx for idx, branch in enumerate(branch_order)}
    translated = [position[index] for index in indices]
    return _is_circular_interval(translated, len(branch_order))


def _circular_branch_orders(degree: int):
    if degree <= 0:
        yield ()
        return
    if degree == 1:
        yield (0,)
        return

    from itertools import permutations

    anchor = 0
    rest = tuple(range(1, degree))
    for perm in permutations(rest):
        order = (anchor, *perm)
        reversed_order = (anchor, *reversed(perm))
        if order <= reversed_order:
            yield order


def _find_circular_ones_order(projected_sets, degree: int):
    for branch_order in _circular_branch_orders(degree):
        if all(_is_circular_interval_in_order(branch_order, projected) for projected in projected_sets):
            return branch_order
    return None


def _laminar_violations(projected_sets):
    violations = []
    sets = [frozenset(projected) for projected in projected_sets]
    for left_index, left in enumerate(sets):
        for right_index in range(left_index + 1, len(sets)):
            right = sets[right_index]
            if not left or not right:
                continue
            if left <= right or right <= left or left.isdisjoint(right):
                continue
            violations.append((tuple(sorted(left)), tuple(sorted(right))))
    return tuple(violations)


def project_farthest_sets_to_pc_nodes(D, T: PCNode, *, circular_ones_degree_limit: int = 8):
    """Project every farthest set onto the branches of every PC-tree node.

    This is a Piste A/D diagnostic.  It records local interval, laminarity and
    circular-ones signals for the branch sets
    ``I_x(v) = {i : branch_i intersects F_x}``.  A violation here is not a
    decision procedure for existence in the PC-tree.
    """

    n = validate_dissimilarity(D)
    tree_labels = set(labels(T))
    if tree_labels != set(range(n)):
        raise ValueError("PC-tree labels must be exactly 0..n-1")

    farthest = farthest_sets(D)
    nodes = []
    for node_info in iter_internal_node_child_labels(T):
        child_label_sets = node_info["child_label_sets"]
        degree = len(child_label_sets)
        child_labels_sorted = tuple(tuple(sorted(child_labels)) for child_labels in child_label_sets)
        projected_by_point = []
        size_histogram: dict[int, int] = {}
        unique_projected_sets: set[tuple[int, ...]] = set()
        proper_projected_sets: set[tuple[int, ...]] = set()
        interval_violations = []

        for point in range(n):
            projected = tuple(
                index
                for index, child_labels in enumerate(child_label_sets)
                if child_labels & farthest[point]
            )
            size_histogram[len(projected)] = size_histogram.get(len(projected), 0) + 1
            unique_projected_sets.add(projected)
            if 1 < len(projected) < degree:
                proper_projected_sets.add(projected)
            is_interval = _is_circular_interval(projected, degree)
            if not is_interval:
                interval_violations.append({"point": point, "projection": projected})
            projected_by_point.append(
                {
                    "point": point,
                    "farthest": tuple(sorted(farthest[point])),
                    "projection": projected,
                    "projection_size": len(projected),
                    "is_declared_order_interval": is_interval,
                }
            )

        sorted_proper = tuple(sorted(proper_projected_sets))
        laminar = _laminar_violations(sorted_proper)
        if degree <= circular_ones_degree_limit:
            circular_ones_witness_order = _find_circular_ones_order(tuple(sorted(unique_projected_sets)), degree)
            circular_ones_compatible = circular_ones_witness_order is not None
            circular_ones_status = "compatible" if circular_ones_compatible else "incompatible"
        else:
            circular_ones_witness_order = None
            circular_ones_compatible = None
            circular_ones_status = "unsupported_degree"

        nodes.append(
            {
                "path": node_info["path"],
                "kind": node_info["kind"],
                "degree": degree,
                "label_count": sum(len(child_labels) for child_labels in child_label_sets),
                "branch_sizes": tuple(len(child_labels) for child_labels in child_label_sets),
                "child_label_sets": child_labels_sorted,
                "size_histogram": dict(sorted(size_histogram.items())),
                "projected_sets_by_point": tuple(projected_by_point),
                "unique_projected_sets": tuple(sorted(unique_projected_sets)),
                "proper_nontrivial_projected_sets": sorted_proper,
                "proper_nontrivial_count": len(sorted_proper),
                "laminar_violation_count": len(laminar),
                "laminar_violations": laminar[:10],
                "declared_order_interval_violation_count": len(interval_violations),
                "declared_order_interval_violations": tuple(interval_violations[:10]),
                "circular_ones_status": circular_ones_status,
                "circular_ones_compatible": circular_ones_compatible,
                "circular_ones_witness_order": circular_ones_witness_order,
            }
        )
    return {
        "n": n,
        "node_count": len(nodes),
        "circular_ones_degree_limit": circular_ones_degree_limit,
        "nodes": tuple(nodes),
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
