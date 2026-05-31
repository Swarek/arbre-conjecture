from pc_circular.generators import instance_by_kind, single_bad_side_quartet_instance
from pc_circular.pc_tree import leaf, p_node, pc_tree_from_kind, star_pc_tree
from pc_circular.solvers.partial_obligation_experiments import (
    pnode_context_gap_relation_report,
    pnode_context_signature_ladder_report,
    pnode_partial_context_dependency_report,
    pnode_partial_obligation_report,
    pnode_separator_signature_report,
)
from tools.pc_context_gap_relation_probe import run_probe as run_gap_probe
from tools.pc_context_signature_ladder_probe import run_probe as run_ladder_probe
from tools.pc_partial_context_lab_probe import run_probe as run_context_probe
from tools.pc_partial_obligation_lab_probe import run_probe as run_obligation_probe
from tools.pc_separator_signature_lab_probe import run_probe as run_separator_probe


def test_partial_report_keeps_fully_visible_star_chord_clean():
    report = pnode_partial_obligation_report(
        single_bad_side_quartet_instance(),
        star_pc_tree(4),
    )

    assert report["pnode_count"] == 1
    assert report["global_not_contained_count"] == 0
    assert report["max_non_chord_obligation_count"] == 0
    node = report["nodes"][0]
    assert node["status"] == "local_matches_global_seen"
    assert node["fully_visible_four_branch_obligation_count"] == 1
    assert node["forbidden_chord_pair_count"] == 1
    assert node["non_chord_obligation_count"] == 0
    assert node["partial_kind"] == "fully_visible_chords_only"
    assert node["fine_role_pattern_histogram"] == {"support:full_four_branch": 1}


def test_partial_report_detects_collapsed_root_obligation():
    T = p_node(
        (
            p_node((leaf(0), leaf(1))),
            p_node((leaf(2), leaf(3))),
        )
    )
    report = pnode_partial_obligation_report(
        single_bad_side_quartet_instance(),
        T,
    )

    root = next(node for node in report["nodes"] if node["path"] == ())
    assert root["forbidden_chord_pair_count"] == 0
    assert root["non_chord_obligation_count"] == 1
    assert root["open_obligation_count"] == 1
    assert root["support_boundary_obligation_count"] == 1
    assert root["partial_kind"] == "open_separator_obligations"
    assert root["fine_role_pattern_histogram"] == {
        "support:full_collapsed:s2:mixed": 1,
    }


def test_partial_obligation_probe_summarizes_small_sweep():
    report = run_obligation_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_branch_degree=5,
        max_examples=2,
        seed=20260620,
    )

    assert report["method"] == "t092_partial_obligation_lab_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert report["summary"]["global_not_contained_rows"] == 0
    assert "fine_role_pattern_histogram" in report["summary"]


def test_partial_context_dependency_detects_collapsed_root_mixed_group():
    T = p_node(
        (
            p_node((leaf(0), leaf(1))),
            p_node((leaf(2), leaf(3))),
        )
    )
    report = pnode_partial_context_dependency_report(
        single_bad_side_quartet_instance(),
        T,
    )

    root = next(node for node in report["nodes"] if node["path"] == ())
    assert report["frontier_truncated"] is False
    assert root["support_boundary_obligation_count"] == 1
    assert root["support_boundary_mixed_group_count"] == 1
    assert root["fully_visible_mixed_group_count"] == 0
    example = root["mixed_examples"][0]
    assert example["same_side"] == (0, 2, 1, 3)
    assert example["fine_role_pattern"] == "support:full_collapsed:s2:mixed"
    assert example["local_branch_order"] == (0, 1)
    assert example["satisfied_frontier"] == (0, 1, 3, 2)
    assert example["violated_frontier"] == (0, 1, 2, 3)


def test_partial_context_dependency_keeps_fully_visible_star_local():
    report = pnode_partial_context_dependency_report(
        single_bad_side_quartet_instance(),
        star_pc_tree(4),
    )

    node = report["nodes"][0]
    assert report["support_boundary_mixed_group_count"] == 0
    assert report["fully_visible_mixed_group_count"] == 0
    assert node["fully_visible_obligation_count"] == 1
    assert node["mixed_group_count"] == 0


def test_partial_context_probe_summarizes_small_sweep():
    report = run_context_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_examples=2,
        seed=20260630,
    )

    assert report["method"] == "t093_partial_context_lab_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert report["summary"]["rows_with_fully_visible_mixed_groups"] == 0


def test_separator_signature_refines_collapsed_root_mixed_group():
    T = p_node(
        (
            p_node((leaf(0), leaf(1))),
            p_node((leaf(2), leaf(3))),
        )
    )
    report = pnode_separator_signature_report(
        single_bad_side_quartet_instance(),
        T,
    )

    root = next(node for node in report["nodes"] if node["path"] == ())
    assert root["branch_order_mixed_group_count"] == 1
    assert root["support_boundary_branch_order_mixed_group_count"] == 1
    assert root["separator_signature_mixed_group_count"] == 0
    assert root["support_boundary_removed_mixed_group_count"] == 1
    example = root["branch_order_mixed_examples"][0]
    assert example["same_side"] == (0, 2, 1, 3)
    assert example["local_branch_order"] == (0, 1)
    assert example["satisfied_frontier"] == (0, 1, 3, 2)
    assert example["violated_frontier"] == (0, 1, 2, 3)
    assert example["satisfied_separator_signature"] != example[
        "violated_separator_signature"
    ]
    assert example["satisfied_separator_signature"] == (
        (0, (("endpoint", 0), ("witness", 1))),
        (1, (("witness", 3), ("endpoint", 2))),
    )
    assert example["violated_separator_signature"] == (
        (0, (("endpoint", 0), ("witness", 1))),
        (1, (("endpoint", 2), ("witness", 3))),
    )


def test_separator_signature_keeps_fully_visible_star_local():
    report = pnode_separator_signature_report(
        single_bad_side_quartet_instance(),
        star_pc_tree(4),
    )

    node = report["nodes"][0]
    assert report["branch_order_mixed_group_count"] == 0
    assert report["separator_signature_mixed_group_count"] == 0
    assert node["fully_visible_obligation_count"] == 1
    assert node["branch_order_mixed_group_count"] == 0


def test_separator_signature_is_not_sufficient_on_mixed_cycle():
    report = pnode_separator_signature_report(
        instance_by_kind(4, kind="cycle"),
        pc_tree_from_kind("mixed", 4),
    )

    assert report["separator_signature_mixed_group_count"] == 4
    assert report["support_boundary_separator_mixed_group_count"] == 4
    node = next(
        node for node in report["nodes"] if node["separator_signature_mixed_group_count"]
    )
    example = node["separator_signature_mixed_examples"][0]
    assert example["same_side"] == (0, 3, 1, 2)
    assert example["satisfied_frontier"] == (0, 1, 2, 3)
    assert example["violated_frontier"] == (0, 1, 3, 2)


def test_separator_signature_probe_summarizes_small_sweep():
    report = run_separator_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_examples=2,
        seed=20260640,
    )

    assert report["method"] == "t094_separator_signature_lab_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert "separator_signature_mixed_group_count" in report["summary"]


def test_context_signature_ladder_explains_t093_minimal_witness():
    T = p_node(
        (
            p_node((leaf(0), leaf(1))),
            p_node((leaf(2), leaf(3))),
        )
    )
    report = pnode_context_signature_ladder_report(
        single_bad_side_quartet_instance(),
        T,
    )

    assert report["modes"]["t094_visible_per_branch"]["mixed_group_count"] == 2
    assert report["modes"]["visible_global"]["mixed_group_count"] == 1
    assert (
        report["modes"]["visible_global_plus_missing_order"]["mixed_group_count"]
        == 0
    )
    assert report["modes"]["full_context_order"]["mixed_group_count"] == 0


def test_context_signature_ladder_explains_mixed_cycle_t094_counter_signal():
    report = pnode_context_signature_ladder_report(
        instance_by_kind(4, kind="cycle"),
        pc_tree_from_kind("mixed", 4),
    )

    assert report["modes"]["t094_visible_per_branch"]["mixed_group_count"] == 4
    assert report["modes"]["visible_global"]["mixed_group_count"] == 2
    assert (
        report["modes"]["visible_global_plus_missing_order"]["mixed_group_count"]
        == 0
    )
    assert report["modes"]["full_context_order"]["mixed_group_count"] == 0


def test_context_signature_ladder_keeps_cycle5_as_stronger_counter_signal():
    report = pnode_context_signature_ladder_report(
        instance_by_kind(5, kind="cycle"),
        pc_tree_from_kind("mixed", 5),
    )

    assert (
        report["modes"]["visible_global_plus_missing_order"]["mixed_group_count"]
        > 0
    )
    assert report["modes"]["full_context_order"]["mixed_group_count"] == 0


def test_context_signature_ladder_probe_summarizes_small_sweep():
    report = run_ladder_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_examples=2,
        seed=20260650,
    )

    assert report["method"] == "t095_context_signature_ladder_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert "visible_global_plus_missing_order" in report["summary"]["modes"]


def test_context_gap_relation_explains_cycle5_t095_counter_signal():
    report = pnode_context_gap_relation_report(
        instance_by_kind(5, kind="cycle"),
        pc_tree_from_kind("mixed", 5),
    )

    assert report["visible_missing_mixed_group_count"] > 0
    assert report["gap_state_mixed_group_count"] == 0
    assert report["full_context_mixed_group_count"] == 0
    assert report["nontrivial_gap_relation_bucket_count"] > 0


def test_context_gap_relation_explains_t093_minimal_witness():
    T = p_node(
        (
            p_node((leaf(0), leaf(1))),
            p_node((leaf(2), leaf(3))),
        )
    )
    report = pnode_context_gap_relation_report(
        single_bad_side_quartet_instance(),
        T,
    )

    assert report["visible_missing_mixed_group_count"] == 0
    assert report["gap_state_mixed_group_count"] == 0
    assert report["full_context_mixed_group_count"] == 0


def test_context_gap_relation_probe_summarizes_small_sweep():
    report = run_gap_probe(
        sizes=[4, 5],
        pc_trees=["star"],
        instance_kinds=["equal", "paired_farthest"],
        repeats=1,
        frontier_limit=200,
        max_examples=2,
        seed=20260660,
    )

    assert report["method"] == "t096_context_gap_relation_probe"
    assert report["summary"]["rows"] == 4
    assert report["summary"]["rows_with_pnodes"] == 4
    assert "gap_state_mixed_group_count" in report["summary"]
