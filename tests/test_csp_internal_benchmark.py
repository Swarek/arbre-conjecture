from tools.pc_csp_internal_benchmark import run_benchmark


def test_csp_internal_benchmark_reports_separate_compile_and_solve_metrics():
    report = run_benchmark(
        sizes=[5],
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
    assert row["context_collision_profile_seconds"] >= 0
    assert row["open_boundary_profile_seconds"] >= 0
    assert row["quartet_scope_report_seconds"] >= 0
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
    quotients = row["profile_component_mask_quotients"]
    assert quotients["full"]["state_count"] == row["profile_component_mask_state_count"]
    assert quotients["full"]["mixed_count"] == 0
    assert quotients["mask_multiset"]["mixed_count"] == 0
    assert quotients["decision_only"]["state_count"] <= quotients["full"]["state_count"]
    context_quotients = row["context_collision_quotients"]
    assert row["context_collision_complete"]
    assert row["context_collision_pair_count"] > 0
    assert context_quotients["assignment_signature"]["mixed_count"] == 0
    assert context_quotients["mask_multiset"]["mixed_count"] > 0
    open_states = row["open_boundary_states"]
    assert row["open_boundary_complete"]
    assert row["open_boundary_context_pair_count"] == row["context_collision_pair_count"]
    assert row["open_boundary_response_checks"] == row["context_collision_assignments_seen"]
    assert open_states["assignment_signature"]["state_count"] == row[
        "open_boundary_local_assignments_seen"
    ]
    assert open_states["assignment_signature"]["boundary_mixed_count"] == 0
    assert open_states["mask_multiset_plus_boundary"]["state_count"] >= open_states[
        "mask_multiset"
    ]["state_count"]
    assert open_states["mask_multiset"]["boundary_mixed_count"] > 0
    assert open_states["mask_multiset_plus_boundary"]["boundary_mixed_count"] == 0
    assert row["quartet_scope_complete"]
    assert row["quartet_scope_quartet_count"] == 5
    assert row["quartet_scope_quartets_profiled"] == 5
    assert row["quartet_scope_projection_mismatch_count"] == 0
    assert row["quartet_scope_support_scope_gt_2_count"] == 5
    assert row["quartet_scope_effective_type_scope_gt_2_count"] == 0
    assert row["quartet_scope_effective_acceptance_scope_gt_2_count"] == 0
    assert row["quartet_scope_two_sat_candidate_quartet_count"] == 5
    assert row["quartet_scope_non_boolean_effective_acceptance_scope_count"] == 0
    assert row["quartet_scope_support_size_histogram"] == {3: 5}
    assert row["quartet_scope_effective_type_scope_size_histogram"] == {2: 5}
    assert row["quartet_scope_effective_acceptance_scope_size_histogram"] == {2: 5}
    assert row["quartet_relation_report_seconds"] >= 0
    assert row["quartet_relation_complete"]
    assert row["quartet_relation_row_class"] == "two_sat_candidate"
    assert row["quartet_relation_two_sat_candidate"]
    assert row["quartet_relation_validation_mismatch_count"] == 0
    assert row["quartet_relation_validation_assignments_seen"] == 16
    assert row["quartet_relation_scope_count"] == 3
    assert row["quartet_relation_binary_boolean_count"] == 3
    assert row["quartet_relation_binary_non_boolean_count"] == 0
    assert row["quartet_relation_high_arity_count"] == 0
    assert row["quartet_primal_edge_count"] == 3
    assert row["quartet_primal_treewidth_upper_bound"] == 2
    assert row["quartet_2sat_complete"]
    assert row["quartet_2sat_exists"] is True
    assert row["quartet_2sat_reason"] == "sat"
    assert row["quartet_2sat_variables"] == 4
    assert row["quartet_2sat_clauses"] == 6
    assert row["quartet_2sat_binary_clauses"] == 6
    assert row["quartet_2sat_empty_clauses"] == 0
    assert row["quartet_2sat_witness_is_cr"]
    assert row["quartet_treewidth_complete"]
    assert row["quartet_treewidth_exists"] is True
    assert row["quartet_treewidth_reason"] == "sat"
    assert row["quartet_treewidth_variables"] == 4
    assert row["quartet_treewidth_active_variables"] == 3
    assert row["quartet_treewidth_exact"] == 2
    assert row["quartet_treewidth_max_domain_size"] == 2
    assert row["quartet_treewidth_witness_is_cr"]
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
    summary_quotients = report["summary"]["profile_component_mask_quotients"]
    assert summary_quotients["full"]["state_count"] == row["profile_component_mask_state_count"]
    assert summary_quotients["full"]["mixed_count"] == 0
    summary_context_quotients = report["summary"]["context_collision_quotients"]
    assert report["summary"]["context_collision_assignments_seen"] == row[
        "context_collision_assignments_seen"
    ]
    assert report["summary"]["context_collision_pairs_profiled"] == row[
        "context_collision_pairs_profiled"
    ]
    assert report["summary"]["context_collision_incomplete_rows"] == 0
    assert summary_context_quotients["assignment_signature"]["mixed_count"] == 0
    assert summary_context_quotients["mask_multiset"]["mixed_count"] == context_quotients[
        "mask_multiset"
    ]["mixed_count"]
    summary_open_states = report["summary"]["open_boundary_states"]
    assert report["summary"]["open_boundary_local_assignments_seen"] == row[
        "open_boundary_local_assignments_seen"
    ]
    assert report["summary"]["open_boundary_response_checks"] == row[
        "open_boundary_response_checks"
    ]
    assert report["summary"]["open_boundary_pairs_profiled"] == row[
        "open_boundary_pairs_profiled"
    ]
    assert report["summary"]["open_boundary_incomplete_rows"] == 0
    assert summary_open_states["assignment_signature"]["state_count"] == row[
        "open_boundary_local_assignments_seen"
    ]
    assert summary_open_states["assignment_signature"]["boundary_mixed_count"] == 0
    assert summary_open_states["mask_multiset"]["boundary_mixed_count"] == open_states[
        "mask_multiset"
    ]["boundary_mixed_count"]
    assert report["summary"]["quartet_scope_incomplete_rows"] == 0
    assert report["summary"]["quartet_scope_quartets_profiled"] == row[
        "quartet_scope_quartets_profiled"
    ]
    assert report["summary"]["quartet_scope_projection_mismatches"] == 0
    assert report["summary"]["quartet_scope_support_scope_gt_2_count"] == row[
        "quartet_scope_support_scope_gt_2_count"
    ]
    assert report["summary"]["quartet_scope_effective_type_scope_gt_2_count"] == 0
    assert report["summary"]["quartet_scope_effective_acceptance_scope_gt_2_count"] == 0
    assert report["summary"]["quartet_scope_two_sat_candidate_quartet_count"] == 5
    assert report["summary"]["quartet_scope_non_boolean_effective_acceptance_scope_count"] == 0
    assert report["summary"]["quartet_scope_support_size_histogram"] == {"3": 5}
    assert report["summary"]["quartet_scope_effective_type_scope_size_histogram"] == {"2": 5}
    assert report["summary"]["quartet_scope_effective_acceptance_scope_size_histogram"] == {"2": 5}
    assert report["summary"]["quartet_relation_incomplete_rows"] == 0
    assert report["summary"]["quartet_relation_validation_mismatches"] == 0
    assert report["summary"]["quartet_relation_two_sat_candidate_rows"] == 1
    assert report["summary"]["quartet_relation_row_class_histogram"] == {"two_sat_candidate": 1}
    assert report["summary"]["quartet_relation_scope_count"] == row[
        "quartet_relation_scope_count"
    ]
    assert report["summary"]["quartet_relation_binary_boolean_count"] == 3
    assert report["summary"]["quartet_relation_binary_non_boolean_count"] == 0
    assert report["summary"]["quartet_relation_high_arity_count"] == 0
    assert report["summary"]["quartet_relation_kind_histogram"] == {"binary_boolean_2sat": 3}
    assert report["summary"]["quartet_primal_max_treewidth_upper_bound"] == 2
    assert report["summary"]["quartet_primal_max_edge_count"] == 3
    assert report["summary"]["quartet_2sat_complete_rows"] == 1
    assert report["summary"]["quartet_2sat_exists_true_rows"] == 1
    assert report["summary"]["quartet_2sat_exists_false_rows"] == 0
    assert report["summary"]["quartet_2sat_incomplete_rows"] == 0
    assert report["summary"]["quartet_2sat_reason_histogram"] == {"sat": 1}
    assert report["summary"]["quartet_2sat_total_clauses"] == 6
    assert report["summary"]["quartet_2sat_witness_failures"] == 0
    assert report["summary"]["quartet_treewidth_complete_rows"] == 1
    assert report["summary"]["quartet_treewidth_exists_true_rows"] == 1
    assert report["summary"]["quartet_treewidth_exists_false_rows"] == 0
    assert report["summary"]["quartet_treewidth_incomplete_rows"] == 0
    assert report["summary"]["quartet_treewidth_reason_histogram"] == {"sat": 1}
    assert report["summary"]["quartet_treewidth_max_exact"] == 2
    assert report["summary"]["quartet_treewidth_max_domain_size"] == 2
    assert report["summary"]["quartet_treewidth_witness_failures"] == 0
