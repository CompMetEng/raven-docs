# Flux sampling convergence and settings

ACHR samples at genome scale were assessed in two ways, by autocorrelation within one chain and by R-hat between chains, and two further sampling settings were tested.

## Autocorrelation within one chain

`thinning=k` takes k random-walk steps between each stored sample; a larger k costs more compute and gives more independent samples. On yeast-GEM (`n_samples=300`, `warmup=1000`, Gurobi):

| `thinning` | Lag-1 autocorrelation | Wall time (s) |
|---|---|---|
| 20 | 0.973 | 660 |
| 100 (default) | 0.926 | 841 |
| 500 | 0.849 | 927 |

At 500, consecutive samples were 85 % correlated. The decay is too slow for the setting to fix: a fivefold increase from 20 to 100 removed 0.047 of the autocorrelation, and the next fivefold removed 0.077. Reaching roughly 0.3 (a commonly used approximate threshold for near-independence) would need thinning in the tens of thousands, which is weeks of compute for 1000 samples.

Under an AR(1) assumption for the chain, the effective sample size is `n × (1−ρ) / (1+ρ)`. At the default, ρ=0.926 gives about 12 independent samples from 300 stored. Collecting 100 would need roughly 2,600 stored samples, about 7.5 hours.

The behaviour is expected: ACHR's mixing time scales with the dimension of the polytope, and yeast-GEM's 4,102 reactions are 15–20 times the models cobrapy calibrated `thinning=100` against. The default equals the upstream value; at genome scale the number of samples needed changes, and the right setting does not.

## Convergence between chains

Autocorrelation measures independence within a chain. It gives no information on whether that chain reached every part of the flux polytope or mixed well inside one sub-region. Judging that needs several independent chains from different starting points and a check that they agree, the Gelman-Rubin R-hat diagnostic.

For each reaction, R-hat compares between-chain variance to within-chain variance across `n_chains` independent `random_sampling` runs (different seeds). R-hat ≈ 1.0 means the chains agree; R-hat > 1.1 (the common convergence threshold) or > 1.01 (the stricter one used in published MCMC work) flags a reaction whose distribution depends on where its chain started.

* Driver: [`scripts/analyze_sampling_convergence.py`](https://github.com/CompMetEng/raven-toolbox/blob/docs/parameter-defaults/scripts/analyze_sampling_convergence.py)
* Settings matched to the single-chain study for direct comparison: `n_samples=300`, `thinning=100`, `warmup=1000` (`thinning` and `warmup` at their defaults; the default `n_samples` is 1000).
* `n_chains=4`, run in parallel via `ProcessPoolExecutor` (one process per chain; cobra models are not guaranteed thread-safe for concurrent solves).

## e_coli_core (95 reactions) as methodology validation

4 chains × 300 samples, 34.7 s wall (parallel).

| | value |
|---|---:|
| reactions scored (non-constant) | 87 / 95 |
| R-hat median | 1.0071 |
| R-hat p90 | 1.0369 |
| R-hat max | 1.3028 |
| reactions with R-hat > 1.01 | 42 (48.3 %) |
| reactions with R-hat > 1.1 | 1 (1.1 %) |

Worst-converged reactions:

| reaction | R-hat |
|---|---:|
| `EX_succ_e` | 1.3028 |
| `EX_co2_e` | 1.0420 |
| `CO2t` | 1.0420 |
| `FUM` | 1.0390 |
| `EX_h_e` | 1.0383 |
| `TKT2`, `RPE`, `TKT1`, `TALA`, `G6PDH2r` | 1.0369 (tied) |

On a 95-reaction textbook model, one reaction (`EX_succ_e`, succinate exchange, a byproduct or overflow pathway) exceeded the "not converged" threshold (R-hat 1.30) at the default settings, and nearly half the reactions failed the stricter 1.01 threshold. This failure mode differs from the one the single-chain ESS result measured (autocorrelation within a chain): independent chains reached measurably different distributions for a subset of reactions. The result is consistent with a byproduct-secretion pathway that is rarely favoured and is explored only if the random walk of a chain reaches that corner of the polytope.

## yeast-GEM (4105 reactions, genome scale)

4 chains × 300 samples, 2524.4 s wall (~42 min). The wall time of four parallel chains is longer than the time of one chain (841 s) by a factor of ~3: the four Gurobi processes evidently contended for resources on a 12-core machine and did not scale linearly.

| | value |
|---|---:|
| reactions scored (non-constant) | 3364 / 4105 |
| R-hat median | 1.1671 |
| R-hat p90 | 1.6414 |
| R-hat max | 9.9416 |
| reactions with R-hat > 1.01 | 3246 (96.5 %) |
| reactions with R-hat > 1.1 | 2271 (67.5 %) |

Worst-converged reactions: `r_0318` (9.94), `r_0307` (9.65), `r_1690` (8.89), `r_1077` (8.59), `r_2625` (5.92), `r_1072` (4.21), `r_4015` (3.88), `r_2690` (3.43), `r_1113` (3.42), `r_1648` (3.42).

This is a materially worse picture than e_coli_core suggested, and worse than the single-chain ESS finding implied on its own. At genome scale, with `thinning=100`, `warmup=1000` and `n_samples=300`, the median reaction already exceeded the 1.1 "not converged" threshold: independent chains disagreed on where the flux distribution of a typical reaction lies. Two in three reactions failed even the loose threshold; only 3.5 % passed the strict one.

The result is consistent with the single-chain result (ESS≈12 effective samples from 300 stored at these settings). Low ESS shows that samples are highly autocorrelated within a chain; R-hat shows that, at genome scale, the chains often had not reached the same distribution within 300×100=30,000 total ACHR steps. The two are independent lines of evidence that point in the same direction.

Per-reaction flux ranges reported by `random_sampling` at default settings on a genome-scale model should not be trusted as converged for the majority of reactions. The `random_sampling` docstring states these numbers and recommends raising `thinning` (at least 1000) or `n_samples`, `method='chrr'`, or an ESS or R-hat check.

## `method='chrr'` on e_coli_core

Same 4 chains × 300 samples on e_coli_core, with `method='chrr'` and with `'achr'`:

| | ACHR | CHRR |
|---|---:|---:|
| wall time | 34.7 s | 702.0 s |
| reactions scored | 87 | 95 (0 excluded as constant) |
| R-hat median | 1.0071 | 1.0049 |
| R-hat p90 | 1.0369 | 1.0146 |
| R-hat max | 1.3028 | 1.0248 |
| R-hat > 1.01 | 48.3 % | 17.9 % |
| R-hat > 1.1 | 1.1 % | 0.0 % |

CHRR converged on e_coli_core: the worst reaction (`ICDHyr`, 1.0248) did not reach the 1.1 threshold, against ACHR's `EX_succ_e` at 1.30. R-hat max fell from 1.30 to 1.02, and the share above 1.01 from 48.3 % to 17.9 %.

CHRR was ~20x slower on a 95-reaction model. CHRR's up-front max-volume-ellipsoid (MVE) rounding step is the likely driver, and MVE computation typically scales worse than linearly with dimension, so the cost at yeast-GEM's 4102 reactions (43x more reactions than e_coli_core) could plausibly be anywhere from more than 20x to much more, and not less. At ACHR's measured 2524 s for 4 genome-scale chains, a proportional 20x would be ~14 hours, which was not attempted blind. The bounded probe below gives the genome-scale measurement.

## Reallocating the ACHR step budget

The total step budget equals the default configuration (`thinning × n_samples` = 30,000 either way) and is distributed differently: `thinning=300, n_samples=100` instead of `thinning=100, n_samples=300`. 4 chains, yeast-GEM.

| | default (t=100, n=300) | reallocated (t=300, n=100) |
|---|---:|---:|
| wall time | 2524.4 s | 3451.0 s |
| R-hat median | 1.1671 | 1.1636 |
| R-hat p90 | 1.6414 | 1.6542 |
| R-hat max | 9.9416 | 9.8345 |
| R-hat > 1.01 | 96.5 % | 95.2 % |
| R-hat > 1.1 | 67.5 % | 67.2 % |
| worst reaction | `r_0318` (9.94) | `r_0318` (9.83) |

R-hat changed little: the worst reactions were the same, the rough ordering was the same, the overall failure rate was the same, and the run took longer (57.5 min against 42 min) despite equal total steps. This rules out more thinning within a fixed budget as a fix. If more thinning improved mixing, spending the same budget on longer gaps between fewer stored samples should have moved R-hat, and it did not move it meaningfully in either direction. The non-convergence looks structural to ACHR's mixing on this polytope and not a matter of an existing setting, consistent with CHRR (a different algorithm) fixing it on e_coli_core while this reallocation, which remains ACHR, does not.

## CHRR at genome scale

CHRR was not run at matching scale (4 chains × 300 samples), because the ~20x e_coli_core cost multiplier implies perhaps 14 hours. A small bounded probe (2 chains, 20 samples, same `thinning=100`) was run to obtain a genome-scale CHRR timing number before deciding whether to attempt a full run.

cobrapy's `OptGPSampler` was not a candidate here: `random_sampling` does not wire it in; its methods are `'achr'`, `'chrr'` and `'random_objective'`.

The probe took 4815.3 s (~80 min) for 2 chains × 20 samples. This gives the timing independent of sample-count effects: CHRR's cost at genome scale is dominated by a fixed per-chain cost (almost certainly the max-volume-ellipsoid rounding step, computed once before any samples are drawn) that does not shrink with a smaller sample request. The 20-sample probe cost wall time comparable to a full 300-sample ACHR run (2524 s). With the current implementation CHRR is not a cheap drop-in genome-scale fix, whatever its converged quality would be at a matching sample count.

The R-hat computed from this probe (median 5.16, p90 86, max in the billions) is not evidence that CHRR converges worse than ACHR at genome scale. With only 20 samples per chain, the within-chain variance (R-hat's denominator) is estimated from too little data to be stable. A reaction that happens to show near-zero variance in 20 draws by chance, combined with any between-chain difference, produces a large ratio (the maximum was in the billions) that reflects the small denominator and not the flux distribution. At e_coli_core, 300 samples per chain gave stable R-hat throughout. This run cannot distinguish "CHRR does not work at genome scale" from "R-hat needs more than 20 samples to mean anything"; telling those apart would need a genome-scale CHRR run with enough samples for a stable R-hat, which has the same cost problem.

## Summary

- Default settings are unconverged for most reactions at genome scale, confirmed by two independent lines of evidence (ESS and R-hat).
- Reallocating the same ACHR budget did not help, which rules out the cheapest possible fix.
- CHRR fixed the problem on a small model, but its genome-scale cost (a fixed ~80 min+ per chain before any samples are even drawn) makes it impractical as a drop-in fix with the current implementation. Whether CHRR would converge at genome scale given enough samples to trust the R-hat is open; it would need a run long enough to be informative, which has the same cost problem.
- No cheap, validated fix was identified. Users doing genome-scale flux sampling with `random_sampling`'s defaults should treat per-reaction flux ranges as unconverged for most reactions. The finding concerns the median reaction and not a minority of reactions. One unblock was identified but not pursued here: CHRR's rounding transform is recomputed from scratch per chain and call, and caching or reusing it across calls on the same model would remove the dominant fixed cost. This is an engineering change, and no parameter default achieves it.

## Other sampling settings

Both settings differ from MATLAB, and in both cases the difference is deliberate.

`replace_max_bound` swaps big-M upper bounds for infinity before sampling, and applies only to `method='random_objective'`. RAVEN-convention models use 1000 as the big-M for almost every reaction (4,083 of yeast-GEM's 4,102), so replacing them all makes the random-objective LP unbounded: the objective can be driven to infinity through any unconstrained reaction. At `False`, 200 samples complete, with 0.57 % of them at the bound. MATLAB's `True` suits models where only a few reactions reach the big-M and those represent real capacity limits, which is rare.

`loopless_good_reactions` selects which reactions are eligible as random objectives. MATLAB excludes any reaction whose FVA maximum reaches 999, treating proximity to the big-M as evidence of a thermodynamic loop. That also excludes reactions that reach capacity for metabolic reasons. Loopless FVA identifies only reactions that participate in infeasible cycles, at higher cost.

## Reproducing

```bash
python scripts/analyze_sampling_convergence.py \
    --model /path/to/yeast-GEM.xml --out work/ \
    --n-chains 4 --n-samples 300 --thinning 100 --warmup 1000
```

Results are cached per (model, n_chains, n_samples, thinning, warmup) config, so re-running with the same settings returns the cached result without sampling; changing `--thinning` or `--n-samples` re-runs and caches separately, so the R-hat against thinning trade-off can be explored without re-deriving cached chains.

Four parallel chains took 2524 s, about 3x the 841 s of the single-chain run at the same settings. The four concurrent Gurobi processes on a 12-core machine evidently contended for resources and did not scale linearly; planning further sweeps at this scale should allow for that.
