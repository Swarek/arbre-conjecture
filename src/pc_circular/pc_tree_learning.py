"""Bounded learners for PC-tree frontier families.

This module is deliberately small and exact only inside the rooted ``PCNode``
scaffold used by the repository.  It is not a Hsu/McConnell PC-tree learner.
The goal is to falsify or support hypotheses on small instances while keeping
all caps and incompleteness visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product, permutations
from math import factorial
from typing import Iterable, Sequence

from .predicates import canonical_circular_order


LinearFamily = frozenset[tuple[int, ...]]
CircularFamily = frozenset[tuple[int, ...]]


@dataclass(frozen=True)
class ScaffoldPCRepresentabilityReport:
    """Result of a bounded exact search in the repository's ``PCNode`` grammar."""

    representable: bool
    complete: bool
    witness: str | None
    target_size: int
    all_order_count: int
    linear_family_count: int
    canonical_family_count: int
    subset_family_counts: dict[str, int]
    overflow_subsets: tuple[tuple[int, ...], ...]
    empty_target: bool = False


def _set_partitions(items: tuple[int, ...]) -> Iterable[tuple[tuple[int, ...], ...]]:
    if not items:
        yield ()
        return

    first = items[0]
    for partition in _set_partitions(items[1:]):
        yield ((first,), *partition)
        for idx in range(len(partition)):
            block = tuple(sorted((first, *partition[idx])))
            candidate = partition[:idx] + (block,) + partition[idx + 1 :]
            yield tuple(sorted(candidate, key=lambda values: (values[0], len(values), values)))


def _unique_set_partitions(items: tuple[int, ...]) -> list[tuple[tuple[int, ...], ...]]:
    seen = set()
    result = []
    for partition in _set_partitions(items):
        key = tuple(sorted((tuple(block) for block in partition), key=lambda values: values))
        if key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def _concat(parts: Sequence[tuple[int, ...]]) -> tuple[int, ...]:
    merged: list[int] = []
    for part in parts:
        merged.extend(part)
    return tuple(merged)


def _p_family(child_families: Sequence[LinearFamily]) -> LinearFamily:
    result = set()
    for child_order in permutations(range(len(child_families))):
        for parts in product(*(child_families[idx] for idx in child_order)):
            result.add(_concat(parts))
    return frozenset(result)


def _c_family(child_families: Sequence[LinearFamily], order: tuple[int, ...]) -> LinearFamily:
    result = set()
    for child_order in (order, tuple(reversed(order))):
        for parts in product(*(child_families[idx] for idx in child_order)):
            result.add(_concat(parts))
    return frozenset(result)


def _canonical_c_family_orders(count: int) -> Iterable[tuple[int, ...]]:
    for order in permutations(range(count)):
        reverse = tuple(reversed(order))
        if order <= reverse:
            yield order


def _family_descriptor(kind: str, child_descriptors: Sequence[str]) -> str:
    if kind == "P":
        return "P(" + ",".join(sorted(child_descriptors)) + ")"
    return "C(" + ",".join(child_descriptors) + ")"


def _linear_families_for_subset(
    subset: tuple[int, ...],
    *,
    memo: dict[tuple[int, ...], tuple[dict[LinearFamily, str], bool, set[tuple[int, ...]]]],
    max_families_per_subset: int,
) -> tuple[dict[LinearFamily, str], bool, set[tuple[int, ...]]]:
    if subset in memo:
        return memo[subset]

    if len(subset) == 1:
        family = frozenset({subset})
        result = ({family: f"L{subset[0]}"}, True, set())
        memo[subset] = result
        return result

    families: dict[LinearFamily, str] = {}
    complete = True
    overflow_subsets: set[tuple[int, ...]] = set()

    def add_family(family: LinearFamily, descriptor: str) -> None:
        nonlocal complete
        if family in families:
            return
        if len(families) >= max_families_per_subset:
            complete = False
            overflow_subsets.add(subset)
            return
        families[family] = descriptor

    for partition in _unique_set_partitions(subset):
        if len(partition) < 2:
            continue
        child_reports = [
            _linear_families_for_subset(
                block, memo=memo, max_families_per_subset=max_families_per_subset
            )
            for block in partition
        ]
        for _, child_complete, child_overflows in child_reports:
            complete = complete and child_complete
            overflow_subsets.update(child_overflows)

        child_maps = [report[0] for report in child_reports]
        for child_items in product(*(child_map.items() for child_map in child_maps)):
            child_families = [item[0] for item in child_items]
            child_descriptors = [item[1] for item in child_items]

            add_family(
                _p_family(child_families),
                _family_descriptor("P", child_descriptors),
            )

            for child_order in _canonical_c_family_orders(len(child_families)):
                ordered_families = [child_families[idx] for idx in child_order]
                ordered_descriptors = [child_descriptors[idx] for idx in child_order]
                add_family(
                    _c_family(ordered_families, tuple(range(len(ordered_families)))),
                    _family_descriptor("C", ordered_descriptors),
                )

    result = (families, complete, overflow_subsets)
    memo[subset] = result
    return result


def circularize_linear_family(family: LinearFamily) -> CircularFamily:
    return frozenset(canonical_circular_order(order) for order in family)


@lru_cache(maxsize=16)
def _linear_families_for_labels(
    label_tuple: tuple[int, ...],
    max_families_per_subset: int,
) -> tuple[
    dict[LinearFamily, str],
    bool,
    tuple[tuple[int, ...], ...],
    dict[str, int],
]:
    memo: dict[tuple[int, ...], tuple[dict[LinearFamily, str], bool, set[tuple[int, ...]]]] = {}
    linear_families, complete, overflow_subsets = _linear_families_for_subset(
        label_tuple,
        memo=memo,
        max_families_per_subset=max_families_per_subset,
    )
    subset_family_counts = {str(key): len(value[0]) for key, value in memo.items()}
    return (
        linear_families,
        complete,
        tuple(sorted(overflow_subsets)),
        subset_family_counts,
    )


def find_scaffold_pc_representation(
    labels: Sequence[int],
    target_orders: Iterable[Sequence[int]],
    *,
    max_families_per_subset: int = 50_000,
) -> ScaffoldPCRepresentabilityReport:
    """Try to represent ``target_orders`` by a scaffold ``PCNode`` frontier set.

    ``complete=False`` means the bounded learner hit ``max_families_per_subset``
    for at least one subset, so a negative result is inconclusive.
    """

    label_tuple = tuple(sorted(labels))
    target = frozenset(canonical_circular_order(order) for order in target_orders)
    all_order_count = 1 if len(label_tuple) <= 2 else factorial(len(label_tuple) - 1) // 2

    if not target:
        return ScaffoldPCRepresentabilityReport(
            representable=False,
            complete=True,
            witness=None,
            target_size=0,
            all_order_count=all_order_count,
            linear_family_count=0,
            canonical_family_count=0,
            subset_family_counts={},
            overflow_subsets=(),
            empty_target=True,
        )

    linear_families, complete, overflow_subsets, subset_family_counts = (
        _linear_families_for_labels(label_tuple, max_families_per_subset)
    )

    canonical_seen: set[CircularFamily] = set()
    for family, descriptor in linear_families.items():
        circular_family = circularize_linear_family(family)
        canonical_seen.add(circular_family)
        if circular_family == target:
            return ScaffoldPCRepresentabilityReport(
                representable=True,
                complete=complete,
                witness=descriptor,
                target_size=len(target),
                all_order_count=all_order_count,
                linear_family_count=len(linear_families),
                canonical_family_count=len(canonical_seen),
                subset_family_counts=subset_family_counts,
                overflow_subsets=overflow_subsets,
            )

    return ScaffoldPCRepresentabilityReport(
        representable=False,
        complete=complete,
        witness=None,
        target_size=len(target),
        all_order_count=all_order_count,
        linear_family_count=len(linear_families),
        canonical_family_count=len(canonical_seen),
        subset_family_counts=subset_family_counts,
        overflow_subsets=overflow_subsets,
    )
