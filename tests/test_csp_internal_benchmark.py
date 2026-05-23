from tools.pc_csp_internal_benchmark import run_benchmark
from tools.pc_csp_width_stress import run_width_stress
from tools.pc_relation_catalog import run_relation_catalog
from tools.pc_relation_chain_probe import run_relation_chain_probe
from tools.pc_relation_component_probe import run_relation_component_probe
from tools.pc_relation_shape_search import run_relation_shape_search
from tools.pc_relation_unsat_core_probe import run_relation_unsat_core_probe
from tools.pc_sparse_matching_conflict_probe import run_sparse_matching_conflict_probe
from tools.pc_permutation_like_probe import run_permutation_like_probe
from tools.pc_permutation_composition_probe import run_permutation_composition_probe
from tools.pc_single_p_domain_stress import run_single_p_domain_stress


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


def test_p3_block_width_stress_reports_growth_and_caps():
    report = run_width_stress(
        block_counts=[3, 4],
        instance_kinds=["cycle"],
        max_treewidth=3,
        validate_until_blocks=3,
    )

    assert report["summary"]["rows"] == 2
    assert report["summary"]["treewidth_complete_rows"] == 1
    assert report["summary"]["treewidth_incomplete_rows"] == 1
    assert report["summary"]["treewidth_reason_histogram"] == {
        "sat": 1,
        "treewidth_cap_exceeded": 1,
    }
    assert report["summary"]["max_primal_treewidth_upper_bound"] == 4
    assert report["summary"]["max_treewidth_exact"] == 3
    assert report["summary"]["witness_failures"] == 0

    complete_row = report["rows"][0]
    capped_row = report["rows"][1]
    assert complete_row["block_count"] == 3
    assert complete_row["relation_row_class"] == "non_boolean_relation_catalog"
    assert complete_row["treewidth_complete"]
    assert complete_row["treewidth_exists"] is True
    assert complete_row["treewidth_exact"] == 3
    assert complete_row["treewidth_witness_is_cr"]
    assert capped_row["block_count"] == 4
    assert capped_row["primal_treewidth_upper_bound"] == 4
    assert capped_row["treewidth_complete"] is False
    assert capped_row["treewidth_exists"] is None
    assert capped_row["treewidth_reason"] == "treewidth_cap_exceeded"


def test_single_p_domain_stress_exposes_factorial_domain_even_at_treewidth_zero():
    report = run_single_p_domain_stress(
        sizes=[4, 6],
        instance_kinds=["equal", "cycle", "single_quartet"],
        frontier_limit=1000,
    )

    assert report["summary"]["rows"] == 5
    assert report["summary"]["treewidth_zero_rows"] == 5
    assert report["summary"]["max_domain_size"] == 60
    assert report["summary"]["max_complete_domain_size"] == 60
    assert report["summary"]["incomplete_exact_count_rows"] == 0

    equal6 = next(
        row
        for row in report["rows"]
        if row["n"] == 6 and row["instance_kind"] == "equal"
    )
    assert equal6["domain_size"] == 60
    assert equal6["cr_order_count"] == 60

    quartet = next(
        row for row in report["rows"] if row["instance_kind"] == "single_quartet"
    )
    assert quartet["n"] == 4
    assert quartet["domain_size"] == 3
    assert quartet["bad_side"]["nontrivial_bad_side_pairs"] == 1
    assert quartet["bad_side"]["unordered_bad_side_constraints"] == 1
    assert quartet["bad_side"]["oriented_bad_side_atoms"] == 2
    assert quartet["bad_side"]["first_nontrivial_pair"] == {
        "pair": [0, 2],
        "bad_witnesses": [1, 3],
        "unordered_constraints": 1,
    }
    assert quartet["cr_order_count"] == 2


def test_relation_catalog_reports_non_boolean_p3_relations_and_parasites():
    report = run_relation_catalog(
        block_counts=[2],
        instance_kinds=["cycle", "paired_farthest", "equal", "four_local_non_cr"],
        repeats=1,
    )

    assert report["summary"]["rows"] == 4
    assert report["summary"]["complete_rows"] == 4
    assert report["summary"]["validation_mismatches"] == 0
    assert report["summary"]["row_class_histogram"] == {
        "non_boolean_relation_catalog": 3,
        "two_sat_candidate": 1,
    }
    assert report["summary"]["binary_non_boolean_rows"] == 3
    assert report["summary"]["binary_non_boolean_relation_instances"] == 3
    assert report["summary"]["unique_binary_non_boolean_catalog_hashes"] >= 1
    assert report["summary"]["max_relation_domain_product"] == 36
    assert report["summary"]["rows_with_unary_non_boolean_parasite"] == 3
    assert report["summary"]["rows_with_constant_reject_parasite"] == 1

    cycle = next(row for row in report["rows"] if row["instance_kind"] == "cycle")
    assert cycle["row_class"] == "non_boolean_relation_catalog"
    assert cycle["relation_accept_assignments"] == cycle["direct_cr_assignments"] == 4
    assert cycle["max_domain_size"] == 6
    assert cycle["domain_size_histogram"] == {"2": 1, "6": 2}
    assert cycle["scope_size_histogram"] == {"1": 2, "2": 1}
    assert cycle["binary_non_boolean_relation_count"] == 1
    assert cycle["parasite_unary_non_boolean_count"] == 2
    assert cycle["parasite_free_gadget_candidate"] is False
    assert cycle["complexity_claim_allowed"] == "fpt_q_w"
    relation = cycle["binary_non_boolean_relations"][0]
    assert relation["domain_sizes"] == [6, 6]
    assert relation["domain_product"] == 36
    assert relation["accepted_signature_count"] == 2
    assert relation["rejected_tuple_ratio"] == 34 / 36
    assert relation["accepted_index_tuples"] == [[0, 0], [5, 5]]
    assert relation["left_functional"]
    assert relation["right_functional"]

    paired = next(
        row for row in report["rows"] if row["instance_kind"] == "paired_farthest"
    )
    assert paired["binary_non_boolean_relation_count"] == 1

    four_local = next(
        row for row in report["rows"] if row["instance_kind"] == "four_local_non_cr"
    )
    assert four_local["parasite_constant_reject_count"] == 1
    assert four_local["negative_certificate_status"] == "relation_unsat_only"
    assert four_local["relation_accept_assignments"] == four_local["direct_cr_assignments"] == 0

    equal = next(row for row in report["rows"] if row["instance_kind"] == "equal")
    assert equal["row_class"] == "two_sat_candidate"
    assert equal["binary_non_boolean_relation_count"] == 0
    assert equal["parasite_relation_count"] == 1
    assert equal["complexity_claim_allowed"] == "two_sat_after_relation_build"


def test_relation_shape_search_classifies_non_boolean_relation_profiles():
    report = run_relation_shape_search(
        block_counts=[2],
        instance_kinds=["cycle", "paired_farthest", "equal", "four_local_non_cr"],
        repeats=1,
    )

    summary = report["summary"]
    assert summary["catalog_rows"] == 4
    assert summary["catalog_complete_rows"] == 4
    assert summary["validation_mismatches"] == 0
    assert summary["binary_relation_instances"] == 3
    assert summary["shape_class_histogram"] == {
        "active_two_regular": 1,
        "partial_bijection": 1,
        "sparse_partial_matching": 1,
    }
    assert summary["functional_relation_instances"] == 2
    assert summary["partial_bijection_relation_instances"] == 1
    assert summary["positive_parasite_free_relation_instances"] == 0
    assert summary["candidate_gadget_instances"] == 0
    assert report["candidate_gadgets"] == []

    cycle = next(
        row for row in report["relation_instances"] if row["instance_kind"] == "cycle"
    )
    assert cycle["shape_class"] == "sparse_partial_matching"
    assert cycle["domain_sizes"] == [6, 6]
    assert cycle["accepted_signature_count"] == 2
    assert cycle["left_degree_histogram"] == {"0": 4, "1": 2}
    assert cycle["right_degree_histogram"] == {"0": 4, "1": 2}
    assert cycle["composability_tags"] == ["promise_scaffold_only", "unary_gated"]

    paired = next(
        row
        for row in report["relation_instances"]
        if row["instance_kind"] == "paired_farthest"
    )
    assert paired["shape_class"] == "partial_bijection"
    assert paired["accepted_signature_count"] == 4
    assert "constant_loose" in paired["composability_tags"]
    assert "constant_blocked" not in paired["composability_tags"]

    blocked = next(
        row
        for row in report["relation_instances"]
        if row["instance_kind"] == "four_local_non_cr"
    )
    assert blocked["shape_class"] == "active_two_regular"
    assert blocked["accepted_signature_count"] == 8
    assert "constant_blocked" in blocked["composability_tags"]
    assert "relation_unsat_only" in blocked["composability_tags"]


def test_relation_chain_probe_finds_permutation_like_near_misses():
    report = run_relation_chain_probe(
        block_counts=[2],
        instance_kinds=["cycle", "paired_farthest", "equal", "four_local_non_cr"],
        repeats=8,
        seed=20260550,
    )

    summary = report["summary"]
    assert summary["rows"] == 11
    assert summary["complete_rows"] == 11
    assert summary["validation_mismatches"] == 0
    assert summary["assignment_incomplete_rows"] == 0
    assert summary["rows_with_functional_relations"] == 5
    assert summary["rows_with_restrictive_parasite_free_functional_candidate"] == 2
    assert summary["rows_with_permutation_like"] == 2
    assert summary["rows_with_restrictive_parasite_free_permutation_like"] == 2
    assert summary["rows_with_constant_reject"] == 5
    assert summary["full_unsat_explanation_histogram"] == {
        "constant_reject": 5,
        "sat": 6,
    }

    candidates = [
        row
        for row in report["rows"]
        if row["restrictive_parasite_free_functional_candidate"]
    ]
    assert len(candidates) == 2
    assert {row["shape_histogram"]["permutation_like"] for row in candidates} == {1}
    assert all(row["constant_reject_count"] == 0 for row in candidates)
    assert all(row["unary_restrictive_count"] == 0 for row in candidates)
    assert all(row["full_accept_count"] == 12 for row in candidates)
    assert all(row["functional_accept_count"] == 12 for row in candidates)
    assert all(row["parasite_accept_count"] == 72 for row in candidates)
    assert all(
        row["binary_relation_profiles"][0]["shape"] == "permutation_like"
        for row in candidates
    )


def test_relation_unsat_core_probe_minimizes_interaction_unsat():
    report = run_relation_unsat_core_probe(
        block_counts=[2],
        instance_kinds=["five_local_non_cr"],
        repeats=1,
        seed=20260550,
    )

    summary = report["summary"]
    assert summary["rows"] == 1
    assert summary["complete_rows"] == 1
    assert summary["validation_mismatches"] == 0
    assert summary["interaction_unsat_rows"] == 1
    assert summary["rows_with_minimal_core"] == 1
    assert summary["min_core_size"] == 2
    assert summary["constant_reject_rows"] == 0

    row = report["rows"][0]
    assert row["full_accept_count"] == 0
    assert row["binary_non_boolean_accept_count"] == 4
    assert row["parasite_accept_count"] == 16
    assert row["minimal_core_count"] == 1

    core = row["minimal_cores"][0]
    assert core["relation_indices"] == [1, 2]
    assert core["relation_kinds"] == [
        "unary_non_boolean",
        "binary_non_boolean_catalog",
    ]
    assert core["relation_shapes"] == ["unary_non_boolean", "sparse_partial_matching"]
    assert core["variables"] == ["0", "1"]
    assert core["variable_count"] == 2
    assert core["core_assignment_space"] == 36
    assert core["core_quartet_count"] == 6
    assert core["core_accept_count"] == 0
    assert core["proper_subsets_satisfiable"] is True

    removal_counts = {
        check["removed_relation_index"]: check["satisfying_assignment_count"]
        for check in core["proper_removal_checks"]
    }
    assert removal_counts == {1: 4, 2: 48}

    conflict = core["projection_conflicts"][0]
    assert conflict["binary_relation_index"] == 2
    assert conflict["unary_relation_index"] == 1
    assert conflict["variable"] == "0"
    assert conflict["status"] == "empty_intersection"
    assert conflict["binary_projection_indices"] == [2, 4]
    assert conflict["unary_accepted_indices"] == [0, 1, 3, 5]

    unary, binary = core["relations"]
    assert unary["accepted_index_tuples"] == [[0], [1], [3], [5]]
    assert binary["shape"] == "sparse_partial_matching"
    assert binary["accepted_index_tuples"] == [[2, 3], [4, 1]]
    assert binary["canonical_accepted_index_tuples"] == [[1, 4], [3, 2]]

    quartet_removals = core["source_quartet_removal_checks"]
    assert len(quartet_removals) == 6
    assert any(check["satisfying_assignment_count"] == 0 for check in quartet_removals)
    assert any(check["satisfying_assignment_count"] > 0 for check in quartet_removals)


def test_permutation_like_probe_checks_exact_small_quasi_scaffold():
    report = run_permutation_like_probe(
        repeats=8,
        seed=20260550,
        block_count=2,
        exact_quasi_max_n=8,
    )

    summary = report["summary"]
    assert summary["rows"] == 8
    assert summary["complete_rows"] == 8
    assert summary["validation_mismatches"] == 0
    assert summary["permutation_like_rows"] == 1
    assert summary["parasite_free_permutation_like_rows"] == 1
    assert summary["permutation_like_exact_quasi_scaffold_rows"] == 1
    assert summary["anomaly_count"] == 0
    assert "not prove NP-hardness" in summary["interpretation"]
    assert "not a general Hsu/McConnell reconstruction" in summary["promise_caveat"]

    row = next(row for row in report["rows"] if row["has_permutation_like"])
    assert row["seed"] == 20262574
    assert row["row_category"] == "permutation_like_parasite_free_exact_quasi_scaffold"
    assert row["parasite_free"] is True
    assert row["constant_reject_count"] == 0
    assert row["unary_restrictive_count"] == 0
    assert row["high_arity_count"] == 0
    assert row["full_accept_count"] == row["functional_accept_count"] == 12
    assert row["binary_non_boolean_accept_count"] == 12
    assert row["parasite_accept_count"] == 72

    quasi = row["exact_quasi_metrics"]
    assert quasi["promise_check_method"] == "exact_quasi_order_enumeration"
    assert quasi["scaffold_frontier_count"] == 18
    assert quasi["exact_quasi_order_count"] == 18
    assert quasi["scaffold_non_quasi_count"] == 0
    assert quasi["missing_quasi_order_count"] == 0
    assert quasi["scaffold_matches_exact_quasi_orders"] is True

    accept_quasi = row["relation_accept_quasi_metrics"]
    assert accept_quasi["relation_accept_assignment_count"] == 12
    assert accept_quasi["relation_accept_quasi_count"] == 12
    assert accept_quasi["relation_accept_non_quasi_count"] == 0
    assert accept_quasi["shape_stable_under_quasi_filter"] is True

    profile = row["permutation_like_profiles"][0]
    assert profile["catalog_hash"] == "2b53bb78399e16b4"
    assert profile["scope"] == ["0", "1"]
    assert profile["domain_sizes"] == [6, 6]
    assert profile["accepted_signature_count"] == 6
    assert profile["density"] == 1 / 6
    assert profile["accepted_index_tuples"] == [
        [0, 3],
        [1, 2],
        [2, 5],
        [3, 4],
        [4, 0],
        [5, 1],
    ]
    assert profile["cycle_type"] == [3, 3]
    assert profile["quartet_count"] == 3


def test_permutation_composition_probe_reports_no_clean_multiblock_candidate():
    report = run_permutation_composition_probe(
        block_counts=[2, 3, 4],
        repeats=16,
        seed=20260550,
        assignment_limit=1_000_000,
        component_product_limit=1_000_000,
    )

    summary = report["summary"]
    assert summary["rows"] == 48
    assert summary["complete_rows"] == 48
    assert summary["validation_mismatches"] == 0
    assert summary["assignment_incomplete_rows"] == 0
    assert summary["permutation_like_rows"] == 1
    assert summary["permutation_like_relation_instances"] == 1
    assert summary["multi_permutation_rows"] == 0
    assert summary["composition_candidate_rows"] == 0
    assert summary["single_permutation_only_rows"] == 1
    assert summary["max_permutation_component_edges"] == 1
    assert "not a proof" in summary["interpretation"]

    assert summary["by_block_count"]["2"]["single_permutation_only_rows"] == 1
    assert summary["by_block_count"]["3"]["permutation_like_rows"] == 0
    assert summary["by_block_count"]["4"]["permutation_like_rows"] == 0
    assert summary["by_block_count"]["3"]["constant_reject_rows"] == 15
    assert summary["by_block_count"]["4"]["constant_reject_rows"] == 16

    row = next(row for row in report["rows"] if row["permutation_like_count"] == 1)
    assert row["block_count"] == 2
    assert row["row_class"] == "single_permutation_only"
    assert row["parasite_free"] is True
    assert row["max_permutation_component_edges"] == 1
    assert row["has_multi_permutation_component"] is False


def test_relation_component_probe_reports_multi_edge_relations_blocked_by_parasites():
    report = run_relation_component_probe(
        block_counts=[2, 3, 4],
        instance_kinds=["paired_farthest"],
        repeats=16,
        seed=20260550,
        component_product_limit=1_000_000,
    )

    summary = report["summary"]
    assert summary["rows"] == 48
    assert summary["complete_rows"] == 48
    assert summary["validation_mismatches"] == 0
    assert summary["component_incomplete_rows"] == 0
    assert summary["binary_relation_rows"] == 48
    assert summary["binary_nonboolean_relation_instances"] == 150
    assert summary["multi_edge_component_rows"] == 32
    assert summary["parasite_free_rows"] == 1
    assert summary["parasite_free_multi_edge_rows"] == 0
    assert summary["sat_parasite_free_multi_edge_rows"] == 0
    assert summary["rows_with_constant_reject"] == 39
    assert summary["max_component_edges"] == 6
    assert "not a proof" in summary["interpretation"]

    assert summary["shape_histogram"]["active_two_regular"] == 78
    assert summary["shape_histogram"]["small_domain_bridge"] == 31
    assert summary["shape_histogram"]["permutation_like"] == 1
    assert summary["multi_edge_component_shape_histogram"]["active_two_regular"] == 70
    assert summary["multi_edge_component_shape_histogram"]["partial_bijection"] == 1

    assert summary["by_block_count"]["2"]["multi_edge_component_rows"] == 0
    assert summary["by_block_count"]["2"]["parasite_free_rows"] == 1
    assert summary["by_block_count"]["3"]["multi_edge_component_rows"] == 16
    assert summary["by_block_count"]["3"]["parasite_free_rows"] == 0
    assert summary["by_block_count"]["4"]["multi_edge_component_rows"] == 16
    assert summary["by_block_count"]["4"]["constant_reject_rows"] == 16

    row = next(row for row in report["rows"] if row["seed"] == 20263586)
    assert row["row_class"] == "multi_edge_blocked_by_parasite"
    assert row["relation_accept_assignments"] == 4
    assert row["constant_reject_count"] == 0
    assert row["unary_restrictive_count"] == 1
    assert row["max_component_edges"] == 4
    assert row["shape_histogram"] == {"small_domain_bridge": 3, "total_cover_dense": 1}
    assert row["components"][0]["accept_count"] == 4
    assert row["components"][0]["shape_histogram"] == {
        "small_domain_bridge": 3,
        "total_cover_dense": 1,
    }


def test_sparse_matching_conflict_probe_classifies_unary_and_binary_conflicts():
    report = run_sparse_matching_conflict_probe(
        block_counts=[2, 3],
        repeats=8,
        seed=20260550,
    )

    summary = report["summary"]
    assert summary["rows"] == 40
    assert summary["complete_rows"] == 40
    assert summary["validation_mismatches"] == 0
    assert summary["assignment_incomplete_rows"] == 0
    assert summary["sparse_rows"] == 14
    assert summary["sparse_relation_instances"] == 21
    assert summary["unique_sparse_hashes"] == 8
    assert summary["rows_with_empty_projection_conflict"] == 6
    assert summary["empty_projection_conflict_instances"] == 10
    assert summary["rows_with_sparse_multi_edge_component"] == 6
    assert summary["rows_with_sparse_zero_component"] == 3
    assert summary["max_sparse_component_edges"] == 3
    assert summary["rows_with_constant_reject"] == 28
    assert "not prove" in summary["interpretation"]

    assert summary["by_instance_kind"]["paired_farthest"]["sparse_rows"] == 0
    assert summary["by_instance_kind"]["five_local_non_cr"]["sparse_rows"] == 2
    assert summary["by_instance_kind"]["random"]["sparse_zero_component_rows"] == 3
    assert summary["row_class_histogram"]["sparse_binary_component_unsat"] == 3
    assert (
        summary["row_class_histogram"][
            "sparse_unary_empty_conflict_without_constant"
        ]
        == 1
    )

    t068_row = next(
        row
        for row in report["rows"]
        if row["instance_kind"] == "five_local_non_cr" and row["block_count"] == 2
    )
    assert t068_row["seed"] == 20308448
    assert t068_row["row_class"] == "sparse_unary_empty_conflict_without_constant"
    assert t068_row["constant_reject_count"] == 0
    assert t068_row["sparse_relation_count"] == 1
    assert t068_row["empty_projection_conflict_count"] == 1
    conflict = t068_row["sparse_unary_conflicts"][0]
    assert conflict["status"] == "empty_intersection"
    assert conflict["variable"] == "0"
    assert conflict["sparse_projection_indices"] == [2, 4]
    assert conflict["unary_accepted_indices"] == [0, 1, 3, 5]
    assert conflict["sparse_relation"]["accepted_index_tuples"] == [[2, 3], [4, 1]]

    binary_unsat = next(
        row
        for row in report["rows"]
        if row["row_class"] == "sparse_binary_component_unsat"
    )
    assert binary_unsat["constant_reject_count"] > 0
    assert binary_unsat["sparse_zero_component_count"] == 1
    zero_component = next(
        component
        for component in binary_unsat["sparse_components"]
        if component["zero_accept"]
    )
    assert zero_component["edge_count"] == 2
    assert zero_component["accept_count"] == 0
