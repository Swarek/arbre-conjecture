#!/usr/bin/env python3
"""Benchmark candidate runtime and write a JSON complexity report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import signal
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pc_circular.generators import (  # noqa: E402
    MIXED_INSTANCE_KINDS,
    benchmark_pc_tree,
    instance_by_kind_with_metadata,
)
from pc_circular.pc_tree import enumerate_frontiers  # noqa: E402
from pc_circular.predicates import is_precircular_order_cR, passes_farthest_crossing_condition  # noqa: E402


class TimeoutExpired(Exception):
    pass


def _timeout_handler(_signum, _frame):
    raise TimeoutExpired()


def load_candidate(spec: str) -> Callable[..., Any]:
    if ":" not in spec:
        raise ValueError("--candidate must have form path.py:function")
    path_text, func_name = spec.split(":", 1)
    path = (ROOT / path_text).resolve()
    module_name = "pc_circular_candidate_benchmark"
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


def parse_sizes(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def timed_call(candidate, D, T, timeout: float):
    previous = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    start = time.perf_counter()
    try:
        result = candidate(D, pc_tree=T)
        elapsed = time.perf_counter() - start
        return {"timeout": False, "seconds": elapsed, "result": result}
    except TimeoutExpired:
        return {"timeout": True, "seconds": timeout, "result": None}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, math.ceil(q * len(values)) - 1)
    return values[idx]


def linear_fit(xs: list[float], ys: list[float]):
    if len(xs) < 2:
        return None
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    if ss_xx == 0:
        return None
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / ss_xx
    intercept = y_mean - slope * x_mean
    predictions = [intercept + slope * x for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, predictions))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 if ss_tot == 0 else 1 - ss_res / ss_tot
    return {"intercept": intercept, "slope": slope, "r2": r2}


def fit_models(rows: list[dict[str, Any]]):
    usable = [
        row
        for row in rows
        if row["median_seconds"] is not None and row["median_seconds"] > 0 and row["timeouts"] == 0
    ]
    if len(usable) < 2:
        return {"polynomial": None, "exponential": None}
    ns = [row["n"] for row in usable]
    logs_t = [math.log(row["median_seconds"]) for row in usable]
    polynomial = linear_fit([math.log(n) for n in ns], logs_t)
    exponential = linear_fit([float(n) for n in ns], logs_t)
    if polynomial:
        polynomial["model"] = "time ~= C * n^p"
        polynomial["p"] = polynomial["slope"]
        polynomial["C"] = math.exp(polynomial["intercept"])
    if exponential:
        exponential["model"] = "time ~= C * exp(a*n)"
        exponential["a"] = exponential["slope"]
        exponential["C"] = math.exp(exponential["intercept"])
    return {"polynomial": polynomial, "exponential": exponential}


def result_field(result: Any, field: str, default=None):
    if isinstance(result, dict):
        return result.get(field, default)
    if field == "exists":
        return bool(result)
    return default


def exact_frontier_diagnostics(D, T) -> dict[str, Any]:
    orders = enumerate_frontiers(T, canonical=True)
    valid_order_count = 0
    farthest_pass_count = 0
    for order in orders:
        if is_precircular_order_cR(D, order):
            valid_order_count += 1
        if passes_farthest_crossing_condition(D, order):
            farthest_pass_count += 1
    return {
        "frontier_count": len(orders),
        "valid_order_count": valid_order_count,
        "farthest_pass_count": farthest_pass_count,
        "valid_fraction": valid_order_count / len(orders) if orders else None,
        "farthest_false_positive_count": max(0, farthest_pass_count - valid_order_count),
    }


def _increment_nested(counter: dict[str, dict[str, int]], outer: str, inner: str) -> None:
    bucket = counter.setdefault(outer, {})
    bucket[inner] = bucket.get(inner, 0) + 1


def run_benchmark(
    candidate,
    *,
    candidate_label: str,
    sizes: list[int],
    repeats: int,
    timeout: float,
    instance_kind: str,
    pc_tree_kind: str,
    seed: int,
    diagnostics_up_to: int = 0,
) -> dict[str, Any]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []

    for n in sizes:
        times: list[float] = []
        timeouts = 0
        exists_true = 0
        incomplete = 0
        solvers: dict[str, int] = {}
        resolved_kind_counts: dict[str, int] = {}
        successful_runs_by_resolved_kind: dict[str, int] = {}
        timeouts_by_resolved_kind: dict[str, int] = {}
        exists_true_by_resolved_kind: dict[str, int] = {}
        incomplete_runs_by_resolved_kind: dict[str, int] = {}
        solver_counts_by_resolved_kind: dict[str, dict[str, int]] = {}
        diagnostics = None
        diagnostics_metadata = None
        for _ in range(repeats):
            D, metadata = instance_by_kind_with_metadata(n, kind=instance_kind, rng=rng)
            resolved_kind = metadata["resolved_kind"]
            resolved_kind_counts[resolved_kind] = resolved_kind_counts.get(resolved_kind, 0) + 1

            T = benchmark_pc_tree(pc_tree_kind, n)
            if diagnostics is None and diagnostics_up_to and n <= diagnostics_up_to:
                diagnostics = exact_frontier_diagnostics(D, T)
                diagnostics_metadata = metadata
            outcome = timed_call(candidate, D, T, timeout)
            if outcome["timeout"]:
                timeouts += 1
                timeouts_by_resolved_kind[resolved_kind] = timeouts_by_resolved_kind.get(resolved_kind, 0) + 1
                continue
            times.append(outcome["seconds"])
            successful_runs_by_resolved_kind[resolved_kind] = successful_runs_by_resolved_kind.get(resolved_kind, 0) + 1

            result = outcome["result"]
            if result_field(result, "exists", False):
                exists_true += 1
                exists_true_by_resolved_kind[resolved_kind] = exists_true_by_resolved_kind.get(resolved_kind, 0) + 1
            if result_field(result, "complete", True) is False:
                incomplete += 1
                incomplete_runs_by_resolved_kind[resolved_kind] = (
                    incomplete_runs_by_resolved_kind.get(resolved_kind, 0) + 1
                )
            solver_name = str(result_field(result, "solver", "unknown"))
            solvers[solver_name] = solvers.get(solver_name, 0) + 1
            _increment_nested(solver_counts_by_resolved_kind, resolved_kind, solver_name)

        row = {
                "n": n,
                "repeats": repeats,
                "timeouts": timeouts,
                "successful_runs": len(times),
                "median_seconds": statistics.median(times) if times else None,
                "p95_seconds": percentile(times, 0.95),
                "min_seconds": min(times) if times else None,
                "max_seconds": max(times) if times else None,
                "exists_true": exists_true,
                "incomplete_runs": incomplete,
                "solver_counts": solvers,
                "resolved_kind_counts": resolved_kind_counts,
                "successful_runs_by_resolved_kind": successful_runs_by_resolved_kind,
                "timeouts_by_resolved_kind": timeouts_by_resolved_kind,
                "exists_true_by_resolved_kind": exists_true_by_resolved_kind,
                "incomplete_runs_by_resolved_kind": incomplete_runs_by_resolved_kind,
                "solver_counts_by_resolved_kind": solver_counts_by_resolved_kind,
            }
        if diagnostics is not None:
            row.update(diagnostics)
            row["diagnostics_sample"] = "first_instance_for_size"
            row["diagnostics_sample_metadata"] = diagnostics_metadata
        rows.append(row)

    return {
        "candidate": candidate_label,
        "sizes": sizes,
        "repeats": repeats,
        "timeout_seconds": timeout,
        "instance_kind": instance_kind,
        "pc_tree": pc_tree_kind,
        "seed": seed,
        "mixed_instance_kinds": list(MIXED_INSTANCE_KINDS),
        "diagnostics_up_to": diagnostics_up_to,
        "baseline_warning": (
            "candidate.py is exact for n <= 8 and for documented proved "
            "sub-cases; other larger runs may be incomplete placeholders and "
            "are benchmarked as such"
        ),
        "rows": rows,
        "model_fits": fit_models(rows),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--sizes", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--instance-kind", default="mixed")
    parser.add_argument("--pc-tree", default="star")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=20260521)
    parser.add_argument("--diagnostics-up-to", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    candidate = load_candidate(args.candidate)
    report = run_benchmark(
        candidate,
        candidate_label=args.candidate,
        sizes=parse_sizes(args.sizes),
        repeats=args.repeats,
        timeout=args.timeout,
        instance_kind=args.instance_kind,
        pc_tree_kind=args.pc_tree,
        seed=args.seed,
        diagnostics_up_to=args.diagnostics_up_to,
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "rows": report["rows"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
