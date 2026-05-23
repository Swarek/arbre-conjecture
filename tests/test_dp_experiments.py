import itertools
import random

from pc_circular.generators import (
    cycle_metric,
    equal_distance_instance,
    quasi_circular_not_circular_four_point,
    random_dissimilarity,
)
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR
from pc_circular.pc_tree import star_pc_tree
from pc_circular.solvers.dp_experiments import (
    bad_side_signature,
    bad_witness_arc_constraints_report,
    bad_witness_arc_order_report,
    bad_witnesses_by_pair,
    block_bad_side_signature,
    block_signature_bucket_report,
    find_signature_collision,
    forced_bad_side_pairs_in_block,
    find_bad_side_cr_violation,
    is_bad_witness,
    passes_bad_side_cr_test,
)


def _matrix_from_pair_values(n, values):
    D = [[0] * n for _ in range(n)]
    for (i, j), value in zip(itertools.combinations(range(n), 2), values):
        D[i][j] = D[j][i] = value
    return D


def test_bad_witnesses_keep_equal_distance_non_strict_case_clean():
    D = equal_distance_instance(5)
    assert all(not witnesses for witnesses in bad_witnesses_by_pair(D).values())
    assert passes_bad_side_cr_test(D, (0, 1, 2, 3, 4))
    assert bad_side_signature(D, (0, 1, 2, 3, 4))[(0, 2)] == {
        "a_to_b": (),
        "b_to_a": (),
    }


def test_bad_side_detects_known_quasi_circular_non_cr_order():
    D = quasi_circular_not_circular_four_point()
    order = (0, 1, 2, 3)
    violation = find_bad_side_cr_violation(D, order)
    assert violation is not None
    assert violation["pair"] == (0, 2)
    assert violation["quadruple"] == (0, 1, 2, 3)
    assert violation["lhs"] < violation["rhs"]
    assert not passes_bad_side_cr_test(D, order)


def test_cycle_metric_order_has_no_bad_side_violation():
    D = cycle_metric(6)
    order = (0, 1, 2, 3, 4, 5)
    assert is_precircular_order_cR(D, order)
    assert passes_bad_side_cr_test(D, order)


def test_is_bad_witness_uses_strict_inequality_for_equalities():
    D = [
        [0, 2, 2, 1],
        [2, 0, 2, 1],
        [2, 2, 0, 1],
        [1, 1, 1, 0],
    ]
    assert not is_bad_witness(D, 0, 1, 2)
    assert not is_bad_witness(D, 0, 1, 3)
    assert is_bad_witness(D, 0, 3, 1)


def test_bad_side_matches_precircular_cr_on_exhaustive_n4():
    n = 4
    pair_count = n * (n - 1) // 2
    for values in itertools.product((1, 2, 3), repeat=pair_count):
        D = _matrix_from_pair_values(n, values)
        for order in all_circular_orders(n):
            assert passes_bad_side_cr_test(D, order) is is_precircular_order_cR(D, order)
            report = bad_witness_arc_order_report(D, order)
            assert report["bad_witness_one_side"] is is_precircular_order_cR(D, order)
            assert not report["one_side_precircular_mismatch"]
            if report["bad_witness_set_arc"]:
                assert report["precircular"]


def test_bad_side_matches_precircular_cr_on_random_small_orders():
    rng = random.Random(20260523)
    for n in (5, 6):
        orders = list(all_circular_orders(n))
        for _ in range(20):
            D = random_dissimilarity(n, rng=rng, values=(1, 2, 3, 4))
            for order in orders:
                assert passes_bad_side_cr_test(D, order) is is_precircular_order_cR(D, order)


def test_bad_witness_set_arc_is_too_strong_for_precircular_cr():
    D = [
        [0, 2, 1, 1, 1],
        [2, 0, 3, 1, 1],
        [1, 3, 0, 2, 1],
        [1, 1, 2, 0, 1],
        [1, 1, 1, 1, 0],
    ]
    order = (0, 2, 4, 1, 3)

    report = bad_witness_arc_order_report(D, order)
    assert report["precircular"]
    assert report["bad_witness_one_side"]
    assert not report["bad_witness_set_arc"]
    assert report["first_bad_witness_set_arc_violation"] == {
        "pair": (0, 3),
        "bad_witnesses": (1, 2),
        "tested_set": (1, 2),
    }


def test_bad_witness_with_endpoints_arc_is_too_strong_for_equal_distances():
    D = equal_distance_instance(4)
    order = (0, 1, 2, 3)

    report = bad_witness_arc_order_report(D, order)
    assert report["precircular"]
    assert report["bad_witness_one_side"]
    assert report["bad_witness_set_arc"]
    assert not report["bad_witness_with_endpoints_arc"]
    assert report["first_bad_witness_with_endpoints_arc_violation"] == {
        "pair": (0, 2),
        "bad_witnesses": (),
        "tested_set": (0, 2),
    }


def test_bad_witness_with_endpoints_arc_is_not_sufficient_for_precircular_cr():
    D = [
        [0, 2, 1, 2],
        [2, 0, 2, 1],
        [1, 2, 0, 2],
        [2, 1, 2, 0],
    ]
    order = (0, 1, 2, 3)

    report = bad_witness_arc_order_report(D, order)
    assert not report["precircular"]
    assert not report["bad_witness_one_side"]
    assert report["bad_witness_with_endpoints_arc"]
    assert report["first_bad_witness_one_side_violation"]["pair"] == (0, 2)


def test_bad_witness_arc_constraints_report_keeps_truncated_absences_unknown():
    D = equal_distance_instance(5)
    report = bad_witness_arc_constraints_report(D, star_pc_tree(5), frontier_limit=1)

    assert not report["complete"]
    assert report["incomplete_reasons"] == ["frontier_limit reached"]
    assert report["order_source"] == "pc_tree_frontiers"
    assert report["counts"]["orders_seen"] == 1
    assert report["exists"]["precircular"] is True
    assert report["exists"]["strict_circular"] is None


def test_block_signature_tracks_forced_inside_external_pair():
    D = [
        [0, 3, 1, 1],
        [3, 0, 1, 1],
        [1, 1, 0, 3],
        [1, 1, 3, 0],
    ]
    block = (1, 0, 2)
    forced = forced_bad_side_pairs_in_block(D, block, universe=range(4))
    assert forced["inside_external"] == ((0, 3),)
    assert block_bad_side_signature(D, block, universe=range(4))[3] == (1, 2)


def test_block_signature_bucket_report_exposes_compression_ratio():
    D = equal_distance_instance(5)
    frontiers = [
        (0, 1, 2, 3),
        (0, 2, 1, 3),
        (3, 1, 2, 0),
    ]
    report = block_signature_bucket_report(D, frontiers, universe=range(5))
    assert report["frontier_count"] == 3
    assert report["signature_count"] == 2
    assert report["largest_bucket_size"] == 2
    assert report["collision_bucket_count"] == 1
    assert report["forced_reject_frontiers"] == 0
    assert report["frontiers_per_signature"] == 1.5
    assert report["median_bucket_size"] == 1.5
    assert any(item["endpoints"] == (0, 3) and item["signature_ratio"] == 0.5 for item in report["endpoint_conditioned"])


def test_signature_collision_finder_catches_intentionally_weak_signature():
    D = quasi_circular_not_circular_four_point()
    frontiers = [(0, 1, 2, 3), (0, 2, 1, 3)]
    collision = find_signature_collision(
        D,
        frontiers,
        contexts=[()],
        universe=range(4),
        signature_func=lambda _frontier: ("weak",),
    )
    assert collision is not None
    assert collision["cr_a"] is not collision["cr_b"]
    assert collision["violation_a"] is not None


def test_signature_collision_finder_catches_endpoints_only_collision():
    D = [
        [0, 4, 3, 4, 2, 2],
        [4, 0, 2, 2, 1, 1],
        [3, 2, 0, 2, 4, 3],
        [4, 2, 2, 0, 3, 2],
        [2, 1, 4, 3, 0, 1],
        [2, 1, 3, 2, 1, 0],
    ]
    collision = find_signature_collision(
        D,
        [(0, 2, 3, 1), (0, 3, 2, 1)],
        contexts=[(5, 4)],
        universe=range(6),
        signature_func=lambda frontier: (frontier[0], frontier[-1]),
    )
    assert collision is not None
    assert collision["cr_a"] is True
    assert collision["cr_b"] is False
    assert collision["violation_b"]["quadruple"] == (0, 3, 2, 1)


def test_default_block_signature_has_no_collision_on_equal_distance_context():
    D = equal_distance_instance(5)
    frontiers = [(0, 1, 2, 3), (0, 2, 1, 3)]
    assert find_signature_collision(D, frontiers, contexts=[(4,)], universe=range(5)) is None
