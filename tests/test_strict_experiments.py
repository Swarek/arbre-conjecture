import itertools

import pytest

from pc_circular.generators import cycle_metric, equal_distance_instance
from pc_circular.oracle import exact_oracle_pc_tree
from pc_circular.pc_tree import balanced_pc_tree, c_node, leaf, p_node, represents_order, star_pc_tree
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    find_strict_precircular_cR_violation,
    find_strict_quasi_circular_violation,
    is_quasi_circular_order,
    is_precircular_order_cR,
    is_robinson_linear,
    is_strict_circular_robinson_order,
    is_strict_precircular_order_cR,
    is_strict_quasi_circular_order,
    is_strict_robinson_linear,
)
from pc_circular.solvers.candidate import _minimum_distance_cycle_order, _paired_farthest_order
from pc_circular.solvers.strict_experiments import (
    strict_algorithm52_report,
    strict_ball_circular_ones_report,
    strict_order_report,
)


def test_strict_linear_robinson_rejects_equalities():
    D = [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ]
    assert is_robinson_linear(D, (0, 1, 2))
    assert not is_strict_robinson_linear(D, (0, 1, 2))


def test_strict_precircular_and_quasi_reject_equal_distance():
    D = equal_distance_instance(4)
    order = (0, 1, 2, 3)

    assert is_precircular_order_cR(D, order)
    assert not is_strict_precircular_order_cR(D, order)
    assert not is_strict_quasi_circular_order(D, order)
    assert find_strict_precircular_cR_violation(D, order)["quadruple"] == (0, 1, 2, 3)
    assert find_strict_quasi_circular_violation(D, order)["quadruple"] == (0, 1, 2, 3)


def test_strict_quasi_does_not_imply_strict_precircular_fig_2_2():
    D = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]

    assert is_strict_quasi_circular_order(D, (0, 1, 2, 3))
    assert not is_strict_precircular_order_cR(D, (0, 1, 2, 3))
    assert not is_strict_circular_robinson_order(D, (0, 1, 2, 3))
    assert find_strict_precircular_cR_violation(D, (0, 1, 2, 3))["quadruple"] == (0, 1, 2, 3)

    assert is_strict_quasi_circular_order(D, (0, 1, 3, 2))
    assert is_strict_precircular_order_cR(D, (0, 1, 3, 2))
    assert is_strict_circular_robinson_order(D, (0, 1, 3, 2))


def test_cycle_metric_has_unique_strict_order_modulo_reversal():
    D = cycle_metric(6)
    order = (0, 1, 2, 3, 4, 5)

    assert is_strict_quasi_circular_order(D, order)
    assert is_strict_precircular_order_cR(D, order)
    assert is_strict_circular_robinson_order(D, order)

    report = strict_order_report(D, star_pc_tree(6))
    assert report["complete"] is True
    assert report["order_count"] == 60
    assert report["strict_quasi_count"] == 1
    assert report["strict_precircular_count"] == 1
    assert report["strict_circular_count"] == 1
    assert report["strict_circular_witness"] == order


def test_strict_report_marks_large_instances_incomplete():
    report = strict_order_report(cycle_metric(9), max_n=8)
    assert report["complete"] is False
    assert report["reason"] == "n exceeds strict_order_report max_n"


def test_algorithm52_report_recovers_cycle_metric_strict_order():
    D = cycle_metric(6)
    report = strict_algorithm52_report(D)

    assert report["complete"] is True
    assert report["strict_quasi_orders"] == [(0, 1, 2, 3, 4, 5)]
    assert report["strict_precircular_orders"] == [(0, 1, 2, 3, 4, 5)]
    assert report["strict_circular_orders"] == [(0, 1, 2, 3, 4, 5)]


def test_algorithm52_report_handles_fig_2_2_quasi_vs_circular_split():
    D = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]
    report = strict_algorithm52_report(D)

    assert report["complete"] is True
    assert set(report["strict_quasi_orders"]) == {(0, 1, 2, 3), (0, 1, 3, 2)}
    assert report["strict_circular_orders"] == [(0, 1, 3, 2)]


def test_algorithm52_report_finds_strict_positive_outside_existing_witness_families():
    D = [
        [0, 3, 1, 3, 1],
        [3, 0, 2, 2, 3],
        [1, 2, 0, 3, 3],
        [3, 2, 3, 0, 1],
        [1, 3, 3, 1, 0],
    ]

    assert _minimum_distance_cycle_order(D, 5) is None
    assert _paired_farthest_order(D, 5) is None
    assert strict_algorithm52_report(D)["strict_circular_orders"] == [(0, 2, 1, 3, 4)]


def test_ball_circular_ones_report_matches_cycle_metric_counts():
    report = strict_ball_circular_ones_report(cycle_metric(6), star_pc_tree(6))

    assert report["complete"] is True
    assert report["ball_arc_count"] == 1
    assert report["quasi_count"] == 1
    assert report["strict_quasi_count"] == 1
    assert report["strict_circular_count"] == 1
    assert report["first_ball_quasi_mismatch"] is None
    assert report["strict_circular_witness"] == (0, 1, 2, 3, 4, 5)


def test_ball_circular_ones_report_separates_quasi_from_circular_fig_2_2():
    D = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]
    report = strict_ball_circular_ones_report(D)

    assert report["first_ball_quasi_mismatch"] is None
    assert set(report["ball_arc_orders"]) == {(0, 1, 2, 3), (0, 1, 3, 2)}
    assert set(report["strict_quasi_orders"]) == {(0, 1, 2, 3), (0, 1, 3, 2)}
    assert report["strict_circular_orders"] == [(0, 1, 3, 2)]


def test_ball_circular_ones_report_records_random_quasi_not_cr_counterexample():
    D = [
        [0, 2, 1, 2, 3, 1],
        [2, 0, 1, 3, 1, 2],
        [1, 1, 0, 3, 1, 3],
        [2, 3, 3, 0, 1, 1],
        [3, 1, 1, 1, 0, 1],
        [1, 2, 3, 1, 1, 0],
    ]
    order = (0, 2, 1, 4, 3, 5)
    report = strict_ball_circular_ones_report(D, star_pc_tree(6))

    assert order in report["ball_arc_orders"]
    assert order in report["quasi_orders"]
    assert not is_precircular_order_cR(D, order)
    assert report["ball_arc_count"] == 1
    assert report["precircular_count"] == 0
    assert report["strict_circular_count"] == 0


def test_ball_circular_ones_report_does_not_confuse_non_strict_equalities():
    report = strict_ball_circular_ones_report(equal_distance_instance(4))

    assert report["counts"]["ball_arc"] == 3
    assert report["exists"]["strict_circular"] is False
    assert report["ball_arc_count"] == 3
    assert report["quasi_count"] == 3
    assert report["precircular_count"] == 3
    assert report["strict_quasi_count"] == 0
    assert report["strict_circular_count"] == 0
    assert report["module_count"] == 1
    assert report["modules"][0]["labels"] == (0, 1, 2, 3)


def test_ball_circular_ones_module_signature_uses_exact_ball_membership():
    report = strict_ball_circular_ones_report(cycle_metric(4))

    assert report["ball_count"] == 4
    assert report["module_count"] == 4
    assert {module["labels"] for module in report["modules"]} == {(0,), (1,), (2,), (3,)}
    assert {module["signature_weight"] for module in report["modules"]} == {3}
    assert len({module["signature"] for module in report["modules"]}) == 4


def test_strict_witness_must_be_represented_by_pc_tree():
    D = [
        [0, 2, 1, 1],
        [2, 0, 1, 1],
        [1, 1, 0, 2],
        [1, 1, 2, 0],
    ]
    order = (0, 2, 1, 3)
    T = balanced_pc_tree(4, kind="C")

    assert is_strict_circular_robinson_order(D, order)
    assert not represents_order(T, order)
    assert exact_oracle_pc_tree(D, T)["exists"] is False
    assert strict_order_report(D, T)["strict_circular_count"] == 0

    unrestricted = strict_algorithm52_report(D)
    represented = strict_algorithm52_report(D, T)
    assert canonical_circular_order(order) in unrestricted["strict_circular_orders"]
    assert represented["strict_circular_count"] == 0
    assert represented["unrepresented_strict_circular_count"] >= 1

    ball_report = strict_ball_circular_ones_report(D, T)
    assert ball_report["strict_circular_count"] == 0
    assert canonical_circular_order(order) not in ball_report["strict_circular_orders"]


def test_ball_circular_ones_report_marks_large_instances_incomplete():
    report = strict_ball_circular_ones_report(cycle_metric(9), max_n=8)

    assert report["complete"] is False
    assert report["reason"] == "n exceeds strict_ball_circular_ones_report max_n"
    assert report["ball_count"] > 0
    assert report["exists"]["strict_circular"] is None


def test_ball_circular_ones_report_validates_pc_tree_labels():
    with pytest.raises(ValueError, match="pc_tree labels"):
        strict_ball_circular_ones_report(cycle_metric(4), c_node([leaf(0), leaf(1), leaf(2), leaf(4)]))


def test_ball_circular_ones_report_checks_nested_tree_representation_sanity():
    T = c_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)]), leaf(4)])
    report = strict_ball_circular_ones_report(cycle_metric(5), T)

    assert report["complete"] is True
    assert report["order_source"] == "pc_tree_frontiers"
    assert report["counts"]["representation_mismatch"] == 0
    assert report["first_representation_mismatch"] is None


def test_strict_circular_implies_strict_precircular_on_n4_values():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        for order in all_circular_orders(n):
            if is_strict_circular_robinson_order(D, order):
                checked += 1
                assert is_strict_precircular_order_cR(D, order)
                assert is_strict_quasi_circular_order(D, order)
    assert checked > 0


def test_strict_precircular_matches_strict_circular_arc_definition_n4_values():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        for order in all_circular_orders(n):
            checked += 1
            assert is_strict_circular_robinson_order(D, order) is is_strict_precircular_order_cR(D, order)
    assert checked == 2187


def test_algorithm52_report_matches_exact_strict_orders_n4_values():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        exact_quasi = {order for order in all_circular_orders(n) if is_strict_quasi_circular_order(D, order)}
        exact_circular = {order for order in all_circular_orders(n) if is_strict_circular_robinson_order(D, order)}
        report = strict_algorithm52_report(D)
        assert report["complete"] is True
        assert set(report["strict_quasi_orders"]) == exact_quasi
        assert set(report["strict_circular_orders"]) == exact_circular
        checked += 1
    assert checked == 729


def test_ball_circular_ones_report_matches_quasi_definition_n4_values():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        exact_quasi = {order for order in all_circular_orders(n) if is_quasi_circular_order(D, order)}
        exact_strict_quasi = {order for order in all_circular_orders(n) if is_strict_quasi_circular_order(D, order)}
        exact_strict_circular = {order for order in all_circular_orders(n) if is_strict_circular_robinson_order(D, order)}
        report = strict_ball_circular_ones_report(D)
        assert report["complete"] is True
        assert set(report["ball_arc_orders"]) == exact_quasi
        assert set(report["quasi_orders"]) == exact_quasi
        assert set(report["strict_quasi_orders"]) == exact_strict_quasi
        assert set(report["strict_circular_orders"]) == exact_strict_circular
        assert report["first_ball_quasi_mismatch"] is None
        checked += 1
    assert checked == 729
