# Cross-solver ftINIT benchmark: Human-GEM / HCT116

Same `ftinit()` call (no-task scaled prep; series `1+1`, which runs its own schedule of MILP runs in each step; `time_limit=900s`) run with each MILP-capable optlang interface that the environment offers. Environment: Human-GEM commit `38567ab8`, raven-toolbox commit `94f3940`, Gurobi 13.0.1, cobra 0.32.1, 4 cores, one run per row. Companion to the CI-scale `tests/test_init_solvers.py`.

## Per-solver result

| solver | big_m | time (s) | status | n_rxns |
|--------|------:|---------:|--------|-------:|
| **gurobi** | 1000 (default) | 92 | ok | 7312 |
| **gurobi** | 100 | 128 | ok | 7324 |
| **glpk** | 1000 (default) | 2182 | ok; step 1 and step 2 each stopped at the 900 s time limit with an unproven gap | 6758 |
| **scipy** (HiGHS, continuous only) | 1000 (default) | 1521 | FAIL: `ValueError: Scipy solver only works with continuous variables. Please use another interface` | 0 |
| **hybrid** (HiGHS) | 1000 (default) | 10 | FAIL: `SolverNotFound: hybrid is not a valid solver interface. Pick one from glpk_exact, glpk, gurobi, scipy` | 0 |

The warnings in the run log number the steps from 0 (`step 0`, `step 1`); this page numbers them from 1.

The GLPK result shares 6635 reactions with the Gurobi result at `big_m=1000` (123 only in GLPK, 677 only in Gurobi, Jaccard 0.892). The Gurobi runs at the two `big_m` values differ in time (92 s and 128 s) and share Jaccard 0.98 (see [init-param-calibration.md](init-param-calibration.md)).

## Findings

* **Gurobi** completes ftINIT on Human-GEM in 92 s for 7312 reactions with the default per-reaction big-M (capped at 1000), and in 128 s with every cap at 100. The 83 s of the full-pipeline table in the [calibration](init-param-calibration.md) times the `ftinit` call alone, while the 92 s here also include loading the prep pickle and scoring the reactions; the 900 s cap against 600 s affects the 5000 s runs of the schedule, while the 120 s and 5 s runs stay below both caps. A separate `run_ftinit` call for the first step alone at `mip_gap=0.001` with a 900 s limit takes 24 s; that call is not a share of the pipeline.
* **GLPK** completes the pipeline in this run: its MIP honors `configuration.timeout`, and both main steps stopped at the 900 s limit with an incumbent whose gap is unproven. The result is 2182 s long and its reaction set differs from the Gurobi one by Jaccard 0.892, so it is a time-limited incumbent and not a reproduction of the optimum.
* **HiGHS** is available through the `scipy` interface of the installed optlang, which handles continuous variables only, so the ftINIT MILP cannot be built with it (failure after 1521 s). The `hybrid` interface was attempted and failed after about 10 s with `SolverNotFound`; it is not among the interfaces the installed optlang offers.

## Practical implications

* **Gurobi completed genome-scale ftINIT without a step reaching the time limit in this benchmark.** It finished in 92 s. GLPK finished in 2182 s with both steps stopped at the time limit and a smaller reaction set (6758 against 7312, Jaccard 0.892), and the HiGHS interface (`scipy`) is not usable because it takes continuous variables only.
* **Toy and unit-test correctness is portable.** `tests/test_init_solvers.py` runs the toy ftINIT networks on every installed MILP backend; the formulation is solver-independent, so local development and CI work without a Gurobi licence.

## Reproducing

```bash
# CI parameterised tests (seconds, runs always):
python -m pytest tests/test_init_solvers.py -v

# Genome-scale benchmark (minutes-to-hours, manual):
python scripts/analyze_init_solvers.py --cell HCT116 \
    --doc docs/parameter-tuning/studies/init-solver-benchmark.md
```

Both reuse the cached Human-GEM no-task prep from the validation run
([humangem-validation.md](humangem-validation.md)) and are resumable per solver.
