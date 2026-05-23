import itertools

from pc_circular.generators import cycle_metric
from pc_circular.pc_tree import balanced_pc_tree, enumerate_frontiers, star_pc_tree
from pc_circular.pc_tree_learning import find_scaffold_pc_representation
from pc_circular.predicates import all_circular_orders, passes_bad_side_precircular_cR
from tools.pc_cr_pc_representability_probe import run_cr_pc_representability_probe


def test_scaffold_pc_learner_recovers_star_family():
    orders = list(all_circular_orders(5))

    report = find_scaffold_pc_representation(range(5), orders)

    assert report.complete
    assert report.representable
    assert report.target_size == 12
    assert report.all_order_count == 12
    assert report.witness is not None


def test_scaffold_pc_learner_recovers_single_c_order_family():
    order = next(iter(all_circular_orders(5)))

    report = find_scaffold_pc_representation(range(5), [order])

    assert report.complete
    assert report.representable
    assert report.target_size == 1
    assert report.witness is not None


def test_scaffold_pc_learner_recovers_existing_tree_family():
    T = balanced_pc_tree(5, kind="mixed")
    frontiers = enumerate_frontiers(T, canonical=True)

    report = find_scaffold_pc_representation(range(5), frontiers)

    assert report.complete
    assert report.representable
    assert report.target_size == len(frontiers)


def test_scaffold_pc_learner_marks_empty_target_separately():
    report = find_scaffold_pc_representation(range(4), [])

    assert report.complete
    assert not report.representable
    assert report.empty_target
    assert report.target_size == 0


def test_cr_pc_representability_probe_smoke():
    report = run_cr_pc_representability_probe(
        sizes=[4],
        instance_kinds=["cycle", "equal", "random"],
        repeats=1,
        max_families_per_subset=2000,
        seed=20260630,
    )

    assert report["summary"]["rows"] == 3
    assert report["summary"]["complete_rows"] == 3
    assert report["summary"]["incomplete_rows"] == 0
    assert report["summary"]["representable_rows"] >= 1


def test_cycle_metric_cr_orders_are_scaffold_pc_representable_small():
    D = cycle_metric(5)
    cr_orders = [
        order for order in all_circular_orders(5) if passes_bad_side_precircular_cR(D, order)
    ]

    report = find_scaffold_pc_representation(range(5), cr_orders)

    assert cr_orders
    assert report.complete
    assert report.representable


def test_no_nontrivial_scaffold_pc_counterexample_exhaustive_n4_values_123():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value
        cr_orders = [
            order for order in all_circular_orders(n) if passes_bad_side_precircular_cR(D, order)
        ]
        report = find_scaffold_pc_representation(range(n), cr_orders)
        assert report.complete
        assert report.representable or report.empty_target


def test_paired_farthest_n5_gives_nontrivial_scaffold_pc_counterexample():
    D = [
        [0, 1, 2, 3, 1],
        [1, 0, 3, 2, 1],
        [2, 3, 0, 1, 1],
        [3, 2, 1, 0, 1],
        [1, 1, 1, 1, 0],
    ]
    cr_orders = [
        order for order in all_circular_orders(5) if passes_bad_side_precircular_cR(D, order)
    ]

    report = find_scaffold_pc_representation(range(5), cr_orders)

    assert cr_orders == [(0, 1, 3, 2, 4), (0, 1, 4, 3, 2)]
    assert report.complete
    assert not report.representable
    assert not report.empty_target


def test_star_frontier_set_is_the_same_as_all_orders_sanity():
    frontiers = set(enumerate_frontiers(star_pc_tree(5), canonical=True))
    assert frontiers == set(all_circular_orders(5))
