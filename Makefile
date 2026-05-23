PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; elif command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi)
PYTEST ?= $(PYTHON) -m pytest

.PHONY: quick check hunt-counterexamples bench-quick bench bench-piste-f bench-csp-quick bench-width-stress bench-single-p-stress bench-relation-catalog bench-relation-shapes bench-relation-chains bench-relation-unsat-cores bench-sparse-matching bench-sparse-binary-cores bench-quartet-coverage bench-frontier-obstructions bench-strict-algorithm52 bench-strict-positive-coverage bench-threshold-roundness bench-cr-pc-representability bench-unrooted-pc-representability bench-permutation-like bench-permutation-composition bench-relation-components unit acceptance

unit:
	$(PYTEST) -q

check:
	$(PYTHON) tools/pc_circular_conjecture_test.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --exhaustive-n 5 \
	  --values 1,2,3 \
	  --random 1000 \
	  --max-n 8 \
	  --self-check \
	  --shrink

hunt-counterexamples:
	$(PYTHON) tools/pc_circular_conjecture_test.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --exhaustive-n 4 \
	  --values 1,2,3 \
	  --random 5000 \
	  --max-n 8 \
	  --self-check \
	  --shrink \
	  --seed 314159

quick:
	$(PYTEST) -q && \
	$(PYTHON) tools/pc_circular_conjecture_test.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --exhaustive-n 4 \
	  --values 1,2,3 \
	  --random 100 \
	  --max-n 7 \
	  --self-check \
	  --shrink

bench-quick:
	mkdir -p reports && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,5,6,8,10,12,16,20 \
	  --repeats 5 \
	  --timeout 2.0 \
	  --instance-kind mixed \
	  --pc-tree star \
	  --output reports/complexity_report_quick.json

bench:
	mkdir -p reports && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,5,6,8,10,12,16,20,30,40,60,80,100 \
	  --repeats 30 \
	  --timeout 3.0 \
	  --instance-kind mixed \
	  --pc-tree star \
	  --output reports/complexity_report.json

bench-piste-f:
	mkdir -p reports && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,5,6,8,10,12,16,20 \
	  --repeats 10 \
	  --timeout 2.0 \
	  --instance-kind cycle \
	  --pc-tree mixed \
	  --diagnostics-up-to 8 \
	  --output reports/complexity_cycle_mixed.json && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,5,6,8,10,12,16,20 \
	  --repeats 10 \
	  --timeout 2.0 \
	  --instance-kind permuted_cycle \
	  --pc-tree star \
	  --diagnostics-up-to 8 \
	  --output reports/complexity_permuted_cycle_star.json && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,6,8,10,12,16,20,30,40 \
	  --repeats 10 \
	  --timeout 2.0 \
	  --instance-kind paired_farthest \
	  --pc-tree star \
	  --diagnostics-up-to 8 \
	  --output reports/complexity_paired_farthest_star.json && \
	$(PYTHON) tools/pc_circular_complexity_benchmark.py \
	  --candidate src/pc_circular/solvers/candidate.py:solve \
	  --sizes 4,6,8,10,12,16,20 \
	  --repeats 10 \
	  --timeout 2.0 \
	  --instance-kind paired_farthest \
	  --pc-tree mixed \
	  --diagnostics-up-to 8 \
	  --output reports/complexity_paired_farthest_mixed.json

bench-csp-quick:
	mkdir -p reports && \
	$(PYTHON) tools/pc_csp_internal_benchmark.py \
	  --sizes 4,5,6,7 \
	  --repeats 3 \
	  --instance-kinds random,cycle,block,ultrametric,equal,non_strict,paired_farthest,permuted_cycle \
	  --pc-trees balanced,mixed \
	  --max-p-degree 3 \
	  --output reports/csp_internal_benchmark_quick.json

bench-width-stress:
	mkdir -p reports && \
	$(PYTHON) tools/pc_csp_width_stress.py \
	  --block-counts 2,3,4,5 \
	  --instance-kinds cycle,paired_farthest,equal \
	  --max-treewidth 4 \
	  --output reports/p3_width_stress.json

bench-single-p-stress:
	mkdir -p reports && \
	$(PYTHON) tools/pc_single_p_domain_stress.py \
	  --sizes 4,5,6,7,8,9,10 \
	  --frontier-limit 25000 \
	  --output reports/single_p_domain_stress.json

bench-relation-catalog:
	mkdir -p reports && \
	$(PYTHON) tools/pc_relation_catalog.py \
	  --block-counts 2,3 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 3 \
	  --output reports/relation_catalog.json

bench-relation-shapes: bench-relation-catalog
	mkdir -p reports && \
	$(PYTHON) tools/pc_relation_shape_search.py \
	  --input reports/relation_catalog.json \
	  --output reports/relation_shape_search.json

bench-relation-chains:
	mkdir -p reports && \
	$(PYTHON) tools/pc_relation_chain_probe.py \
	  --block-counts 2,3 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 8 \
	  --seed 20260550 \
	  --output reports/relation_chain_probe.json

bench-relation-unsat-cores:
	mkdir -p reports && \
	$(PYTHON) tools/pc_relation_unsat_core_probe.py \
	  --block-counts 2,3 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 8 \
	  --seed 20260550 \
	  --output reports/relation_unsat_core_probe.json

bench-sparse-matching:
	mkdir -p reports && \
	$(PYTHON) tools/pc_sparse_matching_conflict_probe.py \
	  --block-counts 2,3 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 8 \
	  --seed 20260550 \
	  --output reports/sparse_matching_conflict_probe.json

bench-sparse-binary-cores:
	mkdir -p reports && \
	$(PYTHON) tools/pc_sparse_binary_core_probe.py \
	  --block-counts 2,3 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 8 \
	  --seed 20260550 \
	  --output reports/sparse_binary_core_probe.json

bench-quartet-coverage:
	mkdir -p reports && \
	$(PYTHON) tools/pc_quartet_solver_coverage_probe.py \
	  --block-counts 2,3,4,5 \
	  --instance-kinds cycle,paired_farthest,random,equal,four_local_non_cr,five_local_non_cr \
	  --repeats 8 \
	  --seed 20260580 \
	  --max-treewidth 5 \
	  --output reports/quartet_solver_coverage_probe.json

bench-frontier-obstructions:
	mkdir -p reports && \
	$(PYTHON) tools/pc_frontier_obstruction_support_probe.py \
	  --sizes 5,6,7,8 \
	  --pc-trees balanced,mixed \
	  --instance-kinds cycle,random,equal,four_local_non_cr,five_local_non_cr,even_high_cycle_low_hub \
	  --repeats 1 \
	  --frontier-limit 512 \
	  --max-non-cr-orders 80 \
	  --seed 20260590 \
	  --output reports/frontier_obstruction_support_probe.json

bench-strict-algorithm52:
	mkdir -p reports && \
	$(PYTHON) tools/pc_strict_algorithm52_audit.py \
	  --sizes 4,5,6,7 \
	  --pc-trees none,star,balanced,mixed \
	  --instance-kinds fig22,strict_t024,cycle,permuted_cycle,random,equal \
	  --repeats 10 \
	  --max-candidates 20000 \
	  --seed 20260600 \
	  --output reports/strict_algorithm52_audit.json

bench-strict-positive-coverage:
	mkdir -p reports && \
	$(PYTHON) tools/pc_strict_positive_coverage_probe.py \
	  --sizes 5,6,8,9,10,12,16,20 \
	  --pc-trees none,star,balanced,mixed \
	  --instance-kinds fig22,strict_t024,cycle,permuted_cycle,random,equal \
	  --repeats 10 \
	  --max-candidates 20000 \
	  --seed 20260610 \
	  --output reports/strict_positive_coverage.json

bench-threshold-roundness:
	mkdir -p reports && \
	$(PYTHON) tools/pc_threshold_roundness_probe.py \
	  --sizes 4,5,6,7 \
	  --instance-kinds cycle,random,equal,paired_farthest,four_local_non_cr,five_local_non_cr \
	  --repeats 5 \
	  --order-limit 5000 \
	  --seed 20260620 \
	  --output reports/threshold_roundness_probe.json

bench-cr-pc-representability:
	mkdir -p reports && \
	$(PYTHON) tools/pc_cr_pc_representability_probe.py \
	  --sizes 4,5,6 \
	  --instance-kinds cycle,random,equal,paired_farthest,four_local_non_cr,five_local_non_cr \
	  --repeats 5 \
	  --max-families-per-subset 50000 \
	  --seed 20260630 \
	  --output reports/cr_pc_representability_probe.json

bench-unrooted-pc-representability:
	mkdir -p reports && \
	$(PYTHON) tools/pc_unrooted_representability_probe.py \
	  --max-candidates 500000 \
	  --output reports/unrooted_pc_representability_probe.json

bench-permutation-like:
	mkdir -p reports && \
	$(PYTHON) tools/pc_permutation_like_probe.py \
	  --repeats 128 \
	  --seed 20260550 \
	  --block-count 2 \
	  --exact-quasi-max-n 8 \
	  --output reports/permutation_like_probe.json

bench-permutation-composition:
	mkdir -p reports && \
	$(PYTHON) tools/pc_permutation_composition_probe.py \
	  --block-counts 2,3,4 \
	  --repeats 64 \
	  --seed 20260550 \
	  --output reports/permutation_composition_probe.json

bench-relation-components:
	mkdir -p reports && \
	$(PYTHON) tools/pc_relation_component_probe.py \
	  --block-counts 2,3,4 \
	  --instance-kinds paired_farthest \
	  --repeats 64 \
	  --seed 20260550 \
	  --output reports/relation_component_probe.json

acceptance:
	make check && make bench
