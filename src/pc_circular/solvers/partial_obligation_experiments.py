"""Diagnostics for partially visible bad-side obligations at P-nodes.

T091 models fully visible ``same_side(a,c;b,d)`` obligations as forced
non-crossings between two branch chords.  This module measures what that model
does not see: obligations that hit a P-node but collapse roles inside branches
or only expose part of the quartet at that node.  The output is a research
diagnostic, not a solver.
"""

from __future__ import annotations

from itertools import combinations

from pc_circular.cyclic_order_sat import same_side_constraint_satisfied
from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels
from pc_circular.solvers.circle_graph_experiments import pnode_circle_graph_local_report
from pc_circular.solvers.dp_experiments import bad_witnesses_by_pair
from pc_circular.solvers.local_constraints import (
    iter_internal_node_child_labels,
    project_bad_side_obligations_to_pc_nodes,
)
from pc_circular.solvers.sat_like_experiments import quartet_support_paths
from pc_circular.solvers.width4_experiments import induced_child_circular_order


NON_CHORD_ROLE_PATTERNS = (
    "partial_boundary",
    "all_in_one_branch",
    "mixed_endpoint_witness",
    "endpoints_collapsed",
    "witnesses_collapsed",
    "collapsed_separate_roles",
)

OPEN_ROLE_PATTERNS = (
    "partial_boundary",
    "mixed_endpoint_witness",
    "endpoints_collapsed",
    "witnesses_collapsed",
    "collapsed_separate_roles",
)


def _sum_histogram(histogram: dict, keys) -> int:
    return sum(int(histogram.get(key, 0)) for key in keys)


def _merge_histogram(target: dict, source: dict) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def _sorted_histogram(histogram: dict) -> dict:
    return dict(sorted(histogram.items(), key=lambda item: str(item[0])))


def _partial_kind(node: dict) -> str:
    if node["projection_hit_count"] == 0:
        return "no_bad_side_projection"
    if node["non_chord_obligation_count"] == 0 and node["multi_level_hit_count"] == 0:
        return "fully_visible_chords_only"
    if node["open_obligation_count"] > 0:
        return "open_separator_obligations"
    return "collapsed_or_multilevel_only"


def _fine_role_pattern(projected_roles, support: tuple[int, ...], *, is_support_node: bool) -> str:
    visible_count = len(projected_roles)
    endpoint_count = sum(1 for role, _, _ in projected_roles if role == "endpoint")
    witness_count = visible_count - endpoint_count
    support_kind = "support" if is_support_node else "projection"
    support_size = len(support)
    roles_by_branch: dict[int, set[str]] = {}
    for role, _, branch in projected_roles:
        roles_by_branch.setdefault(branch, set()).add(role)
    mixed_suffix = "mixed" if any(len(roles) > 1 for roles in roles_by_branch.values()) else "clean"

    if visible_count == 4:
        if support_size == 4:
            return f"{support_kind}:full_four_branch"
        return f"{support_kind}:full_collapsed:s{support_size}:{mixed_suffix}"
    if visible_count == 3:
        if endpoint_count == 1 and witness_count == 2:
            missing = "missing_endpoint"
        elif endpoint_count == 2 and witness_count == 1:
            missing = "missing_witness"
        else:
            missing = f"roles_e{endpoint_count}_w{witness_count}"
        return f"{support_kind}:partial3:{missing}:s{support_size}:{mixed_suffix}"
    if visible_count == 2:
        if endpoint_count == 2:
            role_kind = "EE"
        elif witness_count == 2:
            role_kind = "WW"
        else:
            role_kind = "EW"
        split_kind = "split" if support_size == 2 else "collapsed"
        return f"{support_kind}:partial2:{role_kind}:{split_kind}:{mixed_suffix}"
    return f"{support_kind}:partial{visible_count}:e{endpoint_count}:w{witness_count}:s{support_size}"


def _fine_pnode_projection_by_path(D, T: PCNode) -> dict[tuple[int, ...], dict]:
    node_infos = [
        node_info
        for node_info in iter_internal_node_child_labels(T)
        if node_info["kind"] == "P"
    ]
    per_path = {
        tuple(node_info["path"]): {
            "fine_role_pattern_histogram": {},
            "support_boundary_obligation_count": 0,
            "projection_only_obligation_count": 0,
            "fine_examples": [],
        }
        for node_info in node_infos
    }

    prepared_nodes = []
    for node_info in node_infos:
        label_to_branch: dict[int, int] = {}
        for index, child_labels in enumerate(node_info["child_label_sets"]):
            for label in child_labels:
                label_to_branch[label] = index
        prepared_nodes.append((tuple(node_info["path"]), label_to_branch))

    for pair, witnesses in bad_witnesses_by_pair(D).items():
        a, c = pair
        for b, d in combinations(witnesses, 2):
            same_side = (a, c, b, d)
            support_paths = set(quartet_support_paths(T, same_side))
            roles = (
                ("endpoint", a),
                ("endpoint", c),
                ("witness", b),
                ("witness", d),
            )
            for path, label_to_branch in prepared_nodes:
                projected_roles = tuple(
                    (role, label, label_to_branch[label])
                    for role, label in roles
                    if label in label_to_branch
                )
                if len(projected_roles) < 2:
                    continue
                support = tuple(sorted({branch for _, _, branch in projected_roles}))
                is_support_node = path in support_paths
                pattern = _fine_role_pattern(
                    projected_roles,
                    support,
                    is_support_node=is_support_node,
                )
                entry = per_path[path]
                histogram = entry["fine_role_pattern_histogram"]
                histogram[pattern] = histogram.get(pattern, 0) + 1
                if pattern.startswith("support:") and not pattern.endswith("full_four_branch"):
                    entry["support_boundary_obligation_count"] += 1
                if pattern.startswith("projection:"):
                    entry["projection_only_obligation_count"] += 1
                if len(entry["fine_examples"]) < 5:
                    entry["fine_examples"].append(
                        {
                            "same_side": same_side,
                            "support_paths": tuple(sorted(support_paths)),
                            "is_support_node": is_support_node,
                            "projected_roles": projected_roles,
                            "support": support,
                            "fine_role_pattern": pattern,
                        }
                    )
    return per_path


def _iter_pnode_obligation_projections(D, T: PCNode):
    node_infos = [
        node_info
        for node_info in iter_internal_node_child_labels(T)
        if node_info["kind"] == "P"
    ]
    prepared_nodes = []
    for node_info in node_infos:
        label_to_branch: dict[int, int] = {}
        for index, child_labels in enumerate(node_info["child_label_sets"]):
            for label in child_labels:
                label_to_branch[label] = index
        prepared_nodes.append((node_info, label_to_branch))

    for pair, witnesses in bad_witnesses_by_pair(D).items():
        a, c = pair
        for b, d in combinations(witnesses, 2):
            same_side = (a, c, b, d)
            support_paths = set(quartet_support_paths(T, same_side))
            roles = (
                ("endpoint", a),
                ("endpoint", c),
                ("witness", b),
                ("witness", d),
            )
            for node_info, label_to_branch in prepared_nodes:
                path = tuple(node_info["path"])
                projected_roles = tuple(
                    (role, label, label_to_branch[label])
                    for role, label in roles
                    if label in label_to_branch
                )
                if len(projected_roles) < 2:
                    continue
                support = tuple(sorted({branch for _, _, branch in projected_roles}))
                is_support_node = path in support_paths
                pattern = _fine_role_pattern(
                    projected_roles,
                    support,
                    is_support_node=is_support_node,
                )
                yield {
                    "path": path,
                    "degree": len(node_info["child_label_sets"]),
                    "child_label_sets": node_info["child_label_sets"],
                    "same_side": same_side,
                    "pair": pair,
                    "bad_witnesses": (b, d),
                    "support_paths": tuple(sorted(support_paths)),
                    "is_support_node": is_support_node,
                    "projected_roles": projected_roles,
                    "support": support,
                    "fine_role_pattern": pattern,
                }


def pnode_partial_obligation_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_branch_degree: int = 8,
    max_examples: int = 5,
) -> dict:
    """Correlate T091 local branch-order gaps with partial obligations.

    Fully visible four-branch obligations are already counted by
    ``forbidden_chord_pairs`` in T091.  The new fields here count obligations
    that cannot be represented as a pair of branch chords at the current node.
    They are the immediate candidates for separator/interface state.
    """

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if max_branch_degree < 1:
        raise ValueError("max_branch_degree must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

    projection = project_bad_side_obligations_to_pc_nodes(
        D,
        T,
        max_examples_per_node=max_examples,
    )
    fine_by_path = _fine_pnode_projection_by_path(D, T)
    circle = pnode_circle_graph_local_report(
        D,
        T,
        frontier_limit=frontier_limit,
        max_branch_degree=max_branch_degree,
        max_examples=max_examples,
    )
    circle_by_path = {tuple(node["path"]): node for node in circle["nodes"]}

    nodes = []
    role_pattern_histogram: dict = {}
    fine_role_pattern_histogram: dict = {}
    partial_kind_histogram: dict = {}
    status_histogram: dict = {}

    for projection_node in projection["nodes"]:
        if projection_node["kind"] != "P":
            continue
        path = tuple(projection_node["path"])
        circle_node = circle_by_path.get(path)
        if circle_node is None:
            continue

        role_histogram = dict(projection_node["role_pattern_histogram"])
        non_chord_obligation_count = _sum_histogram(role_histogram, NON_CHORD_ROLE_PATTERNS)
        open_obligation_count = _sum_histogram(role_histogram, OPEN_ROLE_PATTERNS)
        collapsed_only_count = int(role_histogram.get("all_in_one_branch", 0))
        four_distinct_count = int(role_histogram.get("4distinct", 0))
        hidden_full_projection_count = (
            int(projection_node["full_projection_count"])
            - int(projection_node["full_distinct_four_branch_count"])
        )
        fine_entry = fine_by_path.get(
            path,
            {
                "fine_role_pattern_histogram": {},
                "support_boundary_obligation_count": 0,
                "projection_only_obligation_count": 0,
                "fine_examples": [],
            },
        )

        node = {
            "path": path,
            "degree": projection_node["degree"],
            "branch_sizes": projection_node["branch_sizes"],
            "status": circle_node["status"],
            "projection_hit_count": projection_node["projection_hit_count"],
            "support_node_hit_count": projection_node["support_node_hit_count"],
            "multi_level_hit_count": projection_node["multi_level_hit_count"],
            "fully_visible_four_branch_obligation_count": four_distinct_count,
            "forbidden_chord_pair_count": projection_node["forbidden_chord_pair_count"],
            "non_chord_obligation_count": non_chord_obligation_count,
            "open_obligation_count": open_obligation_count,
            "collapsed_only_count": collapsed_only_count,
            "hidden_full_projection_count": hidden_full_projection_count,
            "role_pattern_histogram": role_histogram,
            "fine_role_pattern_histogram": fine_entry["fine_role_pattern_histogram"],
            "support_boundary_obligation_count": fine_entry[
                "support_boundary_obligation_count"
            ],
            "projection_only_obligation_count": fine_entry["projection_only_obligation_count"],
            "support_size_histogram": projection_node["support_size_histogram"],
            "endpoint_branch_count_histogram": projection_node[
                "endpoint_branch_count_histogram"
            ],
            "witness_branch_count_histogram": projection_node["witness_branch_count_histogram"],
            "local_order_count": circle_node["local_order_count"],
            "global_cr_branch_order_count": circle_node["global_cr_branch_order_count"],
            "local_extra_order_count": circle_node["local_extra_order_count"],
            "local_missing_global_order_count": circle_node["local_missing_global_order_count"],
            "local_contains_global_cr_orders": circle_node["local_contains_global_cr_orders"],
            "is_vacuous_local_superset": (
                circle_node["status"] == "local_strict_superset"
                and circle_node["forbidden_chord_pair_count"] == 0
            ),
            "is_constrained_local_superset": (
                circle_node["status"] == "local_strict_superset"
                and circle_node["forbidden_chord_pair_count"] > 0
            ),
            "examples": projection_node["examples"][:max_examples],
            "fine_examples": tuple(fine_entry["fine_examples"][:max_examples]),
        }
        node["partial_kind"] = _partial_kind(node)
        node["has_partial_or_multilevel_info"] = (
            node["non_chord_obligation_count"] > 0 or node["multi_level_hit_count"] > 0
        )

        nodes.append(node)
        _merge_histogram(role_pattern_histogram, role_histogram)
        _merge_histogram(fine_role_pattern_histogram, fine_entry["fine_role_pattern_histogram"])
        partial_kind_histogram[node["partial_kind"]] = (
            partial_kind_histogram.get(node["partial_kind"], 0) + 1
        )
        status_histogram[node["status"]] = status_histogram.get(node["status"], 0) + 1

    vacuous_superset_nodes = [node for node in nodes if node["is_vacuous_local_superset"]]
    constrained_superset_nodes = [node for node in nodes if node["is_constrained_local_superset"]]
    unexplained_vacuous_nodes = [
        node
        for node in vacuous_superset_nodes
        if not node["has_partial_or_multilevel_info"]
    ]
    unexplained_constrained_nodes = [
        node
        for node in constrained_superset_nodes
        if not node["has_partial_or_multilevel_info"]
    ]
    global_not_contained_nodes = [
        node for node in nodes if node["status"] == "global_not_contained"
    ]

    interesting_nodes = [
        node
        for node in nodes
        if node["has_partial_or_multilevel_info"]
        or node["status"] in {"global_not_contained", "local_strict_superset", "local_unsat"}
    ]

    return {
        "method": "pnode_partial_obligation_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": circle["frontiers_seen"],
        "frontier_truncated": circle["frontier_truncated"],
        "accepted_frontier_count": circle["accepted_frontier_count"],
        "obligation_count": projection["obligation_count"],
        "obligations_truncated": projection["obligations_truncated"],
        "pnode_count": len(nodes),
        "tested_pnode_count": circle["tested_pnode_count"],
        "status_histogram": _sorted_histogram(status_histogram),
        "partial_kind_histogram": _sorted_histogram(partial_kind_histogram),
        "role_pattern_histogram": _sorted_histogram(role_pattern_histogram),
        "fine_role_pattern_histogram": _sorted_histogram(fine_role_pattern_histogram),
        "nodes_with_partial_or_multilevel_info": sum(
            1 for node in nodes if node["has_partial_or_multilevel_info"]
        ),
        "nodes_with_open_obligations": sum(1 for node in nodes if node["open_obligation_count"]),
        "vacuous_local_superset_count": len(vacuous_superset_nodes),
        "vacuous_local_superset_with_partial_info_count": sum(
            1 for node in vacuous_superset_nodes if node["has_partial_or_multilevel_info"]
        ),
        "vacuous_local_superset_without_partial_info_count": len(unexplained_vacuous_nodes),
        "constrained_local_superset_count": len(constrained_superset_nodes),
        "constrained_local_superset_with_partial_info_count": sum(
            1 for node in constrained_superset_nodes if node["has_partial_or_multilevel_info"]
        ),
        "constrained_local_superset_without_partial_info_count": len(
            unexplained_constrained_nodes
        ),
        "global_not_contained_count": len(global_not_contained_nodes),
        "max_non_chord_obligation_count": max(
            (node["non_chord_obligation_count"] for node in nodes),
            default=0,
        ),
        "max_open_obligation_count": max(
            (node["open_obligation_count"] for node in nodes),
            default=0,
        ),
        "max_multi_level_hit_count": max(
            (node["multi_level_hit_count"] for node in nodes),
            default=0,
        ),
        "max_support_boundary_obligation_count": max(
            (node["support_boundary_obligation_count"] for node in nodes),
            default=0,
        ),
        "max_projection_only_obligation_count": max(
            (node["projection_only_obligation_count"] for node in nodes),
            default=0,
        ),
        "unexplained_vacuous_examples": tuple(unexplained_vacuous_nodes[:max_examples]),
        "unexplained_constrained_examples": tuple(
            unexplained_constrained_nodes[:max_examples]
        ),
        "interesting_nodes": tuple(interesting_nodes[:max_examples]),
        "nodes": tuple(nodes),
        "interpretation": (
            "T092 partial-obligation census layered on T091. Counts show where "
            "fully visible chord constraints need separator/interface data; "
            "this is not a decision procedure."
        ),
    }


def pnode_partial_context_dependency_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_examples: int = 5,
) -> dict:
    """Test whether local branch order decides partial same-side obligations.

    For each P-node and each projected bad-side obligation, this groups global
    frontiers by the induced local branch order.  A mixed group, with both
    satisfying and violating frontiers for the same local branch order, is a
    direct witness that branch order alone is not a sufficient local state.
    """

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")

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

    obligations = tuple(_iter_pnode_obligation_projections(D, T))
    node_accumulator = {
        path: {
            "path": path,
            "degree": len(node_info["child_label_sets"]),
            "branch_sizes": tuple(len(child_labels) for child_labels in node_info["child_label_sets"]),
            "support_obligation_count": 0,
            "support_boundary_obligation_count": 0,
            "fully_visible_obligation_count": 0,
            "projection_only_obligation_count": 0,
            "context_group_count": 0,
            "mixed_group_count": 0,
            "support_boundary_mixed_group_count": 0,
            "fully_visible_mixed_group_count": 0,
            "mixed_obligations": set(),
            "fine_role_pattern_histogram": {},
            "mixed_fine_role_pattern_histogram": {},
            "mixed_examples": [],
        }
        for path, node_info in node_by_path.items()
    }

    for obligation in obligations:
        path = obligation["path"]
        node = node_accumulator[path]
        pattern = obligation["fine_role_pattern"]
        node["fine_role_pattern_histogram"][pattern] = (
            node["fine_role_pattern_histogram"].get(pattern, 0) + 1
        )
        if obligation["is_support_node"]:
            node["support_obligation_count"] += 1
            if pattern == "support:full_four_branch":
                node["fully_visible_obligation_count"] += 1
            else:
                node["support_boundary_obligation_count"] += 1
        else:
            node["projection_only_obligation_count"] += 1

        grouped: dict[tuple[int, ...], dict] = {}
        for frontier in frontiers:
            local_order = local_order_by_path[path].get(frontier)
            if local_order is None:
                continue
            group = grouped.setdefault(
                local_order,
                {
                    "satisfied": 0,
                    "violated": 0,
                    "satisfied_example": None,
                    "violated_example": None,
                },
            )
            if same_side_constraint_satisfied(frontier, obligation["same_side"]):
                group["satisfied"] += 1
                if group["satisfied_example"] is None:
                    group["satisfied_example"] = frontier
            else:
                group["violated"] += 1
                if group["violated_example"] is None:
                    group["violated_example"] = frontier

        for local_order, group in grouped.items():
            node["context_group_count"] += 1
            if group["satisfied"] and group["violated"]:
                node["mixed_group_count"] += 1
                node["mixed_obligations"].add(obligation["same_side"])
                node["mixed_fine_role_pattern_histogram"][pattern] = (
                    node["mixed_fine_role_pattern_histogram"].get(pattern, 0) + 1
                )
                if pattern == "support:full_four_branch":
                    node["fully_visible_mixed_group_count"] += 1
                if obligation["is_support_node"] and pattern != "support:full_four_branch":
                    node["support_boundary_mixed_group_count"] += 1
                if len(node["mixed_examples"]) < max_examples:
                    node["mixed_examples"].append(
                        {
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "is_support_node": obligation["is_support_node"],
                            "local_branch_order": local_order,
                            "satisfied_count": group["satisfied"],
                            "violated_count": group["violated"],
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                            "projected_roles": obligation["projected_roles"],
                            "support": obligation["support"],
                        }
                    )

    nodes = []
    for node in node_accumulator.values():
        mixed_obligations = tuple(sorted(node.pop("mixed_obligations")))
        node["mixed_obligation_count"] = len(mixed_obligations)
        node["mixed_obligation_examples"] = mixed_obligations[:max_examples]
        node["fine_role_pattern_histogram"] = _sorted_histogram(
            node["fine_role_pattern_histogram"]
        )
        node["mixed_fine_role_pattern_histogram"] = _sorted_histogram(
            node["mixed_fine_role_pattern_histogram"]
        )
        node["mixed_examples"] = tuple(node["mixed_examples"])
        nodes.append(node)

    fine_role_pattern_histogram: dict = {}
    mixed_fine_role_pattern_histogram: dict = {}
    for node in nodes:
        _merge_histogram(fine_role_pattern_histogram, node["fine_role_pattern_histogram"])
        _merge_histogram(
            mixed_fine_role_pattern_histogram,
            node["mixed_fine_role_pattern_histogram"],
        )

    interesting_nodes = [
        node
        for node in nodes
        if node["mixed_group_count"]
        or node["support_boundary_obligation_count"]
        or node["fully_visible_mixed_group_count"]
    ]

    return {
        "method": "pnode_partial_context_dependency_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(nodes),
        "obligation_projection_count": len(obligations),
        "support_obligation_count": sum(node["support_obligation_count"] for node in nodes),
        "support_boundary_obligation_count": sum(
            node["support_boundary_obligation_count"] for node in nodes
        ),
        "fully_visible_obligation_count": sum(
            node["fully_visible_obligation_count"] for node in nodes
        ),
        "projection_only_obligation_count": sum(
            node["projection_only_obligation_count"] for node in nodes
        ),
        "context_group_count": sum(node["context_group_count"] for node in nodes),
        "mixed_group_count": sum(node["mixed_group_count"] for node in nodes),
        "support_boundary_mixed_group_count": sum(
            node["support_boundary_mixed_group_count"] for node in nodes
        ),
        "fully_visible_mixed_group_count": sum(
            node["fully_visible_mixed_group_count"] for node in nodes
        ),
        "nodes_with_mixed_groups": sum(1 for node in nodes if node["mixed_group_count"]),
        "nodes_with_support_boundary_mixed_groups": sum(
            1 for node in nodes if node["support_boundary_mixed_group_count"]
        ),
        "fine_role_pattern_histogram": _sorted_histogram(fine_role_pattern_histogram),
        "mixed_fine_role_pattern_histogram": _sorted_histogram(
            mixed_fine_role_pattern_histogram
        ),
        "max_mixed_group_count": max(
            (node["mixed_group_count"] for node in nodes),
            default=0,
        ),
        "max_support_boundary_mixed_group_count": max(
            (node["support_boundary_mixed_group_count"] for node in nodes),
            default=0,
        ),
        "interesting_nodes": tuple(interesting_nodes[:max_examples]),
        "nodes": tuple(nodes),
        "interpretation": (
            "T093 context-dependency diagnostic. Mixed groups show that local "
            "branch order alone does not decide the projected same-side "
            "obligation; this is not a solver."
        ),
    }
