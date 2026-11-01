# Tuned parameter defaults

Every RAVEN parameter with a non-trivial default has been through one of three processes: matched to a literature value from the original paper of the method, measured empirically on real or synthetic models, or kept for consistency with an existing convention (the default of a widely used underlying tool, or a value already established elsewhere in RAVEN). The short version (current default and a one-line reason) is grouped by capability and covers both the MATLAB and Python (raven-toolbox) implementations. The linked studies give the full measurements and methodology.

:::{admonition} Differences between the two implementations
:class: note

The MATLAB implementation of RAVEN dates from 2013 and the Python implementation (raven-toolbox) from 2026. The parameters re-measured in one implementation have been ported to the other (the homology and KEGG cut-offs). Un-measured defaults of both implementations were not assumed correct; where the two disagreed, the default was measured, with no deference to whichever implementation came first. Every row states the current value(s); where the two differ, both are given. [Cross-toolbox parity decisions](#cross-toolbox-parity-decisions) gives the full accounting, including the cases that are deliberately kept different because the two implementations rest on different solvers or algorithms.
:::

## Flux sampling

RAVEN MATLAB: `randomSampling` (`method='achr'|'chrr'|'random_objective'`), `sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`. raven-toolbox: `random_sampling`, `find_good_reactions`, `max_volume_ellipsoid`. Both implementations expose all three sampling methods through one entry point.

| Parameter | Default | How determined |
|---|---|---|
| `method` | `'achr'` (Python); `'achr'` (RAVEN 3, `randomSampling`) | Literature: ACHR gives near-uniform interior sampling, and the random-objective method draws polytope vertices. All three methods are selectable in both implementations (`'randomObjective'` in MATLAB, `'random_objective'` in Python). RAVEN 2.11.3 had only the random-objective method. |
| `thinning` | `100` | Upstream convention (cobrapy's own ACHR default). Measured insufficient at genome scale: on yeast-GEM one ACHR chain (seed 0) had an effective sample size (ESS) of about 10 from 300 stored samples (9.9 to 63.1 over four seeds), and 4 chains disagreed (median Gelman-Rubin R-hat 1.1020, 50.7 % of scored reactions above 1.1). At `thinning=500` the lag-1 autocorrelation of one chain was 0.825 for seed 0 (0.644 to 0.825 over four seeds, ESS 28.8 to 64.9). Agreement between chains was tested at one other setting, `thinning=300` with `n_samples=100` (the same 30,000 steps per chain), and did not improve. See [Flux sampling convergence and settings](parameter-tuning/studies/sampling-convergence-calibration.md). |
| `warmup` | `1000` | Used by `method='chrr'` only (the steps discarded before the first stored sample); the ACHR sampler of cobrapy has no such parameter. Same as `nBurnin` of RAVEN's `sampleCHRR` and `randomSampling`, which also applies to CHRR only. Not measured. |
| `n_objectives` | `2` | Literature: [Bordel et al. 2010](https://doi.org/10.1371/journal.pcbi.1000859). |
| `replace_max_bound` | `False` | Used by `method='random_objective'`. With `True` the run fails with an unbounded solver status: one probe of 50 objectives gave 49 optimal results and 1 unbounded result. From the cobra code, one unbounded objective stops all draws; the sample at which the run aborted was not recorded. With `False`, 200 samples completed. Kept different from MATLAB on purpose. Whether MATLAB's own solver path handles `True` was not tested. |
| `loopless_good_reactions` | `True` | Loopless FVA excludes only reactions that take part in infeasible cycles, at higher cost; the alternative fixed-threshold (±999) heuristic also excludes reactions that legitimately reach capacity. The loopless technique is implemented in Python only; porting it is a larger project than changing a default. |
| `n_samples`, `seed`, `min_flux`, `max_attempts` | `1000`, `None`, `False`, `100` | Same in both implementations or no evidence favoured a different value. |
| `flux_tol` (in `find_good_reactions`) | `1e-9` | Python-only helper (supports target selection of the random-objective method); no cross-implementation comparison. |
| `maxiter` (in `max_volume_ellipsoid`) | `150` | Literature: [Zhang & Gao 2003](https://doi.org/10.1137/S1052623401397230). |
| `tol`, `reg` (in `max_volume_ellipsoid`) | `1e-6`, `1e-8` | Same in both implementations. |

Full detail: [Flux sampling convergence and settings](parameter-tuning/studies/sampling-convergence-calibration.md) (the primary measurement)

## FSEOF

RAVEN MATLAB: `FSEOF`. raven-toolbox: `fseof`.

| Parameter | Default | How determined |
|---|---|---|
| `n_steps` | `10` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); measured: on iJO1366, 5 and 20 steps change the target set by 4 and 6 targets ([Benchmarks](parameter-tuning/benchmarks.md)). |
| `max_fraction` | `0.9` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); measured: on iJO1366, 0.5 and 0.99 change the target set by 11 and 2 targets, so the sweep does not select 0.9 ([Benchmarks](parameter-tuning/benchmarks.md)). |
| `correlation_threshold` | `0.9` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); measured: on iJO1366, 0.7 adds 4 amplification and 8 knockdown or knockout targets and 0.95 drops 2 and 2 ([Benchmarks](parameter-tuning/benchmarks.md)). |
| `flux_eps` | `1e-6` | Measured on iJO1366: the classification uses the fixed thresholds `1e-10` and `1e-8`, as RAVEN does; `flux_eps` gates the check against the theoretical maximum, and the target counts are identical at `1e-8`, `1e-7` and `1e-6`. |

Full detail: [Benchmarks of `fseof`, `remove_genes` and other defaults](parameter-tuning/benchmarks.md)

## INIT / ftINIT

RAVEN MATLAB: `runINIT`, `scoreModel`, `getINITModel`, `ftINIT`, `prepINITModel`, `ftINITInternalAlg`, `getINITSteps`. raven-toolbox: `score_reactions_from_genes`, `gene_scores_from_expression`, `ftinit`, `prep_init_model`, `run_ftinit`, `get_init_steps`, `classify_reactions`.

Only MATLAB has the legacy tINIT method (`runINIT`, `getINITModel`), which ftINIT replaces; raven-toolbox implements ftINIT alone (see [Context-specific models with ftINIT](guide/init.md)). Rows measured across both algorithms say so.

| Parameter | Default | How determined |
|---|---|---|
| `prod_weight` | `0.5` | Literature: [Ågren et al. 2012](https://doi.org/10.1371/journal.pcbi.1002518) (the original INIT paper). |
| `allow_excretion` | `False` | Recorded, without a measurement, as having no effect at the default `prod_weight`; no measurement is recorded on this site. |
| `mip_gap` | `None` in Python (solver default); `0.0004` in MATLAB | Acts on the first-step solve and on any step without a schedule of MILP runs; a named series such as `1+1` ignores it, because every step runs its own schedule. Steps are counted from 1 here; the logs count from 0, so the logged `step 1` is the second step. Measured on Human-GEM (HCT116) in the first-step solve: the time is flat at 24 to 25 s, the Jaccard index to the result at the tightest gap (0.0002) is 0.9976 at 0.001 and 0.9908 at 0.01, and falls below 0.97 from 0.03. The Python default `None` needs no change. |
| `time_limit` | `None` in Python; `5000` seconds in MATLAB | RAVEN's `ftINIT` sets the Gurobi `TimeLimit` of a MILP run without its own limit to 5000 seconds, and the step schedules of `getINITSteps` use runs of 120 s, 5000 s and 5 s. In Python, `ftinit` with a named series caps each scheduled run by its own limit and `time_limit` lowers that cap further; `time_limit=None` leaves an ad-hoc step or a `run_ftinit` call uncapped, but no scheduled run. The task gap-fill of `ftinit` is a separate MILP with a fixed limit of 300 s per task and does not read `time_limit`. Measured on Human-GEM HCT116 (single runs): first-step solves took 23 to 30 s, and full pipelines 81 to 119 s with scaling and 157 s without. In the robustness runs of [ftINIT parameter calibration and input robustness](parameter-tuning/studies/init-param-calibration.md) (degraded input, with tasks), the gap-fill of one 90 %-dropout model ran longer than 75 minutes; the time limit of that run is not recorded. `None` is the default. The study ran its full pipelines at `time_limit=600`, and its robustness script sets `time_limit=120`; the limit of the recorded robustness runs is not stated. The docstring of `run_ftinit` recommends 120 to 600 s per step for hard or noisy input; no measurement on this site tests that range. |
| `series` | `'1+1'` | Literature: [Gustafsson et al. 2023](https://doi.org/10.1073/pnas.2217868120) (the ftINIT paper). |
| `force_on` | `0.1` | RAVEN's value; measured near-insensitive across the range 0.02–0.5. |
| `big_m` | `1000.0` | The cap on each scored reaction's own big-M, as in `ftINITInternalAlg`: the big-M of a reaction is `max(min(ub, big_m), min(-lb, big_m), 0)`, raised to `force_on` where the "on" floor needs it, and an infinite bound counts as `big_m`. The cap limits the flux a reaction can carry when it is on (it is the largest big-M of a scored reaction in its on/off constraint) and sets no bound on the reaction in the model. |
| `eps` | `1.0` | Same in both implementations. |
| `resolve_ties`, `prove_abs_gap` | `False`, `None`, both opt-in; MATLAB has them as `resolveTies` and `proveAbsGap` at the same defaults | `resolve_ties` fixes the answer among equal-score optima in phases: it holds the score objective at its optimum, minimises the count of kept removable (negative-score) reactions, then among those minimises the summed id rank of the kept ones (a merged reaction is ranked by the smallest original id of its group), then takes the fluxes with the least total absolute flux (relative and absolute gap 1e-6), then those with the least id-rank-weighted backward flux. The last ftINIT step skips the last two phases, because no later step reads its fluxes. Measured on Human-GEM v2.0.0-38 (one cell line, seeds 1234 and 7): with the default escalation the seed-to-seed difference is 110 reactions and 17 predicted essential genes. `resolve_ties=True` gives identical reaction sets at a fixed seed and reduces the seed-to-seed difference to 41 reactions and 1 gene, at about 3.6 times the run time (about 14 min against 4 min at `time_limit=1800`). With `prove_abs_gap=1.0` as well, the difference is 1 reaction and 0 genes, at about 26 times the baseline run time (about 100 min); in the four sweep builds with `prove_abs_gap=1.0`, step 1 took 3305 to 3650 s (59.0 to 66.3 % of a build), mostly in its two flux phases, and step 2 another 1650 to 2500 s; no build without `resolve_ties` was run with `prove_abs_gap`. The flux phases (`phase2c-minflux`, `phase2d-direction`) reach the time limit in most builds, and a warning names each phase adopted at the limit. A tie-break that finds no incumbent in phase 2a or 2b is dropped without a warning. The escalation raises no warning either: in the four `resolve_ties=True` runs without `prove_abs_gap` of the `prove_abs_gap` sweep, its step 1 objective ended 4.0 to 12.0 below the proven optimum. A build without a warning is therefore not necessarily proven or tie-broken. |
| `factor`, `max_score`, `min_score` (in `gene_scores_from_expression`) | `5.0`, `10.0`, `-5.0` | RAVEN's own formula. A 2012 paper (Wang et al. 2012, [mCADRE](https://doi.org/10.1186/1752-0509-6-153)) uses categorical scoring and is not the origin; no source in either implementation cites a paper for it. |
| `score_reactions_from_genes` and `classify_reactions` arguments | various | Same in both implementations or standard practice. |

Full detail: [ftINIT parameter calibration and input robustness](parameter-tuning/studies/init-param-calibration.md) (the primary measurement, genome-scale Human-GEM) · [ftINIT on different solvers](parameter-tuning/studies/init-solver-benchmark.md) · [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](parameter-tuning/studies/ftinit-determinism.md) (`resolve_ties=True` gives identical reaction sets at a fixed seed and a seed-to-seed difference of 41 reactions and 1 gene; adding `prove_abs_gap=1.0` reduces it to 1 reaction and 0 genes at about 26 times the run time) · [Human-GEM cell-type model validation against RAVEN](parameter-tuning/studies/humangem-validation.md) (Jaccard index against RAVEN across 5 cell lines of 0.964 to 0.982 for models extracted without tasks and 0.981 to 0.988 for task-constrained models)

## Gap-filling

RAVEN MATLAB: `fillGaps` (connectivity mode), ported as `connect_blocked_reactions`. `fill_gaps_fast_lp` and `fill_gaps_milp` are the counterparts of RAVEN's `gapFillFastLP` and `gapFillMILP`.

| Parameter | Default | How determined |
|---|---|---|
| `epsilon` (in `fill_gaps_fast_lp`) | `0.0001` | Literature: [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) (the fastGapFill paper). |
| `threshold` (in `connect_blocked_reactions`) | `1.0` | The flux a reaction must be able to exceed to count as unblocked. Same as the fixed threshold of 1 in RAVEN's `fillGaps`, and suited to models in the RAVEN convention, where exchange reactions have bounds of ±1000. Measured on one synthetic network with a maximum flux of 0.5, one run per value: 0.01 and 0.1 filled the gap, 0.5 and 1.0 did not ([Benchmarks](parameter-tuning/benchmarks.md)). |
| `penalty`, `allow_net_production` (in `connect_blocked_reactions`) | `1.0`, `False` | No measurement recorded. `penalty=1.0` makes the MILP minimise the number of added reactions. `allow_net_production=False` keeps the steady-state balance `S @ v == 0`, the stricter test; `True` relaxes it to `S @ v >= 0`. |
| `big_m` (in `fill_gaps_milp`) | `1000.0` | Matches RAVEN's ±1000 bound convention. It caps an unbounded template reaction only when the merged model has no finite bound; otherwise the largest finite bound does. |

Full detail: [Benchmarks of `fseof`, `remove_genes` and other defaults](parameter-tuning/benchmarks.md)

## Homology-based reconstruction

RAVEN MATLAB: `getModelFromHomology`, `getBlast`, `getDiamond`. raven-toolbox: `get_model_from_homology`, `run_blast`, `run_diamond`.

| Parameter | Default | How determined |
|---|---|---|
| `evalue` (`run_blast`) | `1e-4` | Matches MATLAB's `getBlast` (hardcodes `-evalue 10e-5`). On *H. polymorpha* against *S. cerevisiae*, loosening it from `1e-5` to `1e-4` added 5,200 raw hits (8.9 % of the table); 5,310 of the 5,314 rows found only at `1e-4` fail `max_evalue=1e-30` of `get_model_from_homology`; 4 have an E-value below `1e-30`. |
| `evalue` (`run_diamond`) | `1e-3` | Matches MATLAB's `getDiamond`, which passes no `-evalue` flag and so inherits DIAMOND's own default. The value is deliberately different from `run_blast`; each aligner follows its own MATLAB call. |
| `threads` | every CPU the process may run on (Python); the cores assigned to MATLAB (MATLAB) | A 500-query BLAST subset returned the same 2,746 hits at one thread and at four, in 20.4 s and 5.9 s (3.5 times faster; *H. polymorpha* against *S. cerevisiae*, BLAST+ 2.17.0, 2026-11-01). Both sides use all available cores. |
| `max_evalue` | `1e-30` | At identity 40 % and length 200 the score was identical from `1e-4` to `1e-30` in four organisms (BLAST, F0.5, KEGG reference). `1e-50` lowered it by 0.002 to 0.006 in three organisms and left it unchanged in *K. lactis*, and `1e-100` lowered it by 0.020 to 0.063. |
| `min_align_len` | `100`; RAVEN 2.11.3 used `200` | Measured against the KEGG ortholog reference for 4 organisms of increasing distance from *S. cerevisiae*: compared with `200`, a length of 100 raised the score (F0.5) by 0.010 to 0.020, with 2.2 to 3.8 percentage points more recall and at most 0.6 percentage points less precision; 50 and 100 gave the same score. No OMA scores were reported for length. RAVEN 3's `getModelFromHomology` uses `minLen` 100 too. |
| `min_identity` | `40` | Same study: over 25 to 50 % the score changed by 0.062 to 0.275, against 0.047 to 0.055 over alignment lengths 50 to 300 and 0.020 to 0.063 over E-values 1e-4 to 1e-100. With a wrongly transferred reaction weighted as worse than a missing one (F0.5, BLAST), the optimum was 35 or 40 % against KEGG and 35 or 45 % against OMA, depending on the organism; with DIAMOND against OMA the optimum for *E. coli* is 30 %. |
| `bidirectional` | `True` | Same in both implementations. |

Scoring against curated GEMs (hanpo-GEM, rhto-GEM) built by the same reconstruction method is not part of the 2026-11-01 measurement.

Full detail: [Homology cut-off calibration](parameter-tuning/studies/homology-cutoff-calibration.md)
## KEGG-based reconstruction

RAVEN MATLAB: `getKEGGModelForOrganism` (the exact internal name of the KO-assignment sub-step has not been independently confirmed). raven-toolbox: `assign_kos`, `run_hmmsearch`, `build_ko_hmm`, and the `get_kegg_model_*` family.

| Parameter | Default | How determined |
|---|---|---|
| `cutoff` (in `assign_kos`) | `1e-30`; RAVEN 2.11.3 used `1e-50` | Measured against real KEGG gene→KO annotations across 4 organisms of varying study depth: `1e-50` lies inside the E-value distribution of the matched pairs and removes 1 to 10 % of them in three organisms and 10 to 50 % in *M. genitalium*. Precision rose with every stricter cut-off (*S. cerevisiae* 0.73 at `1e-30`, 0.78 at `1e-50`); recall fell by at most 0.03 down to `1e-30` and fell further at stricter cut-offs. Together with `min_score_ratio_g` 0.9, the default raised recall in all four organisms and changed F1 by at most 0.01 in three organisms and raised it by 0.02 in *E. coli*. RAVEN 3's `getKEGGModelForOrganism` uses `cutOff` `10^-30` too. |
| `min_score_ratio_g` (in `assign_kos`) | `0.9`; RAVEN 2.11.3 used `0.8` | Same study: from 0.80 to 0.95 it raised precision by 0.05 to 0.10 at a recall loss of 0.00 to 0.02, and from 0.50 to 0.80 by 0.15 to 0.27; 0.9 itself was not swept. RAVEN 3's `getKEGGModelForOrganism` uses `minScoreRatioG` `0.9` too. |
| `min_score_ratio_ko` (in `assign_kos`) | `0.3` | Same study: at `min_score_ratio_g` 0.80 and `cutoff` `1e-50`, raising it from 0.0 to 0.5 raised precision by 0.00 to 0.03 and lowered recall by 0.00 to 0.01; other combinations were not reported. Kept at the RAVEN value. |
| `seq_identity` (in `build_ko_hmm`) | `0.9` | Literature: the CD-HIT recommendation for protein clustering. |
| `threads` (`run_hmmsearch`, `build_ko_hmm`) | every CPU the process may run on | `hmmsearch` on *S. cerevisiae* gave identical parsed hit tables on 16, 12, 4 and 1 threads, with run times of 89.7, 88.6, 96.4 and 242.5 s ([KEGG HMM cut-off calibration](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md)). `build_ko_hmm` was not measured. |
| `keep_spontaneous`, `keep_undefined_stoich`, `keep_incomplete`, `keep_general` (`get_kegg_model_*`) | `True`, `True`, `True`, `False` | Same in both implementations or standard draft-reconstruction practice. |

Full detail: [KEGG HMM cut-off calibration](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md) (the primary measurement, 4 organisms against real KEGG annotations)

## Sub-cellular localisation

RAVEN MATLAB: `predictLocalization`. raven-toolbox: `predict_localization`. The two use different algorithms: MATLAB uses simulated annealing, a stochastic heuristic with no optimality guarantee, and Python solves a deterministic MILP. For several parameters the question of which value is right does not arise, because the same number means something different in the search budget of a heuristic than in the optimality gap of a solver.

Compartment assignment is in development in Python and is not at parity with MATLAB. The defaults are current, and the method they configure is changing.

| Parameter | Default | How determined |
|---|---|---|
| `default_compartment` | `'c'` in Python; MATLAB requires the argument every call | Convenience default: cytosol is correct for most reactions. MATLAB has no default, so no values disagree. |
| `transport_cost` | `0.5` | Not independently benchmarked; same in both implementations. Calibration note: for real (non-integer-scale) predictor scores, the value typically needs lowering; see the linked study. |
| `time_limit` (Python) and `maxTime` (MATLAB) | `None` (uncapped) in Python; MATLAB's `maxTime` defaults to `15` minutes | The values are not unified: the MATLAB number is a simulated-annealing search budget (more time generally means a better heuristic answer, without a proof of optimality), and the Python number is a MILP solver cutoff (returns a proven-bounded incumbent). Python's `None` was validated at ~2.5 minutes on yeast-GEM, the primary development-scale model. Whether the MILP needs a cap for harder cases has not been stress-tested. |
| `mip_gap` | `None` | Python only; the MATLAB heuristic has no optimality gap. |

Full detail: the measurements behind these values (the yeast-GEM benchmark, the head-to-head against MATLAB's `predictLocalization`, the predictor benchmarks across four organisms, and the design documents) are in [raven-gecko-parity](https://github.com/CompMetEng/raven-gecko-parity/tree/develop/docs/localization), with the rest of the work in progress on this method.

## Model manipulation

RAVEN MATLAB: `removeGenes`, `mergeModels`, `addRxns`, `addTransport`, `simplifyModel` (reversibility-constraining and duplicate-removal modes). raven-toolbox: `remove_genes`, `merge_models`, `add_reactions_from_equations`, `add_transport_reactions`, `constrain_reversible_reactions`, `find_duplicate_reactions`.

| Parameter | Default | How determined |
|---|---|---|
| `blocked_reactions` (in `remove_genes`) | `'constrain'` in Python; MATLAB's `removeGenes` with `removeBlockedRxns` false does the same | Measured on e_coli_core: keeping a reaction unchanged after it has lost its last gene gives false-positive growth after an essential gene is removed (it survives with an empty gene rule). `'constrain'` sets the bounds of such a reaction to 0 and keeps the reaction; `'remove'` deletes it and is opt-in, for gene-essentiality or metabolic-engineering use where the reaction is to disappear; `'keep'` leaves it unchanged. |
| `eps` (in `constrain_reversible_reactions`) | `1e-9` | Matches Gurobi's own default primal feasibility tolerance. |
| `match_by` (in `merge_models`) | `'name'` (Python) and `'metNames'` (MATLAB) | Same semantic field (metabolite display name) under a different schema field name; no values disagree. |
| `remove_orphans`, `mets_by`, `ignore_direction`, `reversible`, `only_to_existing` | various | Python additions and refinements; no direct MATLAB equivalent exists for comparison. |

Full detail: [Benchmarks of `fseof`, `remove_genes` and other defaults](parameter-tuning/benchmarks.md)

## Tasks

RAVEN MATLAB: `checkTasks`. raven-toolbox: `check_tasks`, `find_task_essential_reactions`.

| Parameter | Default | How determined |
|---|---|---|
| `close_boundaries` (both functions) | `False` | Matches RAVEN's `checkTasks`, which leaves the model's own exchange reactions open; published task lists were curated against that. `True` makes the task the whole boundary, as `closeModel` does in RAVEN. |

Full detail: [Benchmarks of `fseof`, `remove_genes` and other defaults](parameter-tuning/benchmarks.md)

## Cross-toolbox parity decisions

Policy: where Python and MATLAB RAVEN disagree on a default, one value is chosen for both, except where a real implementation difference forces the divergence (different solver stack, different algorithm, different data schema). In that case identical values would turn correct behaviour into incorrect behaviour. Every row states which side has to change or explains why the values stay split.

### Unified values

| Parameter | Python now | MATLAB now | Unify at | Side that changes | Confidence | Evidence |
|---|---|---|---|---|---|---|
| `run_blast.evalue` | `1e-4` ✓ done | `1e-4` | `1e-4` | ~~Python~~ done | High | No downstream effect measured either way (`get_model_from_homology`'s `1e-30` dominates); matches `develop`'s independent PR #91 call |
| `get_model_from_homology.min_align_len` | `100` ✓ done | `100` ✓ done (`200` in RAVEN 2.11.3) | `100` | ~~Python and MATLAB~~ done | High | Directly measured: [Homology cut-off calibration](parameter-tuning/studies/homology-cutoff-calibration.md) |
| `assign_kos.cutoff` | `1e-30` ✓ done | `1e-30` ✓ done (`1e-50` in RAVEN 2.11.3) | `1e-30` | ~~MATLAB~~ done | High | Directly measured: [KEGG HMM cut-off calibration](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md) |
| `assign_kos.min_score_ratio_g` | `0.9` ✓ done | `0.9` ✓ done (`0.8` in RAVEN 2.11.3) | `0.9` | ~~MATLAB~~ done | High | Directly measured, same study |
| `run_ftinit.allow_excretion` | `False` ✓ done | `False` | `False` | ~~Python~~ done (2026-06-20) | High | Recorded, without a measurement, as having no effect at the default `prod_weight`; no measurement is recorded on a page of [Parameter tuning](parameter-tuning/index.md). Unified to remove the inconsistency. Within `ftinit`, the step schedule sets the value (`allow_met_secr`) |

### Settings resolved without unification

The INIT parameters `mip_gap` and `time_limit` of `run_init` and `run_ftinit` are resolved by the genome-scale test with real expression data in [ftINIT parameter calibration and input robustness](parameter-tuning/studies/init-param-calibration.md) (Human-GEM HCT116 and Hart2015), without matching the MATLAB numbers:

- `mip_gap`: solve time is flat across the gap in the single first-step solve, so a tight gap is nearly free there. The docstring of `run_ftinit` attributes the flat time to model construction; the study did not measure the share of model construction. A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`, because every step runs its own schedule of MILP runs, so the full pipeline gives the same result at 0.001, 0.003 and 0.01. Neither 0.001 nor 0.01 is MATLAB's `0.0004`. Keep `None` (Gurobi's own `~1e-4` default is at least as tight as the measured-good `0.001`).
- `time_limit`: RAVEN's `ftINIT` limits a MILP run to 5000 seconds when the run sets none, and its schedules use 120 s, 5000 s and 5 s runs. Python's `ftinit` with a named series caps each scheduled run by the same limits, and `time_limit` lowers the cap; `time_limit=None` leaves an ad-hoc step or a `run_ftinit` call uncapped, but no scheduled run. Measured first-step solves took 23 to 30 s, and full pipelines 81 to 119 s with scaling and 157 s without. In the robustness setup, the gap-fill of one 90 %-dropout model ran longer than 75 minutes; the gap-fill has its own fixed limit of 300 s per task and does not read `time_limit`. The study ran its full pipelines at 600 s; its robustness script sets 120 s, and the limit of the recorded robustness runs is not stated. Keep `None` as the code default. The docstring of `run_ftinit` recommends `120-600 s/step`, a range with no measured basis on this site.

[ftINIT on different solvers](parameter-tuning/studies/init-solver-benchmark.md) measured GLPK honouring the 900 s limit: both steps of the full pipeline hit it, the run took 2182 s and kept 6758 reactions (Jaccard 0.892 against Gurobi). The `scipy` interface (HiGHS) fails because it supports continuous variables only. Gurobi is the backend the genome-scale numbers above were measured on. It completed the run within the overall limit; one scheduled solve stopped at a limit (the warning in the `big_m=1000` run).

### Values kept different

| Parameter | Python | MATLAB | Why |
|---|---|---|---|
| `random_sampling.replace_max_bound` | `False` | `True` | With every bound of 1000 replaced by infinity, the random-objective LP becomes unbounded, because the objective can grow without limit through any reaction that is then unconstrained ([Flux sampling convergence and settings](parameter-tuning/studies/sampling-convergence-calibration.md) gives this mechanism, read from the cobra code; the run with `True` failed with an unbounded status, the sample of the abort was not recorded, and the run with `False` completed 200 samples). Whether MATLAB's own solver path handles `True` was not tested. |
| `random_sampling.loopless_good_reactions` | `True` (loopless FVA) | heuristic (exclude FVA ≥ 999) | The two are different techniques. Loopless FVA excludes only reactions that take part in infeasible cycles, and the MATLAB heuristic also excludes reactions that legitimately reach capacity. Porting the loopless technique to MATLAB is a larger project than changing a default. |
| `merge_models.match_by` | `'name'` | `'metNames'` | Same semantic field (metabolite display name) under a different field name, which results from the cobrapy and COBRA Toolbox schemas; the field name is not tunable. |
| `run_diamond.evalue` | `1e-3` | `1e-3` (implicit) | Both agree at `1e-3`, matching the DIAMOND default. `getDiamond` passes no `-evalue` flag, so it inherits the DIAMOND default and does not follow the explicit `1e-4` of `getBlast`. `run_blast` and `run_diamond` deliberately stay unpaired: each follows the MATLAB call of its own aligner. |
| `predict_localization.time_limit` | `None` | `maxTime=15` (minutes) | Confirmed by reading `localization/predictLocalization.m` (2026-08-28): MATLAB solves the problem with simulated annealing (`maxTime` is its search budget; more time generally improves the heuristic answer, with no optimality guarantee), and Python solves a deterministic MILP (`time_limit` is a solver cutoff; returns a proven-bounded incumbent). The same number has a different role in each, so the values are not unified. A tentative unification at `None` is not adopted, because it assumed that both sides solve the same kind of problem. |
| `predict_localization.default_compartment` | `'c'` | required arg (no default) | MATLAB has no default; Python's `'c'` is a convenience default for the near-universal correct choice and produces no output difference (a MATLAB user must already supply `'c'` explicitly in the common case). Optional, low priority: MATLAB could add the same default. |

## Changes needed in MATLAB RAVEN for parity

No change is open. The changes to `getKEGGModelForOrganism` (`cutOff`, `minScoreRatioG`) and `getModelFromHomology` (`minLen`) are in RAVEN 3, checked against `src/` on RAVEN `develop`:

| Function | RAVEN 2.11.3 | RAVEN 3 |
|---|---|---|
| `getKEGGModelForOrganism`, `cutOff` | `10^-50` | `10^-30` |
| `getKEGGModelForOrganism`, `minScoreRatioG` | `0.8` | `0.9` |
| `getModelFromHomology`, `minLen` | `200` | `100` |

The time-budget parameter of the localisation needs no port: `predictLocalization.m` solves the problem with simulated annealing (`maxTime`, default 15 minutes, a search budget), and raven-toolbox uses a deterministic MILP (`time_limit`, a solver cutoff). See the table of values kept different.

## Open items

- Genome-scale ACHR sampling convergence has no cheap fix. At genome scale (yeast-GEM, default ACHR settings) the median reaction fails the R-hat>1.1 threshold. Neither follow-up fixes it cheaply: reallocating the same step budget onto a larger `thinning` makes no measurable difference, and `method='chrr'` converges on a small model, but its genome-scale cost makes it impractical as a drop-in fix: a probe of 2 chains × 20 samples on yeast-GEM took 136 min (8147.9 s) in total, and the share of the rounding step in that time was not measured. [Flux sampling convergence and settings](parameter-tuning/studies/sampling-convergence-calibration.md) describes the investigation, including a possible future unblock (caching the CHRR rounding transform across calls, an engineering change and not a parameter default, so out of scope here).
- The `gene_scores_from_expression` scoring constants (`factor=5.0`, `max_score=10.0`, `min_score=-5.0`) have no confirmed literature source on either side; see the INIT section.

## References

> Choi HS, Lee SY, Kim TY, Woo HM (2010). In silico identification of gene
> amplification targets for improvement of lycopene production.
> Appl Environ Microbiol 76(10):3097–3105.
> <https://doi.org/10.1128/AEM.00115-10>

> Bordel S, Ågren R, Nielsen J (2010). Sampling the solution space in
> genome-scale metabolic networks reveals transcriptional regulation in key
> enzymes. PLoS Comput Biol 6(7):e1000859.
> <https://doi.org/10.1371/journal.pcbi.1000859>

> Zhang Y, Gao L (2003). On numerical solution of the maximum volume
> ellipsoid problem. SIAM J Optim 14(1):53–76.
> <https://doi.org/10.1137/S1052623401397230>

> Ågren R, Bordel S, Mardinoglu A, Pornputtapong N, Nookaew I, Nielsen J
> (2012). Reconstruction of genome-scale active metabolic networks for 69
> human cell types and 16 cancer types using INIT. PLoS Comput Biol
> 8(5):e1002518.
> <https://doi.org/10.1371/journal.pcbi.1002518>

> Gustafsson J, Anton M, Roshanzamir F, et al. (2023). Generation and
> analysis of context-specific genome-scale metabolic models derived from
> single-cell RNA-Seq data. Proc Natl Acad Sci USA 120(6):e2217868120.
> <https://doi.org/10.1073/pnas.2217868120>

> Thiele I, Vlassis N, Fleming RMT (2014). fastGapFill: efficient gap
> filling in metabolic networks. Bioinformatics 30(17):2529–2531.
> <https://doi.org/10.1093/bioinformatics/btu321>

Not listed: the `gene_scores_from_expression` constants (`factor`, `max_score`, `min_score`). Neither the source of RAVEN nor that of raven-toolbox cites a paper for them. A 2012 paper (Wang et al. 2012, [mCADRE](https://doi.org/10.1186/1752-0509-6-153)) uses categorical scoring and is not the origin. The constants are RAVEN's own choice with no confirmed literature source.
