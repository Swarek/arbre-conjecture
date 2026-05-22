"""Regression counterexamples discovered by research iterations.

Do not remove entries to make tests pass.  Add minimal matrices and expected
results when the conjecture tester finds a disagreement.
"""

from pc_circular.predicates import (
    find_farthest_crossing_violation,
    find_precircular_cR_violation,
    is_precircular_order_cR,
    passes_farthest_crossing_condition,
)
from pc_circular.oracle import exact_oracle_pc_tree
from pc_circular.pc_tree import balanced_pc_tree, represents_order
from pc_circular.solvers.candidate import _minimum_distance_cycle_order, _paired_farthest_order

COUNTEREXAMPLES = [
    {
        "name": "equal_distance_cR_but_farthest_crossing_fails",
        "kind": "non_strict_degeneracy",
        "D": [
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0],
        ],
        "order": [0, 1, 2, 3],
        "is_circular_robinson": True,
        "passes_farthest_crossing": False,
    },
    {
        "name": "strict_farthest_crossing_not_sufficient_for_cR",
        "kind": "strict_insufficiency",
        "D": [
            [0, 1, 1, 2],
            [1, 0, 1, 3],
            [1, 1, 0, 4],
            [2, 3, 4, 0],
        ],
        "order": [0, 1, 3, 2],
        "is_circular_robinson": False,
        "passes_farthest_crossing": True,
    },
    {
        "name": "globally_distinct_distances_farthest_not_sufficient",
        "kind": "strict_insufficiency",
        "D": [
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0],
        ],
        "order": [0, 1, 2, 3],
        "is_circular_robinson": False,
        "passes_farthest_crossing": True,
    },
    {
        "name": "minimum_distance_cycle_not_sufficient_for_cR",
        "kind": "minimum_cycle_false_positive",
        "D": [
            [0, 1, 2, 2, 2, 1],
            [1, 0, 1, 2, 2, 3],
            [2, 1, 0, 1, 2, 2],
            [2, 2, 1, 0, 1, 3],
            [2, 2, 2, 1, 0, 1],
            [1, 3, 2, 3, 1, 0],
        ],
        "order": [0, 1, 2, 3, 4, 5],
        "is_circular_robinson": False,
        "passes_farthest_crossing": False,
        "minimum_cycle_order": [0, 1, 2, 3, 4, 5],
    },
    {
        "name": "minimum_cycle_witness_not_sufficient_without_representation",
        "kind": "minimum_cycle_representation_false_positive",
        "D": [
            [0, 2, 3, 2, 1, 1],
            [2, 0, 1, 2, 1, 3],
            [3, 1, 0, 1, 2, 2],
            [2, 2, 1, 0, 3, 1],
            [1, 1, 2, 3, 0, 2],
            [1, 3, 2, 1, 2, 0],
        ],
        "order": [0, 4, 1, 2, 3, 5],
        "is_circular_robinson": True,
        "passes_farthest_crossing": True,
        "minimum_cycle_order": [0, 4, 1, 2, 3, 5],
        "pc_tree_kind": "mixed",
        "witness_represented": False,
        "pc_tree_oracle_exists": False,
    },
    {
        "name": "paired_farthest_witness_not_sufficient_without_representation",
        "kind": "paired_farthest_representation_false_positive",
        "D": [
            [0, 3, 2, 1],
            [3, 0, 1, 2],
            [2, 1, 0, 3],
            [1, 2, 3, 0],
        ],
        "order": [0, 3, 1, 2],
        "is_circular_robinson": True,
        "passes_farthest_crossing": True,
        "paired_farthest_order": [0, 3, 1, 2],
        "pc_tree_kind": "C",
        "witness_represented": False,
        "pc_tree_oracle_exists": False,
    },
    {
        "name": "paired_farthest_canonical_misses_represented_witness",
        "kind": "paired_farthest_canonical_incomplete_non_star",
        "D": [
            [0, 1, 2, 1, 2, 3],
            [1, 0, 2, 1, 3, 2],
            [2, 2, 0, 3, 1, 1],
            [1, 1, 3, 0, 2, 2],
            [2, 3, 1, 2, 0, 1],
            [3, 2, 1, 2, 1, 0],
        ],
        "order": [0, 1, 2, 5, 4, 3],
        "is_circular_robinson": True,
        "passes_farthest_crossing": True,
        "paired_farthest_order": [0, 1, 3, 5, 4, 2],
        "canonical_witness_represented": False,
        "pc_tree_kind": "mixed",
        "witness_represented": True,
        "pc_tree_oracle_exists": True,
    },
    {
        "name": "paired_farthest_high_chords_crossing_not_sufficient",
        "kind": "paired_farthest_high_crossing_false_positive",
        "D": [
            [0, 2, 1, 1, 2, 3],
            [2, 0, 2, 3, 1, 1],
            [1, 2, 0, 1, 3, 2],
            [1, 3, 1, 0, 2, 2],
            [2, 1, 3, 2, 0, 1],
            [3, 1, 2, 2, 1, 0],
        ],
        "order": [0, 1, 2, 5, 3, 4],
        "is_circular_robinson": False,
        "passes_farthest_crossing": True,
    },
]


def test_recorded_counterexamples_are_present():
    assert len(COUNTEREXAMPLES) >= 2


def test_recorded_counterexamples_match_predicates():
    for example in COUNTEREXAMPLES:
        D = example["D"]
        order = example["order"]
        assert is_precircular_order_cR(D, order) is example["is_circular_robinson"]
        assert passes_farthest_crossing_condition(D, order) is example["passes_farthest_crossing"]
        if example["is_circular_robinson"]:
            assert find_precircular_cR_violation(D, order) is None
        else:
            assert find_precircular_cR_violation(D, order) is not None
        if example["passes_farthest_crossing"]:
            assert find_farthest_crossing_violation(D, order) is None
        else:
            assert find_farthest_crossing_violation(D, order) is not None
        if "minimum_cycle_order" in example:
            assert _minimum_distance_cycle_order(D, len(D)) == tuple(example["minimum_cycle_order"])
        if "paired_farthest_order" in example:
            assert _paired_farthest_order(D, len(D)) == tuple(example["paired_farthest_order"])
        if "pc_tree_kind" in example:
            T = balanced_pc_tree(len(D), kind=example["pc_tree_kind"])
            if "canonical_witness_represented" in example:
                canonical_witness = example["paired_farthest_order"]
                assert represents_order(T, canonical_witness) is example["canonical_witness_represented"]
            assert represents_order(T, order) is example["witness_represented"]
            assert exact_oracle_pc_tree(D, T)["exists"] is example["pc_tree_oracle_exists"]
