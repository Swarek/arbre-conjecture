from pc_circular.generators import cycle_metric, quasi_circular_not_circular_four_point, random_dissimilarity
from pc_circular.oracle import exact_oracle_all_orders, exact_oracle_pc_tree
from pc_circular.pc_tree import star_pc_tree
from pc_circular.solvers import brute_force


def test_oracle_agrees_with_bruteforce_on_small_random_instances():
    for n in range(1, 6):
        D = random_dissimilarity(n, values=(1, 2), rng=__import__("random").Random(n))
        T = star_pc_tree(n)
        assert brute_force.solve(D, pc_tree=T)["exists"] == exact_oracle_pc_tree(D, T)["exists"]


def test_cycle_metric_has_positive_witness():
    D = cycle_metric(5)
    result = exact_oracle_all_orders(D)
    assert result["exists"]
    assert result["order"] is not None


def test_restricting_to_one_bad_order_can_make_instance_negative():
    D = quasi_circular_not_circular_four_point()
    assert not exact_oracle_pc_tree(D, None)["exists"] is False
    assert not brute_force.solve(D, quasi_orders=[(0, 1, 2, 3)])["exists"]
