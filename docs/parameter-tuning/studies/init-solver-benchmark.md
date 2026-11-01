# ftINIT on different solvers

ftINIT builds mixed-integer linear programs (MILPs) and passes them to a solver through optlang. This benchmark runs ftINIT on Human-GEM with the gurobi, glpk, scipy and hybrid interfaces of optlang, and records whether the run completed, how long it took and which reactions the extracted model contains.

## Set-up

Every run calls `ftinit()` with the same input: Human-GEM prepared without a task list and with scaled stoichiometry, reaction scores from HCT116 expression, series `1+1` and `time_limit=900` s. The call also passes `mip_gap=0.001`, which a named series ignores. Software: Human-GEM commit `38567ab8`, raven-toolbox commit `94f3940`, gurobipy 13.0.3 and cobra 0.32.1, on 4 cores. Gurobi library 13.0.3 from the gurobipy wheel (most likely); the logs print no version. Each setting ran once.

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

Gurobi completed in 92 s with the default big-M, which caps each reaction at 1000, and in 128 s with every cap at 100. The log of the `big_m=1000` run carries the warning `ftINIT step 1 hit the 900s time limit with an unproven MIP gap (0.0030)`, although the run took 92 s in total, so one scheduled solve stopped at a limit. The logged `step 1` is the second step. The warning prints the `time_limit` argument, not the limit of the run that stopped. The stopped run is a shorter scheduled run, inferred from the total time; the log does not say which. No step ran for the full 900 s. The calibration study reports 83 s for the same call with a limit of 600 s; it times `ftinit()` alone, while the 92 s here also include reading and scoring. The reaction sets of the two Gurobi runs share a Jaccard index of 0.981, with 140 differing reactions.

## GLPK

GLPK completed the pipeline in 2182 s. Its MILP solver honours `configuration.timeout`, and both main steps stopped at the 900 s limit with an incumbent whose gap is not proven. The extracted model has 6758 reactions against 7312 for Gurobi: 6635 are shared, 123 occur only in the GLPK model and 677 only in the Gurobi model (Jaccard index 0.892). The GLPK model is the best solution found within 900 s per step. The benchmark does not show whether a longer limit would bring it closer to the Gurobi model.

## Interfaces that failed

HiGHS is reached through the `scipy` interface of optlang, which accepts continuous variables only and cannot hold the ftINIT MILP. The run failed with the error in the table after 1521 s. `bm.py` sets the solver name `hybrid` for the `hybrid` row, and `hybrid` was not among the solver names offered in this environment: the error lists `glpk_exact`, `glpk`, `gurobi` and `scipy`. `glpk_exact` was offered and not run. The failure came after 10 s, the time spent loading the prepared-model pickle (reference model and prepared model) before the solver name was set. No HiGHS run exists in this benchmark.

## Choice of solver

With one run per solver, Gurobi completed in 92 s and 128 s; GLPK completed in 2182 s with both main steps stopped at the limit; scipy and hybrid failed. HiGHS through `scipy` cannot hold the ftINIT MILP.

Small networks do not need Gurobi. `tests/test_init_solvers.py` runs ftINIT on toy networks with every installed MILP solver, so development and continuous integration need no Gurobi licence.

## Limits

Each setting ran once, on one model and one cell line. In a different set-up (the DLD1 cell line, `big_m=100`, with tasks and gap-filling), two Gurobi builds with different seeds differ by 110 reactions at baseline ([ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](ftinit-determinism.md)), so a difference of that size between solvers does not by itself indicate a solver effect. The 800 reactions that differ between GLPK and Gurobi (123 + 677) are larger. The `scipy` and `hybrid` rows record failures and give no solver timings.

## Source of the numbers and reproduction

The table comes from `bigm/bm.py solver` and the overlap figures from `bigm/compare.py`. The scripts are in raven-toolbox under `scripts/parameter_tuning/init/`. The CI test for toy networks is separate:

```bash
# CI parameterised tests (seconds, runs always):
python -m pytest tests/test_init_solvers.py -v

# Genome-scale benchmark (needs the prepared model from job.sh prep):
job.sh prep
job.sh solver --solvers gurobi,hybrid
job.sh solver --solvers glpk
job.sh solver --solvers scipy
python compare.py --out $WORK/out --shared $WORK/shared --logs $WORK/logs
```

The first command checks the toy networks and runs in seconds. The commands of the second block are the documented invocations; `job.sh` runs `bm.py` as a Slurm job, as in the README of the folder, with the environment variables `WORK`, `TOOLBOX_ROOT`, `HUMANGEM_ROOT` and `PY` set. The `big_m=100` Gurobi row is part of `bm.py solver`. The tables are computed from the outputs by `compare.py`.
