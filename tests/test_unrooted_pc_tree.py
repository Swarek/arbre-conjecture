from pc_circular.predicates import all_circular_orders
from pc_circular.unrooted_pc_tree import find_unrooted_pc_representation
from tools.pc_unrooted_representability_probe import (
    T079_COUNTEREXAMPLE,
    run_unrooted_representability_probe,
)
from pc_circular.predicates import passes_bad_side_precircular_cR


def test_unrooted_pc_model_represents_all_orders_on_five_leaves():
    orders = list(all_circular_orders(5))

    report = find_unrooted_pc_representation(range(5), orders)

    assert report.complete
    assert report.representable
    assert report.witness is not None


def test_unrooted_pc_model_represents_single_order_on_five_leaves():
    order = next(iter(all_circular_orders(5)))

    report = find_unrooted_pc_representation(range(5), [order])

    assert report.complete
    assert report.representable
    assert report.witness is not None


def test_t079_counterexample_survives_tiny_unrooted_pc_model():
    cr_orders = [
        order
        for order in all_circular_orders(5)
        if passes_bad_side_precircular_cR(T079_COUNTEREXAMPLE, order)
    ]

    report = find_unrooted_pc_representation(range(5), cr_orders)

    assert cr_orders == [(0, 1, 3, 2, 4), (0, 1, 4, 3, 2)]
    assert report.complete
    assert not report.representable


def test_unrooted_probe_smoke():
    report = run_unrooted_representability_probe(max_candidates=500_000)

    assert report["summary"]["rows"] == 3
    assert report["summary"]["complete_rows"] == 3
    assert report["summary"]["t079_complete"]
    assert not report["summary"]["t079_representable"]
