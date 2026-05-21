from math import factorial

from pc_circular.pc_tree import balanced_pc_tree, enumerate_frontiers, represents_order, star_pc_tree
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
