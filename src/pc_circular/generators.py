"""Instance generators for correctness tests and benchmarks."""

from __future__ import annotations

import random
from typing import Sequence

from .pc_tree import balanced_pc_tree, pc_tree_from_kind, star_pc_tree


MIXED_INSTANCE_KINDS = (
    "random",
    "cycle",
    "block",
    "ultrametric",
    "equal",
    "non_strict",
)


def _zero_matrix(n: int) -> list[list[int]]:
    return [[0 for _ in range(n)] for _ in range(n)]


def random_dissimilarity(
    n: int,
    *,
    values: Sequence[int] = (1, 2, 3),
    rng: random.Random | None = None,
) -> list[list[int]]:
    rng = rng or random.Random()
    D = _zero_matrix(n)
    for i in range(n):
        for j in range(i + 1, n):
            value = int(rng.choice(values))
            D[i][j] = D[j][i] = value
    return D


def cycle_metric(n: int) -> list[list[int]]:
    D = _zero_matrix(n)
    for i in range(n):
        for j in range(i + 1, n):
            value = min((j - i) % n, (i - j) % n)
            D[i][j] = D[j][i] = value
    return D


def _permute_labels(D: list[list[int]], *, rng: random.Random | None = None) -> list[list[int]]:
    rng = rng or random.Random()
    n = len(D)
    labels = list(range(n))
    rng.shuffle(labels)
    permuted = _zero_matrix(n)
    for hidden_i, label_i in enumerate(labels):
        for hidden_j, label_j in enumerate(labels):
            permuted[label_i][label_j] = D[hidden_i][hidden_j]
    return permuted


def permuted_cycle_metric(n: int, *, rng: random.Random | None = None) -> list[list[int]]:
    """Cycle metric with a hidden planted circular order."""

    return _permute_labels(cycle_metric(n), rng=rng)


def block_cycle(n: int, *, blocks: int | None = None) -> list[list[int]]:
    blocks = blocks or max(2, min(5, n // 2 or 1))
    block_of = [min(blocks - 1, i * blocks // n) for i in range(n)]
    D = _zero_matrix(n)
    for i in range(n):
        for j in range(i + 1, n):
            if block_of[i] == block_of[j]:
                value = 1
            else:
                delta = abs(block_of[i] - block_of[j])
                value = 1 + min(delta, blocks - delta)
            D[i][j] = D[j][i] = value
    return D


def ultrametric(n: int) -> list[list[int]]:
    D = _zero_matrix(n)
    for i in range(n):
        for j in range(i + 1, n):
            value = max(1, (i ^ j).bit_length())
            D[i][j] = D[j][i] = value
    return D


def quasi_positive_example(n: int) -> list[list[int]]:
    return cycle_metric(n)


def equal_distance_instance(n: int, *, value: int = 1) -> list[list[int]]:
    D = _zero_matrix(n)
    for i in range(n):
        for j in range(i + 1, n):
            D[i][j] = D[j][i] = value
    return D


def non_strict_large_farthest_instance(n: int) -> list[list[int]]:
    if n <= 3:
        return equal_distance_instance(n)
    D = equal_distance_instance(n, value=1)
    half = n // 2
    for i in range(half):
        for j in range(half, n):
            D[i][j] = D[j][i] = 2
    return D


def paired_farthest_matching(n: int, *, rng: random.Random | None = None) -> list[list[int]]:
    """Hard-looking family with planted unique farthest pairs.

    For even ``n=2m``, hidden labels are paired ``A_i, B_i``.  Paired points
    have distance 3, same-side points have distance 1, and cross-pair points
    have distance 2.  For odd ``n``, one neutral point is added at distance 1
    from all others.
    """

    if n <= 1:
        return _zero_matrix(n)

    D = _zero_matrix(n)
    paired_n = n if n % 2 == 0 else n - 1
    neutral = n - 1 if n % 2 == 1 else None
    side = {}
    pair = {}
    for i in range(paired_n // 2):
        a = 2 * i
        b = 2 * i + 1
        side[a] = "A"
        side[b] = "B"
        pair[a] = pair[b] = i

    for i in range(n):
        for j in range(i + 1, n):
            if neutral is not None and (i == neutral or j == neutral):
                value = 1
            elif pair[i] == pair[j]:
                value = 3
            elif side[i] == side[j]:
                value = 1
            else:
                value = 2
            D[i][j] = D[j][i] = value
    return _permute_labels(D, rng=rng)


def quasi_circular_not_circular_four_point() -> list[list[int]]:
    return [
        [0, 2, 1, 1],
        [2, 0, 1, 2],
        [1, 1, 0, 2],
        [1, 2, 2, 0],
    ]


def four_local_non_cr_core() -> list[list[int]]:
    """Five-point obstruction whose every four-point induced submatrix is cR."""

    return [
        [0, 1, 1, 2, 2],
        [1, 0, 2, 1, 2],
        [1, 2, 0, 1, 2],
        [2, 1, 1, 0, 2],
        [2, 2, 2, 2, 0],
    ]


def padded_four_local_non_cr(n: int) -> list[list[int]]:
    """Pad the five-point four-local obstruction to larger sizes.

    Added labels are at distance 2 from the core and distance 1 from each
    other.  The core remains an induced non-cR obstruction, while all four-point
    restrictions stay cR in the tested scaffold.
    """

    if n < 5:
        raise ValueError("padded_four_local_non_cr requires n >= 5")
    D = _zero_matrix(n)
    core = four_local_non_cr_core()
    for i in range(5):
        for j in range(5):
            D[i][j] = core[i][j]
    for i in range(n):
        for j in range(i + 1, n):
            if i < 5 and j < 5:
                continue
            value = 1 if i >= 5 and j >= 5 else 2
            D[i][j] = D[j][i] = value
    return D


def five_local_non_cr_core() -> list[list[int]]:
    """Six-point obstruction whose every five-point induced submatrix is cR."""

    return [
        [0, 1, 1, 1, 1, 1],
        [1, 0, 1, 1, 2, 2],
        [1, 1, 0, 2, 1, 2],
        [1, 1, 2, 0, 2, 1],
        [1, 2, 1, 2, 0, 1],
        [1, 2, 2, 1, 1, 0],
    ]


def padded_five_local_non_cr(n: int) -> list[list[int]]:
    """Pad the six-point five-local obstruction to larger sizes."""

    if n < 6:
        raise ValueError("padded_five_local_non_cr requires n >= 6")
    D = _zero_matrix(n)
    core = five_local_non_cr_core()
    for i in range(6):
        for j in range(6):
            D[i][j] = core[i][j]
    for i in range(n):
        for j in range(i + 1, n):
            if i < 6 and j < 6:
                continue
            D[i][j] = D[j][i] = 1
    return D


def odd_high_cycle_plus_low_hub(n: int) -> list[list[int]]:
    """Binary family: an odd high-distance cycle plus one low universal hub."""

    cycle_size = n - 1
    if cycle_size < 5 or cycle_size % 2 == 0:
        raise ValueError("odd_high_cycle_plus_low_hub requires n-1 odd and at least 5")
    D = equal_distance_instance(n, value=1)
    for offset in range(cycle_size):
        a = 1 + offset
        b = 1 + ((offset + 1) % cycle_size)
        D[a][b] = D[b][a] = 2
    return D


def even_high_cycle_plus_low_hub(n: int) -> list[list[int]]:
    """Binary family: an even high-distance cycle plus one low universal hub."""

    cycle_size = n - 1
    if cycle_size < 6 or cycle_size % 2 != 0:
        raise ValueError("even_high_cycle_plus_low_hub requires n-1 even and at least 6")
    D = equal_distance_instance(n, value=1)
    for offset in range(cycle_size):
        a = 1 + offset
        b = 1 + ((offset + 1) % cycle_size)
        D[a][b] = D[b][a] = 2
    return D


def non_bipartite_high_graph_plus_low_hub(n: int) -> list[list[int]]:
    """Binary family: a non-bipartite high graph plus one low universal hub."""

    if n < 4:
        raise ValueError("non_bipartite_high_graph_plus_low_hub requires n >= 4")
    D = equal_distance_instance(n, value=1)
    high_edges = [(1, 2), (2, 3), (1, 3)]
    high_edges.extend((label - 1, label) for label in range(4, n))
    for a, b in high_edges:
        D[a][b] = D[b][a] = 2
    return D


def complete_bipartite_high_graph_plus_low_hub(n: int) -> list[list[int]]:
    """Binary family: complete bipartite high graph plus one low hub."""

    if n < 5:
        raise ValueError("complete_bipartite_high_graph_plus_low_hub requires n >= 5")
    D = equal_distance_instance(n, value=1)
    split = 1 + (n - 1) // 2
    for a in range(1, split):
        for b in range(split, n):
            D[a][b] = D[b][a] = 2
    return D


def chain_high_graph_plus_low_hub(n: int) -> list[list[int]]:
    """Binary family: nested-neighborhood high graph plus one low hub."""

    if n < 5:
        raise ValueError("chain_high_graph_plus_low_hub requires n >= 5")
    D = equal_distance_instance(n, value=1)
    split = 1 + (n - 1) // 2
    left = list(range(1, split))
    right = list(range(split, n))
    for index, a in enumerate(left):
        degree = max(1, len(right) - index)
        for b in right[:degree]:
            D[a][b] = D[b][a] = 2
    return D


def small_paper_like_instances() -> list[list[list[int]]]:
    """Small named examples; extend with paper-derived cases when available."""

    return [
        cycle_metric(4),
        quasi_circular_not_circular_four_point(),
        four_local_non_cr_core(),
        five_local_non_cr_core(),
        odd_high_cycle_plus_low_hub(6),
        even_high_cycle_plus_low_hub(7),
        non_bipartite_high_graph_plus_low_hub(6),
        complete_bipartite_high_graph_plus_low_hub(6),
        chain_high_graph_plus_low_hub(6),
        non_strict_large_farthest_instance(5),
    ]


def mixed_instance(
    n: int,
    *,
    rng: random.Random | None = None,
    values: Sequence[int] = (1, 2, 3),
) -> list[list[int]]:
    D, _metadata = instance_by_kind_with_metadata(n, kind="mixed", rng=rng, values=values)
    return D


def instance_by_kind_with_metadata(
    n: int,
    *,
    kind: str,
    rng: random.Random | None = None,
    values: Sequence[int] = (1, 2, 3),
) -> tuple[list[list[int]], dict[str, str]]:
    """Generate an instance and expose the resolved subfamily.

    For ``kind="mixed"``, this preserves the exact RNG draw sequence of
    ``mixed_instance`` while making the chosen subfamily visible to benchmarks.
    """

    rng = rng or random.Random()
    if kind == "mixed":
        resolved_kind = rng.choice(MIXED_INSTANCE_KINDS)
        D = instance_by_kind(n, kind=resolved_kind, rng=rng, values=values)
    else:
        resolved_kind = kind
        D = instance_by_kind(n, kind=kind, rng=rng, values=values)
    return D, {"requested_kind": kind, "resolved_kind": resolved_kind}


def instance_by_kind(
    n: int,
    *,
    kind: str,
    rng: random.Random | None = None,
    values: Sequence[int] = (1, 2, 3),
) -> list[list[int]]:
    if kind == "random":
        return random_dissimilarity(n, values=values, rng=rng)
    if kind == "cycle":
        return cycle_metric(n)
    if kind == "permuted_cycle":
        return permuted_cycle_metric(n, rng=rng)
    if kind == "block":
        return block_cycle(n)
    if kind == "ultrametric":
        return ultrametric(n)
    if kind in {"equal", "equal-distance"}:
        return equal_distance_instance(n)
    if kind == "non_strict":
        return non_strict_large_farthest_instance(n)
    if kind == "paired_farthest":
        return paired_farthest_matching(n, rng=rng)
    if kind in {"four_local_non_cr", "padded_four_local_non_cr"}:
        return padded_four_local_non_cr(n)
    if kind in {"five_local_non_cr", "padded_five_local_non_cr"}:
        return padded_five_local_non_cr(n)
    if kind == "odd_high_cycle_plus_low_hub":
        return odd_high_cycle_plus_low_hub(n)
    if kind == "even_high_cycle_plus_low_hub":
        return even_high_cycle_plus_low_hub(n)
    if kind == "non_bipartite_high_graph_plus_low_hub":
        return non_bipartite_high_graph_plus_low_hub(n)
    if kind == "complete_bipartite_high_graph_plus_low_hub":
        return complete_bipartite_high_graph_plus_low_hub(n)
    if kind == "chain_high_graph_plus_low_hub":
        return chain_high_graph_plus_low_hub(n)
    if kind == "mixed":
        return mixed_instance(n, rng=rng, values=values)
    raise ValueError(f"unknown instance kind: {kind}")


def pc_tree_star(n: int):
    return star_pc_tree(n)


def pc_tree_balanced(n: int):
    return balanced_pc_tree(n, kind="C")


def pc_tree_mixed(n: int):
    return balanced_pc_tree(n, kind="mixed")


def benchmark_pc_tree(kind: str, n: int):
    return pc_tree_from_kind(kind, n)
