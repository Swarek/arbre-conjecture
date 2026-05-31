#!/usr/bin/env python3
"""T102 probe: binary propagation of insertion-gap relations."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from itertools import combinations, product
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
    _is_gap_composition_projection,
    _iter_pnode_obligation_projections,
    _missing_cyclic_gap_signature,
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


def _merge_histogram(target: dict, source: dict) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def _sample_index_sets(
    *,
    rng: random.Random,
    count: int,
    size: int,
    sample_count: int,
    max_attempts: int,
) -> tuple[list[tuple[int, ...]], int, bool]:
    total = math.comb(count, size) if count >= size else 0
    if total <= sample_count:
        return list(combinations(range(count), size)), 0, True

    seen = set()
    attempts = 0
    while len(seen) < sample_count and attempts < max_attempts:
        attempts += 1
        seen.add(tuple(sorted(rng.sample(range(count), size))))
    return sorted(seen), attempts, len(seen) == total


def _binary_closure_stats(
    relation: set[tuple],
    *,
    arity: int,
    max_product_size: int,
) -> dict:
    marginals = tuple(
        {value_tuple[index] for value_tuple in relation}
        for index in range(arity)
    )
    product_size = 1
    for values in marginals:
        product_size *= len(values)

    pair_projections = {
        (i, j): {
            (value_tuple[i], value_tuple[j])
            for value_tuple in relation
        }
        for i, j in combinations(range(arity), 2)
    }
    restrictive_edge_count = sum(
        1
        for i, j in combinations(range(arity), 2)
        if len(pair_projections[(i, j)]) < len(marginals[i]) * len(marginals[j])
    )

    if product_size > max_product_size:
        return {
            "product_size": product_size,
            "closure_size": None,
            "product_capped": True,
            "false_count": None,
            "first_false_tuple": None,
            "restrictive_edge_count": restrictive_edge_count,
        }

    closure_size = 0
    false_count = 0
    first_false_tuple = None
    for candidate in product(*(sorted(values, key=repr) for values in marginals)):
        if all(
            (candidate[i], candidate[j]) in pair_projections[(i, j)]
            for i, j in combinations(range(arity), 2)
        ):
            closure_size += 1
            if candidate not in relation:
                false_count += 1
                if first_false_tuple is None:
                    first_false_tuple = candidate
    return {
        "product_size": product_size,
        "closure_size": closure_size,
        "product_capped": False,
        "false_count": false_count,
        "first_false_tuple": first_false_tuple,
        "restrictive_edge_count": restrictive_edge_count,
    }


def _row(
    *,
    n: int,
    pc_tree_kind: str,
    instance_kind: str,
    repeat: int,
    seed: int,
    frontier_limit: int,
    projection_set_size: int,
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_examples: int,
) -> dict:
    start = time.perf_counter()
    rng = random.Random(seed)
    D = _instance(instance_kind, n, seed=seed)
    T = _pc_tree(pc_tree_kind, len(D))
    if set(labels(T)) != set(range(len(D))):
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
    total_set_count = (
        math.comb(len(open_obligations), projection_set_size)
        if len(open_obligations) >= projection_set_size
        else 0
    )
    max_attempts = max(sample_count, sample_count * max_attempt_multiplier)
    sampled_index_sets, random_attempt_count, sample_exhausted = _sample_index_sets(
        rng=rng,
        count=len(open_obligations),
        size=projection_set_size,
        sample_count=sample_count,
        max_attempts=max_attempts,
    )

    sampled_set_count = 0
    skipped_same_obligation_set_count = 0
    visible_case_count = 0
    product_capped_case_count = 0
    unary_sufficient_case_count = 0
    binary_sufficient_case_count = 0
    higher_order_case_count = 0
    product_false_case_count = 0
    product_false_tuple_count = 0
    pairwise_false_tuple_count = 0
    max_product_size_seen = 0
    max_closure_size = 0
    max_actual_relation_size = 0
    max_false_count = 0
    restrictive_edge_count_total = 0
    visible_cases_with_restrictive_edges = 0
    min_required_arity_histogram: dict = {}
    actual_relation_size_histogram: dict = {}
    product_size_histogram: dict = {}
    closure_size_histogram: dict = {}
    restrictive_edge_histogram: dict = {}
    distinct_obligation_histogram: dict = {}
    binary_sufficient_examples = []
    higher_order_examples = []

    for index_set in sampled_index_sets:
        obligation_set = tuple(open_obligations[index] for index in index_set)
        distinct_same_side_count = len(
            {obligation["same_side"] for obligation in obligation_set}
        )
        if distinct_same_side_count < min_distinct_obligations:
            skipped_same_obligation_set_count += 1
            continue
        sampled_set_count += 1
        _hist_increment(distinct_obligation_histogram, distinct_same_side_count)

        relation_by_visible: dict[tuple, set[tuple]] = {}
        for frontier in frontiers:
            visible_parts = []
            gap_parts = []
            for index, obligation in enumerate(obligation_set):
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
            visible_case_count += 1
            actual_size = len(actual_relation)
            stats = _binary_closure_stats(
                actual_relation,
                arity=projection_set_size,
                max_product_size=max_product_size,
            )
            product_size = stats["product_size"]
            restrictive_edge_count = stats["restrictive_edge_count"]
            restrictive_edge_count_total += restrictive_edge_count
            if restrictive_edge_count:
                visible_cases_with_restrictive_edges += 1
            max_product_size_seen = max(max_product_size_seen, product_size)
            max_actual_relation_size = max(max_actual_relation_size, actual_size)
            _hist_increment(actual_relation_size_histogram, actual_size)
            _hist_increment(product_size_histogram, product_size)
            _hist_increment(restrictive_edge_histogram, restrictive_edge_count)

            if stats["product_capped"]:
                product_capped_case_count += 1
                _hist_increment(min_required_arity_histogram, "capped")
                continue

            closure_size = stats["closure_size"]
            false_count = stats["false_count"]
            max_closure_size = max(max_closure_size, closure_size)
            max_false_count = max(max_false_count, false_count)
            _hist_increment(closure_size_histogram, closure_size)

            product_false_count = product_size - actual_size
            if product_false_count:
                product_false_case_count += 1
                product_false_tuple_count += product_false_count

            if product_size == actual_size:
                unary_sufficient_case_count += 1
                required_arity = 1
            elif false_count == 0:
                binary_sufficient_case_count += 1
                required_arity = 2
                if len(binary_sufficient_examples) < max_examples:
                    binary_sufficient_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_set
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_set
                            ),
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "closure_size": closure_size,
                            "restrictive_edge_count": restrictive_edge_count,
                        }
                    )
            else:
                higher_order_case_count += 1
                pairwise_false_tuple_count += false_count
                required_arity = ">=3"
                if len(higher_order_examples) < max_examples:
                    higher_order_examples.append(
                        {
                            "same_sides": tuple(
                                obligation["same_side"] for obligation in obligation_set
                            ),
                            "projection_paths": tuple(
                                obligation["path"] for obligation in obligation_set
                            ),
                            "fine_role_patterns": tuple(
                                obligation["fine_role_pattern"]
                                for obligation in obligation_set
                            ),
                            "visible_key": visible_key,
                            "actual_gap_tuples": tuple(
                                sorted(actual_relation, key=repr)[:max_examples]
                            ),
                            "first_false_tuple": stats["first_false_tuple"],
                            "actual_relation_size": actual_size,
                            "product_size": product_size,
                            "closure_size": closure_size,
                            "false_count": false_count,
                            "restrictive_edge_count": restrictive_edge_count,
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
        "complete": not frontier_truncated and sample_exhausted,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "open_obligation_projection_count": len(open_obligations),
        "projection_set_size": projection_set_size,
        "total_set_count": total_set_count,
        "random_attempt_count": random_attempt_count,
        "sampled_index_set_count": len(sampled_index_sets),
        "sampled_set_count": sampled_set_count,
        "skipped_same_obligation_set_count": skipped_same_obligation_set_count,
        "sample_exhausted": sample_exhausted,
        "visible_case_count": visible_case_count,
        "product_capped_case_count": product_capped_case_count,
        "unary_sufficient_case_count": unary_sufficient_case_count,
        "binary_sufficient_case_count": binary_sufficient_case_count,
        "higher_order_case_count": higher_order_case_count,
        "product_false_case_count": product_false_case_count,
        "product_false_tuple_count": product_false_tuple_count,
        "pairwise_false_tuple_count": pairwise_false_tuple_count,
        "max_product_size": max_product_size_seen,
        "max_closure_size": max_closure_size,
        "max_actual_relation_size": max_actual_relation_size,
        "max_false_count": max_false_count,
        "restrictive_edge_count_total": restrictive_edge_count_total,
        "visible_cases_with_restrictive_edges": visible_cases_with_restrictive_edges,
        "min_required_arity_histogram": dict(
            sorted(min_required_arity_histogram.items(), key=lambda item: str(item[0]))
        ),
        "actual_relation_size_histogram": dict(
            sorted(actual_relation_size_histogram.items())
        ),
        "product_size_histogram": dict(sorted(product_size_histogram.items())),
        "closure_size_histogram": dict(sorted(closure_size_histogram.items())),
        "restrictive_edge_histogram": dict(sorted(restrictive_edge_histogram.items())),
        "distinct_obligation_histogram": dict(sorted(distinct_obligation_histogram.items())),
        "binary_sufficient_examples": tuple(binary_sufficient_examples),
        "higher_order_examples": tuple(higher_order_examples),
    }


def _summarize_rows(rows: list[dict]) -> dict:
    min_required_arity_histogram: dict = {}
    restrictive_edge_histogram: dict = {}
    distinct_obligation_histogram: dict = {}
    for row in rows:
        _merge_histogram(
            min_required_arity_histogram,
            row["min_required_arity_histogram"],
        )
        _merge_histogram(restrictive_edge_histogram, row["restrictive_edge_histogram"])
        _merge_histogram(
            distinct_obligation_histogram,
            row["distinct_obligation_histogram"],
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
        "total_set_count": sum(row["total_set_count"] for row in rows),
        "sampled_index_set_count": sum(row["sampled_index_set_count"] for row in rows),
        "sampled_set_count": sum(row["sampled_set_count"] for row in rows),
        "visible_case_count": sum(row["visible_case_count"] for row in rows),
        "product_capped_case_count": sum(
            row["product_capped_case_count"] for row in rows
        ),
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
        "product_false_tuple_count": sum(
            row["product_false_tuple_count"] for row in rows
        ),
        "pairwise_false_tuple_count": sum(
            row["pairwise_false_tuple_count"] for row in rows
        ),
        "rows_with_higher_order_cases": sum(
            1 for row in rows if row["higher_order_case_count"]
        ),
        "restrictive_edge_count_total": sum(
            row["restrictive_edge_count_total"] for row in rows
        ),
        "visible_cases_with_restrictive_edges": sum(
            row["visible_cases_with_restrictive_edges"] for row in rows
        ),
        "max_product_size": max((row["max_product_size"] for row in rows), default=0),
        "max_closure_size": max((row["max_closure_size"] for row in rows), default=0),
        "max_actual_relation_size": max(
            (row["max_actual_relation_size"] for row in rows),
            default=0,
        ),
        "max_false_count": max((row["max_false_count"] for row in rows), default=0),
        "min_required_arity_histogram": dict(
            sorted(min_required_arity_histogram.items(), key=lambda item: str(item[0]))
        ),
        "restrictive_edge_histogram": dict(sorted(restrictive_edge_histogram.items())),
        "distinct_obligation_histogram": dict(
            sorted(distinct_obligation_histogram.items())
        ),
    }


def run_probe(
    *,
    set_sizes: list[int],
    sizes: list[int],
    pc_trees: list[str],
    instance_kinds: list[str],
    repeats: int,
    frontier_limit: int,
    min_distinct_obligations: int,
    scope: str,
    sample_count: int,
    max_attempt_multiplier: int,
    max_product_size: int,
    max_examples: int,
    seed: int,
) -> dict:
    start = time.perf_counter()
    rows = []
    skipped = []
    for set_size in set_sizes:
        for n in sizes:
            for pc_tree_kind in pc_trees:
                for instance_kind in instance_kinds:
                    if not _is_applicable(instance_kind, n):
                        skipped.append(
                            {
                                "set_size": set_size,
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
                            + 1000003 * set_size
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
                                projection_set_size=set_size,
                                min_distinct_obligations=min_distinct_obligations,
                                scope=scope,
                                sample_count=sample_count,
                                max_attempt_multiplier=max_attempt_multiplier,
                                max_product_size=max_product_size,
                                max_examples=max_examples,
                            )
                        )

    by_set_size = {}
    for set_size in set_sizes:
        set_rows = [row for row in rows if row["projection_set_size"] == set_size]
        by_set_size[str(set_size)] = _summarize_rows(set_rows)
    summary = _summarize_rows(rows)
    summary["set_sizes_with_higher_order_cases"] = [
        set_size
        for set_size in set_sizes
        if by_set_size[str(set_size)]["higher_order_case_count"]
    ]
    summary["interpretation"] = (
        "T102 treats binary gap compatibility as a local CSP over larger "
        "projection sets. A higher-order case means binary propagation admits "
        "a gap tuple that no frontier realizes. Zero cases is not a proof."
    )

    return {
        "method": "t102_context_gap_binary_component_probe",
        "set_sizes": set_sizes,
        "sizes": sizes,
        "pc_trees": pc_trees,
        "instance_kinds": instance_kinds,
        "repeats": repeats,
        "frontier_limit": frontier_limit,
        "min_distinct_obligations": min_distinct_obligations,
        "scope": scope,
        "sample_count": sample_count,
        "max_attempt_multiplier": max_attempt_multiplier,
        "max_product_size": max_product_size,
        "seed": seed,
        "seconds": time.perf_counter() - start,
        "summary": summary,
        "by_set_size": by_set_size,
        "skipped": skipped,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set-sizes", default="6,8", type=_parse_ints)
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
    parser.add_argument("--sample-count", type=int, default=800)
    parser.add_argument("--max-attempt-multiplier", type=int, default=20)
    parser.add_argument("--max-product-size", type=int, default=20000)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260720)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/context_gap_binary_component_probe.json"),
    )
    args = parser.parse_args(argv)

    report = run_probe(
        set_sizes=args.set_sizes,
        sizes=args.sizes,
        pc_trees=args.pc_trees,
        instance_kinds=args.instance_kinds,
        repeats=args.repeats,
        frontier_limit=args.frontier_limit,
        min_distinct_obligations=args.min_distinct_obligations,
        scope=args.scope,
        sample_count=args.sample_count,
        max_attempt_multiplier=args.max_attempt_multiplier,
        max_product_size=args.max_product_size,
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
