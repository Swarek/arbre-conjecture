from tools.pc_handwritten_gadget_probe import (
    BLOCKS,
    LABEL_BY_NAME,
    SKETCH_SEED_HIGH_PAIRS,
    evaluate_high_pair_set,
    make_block_gadget_matrix,
    run_handwritten_gadget_probe,
)


def test_block_gadget_matrix_uses_three_expected_levels():
    D = make_block_gadget_matrix(
        [(LABEL_BY_NAME["A0"], LABEL_BY_NAME["D1"])],
        within_value=1,
        base_value=2,
        high_value=3,
    )

    assert len(D) == 8
    for block in BLOCKS:
        left, right = block
        assert D[left][right] == 1
    assert D[LABEL_BY_NAME["A0"]][LABEL_BY_NAME["D1"]] == 3
    assert D[LABEL_BY_NAME["A0"]][LABEL_BY_NAME["B0"]] == 2


def test_evaluate_high_pair_set_keeps_free_and_fixed_orders_separate():
    row = evaluate_high_pair_set(SKETCH_SEED_HIGH_PAIRS)

    assert row["flags"]["sketch_seed"] is True
    assert row["free_p"]["frontier_count"] == 48
    assert row["free_p"]["accepted_frontier_count"] <= row["free_p"]["frontier_count"]
    assert sorted(row["fixed_c_orders"]) == ["ABCD", "ABDC", "ACBD"]
    assert row["bad_side_projection"]["obligation_count"] >= 0


def test_handwritten_gadget_probe_reports_bounded_search_without_solver_claim():
    report = run_handwritten_gadget_probe(
        max_high_pairs=1,
        include_sketch_pattern=False,
        profiles=("sketch_flat_2_2_3",),
        max_examples=5,
    )

    assert report["method"] == "t085_handwritten_4block_gadget_probe"
    assert report["parameters"]["max_high_pairs"] == 1
    assert report["summary"]["rows"] == 26
    assert len(report["sketch_seed_rows"]) == 1
    assert len(report["interesting_rows"]) <= 5
    assert "bounded diagnostic only" in report["summary"]["interpretation"]
