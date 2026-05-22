"""Scratch space for SAT/CSP-style encodings of cyclic constraints.

Nothing in this module is a proved general solver.  The functions below are
frontier-enumeration experiments that treat Proposition 4.5 obstructions as
nogoods on fixed orders, then compare the resulting filter with the exact cR
predicate.  This gives Piste C falsifiable data before a real variable-level
PC-tree encoding is attempted.
"""

from __future__ import annotations

from itertools import islice, permutations, product
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
