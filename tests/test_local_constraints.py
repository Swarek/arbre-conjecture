from pc_circular.generators import equal_distance_instance, quasi_circular_not_circular_four_point
from pc_circular.pc_tree import c_node, leaf, p_node, star_pc_tree
from pc_circular.solvers.local_constraints import (
    classify_order_obstructions,
    measure_obstruction_support,
    project_farthest_sets_to_pc_nodes,
)


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
