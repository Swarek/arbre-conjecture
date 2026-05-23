"""Tiny exhaustive unrooted PC-tree model for very small leaf sets.

This is an independent checker for research probes.  It enumerates labelled
unrooted tree topologies through Prüfer sequences, filters leaves/internal
degrees, assigns P/C node types and C-node cyclic orders, then enumerates the
frontiers induced by all allowed embeddings.

The implementation is intentionally bounded and aimed at ``n <= 5``.  It is
not a production Hsu/McConnell implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product
from math import factorial
from typing import Iterable, Sequence

from .predicates import canonical_circular_order


@dataclass(frozen=True)
class UnrootedPCRepresentabilityReport:
    representable: bool
    complete: bool
    witness: str | None
    target_size: int
    candidate_count: int
    family_count: int
    max_candidates: int
    empty_target: bool = False


def _canonical_circular_orders(values: Sequence[int]) -> list[tuple[int, ...]]:
    values = tuple(sorted(values))
    if len(values) <= 2:
        return [values]
    anchor = values[0]
    result = []
    for perm in permutations(values[1:]):
        order = (anchor, *perm)
        reverse = (anchor, *reversed(perm))
        if order <= reverse:
            result.append(order)
    return result


def _tree_from_prufer(sequence: tuple[int, ...], node_count: int) -> tuple[tuple[int, ...], ...]:
    degree = [1] * node_count
    for value in sequence:
        degree[value] += 1

    adjacency = [set() for _ in range(node_count)]
    leaves = [idx for idx, value in enumerate(degree) if value == 1]
    leaves.sort()
    for value in sequence:
        leaf = leaves.pop(0)
        adjacency[leaf].add(value)
        adjacency[value].add(leaf)
        degree[leaf] -= 1
        degree[value] -= 1
        if degree[value] == 1:
            insert_at = 0
            while insert_at < len(leaves) and leaves[insert_at] < value:
                insert_at += 1
            leaves.insert(insert_at, value)

    a, b = leaves
    adjacency[a].add(b)
    adjacency[b].add(a)
    return tuple(tuple(sorted(neighbors)) for neighbors in adjacency)


def _valid_leaf_internal_tree(
    adjacency: tuple[tuple[int, ...], ...],
    leaf_count: int,
) -> bool:
    for node, neighbors in enumerate(adjacency):
        if node < leaf_count:
            if len(neighbors) != 1:
                return False
        elif len(neighbors) < 3:
            return False
    return True


def _iter_topologies(leaf_count: int) -> Iterable[tuple[tuple[int, ...], ...]]:
    seen = set()
    for internal_count in range(1, max(1, leaf_count - 1)):
        node_count = leaf_count + internal_count
        for sequence in product(range(node_count), repeat=node_count - 2):
            adjacency = _tree_from_prufer(tuple(sequence), node_count)
            if not _valid_leaf_internal_tree(adjacency, leaf_count):
                continue
            key = tuple(sorted((node, tuple(neighbors)) for node, neighbors in enumerate(adjacency)))
            if key in seen:
                continue
            seen.add(key)
            yield adjacency


def _embedding_family(
    adjacency: tuple[tuple[int, ...], ...],
    leaf_count: int,
    internal_types: dict[int, str],
    c_orders: dict[int, tuple[int, ...]],
) -> frozenset[tuple[int, ...]]:
    choices = []
    for node in range(leaf_count, len(adjacency)):
        neighbors = adjacency[node]
        if internal_types[node] == "P":
            choices.append([(node, order) for order in _canonical_circular_orders(neighbors)])
        else:
            order = c_orders[node]
            choices.append([(node, order), (node, tuple(reversed(order)))])

    family = set()
    leaf_orders = {leaf: adjacency[leaf] for leaf in range(leaf_count)}
    for embedding_parts in product(*choices):
        cyclic_orders = dict(leaf_orders)
        cyclic_orders.update(dict(embedding_parts))
        order = _frontier_from_embedding(adjacency, leaf_count, cyclic_orders)
        family.add(canonical_circular_order(order))
    return frozenset(family)


def _frontier_from_embedding(
    adjacency: tuple[tuple[int, ...], ...],
    leaf_count: int,
    cyclic_orders: dict[int, tuple[int, ...]],
) -> tuple[int, ...]:
    start = (0, adjacency[0][0])
    dart = start
    result = []
    seen = set()
    while dart not in seen:
        seen.add(dart)
        previous, current = dart
        if current < leaf_count:
            result.append(current)
        order = cyclic_orders[current]
        index = order.index(previous)
        next_node = order[(index - 1) % len(order)]
        dart = (current, next_node)
    return tuple(result)


def _topology_descriptor(
    adjacency: tuple[tuple[int, ...], ...],
    internal_types: dict[int, str],
    c_orders: dict[int, tuple[int, ...]],
) -> str:
    edges = []
    for node, neighbors in enumerate(adjacency):
        for neighbor in neighbors:
            if node < neighbor:
                edges.append((node, neighbor))
    types = ",".join(f"{node}:{internal_types[node]}" for node in sorted(internal_types))
    c_data = ",".join(f"{node}:{c_orders[node]}" for node in sorted(c_orders))
    return f"edges={edges}; types={types}; c_orders={c_data}"


def find_unrooted_pc_representation(
    labels: Sequence[int],
    target_orders: Iterable[Sequence[int]],
    *,
    max_candidates: int = 500_000,
) -> UnrootedPCRepresentabilityReport:
    """Search all tiny unrooted PC-tree families for ``target_orders``."""

    label_tuple = tuple(sorted(labels))
    if label_tuple != tuple(range(len(label_tuple))):
        raise ValueError("unrooted checker currently expects labels 0..n-1")

    target = frozenset(canonical_circular_order(order) for order in target_orders)
    if not target:
        return UnrootedPCRepresentabilityReport(
            representable=False,
            complete=True,
            witness=None,
            target_size=0,
            candidate_count=0,
            family_count=0,
            max_candidates=max_candidates,
            empty_target=True,
        )

    candidate_count = 0
    families = set()
    leaf_count = len(label_tuple)
    for adjacency in _iter_topologies(leaf_count):
        internal_nodes = tuple(range(leaf_count, len(adjacency)))
        for type_values in product(("P", "C"), repeat=len(internal_nodes)):
            internal_types = dict(zip(internal_nodes, type_values))
            c_nodes = [node for node in internal_nodes if internal_types[node] == "C"]
            c_order_options = [
                _canonical_circular_orders(adjacency[node]) for node in c_nodes
            ]
            for c_order_values in product(*c_order_options):
                candidate_count += 1
                if candidate_count > max_candidates:
                    return UnrootedPCRepresentabilityReport(
                        representable=False,
                        complete=False,
                        witness=None,
                        target_size=len(target),
                        candidate_count=candidate_count,
                        family_count=len(families),
                        max_candidates=max_candidates,
                    )
                c_orders = dict(zip(c_nodes, c_order_values))
                family = _embedding_family(adjacency, leaf_count, internal_types, c_orders)
                families.add(family)
                if family == target:
                    return UnrootedPCRepresentabilityReport(
                        representable=True,
                        complete=True,
                        witness=_topology_descriptor(adjacency, internal_types, c_orders),
                        target_size=len(target),
                        candidate_count=candidate_count,
                        family_count=len(families),
                        max_candidates=max_candidates,
                    )

    return UnrootedPCRepresentabilityReport(
        representable=False,
        complete=True,
        witness=None,
        target_size=len(target),
        candidate_count=candidate_count,
        family_count=len(families),
        max_candidates=max_candidates,
    )


def circular_order_count(n: int) -> int:
    return 1 if n <= 2 else factorial(n - 1) // 2
