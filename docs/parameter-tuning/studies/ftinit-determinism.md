# ftINIT reproducibility: `resolve_ties`, `prove_abs_gap`

How reproducible ftINIT is, what raven-toolbox's opt-in parameters `resolve_ties` and `prove_abs_gap` fix, and what they do not fix. Companion to the API documentation in `raven_toolbox.init.ftinit`.

Two different properties are at stake, and they need separating:

* **Determinism**: same input, different run/machine/solver build → same model.
* **Stability**: *similar* input (a curated template, a different but comparable sample) → *similar* model.

`resolve_ties` and `prove_abs_gap` target determinism. Neither makes the model stable under a change of the input: a small template edit moves a re-extraction by far more than the seed does. raven-toolbox has no parameter that anchors a re-extraction to a prior build.

## Why the problem exists

The extraction MILP is degenerate. In the first step on Human-GEM/DLD1, 1547 merged reactions have a negative score (the true 0/1 keep-or-drop binaries), and **98.3% of them (1520) sit in blocks of equal score**. The largest block has 840 reactions at −5.0; the second, 420 reactions at −2.0 (the default score of a reaction without gene association), has 419 to 421 members across the five Hart2015 cell lines, so the choice of expression data changes its size by at most 2 members. Many reaction subsets reach the same score optimum and the solver returns an arbitrary one.

`Threads=1` and a fixed `Seed` make that choice close to reproducible, not unique: two baseline builds at one seed differ by 2 reactions, because runs that stop at a wall-clock limit (the 5 s run of the last step) can end at a different incumbent depending on machine load. A different Gurobi version, platform, or seed lands on a different member of the tied set, and that surfaces downstream as gene-essentiality predictions that drift for reasons unrelated to the model or the data.

`resolve_ties` and `prove_abs_gap` attack that directly:

* **`resolve_ties`**: a lexicographic phase 2 after the primary solve of each extraction step, with the score objective held at its optimum. The phases are, in order:
  * `phase2a-parsimony`: minimise the count of kept removable (negative-score) reactions.
  * `phase2b-idrank`: among those, minimise the summed id rank of the kept reactions. A merged reaction is ranked by the smallest original id in its group (`rank_keys`), so the rank does not depend on which member names the merged reaction.
  * `phase2c-minflux`: for that on set, minimise the total absolute flux (gap 1e-6), so the fluxes that the next step reads for its forced directions and magnitudes do not depend on the solver's vertex.
  * `phase2d-direction`: among the minimal-flux solutions, minimise the id-rank-weighted backward flux of the reactions whose flux can take either sign (gap 1e-6), so a flux that carries the same total either way gets a fixed direction.

  The last step skips `phase2c-minflux` and `phase2d-direction`, because no later step reads its fluxes. The task gap-fill uses the first two phases. Phases 2a and 2b get half of `time_limit` each; phases 2c and 2d get the full `time_limit`.
* **`prove_abs_gap`**: proves each step to a fixed *absolute* MIP gap in a single solve, replacing RAVEN's relative-gap escalation, whose final near-zero-objective run otherwise accepts an arbitrary within-gap incumbent.

Both default to off (`resolve_ties=False`, `prove_abs_gap=None`).

What happens when a phase does not prove its optimum:

* A phase that stops at `time_limit` and holds an incumbent is adopted, and a `UserWarning` names it (an unproven incumbent): `phase2a-parsimony` and `phase2b-idrank` in one warning that they share, `phase2c-minflux` and `phase2d-direction` each in their own. The shared warning is raised when `phase2b-idrank` ends with an incumbent, and not otherwise.
* A flux phase (`phase2c-minflux`, `phase2d-direction`) that finds no solution warns with its name and keeps the fluxes of the phase before it.
* A phase `phase2a-parsimony` or `phase2b-idrank` that finds no incumbent drops the on/off tie-break of that solve without a warning: the primary solution is kept and the ties of that step are not resolved. The absence of a warning therefore does not mean that the tie-break completed.
* When the primary solve of a step stops at `time_limit`, all tie-break phases of that solve are skipped and the primary solution is kept.
* The baseline escalation (`resolve_ties=False`, `prove_abs_gap=None`) raises no warning either, and its step 1 objective ends 4.0 to 12.0 below the optimum.

For comparison, RAVEN's `ftINIT` with `resolveTies` skips the tie-break after a primary solve that stopped at the time limit, gives the count and id-rank phases half of `params.TimeLimit` each, skips the minimal-flux and direction phases in the last step, and names every unproven phase (`phase2a-parsimony`, `phase2b-idrank`, `phase2c-minflux`, `phase2d-direction`) in its "tie resolution did not converge" warning (`ftINITInternalAlg.m`).

## Method

* **Model / data.** Human-GEM `v2.0.0-38`, Hart2015 DLD1 cell line, 57 essential tasks, series `1+1`. The `model/Human-GEM.yml` of that commit has 12877 reactions and 2848 genes. The preparation is the one of `estimateEssentialGenes.py` at that commit (removal of drug, amino-acid-triplet and duplicate complex I reactions), followed by raven-toolbox's own `prep_init_model`: a reference model of 10141 reactions and a merged model of 6861 reactions, with 206 task-essential reactions. This is not RAVEN's exported `raven_refModel.xml`, so absolute counts are not comparable to the [Human-GEM validation](humangem-validation.md) run, which uses that export.
* **Settings.** `big_m=100`, `mip_gap_abs=10`, `time_limit=1800` (the values of `estimateEssentialGenes.py` at that commit). Without `prove_abs_gap`, each step runs RAVEN's escalation schedule, whose runs carry their own limits (step 1: 120 s for the first run; final step: 5 s, 120 s, then 1800 s). With `prove_abs_gap`, each primary solve and phases 2c and 2d use the 1800 s limit, phases 2a and 2b get half of it (`_TIE_BREAK_TIME_FRACTION = 0.5`), and the task gap-fill uses a fixed 300 s per task.
* **Solver.** Gurobi 13.0.1, `Threads=1` unless stated, raven-toolbox at commit `94f39407`. The builds ran as Slurm jobs on AMD EPYC 9354 nodes shared with other jobs, so wall-clock figures are approximate. Most jobs had 2 CPUs and the `Threads=4` jobs of the first-step probe had 4; several builds ran in sequence in one job (the seeds of a setting, or the three builds of the stability test).
* **Determinism probe.** The extraction `seed` is varied (1234, 7, and further seeds where noted) with everything else (inputs, code, solver build, machine) held fixed, so any difference between builds is the solver's tie-break among equal optima. Cross-version drift is not measured; see *Limitations*.
* **Metrics.** Reaction seed-swing (symmetric difference of kept-reaction sets) and essential-gene seed-swing (symmetric difference of single-gene-deletion essential sets, via `cobra.flux_analysis.find_essential_genes` with its default threshold). The second is what matters for users; the first is what the parameters act on directly.
* **Debug log.** All builds ran with `FTINIT_DEBUG=1`, which logs the status of each solve and of each tie-break phase.

## Results

### Full pipeline, seed 1234 vs 7

Each build is the full pipeline with task gap-fill, one build per seed and setting.

| Config | Reaction swing | **Gene swing** | Essential genes | Build |
|---|---:|---:|---:|---:|
| baseline | 110 | **17** | 125 / 112 | 237 s / 228 s |
| `resolve_ties=True` | 41 | **1** | 114 / 113 | 864 s / 812 s |
| `resolve_ties=True, prove_abs_gap=1.0` | 1 | **0** | 125 / 125 | 5742 s / 6354 s |
| `resolve_ties=True, prove_abs_gap=0.05` | 1 | **0** | 125 / 125 | 5793 s / 6589 s |

The gene-level swing falls from 17 to 1 with `resolve_ties` and to 0 with `prove_abs_gap` added; the reaction-level swing falls from 110 to 41 to 1. The essential-gene counts of the two seeds are equal in the last two rows, and the two `prove_abs_gap` values give the same result. The runtime grows from about 4 minutes (baseline) to about 14 minutes (`resolve_ties`, 3.6 times) and about 100 minutes (`resolve_ties` with `prove_abs_gap`, 26 times).

Repeated builds at a **fixed** seed (seed 1234, two builds per setting, nothing changed between them):

| Config | Reaction difference | Gene difference | Build |
|---|---:|---:|---:|
| baseline | 2 | 0 | 237 s / 231 s |
| `resolve_ties=True` | 0 | 0 | 865 s / 861 s |

The baseline moves 2 reactions between two runs with nothing changed; the `resolve_ties` builds have identical reaction sets.

### Where the degeneracy sits

Six seeds through the first step alone (a one-step series, so the flux phases of `resolve_ties` do not run), with and without `resolve_ties`, and at `Threads` 1 and 4:

| Config | Threads | Distinct solutions / 6 | Mean pairwise swing | Time per build |
|---|---:|---:|---:|---:|
| baseline | 1 | 6 | 48.7 | 54 to 56 s |
| baseline | 4 | 6 | 48.3 | 53 to 56 s |
| `resolve_ties=True` | 1 | 4 | 7.4 | 71 to 124 s |
| `resolve_ties=True` | 4 | 3 | 4.8 | 67 to 95 s |

At the same seed, the baseline solutions at `Threads` 1 and 4 are 5 to 20 reactions apart, and in 5 of the 6 seeds the two runs reach different objective values. The number of distinct solutions and the mean pairwise swing are similar at both thread counts (6 and 6 distinct, 48.7 and 48.3), so raising `Threads` did not remove the degeneracy in these runs.

Conditioning on the objective separates the tie-break from the primary solve. The 12 baseline runs (both thread settings) reached six objective values between 45887.113 and 45899.113. At a *fixed* objective value, the baseline returned 4 distinct solutions from 4 runs at 45892.113 (pairwise differences 6 to 60 reactions) and 4 from 4 at 45894.113 (35 to 53). With `resolve_ties`, the 4 runs at each of these two objective values returned **one** solution each. The 12 `resolve_ties` runs gave 5 distinct reaction sets, and the residual variation came from the primary solve landing on different objective values, not from the tie-break.

### What `prove_abs_gap` does

Sweeping the value with `resolve_ties=True` and the full two-step pipeline without gap-fill, four seeds (1234, 7, 1, 2) per value. "`None`" is the escalation with `resolve_ties=True`. The times are those of the whole step, including its tie-break phases. All 48 solves of step 1 and step 2 with a `prove_abs_gap` value ended with status `optimal`.

| `prove_abs_gap` | Step 1 objectives (4 seeds) | Step 2 objectives (4 seeds) | Step 1 time | Step 2 time |
|---|---|---|---:|---:|
| `None` (escalation) | 45887.113, 45892.113 (2), 45895.113 | −616.906, −614.906, −612.906, −611.264 | 256 to 339 s | 191 to 199 s |
| 5.0 | 45897.113, 45899.113 (3) | −614.906, −613.872 (2), −611.872 | 3433 to 3649 s | 1510 to 1668 s |
| 2.0 | 45899.113 (4) | −613.872 (3), −611.872 | 3310 to 3649 s | 1397 to 1945 s |
| 1.0 | 45899.113 (4) | −613.872 (3), −611.872 | 3305 to 3650 s | 1647 to 2500 s |
| 0.5 | 45899.113 (4) | −613.872 (3), −611.872 | 3307 to 3650 s | 1718 to 2660 s |
| 0.1 | 45899.113 (4) | −613.872 (3), −611.872 | 3313 to 3650 s | 1757 to 2721 s |
| 0.05 | 45899.113 (4) | −613.872 (3), −611.872 | 3317 to 3650 s | 1758 to 2734 s |

The escalation returns a step 1 solution 4.0 to 12.0 below the proven optimum 45899.113, without a warning: of its four runs, none reaches the optimum. `prove_abs_gap=5.0` stops 2.0 below it for one seed; every value from 2.0 to 0.05 reaches it for all four seeds. The step 2 objectives depend on the step 1 result, so they are comparable between rows where step 1 is equal: the four seeds with a proven step 1 give −613.872 for three seeds and −611.872 for seed 7 (`phase2c-minflux` and `phase2d-direction` of step 1 reach the limit, which leaves the flux read-out seed-dependent).

All values from 2.0 to 0.05 give the same objectives and the same final reaction sets. Tighter gaps cost little: step 2 takes up to 2734 s at 0.05 against 2500 s at 1.0, and the mean of a whole build is 5770 s against 5640 s. In step 1, `phase2c-minflux` and `phase2d-direction` run to the limit in most builds (3 of 4 seeds for `phase2c-minflux` and 4 of 4 for `phase2d-direction` at `prove_abs_gap=1.0`); per-phase times were not logged, so the split of step 2 between proof and tie-break is not measured.

Final reaction sets of the sweep (without gap-fill): the escalation gives four distinct sets, 37 to 56 reactions apart; `prove_abs_gap=5.0` gives three; every value from 2.0 to 0.05 gives two, which differ by one reaction (seed 7 against the other three).

### The limit of `resolve_ties` at genome scale

With a proven step 1 objective, the tie-break phases do not all prove at genome scale. The tie-break phase statuses of the eight tie-broken solves (two steps, four seeds) at `prove_abs_gap=1.0` (the other values 0.05 to 5.0 give the same counts):

| Phase | Optimal | Stopped at `time_limit` |
|---|---:|---:|
| `phase2a-parsimony` (steps 1 and 2) | 6 | 2 (both in step 2) |
| `phase2b-idrank` (steps 1 and 2) | 8 | 0 |
| `phase2c-minflux` (step 1) | 1 | 3 |
| `phase2d-direction` (step 1) | 0 | 4 |

Step 2 is the last step, so it skips the last two phases. The log of seed 1234:

```
[ftinit] final solve:                  obj=45899.11 status=optimal achieved_gap=2.8e-06
[ftinit] tie-break phase2a-parsimony:  status=optimal     obj=143.0
[ftinit] tie-break phase2b-idrank:     status=optimal     obj=111784.0
[ftinit] tie-break phase2c-minflux:    status=time_limit  obj=7537.55
[ftinit] tie-break phase2d-direction:  status=time_limit  obj=2626475.28
[ftinit] final solve:                  obj=-613.87 status=optimal achieved_gap=0.0016
[ftinit] tie-break phase2a-parsimony:  status=time_limit  obj=298.0
[ftinit] tie-break phase2b-idrank:     status=optimal     obj=346311.0
```

The on/off tie-break of step 1 is proven in all four seeds, so the step 1 reaction set is fixed. `phase2c-minflux` reaches the 1800 s limit in 3 of the 4 seeds and `phase2d-direction` in all 4; each is adopted as an unproven incumbent, which is why a step 1 takes about 3650 s and a build about 100 minutes. The flux the next step reads is therefore the incumbent of a time-limited solve, and it differs by seed: the step 2 objective is −611.872 for seed 7 and −613.872 for the other three seeds, and the final sets differ by one reaction.

The builds that use the escalation (`prove_abs_gap=None`) with `resolve_ties=True` also adopt phases at a time limit, here the limit of the escalation run. The build of seed 1234 in the full-pipeline table adopted 3 phases (`phase2b-idrank`, `phase2c-minflux`, `phase2d-direction` of step 1) and the build of seed 7 adopted 2 (`phase2c-minflux`, `phase2d-direction` of step 1). In step 2 of both builds `phase2a-parsimony` ended at the time limit with an incumbent and `phase2b-idrank` ended at the time limit with no incumbent (`A-rt-1234.log`, `A-rt-7.log`). `phase2b-idrank` then returns no solution, the tie-break of step 2 returns `False`, the primary solution of step 2 is kept, and no warning is raised. The reaction sets of these two builds therefore rest on a resolved step 1 and an unresolved step 2.

Counts of full builds (gap-fill included) with at least one unproven tie-break phase or a time-limited primary solve:

| Config | Builds | With an adopted phase at `time_limit` | With a primary solve at `time_limit` | With a tie-break dropped without a warning |
|---|---:|---:|---:|---:|
| baseline | 4 | 0 (no tie-break) | 4 (one run of the final step) | not applicable |
| `resolve_ties=True` | 4 | 4 | 4 (tie-break of that solve skipped) | 4 (step 2) |
| `resolve_ties=True, prove_abs_gap=1.0` or `0.05` | 4 | 4 | 0 | 0 |

The phase statuses of a build are in the debug log. The warnings cover the adopted phases and the flux phases without a solution, so a build without a warning can still hold an unresolved tie-break (dropped `phase2a-parsimony` or `phase2b-idrank`) or an unproven escalation, and the debug log is the record of what each solve reached. In the sweep, all 24 builds with `prove_abs_gap` raised at least one warning. Raising `time_limit` is the available lever; the effect of a larger limit is not measured.

## Recommendation

* **`resolve_ties=True`**: one repeat pair at a fixed seed (seed 1234) has identical reaction sets, and the seed-to-seed gene swing falls from 17 to 1 on this data, at about 3.6 times the runtime (4 to 14 minutes). Its warnings name the adopted phases that stopped at the time limit, but a tie-break that finds no incumbent in phase 2a or 2b is dropped without a warning (all four `resolve_ties=True` builds drop the one of step 2). With the escalation, the flux phases of step 1 run with the 120 s limit of that run.
* **`prove_abs_gap=1.0`**, together with `resolve_ties=True`: the seed-to-seed swing falls to 1 reaction and 0 genes, and the objectives of both steps are proven to 1.0 (the escalation is 4.0 to 12.0 below the optimum in step 1). The build takes about 100 minutes at `time_limit=1800` (26 times the baseline), of which step 1 takes 3300 to 3650 s (59 to 66 % of the 4987 to 6183 s wall clock of the four `prove_abs_gap=1.0` sweep builds, which have step 1 plus step 2 and no gap-fill; the 5742 s and 6354 s of the full-pipeline table are the two builds with gap-fill), mostly in the two flux phases, and step 2 another 1650 to 2500 s. Use it when the swing of `resolve_ties` alone (41 reactions, 1 gene here) is too large and the runtime is acceptable. A value from 2.0 to 0.05 gives the same models; 5.0 can stop 2.0 below the optimum. The data contain no build with `prove_abs_gap` and without `resolve_ties`.
* **Pinning the solver stack** (raven-toolbox commit + `gurobipy` version) is the zero-cost lever for run-to-run identity, and the parameters on this page do not change it.

## Stability under a small template change

Baseline and `resolve_ties` with seed 1234 on **identical** inputs differ by 162 reactions and 17 essential-gene calls (125 against 114), with the same step 1 objective (45892.113) and different step 2 objectives (−657.240 for the baseline, −616.906 for `resolve_ties=True`). The step 1 difference is a different pick among equally scored solutions; the step 2 difference is not only tie selection, because step 2 reads the fluxes of step 1 and ends at a different objective. That is the order of magnitude by which a re-extraction can move even when nothing about the biology changed.

That matters for two common workflows:

* **Curating the template.** Fix one or a few reactions, re-extract, and compare. The MILP re-solves globally and can move far more than the edit warrants, because the optimum is a discontinuous function of the input: genes flip that have nothing to do with the curation. A deterministic extractor does not fix this; determinism is not continuity.
* **Comparable but distinct samples.** Two RNA-seq samples from the same healthy tissue that differ by ordinary inter-patient variation can independently reselect within the same tied set and produce two models with reaction-level and gene-level differences that look like biology but are not.

**Measured on Human-GEM/DLD1 with a null-ish edit.** 30 reactions were drawn at random (seed 0) from the 2387 reactions of the prepared reference model that the build with `resolve_ties=True, prove_abs_gap=1.0` (seed 1234, 7754 reactions, 125 essential genes) did not keep and that are not task-essential, and removed from the template. Of the 30, 0 are kept by the `resolve_ties` builds and 1 by the baseline build. Each setting was re-extracted from the edited template (seed 1234) and compared with the build of the same setting from the unedited template:

| Setting | Reaction difference | **Essential-gene drift** | Essential genes | Build |
|---|---:|---:|---:|---:|
| baseline | 156 | **17** (2 gains) | 125 → 112 | 194 s |
| `resolve_ties=True` | 59 | **1** | 114 → 115 | 638 s |
| `resolve_ties=True, prove_abs_gap=1.0` | 16 | **1** | 125 → 126 | 4108 s |

The reference build with `resolve_ties` keeps none of the 30 removed reactions and the baseline reference build keeps 1, so a perfectly stable extractor would show next to no downstream change. The baseline re-extraction moves 156 reactions and 17 essential-gene calls; the tie-broken builds move 59 and 16 reactions and 1 gene each. The growth objective of the models is not a stable indicator on this data: the unedited builds of one setting (`resolve_ties=True`) have 74.6 for seed 1234 and 83.1 for seed 7.

**The control that separates a real effect from re-selection noise is to apply the edit to the *extracted* model as well as to the template.** Comparing an extraction of the edited template against the extracted baseline model with the same edit applied directly gives an exact, causal before/after diff for the reactions the edit touches; the re-extraction diff contains in addition the re-selection noise measured above.

## Limitations

One cell line, one seed pair for the full-pipeline determinism table (six seeds for the first-step probe, four seeds for the sweep), one edit (30 unused reactions removed) for the stability measurement, one machine type, one Gurobi build, one `time_limit`. Enough for direction and rough magnitude, not for error bars on any number. Cross-Gurobi-version drift (the failure mode that `resolve_ties` and `prove_abs_gap` target) is not measured at all; the seed probe stands in for it and is expected to understate it. The stability measurement used a "null-ish" edit chosen to touch almost nothing the reference builds used, which is gentler than a typical real curation. Wall-clock figures come from jobs that shared nodes with other jobs and are approximate; the swing and objective columns are set comparisons unaffected by that. The `prove_abs_gap` runtimes depend on the `time_limit` of 1800 s, because the flux phases of step 1 run to the limit; they were not measured with another limit. RAVEN's `ftINIT` was not run.

## Reproducing

Requires Gurobi and a Human-GEM checkout. The preparation of the Human-GEM template (`prep`) and the scores follow `code/test/estimateEssentialGenes.py` of Human-GEM.

```python
from raven_toolbox.init import ftinit

kw = dict(gene_scores=gene_scores, series="1+1", fill_gaps=True, big_m=100.0,
          mip_gap_abs=10.0, time_limit=1800.0)

# Determinism: same input, different seed.
model_a = ftinit(prep, rxn_scores=rxn_scores, seed=1234, resolve_ties=True, prove_abs_gap=1.0, **kw)
model_b = ftinit(prep, rxn_scores=rxn_scores, seed=7,    resolve_ties=True, prove_abs_gap=1.0, **kw)
print(len({r.id for r in model_a.reactions} ^ {r.id for r in model_b.reactions}))

# Stability: a lightly edited template (prep_edited built from the edited template).
m0 = ftinit(prep, rxn_scores=rxn_scores, resolve_ties=True, prove_abs_gap=1.0, **kw)
m1 = ftinit(prep_edited, rxn_scores=rxn_scores, resolve_ties=True, prove_abs_gap=1.0, **kw)
print(len({r.id for r in m0.reactions} ^ {r.id for r in m1.reactions}))
```

`rxn_scores` and `gene_scores` come from `score_reactions_from_genes` and `gene_scores_from_expression` (original reaction id → score). `prep` comes from `prep_init_model(template, tasks, ...)`; `prep_edited` is built the same way from the edited template.

Set `FTINIT_DEBUG=1` to log each solve's status and each tie-break phase, which shows whether a build rests on a proven optimum or an unproven incumbent. The `UserWarning` messages carry the same information.
