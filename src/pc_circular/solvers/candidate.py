"""Initial candidate API for the research loop.

The current implementation is deliberately conservative:

* for n <= 8 it calls the exact brute-force baseline;
* for a proved universal-order sub-case it returns a represented witness,
  because every circular order is circular Robinson;
* for larger instances it tries a small deterministic set of represented
  orders; a found witness proves ``exists=True``, but failure remains
  ``complete=False``.
* for an explicit finite ``quasi_orders`` family under a small bound, it tests
  the whole provided family exactly.
* when the minimum-distance graph exposes a cycle, it accepts the reconstructed
  order only after direct cR and PC-tree representation verification.
* for a three-level unique-farthest matching sub-case it reconstructs a
  side-by-side paired witness and accepts it only after the same verification.
* for small forbidden induced submatrices and for binary non-bipartite high
  graphs with a low-universal hub, it can return proved negative certificates.
* for a binary even high-cycle of length at least 6 with a low-universal hub,
  it can return a proved negative certificate.
* for a bounded binary low-hub strong-ordering diagnostic it accepts only a
  represented order that is verified directly as cR.

This is not a solution to the general problem.  Future goals should replace
the large-n placeholder with a proved algorithm or a clearly scoped sub-case.
"""

from __future__ import annotations

from collections.abc import Sized
from itertools import combinations, islice
from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels, represents_order, sample_frontier
from pc_circular.predicates import (
    has_at_most_one_bad_witness_per_pair,
    passes_bad_side_precircular_cR,
    validate_dissimilarity,
)
from pc_circular.solvers import brute_force
from pc_circular.solvers.local_constraints import (
    iter_low_hub_strong_ordering_witnesses,
    low_hub_ferrers_strong_ordering_report,
)


EXACT_BRUTE_FORCE_LIMIT = 8
EXACT_PC_TREE_FRONTIER_LIMIT = 4096
EXACT_QUASI_ORDER_LIMIT = 4096
SMALL_FORBIDDEN_SUBMATRIX_ORDER = 4
SMALL_FORBIDDEN_SUBMATRIX_ORDERS = (4, 5, 6)
SMALL_FORBIDDEN_SUBMATRIX_LIMIT = 4096
LOW_HUB_STRONG_ORDERING_PERMUTATION_LIMIT = 100_000


def _large_n_budget(n: int) -> int:
    if n <= 20:
        return 64
    if n <= 40:
        return 16
    return 4


def _fallback_orders(n: int) -> list[tuple[int, ...]]:
    natural = tuple(range(n))
    reversed_order = tuple(reversed(natural))
    even_odd = tuple(list(range(0, n, 2)) + list(range(1, n, 2)))
    return list(dict.fromkeys([natural, reversed_order, even_odd]))


def _validate_order_shape(order: Sequence[int], n: int) -> tuple[int, ...]:
    seq = tuple(order)
    if len(seq) != n or set(seq) != set(range(n)):
        raise ValueError("order must be a permutation of 0..n-1")
    return seq


def _multiply_capped(left: int, right: int, cap: int) -> int:
    if left == 0 or right == 0:
        return 0
    if left > cap // right:
        return cap + 1
    return left * right


def _factorial_capped(value: int, cap: int) -> int:
    result = 1
    for factor in range(2, value + 1):
        result = _multiply_capped(result, factor, cap)
        if result > cap:
            return result
    return result


def _root_p_circular_choices(degree: int, cap: int) -> int:
    if degree <= 2:
        return 1
    result = 1
    for factor in range(2, degree):
        result *= factor
        if result > 2 * cap:
            return cap + 1
    return max(1, result // 2)


def _pc_tree_frontier_upper_bound(
    node: PCNode,
    *,
    cap: int = EXACT_PC_TREE_FRONTIER_LIMIT,
    _root: bool = True,
) -> int:
    """Return a capped upper bound on represented scaffold frontiers."""

    if node.kind == "leaf":
        return 1

    count = 1
    for child in node.children:
        child_count = _pc_tree_frontier_upper_bound(child, cap=cap, _root=False)
        count = _multiply_capped(count, child_count, cap)
        if count > cap:
            return count

    if node.kind == "P":
        if _root:
            local_choices = _root_p_circular_choices(len(node.children), cap)
        else:
            local_choices = _factorial_capped(len(node.children), cap)
    else:
        local_choices = 1 if _root or len(node.children) <= 1 else 2
    return _multiply_capped(count, local_choices, cap)


def _bounded_pc_tree_exact_result(D, n: int, pc_tree: Optional[PCNode]):
    if pc_tree is None:
        return None
    if set(labels(pc_tree)) != set(range(n)):
        raise ValueError("pc_tree labels must be exactly 0..n-1")

    upper_bound = _pc_tree_frontier_upper_bound(pc_tree)
    if upper_bound > EXACT_PC_TREE_FRONTIER_LIMIT:
        return None

    orders = enumerate_frontiers(pc_tree, canonical=True)
    for order in orders:
        if passes_bad_side_precircular_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "solver": "candidate_exact_bounded_pc_tree_frontiers",
                "tried_orders": len(orders),
                "frontiers_enumerated": len(orders),
                "frontier_count": len(orders),
                "frontier_upper_bound": upper_bound,
                "frontier_limit": EXACT_PC_TREE_FRONTIER_LIMIT,
                "note": "all represented PC-tree frontiers were enumerated under a certified upper bound and a cR witness was found",
            }
    return {
        "exists": False,
        "order": None,
        "complete": True,
        "solver": "candidate_exact_bounded_pc_tree_frontiers",
        "tried_orders": len(orders),
        "frontiers_enumerated": len(orders),
        "frontier_count": len(orders),
        "frontier_upper_bound": upper_bound,
        "frontier_limit": EXACT_PC_TREE_FRONTIER_LIMIT,
        "note": "all represented PC-tree frontiers were enumerated under a certified upper bound and none is circular Robinson",
    }


def _bounded_quasi_orders_exact_result(D, n: int, quasi_orders):
    if quasi_orders is None or not isinstance(quasi_orders, Sized):
        return None

    try:
        order_count = len(quasi_orders)
    except TypeError:
        return None
    if order_count > EXACT_QUASI_ORDER_LIMIT:
        return None

    tried = 0
    for raw_order in quasi_orders:
        tried += 1
        order = _validate_order_shape(raw_order, n)
        if passes_bad_side_precircular_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "solver": "candidate_exact_bounded_quasi_orders",
                "tried_orders": tried,
                "quasi_order_count": order_count,
                "quasi_order_limit": EXACT_QUASI_ORDER_LIMIT,
                "note": "the explicit finite quasi_orders family is under the exact limit and contains a verified cR witness",
            }

    return {
        "exists": False,
        "order": None,
        "complete": True,
        "solver": "candidate_exact_bounded_quasi_orders",
        "tried_orders": tried,
        "quasi_order_count": order_count,
        "quasi_order_limit": EXACT_QUASI_ORDER_LIMIT,
        "note": "the explicit finite quasi_orders family is under the exact limit and no provided order is circular Robinson",
    }


def _induced_submatrix(D, subset: tuple[int, ...]):
    return [[D[i][j] for j in subset] for i in subset]


def _small_forbidden_submatrix_result(
    D,
    n: int,
    order_sizes: Sequence[int] = SMALL_FORBIDDEN_SUBMATRIX_ORDERS,
):
    checked_total = 0
    for order_size in order_sizes:
        checked_for_size = 0
        for subset in combinations(range(n), order_size):
            checked_total += 1
            checked_for_size += 1
            submatrix = _induced_submatrix(D, subset)
            if not brute_force.solve(submatrix)["exists"]:
                return {
                    "exists": False,
                    "order": None,
                    "complete": True,
                    "solver": "candidate_small_forbidden_submatrix_obstruction",
                    "obstruction_labels": list(subset),
                    "obstruction_order": order_size,
                    "checked_subsets": checked_total,
                    "checked_subsets_for_order": checked_for_size,
                    "subset_limit": SMALL_FORBIDDEN_SUBMATRIX_LIMIT,
                    "obstruction_orders": list(order_sizes),
                    "note": "an induced submatrix has no circular-Robinson order, so no full order can be circular Robinson",
                }
            if checked_for_size >= SMALL_FORBIDDEN_SUBMATRIX_LIMIT:
                break
    return None


def _is_bipartite(vertices: Sequence[int], neighbors: dict[int, list[int]]) -> bool:
    color: dict[int, int] = {}
    for start in vertices:
        if start in color:
            continue
        color[start] = 0
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in neighbors[current]:
                if neighbor not in color:
                    color[neighbor] = 1 - color[current]
                    stack.append(neighbor)
                elif color[neighbor] == color[current]:
                    return False
    return True


def _non_bipartite_high_graph_low_hub_result(D, n: int):
    positive_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n) if D[i][j] > 0})
    if len(positive_values) != 2:
        return None
    _low, high = positive_values

    high_neighbors = {
        i: [j for j in range(n) if i != j and D[i][j] == high]
        for i in range(n)
    }
    hubs = [i for i, neighbors in high_neighbors.items() if not neighbors]
    high_vertices = [i for i, neighbors in high_neighbors.items() if neighbors]
    if not hubs or len(high_vertices) < 3:
        return None
    if _is_bipartite(high_vertices, high_neighbors):
        return None

    return {
        "exists": False,
        "order": None,
        "complete": True,
        "solver": "candidate_non_bipartite_high_graph_low_hub_obstruction",
        "hub_labels": hubs,
        "high_graph_labels": high_vertices,
        "note": "the high-distance graph is non-bipartite with a low-universal hub, which would force an impossible source/sink 2-coloring",
    }


def _even_high_cycle_low_hub_result(D, n: int):
    positive_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n) if D[i][j] > 0})
    if len(positive_values) != 2:
        return None
    _low, high = positive_values

    high_neighbors = {
        i: [j for j in range(n) if i != j and D[i][j] == high]
        for i in range(n)
    }
    hubs = [i for i, neighbors in high_neighbors.items() if not neighbors]
    cycle_vertices = [i for i, neighbors in high_neighbors.items() if neighbors]
    if not hubs or len(cycle_vertices) < 6 or len(cycle_vertices) % 2 != 0:
        return None
    if any(len(high_neighbors[i]) != 2 for i in cycle_vertices):
        return None

    cycle_set = set(cycle_vertices)
    if any(neighbor not in cycle_set for i in cycle_vertices for neighbor in high_neighbors[i]):
        return None

    start = cycle_vertices[0]
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in high_neighbors[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    if seen != cycle_set:
        return None

    return {
        "exists": False,
        "order": None,
        "complete": True,
        "solver": "candidate_even_high_cycle_low_hub_obstruction",
        "hub_labels": hubs,
        "cycle_labels": cycle_vertices,
        "note": "the high-distance graph is an even cycle of length at least 6 with a low-universal hub, which is incompatible with the bad-witness one-side condition",
    }


def _minimum_distance_cycle_order(D, n: int) -> tuple[int, ...] | None:
    if n < 4:
        return None

    positive_distances = [D[i][j] for i in range(n) for j in range(i + 1, n) if D[i][j] > 0]
    if not positive_distances:
        return None
    minimum = min(positive_distances)
    neighbors = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if D[i][j] == minimum:
                neighbors[i].append(j)
                neighbors[j].append(i)
    if any(len(values) != 2 for values in neighbors.values()):
        return None

    start = 0
    previous = None
    current = start
    order = []
    for _ in range(n):
        order.append(current)
        choices = sorted(neighbors[current])
        next_candidates = [value for value in choices if value != previous]
        if not next_candidates:
            return None
        nxt = next_candidates[0]
        previous, current = current, nxt
    if current != start or len(set(order)) != n:
        return None
    return tuple(order)


def _minimum_cycle_witness_result(D, n: int, pc_tree: Optional[PCNode]):
    order = _minimum_distance_cycle_order(D, n)
    if order is None:
        return None
    if pc_tree is not None and not represents_order(pc_tree, order):
        return None
    if not passes_bad_side_precircular_cR(D, order):
        return None
    return {
        "exists": True,
        "order": list(order),
        "complete": True,
        "solver": "candidate_minimum_distance_cycle_witness",
        "note": "minimum-distance graph is a simple cycle and the reconstructed order is a represented verified witness",
    }


def _paired_farthest_order(D, n: int) -> tuple[int, ...] | None:
    positive_values = sorted({D[i][j] for i in range(n) for j in range(i + 1, n) if D[i][j] > 0})
    if len(positive_values) != 3:
        return None
    low, mid, high = positive_values

    high_neighbors = {
        i: [j for j in range(n) if i != j and D[i][j] == high]
        for i in range(n)
    }
    neutral = [i for i, neighbors in high_neighbors.items() if not neighbors]
    if len(neutral) > 1:
        return None
    if any(len(neighbors) not in {0, 1} for neighbors in high_neighbors.values()):
        return None

    paired = [i for i in range(n) if high_neighbors[i]]
    if len(paired) < 4 or len(paired) % 2:
        return None
    paired_set = set(paired)
    mate = {i: high_neighbors[i][0] for i in paired}
    if any(mate.get(mate[i]) != i for i in paired):
        return None

    if neutral:
        z = neutral[0]
        if any(D[z][v] != low for v in range(n) if v != z):
            return None

    unseen = set(paired)
    components: list[set[int]] = []
    while unseen:
        start = min(unseen)
        stack = [start]
        component: set[int] = set()
        unseen.remove(start)
        while stack:
            current = stack.pop()
            component.add(current)
            for other in list(unseen):
                if D[current][other] == low:
                    unseen.remove(other)
                    stack.append(other)
        components.append(component)

    if len(components) != 2 or len(components[0]) != len(components[1]):
        return None

    for component in components:
        values = sorted(component)
        for idx, a in enumerate(values):
            for b in values[idx + 1 :]:
                if D[a][b] != low:
                    return None

    comp_index = {}
    for idx, component in enumerate(components):
        for value in component:
            comp_index[value] = idx
    if any(comp_index[i] == comp_index[mate[i]] for i in paired):
        return None

    for i in range(len(paired)):
        a = paired[i]
        for b in paired[i + 1 :]:
            if mate[a] == b:
                expected = high
            elif comp_index[a] == comp_index[b]:
                expected = low
            else:
                expected = mid
            if D[a][b] != expected:
                return None

    first_side = sorted(min(components, key=lambda values: tuple(sorted(values))))
    second_side = [mate[value] for value in first_side]
    order = first_side + second_side + neutral
    return tuple(order)


def _paired_farthest_witness_result(D, n: int, pc_tree: Optional[PCNode]):
    order = _paired_farthest_order(D, n)
    if order is None:
        return None
    if pc_tree is not None and not represents_order(pc_tree, order):
        return None
    if not passes_bad_side_precircular_cR(D, order):
        return None
    return {
        "exists": True,
        "order": list(order),
        "complete": True,
        "solver": "candidate_paired_farthest_matching_witness",
        "note": "three-level unique-farthest matching structure has a represented side-by-side cR witness",
    }


def _low_hub_strong_ordering_witness_result(D, n: int, pc_tree: Optional[PCNode]):
    ferrers_report = low_hub_ferrers_strong_ordering_report(D)
    if ferrers_report["strong_ordering_exists"] is True and ferrers_report["witness_order"] is not None:
        order = _validate_order_shape(ferrers_report["witness_order"], n)
        if ferrers_report["witness_order_is_cr"] and passes_bad_side_precircular_cR(D, order):
            if pc_tree is None or represents_order(pc_tree, order):
                return {
                    "exists": True,
                    "order": list(order),
                    "complete": True,
                    "solver": "candidate_low_hub_strong_ordering_witness",
                    "checked_permutation_pairs": 0,
                    "permutation_pair_limit": LOW_HUB_STRONG_ORDERING_PERMUTATION_LIMIT,
                    "hub_labels": list(ferrers_report.get("hub_labels", ())),
                    "part_a": list(ferrers_report.get("part_a", ())),
                    "part_b": list(ferrers_report.get("part_b", ())),
                    "note": "binary low-hub Ferrers high graph produced a represented strong-ordering witness verified directly as circular Robinson",
                }

    for report in iter_low_hub_strong_ordering_witnesses(
        D,
        max_permutation_pairs=LOW_HUB_STRONG_ORDERING_PERMUTATION_LIMIT,
    ):
        order = _validate_order_shape(report["witness_order"], n)
        if not report["witness_order_is_cr"] or not passes_bad_side_precircular_cR(D, order):
            continue
        if pc_tree is not None and not represents_order(pc_tree, order):
            continue
        return {
            "exists": True,
            "order": list(order),
            "complete": True,
            "solver": "candidate_low_hub_strong_ordering_witness",
            "checked_permutation_pairs": report.get("checked_permutation_pairs", 0),
            "permutation_pair_limit": LOW_HUB_STRONG_ORDERING_PERMUTATION_LIMIT,
            "hub_labels": list(report.get("hub_labels", ())),
            "part_a": list(report.get("part_a", ())),
            "part_b": list(report.get("part_b", ())),
            "note": "bounded low-hub strong-ordering diagnostic produced a represented order that was verified directly as circular Robinson",
        }
    return None


def _universal_order_result(n: int, quasi_orders, pc_tree: Optional[PCNode]):
    if quasi_orders is not None:
        iterator = iter(quasi_orders)
        try:
            order = _validate_order_shape(next(iterator), n)
        except StopIteration:
            return {
                "exists": False,
                "order": None,
                "complete": True,
                "solver": "candidate_universal_bad_witness_bound_all_orders",
                "note": "all orders would be circular Robinson, but the provided order family is empty",
            }
    elif pc_tree is not None:
        order = _validate_order_shape(sample_frontier(pc_tree), n)
    else:
        order = tuple(range(n))

    return {
        "exists": True,
        "order": list(order),
        "complete": True,
        "solver": "candidate_universal_bad_witness_bound_all_orders",
        "note": "all represented orders are circular Robinson by the bad-witness count bound",
    }


def _sample_orders(
    n: int,
    quasi_orders: Optional[Iterable[Sequence[int]]],
    pc_tree: Optional[PCNode],
) -> list[tuple[int, ...]]:
    budget = _large_n_budget(n)
    if quasi_orders is not None:
        return [tuple(order) for order in islice(quasi_orders, budget)]
    if pc_tree is not None:
        return enumerate_frontiers(pc_tree, canonical=True, limit=budget)
    return _fallback_orders(n)[:budget]


def solve(D, quasi_orders=None, pc_tree=None):
    n = validate_dissimilarity(D)
    if n <= EXACT_BRUTE_FORCE_LIMIT:
        result = brute_force.solve(D, quasi_orders=quasi_orders, pc_tree=pc_tree)
        result["solver"] = "candidate_exact_bruteforce_n_le_8"
        return result

    if has_at_most_one_bad_witness_per_pair(D):
        return _universal_order_result(n, quasi_orders, pc_tree)

    non_bipartite_high_graph_result = _non_bipartite_high_graph_low_hub_result(D, n)
    if non_bipartite_high_graph_result is not None:
        return non_bipartite_high_graph_result

    even_high_cycle_result = _even_high_cycle_low_hub_result(D, n)
    if even_high_cycle_result is not None:
        return even_high_cycle_result

    exact_quasi_orders_result = _bounded_quasi_orders_exact_result(D, n, quasi_orders)
    if exact_quasi_orders_result is not None:
        return exact_quasi_orders_result

    if quasi_orders is None:
        cycle_result = _minimum_cycle_witness_result(D, n, pc_tree)
        if cycle_result is not None:
            return cycle_result
        paired_result = _paired_farthest_witness_result(D, n, pc_tree)
        if paired_result is not None:
            return paired_result
        strong_ordering_result = _low_hub_strong_ordering_witness_result(D, n, pc_tree)
        if strong_ordering_result is not None:
            return strong_ordering_result
        exact_pc_tree_result = _bounded_pc_tree_exact_result(D, n, pc_tree)
        if exact_pc_tree_result is not None:
            return exact_pc_tree_result

    tried = 0
    for order in _sample_orders(n, quasi_orders, pc_tree):
        tried += 1
        if passes_bad_side_precircular_cR(D, order):
            return {
                "exists": True,
                "order": list(order),
                "complete": True,
                "solver": "candidate_validated_sampled_witness",
                "tried_orders": tried,
                "note": "sampled represented order is a valid circular-Robinson witness",
            }

    obstruction_result = _small_forbidden_submatrix_result(D, n)
    if obstruction_result is not None:
        return obstruction_result

    return {
        "exists": False,
        "order": None,
        "complete": False,
        "solver": "candidate_large_n_placeholder",
        "tried_orders": tried,
        "note": "no sampled witness found; this is not a proof of non-existence",
    }
