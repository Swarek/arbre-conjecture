import itertools

from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point
from pc_circular.pc_tree import star_pc_tree
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR, is_quasi_circular_order
from pc_circular.solvers.sat_like_experiments import (
    prop45_nogood_frontier_report,
    prop45_nogood_frontier_search,
)


def test_prop45_nogood_report_rejects_single_bad_quasi_order():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    report = prop45_nogood_frontier_report(D, quasi_orders=[order])

    assert report["complete"]
    assert report["counts"]["frontiers_seen"] == 1
    assert report["counts"]["checked_orders"] == 1
    assert report["counts"]["prop45_fail"] == 1
    assert report["counts"]["exact_non_cr"] == 1
    assert not report["prop45_exists"]
    assert not report["has_disagreement"]
    assert report["first_rejected"]["order"] == list(order)


def test_prop45_nogood_search_finds_cycle_metric_witness_in_star_tree():
    D = cycle_metric(5)
    result = prop45_nogood_frontier_search(D, pc_tree=star_pc_tree(5))

    assert result["exists"]
    assert result["complete"]
    assert result["order"] is not None
    assert result["report"]["exact_cr_exists"]
    assert not result["report"]["has_disagreement"]


def test_prop45_nogood_report_matches_exact_cr_on_quasi_frontiers_n4():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked_instances = 0

    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value

        quasi_orders = [
            order
            for order in all_circular_orders(n)
            if is_quasi_circular_order(D, order)
        ]
        if not quasi_orders:
            continue
        checked_instances += 1

        report = prop45_nogood_frontier_report(D, quasi_orders=quasi_orders)
        exact_exists = any(is_precircular_order_cR(D, order) for order in quasi_orders)

        assert not report["has_disagreement"]
        assert report["prop45_exists"] is exact_exists
        assert report["exact_cr_exists"] is exact_exists

    assert checked_instances == 657
