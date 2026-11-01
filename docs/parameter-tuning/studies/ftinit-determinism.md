# ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`

This study builds Human-GEM models for one cell line with raven-toolbox's `ftinit` under three settings (default, `resolve_ties=True`, and `resolve_ties=True` with `prove_abs_gap`), varies the solver seed and the template, and records how many reactions and predicted essential genes change between builds and how long each build takes. The API documentation is in `raven_toolbox.init.ftinit`.

Two properties are measured. Determinism is that the same input, run again or with another seed, machine or solver build, gives the same model. Stability is that a similar input (a slightly edited template, or a comparable sample) gives a similar model. Both parameters are opt-in (`resolve_ties=False` and `prove_abs_gap=None` by default) and target determinism. In the measurements, the seed-to-seed difference fell from 110 reactions and 17 essential genes (default) to 41 reactions and 1 gene with `resolve_ties`, and to 1 reaction and 0 genes with `prove_abs_gap=1.0` added, at about 3.6 and 26 times the default build time. Neither parameter made the model stable under a change of the input: a small template edit moved a re-extraction by more reactions than a change of seed (156 against 110 at baseline, 59 against 41 with `resolve_ties`, 16 against 1 with `prove_abs_gap`) and by a similar number of essential genes (17 against 17, 1 against 1, 1 against 0). raven-toolbox has no parameter that anchors a re-extraction to a prior build.

## Main results

Each build in the next two tables is the full pipeline, including the task gap-fill, on Human-GEM and the DLD1 cell line (set-up in the next section). The seed-to-seed difference compares the build at seed 1234 with the build at seed 7. The repeat compares two builds at seed 1234 with nothing changed between them; it was run for two settings. For the baseline, the repeat (job A-base-rep) consists of two further builds (236.6 s and 230.9 s), separate from the seed 1234 build of the table (237.1 s). For `resolve_ties`, the repeat consists of two further builds (865 s and 861 s), separate from the seed 1234 build of the table (864 s).

| Setting | Seed-to-seed difference, reactions | Seed-to-seed difference, essential genes | Essential genes (seed 1234 / seed 7) | Repeat difference at seed 1234, reactions / genes | Build time (seed 1234 / seed 7) |
|---|---:|---:|---:|---:|---:|
| baseline | 110 | 17 | 125 / 112 | 2 / 0 | 237 s / 228 s |
| `resolve_ties=True` | 41 | 1 | 114 / 113 | 0 / 0 | 864 s / 812 s |
| `resolve_ties=True, prove_abs_gap=1.0` | 1 | 0 | 125 / 125 | not run | 5742 s / 6354 s |
| `resolve_ties=True, prove_abs_gap=0.05` | 1 | 0 | 125 / 125 | not run | 5793 s / 6589 s |

The two `prove_abs_gap` values gave the same result. The build time grew from about 4 minutes (baseline) to about 14 minutes with `resolve_ties` (3.6 times) and about 100 minutes with `prove_abs_gap` added (26 times).

The two baseline builds at one seed differed by 2 reactions. Each baseline build had one run of the final step that stopped at its 5 s wall-clock limit; a run stopped at a time limit can return a different solution depending on machine load, and this is the presumed source of the 2 reactions (not tested). The two `resolve_ties` builds of the repeat had identical reaction sets.

The template edit removed 30 reactions that the reference builds did not use. They were drawn at random (seed 0) from the 2387 reactions of the prepared reference model that the build with `resolve_ties=True, prove_abs_gap=1.0` (seed 1234, 7754 reactions, 125 essential genes) did not keep and that are not task-essential. Of the 30, the `resolve_ties` builds kept 0 and the baseline build kept 1. Each setting was re-extracted from the edited template at seed 1234 and compared with its build from the unedited template:

| Setting | Reaction difference | Essential-gene difference | Essential genes (unedited → edited) | Build time (edited) |
|---|---:|---:|---:|---:|
| baseline | 156 | 17 (2 gains) | 125 → 112 | 194 s |
| `resolve_ties=True` | 59 | 1 | 114 → 115 | 638 s |
| `resolve_ties=True, prove_abs_gap=1.0` | 16 | 1 | 125 → 126 | 4108 s |

The unedited builds hardly used the removed reactions. If the re-extraction changed only what the edit forces, the baseline model would lose the one removed reaction it kept and the `resolve_ties` models would lose none (inference, not tested). The baseline moved 156 reactions and 17 essential-gene calls; the two settings with `resolve_ties=True` moved 59 and 16 reactions and 1 gene each.

## Set-up

* Model and data: Human-GEM `v2.0.0-38`, Hart2015 DLD1 cell line, 57 essential tasks, series `1+1`. The `model/Human-GEM.yml` of that commit has 12877 reactions and 2848 genes. The preparation is the one of `estimateEssentialGenes.py` at that commit (removal of drug, amino-acid-triplet and duplicate complex I reactions), followed by raven-toolbox's own `prep_init_model`, which gives a reference model of 10141 reactions and a merged model of 6861 reactions (chains of linked reactions combined into one), with 206 task-essential reactions. This preparation differs from RAVEN's exported `raven_refModel.xml`, so absolute counts are not comparable to the [Human-GEM cell-type model validation against RAVEN](humangem-validation.md) run, which uses that export.
* Steps: series `1+1` runs two extraction steps, counted from 1 here; the debug log counts from 0. Step 1 decides the reactions with a gene association; step 2, the last step, adds the reactions without one and holds the reactions of step 1 on.
* Settings: `big_m=100` (the default is 1000), `mip_gap_abs=10` and `time_limit=1800` s, the values of `estimateEssentialGenes.py` at that commit. A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`; they apply to a step without a run schedule.
* Escalation: each solve stops at a mixed-integer programming (MIP) gap, the distance between the objective of the best solution found and the solver's bound on the optimum, either relative (divided by the objective) or absolute. Without `prove_abs_gap`, each step follows RAVEN's run schedule, here called the escalation. The first run uses a relative gap of 0.0004; each later run uses the larger of its relative gap and its absolute gap (10 or 20) divided by the objective, and the step stops as soon as the gap already reached meets the next target. `time_limit` caps the limit of each run: step 1 has runs of 120 s and 1800 s, the final step runs of 5 s, 120 s and 1800 s.
* With `prove_abs_gap`, each step is one solve proven to that absolute gap, with the 1800 s limit for the primary solve and for the two flux phases of `resolve_ties` (phases 2c and 2d), and half of it (`_TIE_BREAK_TIME_FRACTION = 0.5`) for its two on/off phases (phases 2a and 2b); the phases are defined in the section on the parameters. The task gap-fill uses a fixed 300 s per task in every setting.
* Solver: Gurobi through gurobipy, `Threads=1` unless stated, raven-toolbox at commit `94f39407`. Gurobi library 13.0.3 from the gurobipy wheel (most likely); the logs print no version. The builds ran as Slurm jobs on AMD EPYC 9354 nodes shared with other jobs, so wall-clock figures are approximate. Most jobs had 2 CPUs and the `Threads=4` jobs of the first-step probe had 4. Several builds ran in sequence in one job (the seeds of a setting, or the three builds of the stability test).
* Determinism probe: the extraction `seed` was varied (1234, 7, and further seeds where stated) with inputs, code, solver build and machine held fixed. A difference between builds then has two sources: the solver's choice among equal optima, measured where two builds reached the same objective value, and different objective values reached within the gap and time limits (see the location of the degeneracy and the sweep of `prove_abs_gap`). Differences between Gurobi versions were not measured.
* Metrics: the reaction difference is the symmetric difference of the kept-reaction sets (reactions kept by one build and not the other). The essential-gene difference is the symmetric difference of the sets of genes whose single deletion is predicted essential by `cobra.flux_analysis.find_essential_genes` at its default threshold. The gene difference is the result a user sees; the reaction difference is what the parameters act on.
* Debug log: all builds ran with `FTINIT_DEBUG=1`, which logs the status of each solve and of each tie-break phase. An incumbent is the best solution the solver holds when it stops; at a time limit it is not proven optimal.

## Degeneracy of the extraction MILP

The extraction mixed-integer linear program (MILP) has many optima of equal score. In the first step on Human-GEM and DLD1, 1547 merged reactions have a negative score, and these carry the 0/1 keep-or-drop variables. Of them, 98.3 % (1520) are in blocks of equal score. The largest block has 840 reactions at −5.0. The second has 420 reactions at −2.0, the default score of a reaction without gene association; across the five Hart2015 cell lines it has 419 to 421 members, so the expression data change its size by at most 2 members. Many reaction subsets reach the same optimum, and the solver returns one of them.

`Threads=1` and a fixed `Seed` make that choice close to reproducible on one machine: the two baseline builds at one seed differed by 2 reactions. Another seed can select another member of the tied set, or end the solve at another objective value within the gap and time limits; both were seen in the first-step probe, and in either case the predicted essential genes change for reasons unrelated to the model or the data. Another Gurobi version or platform is expected to act the same way; that was not measured.

## Parameters `resolve_ties` and `prove_abs_gap`

`resolve_ties` adds a lexicographic phase 2 after the primary solve of each extraction step, with the score objective held at its optimum. The phases are, in order:

* `phase2a-parsimony`: minimise the count of kept removable (negative-score) reactions.
* `phase2b-idrank`: among those, minimise the summed id rank of the kept reactions. A merged reaction is ranked by the smallest original id in its group (`rank_keys`), so the rank does not depend on which member names the merged reaction.
* `phase2c-minflux`: for that set of kept reactions, minimise the total absolute flux (gap 1e-6), so the fluxes that the next step reads for its forced directions and magnitudes do not depend on the solver's vertex.
* `phase2d-direction`: among the minimal-flux solutions, minimise the id-rank-weighted backward flux of the reactions whose flux can take either sign (gap 1e-6), so a flux that carries the same total either way gets a fixed direction.

The last step skips `phase2c-minflux` and `phase2d-direction`, because no later step reads its fluxes. The task gap-fill uses the first two phases. Phases 2a and 2b get half of `time_limit` each; phases 2c and 2d get the full `time_limit`.

`prove_abs_gap` proves each step to a fixed absolute MIP gap in a single solve. It replaces the escalation, whose final run, at an objective near zero, accepts any incumbent within its gap.

A phase that does not prove its optimum has these outcomes:

* A phase that stops at `time_limit` with an incumbent is adopted, and a `UserWarning` names it as an unproven incumbent. `phase2a-parsimony` and `phase2b-idrank` share one warning, which is raised when `phase2b-idrank` ends with an incumbent and not otherwise; `phase2c-minflux` and `phase2d-direction` each have their own.
* A flux phase (`phase2c-minflux`, `phase2d-direction`) that finds no solution warns with its name and keeps the fluxes of the phase before it.
* When `phase2a-parsimony` or `phase2b-idrank` finds no incumbent, the on/off tie-break of that solve is dropped without a warning: the primary solution is kept and the ties of that step are not resolved. A build without a warning can therefore hold an unresolved step.
* When the primary solve of a step stops at `time_limit`, all tie-break phases of that solve are skipped and the primary solution is kept.
* The escalation raises no warning either. In the four sweep runs with the escalation and `resolve_ties=True`, the step 1 objective ended 4.0 to 12.0 below the proven optimum; at least one of the 12 first-step runs without `resolve_ties` reached it (the location of the degeneracy).

For comparison, RAVEN's `ftINIT` with `resolveTies` skips the tie-break after a primary solve that stopped at the time limit, gives the count and id-rank phases half of `params.TimeLimit` each, skips the minimal-flux and direction phases in the last step, and names every unproven phase (`phase2a-parsimony`, `phase2b-idrank`, `phase2c-minflux`, `phase2d-direction`) in its "tie resolution did not converge" warning. In RAVEN's `src/INIT/ftINITInternalAlg.m`, the skip after a primary solve at the time limit is at line 483, the half limit at line 518 and the warning at line 662; `src/INIT/ftINIT.m` line 227 sets `pinFluxes` to false in the last step. RAVEN's `ftINIT` was not run in this study.

## Location of the degeneracy

Six seeds were run through the first step alone (a one-step series, so the flux phases of `resolve_ties` do not run), with and without `resolve_ties`, at `Threads` 1 and 4. The mean pairwise difference is the reaction difference averaged over the 15 pairs of seeds.

| Setting | Threads | Distinct solutions / 6 | Mean pairwise difference, reactions | Time per build |
|---|---:|---:|---:|---:|
| baseline | 1 | 6 | 48.7 | 54 to 56 s |
| baseline | 4 | 6 | 48.3 | 53 to 56 s |
| `resolve_ties=True` | 1 | 4 | 7.4 | 71 to 124 s |
| `resolve_ties=True` | 4 | 3 | 4.8 | 67 to 95 s |

At the same seed, the baseline solutions at `Threads` 1 and 4 were 5 to 20 reactions apart, and in 5 of the 6 seeds the two runs reached different objective values. The number of distinct solutions and the mean pairwise difference were similar at both thread counts (6 and 6 distinct, 48.7 and 48.3), so raising `Threads` did not remove the degeneracy in these runs.

Grouping the runs by objective value separates the tie-break from the primary solve. The 12 baseline runs (both thread settings) reached six objective values between 45887.113 and 45899.113. At a fixed objective value, the baseline returned 4 distinct solutions from 4 runs at 45892.113 (pairwise differences 6 to 60 reactions) and 4 from 4 at 45894.113 (35 to 53). With `resolve_ties`, the 4 runs at each of these two objective values returned one solution each. The 12 `resolve_ties` runs gave 5 distinct reaction sets, and the remaining differences came from runs whose primary solve reached different objective values.

## Effect of the `prove_abs_gap` value

The value was swept with `resolve_ties=True` on the two-step pipeline without gap-fill, at four seeds (1234, 7, 1, 2) per value. "`None`" is the escalation with `resolve_ties=True`. A step time includes the tie-break phases of that step. All 48 solves of step 1 and step 2 with a `prove_abs_gap` value ended with status `optimal`.

| `prove_abs_gap` | Step 1 objectives (4 seeds) | Step 2 objectives (4 seeds) | Step 1 time | Step 2 time |
|---|---|---|---:|---:|
| `None` (escalation) | 45887.113, 45892.113 (2), 45895.113 | −616.906, −614.906, −612.906, −611.264 | 256 to 339 s | 191 to 199 s |
| 5.0 | 45897.113, 45899.113 (3) | −614.906, −613.872 (2), −611.872 | 3433 to 3649 s | 1510 to 1668 s |
| 2.0 | 45899.113 (4) | −613.872 (3), −611.872 | 3310 to 3649 s | 1397 to 1945 s |
| 1.0 | 45899.113 (4) | −613.872 (3), −611.872 | 3305 to 3650 s | 1647 to 2500 s |
| 0.5 | 45899.113 (4) | −613.872 (3), −611.872 | 3307 to 3650 s | 1718 to 2660 s |
| 0.1 | 45899.113 (4) | −613.872 (3), −611.872 | 3313 to 3650 s | 1757 to 2721 s |
| 0.05 | 45899.113 (4) | −613.872 (3), −611.872 | 3317 to 3650 s | 1758 to 2734 s |

None of the four escalation runs reached the proven step 1 optimum of 45899.113; they ended 4.0 to 12.0 below it, without a warning. `prove_abs_gap=5.0` stopped 2.0 below it for one seed, and every value from 2.0 to 0.05 reached it for all four seeds. The step 2 objectives depend on the step 1 result, so they are comparable between rows where step 1 is equal. With a proven step 1, step 2 gave −613.872 for three seeds and −611.872 for seed 7. In step 1 of the `prove_abs_gap=1.0` builds, `phase2c-minflux` stopped at the time limit for 3 of the 4 seeds and was optimal for 1, and `phase2d-direction` stopped at the time limit for all 4, so the fluxes passed to step 2 were unproven incumbents; whether this causes the seed 7 difference was not tested.

All values from 2.0 to 0.05 gave the same objectives and the same final reaction sets. A tighter gap added little run time: step 2 took up to 2734 s at 0.05 against 2500 s at 1.0, and a whole build took 5770 s against 5640 s on average. Per-phase times were not logged, so the split of step 2 between the proof and the tie-break is not known.

The final reaction sets of the sweep (without gap-fill) were: four distinct sets with the escalation, 37 to 56 reactions apart; three with `prove_abs_gap=5.0`; two with every value from 2.0 to 0.05, which differ by one reaction (seed 7 against the other three).

## Tie-break phases at genome scale

With a proven step 1 objective, the tie-break phases did not all prove within the time limit. The phase statuses of the eight tie-broken solves (two steps, four seeds) at `prove_abs_gap=1.0` were as follows; the other values from 0.05 to 5.0 gave the same counts.

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

The on/off tie-break of step 1 was proven for all four seeds, so the step 1 reaction set is fixed. `phase2c-minflux` reached the 1800 s limit for 3 of the 4 seeds and `phase2d-direction` for all 4, and each was adopted as an unproven incumbent. In the three seeds in which `phase2c-minflux` stopped at the limit, the two flux phases at the 1800 s limit take 3600 s, which accounts for most of the step 1 time of about 3650 s and for a build time of about 100 minutes. The flux that step 2 reads is therefore the incumbent of a time-limited solve. The step 2 objective differed by seed (−611.872 for seed 7, −613.872 for the other three) and the final sets by one reaction. The fluxes themselves were not compared between seeds; a seed-dependent flux is inferred from the step 2 objectives, not measured.

The escalation builds with `resolve_ties=True` also adopted phases at a time limit, here the limit of the escalation run (120 s in step 1, so 60 s for phases 2a and 2b). The full-pipeline build of seed 1234 adopted 3 phases (`phase2b-idrank`, `phase2c-minflux`, `phase2d-direction` of step 1) and the build of seed 7 adopted 2 (`phase2c-minflux`, `phase2d-direction` of step 1). In step 2 of both builds, `phase2a-parsimony` ended at the time limit with an incumbent and `phase2b-idrank` ended at the time limit with no incumbent (`A-rt-1234.log`, `A-rt-7.log`). `phase2b-idrank` then returns no solution, the tie-break of step 2 returns `False`, the primary solution of step 2 is kept, and no warning is raised. The reaction sets of these two builds rest on a resolved step 1 and an unresolved step 2.

Counts of full builds (gap-fill included) with at least one unproven tie-break phase or a time-limited primary solve. The full builds of the main results are, per setting: baseline 5 (seeds 1234 and 7, the two builds of the repeat, the edited template), `resolve_ties=True` 5 (seeds 1234 and 7, the two builds of the repeat, the edited template), `prove_abs_gap` 5 (seeds 1234 and 7 at each of 1.0 and 0.05, the edited template at 1.0). The Builds column gives how many of them were counted.

| Setting | Builds | With an adopted phase at `time_limit` | With a primary solve at `time_limit` | With a tie-break dropped without a warning |
|---|---:|---:|---:|---:|
| baseline | 5 | 0 (no tie-break) | 5 (one run of the final step) | not applicable |
| `resolve_ties=True` | 5 | 5 | 5 (tie-break of that solve skipped) | 5 (step 2) |
| `resolve_ties=True, prove_abs_gap=1.0` or `0.05` | 5 | 5 | 0 | 0 |

Each row counts all builds of its setting, including the edited build at 1.0 for `prove_abs_gap`. The step 2 logs cited are those of seeds 1234 and 7.

The warnings cover the adopted phases and the flux phases without a solution. A build without a warning can hold an unresolved tie-break (a dropped `phase2a-parsimony` or `phase2b-idrank`) or an unproven escalation, and the debug log is the record of what each solve reached. In the sweep, all 24 builds with `prove_abs_gap` raised at least one warning. A larger `time_limit` is the setting that can let the phases prove; its effect was not measured.

## Stability under a small template change

The template-edit result is in the second table of the main results. The two settings with `resolve_ties=True` moved fewer reactions than the baseline, and for each setting the edit moved more reactions than a change of seed. Determinism does not give stability: a deterministic extractor returns the same model for the same input, and the edit changes the input.

Settings on identical inputs also differ. Baseline and `resolve_ties` at seed 1234 differ by 162 reactions and 17 essential-gene calls (125 against 114), with the same step 1 objective (45892.113) and different step 2 objectives (−657.240 for the baseline, −616.906 for `resolve_ties=True`). The step 1 difference is a different choice among solutions of equal score. The step 2 difference includes more than that choice, because step 2 reads the fluxes of step 1 and ends at a different objective.

The growth objective of the models did not indicate stability on this data: the unedited builds of one setting (`resolve_ties=True`) had 74.6 for seed 1234 and 83.1 for seed 7.

For curation of a template (fix one or a few reactions, re-extract, compare), the re-extraction difference contains the effect of the edit together with re-selection among tied solutions. Applying the same edit to the extracted model gives a control: the difference between that edited model and the unedited extraction contains the effect of the edit alone. No result for this control is reported.

## Choice of settings

* `resolve_ties=True`: the repeat pair at seed 1234 had identical reaction sets, and the seed-to-seed difference fell from 17 genes to 1 on this data, at about 3.6 times the build time (4 to 14 minutes). Its warnings name the adopted phases that stopped at the time limit. A tie-break that finds no incumbent in phase 2a or 2b is dropped without a warning; the builds at seeds 1234 and 7 dropped the one of step 2, and the table of build counts gives 5 of 5 builds with a dropped step 2 tie-break. With the escalation, the tie-break runs again in each run of the schedule (`_solve_step` in `ftinit.py` and the run schedule in `steps.py`): the flux phases of step 1 get 120 s when step 1 stops after its first run and 1800 s when a second run follows (its 5000 s capped by `time_limit`).
* `prove_abs_gap=1.0` together with `resolve_ties=True` reduced the seed-to-seed difference from 41 to 1 reaction (1 to 0 genes) at 26 times the baseline time, about 100 minutes at `time_limit=1800`. The objectives of both steps are proven to 1.0 (in the four sweep runs with the escalation and `resolve_ties=True`, step 1 ended 4.0 to 12.0 below the optimum). In the four `prove_abs_gap=1.0` sweep builds (step 1 and step 2, no gap-fill; 4987 to 6183 s wall clock), step 1 took 3305 to 3650 s, 59.0 to 66.3 % of each build, mostly in the two flux phases, and step 2 another 1650 to 2500 s. A value from 2.0 to 0.05 gave the same models; 5.0 stopped 2.0 below the optimum for one seed. No build with `prove_abs_gap` and without `resolve_ties` was run.
* Gurobi versions were not compared; two baseline builds with everything held fixed differed by 2 reactions.

## Limits

The full-pipeline determinism table rests on one seed pair (seeds 1234 and 7), the first-step probe on six seeds and the sweep on four. The study used one cell line, one machine type, one Gurobi build and one `time_limit`, and one edit (30 unused reactions removed) for the stability measurement. Each figure comes from one build per seed and setting, except the repeat pairs at seed 1234, so the data give direction and rough magnitude and no error bars.

Differences between Gurobi versions, the failure that `resolve_ties` and `prove_abs_gap` target, were not measured; the seed probe stands in for them, and how well it represents them is not known. The stability edit removed 30 of 10141 reference reactions, of which the reference builds kept at most 1. Two comparable samples (for example, two expression profiles of one tissue) were not compared.

Wall-clock figures come from jobs that shared nodes with other jobs and are approximate; the difference and objective columns are set comparisons and do not depend on load. The `prove_abs_gap` build times depend on the `time_limit` of 1800 s, because the flux phases of step 1 run to the limit; no other limit was measured. RAVEN's `ftINIT` was not run.

## Reproduction

Requires Gurobi and a Human-GEM checkout. The numbers come from `det/prep.py` (preparation of the template with the essential tasks, about 2000 s), `det/build.py` (one build or repeats of `ftinit` on DLD1 with `big_m=100`, `mip_gap_abs=10` and `time_limit=1800`), `det/select_edit.py` (the 30 removed reactions of the template edit, seed 0), `det/ties.py` (tied-score blocks) and the summaries `det/analyse.py` and `det/det_extra.py`. The scripts are in raven-toolbox under `scripts/parameter_tuning/init/`. The campaign takes about 100 core-hours. The commands run through the Slurm wrappers as in the README of that folder, with `WORK`, `TOOLBOX_ROOT`, `HUMANGEM_ROOT`, `PY`, `DET_SCRIPTS` and `PREP_DIR` set:

```bash
jid=$(sbatch --parsable -J det-prep -o $WORK/logs/prep.log $DET_SCRIPTS/prep.sbatch)
bash $DET_SCRIPTS/submit_all.sh $jid
# after A-rtp1-1234 has finished:
sbatch -J det-edit -o $WORK/logs/edit.log $DET_SCRIPTS/edit.sbatch
python analyse.py $WORK/out
python det_extra.py $WORK/out $WORK/logs
```

The tables are computed from the outputs and logs by `analyse.py` and `det_extra.py`; the degeneracy counts are read from `ties.log`. `ties.py` and `select_edit.py` need the base preparation `prep-base.pkl`, which is not archived and takes about 2000 s to build. `det/build.py` produced the build numbers; series `1+1` ignores `mip_gap_abs`, which the call below passes as `mip_gap_abs=10.0`.

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

Set `FTINIT_DEBUG=1` to log the status of each solve and each tie-break phase, which shows whether a build rests on a proven optimum or an unproven incumbent. The `UserWarning` messages name the adopted phases at the time limit and miss a dropped tie-break.
