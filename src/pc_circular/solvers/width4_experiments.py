"""Width-4 diagnostics for projected P-node branch orders.

These helpers are research diagnostics only.  They test whether the set of
branch orders seen at a P-node among globally cR frontiers is determined by its
restrictions to every four branches.  They do not decide the original problem.
"""

from __future__ import annotations

from itertools import combinations

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    passes_bad_side_precircular_cR,
    validate_dissimilarity,
)
from pc_circular.solvers.local_constraints import iter_internal_node_child_labels


def restrict_circular_order(order, subset) -> tuple[int, ...]:
    """Return the induced circular order on ``subset``, canonically oriented."""

    subset = set(subset)
    return canonical_circular_order(tuple(item for item in order if item in subset))


def induced_child_circular_order(order, child_label_sets) -> tuple[int, ...] | None:
    """Project a represented frontier to the cyclic order of a node's children.

    The global frontier is circular, so the node block may cross the chosen
    linear cut.  Compressing equal adjacent child indices and merging the
    circular wrap recovers the local child order when the frontier represents
    the PC-tree.
    """

    label_to_child: dict[int, int] = {}
    for index, child_labels in enumerate(child_label_sets):
        for label in child_labels:
            label_to_child[label] = index

    compressed: list[int] = []
    for label in order:
        child_index = label_to_child.get(label)
        if child_index is None:
            continue
        if not compressed or compressed[-1] != child_index:
            compressed.append(child_index)

    if len(compressed) > 1 and compressed[0] == compressed[-1]:
        compressed.pop()

    degree = len(child_label_sets)
    if len(compressed) != degree or set(compressed) != set(range(degree)):
        return None
    return canonical_circular_order(tuple(compressed))


def width4_closure_from_orders(
    degree: int,
    accepted_orders,
    *,
    candidate_orders=None,
    max_examples: int = 5,
) -> dict:
    """Compute the four-restriction closure of a branch-order family."""

    if degree < 1:
        raise ValueError("degree must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

    domain = (
        tuple(all_circular_orders(degree))
        if candidate_orders is None
        else tuple(canonical_circular_order(order) for order in candidate_orders)
    )
    domain_set = set(domain)
    accepted_set = {canonical_circular_order(order) for order in accepted_orders}
    unknown = accepted_set - domain_set
    if unknown:
        raise ValueError(f"accepted orders outside candidate domain: {sorted(unknown)[:3]}")

    if degree < 4:
        closure_set = set(accepted_set)
        relation_by_subset: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    else:
        relation_by_subset = {}
        for subset in combinations(range(degree), 4):
            relation_by_subset[subset] = {
                restrict_circular_order(order, subset) for order in accepted_set
            }
        closure_set = {
            order
            for order in domain_set
            if all(
                restrict_circular_order(order, subset) in relation
                for subset, relation in relation_by_subset.items()
            )
        }

    missing = sorted(closure_set - accepted_set)
    accepted_not_closed = sorted(accepted_set - closure_set)
    relation_kind_counts = {"empty": 0, "forced": 0, "nontrivial": 0, "free": 0}
    max_relation_size = 0
    for relation in relation_by_subset.values():
        size = len(relation)
        max_relation_size = max(max_relation_size, size)
        if size == 0:
            relation_kind_counts["empty"] += 1
        elif size == 1:
            relation_kind_counts["forced"] += 1
        elif size == 3:
            relation_kind_counts["free"] += 1
        else:
            relation_kind_counts["nontrivial"] += 1

    return {
        "degree": degree,
        "candidate_order_count": len(domain_set),
        "accepted_order_count": len(accepted_set),
        "closure_order_count": len(closure_set),
        "missing_order_count": len(missing),
        "accepted_not_closed_count": len(accepted_not_closed),
        "width4_holds": not missing and not accepted_not_closed,
        "four_subset_count": len(relation_by_subset),
        "relation_tuple_count": sum(len(relation) for relation in relation_by_subset.values()),
        "max_relation_size": max_relation_size,
        "relation_kind_histogram": relation_kind_counts,
        "missing_order_examples": tuple(missing[:max_examples]),
        "accepted_not_closed_examples": tuple(accepted_not_closed[:max_examples]),
    }


def pnode_width4_frontier_projection_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 5000,
    max_branch_degree: int = 8,
    max_examples: int = 5,
) -> dict:
    """Test width-4 closure of P-node branch orders seen in cR frontiers."""

    n = validate_dissimilarity(D)
    if set(labels(T)) != set(range(n)):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if max_branch_degree < 1:
        raise ValueError("max_branch_degree must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

    raw_frontiers = enumerate_frontiers(T, canonical=True, limit=frontier_limit + 1)
    frontier_truncated = len(raw_frontiers) > frontier_limit
    frontiers = tuple(raw_frontiers[:frontier_limit])
    accepted_frontiers = tuple(
        order for order in frontiers if passes_bad_side_precircular_cR(D, order)
    )

    nodes = []
    for node_info in iter_internal_node_child_labels(T):
        if node_info["kind"] != "P":
            continue
        child_label_sets = node_info["child_label_sets"]
        degree = len(child_label_sets)
        if degree < 4:
            status = "degree_below_4"
            closure = None
            all_seen_orders = set()
            accepted_orders = set()
        else:
            all_seen_orders = {
                order
                for order in (
                    induced_child_circular_order(frontier, child_label_sets)
                    for frontier in frontiers
                )
                if order is not None
            }
            accepted_orders = {
                order
                for order in (
                    induced_child_circular_order(frontier, child_label_sets)
                    for frontier in accepted_frontiers
                )
                if order is not None
            }
            if frontier_truncated:
                status = "incomplete_frontiers"
                closure = None
            elif degree > max_branch_degree:
                status = "unsupported_degree"
                closure = None
            else:
                closure = width4_closure_from_orders(
                    degree,
                    accepted_orders,
                    max_examples=max_examples,
                )
                status = "holds" if closure["width4_holds"] else "refuted"

        nodes.append(
            {
                "path": node_info["path"],
                "kind": node_info["kind"],
                "degree": degree,
                "branch_sizes": tuple(len(child_labels) for child_labels in child_label_sets),
                "status": status,
                "complete_for_width4_decision": status in {"holds", "refuted"},
                "truncation_reasons": (
                    ("frontier_limit",)
                    if status == "incomplete_frontiers"
                    else (("branch_degree_limit",) if status == "unsupported_degree" else ())
                ),
                "frontier_child_order_count": len(all_seen_orders),
                "accepted_branch_order_count": len(accepted_orders),
                "accepted_branch_order_examples": tuple(sorted(accepted_orders)[:max_examples]),
                "closure": closure,
            }
        )

    tested_nodes = [node for node in nodes if node["status"] in {"holds", "refuted"}]
    refuted_nodes = [node for node in nodes if node["status"] == "refuted"]
    return {
        "n": n,
        "method": "pnode_width4_frontier_projection_report",
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "accepted_frontier_count": len(accepted_frontiers),
        "node_count": len(nodes),
        "tested_node_count": len(tested_nodes),
        "refuted_node_count": len(refuted_nodes),
        "unsupported_node_count": sum(1 for node in nodes if node["status"] == "unsupported_degree"),
        "incomplete_node_count": sum(1 for node in nodes if node["status"] == "incomplete_frontiers"),
        "max_missing_order_count": max(
            (
                node["closure"]["missing_order_count"]
                for node in refuted_nodes
                if node["closure"] is not None
            ),
            default=0,
        ),
        "nodes": tuple(nodes),
        "interpretation": (
            "Empirical width-4 diagnostic for P-node branch-order projections; "
            "not a solver and not a proof of the original problem."
        ),
    }
