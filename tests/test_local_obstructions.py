from pc_circular.generators import (
    cycle_metric,
    five_local_non_cr_core,
    four_local_non_cr_core,
    padded_five_local_non_cr,
    padded_four_local_non_cr,
)
from pc_circular.local_obstructions import (
    induced_submatrix,
    local_obstruction_profile,
)
from tools.pc_local_obstruction_depth_probe import run_local_obstruction_depth_probe


def test_induced_submatrix_preserves_requested_order():
    D = [
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ]

    assert induced_submatrix(D, [2, 0]) == [[0, 2], [2, 0]]


def test_four_local_core_has_minimum_obstruction_size_five():
    profile = local_obstruction_profile(four_local_non_cr_core())

    assert profile["complete"]
    assert profile["global_exists"] is False
    assert profile["min_negative_subset_size"] == 5
    assert profile["negative_subset"] == [0, 1, 2, 3, 4]
    assert profile["all_subsets_positive_up_to"] == 4


def test_five_local_core_has_minimum_obstruction_size_six():
    profile = local_obstruction_profile(five_local_non_cr_core())

    assert profile["complete"]
    assert profile["global_exists"] is False
    assert profile["min_negative_subset_size"] == 6
    assert profile["negative_subset"] == [0, 1, 2, 3, 4, 5]
    assert profile["all_subsets_positive_up_to"] == 5


def test_global_exact_negative_beyond_subset_cap_is_complete():
    profile = local_obstruction_profile(
        five_local_non_cr_core(), max_subset_size=5, max_global_n=6
    )

    assert profile["complete"]
    assert profile["global_exists"] is False
    assert profile["global_reason"] == "exact_global_oracle"
    assert profile["min_negative_subset_size"] is None
    assert profile["all_subsets_positive_up_to"] == 5


def test_padded_obstructions_keep_local_depth_under_subset_cap():
    four_profile = local_obstruction_profile(padded_four_local_non_cr(9), max_subset_size=6)
    five_profile = local_obstruction_profile(padded_five_local_non_cr(9), max_subset_size=6)

    assert four_profile["min_negative_subset_size"] == 5
    assert four_profile["all_subsets_positive_up_to"] == 4
    assert five_profile["min_negative_subset_size"] == 6
    assert five_profile["all_subsets_positive_up_to"] == 5


def test_cycle_metric_has_no_visible_local_obstruction():
    profile = local_obstruction_profile(cycle_metric(6))

    assert profile["complete"]
    assert profile["global_exists"] is True
    assert profile["min_negative_subset_size"] is None
    assert profile["all_subsets_positive_up_to"] == 6


def test_local_obstruction_depth_probe_smoke():
    report = run_local_obstruction_depth_probe(
        sizes=[5, 6],
        instance_kinds=["cycle", "four_local_non_cr", "five_local_non_cr"],
        repeats=1,
        max_subset_size=6,
    )

    assert report["summary"]["rows"] == 4
    assert report["summary"]["negative_rows"] == 2
    assert report["summary"]["max_min_negative_subset_size"] == 6
