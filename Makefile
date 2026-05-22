PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; elif command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi)
PYTEST ?= $(PYTHON) -m pytest

.PHONY: quick check hunt-counterexamples bench-quick bench bench-piste-f bench-csp-quick unit acceptance

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

acceptance:
	make check && make bench
