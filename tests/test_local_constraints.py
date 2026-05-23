from itertools import combinations
import random

from pc_circular.generators import (
    disjoint_chain_high_graph_plus_low_hub,
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    matching_high_graph_plus_low_hub,
    permuted_chain_high_graph_plus_low_hub,
    permuted_disjoint_chain_high_graph_plus_low_hub,
    quasi_circular_not_circular_four_point,
)
from pc_circular.oracle import exact_oracle_pc_tree
from pc_circular.pc_tree import (
    balanced_pc_tree,
    c_node,
    enumerate_frontiers,
    leaf,
    p_node,
    represents_order,
    star_pc_tree,
)
from pc_circular.predicates import all_circular_orders, passes_bad_side_precircular_cR
from pc_circular.solvers import brute_force
from pc_circular.solvers.local_constraints import (
    _matching_crossing_parts,
    classify_order_obstructions,
    iter_low_hub_strong_ordering_witnesses,
    low_hub_component_ferrers_strong_ordering_report,
    low_hub_ferrers_strong_ordering_report,
    low_hub_strong_ordering_report,
    measure_obstruction_support,
    pc_tree_guided_low_hub_matching_witness_report,
    project_farthest_sets_to_pc_nodes,
)


def _binary_low_hub_from_edges(m, edges):
    D = equal_distance_instance(m + 1)
    for a, b in edges:
        D[a][b] = D[b][a] = 2
    return D


def _zero_low_hub_from_edges(m, edges):
    D = [[0 for _ in range(m + 1)] for _ in range(m + 1)]
    for a, b in edges:
        D[a][b] = D[b][a] = 2
    return D


def test_classify_order_obstructions_returns_cr_witness():
    D = quasi_circular_not_circular_four_point()
    result = classify_order_obstructions(D, (0, 1, 2, 3))
    assert not result["is_circular_robinson"]
    assert result["cr_violation"]["quadruple"] == (0, 1, 2, 3)


def test_star_tree_projects_bad_quartet_to_four_branches():
    D = quasi_circular_not_circular_four_point()
    result = measure_obstruction_support(D, star_pc_tree(4), (0, 1, 2, 3))
    cr = next(item for item in result["obstructions"] if item["type"] == "cr")
    root = next(item for item in cr["node_projections"] if item["path"] == ())
    assert root["kind"] == "P"
    assert root["support"] == (0, 1, 2, 3)
    assert root["support_size"] == 4


def test_nested_tree_projection_sees_root_and_deeper_support():
    D = quasi_circular_not_circular_four_point()
    T = p_node([c_node([leaf(0), leaf(1)]), c_node([leaf(2), leaf(3)])])
    result = measure_obstruction_support(D, T, (0, 1, 2, 3))
    cr = next(item for item in result["obstructions"] if item["type"] == "cr")
    root = next(item for item in cr["node_projections"] if item["path"] == ())
    left = next(item for item in cr["node_projections"] if item["path"] == (0,))
    right = next(item for item in cr["node_projections"] if item["path"] == (1,))
    assert root["support"] == (0, 1)
    assert root["projected"] == ((0, 0), (1, 0), (2, 1), (3, 1))
    assert left["contained_points"] == (0, 1)
    assert right["contained_points"] == (2, 3)


def test_farthest_projection_reports_non_laminar_equal_distance_star():
    D = equal_distance_instance(6)
    result = project_farthest_sets_to_pc_nodes(D, star_pc_tree(6))
    root = result["nodes"][0]

    assert root["path"] == ()
    assert root["kind"] == "P"
    assert root["degree"] == 6
    assert root["branch_sizes"] == (1, 1, 1, 1, 1, 1)
    assert root["size_histogram"] == {5: 6}
    assert root["laminar_violation_count"] > 0
    assert root["declared_order_interval_violation_count"] == 0
    assert root["circular_ones_status"] == "compatible"
    assert root["circular_ones_compatible"] is True
    assert root["circular_ones_witness_order"] is not None


def test_farthest_projection_reports_declared_c_node_interval_violation():
    D = equal_distance_instance(5)
    D[4][0] = D[0][4] = 3
    D[4][2] = D[2][4] = 3
    T = c_node([leaf(0), leaf(1), leaf(2), leaf(3), leaf(4)])

    result = project_farthest_sets_to_pc_nodes(D, T)
    root = result["nodes"][0]
    point4 = next(item for item in root["projected_sets_by_point"] if item["point"] == 4)

    assert point4["farthest"] == (0, 2)
    assert point4["projection"] == (0, 2)
    assert point4["projection_size"] == 2
    assert point4["is_declared_order_interval"] is False
    assert {"point": 4, "projection": (0, 2)} in root["declared_order_interval_violations"]


def test_low_hub_i_projection_is_silent_on_refined_negative_pc_tree():
    D = even_high_cycle_plus_low_hub(7)
    T = balanced_pc_tree(7, kind="mixed")

    assert exact_oracle_pc_tree(D, T)["exists"] is False
    frontiers = enumerate_frontiers(T, canonical=True)
    assert len(frontiers) == 16
    assert all(not passes_bad_side_precircular_cR(D, order) for order in frontiers)

    report = project_farthest_sets_to_pc_nodes(D, T)
    assert all(node["circular_ones_status"] == "compatible" for node in report["nodes"])
    assert all(node["proper_nontrivial_count"] == 0 for node in report["nodes"])
    assert all(node["laminar_violation_count"] == 0 for node in report["nodes"])
    assert all(node["declared_order_interval_violation_count"] == 0 for node in report["nodes"])


def test_low_hub_strong_ordering_accepts_c4_and_rejects_c6_c8():
    c4 = _binary_low_hub_from_edges(4, [(1, 2), (2, 3), (3, 4), (1, 4)])
    c4_report = low_hub_strong_ordering_report(c4)
    assert c4_report["status"] == "strong_ordering_found"
    assert c4_report["strong_ordering_exists"] is True
    assert c4_report["witness_order_is_cr"] is True

    c6_report = low_hub_strong_ordering_report(even_high_cycle_plus_low_hub(7))
    assert c6_report["status"] == "no_strong_ordering"
    assert c6_report["strong_ordering_exists"] is False

    c8_report = low_hub_strong_ordering_report(even_high_cycle_plus_low_hub(9))
    assert c8_report["status"] == "no_strong_ordering"
    assert c8_report["strong_ordering_exists"] is False


def test_low_hub_strong_ordering_accepts_complete_bipartite_and_matching_controls():
    k33_edges = [(a, b) for a in (1, 2, 3) for b in (4, 5, 6)]
    k33_report = low_hub_strong_ordering_report(_binary_low_hub_from_edges(6, k33_edges))
    assert k33_report["status"] == "strong_ordering_found"
    assert k33_report["witness_order_is_cr"] is True

    matching_edges = [(1, 5), (2, 6), (3, 7), (4, 8)]
    matching_report = low_hub_strong_ordering_report(_binary_low_hub_from_edges(8, matching_edges))
    assert matching_report["status"] == "strong_ordering_found"
    assert matching_report["witness_order_is_cr"] is True


def test_low_hub_strong_ordering_accepts_permuted_matching_with_component_priority():
    for n in (5, 6, 7, 10, 21):
        for seed in range(20):
            D = matching_high_graph_plus_low_hub(n, rng=random.Random(seed))
            report = low_hub_strong_ordering_report(D, max_permutation_pairs=1)

            assert report["status"] == "strong_ordering_found"
            assert report["strong_ordering_exists"] is True
            assert report["checked_permutation_pairs"] == 1
            assert report["witness_order_is_cr"] is True


def test_low_hub_strong_ordering_witness_iterator_continues_past_first_witness():
    D = matching_high_graph_plus_low_hub(18)
    witnesses = list(iter_low_hub_strong_ordering_witnesses(D, max_permutation_pairs=20))

    assert witnesses
    assert all(item["status"] == "strong_ordering_found" for item in witnesses)
    assert all(item["witness_order_is_cr"] is True for item in witnesses)
    assert len({item["witness_order"] for item in witnesses}) > 1


def test_low_hub_strong_ordering_accepts_matching_with_multiple_hubs():
    D = matching_high_graph_plus_low_hub(20)
    report = low_hub_strong_ordering_report(D, max_permutation_pairs=1)

    assert len(report["hub_labels"]) == 2
    assert report["status"] == "strong_ordering_found"
    assert report["strong_ordering_exists"] is True
    assert report["checked_permutation_pairs"] == 1
    assert report["witness_order_is_cr"] is True


def test_low_hub_strong_ordering_accepts_chain_graph_control():
    chain_edges = []
    for a, degree in [(1, 4), (2, 3), (3, 2), (4, 1)]:
        chain_edges.extend((a, b) for b in range(5, 5 + degree))
    report = low_hub_strong_ordering_report(_binary_low_hub_from_edges(8, chain_edges))

    assert report["status"] == "strong_ordering_found"
    assert report["witness_order_is_cr"] is True


def test_low_hub_ferrers_report_accepts_permuted_chain_without_factorial_search():
    D = permuted_chain_high_graph_plus_low_hub(21, rng=random.Random(0))
    report = low_hub_ferrers_strong_ordering_report(D)

    assert report["status"] == "ferrers_strong_ordering_found"
    assert report["strong_ordering_exists"] is True
    assert report["witness_order_is_cr"] is True


def test_low_hub_ferrers_report_rejects_matching_as_non_ferrers_subcase():
    D = matching_high_graph_plus_low_hub(12)
    report = low_hub_ferrers_strong_ordering_report(D)

    assert report["status"] == "not_ferrers_high_graph"
    assert report["strong_ordering_exists"] is None


def test_low_hub_component_ferrers_report_accepts_disjoint_chain_without_factorial_search():
    D = permuted_disjoint_chain_high_graph_plus_low_hub(21, rng=random.Random(0))
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["status"] == "component_ferrers_strong_ordering_found"
    assert report["strong_ordering_exists"] is True
    assert report["component_count"] == 2
    assert report["witness_order_is_cr"] is True


def test_low_hub_component_ferrers_report_accepts_three_permuted_components():
    D = permuted_disjoint_chain_high_graph_plus_low_hub(16, components=3, rng=random.Random(7))
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["status"] == "component_ferrers_strong_ordering_found"
    assert report["component_count"] == 3
    assert report["witness_order_is_cr"] is True


def test_low_hub_component_ferrers_report_handles_empty_high_graph():
    D = equal_distance_instance(9)
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["status"] == "empty_high_graph"
    assert report["strong_ordering_exists"] is True
    assert report["component_count"] == 0
    assert report["witness_order_is_cr"] is True


def test_low_hub_component_ferrers_requires_same_component_order_on_both_sides():
    D = _binary_low_hub_from_edges(4, [(1, 3), (2, 4)])

    assert passes_bad_side_precircular_cR(D, (0, 1, 2, 3, 4))
    assert not passes_bad_side_precircular_cR(D, (0, 1, 2, 4, 3))


def test_low_hub_component_ferrers_report_accepts_matching_as_degenerate_components():
    D = matching_high_graph_plus_low_hub(12)
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["status"] == "component_ferrers_strong_ordering_found"
    assert report["strong_ordering_exists"] is True
    assert report["witness_order_is_cr"] is True


def test_low_hub_component_ferrers_report_rejects_non_ferrers_component():
    D = even_high_cycle_plus_low_hub(7)
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["status"] == "not_component_ferrers_high_graph"
    assert report["strong_ordering_exists"] is None


def test_low_hub_component_ferrers_report_handles_low_zero_and_multiple_hubs():
    D = disjoint_chain_high_graph_plus_low_hub(12)
    for i in range(11):
        D[i][11] = D[11][i] = 1
    for i in range(12):
        for j in range(i + 1, 12):
            if D[i][j] == 1:
                D[i][j] = D[j][i] = 0
    report = low_hub_component_ferrers_strong_ordering_report(D)

    assert report["low_value"] == 0
    assert len(report["hub_labels"]) == 2
    assert report["status"] == "component_ferrers_strong_ordering_found"
    assert report["witness_order_is_cr"] is True


def test_pc_tree_guided_low_hub_matching_finds_known_nonstar_witness():
    D = matching_high_graph_plus_low_hub(17)
    T = c_node(
        [
            leaf(0),
            p_node([leaf(i) for i in range(1, 9)]),
            c_node([leaf(i) for i in (9, 11, 13, 15, 10, 12, 14, 16)]),
        ]
    )
    report = pc_tree_guided_low_hub_matching_witness_report(D, T)

    assert report["status"] == "pc_tree_guided_matching_witness_found"
    assert report["witness_order"] == (0, 1, 3, 5, 7, 2, 4, 6, 8, 9, 11, 13, 15, 10, 12, 14, 16)
    assert report["templates_checked"] == 1
    assert report["frontiers_sampled"] == 0
    assert report["projected_frontiers_checked"] == 1
    assert report["witness_order_is_cr"] is True


def test_pc_tree_guided_low_hub_matching_handles_zero_low_value():
    D = _zero_low_hub_from_edges(4, [(1, 3), (2, 4)])
    T = c_node([leaf(i) for i in range(5)])
    report = pc_tree_guided_low_hub_matching_witness_report(D, T)

    assert report["low_value"] == 0
    assert report["status"] == "pc_tree_projected_matching_frontier_found"
    assert report["frontiers_sampled"] == 0
    assert report["segments_checked"] == 0
    assert report["witness_order_is_cr"] is True


def test_pc_tree_guided_low_hub_matching_accepts_split_hub_projected_frontier():
    D = matching_high_graph_plus_low_hub(6)
    T = c_node([leaf(0), p_node([leaf(1), leaf(2)]), leaf(5), p_node([leaf(3), leaf(4)])])
    nonrepresented_cR = (0, 5, 3, 4, 1, 2)
    report = pc_tree_guided_low_hub_matching_witness_report(D, T)

    assert exact_oracle_pc_tree(D, T)["exists"] is True
    assert passes_bad_side_precircular_cR(D, nonrepresented_cR)
    assert not represents_order(T, nonrepresented_cR)
    assert report["status"] == "pc_tree_projected_matching_frontier_found"
    assert report["strong_ordering_exists"] is True
    assert report["witness_order"] == (0, 1, 2, 5, 3, 4)
    assert report["projected_order"] == (1, 2, 3, 4)
    assert report["segments_checked"] == 0
    assert report["witness_order_is_cr"] is True
    assert represents_order(T, report["witness_order"])


def test_pc_tree_guided_low_hub_matching_rejects_noncrossing_projected_frontier():
    D = matching_high_graph_plus_low_hub(6)
    T = c_node([leaf(0), leaf(1), leaf(3), leaf(2), leaf(4), leaf(5)])
    report = pc_tree_guided_low_hub_matching_witness_report(D, T, frontier_limit=0)

    assert exact_oracle_pc_tree(D, T)["exists"] is False
    assert report["status"] == "no_pc_tree_guided_matching_witness_found"
    assert report["strong_ordering_exists"] is None
    assert report["projected_frontiers_checked"] == 2


def test_matching_crossing_projection_matches_cr_for_fixed_orders_small():
    for n in range(5, 9):
        D = matching_high_graph_plus_low_hub(n)
        high = max(D[i][j] for i in range(n) for j in range(i + 1, n))
        neighbors = {
            i: tuple(j for j in range(n) if i != j and D[i][j] == high)
            for i in range(n)
        }
        pairs = tuple(
            sorted(
                tuple(sorted((i, values[0])))
                for i, values in neighbors.items()
                if values and i < values[0]
            )
        )

        for order in all_circular_orders(n):
            has_crossing_projection = _matching_crossing_parts(order, pairs) is not None
            assert has_crossing_projection == passes_bad_side_precircular_cR(D, order)


def test_pc_tree_guided_low_hub_matching_frontier_limit_is_incomplete():
    D = matching_high_graph_plus_low_hub(8)
    T = p_node([leaf(4), c_node([leaf(1), leaf(2)]), leaf(5), leaf(7), leaf(6), leaf(3), leaf(0)])

    limited = pc_tree_guided_low_hub_matching_witness_report(D, T, frontier_limit=64)
    extended = pc_tree_guided_low_hub_matching_witness_report(D, T, frontier_limit=80)

    assert exact_oracle_pc_tree(D, T)["exists"] is True
    assert limited["status"] == "no_pc_tree_guided_matching_witness_found"
    assert limited["strong_ordering_exists"] is None
    assert extended["status"] == "pc_tree_guided_matching_witness_found"
    assert extended["witness_order_is_cr"] is True


def test_pc_tree_guided_low_hub_matching_reports_nonapplicable_controls():
    for D, T in (
        (even_high_cycle_plus_low_hub(7), star_pc_tree(7)),
        (even_high_cycle_plus_low_hub(9), star_pc_tree(9)),
        (_binary_low_hub_from_edges(7, [(1, 2), (1, 5), (2, 3), (2, 4), (3, 6), (4, 7)]), star_pc_tree(8)),
    ):
        report = pc_tree_guided_low_hub_matching_witness_report(D, T)
        assert report["status"] == "not_matching_high_graph"
        assert report["strong_ordering_exists"] is None


def test_low_hub_strong_ordering_rejects_tree_counterexample():
    tree_edges = [(1, 2), (1, 5), (2, 3), (2, 4), (3, 6), (4, 7)]
    D = _binary_low_hub_from_edges(7, tree_edges)
    report = low_hub_strong_ordering_report(D)

    assert report["status"] == "no_strong_ordering"
    assert report["strong_ordering_exists"] is False
    assert brute_force.solve(D)["exists"] is False


def test_low_hub_strong_ordering_reports_non_bipartite_high_graph():
    triangle = _binary_low_hub_from_edges(3, [(1, 2), (2, 3), (1, 3)])
    report = low_hub_strong_ordering_report(triangle)

    assert report["status"] == "non_bipartite_high_graph"
    assert report["strong_ordering_exists"] is False


def test_low_hub_strong_ordering_handles_zero_low_value_triangle():
    triangle = _zero_low_hub_from_edges(3, [(1, 2), (2, 3), (1, 3)])
    report = low_hub_strong_ordering_report(triangle)

    assert report["low_value"] == 0
    assert report["status"] == "non_bipartite_high_graph"
    assert report["strong_ordering_exists"] is False
    assert report["witness_order"] is None
    assert brute_force.solve(triangle)["exists"] is False


def test_low_hub_strong_ordering_reports_nonapplicable_and_limit_statuses():
    no_hub = _binary_low_hub_from_edges(4, [(1, 2), (2, 3), (3, 4), (1, 4), (0, 1)])
    assert low_hub_strong_ordering_report(no_hub)["status"] == "no_low_hub"

    not_binary = equal_distance_instance(4)
    not_binary[0][1] = not_binary[1][0] = 2
    not_binary[2][3] = not_binary[3][2] = 3
    assert low_hub_strong_ordering_report(not_binary)["status"] == "not_binary_two_level"

    matching_edges = [(1, 5), (2, 6), (3, 7), (4, 8)]
    limited = low_hub_strong_ordering_report(_binary_low_hub_from_edges(8, matching_edges), max_permutation_pairs=0)
    assert limited["status"] == "unsupported_permutation_limit"
    assert limited["complete"] is False

    delayed_positive_edges = [(1, 2), (1, 6), (2, 5), (3, 4)]
    delayed_positive = _binary_low_hub_from_edges(6, delayed_positive_edges)
    limited_positive = low_hub_strong_ordering_report(delayed_positive, max_permutation_pairs=1)
    assert limited_positive["status"] == "unsupported_permutation_limit"
    assert limited_positive["strong_ordering_exists"] is None
    full_positive = low_hub_strong_ordering_report(delayed_positive)
    assert full_positive["status"] == "strong_ordering_found"
    assert full_positive["witness_order_is_cr"] is True


def test_low_hub_strong_ordering_matches_oracle_for_tiny_high_graphs():
    for m in range(1, 6):
        pairs = list(combinations(range(1, m + 1), 2))
        for mask in range(1 << len(pairs)):
            edges = [pairs[index] for index in range(len(pairs)) if (mask >> index) & 1]
            D = _binary_low_hub_from_edges(m, edges)
            report = low_hub_strong_ordering_report(D)
            exact = brute_force.solve(D)["exists"]

            assert report["complete"] is True
            assert report["strong_ordering_exists"] == exact
