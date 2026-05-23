from itertools import combinations
import random

from pc_circular.generators import (
    equal_distance_instance,
    even_high_cycle_plus_low_hub,
    matching_high_graph_plus_low_hub,
    quasi_circular_not_circular_four_point,
)
from pc_circular.pc_tree import c_node, leaf, p_node, star_pc_tree
from pc_circular.solvers import brute_force
from pc_circular.solvers.local_constraints import (
    classify_order_obstructions,
    low_hub_strong_ordering_report,
    measure_obstruction_support,
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
