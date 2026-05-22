import random

from pc_circular.generators import (
    instance_by_kind,
    paired_farthest_matching,
    permuted_cycle_metric,
)
from pc_circular.predicates import farthest_sets, validate_dissimilarity


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
