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
    assert row["first_hit_assignments"] + row["first_hit_no_hit_assignments"] == row[
        "first_hit_support_assignments_seen"
    ]
    assert row["first_hit_atom_checks"] == (
        row["first_hit_position_sum"] + row["first_hit_checks_spent_on_no_hit"]
    )
    assert row["first_hit_atom_checks_if_exhaustive_seen"] == (
        row["first_hit_atom_checks"] + row["first_hit_checks_saved_on_hits"]
    )
    assert row["first_hit_atom_checks_saved"] == row["first_hit_checks_saved_on_hits"]
    assert row["first_hit_position_sum"] == sum(
        int(position) * count
        for position, count in row["first_hit_position_histogram"].items()
    )
    assert row["support_outcome_profile_seconds"] >= 0
    assert row["profile_complete"]
    assert row["profile_hit_assignments"] == row["first_hit_assignments"]
    assert row["profile_no_hit_assignments"] == row["first_hit_no_hit_assignments"]
    assert row["profile_hit_assignments"] + row["profile_no_hit_assignments"] == row[
        "first_hit_support_assignments_seen"
    ]
    assert row["profile_classification_atom_checks"] == row["first_hit_atom_checks"]
    assert row["profile_exhaustive_atom_checks_seen"] == row[
        "first_hit_atom_checks_if_exhaustive_seen"
    ]
    assert row["profile_no_hit_exhaustive_atom_checks"] == row[
        "first_hit_checks_spent_on_no_hit"
    ]
    assert (
        row["profile_unary_no_hit_certified_assignments"]
        + row["profile_ambiguous_no_hit_assignments"]
        == row["profile_no_hit_assignments"]
    )
    assert (
        row["profile_unary_hit_certified_assignments"] + row["profile_ambiguous_hit_assignments"]
        == row["profile_hit_assignments"]
    )
    assert row["profile_pair_side_split_hit_assignments"] == row["profile_hit_assignments"]
    assert row["profile_pair_side_split_no_hit_assignments"] == row["profile_no_hit_assignments"]
    assert row["profile_pair_side_split_mismatches"] == 0
    assert row["profile_pair_side_split_checks"] == (
        row["profile_pair_side_split_side_checks"]
        + row["profile_pair_side_split_component_witness_checks"]
    )
    assert row["profile_pair_side_split_side_checks"] == (
        row["profile_pair_side_split_side_cache_hits"]
        + row["profile_pair_side_split_side_cache_misses"]
    )
    assert row["profile_pair_side_split_cached_checks"] == (
        row["profile_pair_side_split_side_cache_misses"]
        + row["profile_pair_side_split_component_witness_checks"]
    )
    assert row["profile_pair_side_split_bitset_cached_checks"] == (
        row["profile_pair_side_split_side_cache_misses"]
        + row["profile_pair_side_split_component_checks"]
    )
    assert row["profile_pair_side_split_bitset_cached_checks"] <= row[
        "profile_pair_side_split_cached_checks"
    ]
    assert row["profile_pair_side_split_bitset_hit_assignments"] == row[
        "profile_hit_assignments"
    ]
    assert row["profile_pair_side_split_bitset_no_hit_assignments"] == row[
        "profile_no_hit_assignments"
    ]
    assert row["profile_pair_side_split_bitset_mismatches"] == 0
    assert row["profile_pair_side_split_bitset_checks"] == (
        row["profile_pair_side_split_bitset_component_checks"]
        + row["profile_pair_side_split_bitset_witness_visits"]
    )
    assert row["profile_pair_side_split_bitset_projection_checks"] == (
        row["profile_pair_side_split_bitset_component_checks"]
        + row["profile_pair_side_split_bitset_side_cache_misses"]
    )
    assert row["profile_component_mask_state_count"] <= (
        row["profile_hit_assignments"] + row["profile_no_hit_assignments"]
    )
    assert row["profile_component_mask_state_hit_count"] + row[
        "profile_component_mask_state_no_hit_count"
    ] == row["profile_component_mask_state_count"]
    assert row["profile_component_mask_state_mixed_count"] == 0
    assert row["profile_component_mask_state_mismatches"] == 0
    assert row["profile_component_mask_state_side_cache_hits"] + row[
        "profile_component_mask_state_side_cache_misses"
    ] == row["profile_component_mask_state_witness_visits"]
    assert row["profile_component_mask_state_work_ratio"] == (
        (
            row["profile_component_mask_state_component_masks"]
            + row["profile_component_mask_state_witness_visits"]
        )
        / row["profile_classification_atom_checks"]
    )
    assert row["profile_component_mask_state_projection_work_ratio"] == (
        (
            row["profile_component_mask_state_component_masks"]
            + row["profile_component_mask_state_side_cache_misses"]
        )
        / row["profile_classification_atom_checks"]
    )
    assert report["summary"]["total_first_hit_position_sum"] == row["first_hit_position_sum"]
    assert report["summary"]["total_first_hit_atom_checks_if_exhaustive_seen"] == row[
        "first_hit_atom_checks_if_exhaustive_seen"
    ]
    assert report["summary"]["total_profile_no_hit_exhaustive_atom_checks"] == row[
        "profile_no_hit_exhaustive_atom_checks"
    ]
    assert report["summary"]["total_profile_ambiguous_no_hit_assignments"] == row[
        "profile_ambiguous_no_hit_assignments"
    ]
    assert report["summary"]["profile_pair_side_split_mismatches"] == 0
    assert report["summary"]["total_profile_pair_side_split_checks"] == row[
        "profile_pair_side_split_checks"
    ]
    assert report["summary"]["total_profile_pair_side_split_cached_checks"] == row[
        "profile_pair_side_split_cached_checks"
    ]
    assert report["summary"]["total_profile_pair_side_split_bitset_cached_checks"] == row[
        "profile_pair_side_split_bitset_cached_checks"
    ]
    assert report["summary"]["profile_pair_side_split_bitset_mismatches"] == 0
    assert report["summary"]["total_profile_pair_side_split_bitset_checks"] == row[
        "profile_pair_side_split_bitset_checks"
    ]
    assert report["summary"]["total_profile_pair_side_split_bitset_projection_checks"] == row[
        "profile_pair_side_split_bitset_projection_checks"
    ]
    assert report["summary"]["profile_component_mask_state_mismatches"] == 0
    assert report["summary"]["profile_component_mask_state_mixed_count"] == 0
    assert report["summary"]["total_profile_component_mask_state_count"] == row[
        "profile_component_mask_state_count"
    ]
    assert report["summary"]["total_profile_component_mask_state_witness_visits"] == row[
        "profile_component_mask_state_witness_visits"
    ]
    assert report["summary"]["profile_component_mask_state_work_ratio"] == row[
        "profile_component_mask_state_work_ratio"
    ]
    assert report["summary"]["profile_component_mask_state_projection_work_ratio"] == row[
        "profile_component_mask_state_projection_work_ratio"
    ]
