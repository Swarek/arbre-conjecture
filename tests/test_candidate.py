from pc_circular.generators import cycle_metric, equal_distance_instance
from pc_circular.pc_tree import balanced_pc_tree, sample_frontier, star_pc_tree
from pc_circular.predicates import is_precircular_order_cR
from pc_circular.solvers.candidate import solve


def _one_high_edge_instance(n):
    D = equal_distance_instance(n)
    D[0][1] = D[1][0] = 2
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
    result = solve(D, pc_tree=star_pc_tree(10))
    assert result["solver"] == "candidate_large_n_placeholder"
    assert result["complete"] is False
