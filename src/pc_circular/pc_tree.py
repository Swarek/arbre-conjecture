"""Small PC-tree representation and exact frontier enumeration.

This is a research scaffold, not a full Hsu/McConnell implementation.  It is
enough to represent hand-built P/C trees, enumerate small frontiers exactly,
and generate benchmark trees.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product, permutations
from typing import Iterable, Optional, Sequence

from .predicates import canonical_circular_order


@dataclass(frozen=True)
class PCNode:
    kind: str
    children: tuple["PCNode", ...] = ()
    label: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "children", tuple(self.children))
        if self.kind == "leaf":
            if self.label is None or self.children:
                raise ValueError("leaf nodes need a label and no children")
        elif self.kind in {"P", "C"}:
            if self.label is not None or not self.children:
                raise ValueError("P/C nodes need children and no label")
        else:
            raise ValueError("kind must be 'leaf', 'P', or 'C'")


def leaf(label: int) -> PCNode:
    return PCNode("leaf", label=label)


def p_node(children: Sequence[PCNode]) -> PCNode:
    return PCNode("P", tuple(children))


def c_node(children: Sequence[PCNode]) -> PCNode:
    return PCNode("C", tuple(children))


def labels(node: PCNode) -> tuple[int, ...]:
    if node.kind == "leaf":
        assert node.label is not None
        return (node.label,)
    result: list[int] = []
    for child in node.children:
        result.extend(labels(child))
    if len(result) != len(set(result)):
        raise ValueError("PC-tree leaves must have distinct labels")
    return tuple(result)


def _all_circular_orders_for_labels(values: Sequence[int]) -> Iterable[tuple[int, ...]]:
    values = tuple(sorted(values))
    if len(values) <= 1:
        yield values
        return
    if len(values) == 2:
        yield values
        return

    anchor = values[0]
    rest = values[1:]
    for perm in permutations(rest):
        order = (anchor, *perm)
        reversed_order = (anchor, *reversed(perm))
        if order <= reversed_order:
            yield order


def _is_leaf_star(node: PCNode) -> bool:
    return node.kind == "P" and all(child.kind == "leaf" for child in node.children)


def _linear_frontiers(node: PCNode) -> Iterable[tuple[int, ...]]:
    if node.kind == "leaf":
        assert node.label is not None
        yield (node.label,)
        return

    child_frontiers = [tuple(_linear_frontiers(child)) for child in node.children]
    if node.kind == "P":
        orders = permutations(range(len(node.children)))
    else:
        forward = tuple(range(len(node.children)))
        backward = tuple(reversed(forward))
        orders = (forward,) if forward == backward else (forward, backward)

    for child_order in orders:
        for parts in product(*(child_frontiers[idx] for idx in child_order)):
            merged: list[int] = []
            for part in parts:
                merged.extend(part)
            yield tuple(merged)


def sample_frontier(node: PCNode) -> tuple[int, ...]:
    """Return one represented frontier without enumerating alternatives."""

    if node.kind == "leaf":
        assert node.label is not None
        return (node.label,)

    merged: list[int] = []
    for child in node.children:
        merged.extend(sample_frontier(child))
    return tuple(merged)


def enumerate_frontiers(
    node: PCNode,
    *,
    canonical: bool = True,
    limit: Optional[int] = None,
) -> list[tuple[int, ...]]:
    """Enumerate represented circular orders.

    Enumeration is exact until ``limit`` is reached.  The optimized star case
    avoids generating all rotations before canonicalization.
    """

    if limit is not None and limit <= 0:
        return []

    raw_iter: Iterable[tuple[int, ...]]
    if canonical and _is_leaf_star(node):
        raw_iter = _all_circular_orders_for_labels(labels(node))
    else:
        raw_iter = _linear_frontiers(node)

    seen: set[tuple[int, ...]] = set()
    result: list[tuple[int, ...]] = []
    for frontier in raw_iter:
        key = canonical_circular_order(frontier) if canonical else tuple(frontier)
        if key in seen:
            continue
        seen.add(key)
        result.append(key)
        if limit is not None and len(result) >= limit:
            break
    return result


def _represents_linear_frontier(node: PCNode, seq: tuple[int, ...]) -> bool:
    if node.kind == "leaf":
        return len(seq) == 1 and seq[0] == node.label

    child_label_sets = [set(labels(child)) for child in node.children]
    label_to_child: dict[int, int] = {}
    for idx, child_labels in enumerate(child_label_sets):
        for label in child_labels:
            label_to_child[label] = idx

    chunks: list[tuple[int, tuple[int, ...]]] = []
    seen_children: set[int] = set()
    current_child: int | None = None
    current_chunk: list[int] = []
    for label in seq:
        child_idx = label_to_child.get(label)
        if child_idx is None:
            return False
        if child_idx != current_child:
            if child_idx in seen_children:
                return False
            if current_child is not None:
                chunks.append((current_child, tuple(current_chunk)))
            seen_children.add(child_idx)
            current_child = child_idx
            current_chunk = [label]
        else:
            current_chunk.append(label)

    if current_child is not None:
        chunks.append((current_child, tuple(current_chunk)))
    if len(chunks) != len(node.children):
        return False

    child_order = tuple(child_idx for child_idx, _ in chunks)
    if set(child_order) != set(range(len(node.children))):
        return False
    if node.kind == "C":
        forward = tuple(range(len(node.children)))
        backward = tuple(reversed(forward))
        if child_order != forward and child_order != backward:
            return False

    return all(_represents_linear_frontier(node.children[child_idx], chunk) for child_idx, chunk in chunks)


def _rotations(seq: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
    for idx in range(len(seq)):
        yield seq[idx:] + seq[:idx]


def represents_order(node: PCNode, order: Sequence[int], *, limit: Optional[int] = None) -> bool:
    """Check whether ``order`` is represented by the scaffold PC-tree.

    With ``limit`` this preserves the old bounded-enumeration diagnostic.  When
    no limit is given, membership is checked by parsing the fixed order into
    child blocks and testing only root rotations/reversal, avoiding frontier
    enumeration.
    """

    if limit is not None:
        target = canonical_circular_order(order)
        return target in set(enumerate_frontiers(node, canonical=True, limit=limit))

    seq = tuple(order)
    node_labels = labels(node)
    if len(seq) != len(node_labels) or set(seq) != set(node_labels):
        return False

    seen: set[tuple[int, ...]] = set()
    for oriented in (seq, tuple(reversed(seq))):
        for rotated in _rotations(oriented):
            if rotated in seen:
                continue
            seen.add(rotated)
            if _represents_linear_frontier(node, rotated):
                return True
    return False


def star_pc_tree(n: int) -> PCNode:
    if n <= 0:
        raise ValueError("n must be positive")
    if n == 1:
        return leaf(0)
    return p_node([leaf(i) for i in range(n)])


def balanced_pc_tree(n: int, *, fanout: int = 2, kind: str = "mixed") -> PCNode:
    if n <= 0:
        raise ValueError("n must be positive")
    if fanout < 2:
        raise ValueError("fanout must be at least 2")

    def build(items: Sequence[int], depth: int) -> PCNode:
        if len(items) == 1:
            return leaf(items[0])
        chunk_size = max(1, (len(items) + fanout - 1) // fanout)
        chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
        children = [build(chunk, depth + 1) for chunk in chunks]
        if kind in {"P", "C"}:
            node_kind = kind
        elif kind == "mixed":
            node_kind = "P" if depth % 2 else "C"
        else:
            raise ValueError("kind must be 'P', 'C', or 'mixed'")
        return PCNode(node_kind, tuple(children))

    return build(tuple(range(n)), 0)


def pc_tree_from_kind(kind: str, n: int) -> PCNode:
    if kind == "star":
        return star_pc_tree(n)
    if kind == "balanced":
        return balanced_pc_tree(n, kind="C")
    if kind == "mixed":
        return balanced_pc_tree(n, kind="mixed")
    raise ValueError(f"unknown PC-tree kind: {kind}")
