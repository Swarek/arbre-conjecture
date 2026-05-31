from pc_circular.solvers.interface_experiments import fixed_context_interface_product_report
from tools.pc_residual_interface_probe import (
    p2_focus,
    run_residual_interface_probe,
    two_level_high_pair_matrix,
)


def test_two_level_p2x3_has_binary_residual_relation():
    D = two_level_high_pair_matrix(8, ((0, 2), (1, 3)))
    report = fixed_context_interface_product_report(
        D,
        p2_focus(3),
        branch_order=(0, 1, 2),
        context_before=(6,),
        context_after=(7,),
    )

    assert report["complete"] is True
    assert report["accepted_tuple_count"] == 4
    assert report["closure_by_arity"][1]["false_tuple_count"] == 4
    assert report["closure_by_arity"][2]["exact"] is True
    assert report["minimal_coupling_support_size"] == 2


def test_residual_interface_probe_summarizes_bounded_search():
    report = run_residual_interface_probe(max_high_pairs=2, max_search_cases=500)

    assert report["method"] == "t088_residual_interface_probe"
    assert report["summary"]["two_level_search_complete"] is True
    assert report["summary"]["two_level_cases_searched"] == 406
    assert report["summary"]["two_level_relation_kind_counts"]["nontrivial"] > 0
    assert report["summary"]["two_level_max_minimal_coupling_support_size"] == 2
    assert report["summary"]["two_level_found_beyond_binary"] is False
    assert report["best_non_unary_two_level"] is not None
