from tools.pc_csp_internal_benchmark import run_benchmark


def test_csp_internal_benchmark_reports_separate_compile_and_solve_metrics():
    report = run_benchmark(
        sizes=[4],
        repeats=1,
        instance_kinds=["cycle"],
        pc_trees=["mixed"],
        max_p_degree=3,
        seed=20260522,
        validate=True,
    )

    assert report["summary"]["rows"] == 1
    assert report["summary"]["supported_rows"] == 1
    assert report["summary"]["mismatches"] == 0
    row = report["rows"][0]
    assert row["compile_seconds"] >= 0
    assert row["solve_seconds"] >= 0
    assert row["direct_seconds"] is not None
    assert row["full_assignment_space"] >= row["leaf_assignments_seen"]
