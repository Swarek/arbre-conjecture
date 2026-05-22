import random

from pc_circular.generators import cycle_metric, equal_distance_instance, permuted_cycle_metric
from pc_circular.pc_tree import (
    balanced_pc_tree,
    enumerate_frontiers,
    leaf,
    p_node,
    represents_order,
    sample_frontier,
    star_pc_tree,
)
from pc_circular.predicates import canonical_circular_order, is_precircular_order_cR
from pc_circular.solvers.candidate import _minimum_distance_cycle_order, solve


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
