# Human-GEM cell-type model validation against RAVEN

Validation of raven-toolbox's ftINIT against MATLAB RAVEN on a genome-scale reconstruction (Human-GEM) using the Hart2015 RNA-seq dataset (5 cell lines: DLD1, GBM, HCT116, HELA, RPE1). The goal is functional equivalence: raven-toolbox and RAVEN should extract the same context-specific reaction sets from the same inputs.

## Method

* Versions. Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), RAVEN commit `2d0630e3` (MATLAB 2024b), raven-toolbox commit `94f3940`, Gurobi 13.0.1 for both tools, 4 cores per run.
* Template and inputs. RAVEN ran `prepHumanModelForftINIT` on Human-GEM (drug reactions, amino-acid triplet reactions and the duplicate complex I reaction removed, spontaneous and custom reaction lists set, essential tasks from `metabolicTasks_Essential.txt`), which gives a reference model of 9730 reactions. raven-toolbox ran `prep_init_model` on the same cleaned Human-GEM (11265 reactions). Every reaction in every raven-toolbox result is part of RAVEN's reference model, so the sets are compared directly.
* Scoring. Gene scores `5·ln(level/1)` clipped to [−5, 10] from the TPM values of the Hart2015 file, mapped to reactions through the GPR (`gene_scores_from_expression`, `score_reactions_from_genes` in raven-toolbox; `transcrData` with `threshold=1` in RAVEN), reactions without genes score −2.
* ftINIT. Series `1+1` (2 staged MILP steps). RAVEN: `ftINIT` with default settings. raven-toolbox: `raven_toolbox.init.ftinit` with series `1+1`, `time_limit=600` and the default `big_m=1000`. A named series runs its own schedule of MILP runs in each step, so `mip_gap` and `mip_gap_abs` have no effect on the full pipeline.
* Tasks. Two raven-toolbox variants: **no-task** (preparation without tasks, expression only) and **task-constrained** (essential metabolic tasks, task-essential reactions forced to be kept). RAVEN's reference is task-constrained.

## Construction choices that affect tractability

1. Linear-time constraint construction. Building the steady-state balances with Python `sum()` re-canonicalises a growing sympy expression at each term; hub metabolites (ATP, H⁺ and H₂O in ~10³ reactions) give balances with 10³ terms or more, and summing 1500 terms with `sum` takes 59 s against 0.01 s with `optlang.symbolics.add`. raven-toolbox builds flat term lists once per reaction and sums them with `optlang.symbolics.add`.
2. Per-reaction big-M. The on/off indicator constraints of a scored reaction use `max(min(ub, big_m), min(-lb, big_m), force_on)` as big-M, an infinite bound counting as `big_m`, with `big_m=1000` as the default cap (RAVEN's `bigMCap` in `ftINITInternalAlg`). The cap limits the flux a kept reaction can carry. In the staged pipeline `big_m=25` is infeasible and `big_m=100` is feasible with the default scaling (see [init-param-calibration.md](init-param-calibration.md)).
3. Stoichiometric rescaling. `rescaleModelForINIT` (cap each reaction's coefficient dynamic range at 25×, normalise mean |coeff| to 1) is ported into `prep_init_model`. In the HCT116 runs of the [calibration study](init-param-calibration.md), the staged pipeline with `big_m=1000` is also feasible without it (157 s against 83 s with it, Jaccard 0.969 between the two results), and with `big_m=100` and no rescaling it is infeasible.

## Results

### Run times (one run per cell line)

| step | time |
|------|-----:|
| RAVEN `prepHumanModelForftINIT` (4-worker parallel pool, once per template) | 4320 s |
| raven-toolbox `prep_init_model`, no tasks (cobrapy's default process count for FVA, once per template) | 1556 s |
| raven-toolbox `prep_init_model`, with tasks (`cobra.Configuration().processes = 1`, once per template) | 1695 s |
| RAVEN `ftINIT` per cell line | 40 to 91 s |
| raven-toolbox `ftinit` no-task per cell line | 81 to 91 s |
| raven-toolbox `ftinit` task-constrained per cell line | 146 to 381 s |

The preparation and `ftINIT` times differ from those in the [context-specific model guide](../../guide/init.md) (47 min in MATLAB and 37 min in Python for the preparation; `ftINIT` 797 s in MATLAB and 124 s in Python). The guide runs RAVEN's `prepINITModel` directly on Human-GEM `6812be2a` (12748 reactions, no cleaning) with series `1+0`; the validation runs `prepHumanModelForftINIT` (which removes drug and amino-acid triplet reactions first) on Human-GEM `38567ab8` with series `1+1`. The runs differ in function, template and series together, so the logs do not attribute the difference to one of them.

### Reaction counts

| cell line | RAVEN ftINIT | raven-toolbox ftINIT (no-task) | raven-toolbox ftINIT (task) |
|-----------|-------------:|--------------------------:|-----------------------:|
| DLD1      | 7339 | 7310 | 7348 |
| GBM       | 7278 | 7255 | 7281 |
| HCT116    | 7348 | 7312 | 7343 |
| HELA      | 7417 | 7384 | 7432 |
| RPE1      | 7166 | 7052 | 7165 |

The task-constrained counts are within 0.2 % of RAVEN's; the no-task counts are 0.3 to 0.5 % lower, and 1.6 % lower for RPE1.

### Agreement of raven-toolbox (no-task) ftINIT with RAVEN ftINIT

| cell line | shared | only raven-toolbox | only RAVEN | Jaccard |
|-----------|-------:|--------------:|-----------:|--------:|
| DLD1   | 7255 |  55 |  84 | 0.981 |
| GBM    | 7202 |  53 |  76 | 0.982 |
| HCT116 | 7236 |  76 | 112 | 0.975 |
| HELA   | 7321 |  63 |  96 | 0.979 |
| RPE1   | 6980 |  72 | 186 | 0.964 |

The no-task run is expression-only while RAVEN's reference is task-constrained; the surplus of reactions only in RAVEN (76 to 186) includes reactions that the tasks require.

### Agreement of raven-toolbox (task-constrained) ftINIT with RAVEN ftINIT

| cell line | shared | only raven-toolbox | only RAVEN | Jaccard |
|-----------|-------:|--------------:|-----------:|--------:|
| DLD1   | 7286 | 62 | 53 | 0.984 |
| GBM    | 7235 | 46 | 43 | 0.988 |
| HCT116 | 7277 | 66 | 71 | 0.982 |
| HELA   | 7366 | 66 | 51 | 0.984 |
| RPE1   | 7095 | 70 | 71 | 0.981 |

With the essential metabolic tasks (the task list RAVEN uses) the agreement is Jaccard 0.981 to 0.988 and the differences are symmetric (only-raven-toolbox 46 to 70, only-RAVEN 43 to 71). The residual of 43 to 71 reactions each way out of ~7300 is of the same order as the seed-to-seed difference of 110 reactions in [ftinit-determinism.md](ftinit-determinism.md), which measures a different setup (Human-GEM v2.0.0-38, DLD1, `big_m=100`, escalation schedule).

### Effect of `big_m` on the agreement (no-task, Jaccard against RAVEN)

| cell line | `big_m=1000` (default) | `big_m=100` | Jaccard between the two raven-toolbox results |
|-----------|---------------------:|----------:|----------------------------------------------:|
| DLD1   | 0.981 | 0.979 | 0.984 |
| GBM    | 0.982 | 0.982 | 0.985 |
| HCT116 | 0.975 | 0.974 | 0.981 |
| HELA   | 0.979 | 0.979 | 0.981 |
| RPE1   | 0.964 | 0.967 | 0.984 |

Agreement with RAVEN is the same at the two values tried, `big_m=100` and `big_m=1000`, at the resolution of these runs (differences of at most 0.003, one run per cell line and value). The no-task run time at `big_m=100` is 83 to 122 s, at `big_m=1000` 81 to 91 s.

## Conclusions

From the same cleaned Human-GEM, raven-toolbox reproduces RAVEN's ftINIT reaction selection to Jaccard 0.964 to 0.982 (no-task) and 0.981 to 0.988 (task-constrained) across five cell lines. In the task-constrained run, 43 to 71 reactions per cell line are in only one of the two results, in each direction. Neither tool has a repeat run in this data, so the numbers do not separate solver-level alternate optima from a difference between the implementations.

raven-toolbox uses RAVEN's numerical-conditioning choices (per-reaction big-M capped at 1000, `rescaleModelForINIT`) and uses `optlang.symbolics.add` in place of Python `sum()` in every MILP build (ftINIT and the gap-fill). With these, a task-constrained cell-line model builds in 146 to 381 s and a no-task one in 81 to 91 s after the once-per-template preparation (26 to 28 min), against 40 to 91 s for RAVEN after its 72 min preparation.

## Limits

Each cell line and variant is one run, without seed repeats, so RAVEN's run-to-run spread was not measured and Jaccard differences of a few tenths of a percent are not resolved. The timings come from shared nodes and are approximate. The preparation times compare runs with different parallelism (see the run-time table).
