# Tuned parameter defaults

Every RAVEN parameter with a non-trivial default has been through one of three
processes: matched to a **literature value** from the method's original paper,
**measured** empirically on real or synthetic models, or **kept for consistency**
with an existing convention (a widely-used underlying tool's own default, or a
value already established elsewhere in RAVEN). This page gives the short version
(current default and a one-line reason) grouped by capability, covering both
the MATLAB and Python (raven-toolbox) implementations. For the full measurements
and methodology, follow the linked study.

:::{note} Where the two implementations still differ
RAVEN has existed as MATLAB since 2013 and gained a Python implementation
(raven-toolbox) from 2026; a handful of parameters have only been
re-measured on one side and haven't yet been ported to the other. Neither
implementation's un-measured default was assumed correct going in; where
the two disagreed, the answer was to measure, not to defer to whichever
came first. Every row below states today's actual value(s); where the two
genuinely still differ, both are given, with which side is pending.
[Cross-toolbox parity decisions](#cross-toolbox-parity-decisions) below is
the full accounting, including the cases that are *deliberately* kept
different because the two implementations rest on different solvers or
algorithms.
:::

## Flux sampling

RAVEN MATLAB: `randomSampling` (`method='achr'|'chrr'|'random_objective'`),
`sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`.
raven-toolbox: `random_sampling`, `find_good_reactions`, `max_volume_ellipsoid`.
Both implementations expose all three sampling methods through one entry point.

| Parameter | Default | How determined |
|---|---|---|
| `method` | `'achr'` (Python) / `'random_objective'` (MATLAB) | Literature: ACHR gives near-uniform interior sampling; the random-objective method draws polytope vertices instead. Both algorithms are implemented and selectable on both sides; only which one is the *default* differs. |
| `thinning` | `100` | Upstream convention (cobrapy's own ACHR default, which RAVEN's Python side inherited). **Measured insufficient at genome scale**: yeast-GEM gives only ~12 effective samples from 300 stored (ESS), and independent chains frequently disagree entirely (median Gelman-Rubin R-hat fails the convergence threshold). No cheap fix found; see the [convergence study](parameter-tuning/studies/sampling-convergence-calibration.md). |
| `warmup` | `1000` | Upstream convention (cobrapy). |
| `n_objectives` | `2` | Literature: [Bordel et al. 2010](https://doi.org/10.1371/journal.pcbi.1000859). |
| `replace_max_bound` | `False` | Measured: applying the alternative (`True`) inside the Python/cobrapy solver stack makes the sampler unbounded on standard RAVEN-convention models (±1000 bounds). Kept different by design between implementations, a solver-stack constraint, not a preference; whether MATLAB's own solver path handles it safely wasn't tested here. |
| `loopless_good_reactions` | `True` | Measured more correct than the alternative fixed-threshold (±999) heuristic, which over-excludes reactions that legitimately reach capacity. The proper technique is implemented on the Python side only so far; porting it is a bigger project than a default flip. |
| `n_samples`, `seed`, `min_flux`, `max_attempts` | `1000`, `None`, `False`, `100` | Same on both sides / no evidence favoured a different value. |
| `flux_tol` (in `find_good_reactions`) | `1e-9` | Python-only helper (supports the random-objective method's target selection); no cross-implementation comparison. |
| `maxiter` (in `max_volume_ellipsoid`) | `150` | Literature: [Zhang & Gao 2003](https://doi.org/10.1137/S1052623401397230). |
| `tol`, `reg` (in `max_volume_ellipsoid`) | `1e-6`, `1e-8` | Same on both sides. |

**Full detail:** [sampling convergence study](parameter-tuning/studies/sampling-convergence-calibration.md)
(the primary measurement)

## FSEOF

RAVEN MATLAB: `FSEOF`. raven-toolbox: `fseof`.

| Parameter | Default | How determined |
|---|---|---|
| `n_steps` | `10` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10). |
| `max_fraction` | `0.9` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); measured: values below 0.9 pick up spurious targets on iJO1366. |
| `correlation_threshold` | `0.9` | Literature: [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); measured: 0.7 adds 4 spurious amplification targets on iJO1366. |
| `flux_eps` | `1e-6` | Measured on iJO1366: the classification uses the fixed thresholds `1e-10` and `1e-8`, as RAVEN does; `flux_eps` gates the check against the theoretical maximum, and the target counts are identical at `1e-8`, `1e-7` and `1e-6`. |

**Full detail:** [Parameter benchmarks](parameter-tuning/benchmarks.md)

## INIT / ftINIT

RAVEN MATLAB: `runINIT`, `scoreModel`, `getINITModel`, `ftINIT`, `prepINITModel`,
`ftINITInternalAlg`, `getINITSteps`. raven-toolbox:
`score_reactions_from_genes`, `gene_scores_from_expression`, `ftinit`,
`prep_init_model`, `run_ftinit`, `get_init_steps`, `classify_reactions`.

Only the MATLAB side has tINIT (`runINIT`, `getINITModel`); raven-toolbox
implements ftINIT alone; see
[14. Context-specific models](guide/init.md). Rows below that were measured
across both algorithms say so.

| Parameter | Default | How determined |
|---|---|---|
| `prod_weight` | `0.5` | Literature: [Ågren et al. 2012](https://doi.org/10.1371/journal.pcbi.1002518) (the original INIT paper). |
| `allow_excretion` | `False` | Measured zero effect at the default `prod_weight` across all three INIT entry points as they stood then; raven-toolbox has since dropped the two tINIT ones. |
| `mip_gap` | `None` on the Python side (solver default); `0.0004` on the MATLAB side | Acts on the step-0 solve and on any step without a schedule of MILP runs; a named series such as `1+1` ignores it, because every step runs its own schedule. Measured on Human-GEM (HCT116) in the step-0 solve: the time is flat at 24 to 25 s, the Jaccard index to the 0.001 result is about 0.99 at 0.01, and the Jaccard index to the tightest result falls below 0.97 from 0.03. Python's `None` needs no change. |
| `time_limit` | `None` on the Python side; `5000` seconds on the MATLAB side | RAVEN's `ftINIT` sets the Gurobi `TimeLimit` of a MILP run without its own limit to 5000 seconds, and the step schedules of `getINITSteps` use runs of 120 s, 5000 s and 5 s. In Python, `ftinit` with a named series caps each scheduled run by its own limit and `time_limit` lowers that cap further; `time_limit=None` leaves an ad-hoc step or a `run_ftinit` call uncapped, but no scheduled run. Measured on Human-GEM HCT116 (single runs): single-step solves took 23 to 30 s and full pipelines 82 to 118 s. In the [robustness setup](parameter-tuning/studies/init-param-calibration.md) (degraded input, task layer on), an unbounded gap-fill MILP on one 90 %-dropout model ran longer than 75 minutes. `None` is the default; the working range for hard or noisy input is 120 to 600 s per step. |
| `series` | `'1+1'` | Literature: [Gustafsson et al. 2023](https://doi.org/10.1073/pnas.2217868120) (the ftINIT paper). |
| `force_on` | `0.1` | RAVEN's original value; measured near-insensitive across a 0.02–0.5 range. |
| `big_m` | `1000.0` | The cap on each scored reaction's own big-M, as in `ftINITInternalAlg`: the big-M of a reaction is `max(min(ub, big_m), min(-lb, big_m), 0)`, raised to `force_on` where the "on" floor needs it, and an infinite bound counts as `big_m`. The cap limits the flux a reaction can carry when it is on (it is the largest big-M of a scored reaction in its on/off constraint); it is not a bound set on the reaction in the model. |
| `eps` | `1.0` | Same on both sides. |
| `resolve_ties`, `prove_abs_gap` | `False`, `None`, both opt-in; MATLAB has them as `resolveTies`/`proveAbsGap` at the same defaults | `resolve_ties` fixes the answer among equal-score optima in phases: it holds the score objective at its optimum, minimises the count of kept removable (negative-score) reactions, then among those minimises the summed id rank of the kept ones (a merged reaction is ranked by the smallest original id of its group), then takes the fluxes with the least total absolute flux (relative and absolute gap 1e-6), then those with the least id-rank-weighted backward flux. The last ftINIT step skips the last two phases, because no later step reads its fluxes. Measured on Human-GEM v2.0.0-38 (one cell line, seeds 1234 and 7): with the default escalation the seed-to-seed difference is 110 reactions and 17 predicted essential genes. `resolve_ties=True` gives identical reaction sets at a fixed seed and reduces the seed-to-seed difference to 41 reactions and 1 gene, at about 3.6 times the run time (about 14 min against 4 min at `time_limit=1800`). With `prove_abs_gap=1.0` as well, the difference is 1 reaction and 0 genes, at about 26 times the baseline run time (about 100 min), of which step 1 takes about 60 % (3300 to 3650 s), mostly in its two flux phases, and step 2 another 1650 to 2500 s; no build without `resolve_ties` was run with `prove_abs_gap`. The flux phases (`phase2c-minflux`, `phase2d-direction`) reach the time limit in most builds, and a warning names each phase adopted at the limit. A tie-break that finds no incumbent in phase 2a or 2b is dropped without a warning, and the baseline escalation raises no warning and ends 4 to 12 below the step 1 optimum, so a build without a warning is not necessarily proven or tie-broken. |
| `factor`, `max_score`, `min_score` (in `gene_scores_from_expression`) | `5.0`, `10.0`, `-5.0` | RAVEN's own formula; previously attributed to "Wang et al. 2012" here, which was checked and could not be confirmed; no source in either implementation cites a paper for it. |
| `score_reactions_from_genes` / `classify_reactions` arguments | various | Same on both sides / standard practice. |

**Full detail:** [INIT parameter calibration study](parameter-tuning/studies/init-param-calibration.md)
(the primary measurement, genome-scale Human-GEM) ·
[INIT solver benchmark](parameter-tuning/studies/init-solver-benchmark.md) ·
[ftINIT reproducibility](parameter-tuning/studies/ftinit-determinism.md)
(`resolve_ties=True` gives identical reaction sets at a fixed seed and a seed-to-seed difference of 41 reactions and 1 gene; adding `prove_abs_gap=1.0` reduces it to 1 reaction and 0 genes at about 26 times the run time) ·
[Human-GEM validation vs MATLAB RAVEN](parameter-tuning/studies/humangem-validation.md)
(Jaccard 0.964–0.988 against RAVEN across 5 cell lines)

## Gap-filling

RAVEN MATLAB: `fillGaps` (connectivity mode), ported as `connect_blocked_reactions`.
`fill_gaps_fast_lp` and `fill_gaps_milp` are the counterparts of RAVEN's
`gapFillFastLP` and `gapFillMILP`.

| Parameter | Default | How determined |
|---|---|---|
| `epsilon` (in `fill_gaps_fast_lp`) | `0.0001` | Literature: [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) (the fastGapFill paper). |
| `eps` (in `connect_blocked_reactions`) | `1.0` | Measured on a synthetic supply-limited model; reliable noise filter for RAVEN-convention (±1000-bound) models; lower it for tightly-constrained exchanges. |
| `penalty`, `allow_net_production` (in `connect_blocked_reactions`) | `1.0`, `False` | Measured / standard practice for reconstruction (vs. curation) use. |
| `big_m` (in `fill_gaps_milp`) | `1000.0` | Matches RAVEN's ±1000 bound convention. It caps an unbounded template reaction only when the merged model has no finite bound; otherwise the largest finite bound does. |

**Full detail:** [Parameter benchmarks](parameter-tuning/benchmarks.md)

## Homology-based reconstruction

RAVEN MATLAB: `getModelFromHomology`, `getBlast`, `getDiamond`. raven-toolbox:
`get_model_from_homology`, `run_blast`, `run_diamond`.

| Parameter | Default | How determined |
|---|---|---|
| `evalue` (`run_blast`) | `1e-4` | Matches MATLAB's `getBlast` (hardcodes `-evalue 10e-5`); measured to have no effect on the final model either way, since `get_model_from_homology`'s much stricter filters dominate downstream. |
| `evalue` (`run_diamond`) | `1e-3` | Matches MATLAB's `getDiamond`, which passes no `-evalue` flag and so inherits DIAMOND's own default. Deliberately *not* the same value as `run_blast`; each aligner tracks its own MATLAB call, not the other Python aligner. |
| `threads` | every CPU the process may run on (Python); the cores assigned to MATLAB (MATLAB) | Measured deterministic across thread counts, pure performance change, ~1.9–4× speedup. Both sides use all available cores. |
| `max_evalue` | `1e-30` | Measured **inert** from `1e-4` to `1e-50`; identity and alignment-length have already excluded whatever a looser e-value would admit. |
| `min_align_len` | `100` on the Python side; MATLAB still uses `200` | Measured against independent KEGG and OMA ortholog references across a 4-organism relatedness series: recovers 3–4 points of recall over `200` for ≤0.6 points of precision cost. A MATLAB back-port is proposed but not yet done. |
| `min_identity` | `40` | Same study: the binding filter and the measured optimum, weighting a wrongly-transferred reaction as worse than a missing one. |
| `bidirectional` | `True` | Same on both sides. |

An earlier arm of the same study tried scoring against curated GEMs (hanpo-GEM,
rhto-GEM) built by this same reconstruction method, and was retired once it showed
the obvious circularity directly: agreement with the curated model peaked exactly
at that model's own build settings and collapsed one step past them.

**Full detail:** [homology cut-off calibration study](parameter-tuning/studies/homology-cutoff-calibration.md)
(the primary measurement, including the retired curated-GEM arm)

## KEGG-based reconstruction

RAVEN MATLAB: `getKEGGModelForOrganism` (the KO-assignment sub-step's exact internal
name hasn't been independently confirmed). raven-toolbox: `assign_kos`,
`run_hmmsearch`, `build_ko_hmm`, and the `get_kegg_model_*` family.

| Parameter | Default | How determined |
|---|---|---|
| `cutoff` (in `assign_kos`) | `1e-30` on the Python side; MATLAB still uses `1e-50` | Measured against real KEGG gene→KO annotations across 4 organisms of varying study depth: the tighter value sits inside the tail of *real* matches (~20 orders of magnitude above the noise floor), discarding genuine hits for no gain. MATLAB's port is still pending. |
| `min_score_ratio_g` (in `assign_kos`) | `0.9` on the Python side; MATLAB still uses `0.8` | Same study: the real precision lever (0.8→0.95 lifts precision ~0.07–0.10 for ~0.02 recall). MATLAB's port is still pending. |
| `min_score_ratio_ko` (in `assign_kos`) | `0.3` | Same study: measured empirically **inert** (varying it changes precision/recall by ≤0.02); kept at the original value since it does nothing either way. |
| `seq_identity` (in `build_ko_hmm`) | `0.9` | Literature: CD-HIT's own recommendation for protein clustering. |
| `threads` (`run_hmmsearch`, `build_ko_hmm`) | every CPU the process may run on | Performance-only; HMMER is deterministic (to within insignificant float noise) across thread counts. |
| `keep_spontaneous`, `keep_undefined_stoich`, `keep_incomplete`, `keep_general` (`get_kegg_model_*`) | `True`, `True`, `True`, `False` | Same on both sides / standard draft-reconstruction practice. |

**Full detail:** [KEGG HMM cut-off calibration study](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md)
(the primary measurement, 4 organisms against real KEGG annotations)

## Sub-cellular localisation

RAVEN MATLAB: `predictLocalization`. raven-toolbox: `predict_localization`.
These solve the problem with different algorithms: MATLAB uses simulated
annealing, a stochastic heuristic with no optimality guarantee, while the Python
side solves a deterministic MILP. Several parameters below are therefore not a
question of which value is right; the same number means something different in
a heuristic's search budget than in a solver's optimality gap.

Compartment assignment is in development on the Python side and is not at parity
with MATLAB. The defaults below are current, but the method they configure is
still changing.

| Parameter | Default | How determined |
|---|---|---|
| `default_compartment` | `'c'` on the Python side; MATLAB requires the argument every call | Convenience default: cytosol is correct for the vast majority of reactions. Not a value disagreement, since MATLAB has no default to compare against. |
| `transport_cost` | `0.5` | Not independently benchmarked; same on both sides. Calibration note: for real (non-integer-scale) predictor scores, this typically needs dialing down; see the linked study. |
| `time_limit` (Python) / `maxTime` (MATLAB) | `None` (uncapped) on the Python side; MATLAB's `maxTime` defaults to `15` minutes | Not a value to unify: MATLAB's number is a simulated-annealing search budget (more time generally means a better heuristic answer, not a proof of optimality), while Python's is a MILP solver cutoff (returns a proven-bounded incumbent). Python's `None` was validated at ~2.5 minutes on yeast-GEM, the primary development-scale model. Whether the MILP needs a cap at all for harder cases hasn't been stress-tested. |
| `mip_gap` | `None` | Python-side-only; MATLAB's heuristic has no analogous optimality-gap concept. |

**Full detail:** the measurements behind these values (the yeast-GEM benchmark,
the head-to-head against MATLAB's `predictLocalization`, the predictor
benchmarks across four organisms, and the design documents) are in
[raven-gecko-parity](https://github.com/CompMetEng/raven-gecko-parity/tree/develop/docs/localization),
with the rest of the work in progress on this method.

## Model manipulation

RAVEN MATLAB: `removeGenes`, `mergeModels`, `addRxns`, `addTransport`, `simplifyModel`
(reversibility-constraining and duplicate-removal modes). raven-toolbox:
`remove_genes`, `merge_models`, `add_reactions_from_equations`,
`add_transport_reactions`, `constrain_reversible_reactions`, `find_duplicate_reactions`.

| Parameter | Default | How determined |
|---|---|---|
| `blocked_reactions` (in `remove_genes`) | `'constrain'` on the Python side; MATLAB's `removeGenes` with `removeBlockedRxns` false does the same | Measured on e_coli_core: keeping a reaction unchanged after it loses its last gene gives false-positive growth after an essential gene is removed (it survives with an empty gene rule). `'constrain'` sets the bounds of such a reaction to 0 and keeps the reaction; `'remove'` deletes it and is opt-in, for gene-essentiality or metabolic-engineering use where the reaction should disappear; `'keep'` leaves it unchanged. |
| `eps` (in `constrain_reversible_reactions`) | `1e-9` | Matches Gurobi's own default primal feasibility tolerance. |
| `match_by` (in `merge_models`) | `'name'` (Python) / `'metNames'` (MATLAB) | Same semantic field (metabolite display name), different schema field name, not a value disagreement to resolve. |
| `remove_orphans`, `mets_by`, `ignore_direction`, `reversible`, `only_to_existing` | various | Python-side additions/refinements; no direct MATLAB equivalent to compare against. |

**Full detail:** [Parameter benchmarks](parameter-tuning/benchmarks.md)

## Tasks

RAVEN MATLAB: `checkTasks`. raven-toolbox: `check_tasks`, `find_task_essential_reactions`.

| Parameter | Default | How determined |
|---|---|---|
| `close_boundaries` (both functions) | `False` | Matches RAVEN's `checkTasks`, which leaves the model's own exchange reactions open; published task lists were curated against that. `True` makes the task the whole boundary, as `closeModel` does in RAVEN. |

**Full detail:** [Parameter benchmarks](parameter-tuning/benchmarks.md)

## Cross-toolbox parity decisions

Policy: where Python and MATLAB RAVEN disagree on a default, pick one value for
both rather than let them diverge, except where the divergence is forced by a real
implementation difference (different solver stack, different algorithm, different
data schema), in which case forcing identical values would change correct
behaviour into incorrect behaviour. Every row below either says which side has to
change, or explains why it stays split.

### Unify: one value, both toolboxes converge

| Parameter | Python now | MATLAB now | Unify at | Side that changes | Confidence | Evidence |
|---|---|---|---|---|---|---|
| `run_blast.evalue` | `1e-4` ✓ done | `1e-4` | **`1e-4`** | ~~Python~~ done | High | No downstream effect measured either way (`get_model_from_homology`'s `1e-30` dominates); matches `develop`'s independent PR #91 call |
| `get_model_from_homology.min_align_len` | `100` ✓ done | `200` | **`100`** | Python done; MATLAB pending | High | Directly measured: [homology cut-off calibration study](parameter-tuning/studies/homology-cutoff-calibration.md) |
| `assign_kos.cutoff` | `1e-30` | `1e-50` | **`1e-30`** | MATLAB | High | Directly measured: [KEGG HMM cut-off calibration study](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md) |
| `assign_kos.min_score_ratio_g` | `0.9` | `0.8` | **`0.9`** | MATLAB | High | Directly measured, same study |
| `get_init_model.allow_excretion` | `False` ✓ done | `False` | **`False`** | ~~Python~~ done (2026-06-20) | High | Zero effect at default `prod_weight`, pure inconsistency; see `parameter-tuning/benchmarks.md` |

### Resolved without unifying: `run_init`/`run_ftinit` `mip_gap`/`time_limit`

These were listed as gated pending a genome-scale test with real expression
data. That test already existed
([INIT parameter calibration study](parameter-tuning/studies/init-param-calibration.md), Human-GEM
HCT116/Hart2015); it just hadn't been connected to this question. It resolves
both parameters, but not by matching MATLAB's numbers:

- **`mip_gap`:** solve time is flat across the gap in the single step-0 solve (model build dominates), so a tight gap is nearly free there. A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`, because every step runs its own schedule of MILP runs, so the full pipeline gives the same result at 0.001, 0.003 and 0.01. Neither 0.001 nor 0.01 is MATLAB's `0.0004`. **Keep `None`** (Gurobi's own `~1e-4` default is at least as tight as the measured-good `0.001`).
- **`time_limit`:** RAVEN's `ftINIT` limits a MILP run to 5000 seconds when the run sets none, and its schedules use 120 s, 5000 s and 5 s runs. Python's `ftinit` with a named series caps each scheduled run by the same limits, and `time_limit` lowers the cap; `time_limit=None` leaves an ad-hoc step or a `run_ftinit` call uncapped, but no scheduled run. Measured step-0 solves took 23 to 30 s and full pipelines 82 to 118 s. In the robustness setup, one unbounded gap-fill MILP on a 90 %-dropout model ran longer than 75 minutes. The working values of the study are `120-600 s/step`. **Keep `None`** as the code default (correct for clean-data and single-step use, where no run-away has been observed); the docstring states the working values.

The [INIT solver benchmark](parameter-tuning/studies/init-solver-benchmark.md) measured GLPK honouring the 900 s limit: both steps of the full pipeline hit it, the run took 2182 s and kept 6758 reactions (Jaccard 0.892 against Gurobi). The `scipy` interface (HiGHS) fails because it supports continuous variables only. Gurobi is the backend the genome-scale numbers above were measured on, and the only one that completed without a step hitting the limit.

### Keep different: forcing identical values would break correctness

| Parameter | Python | MATLAB | Why |
|---|---|---|---|
| `random_sampling.method` | `'achr'` | `'random_objective'` | Different algorithms, not a flag. ACHR is methodologically preferred (uniform interior sampling vs vertex-biased). Unifying means porting ACHR into MATLAB RAVEN, a real implementation project, tracked separately, not a default change. |
| `random_sampling.replace_max_bound` | `False` | `True` | Applying MATLAB's `True` inside cobrapy/optlang makes the sampler unbounded on standard RAVEN-convention models (measured; see `sampling.md`). Whether MATLAB's own solver path handles `True` safely wasn't tested here; either way this is a solver-stack constraint, not a preference. |
| `random_sampling.loopless_good_reactions` | `True` (loopless FVA) | heuristic (exclude FVA ≥ 999) | Different techniques, not a value. Python's is more correct; MATLAB's heuristic over-excludes reactions that legitimately reach capacity. Porting the proper technique to MATLAB is a bigger project than a default flip. |
| `merge_models.match_by` | `'name'` | `'metNames'` | Same semantic field (metabolite display name), different field name, an artifact of cobrapy vs COBRA Toolbox schemas, not a tunable behaviour. |
| `run_diamond.evalue` | `1e-3` | `1e-3` (implicit) | Not actually different: both already agree at `1e-3`, matching DIAMOND's own default. `getDiamond` passes no `-evalue` flag at all, so it inherits DIAMOND's default rather than following `getBlast`'s explicit `1e-4`. `run_blast` and `run_diamond` deliberately stay unpaired: each tracks its own aligner's MATLAB call, not each other. |
| `predict_localization.time_limit` | `None` | `maxTime=15` (minutes) | Confirmed by reading `core/predictLocalization.m` directly (2026-08-28): MATLAB solves the problem with simulated annealing (`maxTime` is its search budget; more time generally improves the heuristic answer, no optimality guarantee either way), while Python solves a deterministic MILP (`time_limit` is a solver cutoff; returns a proven-bounded incumbent). The same number plays a structurally different role in each; not a value to unify. Previously listed as a tentative unify-at-`None` candidate, which assumed both sides were solving the same kind of problem. |
| `predict_localization.default_compartment` | `'c'` | required arg (no default) | MATLAB has no default at all; Python's `'c'` is a convenience default for the near-universal correct choice, produces no output difference (a MATLAB user must already supply `'c'` explicitly in the common case). Optional, low-priority: MATLAB could add the same default. |

## Changes needed in MATLAB RAVEN for parity

All rows below were re-checked directly against `core/*.m` on `origin/develop` in
the RAVEN MATLAB repo on 2026-08-28 (not inferred from raven-toolbox's own
prior write-ups).

| Change | Priority | Evidence |
|---|---|---|
| `getKEGGModelForOrganism`'s `cutOff` parameter: `10^-50` → `10^-30` | High | [KEGG HMM cut-off calibration study](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md); current value confirmed directly in `external/kegg/getKEGGModelForOrganism.m` |
| Same function, `minScoreRatioG`: `0.8` → `0.9` | High | Same study and same confirmation |
| `getModelFromHomology`'s `minLen`: `200` → `100` | Medium | [homology cut-off calibration study](parameter-tuning/studies/homology-cutoff-calibration.md); confirmed directly in `core/getModelFromHomology.m`. A fix already exists as an uncommitted local branch (`fix/homology-minlen`) but is stale relative to current `origin/develop` (file moved `reconstruction/homology/` → `core/`) and hasn't been pushed. |

Localisation's time-budget parameter was removed from this table: `core/predictLocalization.m`
confirmed MATLAB solves the problem with simulated annealing (`maxTime`, default 15 minutes,
a search budget), not the deterministic MILP raven-toolbox uses (`time_limit`, a solver
cutoff), different algorithms, not a value to port. See the "Keep different" table above.

## Still open

- **Genome-scale ACHR sampling convergence** has no cheap fix.
  **investigated, no cheap fix found.** At genome scale (yeast-GEM, default
  ACHR settings) the *median* reaction fails the R-hat>1.1 threshold. Neither
  follow-up tried fixes it cheaply: reallocating the same step budget onto a
  bigger `thinning` makes no measurable difference; `method='chrr'` genuinely
  converges on a small model but its genome-scale cost (a fixed per-chain
  rounding step alone costing ~80 min in a trivial probe) makes it impractical
  as a drop-in fix today. See the
  [sampling convergence calibration study](parameter-tuning/studies/sampling-convergence-calibration.md)
  for the full investigation, including a possible future unblock (caching
  CHRR's rounding transform across calls, an engineering change, not a
  parameter default, so out of scope here).
- The `gene_scores_from_expression` scoring constants (`factor=5.0`,
  `max_score=10.0`, `min_score=-5.0`) have no confirmed literature source on
  either side; see the INIT section above.

## References

> Choi HS, Lee SY, Kim TY, Woo HM (2010). **In silico identification of gene
> amplification targets for improvement of lycopene production.**
> *Appl Environ Microbiol* 76(10):3097–3105.
> <https://doi.org/10.1128/AEM.00115-10>

> Bordel S, Ågren R, Nielsen J (2010). **Sampling the solution space in
> genome-scale metabolic networks reveals transcriptional regulation in key
> enzymes.** *PLoS Comput Biol* 6(7):e1000859.
> <https://doi.org/10.1371/journal.pcbi.1000859>

> Zhang Y, Gao L (2003). **On numerical solution of the maximum volume
> ellipsoid problem.** *SIAM J Optim* 14(1):53–76.
> <https://doi.org/10.1137/S1052623401397230>

> Ågren R, Bordel S, Mardinoglu A, Pornputtapong N, Nookaew I, Nielsen J
> (2012). **Reconstruction of genome-scale active metabolic networks for 69
> human cell types and 16 cancer types using INIT.** *PLoS Comput Biol*
> 8(5):e1002518.
> <https://doi.org/10.1371/journal.pcbi.1002518>

> Gustafsson J, Anton M, Roshanzamir F, et al. (2023). **Generation and
> analysis of context-specific genome-scale metabolic models derived from
> single-cell RNA-Seq data.** *Proc Natl Acad Sci USA* 120(6):e2217868120.
> <https://doi.org/10.1073/pnas.2217868120>

> Thiele I, Vlassis N, Fleming RMT (2014). **fastGapFill: efficient gap
> filling in metabolic networks.** *Bioinformatics* 30(17):2529–2531.
> <https://doi.org/10.1093/bioinformatics/btu321>

Not listed: the `gene_scores_from_expression` constants (`factor`, `max_score`,
`min_score`) were previously attributed to "Wang et al. 2012" in this and
raven-toolbox's own docs. That attribution was checked against RAVEN's and
raven-toolbox's own source (neither cites a paper) and against the one 2012
Wang metabolic-modelling paper findable (mCADRE, a categorical method
unrelated to this continuous formula), and could not be confirmed. Treat the
scoring constants as RAVEN's own choice with no confirmed literature source
until a real citation turns up.
