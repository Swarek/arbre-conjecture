import itertools
import random

from pc_circular.generators import (
    cycle_metric,
    equal_distance_instance,
    quasi_circular_not_circular_four_point,
    random_dissimilarity,
)
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR
from pc_circular.solvers.dp_experiments import (
    bad_side_signature,
    bad_witnesses_by_pair,
    find_bad_side_cr_violation,
    is_bad_witness,
    passes_bad_side_cr_test,
)


def _matrix_from_pair_values(n, values):
    D = [[0] * n for _ in range(n)]
    for (i, j), value in zip(itertools.combinations(range(n), 2), values):
        D[i][j] = D[j][i] = value
    return D


def test_bad_witnesses_keep_equal_distance_non_strict_case_clean():
    D = equal_distance_instance(5)
    assert all(not witnesses for witnesses in bad_witnesses_by_pair(D).values())
    assert passes_bad_side_cr_test(D, (0, 1, 2, 3, 4))
    assert bad_side_signature(D, (0, 1, 2, 3, 4))[(0, 2)] == {
        "a_to_b": (),
        "b_to_a": (),
    }


def test_bad_side_detects_known_quasi_circular_non_cr_order():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    violation = find_bad_side_cr_violation(D, order)
    assert violation is not None
    assert violation["pair"] == (0, 2)
    assert violation["quadruple"] == (0, 1, 2, 3)
    assert violation["lhs"] < violation["rhs"]
    assert not passes_bad_side_cr_test(D, order)


def test_cycle_metric_order_has_no_bad_side_violation():
    D = cycle_metric(6)
    order = (0, 1, 2, 3, 4, 5)
    assert is_precircular_order_cR(D, order)
    assert passes_bad_side_cr_test(D, order)


def test_is_bad_witness_uses_strict_inequality_for_equalities():
    D = [
        [0, 2, 2, 1],
        [2, 0, 2, 1],
        [2, 2, 0, 1],
        [1, 1, 1, 0],
    ]
    assert not is_bad_witness(D, 0, 1, 2)
    assert not is_bad_witness(D, 0, 1, 3)
    assert is_bad_witness(D, 0, 3, 1)


def test_bad_side_matches_precircular_cr_on_exhaustive_n4():
    n = 4
    pair_count = n * (n - 1) // 2
    for values in itertools.product((1, 2, 3), repeat=pair_count):
        D = _matrix_from_pair_values(n, values)
        for order in all_circular_orders(n):
            assert passes_bad_side_cr_test(D, order) is is_precircular_order_cR(D, order)


def test_bad_side_matches_precircular_cr_on_random_small_orders():
    rng = random.Random(20260523)
    for n in (5, 6):
        orders = list(all_circular_orders(n))
        for _ in range(20):
            D = random_dissimilarity(n, rng=rng, values=(1, 2, 3, 4))
            for order in orders:
                assert passes_bad_side_cr_test(D, order) is is_precircular_order_cR(D, order)
