"""Scratch space for local P/C-node constraint experiments."""

from __future__ import annotations

from itertools import permutations, product

from pc_circular.predicates import (
    farthest_sets,
    find_farthest_crossing_violation,
    find_precircular_cR_violation,
    is_precircular_order_cR,
    passes_bad_side_precircular_cR,
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


def _factorial(value: int) -> int:
    result = 1
    for factor in range(2, value + 1):
        result *= factor
    return result


def _bipartite_components(vertices, neighbors):
    color: dict[int, int] = {}
    components = []
    for start in vertices:
        if start in color:
            continue
        color[start] = 0
        stack = [start]
        component = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in neighbors[current]:
                if neighbor not in color:
                    color[neighbor] = 1 - color[current]
                    stack.append(neighbor)
                elif color[neighbor] == color[current]:
                    return None
        left = tuple(sorted(vertex for vertex in component if color[vertex] == 0))
        right = tuple(sorted(vertex for vertex in component if color[vertex] == 1))
        components.append((left, right))
    return tuple(components)


def _has_strong_ordering(A_order, B_order, high_edges) -> bool:
    for left_index, a_left in enumerate(A_order):
        for a_right in A_order[left_index + 1 :]:
            for lower_index, b_left in enumerate(B_order):
                for b_right in B_order[lower_index + 1 :]:
                    crossing_edges = (a_left, b_right) in high_edges and (a_right, b_left) in high_edges
                    straight_edges = (a_left, b_left) in high_edges and (a_right, b_right) in high_edges
                    if crossing_edges and not straight_edges:
                        return False
    return True


def _nested_neighborhood_order(vertices, neighbors):
    ordered = tuple(
        sorted(
            vertices,
            key=lambda vertex: (-len(neighbors[vertex]), tuple(sorted(neighbors[vertex])), vertex),
        )
    )
    neighbor_sets = {vertex: frozenset(neighbors[vertex]) for vertex in vertices}
    for left, right in zip(ordered, ordered[1:]):
        if not neighbor_sets[right] <= neighbor_sets[left]:
            return None
    return ordered


def _increasing_neighborhood_order(vertices, neighbors):
    return tuple(
        sorted(
            vertices,
            key=lambda vertex: (len(neighbors[vertex]), tuple(sorted(neighbors[vertex])), vertex),
        )
    )


def low_hub_ferrers_strong_ordering_report(D):
    """Detect a binary low-hub Ferrers/chain high graph and build a witness."""

    n = validate_dissimilarity(D)
    off_diagonal_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n)})
    if len(off_diagonal_values) <= 1:
        order = tuple(range(n))
        return {
            "method": "low_hub_ferrers_strong_ordering_report",
            "n": n,
            "status": "empty_high_graph",
            "strong_ordering_exists": True,
            "low_value": off_diagonal_values[0] if off_diagonal_values else 0,
            "high_value": None,
            "hub_labels": order,
            "high_graph_labels": (),
            "part_a": (),
            "part_b": (),
            "witness_order": order,
            "witness_order_is_cr": passes_bad_side_precircular_cR(D, order),
        }
    if len(off_diagonal_values) != 2:
        return {
            "method": "low_hub_ferrers_strong_ordering_report",
            "n": n,
            "status": "not_binary_two_level",
            "strong_ordering_exists": None,
            "witness_order": None,
            "witness_order_is_cr": None,
        }

    _low, high = off_diagonal_values
    neighbors = {
        i: tuple(j for j in range(n) if i != j and D[i][j] == high)
        for i in range(n)
    }
    hubs = tuple(i for i, values in neighbors.items() if not values)
    high_vertices = tuple(i for i, values in neighbors.items() if values)
    base = {
        "method": "low_hub_ferrers_strong_ordering_report",
        "n": n,
        "low_value": _low,
        "high_value": high,
        "hub_labels": hubs,
        "high_graph_labels": high_vertices,
        "witness_order": None,
        "witness_order_is_cr": None,
    }
    if not hubs:
        return {**base, "status": "no_low_hub", "strong_ordering_exists": None}
    if not high_vertices:
        order = tuple(hubs)
        return {
            **base,
            "status": "empty_high_graph",
            "strong_ordering_exists": True,
            "part_a": (),
            "part_b": (),
            "witness_order": order,
            "witness_order_is_cr": passes_bad_side_precircular_cR(D, order),
        }

    components = _bipartite_components(high_vertices, neighbors)
    if components is None:
        return {**base, "status": "non_bipartite_high_graph", "strong_ordering_exists": False}
    if len(components) != 1:
        return {
            **base,
            "status": "not_ferrers_high_graph",
            "strong_ordering_exists": None,
            "component_count": len(components),
        }

    left, right = components[0]
    for part_a_vertices, part_b_vertices in ((left, right), (right, left)):
        A_order = _nested_neighborhood_order(part_a_vertices, neighbors)
        if A_order is None:
            continue
        B_order = _increasing_neighborhood_order(part_b_vertices, neighbors)
        high_edges = {(a, b) for a in A_order for b in B_order if D[a][b] == high}
        if not _has_strong_ordering(A_order, B_order, high_edges):
            continue
        witness_order = tuple(hubs) + tuple(A_order) + tuple(B_order)
        return {
            **base,
            "status": "ferrers_strong_ordering_found",
            "strong_ordering_exists": True,
            "component_count": len(components),
            "part_a": tuple(A_order),
            "part_b": tuple(B_order),
            "witness_order": witness_order,
            "witness_order_is_cr": passes_bad_side_precircular_cR(D, witness_order),
        }

    return {
        **base,
        "status": "not_ferrers_high_graph",
        "strong_ordering_exists": None,
        "component_count": len(components),
    }


def low_hub_strong_ordering_report(D, *, max_permutation_pairs: int = 100_000):
    """Bounded diagnostic for the binary low-hub strong-ordering conjecture.

    This Piste E/F experiment does not decide the general PC-tree problem.
    ``candidate.py`` may use it only as a positive witness source after direct
    cR and PC-tree validation.  It tests whether the high-distance graph of a
    binary low-hub instance admits a strong ordering, and verifies the resulting
    witness order directly when one is found.
    """

    n = validate_dissimilarity(D)
    off_diagonal_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n)})
    if len(off_diagonal_values) <= 1:
        order = tuple(range(n))
        return {
            "method": "bounded_low_hub_strong_ordering_report",
            "n": n,
            "complete": True,
            "status": "empty_high_graph",
            "strong_ordering_exists": True,
            "low_value": off_diagonal_values[0] if off_diagonal_values else 0,
            "high_value": None,
            "hub_labels": order,
            "high_graph_labels": (),
            "max_permutation_pairs": max_permutation_pairs,
            "part_a": (),
            "part_b": (),
            "witness_order": order,
            "witness_order_is_cr": passes_bad_side_precircular_cR(D, order),
        }
    if len(off_diagonal_values) != 2:
        return {
            "method": "bounded_low_hub_strong_ordering_report",
            "n": n,
            "complete": True,
            "status": "not_binary_two_level",
            "strong_ordering_exists": None,
            "witness_order": None,
            "witness_order_is_cr": None,
        }

    _low, high = off_diagonal_values
    neighbors = {
        i: tuple(j for j in range(n) if i != j and D[i][j] == high)
        for i in range(n)
    }
    hubs = tuple(i for i, values in neighbors.items() if not values)
    high_vertices = tuple(i for i, values in neighbors.items() if values)
    base = {
        "method": "bounded_low_hub_strong_ordering_report",
        "n": n,
        "complete": True,
        "low_value": _low,
        "high_value": high,
        "hub_labels": hubs,
        "high_graph_labels": high_vertices,
        "max_permutation_pairs": max_permutation_pairs,
        "witness_order": None,
        "witness_order_is_cr": None,
    }
    if not hubs:
        return {**base, "status": "no_low_hub", "strong_ordering_exists": None}
    if not high_vertices:
        order = tuple(hubs)
        return {
            **base,
            "status": "empty_high_graph",
            "strong_ordering_exists": True,
            "part_a": (),
            "part_b": (),
            "witness_order": order,
            "witness_order_is_cr": passes_bad_side_precircular_cR(D, order),
        }

    components = _bipartite_components(high_vertices, neighbors)
    if components is None:
        return {**base, "status": "non_bipartite_high_graph", "strong_ordering_exists": False}

    partition_count = 2 ** len(components)
    checked_permutation_pairs = 0
    for flips in product((0, 1), repeat=len(components)):
        part_a = []
        part_b = []
        component_a_order = []
        component_b_order = []
        for flip, (left, right) in zip(flips, components):
            if flip:
                chosen_a = right
                chosen_b = left
            else:
                chosen_a = left
                chosen_b = right
            part_a.extend(chosen_a)
            part_b.extend(chosen_b)
            component_a_order.extend(chosen_a)
            component_b_order.extend(chosen_b)
        part_a = tuple(sorted(part_a))
        part_b = tuple(sorted(part_b))

        high_edges = {(a, b) for a in part_a for b in part_b if D[a][b] == high}
        priority_a_orders = tuple(dict.fromkeys((part_a, tuple(reversed(part_a)))))
        priority_b_orders = tuple(dict.fromkeys((part_b, tuple(reversed(part_b)))))
        component_pair = (tuple(component_a_order), tuple(component_b_order))
        reversed_component_pair = (tuple(reversed(component_a_order)), tuple(reversed(component_b_order)))
        priority_pairs = tuple(
            dict.fromkeys(
                (
                    component_pair,
                    reversed_component_pair,
                    *((A_order, B_order) for A_order in priority_a_orders for B_order in priority_b_orders),
                )
            )
        )
        seen_order_pairs = set()

        def order_pairs():
            for pair in priority_pairs:
                yield pair
            for A_order in permutations(part_a):
                for B_order in permutations(part_b):
                    yield A_order, B_order

        for A_order, B_order in order_pairs():
            if (A_order, B_order) in seen_order_pairs:
                continue
            seen_order_pairs.add((A_order, B_order))
            if checked_permutation_pairs >= max_permutation_pairs:
                return {
                    **base,
                    "complete": False,
                    "status": "unsupported_permutation_limit",
                    "strong_ordering_exists": None,
                    "component_count": len(components),
                    "partition_count": partition_count,
                    "checked_permutation_pairs": checked_permutation_pairs,
                }
            checked_permutation_pairs += 1
            if _has_strong_ordering(A_order, B_order, high_edges):
                witness_order = tuple(hubs) + tuple(A_order) + tuple(B_order)
                return {
                    **base,
                    "status": "strong_ordering_found",
                    "strong_ordering_exists": True,
                    "component_count": len(components),
                    "partition_count": partition_count,
                    "checked_permutation_pairs": checked_permutation_pairs,
                    "part_a": tuple(A_order),
                    "part_b": tuple(B_order),
                    "witness_order": witness_order,
                    "witness_order_is_cr": passes_bad_side_precircular_cR(D, witness_order),
                }

    return {
        **base,
        "status": "no_strong_ordering",
        "strong_ordering_exists": False,
        "component_count": len(components),
        "partition_count": partition_count,
        "checked_permutation_pairs": checked_permutation_pairs,
    }


def iter_low_hub_strong_ordering_witnesses(D, *, max_permutation_pairs: int = 100_000):
    """Yield bounded low-hub strong-ordering witnesses.

    This is a positive-witness iterator for ``candidate.py``.  It deliberately
    yields only orders that have already passed the strong-ordering test and the
    fixed-order cR verifier; callers must still check PC-tree representation.
    Hitting ``max_permutation_pairs`` is an incomplete search, not a rejection.
    """

    n = validate_dissimilarity(D)
    off_diagonal_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n)})
    if len(off_diagonal_values) <= 1:
        order = tuple(range(n))
        if passes_bad_side_precircular_cR(D, order):
            yield {
                "method": "bounded_low_hub_strong_ordering_witness_iterator",
                "n": n,
                "complete": True,
                "status": "empty_high_graph",
                "strong_ordering_exists": True,
                "low_value": off_diagonal_values[0] if off_diagonal_values else 0,
                "high_value": None,
                "hub_labels": order,
                "high_graph_labels": (),
                "max_permutation_pairs": max_permutation_pairs,
                "part_a": (),
                "part_b": (),
                "witness_order": order,
                "witness_order_is_cr": True,
                "checked_permutation_pairs": 0,
            }
        return
    if len(off_diagonal_values) != 2:
        return

    _low, high = off_diagonal_values
    neighbors = {
        i: tuple(j for j in range(n) if i != j and D[i][j] == high)
        for i in range(n)
    }
    hubs = tuple(i for i, values in neighbors.items() if not values)
    high_vertices = tuple(i for i, values in neighbors.items() if values)
    if not hubs:
        return
    if not high_vertices:
        order = tuple(hubs)
        if passes_bad_side_precircular_cR(D, order):
            yield {
                "method": "bounded_low_hub_strong_ordering_witness_iterator",
                "n": n,
                "complete": True,
                "status": "empty_high_graph",
                "strong_ordering_exists": True,
                "low_value": _low,
                "high_value": high,
                "hub_labels": hubs,
                "high_graph_labels": high_vertices,
                "max_permutation_pairs": max_permutation_pairs,
                "part_a": (),
                "part_b": (),
                "witness_order": order,
                "witness_order_is_cr": True,
                "checked_permutation_pairs": 0,
            }
        return

    components = _bipartite_components(high_vertices, neighbors)
    if components is None:
        return

    partition_count = 2 ** len(components)
    checked_permutation_pairs = 0
    seen_witness_orders = set()
    base = {
        "method": "bounded_low_hub_strong_ordering_witness_iterator",
        "n": n,
        "complete": True,
        "low_value": _low,
        "high_value": high,
        "hub_labels": hubs,
        "high_graph_labels": high_vertices,
        "max_permutation_pairs": max_permutation_pairs,
        "component_count": len(components),
        "partition_count": partition_count,
    }
    def flip_search(flips):
        part_a = []
        part_b = []
        component_a_order = []
        component_b_order = []
        for flip, (left, right) in zip(flips, components):
            if flip:
                chosen_a = right
                chosen_b = left
            else:
                chosen_a = left
                chosen_b = right
            part_a.extend(chosen_a)
            part_b.extend(chosen_b)
            component_a_order.extend(chosen_a)
            component_b_order.extend(chosen_b)
        part_a = tuple(sorted(part_a))
        part_b = tuple(sorted(part_b))

        high_edges = {(a, b) for a in part_a for b in part_b if D[a][b] == high}
        priority_a_orders = tuple(dict.fromkeys((part_a, tuple(reversed(part_a)))))
        priority_b_orders = tuple(dict.fromkeys((part_b, tuple(reversed(part_b)))))
        component_pair = (tuple(component_a_order), tuple(component_b_order))
        reversed_component_pair = (tuple(reversed(component_a_order)), tuple(reversed(component_b_order)))
        priority_pairs = tuple(
            dict.fromkeys(
                (
                    component_pair,
                    reversed_component_pair,
                    *((A_order, B_order) for A_order in priority_a_orders for B_order in priority_b_orders),
                )
            )
        )
        return {
            "part_a": part_a,
            "part_b": part_b,
            "high_edges": high_edges,
            "priority_pairs": priority_pairs,
        }

    def witness_report(A_order, B_order, high_edges):
        nonlocal checked_permutation_pairs
        if checked_permutation_pairs >= max_permutation_pairs:
            return "limit"
        checked_permutation_pairs += 1
        if not _has_strong_ordering(A_order, B_order, high_edges):
            return None
        witness_order = tuple(hubs) + tuple(A_order) + tuple(B_order)
        if witness_order in seen_witness_orders:
            return None
        seen_witness_orders.add(witness_order)
        if not passes_bad_side_precircular_cR(D, witness_order):
            return None
        return {
            **base,
            "status": "strong_ordering_found",
            "strong_ordering_exists": True,
            "checked_permutation_pairs": checked_permutation_pairs,
            "part_a": tuple(A_order),
            "part_b": tuple(B_order),
            "witness_order": witness_order,
            "witness_order_is_cr": True,
        }

    seen_priority_pairs = set()
    for flips in product((0, 1), repeat=len(components)):
        search = flip_search(flips)
        for A_order, B_order in search["priority_pairs"]:
            key = (A_order, B_order)
            if key in seen_priority_pairs:
                continue
            seen_priority_pairs.add(key)
            report = witness_report(A_order, B_order, search["high_edges"])
            if report == "limit":
                return
            if report is not None:
                yield report

    for flips in product((0, 1), repeat=len(components)):
        search = flip_search(flips)
        part_a = search["part_a"]
        part_b = search["part_b"]
        high_edges = search["high_edges"]
        seen_order_pairs = set(search["priority_pairs"])
        for A_order in permutations(part_a):
            for B_order in permutations(part_b):
                if (A_order, B_order) in seen_order_pairs:
                    continue
                seen_order_pairs.add((A_order, B_order))
                report = witness_report(A_order, B_order, high_edges)
                if report == "limit":
                    return
                if report is not None:
                    yield report


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
