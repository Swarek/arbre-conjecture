import itertools

from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point
from pc_circular.predicates import (
    all_circular_orders,
    farthest_sets,
    find_farthest_crossing_violation,
    find_farthest_prop_4_4_violation,
    find_farthest_prop_4_5_obstruction,
    find_bad_side_precircular_cR_violation,
    find_precircular_cR_violation,
    has_at_most_one_bad_witness_per_pair,
    is_constant_off_diagonal,
    is_precircular_order_cR,
    is_quasi_circular_order,
    passes_bad_side_precircular_cR,
    passes_farthest_crossing_condition,
    passes_farthest_prop_4_4_condition,
    passes_farthest_prop_4_5_order_test,
)


def test_all_circular_orders_counts_mod_rotation_and_reversal():
    assert len(list(all_circular_orders(1))) == 1
    assert len(list(all_circular_orders(2))) == 1
    assert len(list(all_circular_orders(4))) == 3
    assert len(list(all_circular_orders(5))) == 12


def test_cycle_metric_is_circular_robinson_in_cycle_order():
    D = cycle_metric(6)
    assert is_precircular_order_cR(D, (0, 1, 2, 3, 4, 5))


def test_constant_off_diagonal_predicate_handles_equalities():
    assert is_constant_off_diagonal([[0]])
    assert is_constant_off_diagonal([[0, 7], [7, 0]])
    assert is_constant_off_diagonal(
        [
            [0, 2, 2],
            [2, 0, 2],
            [2, 2, 0],
        ]
    )
    assert not is_constant_off_diagonal(
        [
            [0, 2, 3],
            [2, 0, 2],
            [3, 2, 0],
        ]
    )


def test_single_bad_witness_bound_is_stronger_than_constant_case():
    D = [
        [0, 2, 1, 1],
        [2, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
    ]
    assert not is_constant_off_diagonal(D)
    assert has_at_most_one_bad_witness_per_pair(D)
    for order in all_circular_orders(4):
        assert is_precircular_order_cR(D, order)


def test_single_bad_witness_bound_rejects_low_edge_counterexample():
    D = [
        [0, 2, 1, 2],
        [2, 0, 2, 2],
        [1, 2, 0, 2],
        [2, 2, 2, 0],
    ]
    assert not has_at_most_one_bad_witness_per_pair(D)
    assert not is_precircular_order_cR(D, (0, 1, 2, 3))


def test_four_point_order_can_be_quasi_circular_but_not_circular_robinson():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    assert is_quasi_circular_order(D, order)
    assert not is_precircular_order_cR(D, order)
    assert find_precircular_cR_violation(D, order)["quadruple"] == (0, 1, 2, 3)
    assert not passes_bad_side_precircular_cR(D, order)
    assert find_bad_side_precircular_cR_violation(D, order)["quadruple"] == (0, 1, 2, 3)


def test_bad_side_precircular_matches_quadruple_definition_on_exhaustive_n4():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        for order in all_circular_orders(n):
            checked += 1
            assert passes_bad_side_precircular_cR(D, order) is is_precircular_order_cR(D, order)
            assert (find_bad_side_precircular_cR_violation(D, order) is None) is (
                find_precircular_cR_violation(D, order) is None
            )
    assert checked == 2187


def test_bad_side_precircular_keeps_equalities_non_strict():
    D = [[0 if i == j else 1 for j in range(6)] for i in range(6)]
    order = (0, 1, 2, 3, 4, 5)

    assert is_precircular_order_cR(D, order)
    assert passes_bad_side_precircular_cR(D, order)
    assert find_bad_side_precircular_cR_violation(D, order) is None


def test_bad_side_precircular_detects_wrapping_rotations_and_reversal():
    D = quasi_circular_not_circular_four_point()
    base = (0, 1, 2, 3)
    variants = []
    for order in (base, tuple(reversed(base))):
        for cut in range(len(order)):
            variants.append(order[cut:] + order[:cut])

    for order in variants:
        assert not is_precircular_order_cR(D, order)
        assert not passes_bad_side_precircular_cR(D, order)
        assert find_bad_side_precircular_cR_violation(D, order) is not None


def test_bad_side_precircular_accepts_two_bad_witnesses_on_same_side():
    D = [
        [0, 2, 1, 1, 1],
        [2, 0, 3, 1, 1],
        [1, 3, 0, 2, 1],
        [1, 1, 2, 0, 1],
        [1, 1, 1, 1, 0],
    ]
    order = (0, 2, 4, 1, 3)

    assert is_precircular_order_cR(D, order)
    assert passes_bad_side_precircular_cR(D, order)
    assert find_bad_side_precircular_cR_violation(D, order) is None


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


def test_prop_4_5_finds_obstruction_for_quasi_circular_non_cr_order():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    assert is_quasi_circular_order(D, order)
    assert not is_precircular_order_cR(D, order)
    obstruction = find_farthest_prop_4_5_obstruction(D, order)
    assert obstruction is not None
    assert obstruction["pattern"] in {"x_xp_y_yp", "x_yp_y_xp"}
    assert not passes_farthest_prop_4_5_order_test(D, order)


def test_prop_4_5_has_no_obstruction_for_cycle_metric_order():
    D = cycle_metric(6)
    order = (0, 1, 2, 3, 4, 5)
    assert is_quasi_circular_order(D, order)
    assert is_precircular_order_cR(D, order)
    assert find_farthest_prop_4_5_obstruction(D, order) is None
    assert passes_farthest_prop_4_5_order_test(D, order)


def test_prop_4_5_matches_cr_on_exhaustive_quasi_circular_orders_n4():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked_quasi = 0
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        for order in all_circular_orders(n):
            if not is_quasi_circular_order(D, order):
                continue
            checked_quasi += 1
            assert passes_farthest_prop_4_5_order_test(D, order) is is_precircular_order_cR(D, order)
    assert checked_quasi == 1134
