from pc_circular.generators import equal_distance_instance, single_bad_side_quartet_instance
from pc_circular.pc_tree import leaf, p_node
from pc_circular.solvers.interface_experiments import (
    fixed_context_interface_product_report,
    root_fixed_order_interface_product_report,
)
from tools.pc_pnode_context_interface_probe import (
    context_coupling_seed_matrix,
    run_pnode_context_interface_probe,
)
from tools.pc_pnode_interface_probe import run_pnode_interface_probe


def _nested_p2_tree():
    return p_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)])])


def test_root_interface_product_factorizes_on_equal_distance_control():
    report = root_fixed_order_interface_product_report(
        equal_distance_instance(4),
        _nested_p2_tree(),
        branch_order=(0, 1),
    )

    assert report["complete"] is True
    assert report["accepted_tuple_count"] == 4
    assert report["projection_product_count"] == 4
    assert report["false_product_count"] == 0
    assert report["factorizes"] is True
    assert report["minimal_coupling_support_size"] == 1


def test_root_interface_product_detects_single_bad_side_coupling():
    report = root_fixed_order_interface_product_report(
        single_bad_side_quartet_instance(),
        _nested_p2_tree(),
        branch_order=(0, 1),
    )

    assert report["complete"] is True
    assert report["accepted_tuple_count"] == 2
    assert report["projection_product_count"] == 4
    assert report["false_product_count"] == 2
    assert report["factorizes"] is False
    assert report["minimal_coupling_support_size"] == 2
    assert report["false_product_examples"][0]["bad_side_violation"] is not None


def test_pnode_interface_probe_includes_refuted_and_factorized_controls():
    report = run_pnode_interface_probe()

    assert report["method"] == "t086_pnode_interface_product_probe"
    assert report["summary"]["rows"] == 9
    assert report["summary"]["complete_rows"] == 9
    assert report["summary"]["refuted_rows"] >= 1
    assert report["summary"]["factorized_rows"] >= 1
    cases = {row["case"] for row in report["rows"]}
    assert "equal_nested_p2_control" in cases
    assert "single_bad_side_nested_p2" in cases
    assert "handwritten_seed_sketch_flat_2_2_3" in cases


def test_fixed_context_interface_factorizes_on_equal_distance_control():
    report = fixed_context_interface_product_report(
        equal_distance_instance(6),
        _nested_p2_tree(),
        branch_order=(0, 1),
        context_before=(4,),
        context_after=(5,),
    )

    assert report["complete"] is True
    assert report["accepted_tuple_count"] == 4
    assert report["projection_product_count"] == 4
    assert report["false_product_count"] == 0
    assert report["factorizes"] is True
    assert report["minimal_coupling_support_size"] == 1


def test_fixed_context_interface_detects_context_coupling_seed():
    report = fixed_context_interface_product_report(
        context_coupling_seed_matrix(),
        _nested_p2_tree(),
        branch_order=(0, 1),
        context_before=(4,),
        context_after=(5,),
    )

    assert report["complete"] is True
    assert report["accepted_tuple_count"] == 2
    assert report["projection_product_count"] == 4
    assert report["false_product_count"] == 2
    assert report["factorizes"] is False
    assert report["minimal_coupling_support_size"] == 2
    assert report["false_product_examples"][0]["bad_side_violation"] is not None


def test_pnode_context_interface_probe_includes_refuted_and_factorized_controls():
    report = run_pnode_context_interface_probe()

    assert report["method"] == "t087_pnode_context_interface_product_probe"
    assert report["summary"]["rows"] == 5
    assert report["summary"]["complete_rows"] == 5
    assert report["summary"]["refuted_rows"] >= 1
    assert report["summary"]["factorized_rows"] >= 1
    cases = {row["case"] for row in report["rows"]}
    assert "equal_context_nested_p2_control" in cases
    assert "context_coupling_seed_nested_p2" in cases
    assert "handwritten_seed_context_sketch_flat_2_2_3" in cases
