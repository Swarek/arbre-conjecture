"""Instance generators for correctness tests and benchmarks."""

from __future__ import annotations

import random
from typing import Sequence

from .pc_tree import balanced_pc_tree, pc_tree_from_kind, star_pc_tree


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
    rng = rng or random.Random()
    choices = [
        "random",
        "cycle",
        "block",
        "ultrametric",
        "equal",
        "non_strict",
    ]
    kind = rng.choice(choices)
    return instance_by_kind(n, kind=kind, rng=rng, values=values)


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
    if kind == "block":
        return block_cycle(n)
    if kind == "ultrametric":
        return ultrametric(n)
    if kind in {"equal", "equal-distance"}:
        return equal_distance_instance(n)
    if kind == "non_strict":
        return non_strict_large_farthest_instance(n)
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
