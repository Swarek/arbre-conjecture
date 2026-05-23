from tools.pc_circular_complexity_benchmark import run_benchmark


def test_complexity_benchmark_reports_mixed_subfamilies():
    def candidate(_D, pc_tree=None):
        return {
            "exists": False,
            "order": None,
            "complete": False,
            "solver": "test_placeholder",
        }

    report = run_benchmark(
        candidate,
        candidate_label="test-candidate",
        sizes=[6],
        repeats=6,
        timeout=1.0,
        instance_kind="mixed",
        pc_tree_kind="star",
        seed=123,
    )

    row = report["rows"][0]
    assert report["seed"] == 123
    assert sum(row["resolved_kind_counts"].values()) == 6
    assert sum(row["successful_runs_by_resolved_kind"].values()) == 6
    assert sum(row["incomplete_runs_by_resolved_kind"].values()) == 6
    assert row["timeouts_by_resolved_kind"] == {}
    assert row["solver_counts"] == {"test_placeholder": 6}
    assert {
        solver
        for solvers in row["solver_counts_by_resolved_kind"].values()
        for solver in solvers
    } == {"test_placeholder"}


def test_complexity_benchmark_reports_explicit_kind_as_resolved_kind():
    def candidate(_D, pc_tree=None):
        return {
            "exists": True,
            "order": None,
            "complete": True,
            "solver": "test_complete",
        }

    report = run_benchmark(
        candidate,
        candidate_label="test-candidate",
        sizes=[6],
        repeats=3,
        timeout=1.0,
        instance_kind="cycle",
        pc_tree_kind="star",
        seed=123,
    )

    row = report["rows"][0]
    assert row["resolved_kind_counts"] == {"cycle": 3}
    assert row["exists_true_by_resolved_kind"] == {"cycle": 3}
    assert row["incomplete_runs_by_resolved_kind"] == {}
