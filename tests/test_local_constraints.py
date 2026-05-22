from pc_circular.generators import quasi_circular_not_circular_four_point
from pc_circular.pc_tree import c_node, leaf, p_node, star_pc_tree
from pc_circular.solvers.local_constraints import (
    classify_order_obstructions,
    measure_obstruction_support,
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
