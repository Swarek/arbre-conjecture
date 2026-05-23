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


def small_paper_like_instances() -> list[list[list[int]]]:
    """Small named examples; extend with paper-derived cases when available."""

    return [
        cycle_metric(4),
        quasi_circular_not_circular_four_point(),
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
