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
| `flux_eps` | `1e-6` on the Python side; MATLAB has no threshold at all | Measured: an explicit `1e-6` floor avoids classifying accumulated solver noise as a false-positive knockdown target on genome-scale models. MATLAB's target classification is a bare float comparison with no tolerance whatsoever, stricter than any fixed floor; real solver noise there is expected to produce at least as many spurious classifications as measured here, likely more. |

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
| `mip_gap` | `None` on the Python side (solver default); `0.0004` on the MATLAB side | Measured on genome-scale Human-GEM: the solver's own gap (~1e-4 on Gurobi) is already at least as tight as the measured-good value, so Python's `None` needs no change; genome-scale users get concrete numbers (`0.01` for the full ftINIT pipeline) documented rather than a single hardcoded default, since the right value depends on single-step vs. full-pipeline use. |
| `time_limit` | `None` (uncapped) on the Python side; `5000 ms` on the MATLAB side | The same genome-scale study found the MATLAB value too tight by orders of magnitude (real solves took 42–901s+) but also a real >75-minute uncapped runaway case on degraded input on the Python side; `None` was kept as the safer default there, with the measured working range (120–600s/step) documented for hard or noisy input. |
| `series` | `'1+1'` | Literature: [Gustafsson et al. 2023](https://doi.org/10.1073/pnas.2217868120) (the ftINIT paper). |
| `force_on` | `0.1` | RAVEN's original value; measured near-insensitive across a 0.02–0.5 range. |
| `big_m` | `100.0` | RAVEN's original value; confirmed as an intentional LP-relaxation tightener (not a flux cap); see the linked study for why. |
| `eps` | `1.0` | Same on both sides. |
| `resolve_ties`, `prove_abs_gap`, `reference_reactions` | `False`, `None`, `None`, all opt-in; MATLAB has the first two as `resolveTies`/`proveAbsGap` at the same defaults, and not the third | Measured on genome-scale Human-GEM: the MILP is degenerate (99.7% of removable reactions tied), so the default escalation is both non-deterministic across seeds and, separately, silently suboptimal (351 kept reactions vs. the true optimum's 349). `resolve_ties=True` halves the seed-to-seed swing in predicted essential genes; `prove_abs_gap=1.0` recovers the true optimum. `reference_reactions` (requires `resolve_ties=True`) anchors a re-extraction to a prior build's kept set, cutting spurious essential-gene drift after a small template edit 13x (13 → 1 flips) in one measured case, the stability lever the other two don't provide. |
| `factor`, `max_score`, `min_score` (in `gene_scores_from_expression`) | `5.0`, `10.0`, `-5.0` | RAVEN's own formula; previously attributed to "Wang et al. 2012" here, which was checked and could not be confirmed; no source in either implementation cites a paper for it. |
| `score_reactions_from_genes` / `classify_reactions` arguments | various | Same on both sides / standard practice. |

**Full detail:** [INIT parameter calibration study](parameter-tuning/studies/init-param-calibration.md)
(the primary measurement, genome-scale Human-GEM) ·
[INIT solver benchmark](parameter-tuning/studies/init-solver-benchmark.md) ·
[ftINIT reproducibility](parameter-tuning/studies/ftinit-determinism.md)
(recommend `resolve_ties=True, prove_abs_gap=1.0` for determinism; add
`reference_reactions` for stability under a curated template, 13x less spurious
essential-gene drift, measured) ·
[Human-GEM validation vs MATLAB RAVEN](parameter-tuning/studies/humangem-validation.md)
(Jaccard 0.975–0.980 across 5 cell lines)

## Gap-filling

RAVEN MATLAB: `fillGaps` (connectivity mode), ported as `connect_blocked_reactions`.
`fill_gaps_fast_lp` and `fill_gaps_kumar_milp` are the counterparts of RAVEN's
`gapFillFastLP` and `gapFillMILP`.

| Parameter | Default | How determined |
|---|---|---|
| `epsilon` (in `fill_gaps_fast_lp`) | `0.0001` | Literature: [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) (the fastGapFill paper). |
| `eps` (in `connect_blocked_reactions`) | `1.0` | Measured on a synthetic supply-limited model; reliable noise filter for RAVEN-convention (±1000-bound) models; lower it for tightly-constrained exchanges. |
| `penalty`, `allow_net_production` (in `connect_blocked_reactions`) | `1.0`, `False` | Measured / standard practice for reconstruction (vs. curation) use. |
| `big_m` (in `fill_gaps_kumar_milp`) | `1000.0` | Matches RAVEN's ±1000 bound convention. It caps an unbounded template reaction only when the merged model has no finite bound; otherwise the largest finite bound does. |

**Full detail:** [Parameter benchmarks](parameter-tuning/benchmarks.md)

## Homology-based reconstruction

RAVEN MATLAB: `getModelFromHomology`, `getBlast`, `getDiamond`. raven-toolbox:
`get_model_from_homology`, `run_blast`, `run_diamond`.

| Parameter | Default | How determined |
|---|---|---|
| `evalue` (`run_blast`) | `1e-4` | Matches MATLAB's `getBlast` (hardcodes `-evalue 10e-5`); measured to have no effect on the final model either way, since `get_model_from_homology`'s much stricter filters dominate downstream. |
| `evalue` (`run_diamond`) | `1e-3` | Matches MATLAB's `getDiamond`, which passes no `-evalue` flag and so inherits DIAMOND's own default. Deliberately *not* the same value as `run_blast`; each aligner tracks its own MATLAB call, not the other Python aligner. |
| `threads` | `max(1, cpu_count-1)` (Python); dynamic "all cores" (MATLAB) | Measured deterministic across thread counts, pure performance change, ~1.9–4× speedup. Not treated as a "value" that needs unifying, since both sides already mean "use the available cores". |
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
| `threads` (`run_hmmsearch`, `build_ko_hmm`) | `max(1, cpu_count-1)` | Performance-only; HMMER is deterministic (to within insignificant float noise) across thread counts. |
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
| `blocked_reactions` (in `remove_genes`) | `'remove'` on the Python side; MATLAB's equivalent policy keeps the reaction | Measured on e_coli_core: keeping the reaction gives false-positive growth after an essential gene is removed (it survives with an empty gene rule). `'remove'` is correct for gene-essentiality / metabolic-engineering use; the keep-style policy remains available on the Python side too, for annotation-curation workflows. MATLAB's port of this fix is still pending. |
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
| `fseof.flux_eps` | `1e-6` | implicit `1e-8` | **`1e-6`** | MATLAB (needs exposing as a tunable first) | High | Measured: `1e-8` catches 21 solver-noise false positives (std≈5e-7, below Gurobi's feasibility tolerance accumulated genome-wide); see `parameter-tuning/benchmarks.md` |
| `remove_genes.blocked_reactions` | `'remove'` | `'keep'` | **`'remove'` semantics** | MATLAB | High | Measured on e_coli_core: `'keep'` gives false-positive growth after an essential gene is removed; see `parameter-tuning/benchmarks.md` |
| `get_init_model.allow_excretion` | `False` ✓ done | `False` | **`False`** | ~~Python~~ done (2026-06-20) | High | Zero effect at default `prod_weight`, pure inconsistency; see `parameter-tuning/benchmarks.md` |

### Resolved without unifying: `run_init`/`run_ftinit` `mip_gap`/`time_limit`

These were listed as gated pending a genome-scale test with real expression
data. That test already existed
([INIT parameter calibration study](parameter-tuning/studies/init-param-calibration.md), Human-GEM
HCT116/Hart2015); it just hadn't been connected to this question. It resolves
both parameters, but not by matching MATLAB's numbers:

- **`mip_gap`:** solve time is flat across the gap at single-step scale (model
  build dominates), so a tight gap is nearly free there; the full genome-scale
  pipeline *does* benefit from loosening to `0.01` (~37% faster, Jaccard 0.995).
  Neither number is MATLAB's `0.0004` specifically, and the right choice depends
  on single-step vs. full-pipeline use, so this stays a documented choice rather
  than a new hardcoded default. **Keep `None`** (Gurobi's own `~1e-4` default is
  at least as tight as the measured-good `0.001`); docstring updated with the
  measured numbers.
- **`time_limit`:** the more consequential finding. MATLAB's `5000 ms` cap is far
  too tight for genome scale (measured solves there took 42-901s+); Python's
  uncapped `None` has a real, measured failure mode, one severely-degraded-input
  case ran **>75 minutes** before being manually killed. The study's own working
  values are `120-600 s/step` (ftINIT) and `400 s` (tINIT). **Keep `None`** as the
  code default (still correct for clean-data / single-step use where it's never
  observed to run away), but the docstring now states the measured working values
  and the >75 min risk explicitly, so users degrading input quality know to set a
  cap rather than discovering the runaway case themselves.

This doesn't touch the separate, still-valid finding in the
[INIT solver benchmark](parameter-tuning/studies/init-solver-benchmark.md) that GLPK
ignores `configuration.timeout` entirely and HiGHS doesn't work with cobra in
this stack; Gurobi remains the only backend genome-scale numbers above were
measured on, and the only one a `time_limit` value does anything on today.

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
| `run_blast`/`run_diamond`/`run_hmmsearch`/`build_ko_hmm` `threads` | `max(1, cpu_count-1)` | all cores | Confirmed deterministic regardless of thread count; doesn't affect output, so this is a resource-policy choice (leave one core free), not a correctness-relevant value. Both are dynamic ("use available cores") in spirit. |

## Changes needed in MATLAB RAVEN for parity

All rows below were re-checked directly against `core/*.m` on `origin/develop` in
the RAVEN MATLAB repo on 2026-08-28 (not just inferred from raven-toolbox's own
prior write-ups, which is how the FSEOF and localization rows below turned out
to need correcting from an earlier version of this table).

| Change | Priority | Evidence |
|---|---|---|
| `getKEGGModelForOrganism`'s `cutOff` parameter: `10^-50` → `10^-30` | High | [KEGG HMM cut-off calibration study](parameter-tuning/studies/kegg-hmm-cutoff-calibration.md); current value confirmed directly in `external/kegg/getKEGGModelForOrganism.m` |
| Same function, `minScoreRatioG`: `0.8` → `0.9` | High | Same study and same confirmation |
| `getModelFromHomology`'s `minLen`: `200` → `100` | Medium | [homology cut-off calibration study](parameter-tuning/studies/homology-cutoff-calibration.md); confirmed directly in `core/getModelFromHomology.m`. A fix already exists as an uncommitted local branch (`fix/homology-minlen`) but is stale relative to current `origin/develop` (file moved `reconstruction/homology/` → `core/`) and hasn't been pushed. |
| `removeGenes`'s `removeBlockedRxns` parameter (default `false`, i.e. keep blocked reactions): default to `true` instead, matching raven-toolbox's `'remove'` | Medium | `parameter-tuning/benchmarks.md`, measured false-positive growth on e_coli_core after essential-gene deletion. Confirmed directly in `core/removeGenes.m`: `removeBlockedRxns` defaults to `false`. |
| `FSEOF`: add an explicit noise floor; currently there is **no tolerance at all** (bare `>0`/`<0`/`>`/`<` float comparison), not merely a looser fixed one as an earlier version of this row said | Medium | `parameter-tuning/benchmarks.md` measured `1e-8` catching solver-noise false positives *in raven-toolbox*; confirmed directly in `core/FSEOF.m` that MATLAB has no threshold whatsoever, which was not previously checked and is likely a worse version of the same problem, though not independently measured on the MATLAB side |

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
