import itertools
import random

from pc_circular.generators import (
    cycle_metric,
    equal_distance_instance,
    quasi_circular_not_circular_four_point,
    random_dissimilarity,
)
from pc_circular.pc_tree import balanced_pc_tree, c_node, enumerate_frontiers, leaf, p_node, star_pc_tree
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    is_precircular_order_cR,
    is_quasi_circular_order,
)
from pc_circular.solvers.sat_like_experiments import (
    _cyclic_atom_occurs,
    _nogood_matches,
    _project_atom_order_from_support_assignment,
    _project_labels_order_from_support_assignment,
    _side_of_witness_between_pair,
    _witness_side_cache_key,
    accepted_frontiers_by_csp,
    assignment_frontier_report,
    bad_side_grouped_support_outcome_profile,
    build_local_domains,
    compile_bad_side_nogoods,
    compile_bad_side_nogoods_grouped_first_hit_support_local,
    compile_bad_side_nogoods_grouped_support_local,
    compile_bad_side_nogoods_support_local,
    compile_cr_nogoods,
    compile_cr_nogoods_support_local,
    forbidden_cr_atoms,
    forbidden_bad_side_atoms,
    frontier_from_assignment,
    iter_local_assignments,
    prop45_nogood_frontier_report,
    prop45_nogood_frontier_search,
    quartet_support_paths,
    solve_compiled_bad_side_nogood_csp,
    solve_compiled_nogood_csp,
    solve_pruned_bad_side_nogood_csp,
    solve_nogood_csp,
    solve_pruned_nogood_csp,
    solve_pruned_nogood_csp_from_compilation,
    solve_grouped_first_hit_support_local_bad_side_nogood_csp,
    solve_grouped_support_local_bad_side_nogood_csp,
    solve_support_local_bad_side_nogood_csp,
)


def _nogood_keys(compilation):
    return {
        (
            tuple(nogood["atom"]),
            tuple((path, tuple(choice)) for path, choice in nogood["signature"]),
        )
        for nogood in compilation["nogoods"]
    }


def _nogood_signatures(compilation):
    return {
        tuple((path, tuple(choice)) for path, choice in nogood["signature"])
        for nogood in compilation["nogoods"]
    }


def _assert_first_hit_accounting(compilation):
    counts = compilation["counts"]

    assert (
        counts["first_hit_assignments"] + counts["first_hit_no_hit_assignments"]
        == counts["grouped_support_assignments_seen"]
    )
    assert counts["atom_hits"] == counts["first_hit_assignments"]
    assert sum(counts["first_hit_position_histogram"].values()) == counts["first_hit_assignments"]
    assert counts["first_hit_position_sum"] == sum(
        position * count
        for position, count in counts["first_hit_position_histogram"].items()
    )
    assert counts["first_hit_max_position"] == max(
        counts["first_hit_position_histogram"],
        default=0,
    )
    if counts["first_hit_assignments"] == 0:
        assert counts["first_hit_position_histogram"] == {}
        assert counts["first_hit_position_sum"] == 0
        assert counts["first_hit_max_position"] == 0
        assert counts["first_hit_average_position"] == 0.0
    else:
        assert counts["first_hit_average_position"] == (
            counts["first_hit_position_sum"] / counts["first_hit_assignments"]
        )
    assert all(
        1 <= position <= counts["max_atoms_per_support"]
        for position in counts["first_hit_position_histogram"]
    )
    assert counts["atom_checks"] == (
        counts["first_hit_position_sum"] + counts["first_hit_checks_spent_on_no_hit"]
    )
    assert counts["atom_checks_if_exhaustive_seen"] == (
        counts["atom_checks"] + counts["first_hit_checks_saved_on_hits"]
    )
    assert counts["atom_checks_saved_by_first_hit"] == (
        counts["atom_checks_if_exhaustive_seen"] - counts["atom_checks"]
    )
    assert counts["atom_checks_saved_by_first_hit"] == counts["first_hit_checks_saved_on_hits"]
    assert 0 <= counts["atom_checks_if_exhaustive_seen"] <= counts["atom_checks_if_exhaustive"]
    if compilation["complete"]:
        assert counts["atom_checks_if_exhaustive_seen"] == counts["atom_checks_if_exhaustive"]


def test_prop45_nogood_report_rejects_single_bad_quasi_order():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    report = prop45_nogood_frontier_report(D, quasi_orders=[order])

    assert report["complete"]
    assert report["counts"]["frontiers_seen"] == 1
    assert report["counts"]["checked_orders"] == 1
    assert report["counts"]["prop45_fail"] == 1
    assert report["counts"]["exact_non_cr"] == 1
    assert not report["prop45_exists"]
    assert not report["has_disagreement"]
    assert report["first_rejected"]["order"] == list(order)


def test_prop45_nogood_search_finds_cycle_metric_witness_in_star_tree():
    D = cycle_metric(5)
    result = prop45_nogood_frontier_search(D, pc_tree=star_pc_tree(5))

    assert result["exists"]
    assert result["complete"]
    assert result["order"] is not None
    assert result["report"]["exact_cr_exists"]
    assert not result["report"]["has_disagreement"]


def test_prop45_nogood_report_matches_exact_cr_on_quasi_frontiers_n4():
    n = 4
    pairs = list(itertools.combinations(range(n), 2))
    checked_instances = 0

    for values in itertools.product((1, 2, 3), repeat=len(pairs)):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(pairs, values):
            D[i][j] = D[j][i] = value

        quasi_orders = [
            order
            for order in all_circular_orders(n)
            if is_quasi_circular_order(D, order)
        ]
        if not quasi_orders:
            continue
        checked_instances += 1

        report = prop45_nogood_frontier_report(D, quasi_orders=quasi_orders)
        exact_exists = any(is_precircular_order_cR(D, order) for order in quasi_orders)

        assert not report["has_disagreement"]
        assert report["prop45_exists"] is exact_exists
        assert report["exact_cr_exists"] is exact_exists

    assert checked_instances == 657


def test_local_domain_assignment_frontiers_match_pc_tree_enumeration():
    trees = [
        star_pc_tree(4),
        balanced_pc_tree(6, kind="mixed"),
        c_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)]), leaf(4)]),
    ]

    for T in trees:
        report = assignment_frontier_report(T, max_p_degree=4)
        assert report["complete"]
        assert not report["encoding"]["unsupported"]
        assert set(report["frontiers"]) == set(enumerate_frontiers(T, canonical=True))


def test_frontier_from_assignment_reconstructs_expected_order():
    T = c_node([p_node([leaf(0), leaf(1)]), leaf(2), leaf(3)])
    assignment = {
        (): (2, 1, 0),
        (0,): (1, 0),
    }

    assert frontier_from_assignment(T, assignment) == (3, 2, 1, 0)


def test_cr_source_csp_matches_exact_frontier_filter():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260522))

    expected = {
        order
        for order in enumerate_frontiers(T, canonical=True)
        if is_precircular_order_cR(D, order)
    }
    actual = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)

    assert actual == expected


def test_local_domain_csp_reports_unsupported_large_p_without_false_decision():
    T = star_pc_tree(5)
    D = cycle_metric(5)
    encoding = build_local_domains(T, max_p_degree=3)
    result = solve_nogood_csp(D, T, source="cr", max_p_degree=3)
    compiled = solve_compiled_nogood_csp(D, T, max_p_degree=3)

    assert encoding["unsupported"]
    assert result["unsupported"]
    assert result["exists"] is None
    assert not result["complete"]
    assert result["order"] is None
    assert compiled["unsupported"]
    assert compiled["exists"] is None


def test_quartet_support_paths_include_nested_split_nodes():
    T = c_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)]), leaf(4)])

    assert quartet_support_paths(T, (0, 1, 2, 3)) == ((), (0,), (1,))
    assert quartet_support_paths(T, (0, 2, 3, 4)) == ((), (1,))


def test_omitting_nested_support_can_change_quartet_projection():
    T = c_node([leaf(0), p_node([leaf(1), leaf(2)]), leaf(3)])
    same_root = {(): (0, 1, 2)}
    assignment_a = {**same_root, (1,): (0, 1)}
    assignment_b = {**same_root, (1,): (1, 0)}
    atom = (0, 1, 2, 3)

    assert quartet_support_paths(T, atom) == ((), (1,))
    assert _cyclic_atom_occurs(frontier_from_assignment(T, assignment_a), atom)
    assert not _cyclic_atom_occurs(frontier_from_assignment(T, assignment_b), atom)


def test_project_atom_order_from_support_assignment_matches_full_assignment_projection():
    T = c_node([p_node([leaf(0), leaf(1)]), p_node([leaf(2), leaf(3)]), leaf(4)])
    atom = (0, 1, 2, 3)
    support = quartet_support_paths(T, atom)
    encoding = build_local_domains(T, max_p_degree=3)

    for assignment in iter_local_assignments(encoding):
        support_assignment = {path: assignment[path] for path in support}
        projected = _project_atom_order_from_support_assignment(T, atom, support_assignment)
        full_projection = tuple(label for label in frontier_from_assignment(T, assignment) if label in atom)

        assert projected == full_projection


def test_compiled_cr_nogoods_reject_wrapping_violation():
    D = quasi_circular_not_circular_four_point()
    T = c_node([leaf(3), leaf(0), leaf(1), leaf(2)])
    compilation = compile_cr_nogoods(D, T)
    result = solve_compiled_nogood_csp(D, T)

    assert any(atom_info["atom"] == (0, 1, 2, 3) for atom_info in forbidden_cr_atoms(D))
    assert compilation["counts"]["unique_nogoods"] >= 1
    assert _cyclic_atom_occurs((3, 0, 1, 2), (0, 1, 2, 3))
    assert not result["exists"]
    assert result["counts"]["false_positive_frontiers"] == 0
    assert result["counts"]["false_negative_frontiers"] == 0


def test_compiled_cr_nogoods_match_direct_cr_csp_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260523))
    expected = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_compiled_nogood_csp(D, T, max_p_degree=3)
    actual = {tuple(order) for order in result["accepted_frontiers"]}

    assert actual == expected
    assert result["counts"]["false_positive_frontiers"] == 0
    assert result["counts"]["false_negative_frontiers"] == 0


def test_bad_side_atoms_match_precircular_cr_on_exhaustive_n4():
    n = 4
    pair_count = n * (n - 1) // 2
    for values in itertools.product((1, 2, 3), repeat=pair_count):
        D = [[0] * n for _ in range(n)]
        for (i, j), value in zip(itertools.combinations(range(n), 2), values):
            D[i][j] = D[j][i] = value

        bad_side_atoms = {tuple(atom["atom"]) for atom in forbidden_bad_side_atoms(D)}
        cr_atoms = {tuple(atom["atom"]) for atom in forbidden_cr_atoms(D)}
        assert bad_side_atoms <= cr_atoms

        for order in all_circular_orders(n):
            has_bad_side_atom = any(_cyclic_atom_occurs(order, atom) for atom in bad_side_atoms)
            assert has_bad_side_atom is (not is_precircular_order_cR(D, order))


def test_bad_side_atoms_keep_equal_distance_clean():
    D = equal_distance_instance(6)
    T = balanced_pc_tree(6, kind="mixed")
    compilation = compile_bad_side_nogoods(D, T, max_p_degree=3)
    pruned = solve_pruned_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert forbidden_bad_side_atoms(D) == []
    assert compilation["counts"]["nonempty_bad_pair_count"] == 0
    assert compilation["counts"]["nontrivial_bad_pair_count"] == 0
    assert compilation["counts"]["unique_nogoods"] == 0
    assert pruned["counts"]["branches_pruned"] == 0
    assert pruned["counts"]["validation_false_positive_frontiers"] == 0
    assert pruned["counts"]["validation_false_negative_frontiers"] == 0


def test_compiled_bad_side_nogoods_reject_wrapping_violation():
    D = quasi_circular_not_circular_four_point()
    T = c_node([leaf(3), leaf(0), leaf(1), leaf(2)])
    compilation = compile_bad_side_nogoods(D, T)
    result = solve_compiled_bad_side_nogood_csp(D, T)

    assert any(atom_info["atom"] == (0, 1, 2, 3) for atom_info in forbidden_bad_side_atoms(D))
    assert compilation["counts"]["nontrivial_bad_pair_count"] >= 1
    assert compilation["counts"]["unique_nogoods"] >= 1
    assert not result["exists"]
    assert result["counts"]["false_positive_frontiers"] == 0
    assert result["counts"]["false_negative_frontiers"] == 0


def test_compiled_bad_side_nogoods_match_direct_cr_csp_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    expected = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_compiled_bad_side_nogood_csp(D, T, max_p_degree=3)
    actual = {tuple(order) for order in result["accepted_frontiers"]}

    assert actual == expected
    assert result["counts"]["false_positive_frontiers"] == 0
    assert result["counts"]["false_negative_frontiers"] == 0


def test_support_local_bad_side_nogoods_match_complete_compilation_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    complete = compile_bad_side_nogoods(D, T, max_p_degree=3)
    support_local = compile_bad_side_nogoods_support_local(D, T, max_p_degree=3)

    assert support_local["complete"] is True
    assert _nogood_signatures(support_local) == _nogood_signatures(complete)
    assert support_local["counts"]["unique_nogoods"] == len(_nogood_signatures(complete))
    assert support_local["counts"]["unique_nogoods"] <= complete["counts"]["unique_nogoods"]
    assert support_local["counts"]["support_assignments_seen"] == support_local["counts"]["support_product_total"]


def test_grouped_support_bad_side_nogoods_match_support_local_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    support_local = compile_bad_side_nogoods_support_local(D, T, max_p_degree=3)
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)

    assert grouped["complete"] is True
    assert _nogood_signatures(grouped) == _nogood_signatures(support_local)
    assert grouped["counts"]["unique_nogoods"] == support_local["counts"]["unique_nogoods"]
    assert grouped["counts"]["effective_signature_count"] == grouped["counts"]["unique_nogoods"]
    assert grouped["counts"]["grouped_support_product_total"] < support_local["counts"]["support_product_total"]
    assert grouped["counts"]["support_product_total_if_ungrouped"] == support_local["counts"]["support_product_total"]
    assert grouped["counts"]["grouped_support_assignments_seen"] == grouped["counts"]["grouped_support_product_total"]
    assert grouped["counts"]["atom_checks"] == support_local["counts"]["support_product_total"]
    assert grouped["counts"]["max_atoms_per_support"] > 1


def test_grouped_support_bad_side_solver_matches_direct_and_prunes_cycle_metric():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_grouped_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in result["accepted_frontiers"]} == direct
    assert result["counts"]["branches_pruned"] > 0
    assert result["counts"]["validation_false_positive_frontiers"] == 0
    assert result["counts"]["validation_false_negative_frontiers"] == 0


def test_grouped_first_hit_bad_side_nogoods_match_grouped_signatures():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)

    assert first_hit["complete"] is True
    assert _nogood_signatures(first_hit) == _nogood_signatures(grouped)
    assert first_hit["counts"]["unique_nogoods"] == grouped["counts"]["unique_nogoods"]
    assert first_hit["counts"]["stopped_after_first_hit"] is True
    assert first_hit["counts"]["atom_checks"] < grouped["counts"]["atom_checks"]
    assert first_hit["counts"]["atom_checks_if_exhaustive"] == grouped["counts"]["atom_checks"]
    assert first_hit["counts"]["atom_checks_if_exhaustive_seen"] == grouped["counts"]["atom_checks"]
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] == (
        grouped["counts"]["atom_checks"] - first_hit["counts"]["atom_checks"]
    )
    _assert_first_hit_accounting(first_hit)


def test_grouped_first_hit_bad_side_solver_matches_direct_and_prunes_cycle_metric():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_grouped_first_hit_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in result["accepted_frontiers"]} == direct
    assert result["counts"]["branches_pruned"] > 0
    assert result["counts"]["validation_false_positive_frontiers"] == 0
    assert result["counts"]["validation_false_negative_frontiers"] == 0


def test_grouped_first_hit_keeps_effective_signatures_on_dense_support_groups():
    T = c_node(
        [
            p_node([leaf(0), leaf(1), leaf(2)]),
            p_node([leaf(3), leaf(4), leaf(5)]),
            p_node([leaf(6), leaf(7), leaf(8)]),
        ]
    )
    D = cycle_metric(9)
    support_local = compile_bad_side_nogoods_support_local(D, T, max_p_degree=3)
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)

    assert first_hit["complete"] is True
    assert _nogood_signatures(first_hit) == _nogood_signatures(grouped)
    assert _nogood_signatures(first_hit) == _nogood_signatures(support_local)
    assert grouped["counts"]["max_atoms_per_support"] > 1
    assert first_hit["counts"]["atom_checks"] < grouped["counts"]["atom_checks"]
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] > 0
    assert first_hit["counts"]["first_hit_max_position"] <= grouped["counts"]["max_atoms_per_support"]
    assert first_hit["counts"]["first_hit_checks_saved_on_hits"] == first_hit["counts"]["atom_checks_saved_by_first_hit"]
    assert first_hit["counts"]["first_hit_assignments"] > 0
    _assert_first_hit_accounting(first_hit)


def test_grouped_first_hit_solver_matches_direct_on_dense_support_groups():
    T = c_node(
        [
            p_node([leaf(0), leaf(1), leaf(2)]),
            p_node([leaf(3), leaf(4), leaf(5)]),
            p_node([leaf(6), leaf(7), leaf(8)]),
        ]
    )
    D = cycle_metric(9)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_grouped_first_hit_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in result["accepted_frontiers"]} == direct
    assert result["counts"]["validation_false_positive_frontiers"] == 0
    assert result["counts"]["validation_false_negative_frontiers"] == 0


def test_grouped_first_hit_preserves_signatures_but_not_exhaustive_diagnostics():
    D = [
        [0, 3, 1, 2],
        [3, 0, 2, 1],
        [1, 2, 0, 1],
        [2, 1, 1, 0],
    ]
    T = balanced_pc_tree(4, kind="P")
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)

    assert _nogood_signatures(first_hit) == _nogood_signatures(grouped)
    assert first_hit["counts"]["unique_nogoods"] == grouped["counts"]["unique_nogoods"]
    assert first_hit["counts"]["atoms_with_nogoods"] < grouped["counts"]["atoms_with_nogoods"]
    assert first_hit["counts"]["pairs_with_nogoods"] < grouped["counts"]["pairs_with_nogoods"]
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] > 0


def test_grouped_first_hit_equal_distance_profile_has_no_hits_or_atoms():
    T = balanced_pc_tree(6, kind="mixed")
    D = equal_distance_instance(6)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)

    assert first_hit["counts"]["grouped_support_assignments_seen"] == 0
    assert first_hit["counts"]["first_hit_assignments"] == 0
    assert first_hit["counts"]["first_hit_no_hit_assignments"] == 0
    assert first_hit["counts"]["first_hit_average_position"] == 0.0
    assert first_hit["counts"]["first_hit_position_histogram"] == {}
    assert first_hit["counts"]["atom_checks"] == 0
    assert first_hit["counts"]["atom_hits"] == 0
    assert first_hit["counts"]["first_hit_position_sum"] == 0
    assert first_hit["counts"]["first_hit_max_position"] == 0
    assert first_hit["counts"]["first_hit_checks_spent_on_no_hit"] == 0
    assert first_hit["counts"]["first_hit_checks_saved_on_hits"] == 0
    assert first_hit["counts"]["atom_checks_if_exhaustive_seen"] == 0
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] == 0
    _assert_first_hit_accounting(first_hit)


def test_bad_side_support_outcome_profile_matches_first_hit_accounting():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)
    profile = bad_side_grouped_support_outcome_profile(D, T, max_p_degree=3, max_groups=None)

    assert profile["complete"] is True
    assert "exists" not in profile
    assert "order" not in profile
    assert "accepted_frontiers" not in profile
    assert profile["counts"]["support_group_count"] == first_hit["counts"]["support_group_count"]
    assert profile["counts"]["grouped_support_assignments_seen"] == first_hit["counts"][
        "grouped_support_assignments_seen"
    ]
    assert profile["counts"]["hit_assignments"] == first_hit["counts"]["first_hit_assignments"]
    assert profile["counts"]["no_hit_assignments"] == first_hit["counts"]["first_hit_no_hit_assignments"]
    assert profile["counts"]["classification_atom_checks"] == first_hit["counts"]["atom_checks"]
    assert profile["counts"]["exhaustive_atom_checks_seen"] == first_hit["counts"][
        "atom_checks_if_exhaustive_seen"
    ]
    assert profile["counts"]["no_hit_exhaustive_atom_checks"] == first_hit["counts"][
        "first_hit_checks_spent_on_no_hit"
    ]
    assert profile["counts"]["first_hit_position_sum"] == first_hit["counts"]["first_hit_position_sum"]
    assert profile["counts"]["pair_side_split_hit_assignments"] == profile["counts"]["hit_assignments"]
    assert profile["counts"]["pair_side_split_no_hit_assignments"] == profile["counts"][
        "no_hit_assignments"
    ]
    assert profile["counts"]["pair_side_split_mismatches"] == 0
    assert profile["counts"]["first_pair_side_split_mismatch"] is None
    assert profile["counts"]["pair_side_split_checks"] > 0
    assert profile["counts"]["pair_side_split_side_cache_hits"] > 0
    assert profile["counts"]["pair_side_split_side_cache_misses"] > 0
    assert profile["counts"]["pair_side_split_side_checks"] == (
        profile["counts"]["pair_side_split_side_cache_hits"]
        + profile["counts"]["pair_side_split_side_cache_misses"]
    )
    assert profile["counts"]["pair_side_split_cached_checks"] == (
        profile["counts"]["pair_side_split_side_cache_misses"]
        + profile["counts"]["pair_side_split_component_witness_checks"]
    )
    assert profile["counts"]["pair_side_split_bitset_cached_checks"] == (
        profile["counts"]["pair_side_split_side_cache_misses"]
        + profile["counts"]["pair_side_split_component_checks"]
    )
    assert profile["counts"]["pair_side_split_bitset_cached_checks"] < profile["counts"][
        "classification_atom_checks"
    ]
    assert profile["counts"]["unary_no_hit_certified_assignments"] == 0
    assert profile["counts"]["ambiguous_no_hit_assignments"] == profile["counts"]["no_hit_assignments"]
    assert profile["counts"]["ambiguous_no_hit_ratio"] == 1.0
    assert profile["groups"][0]["no_hit_exhaustive_atom_checks"] >= profile["groups"][-1][
        "no_hit_exhaustive_atom_checks"
    ]


def test_witness_side_cache_key_keeps_nested_support_choices():
    T = c_node([leaf(0), p_node([leaf(1), leaf(2)]), leaf(3)])
    pair = (0, 2)
    witness = 1
    assignment_a = {(): (0, 1, 2), (1,): (0, 1)}
    assignment_b = {(): (0, 1, 2), (1,): (1, 0)}

    assert quartet_support_paths(T, (pair[0], pair[1], witness)) == ((), (1,))
    assert _witness_side_cache_key(T, assignment_a, pair, witness) != _witness_side_cache_key(
        T,
        assignment_b,
        pair,
        witness,
    )

    order_a = _project_labels_order_from_support_assignment(T, (pair[0], pair[1], witness), assignment_a)
    order_b = _project_labels_order_from_support_assignment(T, (pair[0], pair[1], witness), assignment_b)
    assert order_a == (0, 1, 2)
    assert order_b == (0, 2, 1)
    assert _side_of_witness_between_pair(order_a, pair, witness) != _side_of_witness_between_pair(
        order_b,
        pair,
        witness,
    )


def test_bad_side_support_outcome_profile_reports_limit_and_unsupported():
    D = cycle_metric(6)
    T = balanced_pc_tree(6, kind="mixed")
    limited = bad_side_grouped_support_outcome_profile(D, T, max_p_degree=3, limit=1)

    assert limited["complete"] is False
    assert "exists" not in limited
    assert "order" not in limited
    assert "accepted_frontiers" not in limited
    assert limited["counts"]["grouped_support_assignments_seen"] == 1
    assert limited["counts"]["groups_profiled"] == 1
    assert limited["counts"]["hit_assignments"] + limited["counts"]["no_hit_assignments"] == 1
    assert (
        limited["counts"]["pair_side_split_hit_assignments"]
        + limited["counts"]["pair_side_split_no_hit_assignments"]
        == 1
    )
    assert limited["counts"]["pair_side_split_side_checks"] == (
        limited["counts"]["pair_side_split_side_cache_hits"]
        + limited["counts"]["pair_side_split_side_cache_misses"]
    )

    unsupported = bad_side_grouped_support_outcome_profile(cycle_metric(5), star_pc_tree(5), max_p_degree=3)
    assert unsupported["complete"] is False
    assert "exists" not in unsupported
    assert "order" not in unsupported
    assert "accepted_frontiers" not in unsupported
    assert unsupported["encoding"]["unsupported"]
    assert unsupported["counts"]["grouped_support_assignments_seen"] == 0
    assert unsupported["counts"]["pair_side_split_side_cache_hits"] == 0
    assert unsupported["counts"]["pair_side_split_side_cache_misses"] == 0
    assert unsupported["groups"] == []


def test_bad_side_support_outcome_profile_equal_distance_has_no_groups():
    T = balanced_pc_tree(6, kind="mixed")
    profile = bad_side_grouped_support_outcome_profile(equal_distance_instance(6), T, max_p_degree=3)

    assert profile["complete"] is True
    assert profile["counts"]["support_group_count"] == 0
    assert profile["counts"]["hit_assignments"] == 0
    assert profile["counts"]["no_hit_assignments"] == 0
    assert profile["counts"]["classification_atom_checks"] == 0
    assert profile["counts"]["pair_side_split_checks"] == 0
    assert profile["counts"]["pair_side_split_side_cache_hits"] == 0
    assert profile["counts"]["pair_side_split_side_cache_misses"] == 0
    assert profile["counts"]["pair_side_split_cached_checks"] == 0
    assert profile["counts"]["pair_side_split_bitset_cached_checks"] == 0
    assert "exists" not in profile
    assert "order" not in profile
    assert "accepted_frontiers" not in profile
    assert profile["groups"] == []


def test_grouped_support_compilation_reports_limit_without_false_completion():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3, limit=1)

    assert grouped["complete"] is False
    assert grouped["counts"]["grouped_support_assignments_seen"] == 1


def test_grouped_first_hit_compilation_reports_limit_without_false_completion():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3, limit=1)

    assert first_hit["complete"] is False
    assert first_hit["counts"]["grouped_support_assignments_seen"] == 1
    assert first_hit["counts"]["atom_checks_if_exhaustive_seen"] <= first_hit["counts"]["atom_checks_if_exhaustive"]
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] == (
        first_hit["counts"]["atom_checks_if_exhaustive_seen"] - first_hit["counts"]["atom_checks"]
    )
    _assert_first_hit_accounting(first_hit)


def test_grouped_support_reports_unsupported_large_p_without_false_decision():
    T = star_pc_tree(5)
    D = cycle_metric(5)
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)
    result = solve_grouped_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert grouped["complete"] is False
    assert grouped["encoding"]["unsupported"]
    assert grouped["counts"]["unique_nogoods"] == 0
    assert result["unsupported"]
    assert result["exists"] is None
    assert result["order"] is None


def test_grouped_first_hit_reports_unsupported_large_p_without_false_decision():
    T = star_pc_tree(5)
    D = cycle_metric(5)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)
    result = solve_grouped_first_hit_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert first_hit["complete"] is False
    assert first_hit["encoding"]["unsupported"]
    assert first_hit["counts"]["unique_nogoods"] == 0
    assert first_hit["counts"]["first_hit_assignments"] == 0
    assert first_hit["counts"]["first_hit_no_hit_assignments"] == 0
    assert first_hit["counts"]["atom_checks"] == 0
    assert first_hit["counts"]["atom_checks_if_exhaustive_seen"] == 0
    assert first_hit["counts"]["atom_checks_saved_by_first_hit"] == 0
    assert result["unsupported"]
    assert result["exists"] is None
    assert result["order"] is None


def test_grouped_support_signatures_do_not_prune_exact_cr_frontiers_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    grouped = compile_bad_side_nogoods_grouped_support_local(D, T, max_p_degree=3)
    encoding = grouped["encoding"]

    assert grouped["complete"] is True
    for assignment in iter_local_assignments(encoding):
        pruned = any(_nogood_matches(assignment, nogood["signature"]) for nogood in grouped["nogoods"])
        order = canonical_circular_order(frontier_from_assignment(T, assignment))
        if pruned:
            assert not is_precircular_order_cR(D, order)


def test_grouped_first_hit_signatures_do_not_prune_exact_cr_frontiers_on_small_tree():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    first_hit = compile_bad_side_nogoods_grouped_first_hit_support_local(D, T, max_p_degree=3)
    encoding = first_hit["encoding"]

    assert first_hit["complete"] is True
    for assignment in iter_local_assignments(encoding):
        pruned = any(_nogood_matches(assignment, nogood["signature"]) for nogood in first_hit["nogoods"])
        order = canonical_circular_order(frontier_from_assignment(T, assignment))
        if pruned:
            assert not is_precircular_order_cR(D, order)


def test_support_local_atom_identity_is_not_stable_under_global_canonicalization():
    D = [
        [0, 1, 2, 1, 2],
        [1, 0, 1, 1, 1],
        [2, 1, 0, 2, 1],
        [1, 1, 2, 0, 2],
        [2, 1, 1, 2, 0],
    ]
    T = balanced_pc_tree(5, kind="mixed")
    atom = (0, 2, 3, 4)
    support = quartet_support_paths(T, atom)
    shared_support = {
        (): (0, 1),
        (0,): (0, 1),
        (1,): (0, 1),
    }
    assignment_a = {**shared_support, (0, 0): (0, 1)}
    assignment_b = {**shared_support, (0, 0): (1, 0)}

    assert any(tuple(atom_info["atom"]) == atom for atom_info in forbidden_cr_atoms(D))
    assert support == ((), (0,), (1,))
    assert _project_atom_order_from_support_assignment(T, atom, shared_support) == (0, 2, 3, 4)

    canonical_projection_a = tuple(
        label for label in canonical_circular_order(frontier_from_assignment(T, assignment_a)) if label in atom
    )
    canonical_projection_b = tuple(
        label for label in canonical_circular_order(frontier_from_assignment(T, assignment_b)) if label in atom
    )

    assert canonical_projection_a == (0, 2, 3, 4)
    assert canonical_projection_b == (0, 4, 3, 2)
    assert _cyclic_atom_occurs(canonical_projection_a, atom)
    assert not _cyclic_atom_occurs(canonical_projection_b, atom)


def test_support_local_cr_nogoods_match_complete_compilation_on_wrapping_tree():
    D = quasi_circular_not_circular_four_point()
    T = c_node([leaf(3), leaf(0), leaf(1), leaf(2)])
    complete = compile_cr_nogoods(D, T)
    support_local = compile_cr_nogoods_support_local(D, T)

    assert support_local["complete"] is True
    assert _nogood_signatures(support_local) == _nogood_signatures(complete)
    assert support_local["counts"]["unique_nogoods"] == len(_nogood_signatures(complete))


def test_support_local_bad_side_solver_matches_direct_and_prunes_cycle_metric():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    result = solve_support_local_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in result["accepted_frontiers"]} == direct
    assert result["counts"]["branches_pruned"] > 0
    assert result["counts"]["validation_false_positive_frontiers"] == 0
    assert result["counts"]["validation_false_negative_frontiers"] == 0


def test_support_local_compilation_can_avoid_full_assignment_scan_per_atom():
    T = c_node(
        [
            p_node([leaf(0), leaf(1), leaf(2)]),
            p_node([leaf(3), leaf(4), leaf(5)]),
            p_node([leaf(6), leaf(7), leaf(8)]),
        ]
    )
    D = cycle_metric(9)
    support_local = compile_bad_side_nogoods_support_local(D, T, max_p_degree=3)

    assert support_local["complete"] is True
    assert support_local["counts"]["full_assignment_space"] == 2 * 6 * 6 * 6
    assert support_local["counts"]["max_support_product"] < support_local["counts"]["full_assignment_space"]


def test_support_local_compilation_reports_limit_without_false_completion():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260524))
    support_local = compile_bad_side_nogoods_support_local(D, T, max_p_degree=3, limit=1)

    assert support_local["complete"] is False
    assert support_local["counts"]["support_assignments_seen"] == 1


def test_bad_side_nogoods_are_no_larger_than_ordered_cr_nogoods_on_probe():
    T = balanced_pc_tree(6, kind="mixed")
    D = random_dissimilarity(6, values=(1, 2, 3), rng=random.Random(20260525))
    quartet_compilation = compile_cr_nogoods(D, T, max_p_degree=3)
    bad_side_compilation = compile_bad_side_nogoods(D, T, max_p_degree=3)

    assert len(bad_side_compilation["atoms"]) <= len(quartet_compilation["atoms"])
    assert bad_side_compilation["counts"]["unique_nogoods"] <= quartet_compilation["counts"]["unique_nogoods"]
    assert bad_side_compilation["counts"]["atoms_with_nogoods"] <= quartet_compilation["counts"]["atoms_with_nogoods"]


def test_pruned_nogood_csp_matches_compiled_and_prunes_cycle_metric():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    compiled = solve_compiled_nogood_csp(D, T, max_p_degree=3)
    pruned = solve_pruned_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in pruned["accepted_frontiers"]} == {
        tuple(order) for order in compiled["accepted_frontiers"]
    }
    assert pruned["counts"]["branches_pruned"] > 0
    assert pruned["counts"]["leaf_assignments_seen"] < pruned["counts"]["full_assignment_space"]
    assert pruned["counts"]["validation_false_positive_frontiers"] == 0
    assert pruned["counts"]["validation_false_negative_frontiers"] == 0


def test_pruned_bad_side_nogood_csp_matches_direct_and_prunes_cycle_metric():
    T = balanced_pc_tree(6, kind="mixed")
    D = cycle_metric(6)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)
    pruned = solve_pruned_bad_side_nogood_csp(D, T, max_p_degree=3)

    assert {tuple(order) for order in pruned["accepted_frontiers"]} == direct
    assert pruned["counts"]["branches_pruned"] > 0
    assert pruned["counts"]["validation_false_positive_frontiers"] == 0
    assert pruned["counts"]["validation_false_negative_frontiers"] == 0


def test_pruned_nogood_csp_accepts_all_when_no_cr_atoms_exist():
    T = balanced_pc_tree(5, kind="mixed")
    D = equal_distance_instance(5)
    pruned = solve_pruned_nogood_csp(D, T, max_p_degree=3)
    direct = accepted_frontiers_by_csp(D, T, source="cr", max_p_degree=3)

    assert pruned["compilation"]["counts"]["unique_nogoods"] == 0
    assert pruned["counts"]["branches_pruned"] == 0
    assert {tuple(order) for order in pruned["accepted_frontiers"]} == direct
