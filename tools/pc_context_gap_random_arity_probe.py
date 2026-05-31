#!/usr/bin/env python3
"""T101 randomized search for higher-order gap relations."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pc_circular.pc_tree import enumerate_frontiers, labels  # noqa: E402
from pc_circular.solvers.local_constraints import (  # noqa: E402
    iter_internal_node_child_labels,
)
from pc_circular.solvers.partial_obligation_experiments import (  # noqa: E402
    _first_missing_pairwise_tuple,
    _is_gap_composition_projection,
    _iter_pnode_obligation_projections,
    _missing_cyclic_gap_signature,
    _pairwise_closure,
    _visible_global_role_order_signature,
)
from pc_circular.solvers.width4_experiments import (  # noqa: E402
    induced_child_circular_order,
)
from tools.pc_context_gap_arity_probe import (  # noqa: E402
    _instance,
    _is_applicable,
    _json_ready,
    _parse_ints,
    _parse_strings,
    _pc_tree,
    _repeat_count,
    _stable_offset,
)


def _hist_increment(histogram: dict, key, amount: int = 1) -> None:
    histogram[key] = histogram.get(key, 0) + amount


def _sample_index_tuples(
    *,
    rng: random.Random,
    count: int,
    arity: int,
    sample_count: int,
    max_attempts: int,
) -> tuple[list[tuple[int, ...]], int, bool]:
    total = math.comb(count, arity) if count >= arity else 0
    if total <= sample_count:
        return list(combinations(range(count), arity)), 0, True

    seen = set()
    attempts = 0
    while len(seen) < sample_count and attempts < max_attempts:
        attempts += 1
        seen.add(tuple(sorted(rng.sample(range(count), arity))))
    return sorted(seen), attempts, len(seen) == total


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    projection_tuple_size: int,
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    rng = random.Random(seed)
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")

    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = tuple(raw_frontiers[:frontier_limit])

    node_infos = [
        node_info
        for node_info in iter_internal_node_child_labels(T)
        if node_info["kind"] == "P"
    ]
    node_by_path = {tuple(node_info["path"]): node_info for node_info in node_infos}
    local_order_by_path = {path: {} for path in node_by_path}
    for path, node_info in node_by_path.items():
        child_label_sets = node_info["child_label_sets"]
        for frontier in frontiers:
            local_order_by_path[path][frontier] = induced_child_circular_order(
                frontier,
                child_label_sets,
            )

    open_obligations = tuple(
        sorted(
            (
                obligation
                for obligation in _iter_pnode_obligation_projections(D, T)
                if _is_gap_composition_projection(obligation, scope)
            ),
            key=lambda obligation: (
                obligation["same_side"],
                obligation["path"],
                obligation["fine_role_pattern"],
                obligation["projected_roles"],
            ),
        )
    )
    total_combination_count = (
        math.comb(len(open_obligations), projection_tuple_size)
        if len(open_obligations) >= projection_tuple_size
        else 0
    )
    max_attempts = max(sample_count, sample_count * max_attempt_multiplier)
    sampled_index_tuples, random_attempt_count, exhausted = _sample_index_tuples(
        rng=rng,
        count=len(open_obligations),
        arity=projection_tuple_size,
        sample_count=sample_count,
        max_attempts=max_attempts,
    )

    sampled_tuple_count = 0
    skipped_same_obligation_tuple_count = 0
    relation_case_count = 0
    unary_sufficient_case_count = 0
    binary_sufficient_case_count = 0
    higher_order_case_count = 0
    product_false_case_count = 0
    pairwise_false_case_count = 0
    product_false_tuple_count = 0
    pairwise_false_tuple_count = 0
    max_product_size = 0
    max_pairwise_closure_size = 0
    max_actual_relation_size = 0
    max_pairwise_false_count = 0
    min_required_arity_histogram: dict = {}
    tuple_distinct_obligation_histogram: dict = {}
    actual_relation_size_histogram: dict = {}
    product_size_histogram: dict = {}
    pairwise_closure_size_histogram: dict = {}
    binary_sufficient_examples = []
    higher_order_examples = []

    for index_tuple in sampled_index_tuples:
        obligation_tuple = tuple(open_obligations[index] for index in index_tuple)
        distinct_same_side_count = len(
            {obligation["same_side"] for obligation in obligation_tuple}
        )
        if distinct_same_side_count < min_distinct_obligations:
            skipped_same_obligation_tuple_count += 1
            continue
        sampled_tuple_count += 1
        _hist_increment(tuple_distinct_obligation_histogram, distinct_same_side_count)

        relation_by_visible: dict[tuple, set[tuple]] = {}
        for frontier in frontiers:
            visible_parts = []
            gap_parts = []
            for index, obligation in enumerate(obligation_tuple):
                path = obligation["path"]
                local_order = local_order_by_path[path][frontier]
                visible_order = _visible_global_role_order_signature(
                    frontier,
                    obligation["projected_roles"],
                )
                gap_signature = _missing_cyclic_gap_signature(
                    frontier,
                    obligation["same_side"],
                    obligation["projected_roles"],
                )
                identity = (index, obligation["same_side"], path)
                visible_parts.append((identity, local_order, visible_order))
                gap_parts.append((identity, gap_signature))
            relation_by_visible.setdefault(tuple(visible_parts), set()).add(
                tuple(gap_parts)
            )

        for visible_key, actual_relation in relation_by_visible.items():
            relation_case_count += 1
            actual_size = len(actual_relation)
            marginals = tuple(
                {gap_tuple[index] for gap_tuple in actual_relation}
                for index in range(projection_tuple_size)
            )
            product_size = 1
            for values in marginals:
                product_size *= len(values)
            pairwise = _pairwise_closure(actual_relation, projection_tuple_size)
            pairwise_size = len(pairwise)
            product_false_count = product_size - actual_size
            pairwise_false_count = pairwise_size - actual_size

            max_product_size = max(max_product_size, product_size)
            max_pairwise_closure_size = max(max_pairwise_closure_size, pairwise_size)
            max_actual_relation_size = max(max_actual_relation_size, actual_size)
            max_pairwise_false_count = max(
                max_pairwise_false_count,
                pairwise_false_count,
            )
            _hist_increment(actual_relation_size_histogram, actual_size)
            _hist_increment(product_size_histogram, product_size)
            _hist_increment(pairwise_closure_size_histogram, pairwise_size)

            if product_false_count:
                product_false_case_count += 1
                product_false_tuple_count += product_false_count

            if product_size == actual_size:
                unary_sufficient_case_count += 1
                required_arity = 1
            elif pairwise_false_count == 0:
                binary_sufficient_case_count += 1
                required_arity = 2
                if len(binary_sufficient_examples) < max_examples:
                    binary_sufficient_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"]
                                for obligation in obligation_tuple
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_tuple
                            ),
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "pairwise_closure_size": pairwise_size,
                        }
                    )
            else:
                higher_order_case_count += 1
                pairwise_false_case_count += 1
                pairwise_false_tuple_count += pairwise_false_count
                required_arity = ">=3"
                if len(higher_order_examples) < max_examples:
                    higher_order_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"]
                                for obligation in obligation_tuple
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_tuple
                            ),
                            "fine_role_patterns": tuple(
                                obligation["fine_role_pattern"]
                                for obligation in obligation_tuple
                            ),
                            "visible_key": visible_key,
                            "actual_gap_tuples": tuple(
                                sorted(actual_relation, key=repr)[:max_examples]
                            ),
                            "missing_pairwise_tuple": _first_missing_pairwise_tuple(
                                pairwise,
                                actual_relation,
                            ),
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "pairwise_closure_size": pairwise_size,
                            "pairwise_false_count": pairwise_false_count,
                        }
                    )
            _hist_increment(min_required_arity_histogram, required_arity)

    return {
        "n": len(D),
        "pc_tree_kind": pc_tree_kind,
        "instance_kind": instance_kind,
        "repeat": repeat,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "complete": not frontier_truncated and exhausted,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "open_obligation_projection_count": len(open_obligations),
        "projection_tuple_size": projection_tuple_size,
        "total_combination_count": total_combination_count,
        "random_attempt_count": random_attempt_count,
        "sampled_index_tuple_count": len(sampled_index_tuples),
        "sampled_tuple_count": sampled_tuple_count,
        "skipped_same_obligation_tuple_count": skipped_same_obligation_tuple_count,
        "sample_exhausted": exhausted,
        "relation_case_count": relation_case_count,
        "unary_sufficient_case_count": unary_sufficient_case_count,
        "binary_sufficient_case_count": binary_sufficient_case_count,
        "higher_order_case_count": higher_order_case_count,
        "product_false_case_count": product_false_case_count,
        "pairwise_false_case_count": pairwise_false_case_count,
        "product_false_tuple_count": product_false_tuple_count,
        "pairwise_false_tuple_count": pairwise_false_tuple_count,
        "max_product_size": max_product_size,
        "max_pairwise_closure_size": max_pairwise_closure_size,
        "max_actual_relation_size": max_actual_relation_size,
        "max_pairwise_false_count": max_pairwise_false_count,
        "min_required_arity_histogram": dict(
            sorted(min_required_arity_histogram.items(), key=lambda item: str(item[0]))
        ),
        "tuple_distinct_obligation_histogram": dict(
            sorted(tuple_distinct_obligation_histogram.items())
        ),
        "actual_relation_size_histogram": dict(sorted(actual_relation_size_histogram.items())),
        "product_size_histogram": dict(sorted(product_size_histogram.items())),
        "pairwise_closure_size_histogram": dict(
            sorted(pairwise_closure_size_histogram.items())
        ),
        "binary_sufficient_examples": tuple(binary_sufficient_examples),
        "higher_order_examples": tuple(higher_order_examples),
    }


def _merge_histogram(target: dict, source: dict) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def _summarize_rows(rows: list[dict]) -> dict:
    min_required_arity_histogram: dict = {}
    tuple_distinct_obligation_histogram: dict = {}
    for row in rows:
        _merge_histogram(
            min_required_arity_histogram,
            row["min_required_arity_histogram"],
        )
        _merge_histogram(
            tuple_distinct_obligation_histogram,
            row["tuple_distinct_obligation_histogram"],
        )
    return {
        "rows": len(rows),
        "complete_rows": sum(1 for row in rows if row["complete"]),
        "frontier_truncated_rows": sum(1 for row in rows if row["frontier_truncated"]),
        "sample_exhausted_rows": sum(1 for row in rows if row["sample_exhausted"]),
        "rows_with_pnodes": sum(1 for row in rows if row["pnode_count"]),
        "open_obligation_projection_count": sum(
            row["open_obligation_projection_count"] for row in rows
        ),
        "total_combination_count": sum(row["total_combination_count"] for row in rows),
        "random_attempt_count": sum(row["random_attempt_count"] for row in rows),
        "sampled_index_tuple_count": sum(
            row["sampled_index_tuple_count"] for row in rows
        ),
        "sampled_tuple_count": sum(row["sampled_tuple_count"] for row in rows),
        "skipped_same_obligation_tuple_count": sum(
            row["skipped_same_obligation_tuple_count"] for row in rows
        ),
        "relation_case_count": sum(row["relation_case_count"] for row in rows),
        "unary_sufficient_case_count": sum(
            row["unary_sufficient_case_count"] for row in rows
        ),
        "binary_sufficient_case_count": sum(
            row["binary_sufficient_case_count"] for row in rows
        ),
        "higher_order_case_count": sum(row["higher_order_case_count"] for row in rows),
        "product_false_case_count": sum(
            row["product_false_case_count"] for row in rows
        ),
        "pairwise_false_case_count": sum(
            row["pairwise_false_case_count"] for row in rows
        ),
        "product_false_tuple_count": sum(
            row["product_false_tuple_count"] for row in rows
        ),
        "pairwise_false_tuple_count": sum(
            row["pairwise_false_tuple_count"] for row in rows
        ),
        "rows_with_higher_order_cases": sum(
            1 for row in rows if row["higher_order_case_count"]
        ),
        "max_product_size": max((row["max_product_size"] for row in rows), default=0),
        "max_pairwise_closure_size": max(
            (row["max_pairwise_closure_size"] for row in rows),
            default=0,
        ),
        "max_actual_relation_size": max(
            (row["max_actual_relation_size"] for row in rows),
            default=0,
        ),
        "max_pairwise_false_count": max(
            (row["max_pairwise_false_count"] for row in rows),
            default=0,
        ),
        "min_required_arity_histogram": dict(
            sorted(min_required_arity_histogram.items(), key=lambda item: str(item[0]))
        ),
        "tuple_distinct_obligation_histogram": dict(
            sorted(tuple_distinct_obligation_histogram.items())
        ),
    }


def run_probe(
    *,
    tuple_sizes: list[int],
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
    rows = []
    skipped = []
    for tuple_size in tuple_sizes:
        for n in sizes:
            for pc_tree_kind in pc_trees:
                for instance_kind in instance_kinds:
                    if not _is_applicable(instance_kind, n):
                        skipped.append(
                            {
                                "tuple_size": tuple_size,
                                "n": n,
                                "pc_tree_kind": pc_tree_kind,
                                "instance_kind": instance_kind,
                                "reason": "not_applicable",
                            }
                        )
                        continue
                    for repeat in range(_repeat_count(instance_kind, repeats)):
                        row_seed = (
                            seed
                            + 1000003 * tuple_size
                            + 1009 * n
                            + 101 * repeat
                            + _stable_offset(pc_tree_kind, instance_kind)
                        )
                        rows.append(
                            _row(
                                n=n,
                                pc_tree_kind=pc_tree_kind,
                                instance_kind=instance_kind,
                                repeat=repeat,
                                seed=row_seed,
                                frontier_limit=frontier_limit,
                                projection_tuple_size=tuple_size,
                                min_distinct_obligations=min_distinct_obligations,
                                scope=scope,
                                sample_count=sample_count,
                                max_attempt_multiplier=max_attempt_multiplier,
                                max_examples=max_examples,
                            )
                        )

    by_tuple_size = {}
    for tuple_size in tuple_sizes:
        tuple_rows = [row for row in rows if row["projection_tuple_size"] == tuple_size]
        by_tuple_size[str(tuple_size)] = _summarize_rows(tuple_rows)

    summary = _summarize_rows(rows)
    summary["tuple_sizes_with_higher_order_cases"] = [
        tuple_size
        for tuple_size in tuple_sizes
        if by_tuple_size[str(tuple_size)]["higher_order_case_count"]
    ]
    summary["interpretation"] = (
        "T101 randomly samples open projection tuples instead of scanning only "
        "the deterministic prefix under a cap. Higher-order cases would refute "
        "binary gap reconstruction in this bounded scaffold; absence of such "
        "cases is not a proof."
    )

    return {
        "method": "t101_context_gap_random_arity_probe",
        "tuple_sizes": tuple_sizes,
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "min_distinct_obligations": min_distinct_obligations,
        "scope": scope,
        "sample_count": sample_count,
        "max_attempt_multiplier": max_attempt_multiplier,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "by_tuple_size": by_tuple_size,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuple-sizes", default="4,5", type=_parse_ints)
    parser.add_argument("--sizes", default="5,6,7", type=_parse_ints)
    parser.add_argument("--pc-trees", default="balanced,mixed", type=_parse_strings)
    parser.add_argument(
        "--instance-kinds",
        default="cycle,paired_farthest,random,random4,padded_five_local_non_cr",
        type=_parse_strings,
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--frontier-limit", type=int, default=20000)
    parser.add_argument("--min-distinct-obligations", type=int, default=2)
    parser.add_argument(
        "--scope",
        choices=("all_open", "support_open", "projection_only_open"),
        default="all_open",
    )
    parser.add_argument("--sample-count", type=int, default=1200)
    parser.add_argument("--max-attempt-multiplier", type=int, default=20)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_random_arity_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        tuple_sizes=args.tuple_sizes,
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        min_distinct_obligations=args.min_distinct_obligations,
        scope=args.scope,
        sample_count=args.sample_count,
        max_attempt_multiplier=args.max_attempt_multiplier,
        max_examples=args.max_examples,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(_json_ready(report["summary"]), indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
