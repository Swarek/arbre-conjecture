#!/usr/bin/env python3
"""Summarize structural shapes in the non-boolean P-node relation catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tools.pc_relation_catalog import run_relation_catalog  # noqa: E402


DEFAULT_INSTANCE_KINDS = (
    "cycle",
    "paired_farthest",
    "random",
    "equal",
    "four_local_non_cr",
    "five_local_non_cr",
)


def _parse_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part]


def _parse_strings(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _histogram(values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _degree_histogram_values(histogram: dict[str, int]) -> list[int]:
    values: list[int] = []
    for degree, count in histogram.items():
        values.extend([int(degree)] * int(count))
    return values


def classify_relation_shape(profile: dict) -> tuple[str, list[str]]:
    """Return a primary shape and secondary structural tags."""

    tags: set[str] = set()
    left_size, right_size = profile["domain_sizes"]
    accepted_count = profile["accepted_signature_count"]
    if profile["empty"]:
        tags.add("empty")
        return "empty", sorted(tags)
    if profile["complete_bipartite"]:
        tags.add("complete_bipartite")
        return "complete_bipartite", sorted(tags)

    if left_size != right_size:
        tags.add("small_domain_bridge")
        tags.add("asymmetric_domain")
    if profile["left_total"]:
        tags.add("left_total")
    if profile["right_total"]:
        tags.add("right_total")
    if profile["left_functional"]:
        tags.add("left_functional")
    if profile["right_functional"]:
        tags.add("right_functional")
    if profile["permutation_like"]:
        tags.add("permutation_like")

    if profile["left_functional"] and profile["right_functional"]:
        if accepted_count <= 2:
            tags.add("sparse_partial_matching")
        else:
            tags.add("partial_bijection")

    if profile["left_functional"] and not profile["right_functional"]:
        if profile["left_total"]:
            tags.add("left_total_selector")
        tags.add("left_selector")

    if profile["right_functional"] and not profile["left_functional"]:
        if profile["right_total"]:
            tags.add("right_total_selector")
        tags.add("right_selector")

    left_degrees = _degree_histogram_values(profile["left_degree_histogram"])
    right_degrees = _degree_histogram_values(profile["right_degree_histogram"])
    nonzero_left = {degree for degree in left_degrees if degree}
    nonzero_right = {degree for degree in right_degrees if degree}
    if nonzero_left == {2} and nonzero_right == {2}:
        tags.add("active_two_regular")
    elif len(nonzero_left) == 1 and len(nonzero_right) == 1:
        tags.add("biregular_on_support")

    if (
        profile["left_total"]
        and profile["right_total"]
        and not profile["left_functional"]
        and not profile["right_functional"]
    ):
        tags.add("total_cover_dense")

    if "small_domain_bridge" in tags:
        return "small_domain_bridge", sorted(tags)
    if "permutation_like" in tags:
        return "permutation_like", sorted(tags)
    if "sparse_partial_matching" in tags:
        return "sparse_partial_matching", sorted(tags)
    if "partial_bijection" in tags:
        return "partial_bijection", sorted(tags)
    if "left_selector" in tags and "right_selector" not in tags:
        return "left_selector", sorted(tags)
    if "right_selector" in tags and "left_selector" not in tags:
        return "right_selector", sorted(tags)
    if "active_two_regular" in tags:
        return "active_two_regular", sorted(tags)
    if "total_cover_dense" in tags:
        return "total_cover_dense", sorted(tags)
    if "biregular_on_support" in tags:
        return "biregular_on_support", sorted(tags)

    density = float(profile["density"])
    if density <= 0.25:
        tags.add("sparse")
        return "sparse", sorted(tags)
    if density >= 0.75:
        tags.add("dense")
        return "dense", sorted(tags)

    tags.add("mixed")
    return "mixed", sorted(tags)


def composability_tags(row: dict) -> list[str]:
    """Classify row-level caveats for using a relation as a gadget."""

    tags: set[str] = {"promise_scaffold_only"}
    if row["restrictive_parasite_constraint_count"] == 0:
        tags.add("parasite_free")
    if row["parasite_constant_reject_count"] > 0:
        tags.add("constant_blocked")
    if (
        row["parasite_constant_accept_count"] > 0
        and row["parasite_constant_reject_count"] == 0
    ):
        tags.add("constant_loose")
    if (
        row["parasite_unary_non_boolean_count"] > 0
        or row["parasite_unary_boolean_count"] > 0
    ):
        tags.add("unary_gated")
    if row["negative_certificate_status"] == "relation_unsat_only":
        tags.add("relation_unsat_only")
    return sorted(tags)


def _load_or_build_catalog(
    *,
    input_path: str | Path | None,
    block_counts: Sequence[int],
    instance_kinds: Sequence[str],
    repeats: int,
    seed: int,
    max_p_degree: int,
    validate_until_blocks: int,
) -> dict:
    if input_path:
        return json.loads(Path(input_path).read_text())
    return run_relation_catalog(
        block_counts=block_counts,
        instance_kinds=instance_kinds,
        repeats=repeats,
        seed=seed,
        max_p_degree=max_p_degree,
        validate_until_blocks=validate_until_blocks,
    )


def _relation_instance(row: dict, profile: dict) -> dict:
    primary_shape, shape_tags = classify_relation_shape(profile)
    restrictive_parasites = row["restrictive_parasite_constraint_count"]
    row_composability_tags = composability_tags(row)
    return {
        "catalog_hash": profile["catalog_hash"],
        "primary_shape": primary_shape,
        "shape_class": primary_shape,
        "shape_tags": shape_tags,
        "composability_tags": row_composability_tags,
        "block_count": row["block_count"],
        "n": row["n"],
        "instance_kind": row["instance_kind"],
        "repeat": row["repeat"],
        "seed": row["seed"],
        "row_class": row["row_class"],
        "negative_certificate_status": row["negative_certificate_status"],
        "relation_accept_assignments": row["relation_accept_assignments"],
        "direct_cr_assignments": row["direct_cr_assignments"],
        "scope": profile["scope"],
        "domain_sizes": profile["domain_sizes"],
        "domain_product": profile["domain_product"],
        "accepted_signature_count": profile["accepted_signature_count"],
        "rejected_signature_count": profile["rejected_signature_count"],
        "density": profile["density"],
        "rejected_tuple_ratio": profile["rejected_tuple_ratio"],
        "left_degree_histogram": profile["left_degree_histogram"],
        "right_degree_histogram": profile["right_degree_histogram"],
        "left_total": profile["left_total"],
        "right_total": profile["right_total"],
        "left_functional": profile["left_functional"],
        "right_functional": profile["right_functional"],
        "permutation_like": profile["permutation_like"],
        "empty": profile["empty"],
        "complete_bipartite": profile["complete_bipartite"],
        "accepted_index_tuples": profile.get("accepted_index_tuples"),
        "restrictive_parasite_constraint_count": restrictive_parasites,
        "parasite_free_gadget_candidate": row["parasite_free_gadget_candidate"],
        "parasite_kind_histogram": row["parasite_kind_histogram"],
        "constant_reject_context": row["parasite_constant_reject_count"] > 0,
        "unary_non_boolean_context": row["parasite_unary_non_boolean_count"] > 0,
        "promise_status": row["promise_status"],
    }


def _group_relation_instances(
    instances: Sequence[dict],
    *,
    max_examples_per_group: int,
) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for instance in instances:
        grouped[(instance["primary_shape"], instance["catalog_hash"])].append(instance)

    groups = []
    for (shape, catalog_hash), items in sorted(grouped.items()):
        densities = [float(item["density"]) for item in items]
        tags = sorted({tag for item in items for tag in item["shape_tags"]})
        restrictive = [
            item for item in items if item["restrictive_parasite_constraint_count"] > 0
        ]
        positive = [item for item in items if item["accepted_signature_count"] > 0]
        examples = [
            {
                "block_count": item["block_count"],
                "instance_kind": item["instance_kind"],
                "repeat": item["repeat"],
                "seed": item["seed"],
                "scope": item["scope"],
                "density": item["density"],
                "accepted_signature_count": item["accepted_signature_count"],
                "parasite_kind_histogram": item["parasite_kind_histogram"],
            }
            for item in items[:max_examples_per_group]
        ]
        groups.append(
            {
                "catalog_hash": catalog_hash,
                "primary_shape": shape,
                "shape_tags": tags,
                "instance_count": len(items),
                "domain_sizes_seen": sorted(
                    {tuple(item["domain_sizes"]) for item in items}
                ),
                "min_density": min(densities, default=0.0),
                "max_density": max(densities, default=0.0),
                "positive_accept_instances": len(positive),
                "zero_accept_instances": len(items) - len(positive),
                "restrictive_parasite_instances": len(restrictive),
                "parasite_free_instances": len(items) - len(restrictive),
                "constant_reject_context_instances": sum(
                    1 for item in items if item["constant_reject_context"]
                ),
                "unary_non_boolean_context_instances": sum(
                    1 for item in items if item["unary_non_boolean_context"]
                ),
                "examples": examples,
                "isolation_status": (
                    "has_positive_parasite_free_instance"
                    if any(
                        item["accepted_signature_count"] > 0
                        and item["restrictive_parasite_constraint_count"] == 0
                        for item in items
                    )
                    else "only_with_restrictive_parasites"
                    if restrictive
                    else "no_positive_acceptance"
                ),
            }
        )
    return groups


def run_relation_shape_search(
    *,
    input_path: str | Path | None = None,
    block_counts: Sequence[int] = (2, 3),
    instance_kinds: Sequence[str] = DEFAULT_INSTANCE_KINDS,
    repeats: int = 3,
    seed: int = 20260523,
    max_p_degree: int = 3,
    validate_until_blocks: int = 3,
    max_examples_per_group: int = 3,
) -> dict:
    catalog = _load_or_build_catalog(
        input_path=input_path,
        block_counts=block_counts,
        instance_kinds=instance_kinds,
        repeats=repeats,
        seed=seed,
        max_p_degree=max_p_degree,
        validate_until_blocks=validate_until_blocks,
    )

    instances = [
        _relation_instance(row, profile)
        for row in catalog["rows"]
        for profile in row["binary_non_boolean_relations"]
    ]
    groups = _group_relation_instances(
        instances,
        max_examples_per_group=max_examples_per_group,
    )

    shapes = [instance["primary_shape"] for instance in instances]
    tags = [tag for instance in instances for tag in instance["shape_tags"]]
    functional_shapes = {
        "permutation_like",
        "partial_bijection",
        "sparse_partial_matching",
        "left_selector",
        "right_selector",
        "small_domain_bridge",
    }
    positive_parasite_free = [
        instance
        for instance in instances
        if instance["accepted_signature_count"] > 0
        and instance["restrictive_parasite_constraint_count"] == 0
    ]
    structured_positive = [
        instance
        for instance in instances
        if instance["primary_shape"] in functional_shapes
        and instance["accepted_signature_count"] > 0
    ]
    structured_positive_parasite_free = [
        instance
        for instance in structured_positive
        if instance["restrictive_parasite_constraint_count"] == 0
    ]
    candidate_gadgets = [
        instance
        for instance in positive_parasite_free
        if "constant_blocked" not in instance["composability_tags"]
    ]

    summary = {
        "catalog_rows": len(catalog["rows"]),
        "catalog_complete_rows": catalog["summary"]["complete_rows"],
        "validation_mismatches": catalog["summary"]["validation_mismatches"],
        "binary_relation_instances": len(instances),
        "unique_catalog_hashes": len({item["catalog_hash"] for item in instances}),
        "shape_histogram": _histogram(shapes),
        "shape_class_histogram": _histogram(shapes),
        "shape_tag_histogram": _histogram(tags),
        "functional_relation_instances": sum(
            1
            for item in instances
            if item["left_functional"] or item["right_functional"]
        ),
        "partial_bijection_relation_instances": sum(
            1 for item in instances if item["primary_shape"] == "partial_bijection"
        ),
        "permutation_like_relation_instances": sum(
            1 for item in instances if item["primary_shape"] == "permutation_like"
        ),
        "empty_relation_instances": sum(
            1 for item in instances if item["primary_shape"] == "empty"
        ),
        "complete_relation_instances": sum(
            1 for item in instances if item["primary_shape"] == "complete_bipartite"
        ),
        "positive_accept_relation_instances": sum(
            1 for item in instances if item["accepted_signature_count"] > 0
        ),
        "zero_accept_relation_instances": sum(
            1 for item in instances if item["accepted_signature_count"] == 0
        ),
        "restrictive_parasite_relation_instances": sum(
            1
            for item in instances
            if item["restrictive_parasite_constraint_count"] > 0
        ),
        "parasite_free_relation_instances": sum(
            1
            for item in instances
            if item["restrictive_parasite_constraint_count"] == 0
        ),
        "positive_parasite_free_relation_instances": len(positive_parasite_free),
        "structured_positive_relation_instances": len(structured_positive),
        "structured_positive_parasite_free_relation_instances": len(
            structured_positive_parasite_free
        ),
        "candidate_gadget_instances": len(candidate_gadgets),
        "partial_bijection_hashes": sorted(
            {
                item["catalog_hash"]
                for item in instances
                if item["primary_shape"] == "partial_bijection"
            }
        ),
        "sparse_partial_matching_hashes": sorted(
            {
                item["catalog_hash"]
                for item in instances
                if item["primary_shape"] == "sparse_partial_matching"
            }
        ),
        "active_two_regular_hashes": sorted(
            {
                item["catalog_hash"]
                for item in instances
                if item["primary_shape"] == "active_two_regular"
            }
        ),
        "permutation_like_hashes": sorted(
            {
                item["catalog_hash"]
                for item in instances
                if item["primary_shape"] == "permutation_like"
            }
        ),
        "positive_parasite_free_hashes": sorted(
            {item["catalog_hash"] for item in positive_parasite_free}
        ),
        "structured_positive_parasite_free_hashes": sorted(
            {item["catalog_hash"] for item in structured_positive_parasite_free}
        ),
        "promise_caveat": catalog["summary"].get("promise_caveat"),
        "interpretation": (
            "This report classifies observed relation profiles only. It does "
            "not prove NP-hardness, polynomiality, or promise validity."
        ),
    }
    return {
        "method": "p3_block_relation_shape_search",
        "source_catalog_method": catalog.get("method"),
        "source_catalog_summary": catalog["summary"],
        "relation_instances": instances,
        "shapes": instances,
        "shape_groups": groups,
        "candidate_gadgets": candidate_gadgets,
        "summary": summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=None,
        help="Optional existing relation catalog JSON. If omitted, rebuild it.",
    )
    parser.add_argument("--block-counts", default="2,3")
    parser.add_argument(
        "--instance-kinds",
        default=",".join(DEFAULT_INSTANCE_KINDS),
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--max-p-degree", type=int, default=3)
    parser.add_argument("--validate-until-blocks", type=int, default=3)
    parser.add_argument("--max-examples-per-group", type=int, default=3)
    parser.add_argument("--output", default="reports/relation_shape_search.json")
    args = parser.parse_args(argv)

    report = run_relation_shape_search(
        input_path=args.input,
        block_counts=_parse_ints(args.block_counts),
        instance_kinds=_parse_strings(args.instance_kinds),
        repeats=args.repeats,
        seed=args.seed,
        max_p_degree=args.max_p_degree,
        validate_until_blocks=args.validate_until_blocks,
        max_examples_per_group=args.max_examples_per_group,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"output": str(output.resolve()), "summary": report["summary"]},
            indent=2,
        )
    )
    return 1 if report["summary"]["validation_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
