"""Basic predicates for circular Robinson experiments.

The functions in this module are intentionally direct.  They are meant to be
trusted test oracles on small instances, not an optimized decision procedure
for the PC-tree existence problem.
"""

from __future__ import annotations

from itertools import permutations
from numbers import Real
from typing import Iterable, Sequence


Matrix = Sequence[Sequence[Real]]
Order = Sequence[int]


def validate_dissimilarity(D: Matrix) -> int:
    """Validate a finite dissimilarity matrix and return its size."""

    if not isinstance(D, Sequence):
        raise ValueError("D must be a square sequence")
    n = len(D)
    for i, row in enumerate(D):
        if not isinstance(row, Sequence) or len(row) != n:
            raise ValueError("D must be square")
        if row[i] != 0:
            raise ValueError("D must have a zero diagonal")
        for j, value in enumerate(row):
            if not isinstance(value, Real):
                raise ValueError("D entries must be real numbers")
            if value < 0:
                raise ValueError("D entries must be non-negative")
            if D[j][i] != value:
                raise ValueError("D must be symmetric")
    return n


def _validate_order_for_D(D: Matrix, order: Order) -> int:
    n = validate_dissimilarity(D)
    if len(order) != n or set(order) != set(range(n)):
        raise ValueError("order must be a permutation of 0..n-1")
    return n


def all_circular_orders(n: int) -> Iterable[tuple[int, ...]]:
    """Yield circular orders on ``0..n-1`` modulo rotation and reversal."""

    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        yield ()
        return
    if n == 1:
        yield (0,)
        return
    if n == 2:
        yield (0, 1)
        return

    for perm in permutations(range(1, n)):
        order = (0, *perm)
        reversed_order = (0, *reversed(perm))
        if order <= reversed_order:
            yield order


def canonical_circular_order(order: Order) -> tuple[int, ...]:
    """Return a canonical representative modulo rotation and reversal."""

    seq = tuple(order)
    n = len(seq)
    if n == 0:
        return ()
    variants: list[tuple[int, ...]] = []
    for candidate in (seq, tuple(reversed(seq))):
        for i in range(n):
            variants.append(candidate[i:] + candidate[:i])
    return min(variants)


def is_arc(order: Order, S: Iterable[int]) -> bool:
    """Return whether ``S`` is a contiguous circular arc in ``order``."""

    seq = tuple(order)
    if len(set(seq)) != len(seq):
        raise ValueError("order must not contain duplicates")
    subset = set(S)
    if not subset.issubset(set(seq)):
        raise ValueError("S must be a subset of the order elements")
    if not subset or len(subset) == len(seq):
        return True

    inside = [x in subset for x in seq]
    transitions = sum(inside[i] != inside[(i + 1) % len(seq)] for i in range(len(seq)))
    return transitions <= 2


def is_robinson_linear(D: Matrix, seq: Order) -> bool:
    """Test the linear Robinson dissimilarity inequalities for one order."""

    n = _validate_order_for_D(D, seq)
    for i in range(n):
        x = seq[i]
        for j in range(i + 1, n):
            y = seq[j]
            for k in range(j + 1, n):
                z = seq[k]
                if D[x][z] < max(D[x][y], D[y][z]):
                    return False
    return True


def is_quasi_circular_order(D: Matrix, order: Order) -> bool:
    """Test whether every metric ball is an arc in the given circular order."""

    n = _validate_order_for_D(D, order)
    for center in range(n):
        for radius in sorted(set(D[center])):
            ball = {point for point in range(n) if D[center][point] <= radius}
            if not is_arc(order, ball):
                return False
    return True


def is_precircular_order_cR(D: Matrix, order: Order) -> bool:
    """Test the pre-circular/circular Robinson inequality for one order.

    The condition is checked for every cyclic quadruple ``x,y,z,t`` appearing
    in this order:

        d(x,z) >= min(max(d(x,y), d(y,z)), max(d(x,t), d(t,z))).
    """

    return find_precircular_cR_violation(D, order) is None


def find_precircular_cR_violation(D: Matrix, order: Order) -> dict | None:
    """Return the first cyclic quadruple violating the cR inequality."""

    n = _validate_order_for_D(D, order)
    if n < 4:
        return None

    seq = tuple(order)
    for i in range(n):
        x = seq[i]
        for off_y in range(1, n - 2):
            y = seq[(i + off_y) % n]
            for off_z in range(off_y + 1, n - 1):
                z = seq[(i + off_z) % n]
                lhs = D[x][z]
                for off_t in range(off_z + 1, n):
                    t = seq[(i + off_t) % n]
                    rhs = min(
                        max(D[x][y], D[y][z]),
                        max(D[x][t], D[t][z]),
                    )
                    if lhs < rhs:
                        return {
                            "quadruple": (x, y, z, t),
                            "positions": (i, (i + off_y) % n, (i + off_z) % n, (i + off_t) % n),
                            "lhs_pair": (x, z),
                            "lhs": lhs,
                            "rhs": rhs,
                            "d_xy": D[x][y],
                            "d_yz": D[y][z],
                            "d_xt": D[x][t],
                            "d_tz": D[t][z],
                        }
    return None


def farthest_sets(D: Matrix) -> dict[int, set[int]]:
    """Return ``F_x``, the set of farthest neighbors of each point."""

    n = validate_dissimilarity(D)
    result: dict[int, set[int]] = {}
    for x in range(n):
        candidates = [y for y in range(n) if y != x]
        if not candidates:
            result[x] = set()
            continue
        farthest_distance = max(D[x][y] for y in candidates)
        result[x] = {y for y in candidates if D[x][y] == farthest_distance}
    return result


def _strictly_between_clockwise(a: int, b: int, c: int, n: int) -> bool:
    if a < b:
        return a < c < b
    return c > a or c < b


def _chords_cross(a: int, b: int, c: int, d: int, n: int) -> bool:
    c_inside = _strictly_between_clockwise(a, b, c, n)
    d_inside = _strictly_between_clockwise(a, b, d, n)
    return c_inside != d_inside


def passes_farthest_crossing_condition(D: Matrix, order: Order) -> bool:
    """Check the farthest-neighbor chord crossing necessary condition.

    Shared endpoints are treated as non-strict degenerate cases and skipped.
    This predicate is used for experiments; the exact oracle uses
    ``is_precircular_order_cR``.
    """

    return find_farthest_crossing_violation(D, order) is None


def find_farthest_crossing_violation(D: Matrix, order: Order) -> dict | None:
    """Return the first non-crossing farthest-neighbor chord pair.

    This is an experimental diagnostic.  In non-strict cases, farthest-neighbor
    degeneracies may make this condition fail even for a cR order.
    """

    n = _validate_order_for_D(D, order)
    position = {value: idx for idx, value in enumerate(order)}
    farthest = farthest_sets(D)

    for x in range(n):
        for xp in farthest[x]:
            for y in range(x + 1, n):
                for yp in farthest[y]:
                    endpoints = {x, xp, y, yp}
                    if len(endpoints) < 4:
                        continue
                    if not _chords_cross(
                        position[x],
                        position[xp],
                        position[y],
                        position[yp],
                        n,
                    ):
                        return {
                            "chords": ((x, xp), (y, yp)),
                            "positions": (
                                position[x],
                                position[xp],
                                position[y],
                                position[yp],
                            ),
                            "farthest_x": sorted(farthest[x]),
                            "farthest_y": sorted(farthest[y]),
                        }
    return None
