"""Scratch space for SAT/CSP-style encodings of cyclic constraints.

Nothing in this module is a proved general solver.  The functions below are
frontier-enumeration experiments that treat Proposition 4.5 obstructions as
nogoods on fixed orders, then compare the resulting filter with the exact cR
predicate.  This gives Piste C falsifiable data before a real variable-level
PC-tree encoding is attempted.
"""

from __future__ import annotations

from itertools import combinations, islice, permutations, product
from typing import Iterable, Optional, Sequence

from pc_circular.pc_tree import PCNode, enumerate_frontiers, labels
from pc_circular.predicates import (
    all_circular_orders,
    canonical_circular_order,
    find_farthest_prop_4_5_obstruction,
    is_precircular_order_cR,
    is_quasi_circular_order,
    validate_dissimilarity,
)
from pc_circular.solvers.dp_experiments import bad_witnesses_by_pair


Order = Sequence[int]
Path = tuple[int, ...]
Assignment = dict[Path, tuple[int, ...]]
NogoodSignature = tuple[tuple[Path, tuple[int, ...]], ...]


def not_implemented_status() -> dict:
    return {
        "implemented": False,
        "reason": "No sound variable-level constraint encoding has been proved sufficient yet",
    }


def _materialize_orders(
    n: int,
    *,
    quasi_orders: Optional[Iterable[Order]],
    pc_tree: Optional[PCNode],
    limit: Optional[int],
) -> tuple[list[tuple[int, ...]], bool]:
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if quasi_orders is not None and pc_tree is not None:
        raise ValueError("provide quasi_orders or pc_tree, not both")

    if pc_tree is not None:
        raw_orders = enumerate_frontiers(
            pc_tree,
            canonical=True,
            limit=None if limit is None else limit + 1,
        )
    elif quasi_orders is not None:
        raw_orders = list(islice(quasi_orders, None if limit is None else limit + 1))
    else:
        raw_orders = list(islice(all_circular_orders(n), None if limit is None else limit + 1))

    seen: set[tuple[int, ...]] = set()
    orders: list[tuple[int, ...]] = []
    truncated = False
    for raw_order in raw_orders:
        order = canonical_circular_order(raw_order)
        if len(order) != n or set(order) != set(range(n)):
            raise ValueError("orders must be permutations of 0..n-1")
        if order in seen:
            continue
        if limit is not None and len(orders) >= limit:
            truncated = True
            break
        seen.add(order)
        orders.append(order)

    return orders, truncated


def _domain_for_node(node: PCNode, *, max_p_degree: int) -> tuple[tuple[int, ...], ...] | None:
    degree = len(node.children)
    if node.kind == "P":
        if degree > max_p_degree:
            return None
        return tuple(permutations(range(degree)))
    if node.kind == "C":
        forward = tuple(range(degree))
        backward = tuple(reversed(forward))
        return tuple(dict.fromkeys((forward, backward)))
    raise ValueError("only internal P/C nodes have domains")


def build_local_domains(pc_tree: PCNode, *, max_p_degree: int = 3) -> dict:
    """Build finite domains for local PC-tree choices.

    This is an experimental CSP encoding.  A large ``P`` node is reported as
    unsupported instead of being turned into a negative decision.
    """

    if max_p_degree < 1:
        raise ValueError("max_p_degree must be positive")

    variables: list[dict] = []
    domains: dict[Path, tuple[tuple[int, ...], ...]] = {}
    unsupported: list[dict] = []

    def visit(node: PCNode, path: Path) -> None:
        if node.kind == "leaf":
            return
        domain = _domain_for_node(node, max_p_degree=max_p_degree)
        variable = {
            "path": path,
            "kind": node.kind,
            "degree": len(node.children),
            "labels": labels(node),
        }
        variables.append(variable)
        if domain is None:
            unsupported.append(
                {
                    "path": path,
                    "kind": node.kind,
                    "degree": len(node.children),
                    "reason": f"P degree exceeds max_p_degree={max_p_degree}",
                }
            )
        else:
            domains[path] = domain
        for idx, child in enumerate(node.children):
            visit(child, path + (idx,))

    visit(pc_tree, ())
    return {
        "implemented": True,
        "method": "local_pc_node_domains",
        "max_p_degree": max_p_degree,
        "variables": variables,
        "domains": domains,
        "unsupported": unsupported,
        "supported": not unsupported,
    }


def frontier_from_assignment(pc_tree: PCNode, assignment: Assignment) -> tuple[int, ...]:
    """Reconstruct the linear frontier induced by a complete local assignment."""

    def build(node: PCNode, path: Path) -> tuple[int, ...]:
        if node.kind == "leaf":
            assert node.label is not None
            return (node.label,)

        choice = assignment.get(path)
        degree = len(node.children)
        if choice is None:
            raise ValueError(f"missing assignment for internal node at path {path}")
        if sorted(choice) != list(range(degree)):
            raise ValueError(f"invalid child order at path {path}: {choice}")
        if node.kind == "C":
            forward = tuple(range(degree))
            backward = tuple(reversed(forward))
            if choice not in {forward, backward}:
                raise ValueError(f"C node path {path} only supports forward/reverse")

        result: list[int] = []
        for child_idx in choice:
            result.extend(build(node.children[child_idx], path + (child_idx,)))
        return tuple(result)

    return build(pc_tree, ())


def iter_local_assignments(encoding: dict, *, limit: Optional[int] = None) -> Iterable[Assignment]:
    """Yield complete assignments for a supported local-domain encoding."""

    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if encoding["unsupported"]:
        raise ValueError("cannot enumerate assignments for unsupported domains")

    paths = [variable["path"] for variable in encoding["variables"]]
    domain_lists = [encoding["domains"][path] for path in paths]
    count = 0
    for values in product(*domain_lists):
        if limit is not None and count >= limit:
            break
        count += 1
        yield dict(zip(paths, values))


def assignment_frontier_report(
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    canonical: bool = True,
) -> dict:
    """Enumerate frontiers through local assignments and report duplicates."""

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": "local_assignment_frontier_enumeration",
        "encoding": encoding,
        "complete": True,
        "frontiers": [],
        "counts": {
            "assignments_seen": 0,
            "unique_frontiers": 0,
            "duplicate_frontiers": 0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    seen: set[tuple[int, ...]] = set()
    truncated = False
    for assignment in iter_local_assignments(encoding, limit=None if limit is None else limit + 1):
        if limit is not None and report["counts"]["assignments_seen"] >= limit:
            truncated = True
            break
        report["counts"]["assignments_seen"] += 1
        frontier = frontier_from_assignment(pc_tree, assignment)
        key = canonical_circular_order(frontier) if canonical else frontier
        if key in seen:
            report["counts"]["duplicate_frontiers"] += 1
            continue
        seen.add(key)
        report["frontiers"].append(key)

    report["complete"] = not truncated
    report["counts"]["unique_frontiers"] = len(report["frontiers"])
    return report


def _accepted_by_source(D, order: Order, *, source: str) -> bool:
    if source == "cr":
        return is_precircular_order_cR(D, order)
    if source == "prop45":
        return find_farthest_prop_4_5_obstruction(D, order) is None
    raise ValueError("source must be 'cr' or 'prop45'")


def solve_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    source: str = "cr",
    max_p_degree: int = 3,
    require_quasi: bool = False,
    limit: Optional[int] = None,
) -> dict:
    """Experimental finite-domain CSP search over local PC-tree choices.

    ``source='cr'`` uses the exact fixed-order cR predicate as direct nogoods.
    ``source='prop45'`` is diagnostic only and should normally be combined with
    ``require_quasi=True`` to keep the proposition precondition explicit.
    """

    validate_dissimilarity(D)
    frontier_report = assignment_frontier_report(
        pc_tree,
        max_p_degree=max_p_degree,
        limit=limit,
        canonical=True,
    )
    counts = {
        "frontiers_seen": len(frontier_report["frontiers"]),
        "skipped_non_quasi": 0,
        "checked_frontiers": 0,
        "accepted_frontiers": 0,
        "rejected_frontiers": 0,
    }
    result = {
        "implemented": True,
        "solver": "local_domain_nogood_csp_experiment",
        "source": source,
        "exists": None,
        "order": None,
        "complete": frontier_report["complete"],
        "unsupported": frontier_report["encoding"]["unsupported"],
        "counts": counts,
        "accepted_frontiers": [],
        "first_rejected": None,
        "note": "experimental assignment enumeration; not a proved compact solver",
    }
    if result["unsupported"]:
        result["complete"] = False
        result["note"] = "unsupported local domain; no negative decision made"
        return result

    accepted: list[tuple[int, ...]] = []
    for order in frontier_report["frontiers"]:
        if require_quasi and not is_quasi_circular_order(D, order):
            counts["skipped_non_quasi"] += 1
            continue

        counts["checked_frontiers"] += 1
        if _accepted_by_source(D, order, source=source):
            counts["accepted_frontiers"] += 1
            accepted.append(order)
            if result["order"] is None:
                result["order"] = list(order)
        else:
            counts["rejected_frontiers"] += 1
            if result["first_rejected"] is None:
                result["first_rejected"] = list(order)

    result["exists"] = bool(accepted)
    result["accepted_frontiers"] = [list(order) for order in accepted]
    return result


def accepted_frontiers_by_csp(
    D,
    pc_tree: PCNode,
    *,
    source: str = "cr",
    max_p_degree: int = 3,
    require_quasi: bool = False,
) -> set[tuple[int, ...]]:
    """Return the set of frontiers accepted by the experimental CSP."""

    result = solve_nogood_csp(
        D,
        pc_tree,
        source=source,
        max_p_degree=max_p_degree,
        require_quasi=require_quasi,
    )
    if result["unsupported"]:
        raise ValueError("unsupported local domain")
    return {tuple(order) for order in result["accepted_frontiers"]}


def _cr_atom_violation(D, x: int, y: int, z: int, t: int) -> dict | None:
    lhs = D[x][z]
    rhs = min(
        max(D[x][y], D[y][z]),
        max(D[x][t], D[t][z]),
    )
    if lhs < rhs:
        return {
            "atom": (x, y, z, t),
            "lhs_pair": (x, z),
            "lhs": lhs,
            "rhs": rhs,
            "d_xy": D[x][y],
            "d_yz": D[y][z],
            "d_xt": D[x][t],
            "d_tz": D[t][z],
        }
    return None


def forbidden_cr_atoms(D) -> list[dict]:
    """Return ordered cyclic quartet atoms that violate the cR inequality."""

    n = validate_dissimilarity(D)
    atoms: list[dict] = []
    for x in range(n):
        for y in range(n):
            if y == x:
                continue
            for z in range(n):
                if z in {x, y}:
                    continue
                for t in range(n):
                    if t in {x, y, z}:
                        continue
                    violation = _cr_atom_violation(D, x, y, z, t)
                    if violation is not None:
                        atoms.append(violation)
    return atoms


def forbidden_bad_side_atoms(D) -> list[dict]:
    """Return cR-forbidden atoms generated from bad witnesses by endpoint pair.

    For an unordered pair ``{a,b}``, any two bad witnesses ``y,t`` create the
    two cyclic forbidden orientations ``a,y,b,t`` and ``a,t,b,y``.  This is the
    bad-side fixed-order characterization in atom form; it avoids generating
    every ordered quartet whose inequality is numerically bad.
    """

    validate_dissimilarity(D)
    atoms: list[dict] = []
    for pair, witnesses in bad_witnesses_by_pair(D).items():
        a, b = pair
        for y, t in combinations(witnesses, 2):
            for atom in ((a, y, b, t), (a, t, b, y)):
                violation = _cr_atom_violation(D, *atom)
                if violation is None:
                    raise AssertionError("bad-side atom must violate the cR inequality")
                atoms.append(
                    {
                        **violation,
                        "pair": pair,
                        "bad_witnesses": (y, t),
                        "source": "bad_side_pair",
                    }
                )
    return atoms


def _cyclic_atom_occurs(order: Order, atom: Sequence[int]) -> bool:
    x, y, z, t = atom
    position = {value: idx for idx, value in enumerate(order)}
    n = len(order)
    return 0 < (position[y] - position[x]) % n < (position[z] - position[x]) % n < (
        position[t] - position[x]
    ) % n


def quartet_support_paths(pc_tree: PCNode, atom: Sequence[int]) -> tuple[Path, ...]:
    """Return local variables whose choices determine this atom's order.

    A node is included when the queried labels below it are split across at
    least two child branches.  Descendants are relevant only inside child
    branches containing at least two queried labels.
    """

    wanted = set(atom)
    if len(wanted) != len(tuple(atom)):
        raise ValueError("atom labels must be distinct")
    if not wanted.issubset(set(labels(pc_tree))):
        raise ValueError("atom labels must all occur in the PC-tree")

    support: list[Path] = []

    def visit(node: PCNode, path: Path, active: set[int]) -> None:
        if node.kind == "leaf" or len(active) < 2:
            return
        child_active: list[tuple[int, set[int]]] = []
        for idx, child in enumerate(node.children):
            child_labels = set(labels(child))
            overlap = active & child_labels
            if overlap:
                child_active.append((idx, overlap))
        if len(child_active) >= 2:
            support.append(path)
        for idx, overlap in child_active:
            if len(overlap) >= 2:
                visit(node.children[idx], path + (idx,), overlap)

    visit(pc_tree, (), wanted)
    return tuple(support)


def _nogood_signature(assignment: Assignment, support: Sequence[Path]) -> NogoodSignature:
    return tuple((path, assignment[path]) for path in support)


def _nogood_matches(assignment: Assignment, signature: NogoodSignature) -> bool:
    return all(assignment.get(path) == choice for path, choice in signature)


def _project_labels_order_from_support_assignment(
    pc_tree: PCNode,
    wanted_labels: Sequence[int],
    support_assignment: Assignment,
) -> tuple[int, ...]:
    """Project selected labels using the available local support choices."""

    wanted = set(wanted_labels)
    if len(wanted) != len(tuple(wanted_labels)):
        raise ValueError("projected labels must be distinct")

    def build(node: PCNode, path: Path) -> tuple[int, ...]:
        if node.kind == "leaf":
            assert node.label is not None
            return (node.label,) if node.label in wanted else ()

        nonempty_children = []
        for idx, child in enumerate(node.children):
            if wanted & set(labels(child)):
                nonempty_children.append(idx)

        if len(nonempty_children) >= 2:
            choice = support_assignment.get(path)
            if choice is None:
                raise ValueError(f"missing support assignment for label split at path {path}")
        else:
            choice = tuple(range(len(node.children)))

        result: list[int] = []
        for child_idx in choice:
            result.extend(build(node.children[child_idx], path + (child_idx,)))
        return tuple(result)

    order = build(pc_tree, ())
    if set(order) != wanted or len(order) != len(wanted):
        raise ValueError("support assignment did not project every label exactly once")
    return order


def _project_atom_order_from_support_assignment(
    pc_tree: PCNode,
    atom: Sequence[int],
    support_assignment: Assignment,
) -> tuple[int, ...]:
    """Project the four atom labels using only choices on their support."""

    return _project_labels_order_from_support_assignment(pc_tree, atom, support_assignment)


def quartet_type(order: Sequence[int]) -> tuple[int, ...]:
    """Return the circular type of four labels modulo rotation/reversal."""

    seq = tuple(order)
    if len(seq) != 4 or len(set(seq)) != 4:
        raise ValueError("quartet type needs four distinct labels")
    return canonical_circular_order(seq)


def _quartet_type_is_cr_allowed(D, type_order: Sequence[int]) -> bool:
    """Return whether this circular quartet type satisfies all cR rotations."""

    seq = quartet_type(type_order)
    for i in range(4):
        atom = (seq[i], seq[(i + 1) % 4], seq[(i + 2) % 4], seq[(i + 3) % 4])
        if _cr_atom_violation(D, *atom) is not None:
            return False
    return True


def quartet_allowed_types(D, quartet: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    """Return cR-allowed circular types for a four-label subset.

    The result contains at most three representatives modulo rotation and
    reversal.  This is a local fixed-quartet relation; it does not assert that a
    global PC-tree frontier realizing the type exists.
    """

    n = validate_dissimilarity(D)
    labels_set = set(quartet)
    if len(tuple(quartet)) != 4 or len(labels_set) != 4:
        raise ValueError("quartet must contain four distinct labels")
    if not labels_set.issubset(set(range(n))):
        raise ValueError("quartet labels must be in 0..n-1")

    types = {quartet_type(order) for order in permutations(tuple(quartet))}
    return tuple(sorted(type_order for type_order in types if _quartet_type_is_cr_allowed(D, type_order)))


def _minimal_determining_scope(
    paths: Sequence[Path],
    rows: Sequence[dict],
    value_key: str,
) -> tuple[Path, ...] | None:
    """Find a smallest variable subset determining ``value_key`` over rows."""

    ordered_paths = tuple(paths)
    for size in range(len(ordered_paths) + 1):
        for subset in combinations(ordered_paths, size):
            buckets: dict[NogoodSignature, set] = {}
            for row in rows:
                signature = _nogood_signature(row["assignment"], subset)
                buckets.setdefault(signature, set()).add(row[value_key])
            if all(len(values) == 1 for values in buckets.values()):
                return tuple(subset)
    return None


def _quartet_support_rows(
    D,
    pc_tree: PCNode,
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    quartet: Sequence[int],
) -> tuple[tuple[Path, ...], tuple[tuple[int, ...], ...], int, list[dict]]:
    """Return support-local rows for one quartet relation."""

    support = quartet_support_paths(pc_tree, quartet)
    allowed_types = quartet_allowed_types(D, quartet)
    support_domain_product = 1
    for path in support:
        support_domain_product *= len(domains[path])

    support_paths = tuple(support)
    support_domain_lists = [domains[path] for path in support_paths]
    support_rows: list[dict] = []
    for values in product(*support_domain_lists):
        assignment = dict(zip(support_paths, values))
        projected = _project_labels_order_from_support_assignment(pc_tree, quartet, assignment)
        type_order = quartet_type(projected)
        support_rows.append(
            {
                "assignment": assignment,
                "type": type_order,
                "accepted": type_order in allowed_types,
            }
        )

    return support_paths, allowed_types, support_domain_product, support_rows


def _scope_domain_product(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
) -> int:
    result = 1
    for path in scope:
        result *= len(domains[path])
    return result


def _all_scope_signatures(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
) -> set[NogoodSignature]:
    scope_tuple = tuple(scope)
    if not scope_tuple:
        return {()}
    return {
        tuple(zip(scope_tuple, values))
        for values in product(*(domains[path] for path in scope_tuple))
    }


def _signature_indices(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
    signature: NogoodSignature,
) -> tuple[int, ...]:
    choices = dict(signature)
    return tuple(domains[path].index(choices[path]) for path in scope)


def _relation_catalog_key(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
    accepted_signatures: set[NogoodSignature],
) -> tuple:
    domain_sizes = tuple(len(domains[path]) for path in scope)
    accepted_indices = tuple(
        sorted(_signature_indices(domains, scope, signature) for signature in accepted_signatures)
    )
    return (domain_sizes, accepted_indices)


def _relation_kind(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
    accepted_signatures: set[NogoodSignature],
) -> str:
    arity = len(scope)
    domain_sizes = [len(domains[path]) for path in scope]
    domain_product = _scope_domain_product(domains, scope)
    accepted_count = len(accepted_signatures)
    if accepted_count == domain_product:
        return "constant_accept"
    if accepted_count == 0:
        return "constant_reject"
    if arity == 1:
        return "unary_boolean" if domain_sizes[0] <= 2 else "unary_non_boolean"
    if arity == 2:
        return "binary_boolean_2sat" if all(size <= 2 for size in domain_sizes) else "binary_non_boolean_catalog"
    return "high_arity"


def _relation_summary(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scope: Sequence[Path],
    accepted_signatures: set[NogoodSignature],
) -> dict:
    scope_tuple = tuple(scope)
    domain_sizes = tuple(len(domains[path]) for path in scope_tuple)
    domain_product = _scope_domain_product(domains, scope_tuple)
    accepted_count = len(accepted_signatures)
    rejected_count = domain_product - accepted_count
    summary = {
        "scope": scope_tuple,
        "arity": len(scope_tuple),
        "domain_sizes": domain_sizes,
        "domain_product": domain_product,
        "accepted_signature_count": accepted_count,
        "rejected_signature_count": rejected_count,
        "density": accepted_count / domain_product if domain_product else 0.0,
        "relation_kind": _relation_kind(domains, scope_tuple, accepted_signatures),
        "is_boolean_scope": all(size <= 2 for size in domain_sizes),
        "is_2sat_candidate": len(scope_tuple) <= 2 and all(size <= 2 for size in domain_sizes),
    }
    if len(scope_tuple) == 2:
        summary["relation_catalog_key"] = _relation_catalog_key(domains, scope_tuple, accepted_signatures)
    return summary


def _accepted_signatures_for_scope(
    rows: Sequence[dict],
    scope: Sequence[Path],
) -> tuple[set[NogoodSignature], list[dict]]:
    values_by_signature: dict[NogoodSignature, bool] = {}
    conflicts = []
    for row in rows:
        signature = _nogood_signature(row["assignment"], scope)
        accepted = row["accepted"]
        previous = values_by_signature.get(signature)
        if previous is not None and previous != accepted:
            conflicts.append(
                {
                    "signature": signature,
                    "previous": previous,
                    "new": accepted,
                }
            )
        values_by_signature[signature] = accepted
    return {signature for signature, accepted in values_by_signature.items() if accepted}, conflicts


def _edge_key(a: Path, b: Path) -> tuple[Path, Path]:
    return tuple(sorted((a, b)))


def _fill_edge_count(graph: dict[Path, set[Path]], node: Path) -> int:
    neighbors = tuple(graph[node])
    missing = 0
    for idx, left in enumerate(neighbors):
        for right in neighbors[idx + 1 :]:
            if right not in graph[left]:
                missing += 1
    return missing


def _greedy_treewidth_upper_bound(graph: dict[Path, set[Path]], *, strategy: str) -> int:
    if strategy not in {"min_fill", "min_degree"}:
        raise ValueError("strategy must be min_fill or min_degree")
    working = {node: set(neighbors) for node, neighbors in graph.items()}
    width = 0
    while working:
        if strategy == "min_fill":
            node = min(
                working,
                key=lambda item: (_fill_edge_count(working, item), len(working[item]), item),
            )
        else:
            node = min(working, key=lambda item: (len(working[item]), _fill_edge_count(working, item), item))
        neighbors = tuple(working[node])
        width = max(width, len(neighbors))
        for idx, left in enumerate(neighbors):
            for right in neighbors[idx + 1 :]:
                working[left].add(right)
                working[right].add(left)
        for neighbor in neighbors:
            working[neighbor].discard(node)
        del working[node]
    return width


def _primal_graph_metrics(
    domains: dict[Path, tuple[tuple[int, ...], ...]],
    scopes: Sequence[Sequence[Path]],
) -> dict:
    active_vertices = {path for scope in scopes for path in scope}
    graph = {path: set() for path in active_vertices}
    edge_multiplicity: dict[tuple[Path, Path], int] = {}
    high_arity_scope_count = 0
    for scope in scopes:
        scope_tuple = tuple(scope)
        if len(scope_tuple) > 2:
            high_arity_scope_count += 1
        for left, right in combinations(scope_tuple, 2):
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)
            key = _edge_key(left, right)
            edge_multiplicity[key] = edge_multiplicity.get(key, 0) + 1
        for path in scope_tuple:
            graph.setdefault(path, set())

    unseen = set(graph)
    component_sizes = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        size = 0
        while stack:
            node = stack.pop()
            size += 1
            for neighbor in graph[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        component_sizes.append(size)

    min_fill_width = _greedy_treewidth_upper_bound(graph, strategy="min_fill") if graph else 0
    min_degree_width = _greedy_treewidth_upper_bound(graph, strategy="min_degree") if graph else 0
    edge_multiplicity_histogram: dict[int, int] = {}
    for count in edge_multiplicity.values():
        edge_multiplicity_histogram[count] = edge_multiplicity_histogram.get(count, 0) + 1
    component_size_histogram: dict[int, int] = {}
    for size in component_sizes:
        component_size_histogram[size] = component_size_histogram.get(size, 0) + 1

    return {
        "variable_count": len(domains),
        "active_variable_count": len(active_vertices),
        "edge_count": len(edge_multiplicity),
        "edge_multiplicity_histogram": dict(sorted(edge_multiplicity_histogram.items())),
        "max_edge_multiplicity": max(edge_multiplicity.values(), default=0),
        "max_degree": max((len(neighbors) for neighbors in graph.values()), default=0),
        "component_count": len(component_sizes),
        "component_size_histogram": dict(sorted(component_size_histogram.items())),
        "treewidth_upper_bound_min_fill": min_fill_width,
        "treewidth_upper_bound_min_degree": min_degree_width,
        "treewidth_upper_bound": min(min_fill_width, min_degree_width),
        "max_bag_size_upper_bound": min(min_fill_width, min_degree_width) + 1 if graph else 0,
        "high_arity_scope_count": high_arity_scope_count,
    }


def quartet_pc_scope_report(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    max_min_scope_search_size: int = 8,
) -> dict:
    """Measure local PC-tree variable scopes for exact quartet constraints.

    This is an experimental report, not a solver.  It compares the type induced
    by a support-local assignment with the type induced by complete frontiers
    sharing that support signature.  Mismatches indicate that
    ``quartet_support_paths`` has understated the dependencies.
    """

    n = validate_dissimilarity(D)
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if max_min_scope_search_size < 0:
        raise ValueError("max_min_scope_search_size must be non-negative")

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    all_quartets = list(combinations(range(n), 4))
    report = {
        "implemented": True,
        "method": "quartet_pc_scope_report",
        "encoding": encoding,
        "complete": True,
        "quartets": [],
        "first_projection_mismatch": None,
        "first_effective_type_scope_gt_2": None,
        "first_effective_acceptance_scope_gt_2": None,
        "counts": {
            "quartet_count": len(all_quartets),
            "quartets_profiled": 0,
            "full_assignments_seen": 0,
            "support_assignments_seen": 0,
            "support_size_histogram": {},
            "effective_type_scope_size_histogram": {},
            "effective_acceptance_scope_size_histogram": {},
            "max_support_size": 0,
            "max_effective_type_scope_size": 0,
            "max_effective_acceptance_scope_size": 0,
            "support_scope_gt_2_count": 0,
            "effective_type_scope_gt_2_count": 0,
            "effective_acceptance_scope_gt_2_count": 0,
            "boolean_effective_acceptance_scope_count": 0,
            "non_boolean_effective_acceptance_scope_count": 0,
            "two_sat_candidate_quartet_count": 0,
            "min_scope_search_skipped_count": 0,
            "projection_mismatch_count": 0,
            "allowed_type_total": 0,
            "realisable_type_total": 0,
            "accepted_signature_total": 0,
            "rejected_signature_total": 0,
            "max_support_domain_product": 0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    full_assignments = list(iter_local_assignments(encoding))
    report["counts"]["full_assignments_seen"] = len(full_assignments)

    truncated = False
    quartets_to_profile = all_quartets
    if limit is not None and len(all_quartets) > limit:
        quartets_to_profile = all_quartets[:limit]
        truncated = True

    domains = encoding["domains"]
    for quartet in quartets_to_profile:
        support_paths, allowed_types, support_domain_product, support_rows = _quartet_support_rows(
            D,
            pc_tree,
            domains,
            quartet,
        )
        support = support_paths

        report["counts"]["support_assignments_seen"] += len(support_rows)
        support_size = len(support)
        report["counts"]["support_size_histogram"][support_size] = (
            report["counts"]["support_size_histogram"].get(support_size, 0) + 1
        )
        report["counts"]["max_support_size"] = max(report["counts"]["max_support_size"], support_size)
        if support_size > 2:
            report["counts"]["support_scope_gt_2_count"] += 1
        report["counts"]["max_support_domain_product"] = max(
            report["counts"]["max_support_domain_product"], support_domain_product
        )

        effective_type_scope = None
        effective_acceptance_scope = None
        if support_size <= max_min_scope_search_size:
            effective_type_scope = _minimal_determining_scope(support_paths, support_rows, "type")
            effective_acceptance_scope = _minimal_determining_scope(support_paths, support_rows, "accepted")
            assert effective_type_scope is not None
            assert effective_acceptance_scope is not None
            type_size = len(effective_type_scope)
            acceptance_size = len(effective_acceptance_scope)
            report["counts"]["effective_type_scope_size_histogram"][type_size] = (
                report["counts"]["effective_type_scope_size_histogram"].get(type_size, 0) + 1
            )
            report["counts"]["effective_acceptance_scope_size_histogram"][acceptance_size] = (
                report["counts"]["effective_acceptance_scope_size_histogram"].get(acceptance_size, 0) + 1
            )
            report["counts"]["max_effective_type_scope_size"] = max(
                report["counts"]["max_effective_type_scope_size"], type_size
            )
            report["counts"]["max_effective_acceptance_scope_size"] = max(
                report["counts"]["max_effective_acceptance_scope_size"], acceptance_size
            )
            if type_size > 2:
                report["counts"]["effective_type_scope_gt_2_count"] += 1
                if report["first_effective_type_scope_gt_2"] is None:
                    report["first_effective_type_scope_gt_2"] = {
                        "quartet": quartet,
                        "support": support,
                        "effective_type_scope": effective_type_scope,
                    }
            if acceptance_size > 2:
                report["counts"]["effective_acceptance_scope_gt_2_count"] += 1
                if report["first_effective_acceptance_scope_gt_2"] is None:
                    report["first_effective_acceptance_scope_gt_2"] = {
                        "quartet": quartet,
                        "support": support,
                        "effective_acceptance_scope": effective_acceptance_scope,
                    }
            acceptance_domain_sizes = [len(domains[path]) for path in effective_acceptance_scope]
            if all(size <= 2 for size in acceptance_domain_sizes):
                report["counts"]["boolean_effective_acceptance_scope_count"] += 1
                if acceptance_size <= 2:
                    report["counts"]["two_sat_candidate_quartet_count"] += 1
            else:
                report["counts"]["non_boolean_effective_acceptance_scope_count"] += 1
        else:
            report["counts"]["min_scope_search_skipped_count"] += 1

        support_type_by_signature = {
            _nogood_signature(row["assignment"], support): row["type"] for row in support_rows
        }
        for full_assignment in full_assignments:
            full_frontier = frontier_from_assignment(pc_tree, full_assignment)
            full_projection = tuple(label for label in full_frontier if label in quartet)
            full_type = quartet_type(full_projection)
            signature = _nogood_signature(full_assignment, support)
            support_type = support_type_by_signature[signature]
            if full_type != support_type:
                report["counts"]["projection_mismatch_count"] += 1
                if report["first_projection_mismatch"] is None:
                    report["first_projection_mismatch"] = {
                        "quartet": quartet,
                        "support": support,
                        "signature": signature,
                        "support_type": support_type,
                        "full_type": full_type,
                        "full_frontier": full_frontier,
                    }

        realisable_types = {row["type"] for row in support_rows}
        accepted_signature_count = sum(1 for row in support_rows if row["accepted"])
        report["counts"]["allowed_type_total"] += len(allowed_types)
        report["counts"]["realisable_type_total"] += len(realisable_types)
        report["counts"]["accepted_signature_total"] += accepted_signature_count
        report["counts"]["rejected_signature_total"] += len(support_rows) - accepted_signature_count
        report["quartets"].append(
            {
                "quartet": quartet,
                "support": support,
                "support_size": support_size,
                "support_domain_product": support_domain_product,
                "allowed_types": allowed_types,
                "realisable_types": tuple(sorted(realisable_types)),
                "accepted_signature_count": accepted_signature_count,
                "rejected_signature_count": len(support_rows) - accepted_signature_count,
                "effective_type_scope": effective_type_scope,
                "effective_acceptance_scope": effective_acceptance_scope,
            }
        )

    report["counts"]["quartets_profiled"] = len(quartets_to_profile)
    report["counts"]["support_size_histogram"] = dict(sorted(report["counts"]["support_size_histogram"].items()))
    report["counts"]["effective_type_scope_size_histogram"] = dict(
        sorted(report["counts"]["effective_type_scope_size_histogram"].items())
    )
    report["counts"]["effective_acceptance_scope_size_histogram"] = dict(
        sorted(report["counts"]["effective_acceptance_scope_size_histogram"].items())
    )
    report["complete"] = not truncated
    return report


def quartet_effective_relation_report(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    max_min_scope_search_size: int = 8,
    validate: bool = True,
) -> dict:
    """Build an exact effective-relation report for quartet constraints.

    This is a diagnostic CSP object, not a solver.  It materializes the
    effective acceptance relation of each quartet, merges relations with the
    same scope by intersection, builds the primal graph of the merged scopes,
    and optionally validates the finite supported scaffold against the direct
    fixed-order cR predicate on complete local assignments.
    """

    n = validate_dissimilarity(D)
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if max_min_scope_search_size < 0:
        raise ValueError("max_min_scope_search_size must be non-negative")

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    all_quartets = list(combinations(range(n), 4))
    report = {
        "implemented": True,
        "method": "quartet_effective_relation_report",
        "encoding": encoding,
        "complete": True,
        "row_class": "unknown",
        "two_sat_candidate": False,
        "quartet_relations": [],
        "merged_relations": [],
        "first_scope_conflict": None,
        "first_validation_mismatch": None,
        "counts": {
            "quartet_count": len(all_quartets),
            "quartets_profiled": 0,
            "full_assignments_seen": 0,
            "support_assignments_seen": 0,
            "min_scope_search_skipped_count": 0,
            "scope_conflict_count": 0,
            "effective_acceptance_scope_size_histogram": {},
            "quartet_relation_kind_histogram": {},
            "merged_relation_kind_histogram": {},
            "quartet_relation_binary_boolean_count": 0,
            "quartet_relation_binary_non_boolean_count": 0,
            "quartet_relation_high_arity_count": 0,
            "quartet_relation_constant_accept_count": 0,
            "quartet_relation_constant_reject_count": 0,
            "quartet_relation_two_sat_candidate_count": 0,
            "merged_relation_scope_count": 0,
            "merged_relation_binary_boolean_count": 0,
            "merged_relation_binary_non_boolean_count": 0,
            "merged_relation_high_arity_count": 0,
            "merged_relation_constant_accept_count": 0,
            "merged_relation_constant_reject_count": 0,
            "merged_relation_two_sat_candidate_count": 0,
            "merged_relation_non_boolean_count": 0,
            "merged_relation_domain_product_total": 0,
            "merged_relation_accepted_signature_total": 0,
            "merged_relation_rejected_signature_total": 0,
            "max_relation_domain_product": 0,
            "binary_relation_catalog_key_count": 0,
            "validation_performed": False,
            "validation_assignments_seen": 0,
            "relation_accept_assignments": 0,
            "direct_cr_assignments": 0,
            "validation_mismatch_count": 0,
        },
        "primal_graph": {
            "variable_count": 0,
            "active_variable_count": 0,
            "edge_count": 0,
            "edge_multiplicity_histogram": {},
            "max_edge_multiplicity": 0,
            "max_degree": 0,
            "component_count": 0,
            "component_size_histogram": {},
            "treewidth_upper_bound_min_fill": 0,
            "treewidth_upper_bound_min_degree": 0,
            "treewidth_upper_bound": 0,
            "max_bag_size_upper_bound": 0,
            "high_arity_scope_count": 0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        report["row_class"] = "unsupported"
        return report

    domains = encoding["domains"]
    full_assignments = list(iter_local_assignments(encoding))
    report["counts"]["full_assignments_seen"] = len(full_assignments)

    truncated = False
    quartets_to_profile = all_quartets
    if limit is not None and len(all_quartets) > limit:
        quartets_to_profile = all_quartets[:limit]
        truncated = True

    merged: dict[tuple[Path, ...], dict] = {}
    binary_catalog_keys = set()
    for quartet in quartets_to_profile:
        support, allowed_types, support_domain_product, support_rows = _quartet_support_rows(
            D,
            pc_tree,
            domains,
            quartet,
        )
        report["counts"]["support_assignments_seen"] += len(support_rows)
        if len(support) > max_min_scope_search_size:
            report["counts"]["min_scope_search_skipped_count"] += 1
            continue

        effective_scope = _minimal_determining_scope(support, support_rows, "accepted")
        assert effective_scope is not None
        accepted_signatures, conflicts = _accepted_signatures_for_scope(support_rows, effective_scope)
        if conflicts:
            report["counts"]["scope_conflict_count"] += len(conflicts)
            if report["first_scope_conflict"] is None:
                report["first_scope_conflict"] = {
                    "quartet": quartet,
                    "support": support,
                    "effective_scope": effective_scope,
                    "conflict": conflicts[0],
                }

        summary = _relation_summary(domains, effective_scope, accepted_signatures)
        scope_size = len(effective_scope)
        report["counts"]["effective_acceptance_scope_size_histogram"][scope_size] = (
            report["counts"]["effective_acceptance_scope_size_histogram"].get(scope_size, 0) + 1
        )
        relation_kind = summary["relation_kind"]
        report["counts"]["quartet_relation_kind_histogram"][relation_kind] = (
            report["counts"]["quartet_relation_kind_histogram"].get(relation_kind, 0) + 1
        )
        if relation_kind == "binary_boolean_2sat":
            report["counts"]["quartet_relation_binary_boolean_count"] += 1
        elif relation_kind == "binary_non_boolean_catalog":
            report["counts"]["quartet_relation_binary_non_boolean_count"] += 1
        elif relation_kind == "high_arity":
            report["counts"]["quartet_relation_high_arity_count"] += 1
        elif relation_kind == "constant_accept":
            report["counts"]["quartet_relation_constant_accept_count"] += 1
        elif relation_kind == "constant_reject":
            report["counts"]["quartet_relation_constant_reject_count"] += 1
        if summary["is_2sat_candidate"]:
            report["counts"]["quartet_relation_two_sat_candidate_count"] += 1
        if "relation_catalog_key" in summary:
            binary_catalog_keys.add(repr(summary["relation_catalog_key"]))

        merged_entry = merged.setdefault(
            tuple(effective_scope),
            {
                "scope": tuple(effective_scope),
                "accepted_signatures": _all_scope_signatures(domains, effective_scope),
                "quartet_count": 0,
                "quartets": [],
            },
        )
        merged_entry["accepted_signatures"] &= accepted_signatures
        merged_entry["quartet_count"] += 1
        merged_entry["quartets"].append(tuple(quartet))

        relation_row = {
            "quartet": tuple(quartet),
            "support": support,
            "support_domain_product": support_domain_product,
            "allowed_types": allowed_types,
            **summary,
        }
        if len(accepted_signatures) <= 16:
            relation_row["accepted_signatures"] = tuple(sorted(accepted_signatures))
        report["quartet_relations"].append(relation_row)

    merged_summaries = []
    for scope, entry in sorted(merged.items()):
        accepted_signatures = entry["accepted_signatures"]
        summary = _relation_summary(domains, scope, accepted_signatures)
        relation_kind = summary["relation_kind"]
        report["counts"]["merged_relation_kind_histogram"][relation_kind] = (
            report["counts"]["merged_relation_kind_histogram"].get(relation_kind, 0) + 1
        )
        if relation_kind == "binary_boolean_2sat":
            report["counts"]["merged_relation_binary_boolean_count"] += 1
        elif relation_kind == "binary_non_boolean_catalog":
            report["counts"]["merged_relation_binary_non_boolean_count"] += 1
        elif relation_kind == "high_arity":
            report["counts"]["merged_relation_high_arity_count"] += 1
        elif relation_kind == "constant_accept":
            report["counts"]["merged_relation_constant_accept_count"] += 1
        elif relation_kind == "constant_reject":
            report["counts"]["merged_relation_constant_reject_count"] += 1
        if summary["is_2sat_candidate"]:
            report["counts"]["merged_relation_two_sat_candidate_count"] += 1
        if not summary["is_boolean_scope"]:
            report["counts"]["merged_relation_non_boolean_count"] += 1
        report["counts"]["merged_relation_domain_product_total"] += summary["domain_product"]
        report["counts"]["merged_relation_accepted_signature_total"] += summary[
            "accepted_signature_count"
        ]
        report["counts"]["merged_relation_rejected_signature_total"] += summary[
            "rejected_signature_count"
        ]
        report["counts"]["max_relation_domain_product"] = max(
            report["counts"]["max_relation_domain_product"],
            summary["domain_product"],
        )
        merged_row = {
            **summary,
            "quartet_count": entry["quartet_count"],
            "quartets": tuple(entry["quartets"]),
        }
        if len(accepted_signatures) <= 32:
            merged_row["accepted_signatures"] = tuple(sorted(accepted_signatures))
        report["merged_relations"].append(merged_row)
        merged_summaries.append((scope, accepted_signatures))

    report["counts"]["quartets_profiled"] = len(quartets_to_profile)
    report["counts"]["merged_relation_scope_count"] = len(merged_summaries)
    report["counts"]["binary_relation_catalog_key_count"] = len(binary_catalog_keys)
    report["counts"]["effective_acceptance_scope_size_histogram"] = dict(
        sorted(report["counts"]["effective_acceptance_scope_size_histogram"].items())
    )
    report["counts"]["quartet_relation_kind_histogram"] = dict(
        sorted(report["counts"]["quartet_relation_kind_histogram"].items())
    )
    report["counts"]["merged_relation_kind_histogram"] = dict(
        sorted(report["counts"]["merged_relation_kind_histogram"].items())
    )
    report["primal_graph"] = _primal_graph_metrics(
        domains,
        [scope for scope, _ in merged_summaries],
    )

    complete = (
        not truncated
        and report["counts"]["min_scope_search_skipped_count"] == 0
        and report["counts"]["scope_conflict_count"] == 0
    )
    report["complete"] = complete
    if validate and complete:
        report["counts"]["validation_performed"] = True
        for assignment in full_assignments:
            relation_accept = True
            for scope, accepted_signatures in merged_summaries:
                if _nogood_signature(assignment, scope) not in accepted_signatures:
                    relation_accept = False
                    break
            frontier = canonical_circular_order(frontier_from_assignment(pc_tree, assignment))
            direct_cr = is_precircular_order_cR(D, frontier)
            report["counts"]["validation_assignments_seen"] += 1
            if relation_accept:
                report["counts"]["relation_accept_assignments"] += 1
            if direct_cr:
                report["counts"]["direct_cr_assignments"] += 1
            if relation_accept != direct_cr:
                report["counts"]["validation_mismatch_count"] += 1
                if report["first_validation_mismatch"] is None:
                    report["first_validation_mismatch"] = {
                        "assignment": tuple(sorted(assignment.items())),
                        "frontier": frontier,
                        "relation_accept": relation_accept,
                        "direct_cr": direct_cr,
                    }

    if not complete:
        report["row_class"] = "incomplete"
    elif report["counts"]["validation_mismatch_count"]:
        report["row_class"] = "relation_validation_mismatch"
    elif report["counts"]["merged_relation_high_arity_count"]:
        report["row_class"] = "high_arity_relation"
    elif all(row["is_2sat_candidate"] for row in report["merged_relations"]):
        report["row_class"] = "two_sat_candidate"
        report["two_sat_candidate"] = True
    elif all(row["arity"] <= 2 for row in report["merged_relations"]):
        report["row_class"] = "non_boolean_relation_catalog"
    else:
        report["row_class"] = "mixed_relation_catalog"

    return report


def _side_of_witness_between_pair(order: Sequence[int], pair: tuple[int, int], witness: int) -> int:
    """Return which open arc between pair endpoints contains ``witness``."""

    a, b = pair
    position = {value: idx for idx, value in enumerate(order)}
    n = len(order)
    distance_ab = (position[b] - position[a]) % n
    distance_aw = (position[witness] - position[a]) % n
    return 0 if 0 < distance_aw < distance_ab else 1


def _witness_side_cache_key(
    pc_tree: PCNode,
    support_assignment: Assignment,
    pair: tuple[int, int],
    witness: int,
) -> tuple[tuple[int, int], int, NogoodSignature]:
    """Return the minimal support-local key determining one witness side."""

    triple_support = quartet_support_paths(pc_tree, (pair[0], pair[1], witness))
    return (pair, witness, _nogood_signature(support_assignment, triple_support))


def _component_side_cache_key(
    pc_tree: PCNode,
    support_assignment: Assignment,
    pair: tuple[int, int],
    component: tuple[int, ...],
) -> tuple[tuple[int, int], tuple[int, ...], NogoodSignature]:
    """Return the support-local key determining one component side mask."""

    support_paths = {
        path
        for witness in component
        for path in quartet_support_paths(pc_tree, (pair[0], pair[1], witness))
    }
    return (pair, component, _nogood_signature(support_assignment, tuple(sorted(support_paths))))


def _bad_witness_components_by_pair(
    support_atoms: Sequence[dict],
) -> dict[tuple[int, int], tuple[tuple[int, ...], ...]]:
    """Build fixed witness graph components for one support group."""

    adjacency_by_pair: dict[tuple[int, int], dict[int, set[int]]] = {}
    for atom_info in support_atoms:
        if "pair" not in atom_info or "bad_witnesses" not in atom_info:
            continue
        pair = tuple(atom_info["pair"])
        y, t = atom_info["bad_witnesses"]
        adjacency = adjacency_by_pair.setdefault(pair, {})
        adjacency.setdefault(y, set()).add(t)
        adjacency.setdefault(t, set()).add(y)

    components_by_pair: dict[tuple[int, int], tuple[tuple[int, ...], ...]] = {}
    for pair, adjacency in adjacency_by_pair.items():
        components: list[tuple[int, ...]] = []
        unseen = set(adjacency)
        while unseen:
            start = min(unseen)
            stack = [start]
            unseen.remove(start)
            component = []
            while stack:
                witness = stack.pop()
                component.append(witness)
                for neighbor in sorted(adjacency[witness]):
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(component)))
        components_by_pair[pair] = tuple(sorted(components))
    return components_by_pair


def _pair_side_split_outcome(
    pc_tree: PCNode,
    support_assignment: Assignment,
    components_by_pair: dict[tuple[int, int], tuple[tuple[int, ...], ...]],
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
) -> dict:
    """Classify a support assignment by witness-component side splits."""

    side_checks = 0
    side_cache_hits = 0
    side_cache_misses = 0
    component_checks = 0
    component_witness_checks = 0
    for pair, components in components_by_pair.items():
        witnesses = sorted({witness for component in components for witness in component})
        sides: dict[int, int] = {}
        for witness in witnesses:
            cache_key = _witness_side_cache_key(pc_tree, support_assignment, pair, witness)
            if cache_key in side_cache:
                sides[witness] = side_cache[cache_key]
                side_cache_hits += 1
            else:
                order = _project_labels_order_from_support_assignment(
                    pc_tree,
                    (pair[0], pair[1], witness),
                    support_assignment,
                )
                sides[witness] = _side_of_witness_between_pair(order, pair, witness)
                side_cache[cache_key] = sides[witness]
                side_cache_misses += 1
            side_checks += 1
        for component in components:
            component_checks += 1
            first_side = None
            for witness in component:
                component_witness_checks += 1
                if first_side is None:
                    first_side = sides[witness]
                elif sides[witness] != first_side:
                    return {
                        "hit": True,
                        "side_checks": side_checks,
                        "side_cache_hits": side_cache_hits,
                        "side_cache_misses": side_cache_misses,
                        "component_checks": component_checks,
                        "component_witness_checks": component_witness_checks,
                        "checks": side_checks + component_witness_checks,
                        "cached_checks": side_cache_misses + component_witness_checks,
                        "bitset_cached_checks": side_cache_misses + component_checks,
                        "pair": pair,
                        "component": component,
                    }

    return {
        "hit": False,
        "side_checks": side_checks,
        "side_cache_hits": side_cache_hits,
        "side_cache_misses": side_cache_misses,
        "component_checks": component_checks,
        "component_witness_checks": component_witness_checks,
        "checks": side_checks + component_witness_checks,
        "cached_checks": side_cache_misses + component_witness_checks,
        "bitset_cached_checks": side_cache_misses + component_checks,
        "pair": None,
        "component": None,
    }


def _pair_side_bitset_outcome(
    pc_tree: PCNode,
    support_assignment: Assignment,
    components_by_pair: dict[tuple[int, int], tuple[tuple[int, ...], ...]],
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
    component_cache: dict[tuple[tuple[int, int], tuple[int, ...], NogoodSignature], int],
) -> dict:
    """Classify a support assignment by cached component side masks."""

    component_checks = 0
    component_cache_hits = 0
    component_cache_misses = 0
    witness_visits = 0
    side_cache_hits = 0
    side_cache_misses = 0
    for pair, components in components_by_pair.items():
        for component in components:
            component_checks += 1
            if len(component) < 2:
                continue
            component_key = _component_side_cache_key(pc_tree, support_assignment, pair, component)
            if component_key in component_cache:
                mask = component_cache[component_key]
                component_cache_hits += 1
            else:
                component_cache_misses += 1
                mask = 0
                for witness in component:
                    witness_visits += 1
                    side_key = _witness_side_cache_key(pc_tree, support_assignment, pair, witness)
                    if side_key in side_cache:
                        side = side_cache[side_key]
                        side_cache_hits += 1
                    else:
                        order = _project_labels_order_from_support_assignment(
                            pc_tree,
                            (pair[0], pair[1], witness),
                            support_assignment,
                        )
                        side = _side_of_witness_between_pair(order, pair, witness)
                        side_cache[side_key] = side
                        side_cache_misses += 1
                    mask |= 1 << side
                    if mask == 0b11:
                        break
                component_cache[component_key] = mask
            if mask == 0b11:
                return {
                    "hit": True,
                    "component_checks": component_checks,
                    "component_cache_hits": component_cache_hits,
                    "component_cache_misses": component_cache_misses,
                    "witness_visits": witness_visits,
                    "side_cache_hits": side_cache_hits,
                    "side_cache_misses": side_cache_misses,
                    "checks": component_checks + witness_visits,
                    "projection_checks": component_checks + side_cache_misses,
                    "pair": pair,
                    "component": component,
                }

    return {
        "hit": False,
        "component_checks": component_checks,
        "component_cache_hits": component_cache_hits,
        "component_cache_misses": component_cache_misses,
        "witness_visits": witness_visits,
        "side_cache_hits": side_cache_hits,
        "side_cache_misses": side_cache_misses,
        "checks": component_checks + witness_visits,
        "projection_checks": component_checks + side_cache_misses,
        "pair": None,
        "component": None,
    }


def _component_mask_state(
    pc_tree: PCNode,
    support_assignment: Assignment,
    components_by_pair: dict[tuple[int, int], tuple[tuple[int, ...], ...]],
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
) -> dict:
    """Return the full component-mask state for one support assignment."""

    entries = []
    side_cache_hits = 0
    side_cache_misses = 0
    witness_visits = 0
    component_masks = 0
    hit = False
    for pair in sorted(components_by_pair):
        for component in components_by_pair[pair]:
            mask = 0
            component_masks += 1
            for witness in component:
                witness_visits += 1
                side_key = _witness_side_cache_key(pc_tree, support_assignment, pair, witness)
                if side_key in side_cache:
                    side = side_cache[side_key]
                    side_cache_hits += 1
                else:
                    order = _project_labels_order_from_support_assignment(
                        pc_tree,
                        (pair[0], pair[1], witness),
                        support_assignment,
                    )
                    side = _side_of_witness_between_pair(order, pair, witness)
                    side_cache[side_key] = side
                    side_cache_misses += 1
                mask |= 1 << side
            if mask == 0b11:
                hit = True
            entries.append((pair, component, mask))

    return {
        "state": tuple(entries),
        "hit": hit,
        "component_masks": component_masks,
        "witness_visits": witness_visits,
        "side_cache_hits": side_cache_hits,
        "side_cache_misses": side_cache_misses,
    }


def _component_mask_state_quotients(state: tuple) -> dict[str, tuple]:
    """Return diagnostic quotients of a full component-mask state."""

    pair_masks: dict[tuple[int, int], list[int]] = {}
    hit_components = []
    hit_pairs = set()
    for pair, component, mask in state:
        pair_masks.setdefault(pair, []).append(mask)
        if mask == 0b11:
            hit_components.append((pair, component))
            hit_pairs.add(pair)

    has_hit = bool(hit_components)
    return {
        "full": state,
        "mask_multiset": tuple(sorted(mask for _, _, mask in state)),
        "pair_mask_multiset": tuple(
            (pair, tuple(sorted(masks))) for pair, masks in sorted(pair_masks.items())
        ),
        "hit_components": tuple(sorted(hit_components)),
        "hit_pairs": tuple(sorted(hit_pairs)),
        "decision_only": (has_hit,),
        "side_blind_schema": tuple((pair, component) for pair, component, _ in state),
    }


def _support_atom_scan_hit(
    pc_tree: PCNode,
    support_assignment: Assignment,
    support_atoms: Sequence[dict],
) -> bool:
    for atom_info in support_atoms:
        atom = tuple(atom_info["atom"])
        order = canonical_circular_order(
            _project_atom_order_from_support_assignment(pc_tree, atom, support_assignment)
        )
        if _cyclic_atom_occurs(order, atom):
            return True
    return False


def _domain_product_size(encoding: dict, support: Sequence[Path]) -> int:
    result = 1
    for path in support:
        result *= len(encoding["domains"][path])
    return result


def _compile_nogoods_by_support_products(
    D,
    pc_tree: PCNode,
    *,
    atoms: list[dict],
    method: str,
    max_p_degree: int,
    limit: Optional[int],
) -> dict:
    """Compile nogoods from support products, deduplicated by pruning signature.

    The representative ``atom`` stored on a nogood is diagnostic only.  Global
    circular canonicalization can change which oriented atom labels a signature,
    while the signature itself is the pruning object used by the CSP search.
    """

    validate_dissimilarity(D)
    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": method,
        "encoding": encoding,
        "complete": True,
        "atoms": atoms,
        "nogoods": [],
        "counts": {
            "support_assignments_seen": 0,
            "atom_hits": 0,
            "unique_nogoods": 0,
            "atoms_with_nogoods": 0,
            "max_support_size": 0,
            "support_size_histogram": {},
            "support_product_total": 0,
            "max_support_product": 0,
            "full_assignment_space": 0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    full_assignment_space = 1
    for variable in encoding["variables"]:
        full_assignment_space *= len(encoding["domains"][variable["path"]])
    report["counts"]["full_assignment_space"] = full_assignment_space

    seen: dict[NogoodSignature, dict] = {}
    atoms_with_hits: set[tuple[int, ...]] = set()
    pairs_with_hits: set[tuple[int, int]] = set()
    truncated = False
    support_by_atom = {
        tuple(atom_info["atom"]): quartet_support_paths(pc_tree, atom_info["atom"])
        for atom_info in atoms
    }
    for atom_info in atoms:
        atom = tuple(atom_info["atom"])
        support = support_by_atom[atom]
        support_product = _domain_product_size(encoding, support)
        report["counts"]["support_product_total"] += support_product
        report["counts"]["max_support_product"] = max(
            report["counts"]["max_support_product"],
            support_product,
        )
        domain_lists = [encoding["domains"][path] for path in support]
        for choices in product(*domain_lists):
            if limit is not None and report["counts"]["support_assignments_seen"] >= limit:
                truncated = True
                break
            report["counts"]["support_assignments_seen"] += 1
            support_assignment = dict(zip(support, choices))
            order = canonical_circular_order(
                _project_atom_order_from_support_assignment(pc_tree, atom, support_assignment)
            )
            if not _cyclic_atom_occurs(order, atom):
                continue
            signature = _nogood_signature(support_assignment, support)
            report["counts"]["atom_hits"] += 1
            atoms_with_hits.add(atom)
            if "pair" in atom_info:
                pairs_with_hits.add(atom_info["pair"])
            if signature in seen:
                continue
            nogood = {
                "atom": atom,
                "support": support,
                "signature": signature,
                "violation": atom_info,
            }
            if "pair" in atom_info:
                nogood["pair"] = atom_info["pair"]
            if "bad_witnesses" in atom_info:
                nogood["bad_witnesses"] = atom_info["bad_witnesses"]
            seen[signature] = nogood
        if truncated:
            break

    nogoods = list(seen.values())
    histogram: dict[int, int] = {}
    for nogood in nogoods:
        size = len(nogood["support"])
        histogram[size] = histogram.get(size, 0) + 1

    report["nogoods"] = nogoods
    report["complete"] = not truncated
    report["counts"]["unique_nogoods"] = len(nogoods)
    report["counts"]["atoms_with_nogoods"] = len(atoms_with_hits)
    report["counts"]["support_size_histogram"] = dict(sorted(histogram.items()))
    report["counts"]["max_support_size"] = max(histogram, default=0)
    if any("pair" in nogood for nogood in nogoods):
        report["counts"]["pairs_with_nogoods"] = len(pairs_with_hits)
    return report


def _compile_nogoods_by_grouped_supports(
    D,
    pc_tree: PCNode,
    *,
    atoms: list[dict],
    method: str,
    max_p_degree: int,
    limit: Optional[int],
    stop_after_first_hit: bool = False,
) -> dict:
    """Compile nogoods by enumerating each distinct support product once."""

    validate_dissimilarity(D)
    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": method,
        "encoding": encoding,
        "complete": True,
        "atoms": atoms,
        "nogoods": [],
        "counts": {
            "grouped_support_assignments_seen": 0,
            "atom_checks": 0,
            "atom_hits": 0,
            "unique_nogoods": 0,
            "atoms_with_nogoods": 0,
            "support_group_count": 0,
            "max_support_size": 0,
            "support_size_histogram": {},
            "grouped_support_product_total": 0,
            "support_product_total_if_ungrouped": 0,
            "grouped_vs_ungrouped_support_ratio": 0.0,
            "max_support_product": 0,
            "max_atoms_per_support": 0,
            "support_group_size_histogram": {},
            "full_assignment_space": 0,
            "effective_signature_count": 0,
            "stopped_after_first_hit": stop_after_first_hit,
            "atom_checks_if_exhaustive": 0,
            "atom_checks_if_exhaustive_seen": 0,
            "atom_checks_saved_by_first_hit": 0,
            "first_hit_assignments": 0,
            "first_hit_no_hit_assignments": 0,
            "first_hit_position_sum": 0,
            "first_hit_average_position": 0.0,
            "first_hit_max_position": 0,
            "first_hit_position_histogram": {},
            "first_hit_checks_spent_on_no_hit": 0,
            "first_hit_checks_saved_on_hits": 0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    full_assignment_space = 1
    for variable in encoding["variables"]:
        full_assignment_space *= len(encoding["domains"][variable["path"]])
    report["counts"]["full_assignment_space"] = full_assignment_space

    atoms_by_support: dict[tuple[Path, ...], list[dict]] = {}
    for atom_info in atoms:
        support = quartet_support_paths(pc_tree, atom_info["atom"])
        atoms_by_support.setdefault(support, []).append(atom_info)
    report["counts"]["support_group_count"] = len(atoms_by_support)
    group_size_histogram: dict[int, int] = {}
    for support_atoms in atoms_by_support.values():
        group_size = len(support_atoms)
        group_size_histogram[group_size] = group_size_histogram.get(group_size, 0) + 1
        report["counts"]["max_atoms_per_support"] = max(
            report["counts"]["max_atoms_per_support"],
            group_size,
        )
    report["counts"]["support_group_size_histogram"] = dict(sorted(group_size_histogram.items()))

    seen: dict[NogoodSignature, dict] = {}
    atoms_with_hits: set[tuple[int, ...]] = set()
    pairs_with_hits: set[tuple[int, int]] = set()
    first_hit_position_histogram: dict[int, int] = {}
    truncated = False
    for support, support_atoms in atoms_by_support.items():
        support_product = _domain_product_size(encoding, support)
        report["counts"]["grouped_support_product_total"] += support_product
        report["counts"]["support_product_total_if_ungrouped"] += support_product * len(support_atoms)
        report["counts"]["max_support_product"] = max(
            report["counts"]["max_support_product"],
            support_product,
        )
        domain_lists = [encoding["domains"][path] for path in support]
        for choices in product(*domain_lists):
            if limit is not None and report["counts"]["grouped_support_assignments_seen"] >= limit:
                truncated = True
                break
            report["counts"]["grouped_support_assignments_seen"] += 1
            support_assignment = dict(zip(support, choices))
            signature = _nogood_signature(support_assignment, support)
            hit_position = 0
            group_size = len(support_atoms)
            if stop_after_first_hit:
                report["counts"]["atom_checks_if_exhaustive_seen"] += group_size
            for atom_position, atom_info in enumerate(support_atoms, start=1):
                atom = tuple(atom_info["atom"])
                report["counts"]["atom_checks"] += 1
                order = canonical_circular_order(
                    _project_atom_order_from_support_assignment(pc_tree, atom, support_assignment)
                )
                if not _cyclic_atom_occurs(order, atom):
                    continue
                if hit_position == 0:
                    hit_position = atom_position
                report["counts"]["atom_hits"] += 1
                atoms_with_hits.add(atom)
                if "pair" in atom_info:
                    pairs_with_hits.add(atom_info["pair"])
                if signature in seen:
                    if stop_after_first_hit:
                        break
                    continue
                nogood = {
                    "atom": atom,
                    "support": support,
                    "signature": signature,
                    "violation": atom_info,
                }
                if "pair" in atom_info:
                    nogood["pair"] = atom_info["pair"]
                if "bad_witnesses" in atom_info:
                    nogood["bad_witnesses"] = atom_info["bad_witnesses"]
                seen[signature] = nogood
                if stop_after_first_hit:
                    break
            if stop_after_first_hit:
                if hit_position:
                    report["counts"]["first_hit_assignments"] += 1
                    report["counts"]["first_hit_position_sum"] += hit_position
                    report["counts"]["first_hit_max_position"] = max(
                        report["counts"]["first_hit_max_position"],
                        hit_position,
                    )
                    first_hit_position_histogram[hit_position] = (
                        first_hit_position_histogram.get(hit_position, 0) + 1
                    )
                    report["counts"]["first_hit_checks_saved_on_hits"] += group_size - hit_position
                else:
                    report["counts"]["first_hit_no_hit_assignments"] += 1
                    report["counts"]["first_hit_checks_spent_on_no_hit"] += group_size
        if truncated:
            break

    nogoods = list(seen.values())
    histogram: dict[int, int] = {}
    for nogood in nogoods:
        size = len(nogood["support"])
        histogram[size] = histogram.get(size, 0) + 1

    report["nogoods"] = nogoods
    report["complete"] = not truncated
    report["counts"]["unique_nogoods"] = len(nogoods)
    report["counts"]["effective_signature_count"] = len(nogoods)
    report["counts"]["atoms_with_nogoods"] = len(atoms_with_hits)
    report["counts"]["support_size_histogram"] = dict(sorted(histogram.items()))
    report["counts"]["max_support_size"] = max(histogram, default=0)
    ungrouped_total = report["counts"]["support_product_total_if_ungrouped"]
    report["counts"]["atom_checks_if_exhaustive"] = ungrouped_total
    baseline_checks_seen = (
        report["counts"]["atom_checks_if_exhaustive_seen"]
        if stop_after_first_hit
        else ungrouped_total
    )
    report["counts"]["atom_checks_saved_by_first_hit"] = baseline_checks_seen - report["counts"]["atom_checks"]
    report["counts"]["first_hit_position_histogram"] = dict(sorted(first_hit_position_histogram.items()))
    hit_assignments = report["counts"]["first_hit_assignments"]
    report["counts"]["first_hit_average_position"] = (
        report["counts"]["first_hit_position_sum"] / hit_assignments
        if hit_assignments
        else 0.0
    )
    report["counts"]["grouped_vs_ungrouped_support_ratio"] = (
        report["counts"]["grouped_support_product_total"] / ungrouped_total
        if ungrouped_total
        else 0.0
    )
    if any("pair" in nogood for nogood in nogoods):
        report["counts"]["pairs_with_nogoods"] = len(pairs_with_hits)
    return report


def _profile_single_support_group(
    pc_tree: PCNode,
    encoding: dict,
    support: tuple[Path, ...],
    support_atoms: list[dict],
    *,
    limit: Optional[int],
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
    bitset_side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
    component_side_cache: dict[tuple[tuple[int, int], tuple[int, ...], NogoodSignature], int],
    mask_state_side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int],
) -> dict:
    """Profile hit/no-hit outcomes for one support group.

    This is diagnostic, not a solver: it still tests atoms sequentially.  The
    extra value is to measure whether no-hit assignments have a simple
    one-coordinate explanation.
    """

    domain_lists = [encoding["domains"][path] for path in support]
    group_size = len(support_atoms)
    support_product = _domain_product_size(encoding, support)
    components_by_pair = _bad_witness_components_by_pair(support_atoms)
    outcomes: list[tuple[NogoodSignature, bool, int]] = []
    slice_stats: dict[tuple[Path, tuple[int, ...]], dict] = {}
    hit_signatures: set[NogoodSignature] = set()
    no_hit_signatures: set[NogoodSignature] = set()
    hit_position_histogram: dict[int, int] = {}
    first_hit_position_sum = 0
    classification_atom_checks = 0
    pair_side_split_hit_assignments = 0
    pair_side_split_no_hit_assignments = 0
    pair_side_split_side_checks = 0
    pair_side_split_side_cache_hits = 0
    pair_side_split_side_cache_misses = 0
    pair_side_split_component_checks = 0
    pair_side_split_component_witness_checks = 0
    pair_side_split_checks = 0
    pair_side_split_cached_checks = 0
    pair_side_split_bitset_cached_checks = 0
    pair_side_split_mismatches = 0
    first_pair_side_split_mismatch = None
    pair_side_split_bitset_hit_assignments = 0
    pair_side_split_bitset_no_hit_assignments = 0
    pair_side_split_bitset_checks = 0
    pair_side_split_bitset_component_checks = 0
    pair_side_split_bitset_component_cache_hits = 0
    pair_side_split_bitset_component_cache_misses = 0
    pair_side_split_bitset_witness_visits = 0
    pair_side_split_bitset_side_cache_hits = 0
    pair_side_split_bitset_side_cache_misses = 0
    pair_side_split_bitset_projection_checks = 0
    pair_side_split_bitset_mismatches = 0
    first_pair_side_split_bitset_mismatch = None
    component_mask_state_counts: dict[tuple, int] = {}
    component_mask_state_hit_values: dict[tuple, bool] = {}
    component_mask_state_mixed_states: set[tuple] = set()
    component_mask_state_mismatches = 0
    first_component_mask_state_mismatch = None
    component_mask_state_component_masks = 0
    component_mask_state_witness_visits = 0
    component_mask_state_side_cache_hits = 0
    component_mask_state_side_cache_misses = 0
    component_mask_quotient_counts: dict[str, dict[tuple, int]] = {}
    component_mask_quotient_hit_values: dict[str, dict[tuple, bool]] = {}
    component_mask_quotient_mixed: dict[str, set[tuple]] = {}
    truncated = False

    for choices in product(*domain_lists):
        if limit is not None and len(outcomes) >= limit:
            truncated = True
            break
        support_assignment = dict(zip(support, choices))
        signature = _nogood_signature(support_assignment, support)
        hit_position = 0
        checks = 0
        for atom_position, atom_info in enumerate(support_atoms, start=1):
            checks += 1
            atom = tuple(atom_info["atom"])
            order = canonical_circular_order(
                _project_atom_order_from_support_assignment(pc_tree, atom, support_assignment)
            )
            if _cyclic_atom_occurs(order, atom):
                hit_position = atom_position
                break

        hit = hit_position != 0
        classification_atom_checks += checks
        outcomes.append((signature, hit, hit_position))
        if hit:
            hit_signatures.add(signature)
            first_hit_position_sum += hit_position
            hit_position_histogram[hit_position] = hit_position_histogram.get(hit_position, 0) + 1
        else:
            no_hit_signatures.add(signature)

        pair_side_split = _pair_side_split_outcome(
            pc_tree,
            support_assignment,
            components_by_pair,
            side_cache,
        )
        pair_side_split_checks += pair_side_split["checks"]
        pair_side_split_side_checks += pair_side_split["side_checks"]
        pair_side_split_side_cache_hits += pair_side_split["side_cache_hits"]
        pair_side_split_side_cache_misses += pair_side_split["side_cache_misses"]
        pair_side_split_component_checks += pair_side_split["component_checks"]
        pair_side_split_component_witness_checks += pair_side_split["component_witness_checks"]
        pair_side_split_cached_checks += pair_side_split["cached_checks"]
        pair_side_split_bitset_cached_checks += pair_side_split["bitset_cached_checks"]
        if pair_side_split["hit"]:
            pair_side_split_hit_assignments += 1
        else:
            pair_side_split_no_hit_assignments += 1
        if pair_side_split["hit"] != hit:
            pair_side_split_mismatches += 1
            if first_pair_side_split_mismatch is None:
                first_pair_side_split_mismatch = {
                    "signature": signature,
                    "atom_scan_hit": hit,
                    "pair_side_split_hit": pair_side_split["hit"],
                    "pair": pair_side_split["pair"],
                    "component": pair_side_split["component"],
                }

        pair_side_bitset = _pair_side_bitset_outcome(
            pc_tree,
            support_assignment,
            components_by_pair,
            bitset_side_cache,
            component_side_cache,
        )
        pair_side_split_bitset_checks += pair_side_bitset["checks"]
        pair_side_split_bitset_component_checks += pair_side_bitset["component_checks"]
        pair_side_split_bitset_component_cache_hits += pair_side_bitset["component_cache_hits"]
        pair_side_split_bitset_component_cache_misses += pair_side_bitset[
            "component_cache_misses"
        ]
        pair_side_split_bitset_witness_visits += pair_side_bitset["witness_visits"]
        pair_side_split_bitset_side_cache_hits += pair_side_bitset["side_cache_hits"]
        pair_side_split_bitset_side_cache_misses += pair_side_bitset["side_cache_misses"]
        pair_side_split_bitset_projection_checks += pair_side_bitset["projection_checks"]
        if pair_side_bitset["hit"]:
            pair_side_split_bitset_hit_assignments += 1
        else:
            pair_side_split_bitset_no_hit_assignments += 1
        if pair_side_bitset["hit"] != hit:
            pair_side_split_bitset_mismatches += 1
            if first_pair_side_split_bitset_mismatch is None:
                first_pair_side_split_bitset_mismatch = {
                    "signature": signature,
                    "atom_scan_hit": hit,
                    "pair_side_bitset_hit": pair_side_bitset["hit"],
                    "pair": pair_side_bitset["pair"],
                    "component": pair_side_bitset["component"],
                }

        mask_state = _component_mask_state(
            pc_tree,
            support_assignment,
            components_by_pair,
            mask_state_side_cache,
        )
        state = mask_state["state"]
        component_mask_state_counts[state] = component_mask_state_counts.get(state, 0) + 1
        component_mask_state_component_masks += mask_state["component_masks"]
        component_mask_state_witness_visits += mask_state["witness_visits"]
        component_mask_state_side_cache_hits += mask_state["side_cache_hits"]
        component_mask_state_side_cache_misses += mask_state["side_cache_misses"]
        previous_hit = component_mask_state_hit_values.setdefault(state, mask_state["hit"])
        if previous_hit != mask_state["hit"]:
            component_mask_state_mixed_states.add(state)
        if mask_state["hit"] != hit:
            component_mask_state_mismatches += 1
            if first_component_mask_state_mismatch is None:
                first_component_mask_state_mismatch = {
                    "signature": signature,
                    "atom_scan_hit": hit,
                    "component_mask_state_hit": mask_state["hit"],
                }
        for quotient_name, quotient_state in _component_mask_state_quotients(state).items():
            quotient_counts = component_mask_quotient_counts.setdefault(quotient_name, {})
            quotient_counts[quotient_state] = quotient_counts.get(quotient_state, 0) + 1
            quotient_hit_values = component_mask_quotient_hit_values.setdefault(quotient_name, {})
            previous_quotient_hit = quotient_hit_values.setdefault(quotient_state, mask_state["hit"])
            if previous_quotient_hit != mask_state["hit"]:
                component_mask_quotient_mixed.setdefault(quotient_name, set()).add(quotient_state)

        for path, choice in signature:
            key = (path, choice)
            stats = slice_stats.setdefault(
                key,
                {
                    "seen": 0,
                    "hits": 0,
                    "signatures": set(),
                },
            )
            stats["seen"] += 1
            if hit:
                stats["hits"] += 1
            stats["signatures"].add(signature)

    pure_hit_slices: list[dict] = []
    pure_no_hit_slices: list[dict] = []
    unary_hit_covered: set[NogoodSignature] = set()
    unary_no_hit_covered: set[NogoodSignature] = set()
    for (path, choice), stats in slice_stats.items():
        if stats["seen"] == 0:
            continue
        if stats["hits"] == stats["seen"]:
            pure_hit_slices.append(
                {
                    "path": path,
                    "choice": choice,
                    "assignments": stats["seen"],
                }
            )
            unary_hit_covered.update(stats["signatures"])
        elif stats["hits"] == 0:
            pure_no_hit_slices.append(
                {
                    "path": path,
                    "choice": choice,
                    "assignments": stats["seen"],
                }
            )
            unary_no_hit_covered.update(stats["signatures"])

    hit_count = len(hit_signatures)
    no_hit_count = len(no_hit_signatures)
    unary_hit_certified = len(unary_hit_covered & hit_signatures)
    unary_no_hit_certified = len(unary_no_hit_covered & no_hit_signatures)
    assignments_seen = len(outcomes)
    no_hit_exhaustive_atom_checks = no_hit_count * group_size
    exhaustive_atom_checks_seen = assignments_seen * group_size
    component_mask_state_count = len(component_mask_state_counts)
    component_mask_state_hit_count = sum(component_mask_state_hit_values.values())
    component_mask_state_no_hit_count = component_mask_state_count - component_mask_state_hit_count
    component_mask_state_max_bucket = max(component_mask_state_counts.values(), default=0)
    component_mask_quotients = {}
    for quotient_name, quotient_counts in sorted(component_mask_quotient_counts.items()):
        quotient_state_count = len(quotient_counts)
        quotient_hit_values = component_mask_quotient_hit_values[quotient_name]
        quotient_hit_count = sum(quotient_hit_values.values())
        component_mask_quotients[quotient_name] = {
            "state_count": quotient_state_count,
            "hit_state_count": quotient_hit_count,
            "no_hit_state_count": quotient_state_count - quotient_hit_count,
            "mixed_count": len(component_mask_quotient_mixed.get(quotient_name, set())),
            "max_bucket_size": max(quotient_counts.values(), default=0),
            "ratio": quotient_state_count / assignments_seen if assignments_seen else 0.0,
            "average_bucket_size": (
                assignments_seen / quotient_state_count if quotient_state_count else 0.0
            ),
        }

    return {
        "support": support,
        "support_size": len(support),
        "domain_sizes": tuple(len(encoding["domains"][path]) for path in support),
        "group_size": group_size,
        "support_product": support_product,
        "assignments_seen": assignments_seen,
        "hit_assignments": hit_count,
        "no_hit_assignments": no_hit_count,
        "hit_ratio": hit_count / assignments_seen if assignments_seen else 0.0,
        "no_hit_ratio": no_hit_count / assignments_seen if assignments_seen else 0.0,
        "classification_atom_checks": classification_atom_checks,
        "exhaustive_atom_checks_seen": exhaustive_atom_checks_seen,
        "no_hit_exhaustive_atom_checks": no_hit_exhaustive_atom_checks,
        "first_hit_position_sum": first_hit_position_sum,
        "first_hit_position_histogram": dict(sorted(hit_position_histogram.items())),
        "pair_side_split_hit_assignments": pair_side_split_hit_assignments,
        "pair_side_split_no_hit_assignments": pair_side_split_no_hit_assignments,
        "pair_side_split_checks": pair_side_split_checks,
        "pair_side_split_side_checks": pair_side_split_side_checks,
        "pair_side_split_side_cache_hits": pair_side_split_side_cache_hits,
        "pair_side_split_side_cache_misses": pair_side_split_side_cache_misses,
        "pair_side_split_component_checks": pair_side_split_component_checks,
        "pair_side_split_component_witness_checks": pair_side_split_component_witness_checks,
        "pair_side_split_cached_checks": pair_side_split_cached_checks,
        "pair_side_split_bitset_cached_checks": pair_side_split_bitset_cached_checks,
        "pair_side_split_cached_work_ratio": (
            pair_side_split_cached_checks / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "pair_side_split_bitset_cached_work_ratio": (
            pair_side_split_bitset_cached_checks / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "pair_side_split_bitset_hit_assignments": pair_side_split_bitset_hit_assignments,
        "pair_side_split_bitset_no_hit_assignments": pair_side_split_bitset_no_hit_assignments,
        "pair_side_split_bitset_checks": pair_side_split_bitset_checks,
        "pair_side_split_bitset_component_checks": pair_side_split_bitset_component_checks,
        "pair_side_split_bitset_component_cache_hits": pair_side_split_bitset_component_cache_hits,
        "pair_side_split_bitset_component_cache_misses": (
            pair_side_split_bitset_component_cache_misses
        ),
        "pair_side_split_bitset_witness_visits": pair_side_split_bitset_witness_visits,
        "pair_side_split_bitset_side_cache_hits": pair_side_split_bitset_side_cache_hits,
        "pair_side_split_bitset_side_cache_misses": pair_side_split_bitset_side_cache_misses,
        "pair_side_split_bitset_projection_checks": pair_side_split_bitset_projection_checks,
        "pair_side_split_bitset_work_ratio": (
            pair_side_split_bitset_checks / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "pair_side_split_bitset_projection_work_ratio": (
            pair_side_split_bitset_projection_checks / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "pair_side_split_bitset_mismatches": pair_side_split_bitset_mismatches,
        "first_pair_side_split_bitset_mismatch": first_pair_side_split_bitset_mismatch,
        "component_mask_state_count": component_mask_state_count,
        "component_mask_state_hit_count": component_mask_state_hit_count,
        "component_mask_state_no_hit_count": component_mask_state_no_hit_count,
        "component_mask_state_mixed_count": len(component_mask_state_mixed_states),
        "component_mask_state_mismatches": component_mask_state_mismatches,
        "first_component_mask_state_mismatch": first_component_mask_state_mismatch,
        "component_mask_state_max_bucket_size": component_mask_state_max_bucket,
        "component_mask_state_ratio": (
            component_mask_state_count / assignments_seen if assignments_seen else 0.0
        ),
        "component_mask_state_average_bucket_size": (
            assignments_seen / component_mask_state_count if component_mask_state_count else 0.0
        ),
        "component_mask_state_component_masks": component_mask_state_component_masks,
        "component_mask_state_witness_visits": component_mask_state_witness_visits,
        "component_mask_state_side_cache_hits": component_mask_state_side_cache_hits,
        "component_mask_state_side_cache_misses": component_mask_state_side_cache_misses,
        "component_mask_state_work_ratio": (
            (component_mask_state_component_masks + component_mask_state_witness_visits)
            / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "component_mask_state_projection_work_ratio": (
            (component_mask_state_component_masks + component_mask_state_side_cache_misses)
            / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "component_mask_quotients": component_mask_quotients,
        "pair_side_split_work_ratio": (
            pair_side_split_checks / classification_atom_checks
            if classification_atom_checks
            else 0.0
        ),
        "pair_side_split_mismatches": pair_side_split_mismatches,
        "first_pair_side_split_mismatch": first_pair_side_split_mismatch,
        "pure_hit_slice_count": len(pure_hit_slices),
        "pure_no_hit_slice_count": len(pure_no_hit_slices),
        "unary_hit_certified_assignments": unary_hit_certified,
        "unary_no_hit_certified_assignments": unary_no_hit_certified,
        "ambiguous_hit_assignments": hit_count - unary_hit_certified,
        "ambiguous_no_hit_assignments": no_hit_count - unary_no_hit_certified,
        "unary_hit_coverage_ratio": unary_hit_certified / hit_count if hit_count else 0.0,
        "unary_no_hit_coverage_ratio": (
            unary_no_hit_certified / no_hit_count if no_hit_count else 0.0
        ),
        "pure_hit_slices": sorted(
            pure_hit_slices,
            key=lambda item: (item["path"], item["choice"]),
        ),
        "pure_no_hit_slices": sorted(
            pure_no_hit_slices,
            key=lambda item: (item["path"], item["choice"]),
        ),
        "truncated": truncated,
    }


def _grouped_support_outcome_profile(
    D,
    pc_tree: PCNode,
    *,
    atoms: list[dict],
    method: str,
    max_p_degree: int,
    limit: Optional[int],
    max_groups: Optional[int],
) -> dict:
    validate_dissimilarity(D)
    if max_groups is not None and max_groups < 0:
        raise ValueError("max_groups must be non-negative or None")

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": method,
        "encoding": encoding,
        "complete": True,
        "atoms": atoms,
        "groups": [],
        "counts": {
            "support_group_count": 0,
            "groups_profiled": 0,
            "grouped_support_assignments_seen": 0,
            "hit_assignments": 0,
            "no_hit_assignments": 0,
            "classification_atom_checks": 0,
            "exhaustive_atom_checks_seen": 0,
            "no_hit_exhaustive_atom_checks": 0,
            "first_hit_position_sum": 0,
            "pair_side_split_hit_assignments": 0,
            "pair_side_split_no_hit_assignments": 0,
            "pair_side_split_checks": 0,
            "pair_side_split_side_checks": 0,
            "pair_side_split_side_cache_hits": 0,
            "pair_side_split_side_cache_misses": 0,
            "pair_side_split_component_checks": 0,
            "pair_side_split_component_witness_checks": 0,
            "pair_side_split_cached_checks": 0,
            "pair_side_split_bitset_cached_checks": 0,
            "pair_side_split_mismatches": 0,
            "pair_side_split_work_ratio": 0.0,
            "pair_side_split_cached_work_ratio": 0.0,
            "pair_side_split_bitset_cached_work_ratio": 0.0,
            "first_pair_side_split_mismatch": None,
            "pair_side_split_bitset_hit_assignments": 0,
            "pair_side_split_bitset_no_hit_assignments": 0,
            "pair_side_split_bitset_checks": 0,
            "pair_side_split_bitset_component_checks": 0,
            "pair_side_split_bitset_component_cache_hits": 0,
            "pair_side_split_bitset_component_cache_misses": 0,
            "pair_side_split_bitset_witness_visits": 0,
            "pair_side_split_bitset_side_cache_hits": 0,
            "pair_side_split_bitset_side_cache_misses": 0,
            "pair_side_split_bitset_projection_checks": 0,
            "pair_side_split_bitset_work_ratio": 0.0,
            "pair_side_split_bitset_projection_work_ratio": 0.0,
            "pair_side_split_bitset_mismatches": 0,
            "first_pair_side_split_bitset_mismatch": None,
            "component_mask_state_count": 0,
            "component_mask_state_hit_count": 0,
            "component_mask_state_no_hit_count": 0,
            "component_mask_state_mixed_count": 0,
            "component_mask_state_mismatches": 0,
            "first_component_mask_state_mismatch": None,
            "component_mask_state_max_bucket_size": 0,
            "component_mask_state_ratio": 0.0,
            "component_mask_state_average_bucket_size": 0.0,
            "component_mask_state_component_masks": 0,
            "component_mask_state_witness_visits": 0,
            "component_mask_state_side_cache_hits": 0,
            "component_mask_state_side_cache_misses": 0,
            "component_mask_state_work_ratio": 0.0,
            "component_mask_state_projection_work_ratio": 0.0,
            "component_mask_quotients": {},
            "pure_hit_slice_count": 0,
            "pure_no_hit_slice_count": 0,
            "unary_hit_certified_assignments": 0,
            "unary_no_hit_certified_assignments": 0,
            "ambiguous_hit_assignments": 0,
            "ambiguous_no_hit_assignments": 0,
            "max_group_no_hit_assignments": 0,
            "max_group_no_hit_ratio": 0.0,
            "max_group_no_hit_exhaustive_atom_checks": 0,
            "unary_hit_coverage_ratio": 0.0,
            "unary_no_hit_coverage_ratio": 0.0,
            "ambiguous_hit_ratio": 0.0,
            "ambiguous_no_hit_ratio": 0.0,
            "no_hit_assignment_ratio": 0.0,
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    atoms_by_support: dict[tuple[Path, ...], list[dict]] = {}
    for atom_info in atoms:
        support = quartet_support_paths(pc_tree, atom_info["atom"])
        atoms_by_support.setdefault(support, []).append(atom_info)
    report["counts"]["support_group_count"] = len(atoms_by_support)

    group_profiles: list[dict] = []
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int] = {}
    bitset_side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int] = {}
    component_side_cache: dict[tuple[tuple[int, int], tuple[int, ...], NogoodSignature], int] = {}
    mask_state_side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int] = {}
    truncated = False
    for support, support_atoms in atoms_by_support.items():
        if limit is None:
            remaining_limit = None
        else:
            remaining_limit = limit - report["counts"]["grouped_support_assignments_seen"]
            if remaining_limit <= 0:
                truncated = True
                break
        group = _profile_single_support_group(
            pc_tree,
            encoding,
            support,
            support_atoms,
            limit=remaining_limit,
            side_cache=side_cache,
            bitset_side_cache=bitset_side_cache,
            component_side_cache=component_side_cache,
            mask_state_side_cache=mask_state_side_cache,
        )
        group_profiles.append(group)
        counts = report["counts"]
        counts["groups_profiled"] += 1
        counts["grouped_support_assignments_seen"] += group["assignments_seen"]
        counts["hit_assignments"] += group["hit_assignments"]
        counts["no_hit_assignments"] += group["no_hit_assignments"]
        counts["classification_atom_checks"] += group["classification_atom_checks"]
        counts["exhaustive_atom_checks_seen"] += group["exhaustive_atom_checks_seen"]
        counts["no_hit_exhaustive_atom_checks"] += group["no_hit_exhaustive_atom_checks"]
        counts["first_hit_position_sum"] += group["first_hit_position_sum"]
        counts["pair_side_split_hit_assignments"] += group["pair_side_split_hit_assignments"]
        counts["pair_side_split_no_hit_assignments"] += group["pair_side_split_no_hit_assignments"]
        counts["pair_side_split_checks"] += group["pair_side_split_checks"]
        counts["pair_side_split_side_checks"] += group["pair_side_split_side_checks"]
        counts["pair_side_split_side_cache_hits"] += group["pair_side_split_side_cache_hits"]
        counts["pair_side_split_side_cache_misses"] += group["pair_side_split_side_cache_misses"]
        counts["pair_side_split_component_checks"] += group["pair_side_split_component_checks"]
        counts["pair_side_split_component_witness_checks"] += group[
            "pair_side_split_component_witness_checks"
        ]
        counts["pair_side_split_cached_checks"] += group["pair_side_split_cached_checks"]
        counts["pair_side_split_bitset_cached_checks"] += group[
            "pair_side_split_bitset_cached_checks"
        ]
        counts["pair_side_split_mismatches"] += group["pair_side_split_mismatches"]
        if (
            counts["first_pair_side_split_mismatch"] is None
            and group["first_pair_side_split_mismatch"] is not None
        ):
            counts["first_pair_side_split_mismatch"] = group["first_pair_side_split_mismatch"]
        counts["pair_side_split_bitset_hit_assignments"] += group[
            "pair_side_split_bitset_hit_assignments"
        ]
        counts["pair_side_split_bitset_no_hit_assignments"] += group[
            "pair_side_split_bitset_no_hit_assignments"
        ]
        counts["pair_side_split_bitset_checks"] += group["pair_side_split_bitset_checks"]
        counts["pair_side_split_bitset_component_checks"] += group[
            "pair_side_split_bitset_component_checks"
        ]
        counts["pair_side_split_bitset_component_cache_hits"] += group[
            "pair_side_split_bitset_component_cache_hits"
        ]
        counts["pair_side_split_bitset_component_cache_misses"] += group[
            "pair_side_split_bitset_component_cache_misses"
        ]
        counts["pair_side_split_bitset_witness_visits"] += group[
            "pair_side_split_bitset_witness_visits"
        ]
        counts["pair_side_split_bitset_side_cache_hits"] += group[
            "pair_side_split_bitset_side_cache_hits"
        ]
        counts["pair_side_split_bitset_side_cache_misses"] += group[
            "pair_side_split_bitset_side_cache_misses"
        ]
        counts["pair_side_split_bitset_projection_checks"] += group[
            "pair_side_split_bitset_projection_checks"
        ]
        counts["pair_side_split_bitset_mismatches"] += group[
            "pair_side_split_bitset_mismatches"
        ]
        if (
            counts["first_pair_side_split_bitset_mismatch"] is None
            and group["first_pair_side_split_bitset_mismatch"] is not None
        ):
            counts["first_pair_side_split_bitset_mismatch"] = group[
                "first_pair_side_split_bitset_mismatch"
            ]
        counts["component_mask_state_count"] += group["component_mask_state_count"]
        counts["component_mask_state_hit_count"] += group["component_mask_state_hit_count"]
        counts["component_mask_state_no_hit_count"] += group[
            "component_mask_state_no_hit_count"
        ]
        counts["component_mask_state_mixed_count"] += group["component_mask_state_mixed_count"]
        counts["component_mask_state_mismatches"] += group["component_mask_state_mismatches"]
        if (
            counts["first_component_mask_state_mismatch"] is None
            and group["first_component_mask_state_mismatch"] is not None
        ):
            counts["first_component_mask_state_mismatch"] = group[
                "first_component_mask_state_mismatch"
            ]
        counts["component_mask_state_max_bucket_size"] = max(
            counts["component_mask_state_max_bucket_size"],
            group["component_mask_state_max_bucket_size"],
        )
        counts["component_mask_state_component_masks"] += group[
            "component_mask_state_component_masks"
        ]
        counts["component_mask_state_witness_visits"] += group[
            "component_mask_state_witness_visits"
        ]
        counts["component_mask_state_side_cache_hits"] += group[
            "component_mask_state_side_cache_hits"
        ]
        counts["component_mask_state_side_cache_misses"] += group[
            "component_mask_state_side_cache_misses"
        ]
        for quotient_name, quotient in group["component_mask_quotients"].items():
            aggregate = counts["component_mask_quotients"].setdefault(
                quotient_name,
                {
                    "state_count": 0,
                    "hit_state_count": 0,
                    "no_hit_state_count": 0,
                    "mixed_count": 0,
                    "max_bucket_size": 0,
                    "ratio": 0.0,
                    "average_bucket_size": 0.0,
                },
            )
            aggregate["state_count"] += quotient["state_count"]
            aggregate["hit_state_count"] += quotient["hit_state_count"]
            aggregate["no_hit_state_count"] += quotient["no_hit_state_count"]
            aggregate["mixed_count"] += quotient["mixed_count"]
            aggregate["max_bucket_size"] = max(
                aggregate["max_bucket_size"],
                quotient["max_bucket_size"],
            )
        counts["pure_hit_slice_count"] += group["pure_hit_slice_count"]
        counts["pure_no_hit_slice_count"] += group["pure_no_hit_slice_count"]
        counts["unary_hit_certified_assignments"] += group["unary_hit_certified_assignments"]
        counts["unary_no_hit_certified_assignments"] += group["unary_no_hit_certified_assignments"]
        counts["ambiguous_hit_assignments"] += group["ambiguous_hit_assignments"]
        counts["ambiguous_no_hit_assignments"] += group["ambiguous_no_hit_assignments"]
        counts["max_group_no_hit_assignments"] = max(
            counts["max_group_no_hit_assignments"],
            group["no_hit_assignments"],
        )
        counts["max_group_no_hit_ratio"] = max(
            counts["max_group_no_hit_ratio"],
            group["no_hit_ratio"],
        )
        counts["max_group_no_hit_exhaustive_atom_checks"] = max(
            counts["max_group_no_hit_exhaustive_atom_checks"],
            group["no_hit_exhaustive_atom_checks"],
        )
        if group["truncated"]:
            truncated = True
            break

    counts = report["counts"]
    if counts["hit_assignments"]:
        counts["unary_hit_coverage_ratio"] = (
            counts["unary_hit_certified_assignments"] / counts["hit_assignments"]
        )
        counts["ambiguous_hit_ratio"] = counts["ambiguous_hit_assignments"] / counts["hit_assignments"]
    if counts["no_hit_assignments"]:
        counts["unary_no_hit_coverage_ratio"] = (
            counts["unary_no_hit_certified_assignments"] / counts["no_hit_assignments"]
        )
        counts["ambiguous_no_hit_ratio"] = (
            counts["ambiguous_no_hit_assignments"] / counts["no_hit_assignments"]
        )
    if counts["grouped_support_assignments_seen"]:
        counts["no_hit_assignment_ratio"] = (
            counts["no_hit_assignments"] / counts["grouped_support_assignments_seen"]
        )
        counts["component_mask_state_ratio"] = (
            counts["component_mask_state_count"] / counts["grouped_support_assignments_seen"]
        )
    if counts["component_mask_state_count"]:
        counts["component_mask_state_average_bucket_size"] = (
            counts["grouped_support_assignments_seen"] / counts["component_mask_state_count"]
        )
    for quotient in counts["component_mask_quotients"].values():
        if counts["grouped_support_assignments_seen"]:
            quotient["ratio"] = quotient["state_count"] / counts["grouped_support_assignments_seen"]
        if quotient["state_count"]:
            quotient["average_bucket_size"] = (
                counts["grouped_support_assignments_seen"] / quotient["state_count"]
            )
    if counts["classification_atom_checks"]:
        counts["component_mask_state_work_ratio"] = (
            (
                counts["component_mask_state_component_masks"]
                + counts["component_mask_state_witness_visits"]
            )
            / counts["classification_atom_checks"]
        )
        counts["component_mask_state_projection_work_ratio"] = (
            (
                counts["component_mask_state_component_masks"]
                + counts["component_mask_state_side_cache_misses"]
            )
            / counts["classification_atom_checks"]
        )
        counts["pair_side_split_work_ratio"] = (
            counts["pair_side_split_checks"] / counts["classification_atom_checks"]
        )
        counts["pair_side_split_cached_work_ratio"] = (
            counts["pair_side_split_cached_checks"] / counts["classification_atom_checks"]
        )
        counts["pair_side_split_bitset_cached_work_ratio"] = (
            counts["pair_side_split_bitset_cached_checks"] / counts["classification_atom_checks"]
        )
        counts["pair_side_split_bitset_work_ratio"] = (
            counts["pair_side_split_bitset_checks"] / counts["classification_atom_checks"]
        )
        counts["pair_side_split_bitset_projection_work_ratio"] = (
            counts["pair_side_split_bitset_projection_checks"]
            / counts["classification_atom_checks"]
        )

    group_profiles.sort(
        key=lambda group: (
            group["no_hit_exhaustive_atom_checks"],
            group["ambiguous_no_hit_assignments"],
            group["support_product"],
            group["group_size"],
        ),
        reverse=True,
    )
    report["groups"] = group_profiles if max_groups is None else group_profiles[:max_groups]
    report["complete"] = not truncated
    return report


def compile_cr_nogoods(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile cR-violating cyclic quartet atoms into projected nogoods.

    The compilation is still experimental and enumerates complete assignments
    to discover projected signatures.  It is useful for measuring whether the
    support projection is exact on small PC-trees.
    """

    validate_dissimilarity(D)
    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": "compiled_cr_quartet_nogoods",
        "encoding": encoding,
        "complete": True,
        "atoms": forbidden_cr_atoms(D),
        "nogoods": [],
        "counts": {
            "assignments_seen": 0,
            "atom_hits": 0,
            "unique_nogoods": 0,
            "atoms_with_nogoods": 0,
            "max_support_size": 0,
            "support_size_histogram": {},
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    atoms = report["atoms"]
    support_by_atom = {
        tuple(atom_info["atom"]): quartet_support_paths(pc_tree, atom_info["atom"])
        for atom_info in atoms
    }
    seen: dict[tuple[tuple[int, ...], NogoodSignature], dict] = {}
    truncated = False
    for assignment in iter_local_assignments(encoding, limit=None if limit is None else limit + 1):
        if limit is not None and report["counts"]["assignments_seen"] >= limit:
            truncated = True
            break
        report["counts"]["assignments_seen"] += 1
        order = canonical_circular_order(frontier_from_assignment(pc_tree, assignment))
        for atom_info in atoms:
            atom = tuple(atom_info["atom"])
            if not _cyclic_atom_occurs(order, atom):
                continue
            support = support_by_atom[atom]
            signature = _nogood_signature(assignment, support)
            key = (atom, signature)
            report["counts"]["atom_hits"] += 1
            if key in seen:
                continue
            nogood = {
                "atom": atom,
                "support": support,
                "signature": signature,
                "violation": atom_info,
            }
            seen[key] = nogood

    nogoods = list(seen.values())
    atoms_with_nogoods = {nogood["atom"] for nogood in nogoods}
    histogram: dict[int, int] = {}
    for nogood in nogoods:
        size = len(nogood["support"])
        histogram[size] = histogram.get(size, 0) + 1

    report["nogoods"] = nogoods
    report["complete"] = not truncated
    report["counts"]["unique_nogoods"] = len(nogoods)
    report["counts"]["atoms_with_nogoods"] = len(atoms_with_nogoods)
    report["counts"]["support_size_histogram"] = dict(sorted(histogram.items()))
    report["counts"]["max_support_size"] = max(histogram, default=0)
    return report


def compile_bad_side_nogoods(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile bad-side pair atoms into projected nogoods.

    This is still an enumeration-based experiment.  It uses fewer source atoms
    than ``compile_cr_nogoods`` when many ordered quartet violations are
    duplicates of the same endpoint-pair bad-side obstruction.
    """

    validate_dissimilarity(D)
    witnesses_by_pair = bad_witnesses_by_pair(D)
    witness_pair_constraints = sum(
        len(witnesses) * (len(witnesses) - 1) // 2
        for witnesses in witnesses_by_pair.values()
    )
    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": "compiled_bad_side_pair_nogoods",
        "encoding": encoding,
        "complete": True,
        "atoms": forbidden_bad_side_atoms(D),
        "bad_pairs": [
            {"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": len(witnesses)}
            for pair, witnesses in witnesses_by_pair.items()
            if witnesses
        ],
        "nogoods": [],
        "counts": {
            "assignments_seen": 0,
            "atom_hits": 0,
            "nonempty_bad_pair_count": sum(1 for witnesses in witnesses_by_pair.values() if witnesses),
            "nontrivial_bad_pair_count": sum(1 for witnesses in witnesses_by_pair.values() if len(witnesses) >= 2),
            "bad_witness_total": sum(len(witnesses) for witnesses in witnesses_by_pair.values()),
            "witness_pair_constraints": witness_pair_constraints,
            "unique_nogoods": 0,
            "atoms_with_nogoods": 0,
            "pairs_with_nogoods": 0,
            "max_support_size": 0,
            "support_size_histogram": {},
        },
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    atoms = report["atoms"]
    support_by_atom = {
        tuple(atom_info["atom"]): quartet_support_paths(pc_tree, atom_info["atom"])
        for atom_info in atoms
    }
    seen: dict[tuple[tuple[int, ...], NogoodSignature], dict] = {}
    truncated = False
    for assignment in iter_local_assignments(encoding, limit=None if limit is None else limit + 1):
        if limit is not None and report["counts"]["assignments_seen"] >= limit:
            truncated = True
            break
        report["counts"]["assignments_seen"] += 1
        order = canonical_circular_order(frontier_from_assignment(pc_tree, assignment))
        for atom_info in atoms:
            atom = tuple(atom_info["atom"])
            if not _cyclic_atom_occurs(order, atom):
                continue
            support = support_by_atom[atom]
            signature = _nogood_signature(assignment, support)
            key = (atom, signature)
            report["counts"]["atom_hits"] += 1
            if key in seen:
                continue
            nogood = {
                "atom": atom,
                "pair": atom_info["pair"],
                "bad_witnesses": atom_info["bad_witnesses"],
                "support": support,
                "signature": signature,
                "violation": atom_info,
            }
            seen[key] = nogood

    nogoods = list(seen.values())
    atoms_with_nogoods = {nogood["atom"] for nogood in nogoods}
    histogram: dict[int, int] = {}
    for nogood in nogoods:
        size = len(nogood["support"])
        histogram[size] = histogram.get(size, 0) + 1

    report["nogoods"] = nogoods
    report["complete"] = not truncated
    report["counts"]["unique_nogoods"] = len(nogoods)
    report["counts"]["atoms_with_nogoods"] = len(atoms_with_nogoods)
    report["counts"]["pairs_with_nogoods"] = len({nogood["pair"] for nogood in nogoods})
    report["counts"]["support_size_histogram"] = dict(sorted(histogram.items()))
    report["counts"]["max_support_size"] = max(histogram, default=0)
    return report


def compile_cr_nogoods_support_local(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile cR quartet nogoods by enumerating only support domains."""

    return _compile_nogoods_by_support_products(
        D,
        pc_tree,
        atoms=forbidden_cr_atoms(D),
        method="support_local_cr_quartet_nogoods",
        max_p_degree=max_p_degree,
        limit=limit,
    )


def compile_bad_side_nogoods_support_local(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile bad-side pair nogoods by enumerating only support domains."""

    validate_dissimilarity(D)
    witnesses_by_pair = bad_witnesses_by_pair(D)
    witness_pair_constraints = sum(
        len(witnesses) * (len(witnesses) - 1) // 2
        for witnesses in witnesses_by_pair.values()
    )
    report = _compile_nogoods_by_support_products(
        D,
        pc_tree,
        atoms=forbidden_bad_side_atoms(D),
        method="support_local_bad_side_pair_nogoods",
        max_p_degree=max_p_degree,
        limit=limit,
    )
    report["bad_pairs"] = [
        {"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": len(witnesses)}
        for pair, witnesses in witnesses_by_pair.items()
        if witnesses
    ]
    report["counts"]["nonempty_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if witnesses
    )
    report["counts"]["nontrivial_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if len(witnesses) >= 2
    )
    report["counts"]["bad_witness_total"] = sum(len(witnesses) for witnesses in witnesses_by_pair.values())
    report["counts"]["witness_pair_constraints"] = witness_pair_constraints
    if "pairs_with_nogoods" not in report["counts"]:
        report["counts"]["pairs_with_nogoods"] = 0
    return report


def compile_bad_side_nogoods_grouped_support_local(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile bad-side nogoods while grouping atoms by identical support."""

    validate_dissimilarity(D)
    witnesses_by_pair = bad_witnesses_by_pair(D)
    witness_pair_constraints = sum(
        len(witnesses) * (len(witnesses) - 1) // 2
        for witnesses in witnesses_by_pair.values()
    )
    report = _compile_nogoods_by_grouped_supports(
        D,
        pc_tree,
        atoms=forbidden_bad_side_atoms(D),
        method="grouped_support_local_bad_side_pair_nogoods",
        max_p_degree=max_p_degree,
        limit=limit,
    )
    report["bad_pairs"] = [
        {"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": len(witnesses)}
        for pair, witnesses in witnesses_by_pair.items()
        if witnesses
    ]
    report["counts"]["nonempty_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if witnesses
    )
    report["counts"]["nontrivial_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if len(witnesses) >= 2
    )
    report["counts"]["bad_witness_total"] = sum(len(witnesses) for witnesses in witnesses_by_pair.values())
    report["counts"]["witness_pair_constraints"] = witness_pair_constraints
    if "pairs_with_nogoods" not in report["counts"]:
        report["counts"]["pairs_with_nogoods"] = 0
    return report


def compile_bad_side_nogoods_grouped_first_hit_support_local(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Compile grouped bad-side nogoods, stopping after the first hit per signature."""

    validate_dissimilarity(D)
    witnesses_by_pair = bad_witnesses_by_pair(D)
    witness_pair_constraints = sum(
        len(witnesses) * (len(witnesses) - 1) // 2
        for witnesses in witnesses_by_pair.values()
    )
    report = _compile_nogoods_by_grouped_supports(
        D,
        pc_tree,
        atoms=forbidden_bad_side_atoms(D),
        method="grouped_first_hit_support_local_bad_side_pair_nogoods",
        max_p_degree=max_p_degree,
        limit=limit,
        stop_after_first_hit=True,
    )
    report["bad_pairs"] = [
        {"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": len(witnesses)}
        for pair, witnesses in witnesses_by_pair.items()
        if witnesses
    ]
    report["counts"]["nonempty_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if witnesses
    )
    report["counts"]["nontrivial_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if len(witnesses) >= 2
    )
    report["counts"]["bad_witness_total"] = sum(len(witnesses) for witnesses in witnesses_by_pair.values())
    report["counts"]["witness_pair_constraints"] = witness_pair_constraints
    if "pairs_with_nogoods" not in report["counts"]:
        report["counts"]["pairs_with_nogoods"] = 0
    return report


def bad_side_grouped_support_outcome_profile(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    max_groups: Optional[int] = 10,
) -> dict:
    """Profile support-level hit/no-hit outcomes for bad-side atoms.

    A no-hit assignment is a support assignment for which no atom in the group
    occurs.  This report is deliberately diagnostic: it still scans atoms and
    therefore is not a compact solver.  The unary coverage counters measure how
    often a hit/no-hit outcome is certified by a single pure local choice.
    """

    validate_dissimilarity(D)
    witnesses_by_pair = bad_witnesses_by_pair(D)
    witness_pair_constraints = sum(
        len(witnesses) * (len(witnesses) - 1) // 2
        for witnesses in witnesses_by_pair.values()
    )
    report = _grouped_support_outcome_profile(
        D,
        pc_tree,
        atoms=forbidden_bad_side_atoms(D),
        method="grouped_support_bad_side_outcome_profile",
        max_p_degree=max_p_degree,
        limit=limit,
        max_groups=max_groups,
    )
    report["bad_pairs"] = [
        {"pair": pair, "bad_witnesses": witnesses, "bad_witness_count": len(witnesses)}
        for pair, witnesses in witnesses_by_pair.items()
        if witnesses
    ]
    report["counts"]["nonempty_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if witnesses
    )
    report["counts"]["nontrivial_bad_pair_count"] = sum(
        1 for witnesses in witnesses_by_pair.values() if len(witnesses) >= 2
    )
    report["counts"]["bad_witness_total"] = sum(len(witnesses) for witnesses in witnesses_by_pair.values())
    report["counts"]["witness_pair_constraints"] = witness_pair_constraints
    return report


def component_mask_quotient_context_collision_profile(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    max_pairs: Optional[int] = None,
) -> dict:
    """Measure whether local mask-state quotients survive neighboring supports.

    For two overlapping support groups ``S`` and ``C``, this diagnostic fixes
    the choices on ``(S union C) \\ S`` and asks whether a quotient of the local
    state on ``S`` still determines the hit/no-hit outcome of context group
    ``C``.  Mixed buckets are counterexamples to using that quotient as a
    standalone DP state.  The control quotient ``assignment_signature`` should
    never be mixed.
    """

    validate_dissimilarity(D)
    if max_pairs is not None and max_pairs < 0:
        raise ValueError("max_pairs must be non-negative or None")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": "component_mask_quotient_context_collision_profile",
        "encoding": encoding,
        "complete": True,
        "counts": {
            "support_group_count": 0,
            "context_pair_count": 0,
            "pairs_profiled": 0,
            "context_assignments_seen": 0,
            "max_context_support_product": 0,
        },
        "quotients": {},
        "first_collisions": {},
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    atoms = forbidden_bad_side_atoms(D)
    atoms_by_support: dict[tuple[Path, ...], list[dict]] = {}
    for atom_info in atoms:
        support = quartet_support_paths(pc_tree, atom_info["atom"])
        atoms_by_support.setdefault(support, []).append(atom_info)
    report["counts"]["support_group_count"] = len(atoms_by_support)

    support_items = sorted(atoms_by_support.items(), key=lambda item: (len(item[0]), item[0]))
    context_pairs: list[
        tuple[tuple[Path, ...], list[dict], tuple[Path, ...], list[dict], tuple[Path, ...]]
    ] = []
    for base_support, base_atoms in support_items:
        base_set = set(base_support)
        for context_support, context_atoms in support_items:
            context_set = set(context_support)
            if context_support == base_support or not (base_set & context_set):
                continue
            union_support = tuple(sorted(base_set | context_set))
            context_pairs.append(
                (base_support, base_atoms, context_support, context_atoms, union_support)
            )
    report["counts"]["context_pair_count"] = len(context_pairs)

    quotient_counts: dict[str, dict[tuple, int]] = {}
    quotient_hit_values: dict[str, dict[tuple, bool]] = {}
    quotient_mixed: dict[str, set[tuple]] = {}
    quotient_representatives: dict[str, dict[tuple, dict]] = {}
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int] = {}
    truncated = False

    for base_support, base_atoms, context_support, context_atoms, union_support in context_pairs:
        if max_pairs is not None and report["counts"]["pairs_profiled"] >= max_pairs:
            truncated = True
            break
        context_support_product = _domain_product_size(encoding, union_support)
        report["counts"]["max_context_support_product"] = max(
            report["counts"]["max_context_support_product"],
            context_support_product,
        )
        base_set = set(base_support)
        extra_support = tuple(path for path in union_support if path not in base_set)
        domain_lists = [encoding["domains"][path] for path in union_support]
        components_by_pair = _bad_witness_components_by_pair(base_atoms)
        report["counts"]["pairs_profiled"] += 1

        for choices in product(*domain_lists):
            if limit is not None and report["counts"]["context_assignments_seen"] >= limit:
                truncated = True
                break
            context_assignment = dict(zip(union_support, choices))
            base_assignment = {path: context_assignment[path] for path in base_support}
            context_hit = _support_atom_scan_hit(pc_tree, context_assignment, context_atoms)
            context_signature = _nogood_signature(context_assignment, context_support)
            base_signature = _nogood_signature(base_assignment, base_support)
            extra_signature = _nogood_signature(context_assignment, extra_support)
            mask_state = _component_mask_state(
                pc_tree,
                base_assignment,
                components_by_pair,
                side_cache,
            )
            quotients = {
                "assignment_signature": base_signature,
                **_component_mask_state_quotients(mask_state["state"]),
            }

            for quotient_name, quotient_state in quotients.items():
                key = (base_support, context_support, extra_signature, quotient_state)
                counts = quotient_counts.setdefault(quotient_name, {})
                counts[key] = counts.get(key, 0) + 1
                hit_values = quotient_hit_values.setdefault(quotient_name, {})
                representatives = quotient_representatives.setdefault(quotient_name, {})
                representative = representatives.setdefault(
                    key,
                    {
                        "hit": context_hit,
                        "base_signature": base_signature,
                        "context_signature": context_signature,
                    },
                )
                previous_hit = hit_values.setdefault(key, context_hit)
                if previous_hit != context_hit:
                    quotient_mixed.setdefault(quotient_name, set()).add(key)
                    if quotient_name not in report["first_collisions"]:
                        report["first_collisions"][quotient_name] = {
                            "base_support": base_support,
                            "context_support": context_support,
                            "extra_signature": extra_signature,
                            "quotient_state": quotient_state,
                            "previous_hit": representative["hit"],
                            "new_hit": context_hit,
                            "previous_base_signature": representative["base_signature"],
                            "new_base_signature": base_signature,
                            "previous_context_signature": representative["context_signature"],
                            "new_context_signature": context_signature,
                        }
            report["counts"]["context_assignments_seen"] += 1
        if truncated:
            break

    quotient_reports = {}
    assignments_seen = report["counts"]["context_assignments_seen"]
    for quotient_name, counts in sorted(quotient_counts.items()):
        state_count = len(counts)
        mixed_count = len(quotient_mixed.get(quotient_name, set()))
        quotient_reports[quotient_name] = {
            "state_count": state_count,
            "mixed_count": mixed_count,
            "max_bucket_size": max(counts.values(), default=0),
            "ratio": state_count / assignments_seen if assignments_seen else 0.0,
            "average_bucket_size": assignments_seen / state_count if state_count else 0.0,
            "mixed_ratio": mixed_count / state_count if state_count else 0.0,
        }

    report["quotients"] = quotient_reports
    report["complete"] = not truncated
    return report


def _component_mask_state_summary(
    states: dict[str, dict[tuple, int]],
    assignments_seen: int,
    *,
    boundary_mixed: Optional[dict[str, set[tuple]]] = None,
    local_hit_mixed: Optional[dict[str, set[tuple]]] = None,
) -> dict:
    summary = {}
    for state_name, counts in sorted(states.items()):
        state_count = len(counts)
        boundary_mixed_count = len((boundary_mixed or {}).get(state_name, set()))
        local_hit_mixed_count = len((local_hit_mixed or {}).get(state_name, set()))
        summary[state_name] = {
            "state_count": state_count,
            "max_bucket_size": max(counts.values(), default=0),
            "ratio": state_count / assignments_seen if assignments_seen else 0.0,
            "average_bucket_size": assignments_seen / state_count if state_count else 0.0,
            "boundary_mixed_count": boundary_mixed_count,
            "boundary_mixed_ratio": (
                boundary_mixed_count / state_count if state_count else 0.0
            ),
            "local_hit_mixed_count": local_hit_mixed_count,
            "local_hit_mixed_ratio": (
                local_hit_mixed_count / state_count if state_count else 0.0
            ),
        }
    return summary


def component_mask_open_boundary_profile(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
    max_pairs: Optional[int] = None,
) -> dict:
    """Count states that carry one-hop open boundary responses.

    This diagnostic repairs the T056 collision test by storing, for every local
    assignment of a support group, the hit/no-hit responses of neighboring
    support groups under each external context choice.  It is not a solver: the
    response vector is built by enumeration and only covers one-hop neighbors.
    """

    validate_dissimilarity(D)
    if max_pairs is not None and max_pairs < 0:
        raise ValueError("max_pairs must be non-negative or None")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")

    encoding = build_local_domains(pc_tree, max_p_degree=max_p_degree)
    report = {
        "implemented": True,
        "method": "component_mask_open_boundary_profile",
        "encoding": encoding,
        "complete": True,
        "counts": {
            "support_group_count": 0,
            "context_pair_count": 0,
            "pairs_profiled": 0,
            "local_assignments_seen": 0,
            "boundary_response_checks": 0,
            "boundary_entries_total": 0,
            "max_boundary_entries_per_assignment": 0,
            "average_boundary_entries_per_assignment": 0.0,
            "max_context_support_product": 0,
        },
        "states": {},
    }
    if encoding["unsupported"]:
        report["complete"] = False
        return report

    atoms = forbidden_bad_side_atoms(D)
    atoms_by_support: dict[tuple[Path, ...], list[dict]] = {}
    for atom_info in atoms:
        support = quartet_support_paths(pc_tree, atom_info["atom"])
        atoms_by_support.setdefault(support, []).append(atom_info)
    report["counts"]["support_group_count"] = len(atoms_by_support)

    support_items = sorted(atoms_by_support.items(), key=lambda item: (len(item[0]), item[0]))
    contexts_by_base: dict[
        tuple[Path, ...],
        list[tuple[tuple[Path, ...], list[dict], tuple[Path, ...], tuple[Path, ...]]],
    ] = {support: [] for support, _ in support_items}
    pair_count = 0
    for base_support, _base_atoms in support_items:
        base_set = set(base_support)
        for context_support, context_atoms in support_items:
            context_set = set(context_support)
            if context_support == base_support or not (base_set & context_set):
                continue
            pair_count += 1
            if max_pairs is not None and pair_count > max_pairs:
                continue
            union_support = tuple(sorted(base_set | context_set))
            extra_support = tuple(path for path in union_support if path not in base_set)
            contexts_by_base[base_support].append(
                (context_support, context_atoms, union_support, extra_support)
            )
    report["counts"]["context_pair_count"] = pair_count
    report["counts"]["pairs_profiled"] = sum(len(contexts) for contexts in contexts_by_base.values())

    states: dict[str, dict[tuple, int]] = {}
    state_boundary_values: dict[str, dict[tuple, tuple]] = {}
    state_boundary_mixed: dict[str, set[tuple]] = {}
    state_local_hit_values: dict[str, dict[tuple, bool]] = {}
    state_local_hit_mixed: dict[str, set[tuple]] = {}
    side_cache: dict[tuple[tuple[int, int], int, NogoodSignature], int] = {}
    truncated = False
    for base_support, base_atoms in support_items:
        if limit is not None and report["counts"]["local_assignments_seen"] >= limit:
            truncated = True
            break
        base_domain_lists = [encoding["domains"][path] for path in base_support]
        components_by_pair = _bad_witness_components_by_pair(base_atoms)
        contexts = contexts_by_base[base_support]

        for base_choices in product(*base_domain_lists):
            if limit is not None and report["counts"]["local_assignments_seen"] >= limit:
                truncated = True
                break
            base_assignment = dict(zip(base_support, base_choices))
            base_signature = _nogood_signature(base_assignment, base_support)
            boundary_entries = []
            for context_support, context_atoms, union_support, extra_support in contexts:
                report["counts"]["max_context_support_product"] = max(
                    report["counts"]["max_context_support_product"],
                    _domain_product_size(encoding, union_support),
                )
                extra_domain_lists = [encoding["domains"][path] for path in extra_support]
                for extra_choices in product(*extra_domain_lists):
                    union_assignment = dict(base_assignment)
                    union_assignment.update(dict(zip(extra_support, extra_choices)))
                    extra_signature = _nogood_signature(union_assignment, extra_support)
                    context_hit = _support_atom_scan_hit(
                        pc_tree,
                        union_assignment,
                        context_atoms,
                    )
                    report["counts"]["boundary_response_checks"] += 1
                    boundary_entries.append((context_support, extra_signature, context_hit))

            boundary_response = tuple(boundary_entries)
            mask_state = _component_mask_state(
                pc_tree,
                base_assignment,
                components_by_pair,
                side_cache,
            )
            closed_quotients = _component_mask_state_quotients(mask_state["state"])
            candidate_states = {
                "assignment_signature": (base_support, base_signature),
                "full": (base_support, closed_quotients["full"]),
                "mask_multiset": (base_support, closed_quotients["mask_multiset"]),
                "boundary_response": (base_support, boundary_response),
                "local_boundary_response": (base_support, mask_state["hit"], boundary_response),
                "full_plus_boundary": (base_support, closed_quotients["full"], boundary_response),
                "mask_multiset_plus_boundary": (
                    base_support,
                    closed_quotients["mask_multiset"],
                    boundary_response,
                ),
                "hit_components_plus_boundary": (
                    base_support,
                    closed_quotients["hit_components"],
                    boundary_response,
                ),
            }
            for state_name, state in candidate_states.items():
                state_counts = states.setdefault(state_name, {})
                state_counts[state] = state_counts.get(state, 0) + 1
                boundary_values = state_boundary_values.setdefault(state_name, {})
                previous_boundary = boundary_values.setdefault(state, boundary_response)
                if previous_boundary != boundary_response:
                    state_boundary_mixed.setdefault(state_name, set()).add(state)
                local_hit_values = state_local_hit_values.setdefault(state_name, {})
                previous_local_hit = local_hit_values.setdefault(state, mask_state["hit"])
                if previous_local_hit != mask_state["hit"]:
                    state_local_hit_mixed.setdefault(state_name, set()).add(state)
            report["counts"]["local_assignments_seen"] += 1
            boundary_entry_count = len(boundary_entries)
            report["counts"]["boundary_entries_total"] += boundary_entry_count
            report["counts"]["max_boundary_entries_per_assignment"] = max(
                report["counts"]["max_boundary_entries_per_assignment"],
                boundary_entry_count,
            )
        if truncated:
            break

    local_assignments_seen = report["counts"]["local_assignments_seen"]
    if local_assignments_seen:
        report["counts"]["average_boundary_entries_per_assignment"] = (
            report["counts"]["boundary_entries_total"] / local_assignments_seen
        )
    report["states"] = _component_mask_state_summary(
        states,
        local_assignments_seen,
        boundary_mixed=state_boundary_mixed,
        local_hit_mixed=state_local_hit_mixed,
    )
    if max_pairs is not None and pair_count > max_pairs:
        truncated = True
    report["complete"] = not truncated
    return report


def solve_compiled_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Search using compiled cR quartet nogoods.

    This is a consistency experiment for the nogood projection.  A returned
    witness is rechecked with the exact cR predicate before being exposed.
    """

    compilation = compile_cr_nogoods(
        D,
        pc_tree,
        max_p_degree=max_p_degree,
        limit=limit,
    )
    counts = {
        "assignments_seen": 0,
        "unique_frontiers_seen": 0,
        "accepted_frontiers": 0,
        "rejected_assignments": 0,
        "duplicate_frontiers": 0,
        "false_positive_frontiers": 0,
        "false_negative_frontiers": 0,
    }
    result = {
        "implemented": True,
        "solver": "compiled_cr_quartet_nogood_experiment",
        "exists": None,
        "order": None,
        "complete": compilation["complete"],
        "unsupported": compilation["encoding"]["unsupported"],
        "counts": counts,
        "accepted_frontiers": [],
        "first_disagreement": None,
        "compilation": compilation,
        "note": "experimental compiled nogood search; not a proved compact solver",
    }
    if result["unsupported"]:
        result["complete"] = False
        result["note"] = "unsupported local domain; no negative decision made"
        return result

    nogoods = compilation["nogoods"]
    seen_frontiers: set[tuple[int, ...]] = set()
    accepted: list[tuple[int, ...]] = []
    truncated = False
    for assignment in iter_local_assignments(
        compilation["encoding"],
        limit=None if limit is None else limit + 1,
    ):
        if limit is not None and counts["assignments_seen"] >= limit:
            truncated = True
            break
        counts["assignments_seen"] += 1
        rejected = any(_nogood_matches(assignment, nogood["signature"]) for nogood in nogoods)
        order = canonical_circular_order(frontier_from_assignment(pc_tree, assignment))
        exact = is_precircular_order_cR(D, order)
        if order in seen_frontiers:
            counts["duplicate_frontiers"] += 1
        else:
            seen_frontiers.add(order)
            counts["unique_frontiers_seen"] += 1

        if rejected:
            counts["rejected_assignments"] += 1
            if exact:
                counts["false_negative_frontiers"] += 1
                if result["first_disagreement"] is None:
                    result["first_disagreement"] = {
                        "kind": "false_negative",
                        "order": list(order),
                    }
            continue

        if not exact:
            counts["false_positive_frontiers"] += 1
            if result["first_disagreement"] is None:
                result["first_disagreement"] = {
                    "kind": "false_positive",
                    "order": list(order),
                }
            continue

        if order not in accepted:
            counts["accepted_frontiers"] += 1
            accepted.append(order)
            if result["order"] is None:
                result["order"] = list(order)

    result["complete"] = result["complete"] and not truncated
    result["exists"] = bool(accepted)
    result["accepted_frontiers"] = [list(order) for order in accepted]
    return result


def solve_compiled_bad_side_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    limit: Optional[int] = None,
) -> dict:
    """Search using compiled bad-side pair nogoods."""

    compilation = compile_bad_side_nogoods(
        D,
        pc_tree,
        max_p_degree=max_p_degree,
        limit=limit,
    )
    counts = {
        "assignments_seen": 0,
        "unique_frontiers_seen": 0,
        "accepted_frontiers": 0,
        "rejected_assignments": 0,
        "duplicate_frontiers": 0,
        "false_positive_frontiers": 0,
        "false_negative_frontiers": 0,
    }
    result = {
        "implemented": True,
        "solver": "compiled_bad_side_pair_nogood_experiment",
        "exists": None,
        "order": None,
        "complete": compilation["complete"],
        "unsupported": compilation["encoding"]["unsupported"],
        "counts": counts,
        "accepted_frontiers": [],
        "first_disagreement": None,
        "compilation": compilation,
        "note": "experimental compiled bad-side nogood search; not a proved compact solver",
    }
    if result["unsupported"]:
        result["complete"] = False
        result["note"] = "unsupported local domain; no negative decision made"
        return result

    nogoods = compilation["nogoods"]
    seen_frontiers: set[tuple[int, ...]] = set()
    accepted: list[tuple[int, ...]] = []
    truncated = False
    for assignment in iter_local_assignments(
        compilation["encoding"],
        limit=None if limit is None else limit + 1,
    ):
        if limit is not None and counts["assignments_seen"] >= limit:
            truncated = True
            break
        counts["assignments_seen"] += 1
        rejected = any(_nogood_matches(assignment, nogood["signature"]) for nogood in nogoods)
        order = canonical_circular_order(frontier_from_assignment(pc_tree, assignment))
        exact = is_precircular_order_cR(D, order)
        if order in seen_frontiers:
            counts["duplicate_frontiers"] += 1
        else:
            seen_frontiers.add(order)
            counts["unique_frontiers_seen"] += 1

        if rejected:
            counts["rejected_assignments"] += 1
            if exact:
                counts["false_negative_frontiers"] += 1
                if result["first_disagreement"] is None:
                    result["first_disagreement"] = {
                        "kind": "false_negative",
                        "order": list(order),
                    }
            continue

        if not exact:
            counts["false_positive_frontiers"] += 1
            if result["first_disagreement"] is None:
                result["first_disagreement"] = {
                    "kind": "false_positive",
                    "order": list(order),
                }
            continue

        if order not in accepted:
            counts["accepted_frontiers"] += 1
            accepted.append(order)
            if result["order"] is None:
                result["order"] = list(order)

    result["complete"] = result["complete"] and not truncated
    result["exists"] = bool(accepted)
    result["accepted_frontiers"] = [list(order) for order in accepted]
    return result


def _nogoods_by_last_path(nogoods: Sequence[dict], variable_order: Sequence[Path]) -> dict[Path, list[dict]]:
    position = {path: idx for idx, path in enumerate(variable_order)}
    indexed: dict[Path, list[dict]] = {path: [] for path in variable_order}
    for nogood in nogoods:
        paths = [path for path, _choice in nogood["signature"]]
        if not paths:
            continue
        last_path = max(paths, key=lambda path: position[path])
        indexed[last_path].append(nogood)
    return indexed


def _first_matching_completed_nogood(
    partial_assignment: Assignment,
    candidates: Sequence[dict],
) -> dict | None:
    for nogood in candidates:
        if _nogood_matches(partial_assignment, nogood["signature"]):
            return nogood
    return None


def solve_pruned_nogood_csp_from_compilation(
    D,
    pc_tree: PCNode,
    compilation: dict,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack through local domains using a precomputed compilation."""

    counts = {
        "nodes_visited": 0,
        "branches_considered": 0,
        "branches_pruned": 0,
        "leaf_assignments_seen": 0,
        "leaf_assignments_pruned_estimate": 0,
        "full_assignment_space": 0,
        "unique_frontiers_seen": 0,
        "duplicate_frontiers": 0,
        "accepted_frontiers": 0,
        "false_positive_frontiers": 0,
        "validation_false_positive_frontiers": 0,
        "validation_false_negative_frontiers": 0,
    }
    result = {
        "implemented": True,
        "solver": "pruned_cr_quartet_nogood_experiment",
        "exists": None,
        "order": None,
        "complete": compilation["complete"],
        "unsupported": compilation["encoding"]["unsupported"],
        "counts": counts,
        "accepted_frontiers": [],
        "first_pruned": None,
        "first_disagreement": None,
        "compilation": compilation,
        "note": "experimental post-compilation pruning; not a proved compact solver",
    }
    if result["unsupported"]:
        result["complete"] = False
        result["note"] = "unsupported local domain; no negative decision made"
        return result

    encoding = compilation["encoding"]
    variable_order = [variable["path"] for variable in encoding["variables"]]
    domain_sizes = [len(encoding["domains"][path]) for path in variable_order]
    suffix_products = [1] * (len(variable_order) + 1)
    for idx in range(len(variable_order) - 1, -1, -1):
        suffix_products[idx] = suffix_products[idx + 1] * domain_sizes[idx]
    counts["full_assignment_space"] = suffix_products[0]

    indexed_nogoods = _nogoods_by_last_path(compilation["nogoods"], variable_order)
    partial: Assignment = {}
    accepted: list[tuple[int, ...]] = []
    seen_frontiers: set[tuple[int, ...]] = set()

    def visit(depth: int) -> None:
        counts["nodes_visited"] += 1
        if depth == len(variable_order):
            counts["leaf_assignments_seen"] += 1
            order = canonical_circular_order(frontier_from_assignment(pc_tree, partial))
            if order in seen_frontiers:
                counts["duplicate_frontiers"] += 1
            else:
                seen_frontiers.add(order)
                counts["unique_frontiers_seen"] += 1

            exact = is_precircular_order_cR(D, order)
            if exact:
                if order not in accepted:
                    accepted.append(order)
                    counts["accepted_frontiers"] += 1
                    if result["order"] is None:
                        result["order"] = list(order)
            else:
                counts["false_positive_frontiers"] += 1
                if result["first_disagreement"] is None:
                    result["first_disagreement"] = {
                        "kind": "false_positive",
                        "order": list(order),
                    }
            return

        path = variable_order[depth]
        for choice in encoding["domains"][path]:
            counts["branches_considered"] += 1
            partial[path] = choice
            matched = _first_matching_completed_nogood(partial, indexed_nogoods[path])
            if matched is not None:
                counts["branches_pruned"] += 1
                counts["leaf_assignments_pruned_estimate"] += suffix_products[depth + 1]
                if result["first_pruned"] is None:
                    result["first_pruned"] = {
                        "path": path,
                        "choice": choice,
                        "nogood": matched,
                    }
                del partial[path]
                continue
            visit(depth + 1)
            del partial[path]

    visit(0)
    result["exists"] = bool(accepted)
    result["accepted_frontiers"] = [list(order) for order in accepted]
    result["counts"]["pruning_rate"] = (
        counts["branches_pruned"] / counts["branches_considered"]
        if counts["branches_considered"]
        else 0.0
    )

    if validate_against_direct:
        direct = accepted_frontiers_by_csp(D, pc_tree, source="cr", max_p_degree=max_p_degree)
        actual = {tuple(order) for order in result["accepted_frontiers"]}
        extra = actual - direct
        missing = direct - actual
        counts["validation_false_positive_frontiers"] = len(extra)
        counts["validation_false_negative_frontiers"] = len(missing)
        if (extra or missing) and result["first_disagreement"] is None:
            result["first_disagreement"] = {
                "kind": "validation_mismatch",
                "extra": [list(order) for order in sorted(extra)[:1]],
                "missing": [list(order) for order in sorted(missing)[:1]],
            }

    return result


def solve_pruned_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack through local domains and prune completed nogood signatures.

    Compilation still enumerates complete assignments.  The gain measured here
    is only in the post-compilation search phase.
    """

    compilation = compile_cr_nogoods(D, pc_tree, max_p_degree=max_p_degree)
    return solve_pruned_nogood_csp_from_compilation(
        D,
        pc_tree,
        compilation,
        max_p_degree=max_p_degree,
        validate_against_direct=validate_against_direct,
    )


def solve_pruned_bad_side_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack through local domains with compiled bad-side pair nogoods."""

    compilation = compile_bad_side_nogoods(D, pc_tree, max_p_degree=max_p_degree)
    result = solve_pruned_nogood_csp_from_compilation(
        D,
        pc_tree,
        compilation,
        max_p_degree=max_p_degree,
        validate_against_direct=validate_against_direct,
    )
    result["solver"] = "pruned_bad_side_pair_nogood_experiment"
    result["note"] = "experimental bad-side post-compilation pruning; not a proved compact solver"
    return result


def solve_support_local_bad_side_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack with bad-side nogoods compiled from support products."""

    compilation = compile_bad_side_nogoods_support_local(D, pc_tree, max_p_degree=max_p_degree)
    result = solve_pruned_nogood_csp_from_compilation(
        D,
        pc_tree,
        compilation,
        max_p_degree=max_p_degree,
        validate_against_direct=validate_against_direct,
    )
    result["solver"] = "support_local_bad_side_pair_nogood_experiment"
    result["note"] = "experimental support-local bad-side compilation; not a proved compact solver"
    return result


def solve_grouped_support_local_bad_side_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack with bad-side nogoods compiled by grouped supports."""

    compilation = compile_bad_side_nogoods_grouped_support_local(
        D,
        pc_tree,
        max_p_degree=max_p_degree,
    )
    result = solve_pruned_nogood_csp_from_compilation(
        D,
        pc_tree,
        compilation,
        max_p_degree=max_p_degree,
        validate_against_direct=validate_against_direct,
    )
    result["solver"] = "grouped_support_local_bad_side_pair_nogood_experiment"
    result["note"] = "experimental grouped-support bad-side compilation; not a proved compact solver"
    return result


def solve_grouped_first_hit_support_local_bad_side_nogood_csp(
    D,
    pc_tree: PCNode,
    *,
    max_p_degree: int = 3,
    validate_against_direct: bool = True,
) -> dict:
    """Backtrack with grouped first-hit bad-side nogoods."""

    compilation = compile_bad_side_nogoods_grouped_first_hit_support_local(
        D,
        pc_tree,
        max_p_degree=max_p_degree,
    )
    result = solve_pruned_nogood_csp_from_compilation(
        D,
        pc_tree,
        compilation,
        max_p_degree=max_p_degree,
        validate_against_direct=validate_against_direct,
    )
    result["solver"] = "grouped_first_hit_support_local_bad_side_pair_nogood_experiment"
    result["note"] = "experimental first-hit grouped-support bad-side compilation; not a proved compact solver"
    return result


def prop45_nogood_frontier_report(
    D,
    *,
    quasi_orders: Optional[Iterable[Order]] = None,
    pc_tree: Optional[PCNode] = None,
    limit: Optional[int] = None,
    require_quasi: bool = True,
) -> dict:
    """Compare the Prop. 4.5 fixed-order filter with exact cR on frontiers.

    The report is an experimental CSP scaffold: each Prop. 4.5 obstruction is
    treated as a nogood for the currently enumerated frontier.  It is still an
    enumeration-based diagnostic, not a compact PC-tree decision procedure.
    """

    n = validate_dissimilarity(D)
    orders, truncated = _materialize_orders(
        n,
        quasi_orders=quasi_orders,
        pc_tree=pc_tree,
        limit=limit,
    )

    counts = {
        "frontiers_seen": 0,
        "skipped_non_quasi": 0,
        "checked_orders": 0,
        "prop45_pass": 0,
        "prop45_fail": 0,
        "exact_cr": 0,
        "exact_non_cr": 0,
        "false_positive_prop45": 0,
        "false_negative_prop45": 0,
    }
    report = {
        "implemented": True,
        "method": "enumerated_frontier_prop45_nogood_filter",
        "complete": not truncated,
        "limit": limit,
        "require_quasi": require_quasi,
        "counts": counts,
        "witness_order": None,
        "first_rejected": None,
        "first_false_positive": None,
        "first_false_negative": None,
    }

    for order in orders:
        counts["frontiers_seen"] += 1
        if require_quasi and not is_quasi_circular_order(D, order):
            counts["skipped_non_quasi"] += 1
            continue

        counts["checked_orders"] += 1
        obstruction = find_farthest_prop_4_5_obstruction(D, order)
        prop45_passes = obstruction is None
        exact_cr = is_precircular_order_cR(D, order)

        if prop45_passes:
            counts["prop45_pass"] += 1
            if report["witness_order"] is None:
                report["witness_order"] = list(order)
        else:
            counts["prop45_fail"] += 1
            if report["first_rejected"] is None:
                report["first_rejected"] = {
                    "order": list(order),
                    "obstruction": obstruction,
                }

        if exact_cr:
            counts["exact_cr"] += 1
        else:
            counts["exact_non_cr"] += 1

        if prop45_passes and not exact_cr:
            counts["false_positive_prop45"] += 1
            if report["first_false_positive"] is None:
                report["first_false_positive"] = list(order)
        elif not prop45_passes and exact_cr:
            counts["false_negative_prop45"] += 1
            if report["first_false_negative"] is None:
                report["first_false_negative"] = {
                    "order": list(order),
                    "obstruction": obstruction,
                }

    report["prop45_exists"] = counts["prop45_pass"] > 0
    report["exact_cr_exists"] = counts["exact_cr"] > 0
    report["has_disagreement"] = bool(
        counts["false_positive_prop45"] or counts["false_negative_prop45"]
    )
    return report


def prop45_nogood_frontier_search(
    D,
    *,
    quasi_orders: Optional[Iterable[Order]] = None,
    pc_tree: Optional[PCNode] = None,
    limit: Optional[int] = None,
    require_quasi: bool = True,
) -> dict:
    """Return the first frontier accepted by the Prop. 4.5 nogood filter."""

    report = prop45_nogood_frontier_report(
        D,
        quasi_orders=quasi_orders,
        pc_tree=pc_tree,
        limit=limit,
        require_quasi=require_quasi,
    )
    return {
        "exists": report["prop45_exists"],
        "order": report["witness_order"],
        "complete": report["complete"],
        "solver": "prop45_nogood_frontier_experiment",
        "note": "experimental fixed-order nogood filter; not a proved PC-tree solver",
        "report": report,
    }
