"""Diagnostics for partially visible bad-side obligations at P-nodes.

T091 models fully visible ``same_side(a,c;b,d)`` obligations as forced
non-crossings between two branch chords.  This module measures what that model
does not see: obligations that hit a P-node but collapse roles inside branches
or only expose part of the quartet at that node.  The output is a research
diagnostic, not a solver.
"""

from __future__ import annotations

from itertools import combinations, product

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


def _branch_role_order_signature(frontier, projected_roles) -> tuple:
    """Order the visible endpoint/witness roles inside each touched branch.

    This is a frontier-derived separator diagnostic: it deliberately keeps more
    information than a closed local P-node branch order.  It is not claimed to
    be a compact or composable DP state.
    """

    position = {label: index for index, label in enumerate(frontier)}
    by_branch: dict[int, list[tuple[int, str, int]]] = {}
    for role, label, branch in projected_roles:
        by_branch.setdefault(branch, []).append((position[label], role, label))

    return tuple(
        (
            branch,
            tuple((role, label) for _, role, label in sorted(items)),
        )
        for branch, items in sorted(by_branch.items())
    )


def _obligation_roles(same_side) -> tuple[tuple[str, int], ...]:
    a, c, b, d = same_side
    return (
        ("endpoint", a),
        ("endpoint", c),
        ("witness", b),
        ("witness", d),
    )


def _visible_global_role_order_signature(frontier, projected_roles) -> tuple:
    branch_by_label = {label: branch for _, label, branch in projected_roles}
    items = []
    projected_labels = set(branch_by_label)
    for role, label in _obligation_roles_from_projected(projected_roles):
        if label in projected_labels:
            items.append((frontier.index(label), role, label, branch_by_label[label]))
    return tuple((role, label, branch) for _, role, label, branch in sorted(items))


def _missing_role_order_signature(frontier, same_side, projected_roles) -> tuple:
    projected_labels = {label for _, label, _ in projected_roles}
    items = []
    for role, label in _obligation_roles(same_side):
        if label not in projected_labels:
            items.append((frontier.index(label), role, label))
    return tuple((role, label) for _, role, label in sorted(items))


def _missing_cyclic_gap_signature(frontier, same_side, projected_roles) -> tuple:
    """Place missing roles in cyclic gaps between visible projected roles."""

    projected_labels = {label for _, label, _ in projected_roles}
    visible_positions = sorted(frontier.index(label) for _, label, _ in projected_roles)
    if not visible_positions:
        return ()
    n = len(frontier)
    missing_items = []
    for role, label in _obligation_roles(same_side):
        if label in projected_labels:
            continue
        position = frontier.index(label)
        previous_index = len(visible_positions) - 1
        for index, visible_position in enumerate(visible_positions):
            if visible_position > position:
                previous_index = index - 1 if index > 0 else len(visible_positions) - 1
                break
        previous_position = visible_positions[previous_index]
        cyclic_distance = (position - previous_position) % n
        missing_items.append((previous_index, cyclic_distance, role, label))
    return tuple(
        (gap_index, role, label)
        for gap_index, _, role, label in sorted(missing_items)
    )


def _full_context_role_order_signature(frontier, same_side, projected_roles) -> tuple:
    branch_by_label = {label: branch for _, label, branch in projected_roles}
    items = []
    for role, label in _obligation_roles(same_side):
        if label in branch_by_label:
            location = ("branch", branch_by_label[label])
        else:
            location = ("outside",)
        items.append((frontier.index(label), role, label, location))
    return tuple((role, label, location) for _, role, label, location in sorted(items))


def _obligation_roles_from_projected(projected_roles) -> tuple[tuple[str, int], ...]:
    # The projected roles preserve the original endpoint/witness labels but may
    # omit labels outside the current P-node.
    return tuple((role, label) for role, label, _ in projected_roles)


def _context_ladder_signature(mode: str, frontier, local_order, obligation) -> tuple:
    projected_roles = obligation["projected_roles"]
    same_side = obligation["same_side"]
    if mode == "t094_visible_per_branch":
        return (
            local_order,
            _branch_role_order_signature(frontier, projected_roles),
        )
    if mode == "visible_global":
        return (
            local_order,
            _visible_global_role_order_signature(frontier, projected_roles),
        )
    if mode == "visible_global_plus_missing_order":
        return (
            local_order,
            _visible_global_role_order_signature(frontier, projected_roles),
            _missing_role_order_signature(frontier, same_side, projected_roles),
        )
    if mode == "full_context_order":
        return _full_context_role_order_signature(frontier, same_side, projected_roles)
    raise ValueError(f"unknown context ladder mode: {mode}")


def _context_gap_state_signature(frontier, local_order, obligation) -> tuple:
    return (
        local_order,
        _visible_global_role_order_signature(frontier, obligation["projected_roles"]),
        _missing_cyclic_gap_signature(
            frontier,
            obligation["same_side"],
            obligation["projected_roles"],
        ),
    )


def _is_gap_composition_projection(obligation: dict, scope: str) -> bool:
    has_missing_role = len(obligation["projected_roles"]) < 4
    if not has_missing_role:
        return False
    if scope == "all_open":
        return True
    if scope == "support_open":
        return bool(obligation["is_support_node"])
    if scope == "projection_only_open":
        return not obligation["is_support_node"]
    raise ValueError(f"unknown gap-composition scope: {scope}")


def _product_size(sets: tuple[set, ...]) -> int:
    size = 1
    for values in sets:
        size *= len(values)
    return size


def _first_missing_product_tuple(marginals: tuple[set, ...], actual: set) -> tuple | None:
    sorted_marginals = [
        sorted(values, key=repr)
        for values in marginals
    ]
    for candidate in product(*sorted_marginals):
        if candidate not in actual:
            return candidate
    return None


def _pairwise_closure(relation: set[tuple], arity: int) -> set[tuple]:
    marginals = tuple(
        {value_tuple[index] for value_tuple in relation}
        for index in range(arity)
    )
    pair_projections = {
        (i, j): {
            (value_tuple[i], value_tuple[j])
            for value_tuple in relation
        }
        for i, j in combinations(range(arity), 2)
    }
    closure = set()
    for candidate in product(*(sorted(values, key=repr) for values in marginals)):
        if all(
            (candidate[i], candidate[j]) in pair_projections[(i, j)]
            for i, j in combinations(range(arity), 2)
        ):
            closure.add(candidate)
    return closure


def _first_missing_pairwise_tuple(pairwise_closure: set[tuple], actual: set) -> tuple | None:
    for candidate in sorted(pairwise_closure, key=repr):
        if candidate not in actual:
            return candidate
    return None


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


def pnode_context_gap_arity_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    projection_tuple_size: int = 3,
    scope: str = "all_open",
    max_projection_tuples: int = 50000,
    max_examples: int = 5,
) -> dict:
    """Measure whether joint gap relations need arity beyond binary."""

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if projection_tuple_size < 3:
        raise ValueError("projection_tuple_size must be at least 3")
    if max_projection_tuples < 1:
        raise ValueError("max_projection_tuples must be positive")
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
    open_obligations = tuple(
        obligation
        for obligation in obligations
        if _is_gap_composition_projection(obligation, scope)
    )
    obligations_by_same_side: dict[tuple, list[dict]] = {}
    for obligation in open_obligations:
        obligations_by_same_side.setdefault(obligation["same_side"], []).append(obligation)

    same_side_obligation_count = len(obligations_by_same_side)
    arity_obligation_count = 0
    projection_tuple_count = 0
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
    actual_relation_size_histogram: dict = {}
    product_size_histogram: dict = {}
    pairwise_closure_size_histogram: dict = {}
    pairwise_false_size_histogram: dict = {}
    tuple_pattern_histogram: dict = {}
    binary_sufficient_examples = []
    higher_order_examples = []
    projection_tuple_limit_reached = False

    for same_side, same_side_obligations in sorted(obligations_by_same_side.items()):
        ordered_obligations = sorted(
            same_side_obligations,
            key=lambda obligation: (
                obligation["path"],
                obligation["fine_role_pattern"],
                obligation["projected_roles"],
            ),
        )
        if len(ordered_obligations) < projection_tuple_size:
            continue
        arity_obligation_count += 1

        for obligation_tuple in combinations(ordered_obligations, projection_tuple_size):
            if projection_tuple_count >= max_projection_tuples:
                projection_tuple_limit_reached = True
                break
            projection_tuple_count += 1
            tuple_patterns = tuple(
                obligation["fine_role_pattern"] for obligation in obligation_tuple
            )
            tuple_pattern_histogram[tuple_patterns] = (
                tuple_pattern_histogram.get(tuple_patterns, 0) + 1
            )

            relation_by_visible: dict[tuple, set[tuple]] = {}
            for frontier in frontiers:
                visible_parts = []
                gap_parts = []
                for obligation in obligation_tuple:
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
                    visible_parts.append((path, local_order, visible_order))
                    gap_parts.append((path, gap_signature))
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
                product_size = _product_size(marginals)
                pairwise = _pairwise_closure(actual_relation, projection_tuple_size)
                pairwise_size = len(pairwise)
                product_false_count = product_size - actual_size
                pairwise_false_count = pairwise_size - actual_size

                max_product_size = max(max_product_size, product_size)
                max_pairwise_closure_size = max(
                    max_pairwise_closure_size,
                    pairwise_size,
                )
                max_actual_relation_size = max(max_actual_relation_size, actual_size)
                max_pairwise_false_count = max(
                    max_pairwise_false_count,
                    pairwise_false_count,
                )

                actual_relation_size_histogram[actual_size] = (
                    actual_relation_size_histogram.get(actual_size, 0) + 1
                )
                product_size_histogram[product_size] = (
                    product_size_histogram.get(product_size, 0) + 1
                )
                pairwise_closure_size_histogram[pairwise_size] = (
                    pairwise_closure_size_histogram.get(pairwise_size, 0) + 1
                )
                pairwise_false_size_histogram[pairwise_false_count] = (
                    pairwise_false_size_histogram.get(pairwise_false_count, 0) + 1
                )

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
                                "same_side": same_side,
                                "projection_paths": tuple(
                                    obligation["path"] for obligation in obligation_tuple
                                ),
                                "fine_role_patterns": tuple_patterns,
                                "visible_key": visible_key,
                                "actual_relation_size": actual_size,
                                "product_size": product_size,
                                "pairwise_closure_size": pairwise_size,
                            }
                        )
                else:
                    higher_order_case_count += 1
                    pairwise_false_case_count += 1
                    pairwise_false_tuple_count += pairwise_false_count
                    required_arity = f">=3"
                    if len(higher_order_examples) < max_examples:
                        higher_order_examples.append(
                            {
                                "same_side": same_side,
                                "projection_paths": tuple(
                                    obligation["path"] for obligation in obligation_tuple
                                ),
                                "fine_role_patterns": tuple_patterns,
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
                min_required_arity_histogram[required_arity] = (
                    min_required_arity_histogram.get(required_arity, 0) + 1
                )
        if projection_tuple_limit_reached:
            break

    return {
        "method": "pnode_context_gap_arity_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "projection_tuple_size": projection_tuple_size,
        "scope": scope,
        "max_projection_tuples": max_projection_tuples,
        "projection_tuple_limit_reached": projection_tuple_limit_reached,
        "pnode_count": len(node_infos),
        "obligation_projection_count": len(obligations),
        "open_obligation_projection_count": len(open_obligations),
        "same_side_obligation_count": same_side_obligation_count,
        "arity_obligation_count": arity_obligation_count,
        "projection_tuple_count": projection_tuple_count,
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
        "min_required_arity_histogram": _sorted_histogram(
            min_required_arity_histogram
        ),
        "actual_relation_size_histogram": _sorted_histogram(
            actual_relation_size_histogram
        ),
        "product_size_histogram": _sorted_histogram(product_size_histogram),
        "pairwise_closure_size_histogram": _sorted_histogram(
            pairwise_closure_size_histogram
        ),
        "pairwise_false_size_histogram": _sorted_histogram(
            pairwise_false_size_histogram
        ),
        "tuple_pattern_histogram": _sorted_histogram(tuple_pattern_histogram),
        "binary_sufficient_examples": tuple(binary_sufficient_examples),
        "higher_order_examples": tuple(higher_order_examples),
        "interpretation": (
            "T098 gap-arity diagnostic. Unary means independent marginals "
            "suffice, binary means pairwise projections exactly reconstruct "
            "the observed joint gap relation, and >=3 means pairwise closure "
            "still admits impossible tuples. This is not a solver."
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


def pnode_separator_signature_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_examples: int = 5,
) -> dict:
    """Measure whether a simple separator signature refines T093 collisions.

    T093 groups by ``(P-node, same_side obligation, local branch order)``.  This
    report adds, for every frontier, the order of the obligation's visible
    endpoint/witness roles inside each touched branch.  If T093's mixed groups
    disappear under this refinement, the minimal missing information is exposed
    as separator/order-of-roles data rather than as a closed branch-order
    constraint.
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
            "branch_sizes": tuple(
                len(child_labels) for child_labels in node_info["child_label_sets"]
            ),
            "obligation_projection_count": 0,
            "support_obligation_count": 0,
            "support_boundary_obligation_count": 0,
            "fully_visible_obligation_count": 0,
            "projection_only_obligation_count": 0,
            "branch_order_group_count": 0,
            "branch_order_mixed_group_count": 0,
            "support_boundary_branch_order_mixed_group_count": 0,
            "fully_visible_branch_order_mixed_group_count": 0,
            "separator_signature_group_count": 0,
            "separator_signature_mixed_group_count": 0,
            "support_boundary_separator_mixed_group_count": 0,
            "fully_visible_separator_mixed_group_count": 0,
            "branch_order_mixed_obligations": set(),
            "separator_signature_mixed_obligations": set(),
            "fine_role_pattern_histogram": {},
            "branch_order_mixed_fine_role_pattern_histogram": {},
            "separator_mixed_fine_role_pattern_histogram": {},
            "branch_order_mixed_examples": [],
            "separator_signature_mixed_examples": [],
        }
        for path, node_info in node_by_path.items()
    }

    for obligation in obligations:
        path = obligation["path"]
        node = node_accumulator[path]
        pattern = obligation["fine_role_pattern"]
        node["obligation_projection_count"] += 1
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

        branch_groups: dict[tuple[int, ...], dict] = {}
        separator_groups: dict[tuple, dict] = {}
        for frontier in frontiers:
            local_order = local_order_by_path[path].get(frontier)
            if local_order is None:
                continue
            separator_signature = _branch_role_order_signature(
                frontier,
                obligation["projected_roles"],
            )
            satisfied = same_side_constraint_satisfied(frontier, obligation["same_side"])

            branch_group = branch_groups.setdefault(
                local_order,
                {
                    "satisfied": 0,
                    "violated": 0,
                    "satisfied_example": None,
                    "violated_example": None,
                    "satisfied_signature": None,
                    "violated_signature": None,
                },
            )
            target_prefix = "satisfied" if satisfied else "violated"
            branch_group[target_prefix] += 1
            if branch_group[f"{target_prefix}_example"] is None:
                branch_group[f"{target_prefix}_example"] = frontier
                branch_group[f"{target_prefix}_signature"] = separator_signature

            separator_key = (local_order, separator_signature)
            separator_group = separator_groups.setdefault(
                separator_key,
                {
                    "satisfied": 0,
                    "violated": 0,
                    "satisfied_example": None,
                    "violated_example": None,
                },
            )
            separator_group[target_prefix] += 1
            if separator_group[f"{target_prefix}_example"] is None:
                separator_group[f"{target_prefix}_example"] = frontier

        for local_order, group in branch_groups.items():
            node["branch_order_group_count"] += 1
            if group["satisfied"] and group["violated"]:
                node["branch_order_mixed_group_count"] += 1
                node["branch_order_mixed_obligations"].add(obligation["same_side"])
                node["branch_order_mixed_fine_role_pattern_histogram"][pattern] = (
                    node["branch_order_mixed_fine_role_pattern_histogram"].get(pattern, 0)
                    + 1
                )
                if pattern == "support:full_four_branch":
                    node["fully_visible_branch_order_mixed_group_count"] += 1
                if obligation["is_support_node"] and pattern != "support:full_four_branch":
                    node["support_boundary_branch_order_mixed_group_count"] += 1
                if len(node["branch_order_mixed_examples"]) < max_examples:
                    node["branch_order_mixed_examples"].append(
                        {
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "is_support_node": obligation["is_support_node"],
                            "local_branch_order": local_order,
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                            "satisfied_separator_signature": group[
                                "satisfied_signature"
                            ],
                            "violated_separator_signature": group["violated_signature"],
                        }
                    )

        for (local_order, separator_signature), group in separator_groups.items():
            node["separator_signature_group_count"] += 1
            if group["satisfied"] and group["violated"]:
                node["separator_signature_mixed_group_count"] += 1
                node["separator_signature_mixed_obligations"].add(
                    obligation["same_side"]
                )
                node["separator_mixed_fine_role_pattern_histogram"][pattern] = (
                    node["separator_mixed_fine_role_pattern_histogram"].get(pattern, 0)
                    + 1
                )
                if pattern == "support:full_four_branch":
                    node["fully_visible_separator_mixed_group_count"] += 1
                if obligation["is_support_node"] and pattern != "support:full_four_branch":
                    node["support_boundary_separator_mixed_group_count"] += 1
                if len(node["separator_signature_mixed_examples"]) < max_examples:
                    node["separator_signature_mixed_examples"].append(
                        {
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "is_support_node": obligation["is_support_node"],
                            "local_branch_order": local_order,
                            "separator_signature": separator_signature,
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                        }
                    )

    nodes = []
    fine_role_pattern_histogram: dict = {}
    branch_order_mixed_fine_role_pattern_histogram: dict = {}
    separator_mixed_fine_role_pattern_histogram: dict = {}

    for node in node_accumulator.values():
        node = dict(node)
        node["branch_order_mixed_obligations"] = tuple(
            sorted(node["branch_order_mixed_obligations"])
        )
        node["separator_signature_mixed_obligations"] = tuple(
            sorted(node["separator_signature_mixed_obligations"])
        )
        node["fine_role_pattern_histogram"] = _sorted_histogram(
            node["fine_role_pattern_histogram"]
        )
        node["branch_order_mixed_fine_role_pattern_histogram"] = _sorted_histogram(
            node["branch_order_mixed_fine_role_pattern_histogram"]
        )
        node["separator_mixed_fine_role_pattern_histogram"] = _sorted_histogram(
            node["separator_mixed_fine_role_pattern_histogram"]
        )
        node["removed_mixed_group_count"] = (
            node["branch_order_mixed_group_count"]
            - node["separator_signature_mixed_group_count"]
        )
        node["support_boundary_removed_mixed_group_count"] = (
            node["support_boundary_branch_order_mixed_group_count"]
            - node["support_boundary_separator_mixed_group_count"]
        )
        nodes.append(node)
        _merge_histogram(fine_role_pattern_histogram, node["fine_role_pattern_histogram"])
        _merge_histogram(
            branch_order_mixed_fine_role_pattern_histogram,
            node["branch_order_mixed_fine_role_pattern_histogram"],
        )
        _merge_histogram(
            separator_mixed_fine_role_pattern_histogram,
            node["separator_mixed_fine_role_pattern_histogram"],
        )

    interesting_nodes = [
        node
        for node in nodes
        if node["branch_order_mixed_group_count"]
        or node["separator_signature_mixed_group_count"]
        or node["support_boundary_obligation_count"]
    ]

    branch_order_mixed_group_count = sum(
        node["branch_order_mixed_group_count"] for node in nodes
    )
    separator_signature_mixed_group_count = sum(
        node["separator_signature_mixed_group_count"] for node in nodes
    )
    support_boundary_branch_order_mixed_group_count = sum(
        node["support_boundary_branch_order_mixed_group_count"] for node in nodes
    )
    support_boundary_separator_mixed_group_count = sum(
        node["support_boundary_separator_mixed_group_count"] for node in nodes
    )

    return {
        "method": "pnode_separator_signature_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(nodes),
        "obligation_projection_count": sum(
            node["obligation_projection_count"] for node in nodes
        ),
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
        "branch_order_group_count": sum(
            node["branch_order_group_count"] for node in nodes
        ),
        "branch_order_mixed_group_count": branch_order_mixed_group_count,
        "support_boundary_branch_order_mixed_group_count": (
            support_boundary_branch_order_mixed_group_count
        ),
        "fully_visible_branch_order_mixed_group_count": sum(
            node["fully_visible_branch_order_mixed_group_count"] for node in nodes
        ),
        "separator_signature_group_count": sum(
            node["separator_signature_group_count"] for node in nodes
        ),
        "separator_signature_mixed_group_count": separator_signature_mixed_group_count,
        "support_boundary_separator_mixed_group_count": (
            support_boundary_separator_mixed_group_count
        ),
        "fully_visible_separator_mixed_group_count": sum(
            node["fully_visible_separator_mixed_group_count"] for node in nodes
        ),
        "removed_mixed_group_count": (
            branch_order_mixed_group_count - separator_signature_mixed_group_count
        ),
        "support_boundary_removed_mixed_group_count": (
            support_boundary_branch_order_mixed_group_count
            - support_boundary_separator_mixed_group_count
        ),
        "nodes_with_branch_order_mixed_groups": sum(
            1 for node in nodes if node["branch_order_mixed_group_count"]
        ),
        "nodes_with_separator_signature_mixed_groups": sum(
            1 for node in nodes if node["separator_signature_mixed_group_count"]
        ),
        "fine_role_pattern_histogram": _sorted_histogram(fine_role_pattern_histogram),
        "branch_order_mixed_fine_role_pattern_histogram": _sorted_histogram(
            branch_order_mixed_fine_role_pattern_histogram
        ),
        "separator_mixed_fine_role_pattern_histogram": _sorted_histogram(
            separator_mixed_fine_role_pattern_histogram
        ),
        "max_branch_order_mixed_group_count": max(
            (node["branch_order_mixed_group_count"] for node in nodes),
            default=0,
        ),
        "max_separator_signature_mixed_group_count": max(
            (node["separator_signature_mixed_group_count"] for node in nodes),
            default=0,
        ),
        "interesting_nodes": tuple(interesting_nodes[:max_examples]),
        "nodes": tuple(nodes),
        "interpretation": (
            "T094 separator-signature diagnostic. It tests whether adding the "
            "per-branch order of visible endpoint/witness roles refines the "
            "T093 branch-order mixed groups. This is a frontier-derived "
            "diagnostic, not a compact DP state or solver."
        ),
    }


CONTEXT_LADDER_MODES = (
    "t094_visible_per_branch",
    "visible_global",
    "visible_global_plus_missing_order",
    "full_context_order",
)


def pnode_context_signature_ladder_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_examples: int = 5,
    modes: tuple[str, ...] = CONTEXT_LADDER_MODES,
) -> dict:
    """Compare increasingly context-aware signatures for open obligations."""

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if max_examples < 0:
        raise ValueError("max_examples must be non-negative")
    for mode in modes:
        if mode not in CONTEXT_LADDER_MODES:
            raise ValueError(f"unknown context ladder mode: {mode}")

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
    mode_stats = {
        mode: {
            "group_count": 0,
            "mixed_group_count": 0,
            "support_boundary_mixed_group_count": 0,
            "fully_visible_mixed_group_count": 0,
            "projection_only_mixed_group_count": 0,
            "mixed_fine_role_pattern_histogram": {},
            "mixed_examples": [],
        }
        for mode in modes
    }
    fine_role_pattern_histogram: dict = {}
    obligation_projection_count = 0
    support_boundary_obligation_count = 0
    fully_visible_obligation_count = 0
    projection_only_obligation_count = 0

    for obligation in obligations:
        path = obligation["path"]
        if path not in local_order_by_path:
            continue
        pattern = obligation["fine_role_pattern"]
        obligation_projection_count += 1
        fine_role_pattern_histogram[pattern] = fine_role_pattern_histogram.get(pattern, 0) + 1
        if obligation["is_support_node"]:
            if pattern == "support:full_four_branch":
                fully_visible_obligation_count += 1
            else:
                support_boundary_obligation_count += 1
        else:
            projection_only_obligation_count += 1

        grouped_by_mode = {mode: {} for mode in modes}
        for frontier in frontiers:
            local_order = local_order_by_path[path].get(frontier)
            if local_order is None:
                continue
            satisfied = same_side_constraint_satisfied(frontier, obligation["same_side"])
            target = "satisfied" if satisfied else "violated"
            for mode in modes:
                signature = _context_ladder_signature(
                    mode,
                    frontier,
                    local_order,
                    obligation,
                )
                group = grouped_by_mode[mode].setdefault(
                    signature,
                    {
                        "satisfied": 0,
                        "violated": 0,
                        "satisfied_example": None,
                        "violated_example": None,
                    },
                )
                group[target] += 1
                if group[f"{target}_example"] is None:
                    group[f"{target}_example"] = frontier

        for mode, groups in grouped_by_mode.items():
            stats = mode_stats[mode]
            for signature, group in groups.items():
                stats["group_count"] += 1
                if not (group["satisfied"] and group["violated"]):
                    continue
                stats["mixed_group_count"] += 1
                if obligation["is_support_node"] and pattern != "support:full_four_branch":
                    stats["support_boundary_mixed_group_count"] += 1
                if pattern == "support:full_four_branch":
                    stats["fully_visible_mixed_group_count"] += 1
                if not obligation["is_support_node"]:
                    stats["projection_only_mixed_group_count"] += 1
                mixed_histogram = stats["mixed_fine_role_pattern_histogram"]
                mixed_histogram[pattern] = mixed_histogram.get(pattern, 0) + 1
                if len(stats["mixed_examples"]) < max_examples:
                    stats["mixed_examples"].append(
                        {
                            "same_side": obligation["same_side"],
                            "path": path,
                            "fine_role_pattern": pattern,
                            "is_support_node": obligation["is_support_node"],
                            "signature": signature,
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                        }
                    )

    for stats in mode_stats.values():
        stats["mixed_fine_role_pattern_histogram"] = _sorted_histogram(
            stats["mixed_fine_role_pattern_histogram"]
        )
        stats["mixed_examples"] = tuple(stats["mixed_examples"])

    previous_mode = None
    mode_deltas = {}
    for mode in modes:
        current = mode_stats[mode]["mixed_group_count"]
        mode_deltas[mode] = None if previous_mode is None else previous_mode - current
        previous_mode = current

    return {
        "method": "pnode_context_signature_ladder_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "obligation_projection_count": obligation_projection_count,
        "support_boundary_obligation_count": support_boundary_obligation_count,
        "fully_visible_obligation_count": fully_visible_obligation_count,
        "projection_only_obligation_count": projection_only_obligation_count,
        "fine_role_pattern_histogram": _sorted_histogram(fine_role_pattern_histogram),
        "modes": mode_stats,
        "mode_mixed_group_deltas": mode_deltas,
        "interpretation": (
            "T095 context-signature ladder. It compares visible-only and "
            "context-aware signatures for open same-side obligations. These "
            "signatures are diagnostics over enumerated frontiers, not compact "
            "DP states or solver decisions."
        ),
    }


def pnode_context_gap_relation_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    max_examples: int = 5,
) -> dict:
    """Measure the insertion-gap relation needed by open obligations."""

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
    fine_role_pattern_histogram: dict = {}
    gap_relation_size_histogram: dict = {}
    visible_missing_mixed_histogram: dict = {}
    gap_mixed_histogram: dict = {}
    obligation_projection_count = 0
    support_boundary_obligation_count = 0
    fully_visible_obligation_count = 0
    projection_only_obligation_count = 0
    visible_missing_group_count = 0
    visible_missing_mixed_group_count = 0
    gap_state_group_count = 0
    gap_state_mixed_group_count = 0
    full_context_group_count = 0
    full_context_mixed_group_count = 0
    gap_relation_bucket_count = 0
    nontrivial_gap_relation_bucket_count = 0
    max_gap_patterns_per_visible_state = 0
    max_gap_state_count_per_obligation = 0
    visible_missing_mixed_examples = []
    gap_mixed_examples = []
    nontrivial_gap_relation_examples = []

    for obligation in obligations:
        path = obligation["path"]
        if path not in local_order_by_path:
            continue
        pattern = obligation["fine_role_pattern"]
        obligation_projection_count += 1
        fine_role_pattern_histogram[pattern] = fine_role_pattern_histogram.get(pattern, 0) + 1
        if obligation["is_support_node"]:
            if pattern == "support:full_four_branch":
                fully_visible_obligation_count += 1
            else:
                support_boundary_obligation_count += 1
        else:
            projection_only_obligation_count += 1

        visible_missing_groups = {}
        gap_state_groups = {}
        full_context_groups = {}
        gap_relation: dict[tuple, set[tuple]] = {}
        for frontier in frontiers:
            local_order = local_order_by_path[path].get(frontier)
            if local_order is None:
                continue
            visible_order = _visible_global_role_order_signature(
                frontier,
                obligation["projected_roles"],
            )
            missing_order = _missing_role_order_signature(
                frontier,
                obligation["same_side"],
                obligation["projected_roles"],
            )
            gap_signature = _missing_cyclic_gap_signature(
                frontier,
                obligation["same_side"],
                obligation["projected_roles"],
            )
            visible_missing_state = (local_order, visible_order, missing_order)
            gap_state = (local_order, visible_order, gap_signature)
            full_context_state = _full_context_role_order_signature(
                frontier,
                obligation["same_side"],
                obligation["projected_roles"],
            )
            satisfied = same_side_constraint_satisfied(frontier, obligation["same_side"])
            target = "satisfied" if satisfied else "violated"

            for groups, state in (
                (visible_missing_groups, visible_missing_state),
                (gap_state_groups, gap_state),
                (full_context_groups, full_context_state),
            ):
                group = groups.setdefault(
                    state,
                    {
                        "satisfied": 0,
                        "violated": 0,
                        "satisfied_example": None,
                        "violated_example": None,
                    },
                )
                group[target] += 1
                if group[f"{target}_example"] is None:
                    group[f"{target}_example"] = frontier

            visible_state = (local_order, visible_order)
            gap_relation.setdefault(visible_state, set()).add(gap_signature)

        max_gap_state_count_per_obligation = max(
            max_gap_state_count_per_obligation,
            len(gap_state_groups),
        )

        for state, group in visible_missing_groups.items():
            visible_missing_group_count += 1
            if group["satisfied"] and group["violated"]:
                visible_missing_mixed_group_count += 1
                visible_missing_mixed_histogram[pattern] = (
                    visible_missing_mixed_histogram.get(pattern, 0) + 1
                )
                if len(visible_missing_mixed_examples) < max_examples:
                    visible_missing_mixed_examples.append(
                        {
                            "path": path,
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "state": state,
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                        }
                    )

        for state, group in gap_state_groups.items():
            gap_state_group_count += 1
            if group["satisfied"] and group["violated"]:
                gap_state_mixed_group_count += 1
                gap_mixed_histogram[pattern] = gap_mixed_histogram.get(pattern, 0) + 1
                if len(gap_mixed_examples) < max_examples:
                    gap_mixed_examples.append(
                        {
                            "path": path,
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "state": state,
                            "satisfied_frontier": group["satisfied_example"],
                            "violated_frontier": group["violated_example"],
                        }
                    )

        for group in full_context_groups.values():
            full_context_group_count += 1
            if group["satisfied"] and group["violated"]:
                full_context_mixed_group_count += 1

        for visible_state, gap_patterns in gap_relation.items():
            gap_relation_bucket_count += 1
            relation_size = len(gap_patterns)
            gap_relation_size_histogram[relation_size] = (
                gap_relation_size_histogram.get(relation_size, 0) + 1
            )
            max_gap_patterns_per_visible_state = max(
                max_gap_patterns_per_visible_state,
                relation_size,
            )
            if relation_size > 1:
                nontrivial_gap_relation_bucket_count += 1
                if len(nontrivial_gap_relation_examples) < max_examples:
                    nontrivial_gap_relation_examples.append(
                        {
                            "path": path,
                            "same_side": obligation["same_side"],
                            "fine_role_pattern": pattern,
                            "visible_state": visible_state,
                            "gap_patterns": tuple(sorted(gap_patterns)),
                        }
                    )

    return {
        "method": "pnode_context_gap_relation_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "pnode_count": len(node_infos),
        "obligation_projection_count": obligation_projection_count,
        "support_boundary_obligation_count": support_boundary_obligation_count,
        "fully_visible_obligation_count": fully_visible_obligation_count,
        "projection_only_obligation_count": projection_only_obligation_count,
        "fine_role_pattern_histogram": _sorted_histogram(fine_role_pattern_histogram),
        "visible_missing_group_count": visible_missing_group_count,
        "visible_missing_mixed_group_count": visible_missing_mixed_group_count,
        "gap_state_group_count": gap_state_group_count,
        "gap_state_mixed_group_count": gap_state_mixed_group_count,
        "full_context_group_count": full_context_group_count,
        "full_context_mixed_group_count": full_context_mixed_group_count,
        "gap_relation_bucket_count": gap_relation_bucket_count,
        "nontrivial_gap_relation_bucket_count": nontrivial_gap_relation_bucket_count,
        "max_gap_patterns_per_visible_state": max_gap_patterns_per_visible_state,
        "max_gap_state_count_per_obligation": max_gap_state_count_per_obligation,
        "gap_relation_size_histogram": _sorted_histogram(gap_relation_size_histogram),
        "visible_missing_mixed_fine_role_pattern_histogram": _sorted_histogram(
            visible_missing_mixed_histogram
        ),
        "gap_mixed_fine_role_pattern_histogram": _sorted_histogram(gap_mixed_histogram),
        "visible_missing_mixed_examples": tuple(visible_missing_mixed_examples),
        "gap_mixed_examples": tuple(gap_mixed_examples),
        "nontrivial_gap_relation_examples": tuple(nontrivial_gap_relation_examples),
        "interpretation": (
            "T096 context-gap diagnostic. A zero gap_state_mixed count means "
            "that insertion gaps explain the open obligation on enumerated "
            "frontiers; relation-size counters measure whether this is compact. "
            "This is not a solver."
        ),
    }


def pnode_context_gap_composition_report(
    D,
    T: PCNode,
    *,
    frontier_limit: int = 20000,
    projection_tuple_size: int = 2,
    scope: str = "all_open",
    max_projection_tuples: int = 50000,
    max_examples: int = 5,
) -> dict:
    """Compare joint gap relations with products of local marginals.

    T096 shows that gap signatures decide isolated open obligations on the
    enumerated frontiers.  This diagnostic asks a stricter question: for the
    same ``same_side`` obligation seen through several P-nodes, can the gap
    choices be composed independently once the visible state of each projection
    is fixed?
    """

    tree_labels = set(labels(T))
    if tree_labels != set(range(len(D))):
        raise ValueError("PC-tree labels must be exactly 0..n-1")
    if frontier_limit <= 0:
        raise ValueError("frontier_limit must be positive")
    if projection_tuple_size < 2:
        raise ValueError("projection_tuple_size must be at least 2")
    if max_projection_tuples < 1:
        raise ValueError("max_projection_tuples must be positive")
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
    open_obligations = tuple(
        obligation
        for obligation in obligations
        if _is_gap_composition_projection(obligation, scope)
    )
    obligations_by_same_side: dict[tuple, list[dict]] = {}
    for obligation in open_obligations:
        obligations_by_same_side.setdefault(obligation["same_side"], []).append(obligation)

    same_side_obligation_count = len(obligations_by_same_side)
    composition_obligation_count = 0
    projection_tuple_count = 0
    visible_relation_case_count = 0
    nontrivial_product_case_count = 0
    false_product_case_count = 0
    false_product_tuple_count = 0
    max_product_size = 0
    max_actual_relation_size = 0
    max_false_product_count = 0
    actual_relation_size_histogram: dict = {}
    product_size_histogram: dict = {}
    false_product_size_histogram: dict = {}
    tuple_pattern_histogram: dict = {}
    false_product_examples = []
    nontrivial_product_examples = []
    projection_tuple_limit_reached = False

    for same_side, same_side_obligations in sorted(obligations_by_same_side.items()):
        ordered_obligations = sorted(
            same_side_obligations,
            key=lambda obligation: (
                obligation["path"],
                obligation["fine_role_pattern"],
                obligation["projected_roles"],
            ),
        )
        if len(ordered_obligations) < projection_tuple_size:
            continue
        composition_obligation_count += 1

        for obligation_tuple in combinations(ordered_obligations, projection_tuple_size):
            if projection_tuple_count >= max_projection_tuples:
                projection_tuple_limit_reached = True
                break
            projection_tuple_count += 1
            tuple_patterns = tuple(
                obligation["fine_role_pattern"] for obligation in obligation_tuple
            )
            tuple_pattern_histogram[tuple_patterns] = (
                tuple_pattern_histogram.get(tuple_patterns, 0) + 1
            )

            relation_by_visible: dict[tuple, set[tuple]] = {}
            for frontier in frontiers:
                visible_parts = []
                gap_parts = []
                for obligation in obligation_tuple:
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
                    visible_parts.append((path, local_order, visible_order))
                    gap_parts.append((path, gap_signature))
                visible_key = tuple(visible_parts)
                gap_tuple = tuple(gap_parts)
                relation_by_visible.setdefault(visible_key, set()).add(gap_tuple)

            for visible_key, actual_relation in relation_by_visible.items():
                visible_relation_case_count += 1
                actual_size = len(actual_relation)
                marginals = tuple(
                    {gap_tuple[index] for gap_tuple in actual_relation}
                    for index in range(projection_tuple_size)
                )
                product_size = _product_size(marginals)
                false_count = product_size - actual_size
                max_product_size = max(max_product_size, product_size)
                max_actual_relation_size = max(max_actual_relation_size, actual_size)
                max_false_product_count = max(max_false_product_count, false_count)
                actual_relation_size_histogram[actual_size] = (
                    actual_relation_size_histogram.get(actual_size, 0) + 1
                )
                product_size_histogram[product_size] = (
                    product_size_histogram.get(product_size, 0) + 1
                )
                false_product_size_histogram[false_count] = (
                    false_product_size_histogram.get(false_count, 0) + 1
                )

                if product_size > 1:
                    nontrivial_product_case_count += 1
                    if len(nontrivial_product_examples) < max_examples:
                        nontrivial_product_examples.append(
                            {
                                "same_side": same_side,
                                "projection_paths": tuple(
                                    obligation["path"] for obligation in obligation_tuple
                                ),
                                "fine_role_patterns": tuple_patterns,
                                "visible_key": visible_key,
                                "actual_relation_size": actual_size,
                                "product_size": product_size,
                                "marginal_sizes": tuple(
                                    len(values) for values in marginals
                                ),
                            }
                        )
                if false_count > 0:
                    false_product_case_count += 1
                    false_product_tuple_count += false_count
                    if len(false_product_examples) < max_examples:
                        false_product_examples.append(
                            {
                                "same_side": same_side,
                                "projection_paths": tuple(
                                    obligation["path"] for obligation in obligation_tuple
                                ),
                                "fine_role_patterns": tuple_patterns,
                                "visible_key": visible_key,
                                "actual_gap_tuples": tuple(
                                    sorted(actual_relation, key=repr)[:max_examples]
                                ),
                                "marginal_gap_patterns": tuple(
                                    tuple(sorted(values, key=repr))
                                    for values in marginals
                                ),
                                "missing_product_gap_tuple": _first_missing_product_tuple(
                                    marginals,
                                    actual_relation,
                                ),
                                "actual_relation_size": actual_size,
                                "product_size": product_size,
                                "false_product_count": false_count,
                            }
                        )
        if projection_tuple_limit_reached:
            break

    return {
        "method": "pnode_context_gap_composition_report",
        "n": len(D),
        "frontier_limit": frontier_limit,
        "frontiers_seen": len(frontiers),
        "frontier_truncated": frontier_truncated,
        "projection_tuple_size": projection_tuple_size,
        "scope": scope,
        "max_projection_tuples": max_projection_tuples,
        "projection_tuple_limit_reached": projection_tuple_limit_reached,
        "pnode_count": len(node_infos),
        "obligation_projection_count": len(obligations),
        "open_obligation_projection_count": len(open_obligations),
        "same_side_obligation_count": same_side_obligation_count,
        "composition_obligation_count": composition_obligation_count,
        "projection_tuple_count": projection_tuple_count,
        "visible_relation_case_count": visible_relation_case_count,
        "nontrivial_product_case_count": nontrivial_product_case_count,
        "false_product_case_count": false_product_case_count,
        "false_product_tuple_count": false_product_tuple_count,
        "max_product_size": max_product_size,
        "max_actual_relation_size": max_actual_relation_size,
        "max_false_product_count": max_false_product_count,
        "actual_relation_size_histogram": _sorted_histogram(
            actual_relation_size_histogram
        ),
        "product_size_histogram": _sorted_histogram(product_size_histogram),
        "false_product_size_histogram": _sorted_histogram(
            false_product_size_histogram
        ),
        "tuple_pattern_histogram": _sorted_histogram(tuple_pattern_histogram),
        "nontrivial_product_examples": tuple(nontrivial_product_examples),
        "false_product_examples": tuple(false_product_examples),
        "interpretation": (
            "T097 gap-composition diagnostic. false_product_case_count > 0 "
            "refutes independent composition of per-projection gap marginals "
            "for the enumerated frontiers. Zero false products is only a "
            "bounded non-refutation, not a proof."
        ),
    }
