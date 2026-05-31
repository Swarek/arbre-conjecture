"""Interface-relation diagnostics for fixed branch orders.

These helpers test whether internal branch completions factorize once a root
branch order is fixed.  They are research diagnostics only; they do not decide
the original PC-tree existence problem.
"""

from __future__ import annotations

from itertools import combinations, product
from math import prod

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels
from pc_circular.predicates import (
    find_bad_side_precircular_cR_violation,
    passes_bad_side_precircular_cR,
    validate_dissimilarity,
)
from pc_circular.solvers.local_constraints import project_bad_side_obligations_to_pc_nodes


def _unique_linear_frontiers(node: PCNode, *, limit: int | None = None) -> tuple[tuple[int, ...], ...]:
    raw = enumerate_frontiers(node, canonical=False, limit=limit)
    seen: set[tuple[int, ...]] = set()
    result = []
    for frontier in raw:
        frontier = tuple(frontier)
        if frontier in seen:
            continue
        seen.add(frontier)
        result.append(frontier)
    return tuple(result)


def _compose_order(
    branch_options: tuple[tuple[tuple[int, ...], ...], ...],
    branch_order: tuple[int, ...],
    option_tuple: tuple[int, ...],
) -> tuple[int, ...]:
    merged: list[int] = []
    option_by_branch = dict(zip(branch_order, option_tuple))
    for branch in branch_order:
        merged.extend(branch_options[branch][option_by_branch[branch]])
    return tuple(merged)


def _relation_projection(relation, subset: tuple[int, ...]) -> set[tuple[int, ...]]:
    return {tuple(item[index] for index in subset) for item in relation}


def _closure_from_projection_arity(
    relation: set[tuple[int, ...]],
    domains: tuple[range, ...],
    arity: int,
    *,
    max_candidates: int,
) -> tuple[set[tuple[int, ...]] | None, bool]:
    degree = len(domains)
    if degree == 0:
        return {()}, False
    if not relation:
        return set(), False
    if arity < 1 or arity > degree:
        raise ValueError("arity must be between 1 and degree")
    candidate_count = prod(len(domain) for domain in domains)
    if candidate_count > max_candidates:
        return None, True

    subsets = tuple(combinations(range(degree), arity))
    projections = {
        subset: _relation_projection(relation, subset)
        for subset in subsets
    }
    closure = {
        candidate
        for candidate in product(*domains)
        if all(tuple(candidate[index] for index in subset) in projections[subset] for subset in subsets)
    }
    return closure, False


def _root_bad_side_summary(D, T: PCNode) -> dict:
    report = project_bad_side_obligations_to_pc_nodes(D, T)
    root = report["nodes"][0] if report["nodes"] else {}
    return {
        "obligation_count": report["obligation_count"],
        "multi_level_obligation_count": report["multi_level_obligation_count"],
        "root_projection_hit_count": root.get("projection_hit_count", 0),
        "root_full_projection_count": root.get("full_projection_count", 0),
        "root_full_distinct_four_branch_count": root.get(
            "full_distinct_four_branch_count", 0
        ),
        "root_role_pattern_histogram": root.get("role_pattern_histogram", {}),
        "root_max_branch_interface_load": root.get("max_branch_interface_load", 0),
    }


def root_fixed_order_interface_product_report(
    D,
    T: PCNode,
    *,
    branch_order: tuple[int, ...] | None = None,
    max_branch_options: int = 256,
    max_product_tuples: int = 200000,
    max_examples: int = 5,
) -> dict:
    """Compare exact accepted internal completions with unary projections."""

    n = validate_dissimilarity(D)
    if set(labels(T)) != set(range(n)):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if T.kind == "leaf":
        raise ValueError("root must be an internal node")
    if max_branch_options <= 0:
        raise ValueError("max_branch_options must be positive")
    if max_product_tuples <= 0:
        raise ValueError("max_product_tuples must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

    degree = len(T.children)
    if branch_order is None:
        branch_order = tuple(range(degree))
    else:
        branch_order = tuple(branch_order)
    if set(branch_order) != set(range(degree)):
        raise ValueError("branch_order must be a permutation of root branches")

    branch_options = []
    branch_truncated = False
    for child in T.children:
        options = _unique_linear_frontiers(child, limit=max_branch_options + 1)
        if len(options) > max_branch_options:
            branch_truncated = True
            options = options[:max_branch_options]
        branch_options.append(options)
    branch_options = tuple(branch_options)
    option_counts = tuple(len(options) for options in branch_options)
    product_tuple_count = prod(option_counts)
    product_truncated = product_tuple_count > max_product_tuples

    accepted: set[tuple[int, ...]] = set()
    accepted_examples = []
    if not branch_truncated and not product_truncated:
        domains_for_order = tuple(range(option_counts[branch]) for branch in branch_order)
        for option_tuple in product(*domains_for_order):
            order = _compose_order(branch_options, branch_order, option_tuple)
            if passes_bad_side_precircular_cR(D, order):
                accepted.add(tuple(option_tuple))
                if len(accepted_examples) < max_examples:
                    accepted_examples.append({"tuple": tuple(option_tuple), "order": order})

    complete = not branch_truncated and not product_truncated
    domains_for_order = tuple(range(option_counts[branch]) for branch in branch_order)
    projection_product, projection_product_truncated = (
        _closure_from_projection_arity(
            accepted,
            domains_for_order,
            1,
            max_candidates=max_product_tuples,
        )
        if complete
        else (None, False)
    )
    false_product = (
        sorted(projection_product - accepted)
        if complete and projection_product is not None
        else []
    )

    false_examples = []
    for option_tuple in false_product[:max_examples]:
        order = _compose_order(branch_options, branch_order, tuple(option_tuple))
        false_examples.append(
            {
                "tuple": tuple(option_tuple),
                "order": order,
                "bad_side_violation": find_bad_side_precircular_cR_violation(D, order),
            }
        )

    closure_by_arity = {}
    minimal_coupling_support_size = None
    if complete:
        for arity in range(1, degree + 1):
            closure, truncated = _closure_from_projection_arity(
                accepted,
                domains_for_order,
                arity,
                max_candidates=max_product_tuples,
            )
            closure_by_arity[arity] = {
                "truncated": truncated,
                "closure_tuple_count": None if closure is None else len(closure),
                "exact": closure == accepted if closure is not None else False,
                "false_tuple_count": None if closure is None else len(closure - accepted),
            }
            if closure == accepted and minimal_coupling_support_size is None:
                minimal_coupling_support_size = arity

    return {
        "method": "root_fixed_order_interface_product_report",
        "n": n,
        "root_kind": T.kind,
        "degree": degree,
        "branch_order": branch_order,
        "branch_label_sets": tuple(tuple(labels(child)) for child in T.children),
        "branch_option_counts": option_counts,
        "branch_options": branch_options,
        "product_tuple_count": product_tuple_count,
        "branch_truncated": branch_truncated,
        "product_truncated": product_truncated,
        "complete": complete,
        "accepted_tuple_count": len(accepted),
        "accepted_tuple_examples": tuple(accepted_examples),
        "projection_product_count": (
            None if projection_product is None else len(projection_product)
        ),
        "projection_product_truncated": projection_product_truncated,
        "false_product_count": len(false_product),
        "false_product_examples": tuple(false_examples),
        "factorizes": complete and projection_product == accepted,
        "minimal_coupling_support_size": minimal_coupling_support_size,
        "closure_by_arity": closure_by_arity,
        "bad_side_projection": _root_bad_side_summary(D, T),
        "interpretation": (
            "diagnostic only: a mismatch refutes unary product factorization "
            "for this fixed root order, not the whole problem"
        ),
    }
