# ftINIT on different solvers

ftINIT builds mixed-integer linear programs (MILPs) and passes them to a solver through optlang. This benchmark runs ftINIT on Human-GEM with each solver interface that the environment offered, and records whether the run completed, how long it took and which reactions the extracted model contains.

## Set-up

Every run calls `ftinit()` with the same input: Human-GEM prepared without a task list, reaction scores from HCT116 expression, series `1+1` and `time_limit=900` s. The call also passes `mip_gap=0.001`, which a named series ignores. Software: Human-GEM commit `38567ab8`, raven-toolbox commit `94f3940`, Gurobi 13.0.1 and cobra 0.32.1, on 4 cores. Each setting ran once.

The time is the wall-clock time of the whole benchmark step: reading the reference and the prepared model, scoring the reactions and calling `ftinit()`. A failed run reports the time until the failure.

## Results

| Solver interface | big_m | Time (s) | Outcome | Reactions in the extracted model |
|---|---:|---:|---|---:|
| gurobi | 1000 (default) | 92 | completed | 7312 |
| gurobi | 100 | 128 | completed | 7324 |
| glpk | 1000 (default) | 2182 | completed; steps 1 and 2 each stopped at the 900 s limit, gap not proven | 6758 |
| scipy | 1000 (default) | 1521 | failed: `ValueError: Scipy solver only works with continuous variables. Please use another interface` | none |
| hybrid | 1000 (default) | 10 | failed: `SolverNotFound: hybrid is not a valid solver interface. Pick one from glpk_exact, glpk, gurobi, scipy` | none |

The run log counts the steps from 0; the table counts them from 1.

## Gurobi

Gurobi completed in 92 s with the default big-M, which caps each reaction at 1000, and in 128 s with every cap at 100. No step reached the 900 s limit. The calibration study reports 83 s for the same call with a limit of 600 s; it times `ftinit()` alone, while the 92 s here also include reading and scoring. The two Gurobi models were not compared reaction by reaction. In the calibration study, with a time limit of 600 s, the reaction sets at `big_m` 100 and 1000 share a Jaccard index of 0.981 ([ftINIT parameter calibration and input robustness](init-param-calibration.md)).

## GLPK

GLPK completed the pipeline in 2182 s. Its MILP solver honours `configuration.timeout`, and both main steps stopped at the 900 s limit with an incumbent whose gap is not proven. The extracted model has 6758 reactions against 7312 for Gurobi: 6635 are shared, 123 occur only in the GLPK model and 677 only in the Gurobi model (Jaccard index 0.892). The GLPK model is the best solution found within 900 s per step. The benchmark does not show whether a longer limit would bring it closer to the Gurobi model.

## Interfaces that failed

HiGHS is reached through the `scipy` interface of optlang, which accepts continuous variables only and cannot hold the ftINIT MILP. The run failed with the error in the table after 1521 s. The benchmark selected optlang's `hybrid_interface` for HiGHS, but cobra 0.32.1 does not accept `hybrid` as a solver name; it accepts `glpk_exact`, `glpk`, `gurobi` and `scipy`. The failure came after 10 s, the time spent reading the reference model before the solver name was set.

## Choice of solver

Gurobi is the only solver that completed genome-scale ftINIT without reaching the time limit: 92 s against 2182 s for GLPK, which ended both main steps at the limit. HiGHS through `scipy` cannot be used.

Small networks do not need Gurobi. `tests/test_init_solvers.py` runs ftINIT on toy networks with every installed MILP solver, so development and continuous integration need no Gurobi licence.

## Limits

Each setting ran once, on one model and one cell line. In a different set-up (the DLD1 cell line, `big_m=100`, with tasks and gap-filling), two Gurobi builds with different seeds differ by 110 reactions at baseline ([ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](ftinit-determinism.md)), so a difference of that size between solvers does not by itself indicate a solver effect. The 800 reactions that differ between GLPK and Gurobi (123 + 677) are larger. The `scipy` and `hybrid` rows record failures and give no solver timings.

## Reproduction

```bash
# CI parameterised tests (seconds, runs always):
python -m pytest tests/test_init_solvers.py -v

# Genome-scale benchmark (minutes-to-hours, manual):
python scripts/analyze_init_solvers.py --cell HCT116 \
    --doc docs/parameter-tuning/studies/init-solver-benchmark.md
```

The first command checks the toy networks and runs in seconds. The second runs the genome-scale benchmark, which takes minutes to hours. It resumes per solver and reuses the prepared Human-GEM of [Human-GEM cell-type model validation against RAVEN](humangem-validation.md). The script writes its report to the file given by `--doc`; give another path to keep the page.
