from pc_circular.generators import single_bad_side_quartet_instance
from pc_circular.pc_tree import star_pc_tree
from pc_circular.solvers.circle_graph_experiments import (
    branch_order_satisfies_forbidden_chord_pairs,
    chord_crosses_in_order,
    pnode_circle_graph_local_report,
)
from tools.pc_circle_graph_lab_probe import run_probe


def test_chord_crosses_in_order_detects_alternation():
    assert chord_crosses_in_order((0, 1, 2, 3), (0, 2), (1, 3)) is True
    assert chord_crosses_in_order((0, 1, 2, 3), (0, 1), (2, 3)) is False
    assert chord_crosses_in_order((0, 1, 2, 3), (0, 2), (0, 3)) is False


def test_branch_order_satisfies_forced_noncrossing_constraints():
    forbidden = (((0, 2), (1, 3)),)

    assert branch_order_satisfies_forbidden_chord_pairs((0, 1, 2, 3), forbidden) is False
    assert branch_order_satisfies_forbidden_chord_pairs((0, 1, 3, 2), forbidden) is True


def test_circle_graph_report_matches_star_single_bad_side_instance():
    report = pnode_circle_graph_local_report(
        single_bad_side_quartet_instance(),
        star_pc_tree(4),
    )

    assert report["pnode_count"] == 1
    assert report["global_not_contained_count"] == 0
    assert report["local_matches_global_seen_count"] == 1
    node = report["nodes"][0]
    assert node["forbidden_chord_pair_count"] == 1
    assert node["local_order_count"] == 2
    assert node["global_cr_branch_order_count"] == 2


def test_circle_graph_lab_probe_summarizes_small_sweep():
    report = run_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_branch_degree=5,
        max_examples=2,
        seed=20260610,
    )

    assert report["method"] == "t091_circle_graph_lab_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert report["summary"]["global_not_contained_rows"] == 0
