"""Circle/interlacement diagnostics for local bad-side constraints.

The helpers in this module are research diagnostics only.  A fully visible
bad-side obligation at a P-node has the form ``same_side(a,c;b,d)`` after
projection to four distinct branches.  Locally, this says that the branch chord
``ac`` must not cross the branch chord ``bd``.  We enumerate the branch orders
that satisfy these forced non-interlacements and compare them with branch orders
actually seen among globally cR frontiers.
"""

from __future__ import annotations

from itertools import combinations

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels
from pc_circular.predicates import all_circular_orders, passes_bad_side_precircular_cR
from pc_circular.solvers.local_constraints import project_bad_side_obligations_to_pc_nodes
from pc_circular.solvers.width4_experiments import induced_child_circular_order


Chord = tuple[int, int]
ForbiddenChordPair = tuple[Chord, Chord]


def chord_crosses_in_order(branch_order, left_chord: Chord, right_chord: Chord) -> bool:
    """Return whether two branch chords alternate in ``branch_order``."""

    order = tuple(branch_order)
    if len(set(order)) != len(order):
        raise ValueError("branch_order must contain distinct branches")
    if len(set(left_chord)) != 2 or len(set(right_chord)) != 2:
        raise ValueError("chords must have two distinct endpoints")
    if set(left_chord) & set(right_chord):
        return False
    if not set(left_chord).issubset(set(order)) or not set(right_chord).issubset(set(order)):
        raise ValueError("chord endpoints must appear in branch_order")

    a, c = left_chord
    b, d = right_chord
    position = {branch: index for index, branch in enumerate(order)}
    b_between = (
        0
        < (position[b] - position[a]) % len(order)
        < (position[c] - position[a]) % len(order)
    )
    d_between = (
        0
        < (position[d] - position[a]) % len(order)
        < (position[c] - position[a]) % len(order)
    )
    return b_between != d_between


def branch_order_satisfies_forbidden_chord_pairs(
    branch_order,
    forbidden_chord_pairs,
) -> bool:
    """Check all forced non-crossing constraints."""

    return all(
        not chord_crosses_in_order(branch_order, left_chord, right_chord)
        for left_chord, right_chord in forbidden_chord_pairs
    )


def _components(vertices, edges) -> tuple[tuple, ...]:
    neighbors = {vertex: set() for vertex in vertices}
    for left, right in edges:
        neighbors.setdefault(left, set()).add(right)
        neighbors.setdefault(right, set()).add(left)

    seen = set()
    components = []
    for start in sorted(neighbors):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in neighbors[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(sorted(components, key=lambda item: (-len(item), item)))


def _branch_interaction_edges(forbidden_chord_pairs) -> tuple[tuple[int, int], ...]:
    edges = set()
    for left_chord, right_chord in forbidden_chord_pairs:
        support = tuple(sorted({*left_chord, *right_chord}))
        for left, right in combinations(support, 2):
            edges.add((left, right))
    return tuple(sorted(edges))


def _local_orders_for_constraints(degree: int, forbidden_chord_pairs) -> tuple[tuple[int, ...], ...]:
    return tuple(
        order
        for order in all_circular_orders(degree)
        if branch_order_satisfies_forbidden_chord_pairs(order, forbidden_chord_pairs)
    )


def pnode_circle_graph_local_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_branch_degree: int = 8,
    max_examples: int = 5,
) -> dict:
    """Compare local non-interlacement constraints to global cR branch orders."""

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if max_branch_degree < 1:
        raise ValueError("max_branch_degree must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

    projection = project_bad_side_obligations_to_pc_nodes(D, T)
    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = tuple(raw_frontiers[:frontier_limit])
    accepted_frontiers = tuple(
        order for order in frontiers if passes_bad_side_precircular_cR(D, order)
    )

    nodes = []
    for node in projection["nodes"]:
        if node["kind"] != "P":
            continue
        degree = node["degree"]
        forbidden_chord_pairs = tuple(
            (tuple(pair[0]), tuple(pair[1])) for pair in node["forbidden_chord_pairs"]
        )
        active_chords = tuple(
            sorted({chord for pair in forbidden_chord_pairs for chord in pair})
        )
        chord_components = _components(active_chords, forbidden_chord_pairs)
        branch_edges = _branch_interaction_edges(forbidden_chord_pairs)
        branch_components = _components(tuple(range(degree)), branch_edges)
        declared_order = tuple(range(degree))
        declared_crossing_count = sum(
            1
            for left_chord, right_chord in forbidden_chord_pairs
            if chord_crosses_in_order(declared_order, left_chord, right_chord)
        )

        all_seen_orders = {
            order
            for order in (
                induced_child_circular_order(frontier, node["child_label_sets"])
                for frontier in frontiers
            )
            if order is not None
        }
        global_cr_orders = {
            order
            for order in (
                induced_child_circular_order(frontier, node["child_label_sets"])
                for frontier in accepted_frontiers
            )
            if order is not None
        }

        if degree > max_branch_degree:
            status = "unsupported_degree"
            local_orders = None
            local_contains_global = None
            local_extra_order_count = None
            local_missing_global_count = None
        else:
            local_orders = set(_local_orders_for_constraints(degree, forbidden_chord_pairs))
            local_contains_global = global_cr_orders <= local_orders
            local_extra_order_count = len(local_orders - global_cr_orders)
            local_missing_global_count = len(global_cr_orders - local_orders)
            if local_missing_global_count:
                status = "global_not_contained"
            elif not local_orders:
                status = "local_unsat"
            elif local_extra_order_count:
                status = "local_strict_superset"
            else:
                status = "local_matches_global_seen"

        nodes.append(
            {
                "path": node["path"],
                "degree": degree,
                "status": status,
                "branch_sizes": node["branch_sizes"],
                "forbidden_chord_pair_count": len(forbidden_chord_pairs),
                "forbidden_chord_pairs": forbidden_chord_pairs[:max_examples],
                "active_chord_count": len(active_chords),
                "forced_noncross_chord_component_count": len(chord_components),
                "forced_noncross_chord_component_sizes": tuple(
                    len(component) for component in chord_components
                ),
                "branch_interaction_component_count": len(branch_components),
                "branch_interaction_component_sizes": tuple(
                    len(component) for component in branch_components
                ),
                "declared_order_crossing_violation_count": declared_crossing_count,
                "frontier_child_order_count": len(all_seen_orders),
                "global_cr_branch_order_count": len(global_cr_orders),
                "local_order_count": None if local_orders is None else len(local_orders),
                "local_contains_global_cr_orders": local_contains_global,
                "local_extra_order_count": local_extra_order_count,
                "local_missing_global_order_count": local_missing_global_count,
                "local_order_examples": (
                    None if local_orders is None else tuple(sorted(local_orders)[:max_examples])
                ),
                "global_cr_order_examples": tuple(sorted(global_cr_orders)[:max_examples]),
                "interpretation": (
                    "local forced non-interlacement constraints only; "
                    "extra local orders show missing context/internal information"
                ),
            }
        )

    tested_nodes = [node for node in nodes if node["status"] != "unsupported_degree"]
    return {
        "method": "pnode_circle_graph_local_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "accepted_frontier_count": len(accepted_frontiers),
        "obligation_count": projection["obligation_count"],
        "obligations_truncated": projection["obligations_truncated"],
        "pnode_count": len(nodes),
        "tested_pnode_count": len(tested_nodes),
        "unsupported_pnode_count": sum(1 for node in nodes if node["status"] == "unsupported_degree"),
        "global_not_contained_count": sum(1 for node in nodes if node["status"] == "global_not_contained"),
        "local_unsat_count": sum(1 for node in nodes if node["status"] == "local_unsat"),
        "local_strict_superset_count": sum(
            1 for node in nodes if node["status"] == "local_strict_superset"
        ),
        "constrained_local_strict_superset_count": sum(
            1
            for node in nodes
            if node["status"] == "local_strict_superset"
            and node["forbidden_chord_pair_count"] > 0
        ),
        "vacuous_local_strict_superset_count": sum(
            1
            for node in nodes
            if node["status"] == "local_strict_superset"
            and node["forbidden_chord_pair_count"] == 0
        ),
        "local_matches_global_seen_count": sum(
            1 for node in nodes if node["status"] == "local_matches_global_seen"
        ),
        "max_local_extra_order_count": max(
            (
                node["local_extra_order_count"]
                for node in tested_nodes
                if node["local_extra_order_count"] is not None
            ),
            default=0,
        ),
        "max_forbidden_chord_pair_count": max(
            (node["forbidden_chord_pair_count"] for node in nodes),
            default=0,
        ),
        "nodes": tuple(nodes),
        "interpretation": (
            "Circle/interlacement lab for fully visible same_side constraints; "
            "not split decomposition and not a solver."
        ),
    }
