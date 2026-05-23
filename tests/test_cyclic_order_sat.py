import random

from pc_circular.cyclic_order_sat import (
    local_chirotope_obstruction_profile,
    order_satisfies_same_side_system,
    same_side_constraint_satisfied,
    same_side_constraints_from_dissimilarity,
    solve_bad_side_chirotope,
)
from pc_circular.generators import (
    cycle_metric,
    even_high_cycle_plus_low_hub,
    five_local_non_cr_core,
    random_dissimilarity,
    single_bad_side_quartet_instance,
)
from pc_circular.oracle import exact_oracle_all_orders
from tools.pc_chirotope_high_girth_probe import run_chirotope_high_girth_probe


def test_same_side_constraint_detects_alternation():
    assert not same_side_constraint_satisfied((0, 1, 2, 3), (0, 2, 1, 3))
    assert same_side_constraint_satisfied((0, 1, 3, 2), (0, 2, 1, 3))


def test_single_bad_side_quartet_generates_one_same_side_constraint():
    D = single_bad_side_quartet_instance()
    assert same_side_constraints_from_dissimilarity(D) == ((0, 2, 1, 3),)
    assert not order_satisfies_same_side_system((0, 1, 2, 3), ((0, 2, 1, 3),))


def test_bad_side_chirotope_matches_exact_oracle_on_small_random_instances():
    for n in range(4, 7):
        for seed in range(8):
            D = random_dissimilarity(n, values=(1, 2, 3), rng=random.Random(seed))
            chirotope = solve_bad_side_chirotope(D)
            oracle = exact_oracle_all_orders(D)
            assert chirotope["complete"]
            assert chirotope["exists"] is oracle["exists"]


def test_cycle_metric_is_chirotope_positive():
    result = solve_bad_side_chirotope(cycle_metric(7))
    assert result["complete"]
    assert result["exists"] is True


def test_five_local_core_has_chirotope_depth_six():
    profile = local_chirotope_obstruction_profile(five_local_non_cr_core())
    assert profile["complete"]
    assert profile["global_exists"] is False
    assert profile["min_negative_subset_size"] == 6
    assert profile["all_subsets_positive_up_to"] == 5


def test_even_high_cycle_low_hub_is_high_girth_candidate_at_cap_six():
    D = even_high_cycle_plus_low_hub(9)
    profile = local_chirotope_obstruction_profile(D, max_subset_size=6, max_global_n=9)

    assert profile["complete"]
    assert profile["global_exists"] is False
    assert profile["min_negative_subset_size"] is None
    assert profile["all_subsets_positive_up_to"] == 6


def test_chirotope_high_girth_probe_smoke():
    report = run_chirotope_high_girth_probe(
        sizes=[6, 9],
        instance_kinds=["cycle", "padded_five_local_non_cr", "even_high_cycle_low_hub"],
        repeats=1,
        max_subset_size=6,
        max_global_n=9,
        oracle_crosscheck_n=6,
    )
    assert report["summary"]["rows"] == 5
    assert report["summary"]["oracle_mismatches"] == 0
    assert report["summary"]["max_min_negative_subset_size"] == 6
    assert report["summary"]["high_girth_candidates"] == 1
