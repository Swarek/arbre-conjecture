from itertools import combinations
import random

from pc_circular.generators import (
    MIXED_INSTANCE_KINDS,
    even_high_cycle_plus_low_hub,
    five_local_non_cr_core,
    four_local_non_cr_core,
    instance_by_kind,
    instance_by_kind_with_metadata,
    non_bipartite_high_graph_plus_low_hub,
    odd_high_cycle_plus_low_hub,
    paired_farthest_matching,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
    permuted_cycle_metric,
)
from pc_circular.predicates import farthest_sets, validate_dissimilarity
from pc_circular.solvers import brute_force


def test_permuted_cycle_metric_is_valid_dissimilarity():
    D = permuted_cycle_metric(7, rng=random.Random(1))
    assert validate_dissimilarity(D) == 7
    assert sorted(D[0]) == sorted(instance_by_kind(7, kind="cycle")[0])


def test_paired_farthest_matching_has_unique_pairs_for_even_n():
    D = paired_farthest_matching(6, rng=random.Random(2))
    assert validate_dissimilarity(D) == 6
    farthest = farthest_sets(D)
    assert all(len(value) == 1 for value in farthest.values())
    assert all(next(iter(farthest[next(iter(value))])) == point for point, value in farthest.items())


def test_instance_by_kind_accepts_explicit_piste_f_families():
    assert validate_dissimilarity(instance_by_kind(5, kind="permuted_cycle", rng=random.Random(3))) == 5
    assert validate_dissimilarity(instance_by_kind(5, kind="paired_farthest", rng=random.Random(4))) == 5
    assert validate_dissimilarity(instance_by_kind(5, kind="four_local_non_cr")) == 5
    assert validate_dissimilarity(instance_by_kind(6, kind="five_local_non_cr")) == 6
    assert validate_dissimilarity(instance_by_kind(6, kind="odd_high_cycle_plus_low_hub")) == 6
    assert validate_dissimilarity(instance_by_kind(7, kind="even_high_cycle_plus_low_hub")) == 7
    assert validate_dissimilarity(instance_by_kind(6, kind="non_bipartite_high_graph_plus_low_hub")) == 6


def test_four_local_non_cr_core_is_global_negative_but_four_local_positive():
    D = four_local_non_cr_core()

    assert not brute_force.solve(D)["exists"]
    for subset in combinations(range(5), 4):
        submatrix = [[D[i][j] for j in subset] for i in subset]
        assert brute_force.solve(submatrix)["exists"]


def test_padded_four_local_non_cr_preserves_four_local_positive_core_obstruction():
    D = padded_four_local_non_cr(9)

    assert not brute_force.solve([[D[i][j] for j in range(5)] for i in range(5)])["exists"]
    for subset in combinations(range(9), 4):
        submatrix = [[D[i][j] for j in subset] for i in subset]
        assert brute_force.solve(submatrix)["exists"]


def test_five_local_non_cr_core_is_global_negative_but_five_local_positive():
    D = five_local_non_cr_core()

    assert not brute_force.solve(D)["exists"]
    for subset in combinations(range(6), 5):
        submatrix = [[D[i][j] for j in subset] for i in subset]
        assert brute_force.solve(submatrix)["exists"]


def test_padded_five_local_non_cr_preserves_five_local_positive_core_obstruction():
    D = padded_five_local_non_cr(9)

    assert not brute_force.solve([[D[i][j] for j in range(6)] for i in range(6)])["exists"]
    for subset in combinations(range(9), 5):
        submatrix = [[D[i][j] for j in subset] for i in subset]
        assert brute_force.solve(submatrix)["exists"]


def test_odd_high_cycle_plus_low_hub_is_vertex_critical_for_small_odd_cycles():
    for n in (6, 8):
        D = odd_high_cycle_plus_low_hub(n)

        assert not brute_force.solve(D)["exists"]
        for subset in combinations(range(n), n - 1):
            submatrix = [[D[i][j] for j in subset] for i in subset]
            assert brute_force.solve(submatrix)["exists"]


def test_non_bipartite_high_graph_plus_low_hub_is_large_negative_family():
    D = non_bipartite_high_graph_plus_low_hub(9)

    assert not brute_force.solve([[D[i][j] for j in range(6)] for i in range(6)])["exists"]
    high_degree = [
        sum(1 for j in range(9) if D[i][j] == 2)
        for i in range(9)
    ]
    assert max(high_degree) > 2


def test_even_high_cycle_plus_low_hub_has_no_six_point_obstruction_at_c8():
    D = even_high_cycle_plus_low_hub(9)

    assert not brute_force.solve(even_high_cycle_plus_low_hub(7))["exists"]
    for subset in combinations(range(9), 6):
        submatrix = [[D[i][j] for j in subset] for i in subset]
        assert brute_force.solve(submatrix)["exists"]


def test_instance_metadata_preserves_mixed_rng_sequence():
    rng_legacy = random.Random(9)
    rng_metadata = random.Random(9)

    legacy = instance_by_kind(7, kind="mixed", rng=rng_legacy)
    generated, metadata = instance_by_kind_with_metadata(7, kind="mixed", rng=rng_metadata)

    assert generated == legacy
    assert metadata["requested_kind"] == "mixed"
    assert metadata["resolved_kind"] in MIXED_INSTANCE_KINDS


def test_instance_metadata_for_explicit_kind_is_self_resolved():
    for kind in ["random", "cycle", "equal-distance", "paired_farthest"]:
        rng_legacy = random.Random(3)
        rng_metadata = random.Random(3)

        legacy = instance_by_kind(7, kind=kind, rng=rng_legacy)
        generated, metadata = instance_by_kind_with_metadata(7, kind=kind, rng=rng_metadata)

        assert generated == legacy
        assert validate_dissimilarity(generated) == 7
        assert metadata == {"requested_kind": kind, "resolved_kind": kind}
