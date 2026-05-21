#!/usr/bin/env python3
"""Exact small-instance checker for PC-tree circular Robinson candidates."""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pc_circular.generators import cycle_metric, instance_by_kind  # noqa: E402
from pc_circular.oracle import exact_oracle_pc_tree  # noqa: E402
from pc_circular.pc_tree import pc_tree_from_kind, star_pc_tree  # noqa: E402
from pc_circular.predicates import all_circular_orders, is_precircular_order_cR  # noqa: E402


def load_candidate(spec: str) -> Callable[..., Any]:
    if ":" not in spec:
        raise ValueError("--candidate must have form path.py:function")
    path_text, func_name = spec.split(":", 1)
    path = (ROOT / path_text).resolve()
    module_name = "pc_circular_candidate_under_test"
    import_spec = importlib.util.spec_from_file_location(module_name, path)
    if import_spec is None or import_spec.loader is None:
        raise ImportError(f"cannot import candidate from {path}")
    module = importlib.util.module_from_spec(import_spec)
    sys.modules[module_name] = module
    import_spec.loader.exec_module(module)
    candidate = getattr(module, func_name)
    if not callable(candidate):
        raise TypeError(f"{spec} is not callable")
    return candidate


def matrix_from_values(n: int, values: tuple[int, ...]) -> list[list[int]]:
    D = [[0 for _ in range(n)] for _ in range(n)]
    pairs = list(itertools.combinations(range(n), 2))
    for (i, j), value in zip(pairs, values):
        D[i][j] = D[j][i] = int(value)
    return D


def all_matrices(n: int, values: tuple[int, ...]):
    pairs = n * (n - 1) // 2
    for assignment in itertools.product(values, repeat=pairs):
        yield matrix_from_values(n, assignment)


def result_exists(result: Any) -> bool:
    if isinstance(result, dict):
        return bool(result.get("exists"))
    return bool(result)


def result_order(result: Any):
    if isinstance(result, dict):
        return result.get("order")
    return None


def run_one(candidate, D, T, *, label: str):
    expected = exact_oracle_pc_tree(D, T)
    observed = candidate(D, pc_tree=T)
    if result_exists(observed) != bool(expected["exists"]):
        return {
            "label": label,
            "D": D,
            "expected": expected,
            "observed": observed,
        }
    order = result_order(observed)
    if result_exists(observed) and order is not None and not is_precircular_order_cR(D, order):
        return {
            "label": label,
            "D": D,
            "expected": expected,
            "observed": observed,
            "error": "candidate returned a non-circular-Robinson witness",
        }
    return None


def shrink_counterexample(candidate, counterexample):
    D = counterexample["D"]
    best = counterexample
    changed = True
    while changed and len(D) > 1:
        changed = False
        for drop in range(len(D)):
            kept = [i for i in range(len(D)) if i != drop]
            smaller = [[D[i][j] for j in kept] for i in kept]
            T = star_pc_tree(len(smaller))
            mismatch = run_one(candidate, smaller, T, label=f"shrunk_drop_{drop}")
            if mismatch:
                best = mismatch
                D = smaller
                changed = True
                break
    return best


def self_check() -> None:
    expected_counts = {1: 1, 2: 1, 3: 1, 4: 3, 5: 12, 6: 60}
    for n, expected in expected_counts.items():
        actual = len(list(all_circular_orders(n)))
        if actual != expected:
            raise AssertionError(f"all_circular_orders({n})={actual}, expected {expected}")
    for n in range(3, 8):
        D = cycle_metric(n)
        result = exact_oracle_pc_tree(D, star_pc_tree(n))
        if not result["exists"]:
            raise AssertionError(f"cycle metric should be positive for n={n}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--exhaustive-n", type=int, default=4)
    parser.add_argument("--values", default="1,2,3")
    parser.add_argument("--random", type=int, default=100)
    parser.add_argument("--max-n", type=int, default=7)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--shrink", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    values = tuple(int(part) for part in args.values.split(",") if part)
    candidate = load_candidate(args.candidate)
    if args.self_check:
        self_check()

    for n in range(1, args.exhaustive_n + 1):
        T = star_pc_tree(n)
        for idx, D in enumerate(all_matrices(n, values)):
            mismatch = run_one(candidate, D, T, label=f"exhaustive_n={n}_idx={idx}")
            if mismatch:
                if args.shrink:
                    mismatch = shrink_counterexample(candidate, mismatch)
                print(json.dumps(mismatch, indent=2, sort_keys=True))
                return 1

    rng = random.Random(args.seed)
    instance_kinds = [
        "random",
        "cycle",
        "block",
        "ultrametric",
        "equal",
        "non_strict",
        "mixed",
    ]
    pc_tree_kinds = ["star", "balanced", "mixed"]
    for idx in range(args.random):
        n = rng.randint(1, args.max_n)
        kind = rng.choice(instance_kinds)
        tree_kind = rng.choice(pc_tree_kinds)
        D = instance_by_kind(n, kind=kind, rng=rng, values=values)
        T = pc_tree_from_kind(tree_kind, n)
        label = f"random_idx={idx}_n={n}_kind={kind}_tree={tree_kind}"
        mismatch = run_one(candidate, D, T, label=label)
        if mismatch:
            if args.shrink:
                mismatch = shrink_counterexample(candidate, mismatch)
            print(json.dumps(mismatch, indent=2, sort_keys=True))
            return 1

    print("JUSTE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
