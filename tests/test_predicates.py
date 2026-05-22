from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point
from pc_circular.predicates import (
    all_circular_orders,
    farthest_sets,
    find_farthest_crossing_violation,
    find_farthest_prop_4_4_violation,
    find_precircular_cR_violation,
    is_precircular_order_cR,
    is_quasi_circular_order,
    passes_farthest_crossing_condition,
    passes_farthest_prop_4_4_condition,
)


def test_all_circular_orders_counts_mod_rotation_and_reversal():
    assert len(list(all_circular_orders(1))) == 1
    assert len(list(all_circular_orders(2))) == 1
    assert len(list(all_circular_orders(4))) == 3
    assert len(list(all_circular_orders(5))) == 12


def test_cycle_metric_is_circular_robinson_in_cycle_order():
    D = cycle_metric(6)
    assert is_precircular_order_cR(D, (0, 1, 2, 3, 4, 5))


def test_four_point_order_can_be_quasi_circular_but_not_circular_robinson():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    assert is_quasi_circular_order(D, order)
    assert not is_precircular_order_cR(D, order)
    assert find_precircular_cR_violation(D, order)["quadruple"] == (0, 1, 2, 3)


def test_farthest_sets_and_crossing_condition_on_square_cycle():
    D = cycle_metric(4)
    assert farthest_sets(D) == {0: {2}, 1: {3}, 2: {0}, 3: {1}}
    assert passes_farthest_crossing_condition(D, (0, 1, 2, 3))
    assert find_farthest_crossing_violation(D, (0, 1, 2, 3)) is None
    assert passes_farthest_prop_4_4_condition(D, (0, 1, 2, 3))


def test_prop_4_4_keeps_non_strict_degeneracy_clause_separate():
    D = [
        [0, 1, 1, 1],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
    ]
    order = (0, 1, 2, 3)
    assert is_precircular_order_cR(D, order)
    assert not passes_farthest_crossing_condition(D, order)
    assert passes_farthest_prop_4_4_condition(D, order)
    assert find_farthest_prop_4_4_violation(D, order) is None


def test_prop_4_4_is_stronger_than_crude_crossing_on_strict_counterexample():
    D = [
        [0, 1, 2, 3],
        [1, 0, 4, 5],
        [2, 4, 0, 6],
        [3, 5, 6, 0],
    ]
    order = (0, 1, 2, 3)
    assert not is_precircular_order_cR(D, order)
    assert passes_farthest_crossing_condition(D, order)
    assert not passes_farthest_prop_4_4_condition(D, order, strict=True)


def test_prop_4_4_is_not_sufficient_without_quasi_circularity():
    D = [
        [0, 1, 1, 1],
        [1, 0, 1, 2],
        [1, 1, 0, 2],
        [1, 2, 2, 0],
    ]
    order = (0, 1, 3, 2)
    assert not is_quasi_circular_order(D, order)
    assert not is_precircular_order_cR(D, order)
    assert passes_farthest_prop_4_4_condition(D, order)
