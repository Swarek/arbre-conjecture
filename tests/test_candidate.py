from itertools import combinations
import random

from pc_circular.generators import (
    chain_high_graph_plus_low_hub,
    complete_bipartite_high_graph_plus_low_hub,
    cycle_metric,
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    matching_high_graph_plus_low_hub,
    non_bipartite_high_graph_plus_low_hub,
    odd_high_cycle_plus_low_hub,
    paired_farthest_matching,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    permuted_chain_high_graph_plus_low_hub,
    permuted_disjoint_chain_high_graph_plus_low_hub,
    permuted_cycle_metric,
    quasi_circular_not_circular_four_point,
    random_dissimilarity,
)
from pc_circular.pc_tree import (
    balanced_pc_tree,
    c_node,
    enumerate_frontiers,
    leaf,
    p_node,
    represents_order,
    sample_frontier,
    star_pc_tree,
)
from pc_circular.predicates import all_circular_orders, canonical_circular_order, is_precircular_order_cR
from pc_circular.solvers.candidate import (
    EXACT_PC_TREE_FRONTIER_LIMIT,
    EXACT_QUASI_ORDER_LIMIT,
    SMALL_FORBIDDEN_SUBMATRIX_ORDER,
    SMALL_FORBIDDEN_SUBMATRIX_ORDERS,
    _even_high_cycle_low_hub_result,
    _low_hub_strong_ordering_witness_result,
    _minimum_distance_cycle_order,
    _paired_farthest_order,
    _pc_tree_frontier_upper_bound,
    _small_forbidden_submatrix_result,
    solve,
)
from pc_circular.solvers import brute_force
from pc_circular.solvers.local_constraints import (
    low_hub_component_ferrers_strong_ordering_report,
    low_hub_ferrers_strong_ordering_report,
    pc_tree_guided_low_hub_matching_witness_report,
)


def _one_high_edge_instance(n):
    D = equal_distance_instance(n)
    D[0][1] = D[1][0] = 2
    return D


def _matching_with_extra_hubs(pair_count, hub_count):
    n = 2 * pair_count + hub_count
    D = equal_distance_instance(n)
    for left in range(pair_count):
        right = pair_count + left
        D[left][right] = D[right][left] = 2
    return D


def _cycle_metric_for_order(order):
    n = len(order)
    position = {label: idx for idx, label in enumerate(order)}
    D = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            delta = abs(position[i] - position[j])
            D[i][j] = D[j][i] = min(delta, n - delta)
    return D


def _plateau_cycle_metric(n):
    D = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            delta = min((j - i) % n, (i - j) % n)
            D[i][j] = D[j][i] = max(1, delta - 1)
    return D


def _rigid_c_tree(n):
    return c_node([leaf(i) for i in range(n)])


def _induced_submatrix(D, subset):
    return [[D[i][j] for j in subset] for i in subset]


def _extended_non_cr_four_point_instance(n):
    D = equal_distance_instance(n)
    base = quasi_circular_not_circular_four_point()
    for i in range(4):
        for j in range(4):
            D[i][j] = base[i][j]
    return D


def test_candidate_solves_large_constant_off_diagonal_star_tree_completely():
    D = equal_distance_instance(12, value=5)
    T = star_pc_tree(12)
    result = solve(D, pc_tree=T)
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_universal_bad_witness_bound_all_orders"
    assert is_precircular_order_cR(D, result["order"])
    assert result["order"] == list(range(12))


def test_candidate_universal_subcase_uses_represented_balanced_frontier():
    D = _one_high_edge_instance(11)
    T = balanced_pc_tree(11, kind="mixed")
    result = solve(D, pc_tree=T)
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["order"] == list(sample_frontier(T))
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_universal_subcase_respects_empty_quasi_order_family():
    D = equal_distance_instance(10)
    result = solve(D, quasi_orders=[])
    assert result["exists"] is False
    assert result["complete"] is True
    assert result["order"] is None


def test_candidate_exact_bounded_quasi_orders_handles_empty_non_universal_family():
    D = cycle_metric(10)
    result = solve(D, quasi_orders=[])
    assert result["exists"] is False
    assert result["complete"] is True
    assert result["order"] is None
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"
    assert result["quasi_order_count"] == 0


def test_candidate_universal_subcase_uses_first_quasi_order():
    D = _one_high_edge_instance(10)
    result = solve(D, quasi_orders=[(9, 8, 7, 6, 5, 4, 3, 2, 1, 0)])
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["order"] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_exact_bounded_quasi_orders_proves_large_finite_negative():
    D = cycle_metric(10)
    bad_first_orders = [(0, 2, 4, 6, 8, 1, 3, 5, 7, 9)]
    result = solve(D, quasi_orders=bad_first_orders)
    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"
    assert result["tried_orders"] == 1
    assert result["quasi_order_count"] == 1


def test_candidate_exact_bounded_quasi_orders_finds_witness_beyond_sample_budget():
    D = cycle_metric(10)
    bad_order = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
    witness = tuple(range(10))
    assert not is_precircular_order_cR(D, bad_order)
    assert is_precircular_order_cR(D, witness)

    result = solve(D, quasi_orders=[bad_order] * 64 + [witness])
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"
    assert result["tried_orders"] == 65
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_marks_sampled_positive_witness_complete_for_non_sized_iterator():
    D = cycle_metric(10)
    result = solve(D, quasi_orders=iter([tuple(range(10))]))
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_validated_sampled_witness"
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_large_finite_quasi_order_family_remains_incomplete_without_false_negative():
    D = cycle_metric(10)
    bad_order = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
    witness = tuple(range(10))
    orders = [bad_order] * (EXACT_QUASI_ORDER_LIMIT + 1) + [witness]
    result = solve(D, quasi_orders=orders)
    assert result["exists"] is False
    assert result["complete"] is False
    assert result["solver"] == "candidate_large_n_placeholder"
    assert result["tried_orders"] == 64


def test_candidate_small_forbidden_submatrix_proves_large_random_negative():
    D = random_dissimilarity(10, rng=random.Random(0), values=(1, 2, 3))
    result = solve(D, pc_tree=star_pc_tree(10))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_small_forbidden_submatrix_obstruction"
    assert result["obstruction_order"] == SMALL_FORBIDDEN_SUBMATRIX_ORDER
    subset = tuple(result["obstruction_labels"])
    submatrix = [[D[i][j] for j in subset] for i in subset]
    assert not brute_force.solve(submatrix)["exists"]


def test_candidate_small_forbidden_submatrix_reports_explicit_obstruction():
    obstruction = [
        [0, 2, 1, 2],
        [2, 0, 3, 3],
        [1, 3, 0, 3],
        [2, 3, 3, 0],
    ]
    D = equal_distance_instance(9)
    for i in range(4):
        for j in range(4):
            D[i][j] = obstruction[i][j]

    assert not brute_force.solve(obstruction)["exists"]
    result = solve(D, pc_tree=star_pc_tree(9))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_small_forbidden_submatrix_obstruction"
    assert result["obstruction_labels"] == [0, 1, 2, 3]
    assert result["checked_subsets"] == 1


def test_candidate_small_forbidden_submatrix_finds_five_point_obstruction_after_four_local_passes():
    D = padded_four_local_non_cr(9)
    assert 5 in SMALL_FORBIDDEN_SUBMATRIX_ORDERS
    assert all(
        brute_force.solve(_induced_submatrix(D, subset))["exists"]
        for subset in combinations(range(9), 4)
    )

    result = _small_forbidden_submatrix_result(D, len(D), (5,))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_small_forbidden_submatrix_obstruction"
    assert result["obstruction_order"] == 5
    assert result["obstruction_labels"] == [0, 1, 2, 3, 4]
    assert result["checked_subsets_for_order"] == 1
    assert not brute_force.solve(_induced_submatrix(D, result["obstruction_labels"]))["exists"]


def test_candidate_small_forbidden_submatrix_finds_six_point_obstruction_after_five_local_passes():
    D = padded_five_local_non_cr(9)
    assert 6 in SMALL_FORBIDDEN_SUBMATRIX_ORDERS
    assert all(
        brute_force.solve(_induced_submatrix(D, subset))["exists"]
        for subset in combinations(range(9), 5)
    )

    result = _small_forbidden_submatrix_result(D, len(D), (6,))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_small_forbidden_submatrix_obstruction"
    assert result["obstruction_order"] == 6
    assert result["obstruction_labels"] == [0, 1, 2, 3, 4, 5]
    assert result["checked_subsets_for_order"] == 1
    assert not brute_force.solve(_induced_submatrix(D, result["obstruction_labels"]))["exists"]


def test_candidate_small_forbidden_submatrix_does_not_block_cycle_witness():
    D = cycle_metric(10)
    result = solve(D, pc_tree=star_pc_tree(10))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_minimum_distance_cycle_witness"
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_non_bipartite_high_graph_low_hub_obstruction_covers_odd_cycle():
    D = odd_high_cycle_plus_low_hub(10)
    result = solve(D, pc_tree=star_pc_tree(10))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_non_bipartite_high_graph_low_hub_obstruction"
    assert result["hub_labels"] == [0]
    assert set(result["high_graph_labels"]) == set(range(1, 10))


def test_candidate_non_bipartite_high_graph_low_hub_obstruction_handles_branches():
    D = non_bipartite_high_graph_plus_low_hub(12)
    result = solve(D, pc_tree=star_pc_tree(12))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_non_bipartite_high_graph_low_hub_obstruction"
    assert result["hub_labels"] == [0]
    assert set(result["high_graph_labels"]) == set(range(1, 12))


def test_candidate_even_high_cycle_low_hub_obstruction_proves_large_negative():
    D = even_high_cycle_plus_low_hub(9)

    assert _small_forbidden_submatrix_result(D, 9) is None
    result = solve(D, pc_tree=star_pc_tree(9))

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_even_high_cycle_low_hub_obstruction"
    assert result["hub_labels"] == [0]
    assert set(result["cycle_labels"]) == set(range(1, 9))


def test_candidate_even_high_cycle_low_hub_obstruction_keeps_c4_positive_control():
    D = equal_distance_instance(5)
    for a, b in [(1, 2), (2, 3), (3, 4), (1, 4)]:
        D[a][b] = D[b][a] = 2

    assert _even_high_cycle_low_hub_result(D, 5) is None
    assert brute_force.solve(D)["exists"] is True


def test_candidate_even_high_cycle_low_hub_obstruction_ignores_k33_positive_control():
    D = equal_distance_instance(7)
    for a in (1, 2, 3):
        for b in (4, 5, 6):
            D[a][b] = D[b][a] = 2

    assert _even_high_cycle_low_hub_result(D, 7) is None
    assert brute_force.solve(D)["exists"] is True


def test_candidate_low_hub_strong_ordering_witness_accepts_chain_star():
    D = chain_high_graph_plus_low_hub(12)
    result = solve(D, pc_tree=star_pc_tree(12))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(star_pc_tree(12), result["order"])


def test_candidate_low_hub_ferrers_witness_accepts_permuted_chain_star():
    D = permuted_chain_high_graph_plus_low_hub(21, rng=random.Random(0))
    result = solve(D, pc_tree=star_pc_tree(21))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert result["checked_permutation_pairs"] == 0
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(star_pc_tree(21), result["order"])


def test_candidate_low_hub_component_ferrers_witness_accepts_permuted_disjoint_chain_star():
    D = permuted_disjoint_chain_high_graph_plus_low_hub(21, rng=random.Random(0))
    result = solve(D, pc_tree=star_pc_tree(21))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert result["checked_permutation_pairs"] == 0
    assert result["component_count"] == 2
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(star_pc_tree(21), result["order"])


def test_candidate_low_hub_component_ferrers_continues_after_nonrepresented_nonstar_witness():
    D = permuted_disjoint_chain_high_graph_plus_low_hub(9, rng=random.Random(0))
    T = p_node([c_node([leaf(0), leaf(1)]), *[leaf(i) for i in (2, 3, 4, 5, 6, 7, 8)]])
    component_report = low_hub_component_ferrers_strong_ordering_report(D)

    assert component_report["status"] == "component_ferrers_strong_ordering_found"
    assert component_report["witness_order_is_cr"] is True
    assert not represents_order(T, component_report["witness_order"])

    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert result["checked_permutation_pairs"] > 0
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_low_hub_strong_ordering_witness_accepts_complete_bipartite_star():
    D = complete_bipartite_high_graph_plus_low_hub(11)
    result = solve(D, pc_tree=star_pc_tree(11))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_low_hub_strong_ordering_witness_accepts_permuted_matching_star():
    D = matching_high_graph_plus_low_hub(21, rng=random.Random(39))
    result = solve(D, pc_tree=star_pc_tree(21))

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert result["checked_permutation_pairs"] == 0
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(star_pc_tree(21), result["order"])


def test_candidate_low_hub_strong_ordering_searches_for_represented_nonstar_witness():
    D = matching_high_graph_plus_low_hub(18)
    T = c_node(
        [
            p_node([leaf(0), leaf(17)]),
            p_node([leaf(i) for i in (9, 2, 3, 4, 5, 6, 7, 8)]),
            p_node([leaf(i) for i in (10, 11, 12, 13, 14, 15, 16, 1)]),
        ]
    )
    planted_order = (0, 17, 9, 2, 3, 4, 5, 6, 7, 8, 1, 10, 11, 12, 13, 14, 15, 16)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert represents_order(T, planted_order)
    assert is_precircular_order_cR(D, planted_order)

    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_pc_tree_guided_matching_witness"
    assert result["templates_checked"] >= 1
    assert result["frontiers_sampled"] == 0
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_low_hub_pc_tree_guided_matching_finds_large_nonstar_witness():
    D = matching_high_graph_plus_low_hub(17)
    T = c_node(
        [
            leaf(0),
            p_node([leaf(i) for i in range(1, 9)]),
            c_node([leaf(i) for i in (9, 11, 13, 15, 10, 12, 14, 16)]),
        ]
    )
    represented_witness = (0, 1, 3, 5, 7, 2, 4, 6, 8, 9, 11, 13, 15, 10, 12, 14, 16)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert is_precircular_order_cR(D, represented_witness)
    assert represents_order(T, represented_witness)

    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_pc_tree_guided_matching_witness"
    assert result["order"] == list(represented_witness)
    assert result["templates_checked"] == 1
    assert result["frontiers_sampled"] == 0
    assert result["pair_count"] == 8
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_low_hub_projected_matching_accepts_large_split_hubs():
    D = matching_high_graph_plus_low_hub(12)
    T = c_node(
        [
            leaf(0),
            p_node([leaf(i) for i in range(1, 6)]),
            leaf(11),
            p_node([leaf(i) for i in range(6, 11)]),
        ]
    )
    projected_witness = (0, 1, 2, 3, 4, 5, 11, 6, 7, 8, 9, 10)
    component_report = low_hub_component_ferrers_strong_ordering_report(D)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert component_report["witness_order_is_cr"] is True
    assert not represents_order(T, component_report["witness_order"])
    assert is_precircular_order_cR(D, projected_witness)
    assert represents_order(T, projected_witness)

    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_pc_tree_guided_matching_witness"
    assert result["order"] == list(projected_witness)
    assert result["projected_frontiers_checked"] == 1
    assert result["segments_checked"] == 0
    assert result["frontiers_sampled"] == 0


def test_candidate_exact_low_hub_matching_projection_search_rejects_large_rigid_noncrossing():
    D = matching_high_graph_plus_low_hub(12)
    T = p_node(
        [
            p_node([leaf(1), leaf(6)]),
            p_node([leaf(2), leaf(7)]),
            p_node([leaf(3), leaf(8)]),
            p_node([leaf(4), leaf(9)]),
            p_node([leaf(5), leaf(10)]),
            leaf(0),
            leaf(11),
        ]
    )
    guided = pc_tree_guided_low_hub_matching_witness_report(D, T, frontier_limit=64)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert guided["status"] == "no_pc_tree_guided_matching_witness_found"

    result = solve(D, pc_tree=T)

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_low_hub_matching_projected_pc_tree_search"
    assert result["projection_orders_checked"] <= result["projection_order_bound"]
    assert result["lifted_orders_checked"] == 0


def test_candidate_projected_low_hub_matching_search_avoids_hub_placement_limit():
    D = _matching_with_extra_hubs(pair_count=5, hub_count=8)
    T = p_node(
        [
            *(p_node([leaf(left), leaf(left + 5)]) for left in range(5)),
            *(leaf(hub) for hub in range(10, 18)),
        ]
    )
    guided = pc_tree_guided_low_hub_matching_witness_report(D, T, frontier_limit=64)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert guided["status"] == "no_pc_tree_guided_matching_witness_found"

    result = solve(D, pc_tree=T)

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_low_hub_matching_projected_pc_tree_search"
    assert result["projection_orders_checked"] <= result["projection_order_bound"]
    assert result["lifted_orders_checked"] == 0


def test_candidate_low_hub_ferrers_nonrepresented_witness_continues_search():
    D = permuted_chain_high_graph_plus_low_hub(9, rng=random.Random(0))
    T = p_node([c_node([leaf(2), leaf(5)]), *[leaf(i) for i in (0, 1, 3, 4, 6, 7, 8)]])
    ferrers_report = low_hub_ferrers_strong_ordering_report(D)

    assert ferrers_report["status"] == "ferrers_strong_ordering_found"
    assert ferrers_report["witness_order_is_cr"] is True
    assert not represents_order(T, ferrers_report["witness_order"])

    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert result["checked_permutation_pairs"] > 0
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_exact_pc_tree_uses_circular_root_bound_for_refined_matching_positive():
    D = matching_high_graph_plus_low_hub(10)
    T = p_node(
        [
            c_node([leaf(i) for i in (4, 0, 7, 2)]),
            leaf(1),
            leaf(3),
            leaf(5),
            leaf(6),
            leaf(8),
            leaf(9),
        ]
    )

    assert _pc_tree_frontier_upper_bound(T) == len(enumerate_frontiers(T, canonical=True)) == 720
    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_pc_tree_frontiers"
    assert result["frontier_count"] == 720
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_low_hub_strong_ordering_witness_does_not_accept_tree_negative():
    D = equal_distance_instance(8)
    for a, b in [(1, 2), (1, 5), (2, 3), (2, 4), (3, 6), (4, 7)]:
        D[a][b] = D[b][a] = 2

    assert _low_hub_strong_ordering_witness_result(D, 8, None) is None
    assert brute_force.solve(D)["exists"] is False


def test_candidate_low_hub_strong_ordering_witness_requires_representation():
    D = chain_high_graph_plus_low_hub(10)
    T = c_node([leaf(i) for i in (0, 1, 6, 2, 7, 3, 8, 4, 9, 5)])
    result = _low_hub_strong_ordering_witness_result(D, 10, T)

    assert result is None


def test_candidate_low_hub_strong_ordering_does_not_bypass_explicit_quasi_orders():
    D = chain_high_graph_plus_low_hub(12)
    result = solve(D, quasi_orders=[])

    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"
    assert result["order"] is None


def test_candidate_non_sized_quasi_orders_remain_incomplete_when_sample_misses_witness():
    D = cycle_metric(10)
    bad_order = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
    witness = tuple(range(10))
    result = solve(D, quasi_orders=iter([bad_order] * 64 + [witness]))
    assert result["exists"] is False
    assert result["complete"] is False
    assert result["solver"] == "candidate_large_n_placeholder"
    assert result["tried_orders"] == 64


def test_candidate_exact_bounded_pc_tree_finds_large_rigid_c_tree_witness_without_shortcut():
    D = _plateau_cycle_metric(9)
    T = _rigid_c_tree(9)

    assert enumerate_frontiers(T, canonical=True) == [tuple(range(9))]
    assert _minimum_distance_cycle_order(D, 9) is None
    assert _paired_farthest_order(D, 9) is None
    result = solve(D, pc_tree=T)

    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_pc_tree_frontiers"
    assert result["frontier_count"] == 1
    assert result["frontiers_enumerated"] == 1
    assert result["frontier_limit"] == EXACT_PC_TREE_FRONTIER_LIMIT
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_exact_bounded_pc_tree_proves_large_rigid_negative():
    D = _extended_non_cr_four_point_instance(9)
    T = _rigid_c_tree(9)
    natural = tuple(range(9))

    assert enumerate_frontiers(T, canonical=True) == [natural]
    assert not is_precircular_order_cR(D, natural)
    result = solve(D, pc_tree=T)

    assert result["exists"] is False
    assert result["order"] is None
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_pc_tree_frontiers"
    assert result["frontier_count"] == 1


def test_candidate_low_hub_strong_ordering_recovers_large_star_witness_missed_by_sampling():
    D = _extended_non_cr_four_point_instance(9)
    T = star_pc_tree(9)
    sampled = enumerate_frontiers(T, canonical=True, limit=64)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert len(sampled) == 64
    assert not any(is_precircular_order_cR(D, order) for order in sampled)
    assert any(is_precircular_order_cR(D, order) for order in all_circular_orders(9))

    result = solve(D, pc_tree=T)
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_low_hub_strong_ordering_witness"
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_finds_large_permuted_cycle_witness_in_star_tree():
    D = permuted_cycle_metric(14, rng=random.Random(7))
    result = solve(D, pc_tree=star_pc_tree(14))
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_minimum_distance_cycle_witness"
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_finds_large_cycle_witness_in_representing_balanced_tree():
    D = cycle_metric(14)
    T = balanced_pc_tree(14, kind="mixed")
    result = solve(D, pc_tree=T)
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_minimum_distance_cycle_witness"
    assert is_precircular_order_cR(D, result["order"])
    assert represents_order(T, result["order"])


def test_candidate_finds_represented_cycle_witness_outside_sample_budget():
    order = (0, 1, 2, 3, 4, 6, 7, 8, 5, 9)
    D = _cycle_metric_for_order(order)
    T = p_node([p_node([leaf(0), leaf(1)]), *[leaf(i) for i in range(2, 10)]])
    sampled = set(enumerate_frontiers(T, canonical=True, limit=64))
    assert canonical_circular_order(order) not in sampled
    result = solve(D, pc_tree=T)
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_minimum_distance_cycle_witness"
    assert result["order"] == list(order)
    assert represents_order(T, result["order"])


def test_candidate_does_not_use_minimum_cycle_witness_when_not_represented():
    D = permuted_cycle_metric(14, rng=random.Random(11))
    T = balanced_pc_tree(14, kind="mixed")
    order = _minimum_distance_cycle_order(D, 14)
    assert order is not None
    assert not represents_order(T, order)
    result = solve(D, pc_tree=T)
    assert result["solver"] != "candidate_minimum_distance_cycle_witness"


def test_candidate_does_not_bypass_explicit_quasi_orders_with_pc_tree():
    D = cycle_metric(10)
    T = balanced_pc_tree(10, kind="mixed")
    bad_first_orders = [(0, 2, 4, 6, 8, 1, 3, 5, 7, 9)]
    result = solve(D, quasi_orders=bad_first_orders, pc_tree=T)
    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"


def test_candidate_finds_large_paired_farthest_witness_in_star_tree():
    D = paired_farthest_matching(20, rng=random.Random(5))
    order = _paired_farthest_order(D, 20)
    assert order is not None
    result = solve(D, pc_tree=star_pc_tree(20))
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_paired_farthest_matching_witness"
    assert result["order"] == list(order)
    assert is_precircular_order_cR(D, result["order"])


def test_paired_farthest_constructed_witness_is_cr_on_small_seeded_instances():
    for n in range(4, 13):
        for seed in range(3):
            D = paired_farthest_matching(n, rng=random.Random(seed))
            order = _paired_farthest_order(D, n)
            assert order is not None
            assert is_precircular_order_cR(D, order)


def test_paired_farthest_witness_handles_neutral_point():
    D = paired_farthest_matching(21, rng=random.Random(8))
    order = _paired_farthest_order(D, 21)
    assert order is not None
    result = solve(D, pc_tree=star_pc_tree(21))
    assert result["solver"] == "candidate_paired_farthest_matching_witness"
    assert result["order"] == list(order)
    assert is_precircular_order_cR(D, result["order"])


def test_paired_farthest_detector_rejects_perturbed_side_clique():
    D = paired_farthest_matching(12, rng=random.Random(6))
    order = _paired_farthest_order(D, 12)
    assert order is not None
    a, b = order[0], order[1]
    D[a][b] = D[b][a] = 2
    assert _paired_farthest_order(D, 12) is None


def test_candidate_does_not_bypass_explicit_quasi_orders_for_paired_farthest():
    D = paired_farthest_matching(10, rng=random.Random(5))
    bad_order = tuple(range(10))
    assert not is_precircular_order_cR(D, bad_order)
    result = solve(D, quasi_orders=[bad_order], pc_tree=star_pc_tree(10))
    assert result["exists"] is False
    assert result["complete"] is True
    assert result["solver"] == "candidate_exact_bounded_quasi_orders"


def test_minimum_cycle_candidate_is_only_a_verified_witness():
    D = [
        [0, 1, 2, 2, 2, 1],
        [1, 0, 1, 2, 2, 3],
        [2, 1, 0, 1, 2, 2],
        [2, 2, 1, 0, 1, 3],
        [2, 2, 2, 1, 0, 1],
        [1, 3, 2, 3, 1, 0],
    ]
    order = _minimum_distance_cycle_order(D, 6)
    assert order == (0, 1, 2, 3, 4, 5)
    assert not is_precircular_order_cR(D, order)
