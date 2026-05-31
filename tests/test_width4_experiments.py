from pc_circular.generators import equal_distance_instance, single_bad_side_quartet_instance
from pc_circular.pc_tree import leaf, p_node, star_pc_tree
from pc_circular.solvers.width4_experiments import (
    induced_child_circular_order,
    restrict_circular_order,
    pnode_width4_frontier_projection_report,
    width4_closure_from_orders,
)


def test_restrict_circular_order_is_canonical_under_rotation_and_reversal():
    subset = {0, 2, 4, 5}

    assert restrict_circular_order((0, 1, 2, 3, 4, 5), subset) == (0, 2, 4, 5)
    assert restrict_circular_order((2, 3, 4, 5, 0, 1), subset) == (0, 2, 4, 5)
    assert restrict_circular_order((5, 4, 3, 2, 1, 0), subset) == (0, 2, 4, 5)


def test_induced_child_circular_order_handles_circular_cut():
    child_label_sets = (frozenset({0, 1}), frozenset({2}), frozenset({3, 4}))

    order = (1, 2, 3, 4, 0)

    assert induced_child_circular_order(order, child_label_sets) == (0, 1, 2)


def test_width4_closure_detects_synthetic_non_closed_family():
    accepted = {
        (0, 1, 2, 3, 4),
        (0, 1, 2, 4, 3),
        (0, 1, 3, 4, 2),
    }

    report = width4_closure_from_orders(5, accepted)

    assert not report["width4_holds"]
    assert report["accepted_order_count"] == 3
    assert report["closure_order_count"] == 4
    assert report["missing_order_count"] == 1
    assert report["missing_order_examples"] == ((0, 1, 4, 3, 2),)


def test_width4_report_accepts_equal_distance_star_as_full_family():
    report = pnode_width4_frontier_projection_report(
        equal_distance_instance(5),
        star_pc_tree(5),
        frontier_limit=20,
    )
    root = report["nodes"][0]

    assert report["frontier_truncated"] is False
    assert report["accepted_frontier_count"] == 12
    assert report["tested_node_count"] == 1
    assert report["refuted_node_count"] == 0
    assert root["status"] == "holds"
    assert root["closure"]["candidate_order_count"] == 12
    assert root["closure"]["accepted_order_count"] == 12
    assert root["closure"]["closure_order_count"] == 12


def test_width4_report_handles_single_bad_side_star_constraint():
    report = pnode_width4_frontier_projection_report(
        single_bad_side_quartet_instance(),
        star_pc_tree(4),
        frontier_limit=10,
    )
    root = report["nodes"][0]

    assert report["frontier_truncated"] is False
    assert report["accepted_frontier_count"] == 2
    assert root["status"] == "holds"
    assert root["closure"]["candidate_order_count"] == 3
    assert root["closure"]["accepted_order_count"] == 2
    assert root["closure"]["relation_kind_histogram"]["nontrivial"] == 1


def test_width4_report_marks_truncated_frontiers_incomplete():
    T = p_node([leaf(i) for i in range(6)])
    report = pnode_width4_frontier_projection_report(
        equal_distance_instance(6),
        T,
        frontier_limit=5,
    )

    assert report["frontier_truncated"] is True
    assert report["nodes"][0]["status"] == "incomplete_frontiers"
