from math import factorial

from pc_circular.pc_tree import (
    balanced_pc_tree,
    c_node,
    enumerate_frontiers,
    leaf,
    labels,
    p_node,
    represents_order,
    sample_frontier,
    star_pc_tree,
)
from pc_circular.predicates import all_circular_orders


def circular_order_count(n):
    if n <= 2:
        return 1
    return factorial(n - 1) // 2


def test_star_pc_tree_enumerates_all_circular_orders_small_n():
    for n in range(1, 7):
        T = star_pc_tree(n)
        frontiers = set(enumerate_frontiers(T, canonical=True))
        assert len(frontiers) == circular_order_count(n)
        assert frontiers == set(all_circular_orders(n))


def test_represents_order_uses_circular_canonicalization():
    T = star_pc_tree(5)
    assert represents_order(T, (2, 3, 4, 0, 1))
    assert represents_order(T, (1, 0, 4, 3, 2))


def test_balanced_tree_frontiers_are_valid_permutations():
    T = balanced_pc_tree(6, kind="mixed")
    frontiers = enumerate_frontiers(T, canonical=True)
    assert frontiers
    for order in frontiers:
        assert sorted(order) == list(range(6))


def test_sample_frontier_is_represented_without_full_enumeration():
    T = balanced_pc_tree(7, kind="mixed")
    order = sample_frontier(T)
    assert sorted(order) == list(range(7))
    assert represents_order(T, order)


def test_represents_order_matches_exact_enumeration_on_small_trees():
    for T in [
        star_pc_tree(6),
        balanced_pc_tree(6, kind="C"),
        balanced_pc_tree(7, kind="mixed"),
        p_node([c_node([leaf(0), leaf(1)]), c_node([leaf(2), leaf(3)]), leaf(4)]),
    ]:
        represented = set(enumerate_frontiers(T, canonical=True))
        for order in all_circular_orders(len(labels(T))):
            assert represents_order(T, order) is (order in represented)


def test_represents_order_rejects_split_child_blocks():
    T = p_node([c_node([leaf(0), leaf(1)]), c_node([leaf(2), leaf(3)])])
    assert represents_order(T, (0, 1, 2, 3))
    assert not represents_order(T, (0, 2, 1, 3))


def test_represents_order_rejects_invalid_label_sets():
    T = star_pc_tree(4)
    assert not represents_order(T, (0, 1, 2))
    assert not represents_order(T, (0, 1, 1, 2))
    assert not represents_order(T, (0, 1, 2, 9))


def test_represents_order_respects_c_node_cyclic_order():
    T = c_node([leaf(0), leaf(1), leaf(2), leaf(3)])
    assert represents_order(T, (1, 2, 3, 0))
    assert represents_order(T, (3, 2, 1, 0))
    assert not represents_order(T, (0, 2, 1, 3))


def test_represents_order_does_not_rotate_internal_c_nodes():
    T = p_node([c_node([leaf(0), leaf(1), leaf(2)]), leaf(3)])
    assert represents_order(T, (0, 1, 2, 3))
    assert not represents_order(T, (1, 2, 0, 3))
