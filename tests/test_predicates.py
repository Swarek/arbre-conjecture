from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point
from pc_circular.predicates import (
    all_circular_orders,
    farthest_sets,
    find_farthest_crossing_violation,
    find_precircular_cR_violation,
    is_precircular_order_cR,
    is_quasi_circular_order,
    passes_farthest_crossing_condition,
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
