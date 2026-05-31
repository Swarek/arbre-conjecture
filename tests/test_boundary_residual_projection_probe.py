from tools.pc_boundary_residual_projection_probe import (
    boundary_projection_rows,
    run_boundary_residual_projection_probe,
)
from tools.pc_residual_interface_probe import two_level_high_pair_matrix


def test_boundary_projection_seed_still_needs_binary_relation():
    report = boundary_projection_rows(
        case="unit_binary_projection_seed",
        D=two_level_high_pair_matrix(10, ((0, 2), (1, 3))),
        branch_sizes=(2, 2, 2, 2),
    )

    assert report["accepted_tuple_count"] == 8
    assert report["nontrivial_boundary_projection_count"] > 0
    assert report["max_boundary_minimal_arity"] == 2
    assert report["found_beyond_binary"] is False
    assert report["best_non_unary"]["minimal_projection_arity"] == 2


def test_boundary_residual_projection_probe_summarizes_small_search():
    report = run_boundary_residual_projection_probe(
        p2x4_max_high_pairs=2,
        p2x4_max_cases=500,
        p2x5_max_high_pairs=1,
        p2x5_max_cases=100,
        random_trials=10,
        seed=20260600,
    )

    assert report["method"] == "t090_boundary_residual_projection_probe"
    assert report["summary"]["controls"] == 1
    assert report["summary"]["sparse_scans"] == 2
    assert report["summary"]["max_boundary_minimal_arity"] == 2
    assert report["summary"]["found_beyond_binary"] is False
    assert report["sparse_scans"][0]["cases_searched"] == 500
    assert report["sparse_scans"][0]["found_beyond_binary"] is False
