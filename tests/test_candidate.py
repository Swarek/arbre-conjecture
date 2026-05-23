import random

from pc_circular.generators import (
    cycle_metric,
    equal_distance_instance,
    paired_farthest_matching,
    permuted_cycle_metric,
    quasi_circular_not_circular_four_point,
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
    _minimum_distance_cycle_order,
    _paired_farthest_order,
    _pc_tree_frontier_upper_bound,
    solve,
)


def _one_high_edge_instance(n):
    D = equal_distance_instance(n)
    D[0][1] = D[1][0] = 2
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


def test_candidate_universal_subcase_uses_first_quasi_order():
    D = _one_high_edge_instance(10)
    result = solve(D, quasi_orders=[(9, 8, 7, 6, 5, 4, 3, 2, 1, 0)])
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["order"] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    assert is_precircular_order_cR(D, result["order"])


def test_candidate_non_constant_large_instance_remains_incomplete_placeholder():
    D = cycle_metric(10)
    bad_first_orders = [(0, 2, 4, 6, 8, 1, 3, 5, 7, 9)]
    result = solve(D, quasi_orders=bad_first_orders)
    assert result["exists"] is False
    assert result["complete"] is False


def test_candidate_marks_sampled_positive_witness_complete():
    D = cycle_metric(10)
    result = solve(D, quasi_orders=[tuple(range(10))])
    assert result["exists"] is True
    assert result["complete"] is True
    assert result["solver"] == "candidate_validated_sampled_witness"
    assert is_precircular_order_cR(D, result["order"])


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


def test_candidate_exact_bounded_pc_tree_skips_large_star_frontier_space_without_false_negative():
    D = _extended_non_cr_four_point_instance(9)
    T = star_pc_tree(9)
    sampled = enumerate_frontiers(T, canonical=True, limit=64)

    assert _pc_tree_frontier_upper_bound(T) > EXACT_PC_TREE_FRONTIER_LIMIT
    assert len(sampled) == 64
    assert not any(is_precircular_order_cR(D, order) for order in sampled)
    assert any(is_precircular_order_cR(D, order) for order in all_circular_orders(9))

    result = solve(D, pc_tree=T)
    assert result["exists"] is False
    assert result["complete"] is False
    assert result["solver"] == "candidate_large_n_placeholder"
    assert result["tried_orders"] == 64


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
    assert result["complete"] is False
    assert result["solver"] == "candidate_large_n_placeholder"


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
    assert result["complete"] is False
    assert result["solver"] == "candidate_large_n_placeholder"


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
