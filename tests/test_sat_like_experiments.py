import itertools
import random

from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point, random_dissimilarity
from pc_circular.pc_tree import balanced_pc_tree, c_node, enumerate_frontiers, leaf, p_node, star_pc_tree
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR, is_quasi_circular_order
from pc_circular.solvers.sat_like_experiments import (
    accepted_frontiers_by_csp,
    assignment_frontier_report,
    build_local_domains,
    frontier_from_assignment,
    prop45_nogood_frontier_report,
    prop45_nogood_frontier_search,
    solve_nogood_csp,
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


def test_local_domain_assignment_frontiers_match_pc_tree_enumeration():
    trees = [
        star_pc_tree(4),
        balanced_pc_tree(6, kind="mixed"),
        c_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)]), leaf(4)]),
    ]

    for T in trees:
        report = assignment_frontier_report(T, max_p_degree=4)
        assert report["complete"]
        assert not report["encoding"]["unsupported"]
        assert set(report["frontiers"]) == set(enumerate_frontiers(T, canonical=True))


def test_frontier_from_assignment_reconstructs_expected_order():
    T = c_node([p_node([leaf(0), leaf(1)]), leaf(2), leaf(3)])
    assignment = {
        (): (2, 1, 0),
        (0,): (1, 0),
    }

    assert frontier_from_assignment(T, assignment) == (3, 2, 1, 0)


def test_cr_source_csp_matches_exact_frontier_filter():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260522))

    expected = {
        order
        for order in enumerate_frontiers(T, canonical=True)
        if is_precircular_order_cR(D, order)
    }
    actual = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)

    assert actual == expected


def test_local_domain_csp_reports_unsupported_large_p_without_false_decision():
    T = star_pc_tree(5)
    D = cycle_metric(5)
    encoding = build_local_domains(T, max_p_degree=3)
    result = solve_nogood_csp(D, T, source="cr", max_p_degree=3)

    assert encoding["unsupported"]
    assert result["unsupported"]
    assert result["exists"] is None
    assert not result["complete"]
    assert result["order"] is None
