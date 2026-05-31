from tools.pc_residual_interface_stress_probe import (
    branch_size_focus,
    run_residual_interface_stress_probe,
)
from tools.pc_residual_interface_probe import residual_row, two_level_high_pair_matrix


def test_p3x3_binary_seed_is_non_unary_but_binary():
    focus, used_labels = branch_size_focus((3, 3, 3))
    row = residual_row(
        case="p3x3_binary_seed",
        D=two_level_high_pair_matrix(
            used_labels + 2,
            ((0, 4), (0, 5), (1, 7), (2, 6)),
        ),
        focus=focus,
        branch_order=(0, 1, 2),
        context_before=(used_labels,),
        context_after=(used_labels + 1,),
    )

    assert row["accepted_tuple_count"] == 24
    assert row["minimal_coupling_support_size"] == 2
    assert row["closure_by_arity"][1]["false_tuple_count"] == 24
    assert row["closure_by_arity"][2]["exact"] is True


def test_residual_interface_stress_probe_runs_small_deterministic_sweep():
    report = run_residual_interface_stress_probe(
        p2x4_trials=80,
        p3x3_trials=40,
        seed=20260593,
    )

    assert report["method"] == "t089_residual_interface_stress_probe"
    assert report["summary"]["control_rows"] == 2
    assert report["summary"]["profiles"] == 2
    assert report["summary"]["max_minimal_coupling_support_size"] >= 2
    assert report["control_rows"][0]["minimal_coupling_support_size"] == 2
    assert report["control_rows"][1]["minimal_coupling_support_size"] == 2
