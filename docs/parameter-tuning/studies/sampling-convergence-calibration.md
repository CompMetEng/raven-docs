# Flux sampling convergence and settings

`random_sampling` in raven-toolbox draws flux vectors from a model with a Markov-chain sampler (`method='achr'` or `'chrr'`) or with random objectives (`method='random_objective'`). This study ran the two Markov-chain samplers on e_coli_core (95 reactions) and yeast-GEM, and recorded how strongly consecutive samples of one chain are correlated, whether independent chains reach the same flux distribution, and the wall time. It also records why two settings of the random-objective method differ from RAVEN MATLAB.

## Terms

- The **flux polytope** is the set of flux vectors `v` with `S v = 0` and `lb <= v <= ub`, where `S` is the stoichiometric matrix and `lb` and `ub` are the reaction bounds. A **vertex** is a corner point of the polytope.
- A **Markov chain Monte Carlo (MCMC)** sampler is a random walk inside the polytope whose visited points, after enough steps, are distributed close to uniformly over it. One walk from one starting point and one random seed is a **chain**.
- A **hit-and-run** step chooses a direction, finds the line segment through the current point along that direction that lies inside the polytope, and moves to a uniformly random point on that segment.
- **ACHR** (Artificially Centered Hit-and-Run) takes its directions from warmup points and a running centre of the chain, and does not transform the polytope. raven-toolbox wraps `cobra.sampling.ACHRSampler`, which computes its warmup points with two linear programs (LPs) per reaction before the first step ([Random sampling](../../guide/sampling.md)).
- **CHRR** (Coordinate Hit-and-Run with Rounding) first runs a flux variability analysis (FVA), fixes the reactions whose range is narrower than `fixed_width_tol`, reduces the polytope to a full-dimensional body through the nullspace of the equality constraints, and **rounds** it: it maps the body so that its maximum-volume inscribed ellipsoid (**MVE**) becomes a unit ball. The walk then moves along one coordinate per step.
- **`thinning`** is the number of steps between two stored samples. An ACHR chain with `n_samples` stored samples therefore takes `thinning × n_samples` steps after its warmup points, and a CHRR chain takes `warmup + thinning × n_samples` steps after the rounding.
- **`warmup`** is the number of CHRR steps discarded before the first stored sample. `random_sampling` passes it to CHRR only; the ACHR runs ignore it.
- The **lag-1 autocorrelation** `ρ` is the correlation between consecutive stored samples of one chain.
- The **effective sample size (ESS)** is the number of independent samples that carry the same information as the correlated ones. Under the assumption that the chain is a first-order autoregressive process, `ESS = n × (1−ρ) / (1+ρ)` for `n` stored samples.
- The **R-hat** of a reaction (Gelman-Rubin statistic) compares the flux variance between chains with the variance within chains. With `m` chains of `n` samples, `W` the mean within-chain variance and `B/n` the variance of the chain means, `R-hat = sqrt(((n−1)/n × W + B/n) / W)`. R-hat is 1.0 when the chains agree and grows when the distribution of a chain depends on where it started. The script reports the share of reactions above 1.1 and above 1.01, the stricter of the two thresholds.

## Set-up

Driver for the comparisons between chains: [`scripts/analyze_sampling_convergence.py`](https://github.com/CompMetEng/raven-toolbox/blob/docs/parameter-defaults/scripts/analyze_sampling_convergence.py). It starts `n_chains` calls of `random_sampling` with seeds 0 to `n_chains − 1`, one process per chain through `ProcessPoolExecutor`, because cobra models are not guaranteed to be safe for concurrent solves in threads. Each process reads the model from the SBML file. The script computes R-hat per reaction with the formula in [Terms](#terms). A reaction with the same constant flux in every chain has `W = 0` and no variance between the chain means, gets no R-hat, and is excluded as **not scored**. A reaction that is constant within each chain at different values in different chains has `W = 0` and an infinite R-hat, and is scored.

Settings: `n_samples=300`, `thinning=100`, `warmup=1000` and 4 chains, unless a table states otherwise. `thinning` and `warmup` are at their defaults; the default `n_samples` is 1000. The solver was Gurobi, on a machine with 12 cores. Software versions were not recorded. Each configuration ran once. cobrapy's `OptGPSampler` was not tested, because `random_sampling` does not call it; its methods are `'achr'`, `'chrr'` and `'random_objective'`.

The models are two files of yeast-GEM. The single-chain runs were made on a yeast-GEM with 4,102 reactions, the same reaction count as the bundled `docs/data/yeast-GEM.xml` (yeastGEM_v9.1.0); which file they read was not recorded. The comparisons between chains read a yeast-GEM file with 4105 reactions, the count that the script reports; its version was not recorded.

The wall time of a comparison between chains is the time from starting the processes to the return of the last chain: reading the model, the warmup and the sampling, without the R-hat computation. What the single-chain wall times include, and how `ρ` was combined over the reactions, was not recorded.

## Results

### Autocorrelation within one chain

One ACHR chain on yeast-GEM (4,102 reactions), `n_samples=300`, at three values of `thinning`. The ESS column is computed from the formula in [Terms](#terms).

| `thinning` | Lag-1 autocorrelation | ESS of 300 stored samples | Wall time (s) |
|---|---|---|---|
| 20 | 0.973 | ~4 | 660 |
| 100 (default) | 0.926 | ~12 | 841 |
| 500 | 0.849 | ~25 | 927 |

At `thinning=500`, consecutive samples were 85 % correlated. The fivefold step from 20 to 100 lowered `ρ` by 0.047, and the next fivefold step lowered it by 0.077. Reaching a `ρ` of about 0.3, an approximate level for near-independent samples, needs a `thinning` above the measured range, and three points do not establish how `ρ` decays beyond 500.

`n_samples` was not varied. With `ρ` fixed at its value for the default `thinning=100`, the ESS formula is proportional to `n_samples`: ~12 from 300 stored samples, ~38 from the default 1000, and 100 needs ~2,600 stored samples. Scaled in proportion from 841 s for 300 samples, 2,600 samples take ~7,300 s (~2 h). The wall time rose from 660 s to 927 s (1.4-fold) while the number of steps rose 25-fold, so most of the time of these runs did not depend on `thinning`. If the wall time is a fixed cost per run plus a cost per stored sample, the scaled estimate is an upper bound for one chain; the thinning sweep kept `n_samples` at 300 and cannot separate the two parts.

For the choice of settings: within the measured range, a larger `thinning` gave more ESS per second of wall time (~4 in 660 s at 20, ~25 in 927 s at 500). That a larger `n_samples` at a fixed `thinning` raises ESS in proportion and leaves `ρ` unchanged follows from the first-order autoregressive formula; it was not measured.

### Agreement between chains on e_coli_core

ACHR, 4 chains × 300 samples, 34.7 s wall time.

| Measure | Value |
|---|---:|
| reactions scored (non-constant) | 87 / 95 |
| R-hat median | 1.0071 |
| R-hat p90 | 1.0369 |
| R-hat max | 1.3028 |
| reactions with R-hat > 1.01 | 42 (48.3 %) |
| reactions with R-hat > 1.1 | 1 (1.1 %) |

Reactions with the highest R-hat:

| Reaction | R-hat |
|---|---:|
| `EX_succ_e` | 1.3028 |
| `EX_co2_e` | 1.0420 |
| `CO2t` | 1.0420 |
| `FUM` | 1.0390 |
| `EX_h_e` | 1.0383 |
| `TKT2`, `RPE`, `TKT1`, `TALA`, `G6PDH2r` | 1.0369 (tied) |

One reaction, the succinate exchange `EX_succ_e` (R-hat 1.30), exceeded 1.1, and 42 of 87 scored reactions exceeded 1.01. The chains reached different distributions for that reaction, a failure that the autocorrelation of one chain cannot detect.

For the choice of settings: on a 95-reaction model, the default `thinning` with 300 samples per chain gave agreement at the 1.1 threshold for 86 of 87 scored reactions. Agreement at 1.01 needs more steps or a different method (see [CHRR on e_coli_core](#chrr-on-e_coli_core)).

### Agreement between chains on yeast-GEM

ACHR, 4 chains × 300 samples, 2524.4 s wall time (~42 min).

| Measure | Value |
|---|---:|
| reactions scored (non-constant) | 3364 / 4105 |
| R-hat median | 1.1671 |
| R-hat p90 | 1.6414 |
| R-hat max | 9.9416 |
| reactions with R-hat > 1.01 | 3246 (96.5 %) |
| reactions with R-hat > 1.1 | 2271 (67.5 %) |

Reactions with the highest R-hat: `r_0318` (9.94), `r_0307` (9.65), `r_1690` (8.89), `r_1077` (8.59), `r_2625` (5.92), `r_1072` (4.21), `r_4015` (3.88), `r_2690` (3.43), `r_1113` (3.42), `r_1648` (3.42).

The median scored reaction exceeded 1.1: two in three reactions failed that threshold, and 3.5 % passed 1.01. Each chain took 300 × 100 = 30,000 ACHR steps after its warmup points. The low ESS of one chain and the disagreement between chains are two separate measurements, and both show that these settings do not give a converged sample of yeast-GEM.

The four parallel chains took 2524 s, ~3 times the 841 s of the single chain at the same settings. The two runs read different yeast-GEM files (4105 and 4,102 reactions). Contention between the four Gurobi processes on the 12 cores is a possible cause of the difference; it was not measured.

For the choice of settings: at the default `thinning` and `n_samples=300`, the flux distributions of most reactions in a genome-scale model depend on the seed. The default `n_samples=1000` (100,000 steps per chain) was not tested.

### Reallocating the ACHR step budget

The 30,000 steps per chain of the default run (`thinning=100, n_samples=300`), spread as `thinning=300, n_samples=100`. ACHR, 4 chains, yeast-GEM.

| Measure | t=100, n=300 (default thinning) | t=300, n=100 (reallocated) |
|---|---:|---:|
| wall time | 2524.4 s | 3451.0 s |
| R-hat median | 1.1671 | 1.1636 |
| R-hat p90 | 1.6414 | 1.6542 |
| R-hat max | 9.9416 | 9.8345 |
| R-hat > 1.01 | 96.5 % | 95.2 % |
| R-hat > 1.1 | 67.5 % | 67.2 % |
| worst reaction | `r_0318` (9.94) | `r_0318` (9.83) |

The reallocation moved the median R-hat from 1.1671 to 1.1636 and the shares above the two thresholds by at most 1.3 percentage points, the reaction with the highest R-hat was the same, and the run took 57.5 min against 42 min. That the disagreement comes from how ACHR moves through this polytope, and not from the split of the steps, is an inference from this result and from the CHRR result on e_coli_core; it was not tested at genome scale.

For the choice of settings: at a fixed number of steps, moving steps from `n_samples` to `thinning` did not improve agreement between chains. A larger total number of steps was not tested with R-hat.

### CHRR on e_coli_core

4 chains × 300 samples on e_coli_core, with `method='achr'` and `method='chrr'`.

| Measure | ACHR | CHRR |
|---|---:|---:|
| wall time | 34.7 s | 702.0 s |
| reactions scored | 87 | 95 (0 excluded as constant) |
| R-hat median | 1.0071 | 1.0049 |
| R-hat p90 | 1.0369 | 1.0146 |
| R-hat max | 1.3028 | 1.0248 |
| R-hat > 1.01 | 48.3 % | 17.9 % |
| R-hat > 1.1 | 1.1 % | 0.0 % |

With CHRR, no reaction exceeded 1.1; the highest R-hat was `ICDHyr` at 1.0248, against `EX_succ_e` at 1.30 with ACHR. The share above 1.01 fell from 48.3 % to 17.9 %. CHRR took ~20 times the wall time of ACHR. The percentages have different denominators, 87 and 95 scored reactions. The 8 reactions that ACHR left constant were scored with CHRR. CHRR computes every flux of a sample from the nullspace basis (`v0 + N x`); that rounding error in this product makes those 8 reactions vary is an inference that was not checked.

For the choice of settings: on a 95-reaction model, CHRR with the default `thinning` and 300 samples per chain gave agreement at 1.1 for every reaction.

### CHRR at genome scale

CHRR was not run on yeast-GEM with 4 chains × 300 samples, because 20 times the 2524 s of the ACHR run gives ~14 h. A probe with 2 chains × 20 samples (`thinning=100`) took 4815.3 s (~80 min), 1.9 times the 2524 s of the full ACHR run. yeast-GEM has 43 times the reactions of e_coli_core.

Each CHRR chain ran an FVA, a nullspace computation and the MVE rounding before its first step, and then 1,000 warmup steps and 2,000 sampling steps. The probe does not separate these parts. That the cost before the first step dominates, and that most of it is the MVE rounding, is an inference from the small number of steps; the parts were not timed. `random_sampling` computes this transform anew in every call, so each chain pays it.

The R-hat of the probe (median 5.16, p90 86, max in the billions) does not show that CHRR converges worse than ACHR at genome scale. With 20 samples per chain, the within-chain variance `W` is estimated from too few samples to be stable: a reaction that shows almost no variance in 20 draws by chance, combined with any difference between the chain means (`B/n`), gives a large R-hat whatever its distribution. The probe cannot distinguish a CHRR that does not converge on yeast-GEM from an R-hat that needs more samples; a run with enough samples for a stable R-hat has the cost problem of the full run.

For the choice of settings: 20 samples per chain are too few for R-hat on yeast-GEM. Whether CHRR converges on yeast-GEM with 300 samples per chain is open.

## Choice of `thinning` and `n_samples`

The defaults stay `method='achr'`, `thinning=100` and `n_samples=1000` ([Tuned parameter defaults](../../tuned-parameters.md)). On a model the size of e_coli_core, the default `thinning` with 300 samples per chain gave chains that agree at R-hat 1.1 for all but one reaction. On yeast-GEM, no setting tested gave converged samples: a `thinning` up to 500 left `ρ` at 0.849, and moving the same 30,000 steps from `n_samples` to `thinning` moved the median R-hat from 1.1671 to 1.1636 and the shares above 1.01 and 1.1 by at most 1.3 percentage points. Flux ranges from `random_sampling` with the default settings on a genome-scale model are unconverged for most reactions.

The `random_sampling` docstring gives these numbers and recommends, for genome-scale models, a `thinning` of at least 1000 or a larger `n_samples`, `method='chrr'`, or an ESS or R-hat check. A `thinning` of 1000 or more was not measured. The driver script runs the R-hat check: it samples several chains with different seeds at given settings and reports the share of reactions above the R-hat thresholds, so a sampling result can be checked at the settings that produced it.

One change outside the parameters was identified and not pursued: CHRR recomputes its rounding transform in every call. The chains run in separate processes at the same time, so to save that cost the transform would have to be computed once per model and passed to every chain. The saving depends on the share of the rounding in the 80 min of the probe, which was not measured.

## Other sampling settings

Two settings of `method='random_objective'` differ from RAVEN MATLAB's `randomSampling` on purpose.

`replace_max_bound` (default `False`; MATLAB's `replaceBoundsWithInf` defaults to true) replaces the largest upper bound, the **big-M** value that stands for an unconstrained reaction, with infinity before sampling, and replaces the most negative lower bound, if it is below 0, with minus infinity. RAVEN-convention models use 1000 as the big-M for almost every reaction (4,083 of the 4,102 reactions of yeast-GEM). With every such bound replaced, the random-objective LP becomes unbounded, because the objective can grow without limit through any reaction that is then unconstrained. With `False`, 200 samples completed, with 0.57 % of them at the bound.

`loopless_good_reactions` (default `True`) selects which reactions are eligible as random objectives. MATLAB excludes every reaction whose FVA maximum is infinite or above 0.999 times the largest upper bound (999 on a model capped at 1000), and, when the smallest lower bound is negative, every reaction whose FVA minimum is minus infinity or below 0.999 times that bound; it treats proximity to the big-M as a sign of a thermodynamic loop. It also excludes reactions that cannot carry a non-zero flux and, in an ecModel, the `usage_prot_` reactions. That rule also excludes reactions that reach the bound for metabolic reasons. A loopless FVA excludes only the reactions that take part in infeasible cycles, at a higher cost.

## Limits

- Each configuration ran once. The spread of R-hat and `ρ` between repeated runs with other seeds was not measured, so differences of the size seen in the reallocation (0.0035 in the median) are within an unknown run-to-run spread.
- One small and one genome-scale model were tested. The single-chain runs and the comparisons between chains used two different yeast-GEM files, and software versions were not recorded.
- R-hat is computed in its original form, without split chains or rank normalisation.
- The default `n_samples=1000`, a `thinning` above 500, and CHRR on yeast-GEM with more than 20 samples per chain were not tested.

## Reproduction

```bash
python scripts/analyze_sampling_convergence.py \
    --model /path/to/yeast-GEM.xml --out work/ \
    --n-chains 4 --n-samples 300 --thinning 100 --warmup 1000
```

The CHRR runs use the same command with `--method chrr`. The script caches the chains per model, method, `n_chains`, `n_samples`, `thinning` and `warmup` under `--out`; a run with a cached configuration computes R-hat from the stored chains without sampling. Another `--thinning` or `--n-samples` samples again and is cached separately. On yeast-GEM, four ACHR chains in parallel on 12 cores took ~3 times the wall time of one chain at the same settings; the two runs read different yeast-GEM files and the cause of the difference was not measured (see [Agreement between chains on yeast-GEM](#agreement-between-chains-on-yeast-gem)). A sweep at genome scale can therefore take more time than one chain per configuration suggests.
