# Flux sampling convergence and settings

The function `random_sampling` of raven-toolbox draws flux vectors from a model with a Markov-chain sampler (`method='achr'` or `'chrr'`) or with random objectives (`method='random_objective'`). The study ran the two Markov-chain samplers on e_coli_core (95 reactions) and yeast-GEM and recorded three results: how strongly consecutive samples of one chain are correlated, whether independent chains reach the same flux distribution, and the wall time. It also records why two settings of the random-objective method differ from RAVEN in MATLAB.

On e_coli_core, four chains of 300 samples agree at the R-hat threshold of 1.1 for 87 of 87 scored reactions, and the CHRR sampler was no better than ACHR there in single runs. On yeast-GEM, 50.7 % of the scored reactions exceed an R-hat of 1.1 for `n_samples=300` at the default `thinning=100`; the default `n_samples` of 1000 was not tested. No setting measured with R-hat or `ρ` gave converged samples.

## Terms

- The flux polytope is the set of flux vectors `v` with `S v = 0` and `lb <= v <= ub`, where `S` is the stoichiometric matrix and `lb` and `ub` are the reaction bounds. A vertex is a corner point of the polytope.
- A Markov chain Monte Carlo (MCMC) sampler is a random walk inside the polytope whose visited points, after enough steps, are distributed close to uniformly over it. One walk from one starting point and one random seed is a chain.
- A hit-and-run step chooses a direction, finds the line segment through the current point along that direction that lies inside the polytope, and moves to a uniformly random point on that segment.
- ACHR (Artificially Centered Hit-and-Run) takes its directions from warmup points and a running centre of the chain, and does not transform the polytope. raven-toolbox wraps `cobra.sampling.ACHRSampler`, which computes its warmup points with two linear programs (LPs) per reaction before the first step ([Random sampling](../../guide/sampling.md)).
- CHRR (Coordinate Hit-and-Run with Rounding) first runs a flux variability analysis (FVA), fixes the reactions whose range is narrower than `fixed_width_tol`, reduces the polytope to a full-dimensional body through the nullspace of the equality constraints, and rounds it: it maps the body so that its maximum-volume inscribed ellipsoid (MVE) becomes a unit ball. The walk then moves along one coordinate per step.
- `thinning` is the number of steps between two stored samples. An ACHR chain with `n_samples` stored samples therefore takes `thinning × n_samples` steps after its warmup points, and a CHRR chain takes `warmup + thinning × n_samples` steps after the rounding.
- `warmup` is the number of CHRR steps discarded before the first stored sample. `random_sampling` passes it to CHRR only, and the ACHR runs ignore it.
- The lag-1 autocorrelation `ρ` is the correlation between consecutive stored samples of one chain.
- The effective sample size (ESS) is the number of independent samples that carry the same information as the correlated ones. Under the assumption that the chain is a first-order autoregressive process, `ESS = n × (1−ρ) / (1+ρ)` for `n` stored samples.
- The R-hat of a reaction (Gelman-Rubin statistic) compares the flux variance between chains with the variance within chains. With `m` chains of `n` samples, `W` the mean within-chain variance and `B/n` the variance of the chain means, `R-hat = sqrt(((n−1)/n × W + B/n) / W)`. R-hat is 1.0 when the chains agree and grows when the distribution of a chain depends on where it started. The script reports the share of reactions above 1.1 and above 1.01, the stricter of the two thresholds.

## Set-up

The driver for the comparisons between chains is `scripts/analyze_sampling_convergence.py` in raven-toolbox. It starts `n_chains` calls of `random_sampling` with seeds 0 to `n_chains − 1`, one process per chain through `ProcessPoolExecutor`, because cobra models are not guaranteed to be safe for concurrent solves in threads. Each process reads the model from the SBML file. The script computes R-hat per reaction with the formula in [Terms](#terms). A reaction with the same constant flux in every chain has `W = 0` and no variance between the chain means, gets no R-hat, and is excluded as not scored. A reaction that is constant within each chain at different values in different chains has `W = 0` and an infinite R-hat, and is scored.

The settings were `n_samples=300`, `thinning=100`, `warmup=1000` and 4 chains, unless a table states otherwise. The values of `thinning` and `warmup` are the defaults, and the default `n_samples` is 1000. The solver was Gurobi, with 12 cores per job on AMD EPYC 9354 nodes. All figures are from runs on 2026-11-01 with Python 3.14.2, cobra 0.32.1, optlang 1.9.1, gurobipy 13.0.3 (Gurobi library 13.0.3) and raven-toolbox `94f3940`. Each configuration ran once, except e_coli_core ACHR, which was repeated. The single-chain runs also ran with seeds 1 to 3 (see [Autocorrelation within one chain](#autocorrelation-within-one-chain)). The `OptGPSampler` of cobrapy was not tested, because `random_sampling` does not call it, and its methods are `'achr'`, `'chrr'` and `'random_objective'`.

The models are two files of yeast-GEM and one of e_coli_core. The single-chain runs read the bundled `docs/data/yeast-GEM.xml` (yeastGEM_v9.1.0, 4,102 reactions). The comparisons between chains read yeast-GEM v9.1.1 (4,105 reactions), which differs from the develop branch at commit `ea756c2` only in the model identifier and two dates. The model e_coli_core is `textbook.xml.gz` of cobrapy 0.32.1 (model identifier `e_coli_core`).

The wall time of a comparison between chains is the time from starting the processes to the return of the last chain: reading the model, the warmup and the sampling, without the R-hat computation. The wall time of a single-chain run is the time of reading the SBML file plus `random_sampling`. The `ρ` of a chain is the mean over the reactions with a flux range above `1e-6` in that chain of the lag-1 Pearson correlation of the reaction (`pandas.Series.autocorr(1)`). The median over the reactions is higher and is given in the text. The ESS uses the mean.

## Results

### Autocorrelation within one chain

The runs used one ACHR chain on yeast-GEM (4,102 reactions), `n_samples=300`, seed 0, at three values of `thinning`. The ESS column is computed from the formula in [Terms](#terms).

| `thinning` | Lag-1 autocorrelation | ESS of 300 stored samples | Wall time (s) |
|---|---|---|---|
| 20 | 0.9725 | 4.2 | 189.5 |
| 100 (default) | 0.9361 | 9.9 | 203.6 |
| 500 | 0.8251 | 28.8 | 223.3 |

The reactions with a flux range above `1e-6` numbered 2506, 2535 and 2575 of 4102. The median `ρ` over these reactions is 0.9829, 0.9519 and 0.8586. At `thinning=500`, consecutive samples were 83 % correlated. The fivefold step from 20 to 100 lowered `ρ` by 0.036, and the next fivefold step lowered it by 0.111. Three points do not establish how `ρ` decays beyond 500.

The same settings with seeds 0 to 3 give the following `ρ`.

| `thinning` | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Range |
|---|---|---|---|---|---|
| 20 | 0.9725 | 0.9244 | 0.9790 | 0.9753 | 0.924 to 0.979 |
| 100 | 0.9361 | 0.6523 | 0.9238 | 0.9286 | 0.652 to 0.936 |
| 500 | 0.8251 | 0.6444 | 0.8013 | 0.7694 | 0.644 to 0.825 |

For every seed, `ρ` falls as `thinning` rises. Between seeds, `ρ` differs by up to 0.28, and the ESS of 300 stored samples ranges from 3.2 to 11.8 at `thinning=20`, from 9.9 to 63.1 at 100 and from 28.8 to 64.9 at 500. Seed 1 gives the lowest `ρ` at all three values, and without it the ranges are 0.972 to 0.979, 0.924 to 0.936 and 0.769 to 0.825. The four chains of the yeast-GEM comparison with 4,105 reactions (seeds 0 to 3, `thinning=100`) give a mean `ρ` of 0.951, 0.847, 0.947 and 0.911, so a low value for seed 1 appears on both model files. The spread between seeds is 0.10 on the 4,105-reaction chains (0.847 to 0.951) and 0.28 on the 4,102-reaction chains (0.652 to 0.936), and seed 1 is the lowest in both.

The value `n_samples` was not varied. With `ρ` fixed at its seed-0 value for the default `thinning=100`, the ESS formula is proportional to `n_samples`: about 10 from 300 stored samples, about 33 from the default 1000, and 100 needs about 3,000 stored samples. Building the ACHR warmup points alone took 185.9 s, 196.6 s and 195.4 s in the three runs, so the sampling steps took about 1 s, 5 s and 26 s for 6,000, 30,000 and 150,000 steps.

The warmup is therefore about 95 % of the wall time at `thinning=100`, and the wall time rose from 189.5 s to 223.3 s (1.2-fold) while the number of steps rose 25-fold.

With a fixed cost per run plus a cost per stored sample, 3,025 stored samples take about 242 s for one chain. Scaling the 203.6 s in proportion to 3,025 samples gives 2,053 s (about 34 min), an upper bound.

The warmup time was measured on a second, fresh sampler after the run, so the split is approximate.

Within the measured range, a larger `thinning` gave more ESS per second of wall time (4.2 in 189.5 s at 20, 28.8 in 223.3 s at 500). That a larger `n_samples` at a fixed `thinning` raises the ESS in proportion and leaves `ρ` unchanged follows from the first-order autoregressive formula, and it was not measured.

### Agreement between chains on e_coli_core

The ACHR run used 4 chains × 300 samples and took 10.9 s wall time (5.4 s in a repeat). The repeat gave the same R-hat for every reaction, so on e_coli_core a chain is deterministic for a given seed and software. Reproducibility on yeast-GEM was not tested, and the `random_objective` run on yeast-GEM is not reproducible (see [Other sampling settings](#other-sampling-settings)). The difference between 10.9 s and 5.4 s is unexplained.

| Measure | Value |
|---|---:|
| reactions scored (non-constant) | 87 / 95 |
| R-hat median | 1.0027 |
| R-hat p90 | 1.0171 |
| R-hat max | 1.0276 |
| reactions with R-hat > 1.01 | 12 (13.8 %) |
| reactions with R-hat > 1.1 | 0 (0.0 %) |

The reactions with the highest R-hat were:

| Reaction | R-hat |
|---|---:|
| `EX_succ_e` | 1.0276 |
| `FRD7` | 1.0266 |
| `SUCDi` | 1.0265 |
| `MALS`, `ICL` | 1.0208 |
| `SUCOAS`, `AKGDH` | 1.0203 |
| `ICDHyr` | 1.0193 |
| `ME1` | 1.0191 |
| `MDH` | 1.0157 |

No reaction exceeded 1.1, and 12 of 87 scored reactions exceeded 1.01. The reaction with the highest R-hat is the succinate exchange `EX_succ_e`.

On a 95-reaction model, the default `thinning` with 300 samples per chain gave agreement at the 1.1 threshold for 87 of 87 scored reactions and at 1.01 for 75 of 87. Agreement at 1.01 for the remaining 12 needs more steps or another method, and CHRR did not remove it (see [CHRR on e_coli_core](#chrr-on-e_coli_core)).

### Agreement between chains on yeast-GEM

The ACHR run used 4 chains × 300 samples and took 572.3 s wall time (about 9.5 min).

| Measure | Value |
|---|---:|
| reactions scored (non-constant) | 3325 / 4105 |
| R-hat median | 1.1020 |
| R-hat p90 | 1.3793 |
| R-hat max | 18.8976 |
| reactions with R-hat > 1.01 | 3167 (95.2 %) |
| reactions with R-hat > 1.1 | 1685 (50.7 %) |

The reactions with the highest R-hat were `r_4562` (18.90), `r_4358` (18.90), `r_0992` (5.18), `r_4249` (5.18), `r_4701` (5.18), `r_4621` (5.18), `r_1965` (5.09), `r_0917` (3.90), `r_0891` (3.90) and `r_0918` (3.90).

The median scored reaction was 1.1020, and one in two reactions (50.7 %) exceeded 1.1, and 4.8 % were at or below 1.01. Each chain took 300 × 100 = 30,000 ACHR steps after its warmup points. The low ESS of one chain and the disagreement between chains are two separate measurements, and both show that these settings do not give a converged sample of yeast-GEM.

The four parallel chains took 572.3 s, 2.8 times the 203.6 s of the single chain at the same settings. The two runs read different yeast-GEM files (4,105 and 4,102 reactions). Contention between the four Gurobi processes on the 12 cores is a possible cause of the difference, and it was not measured.

On yeast-GEM with `n_samples=300` and `thinning=100`, 50.7 % of the 3325 scored reactions had R-hat above 1.1. The default `n_samples=1000` (100,000 steps per chain) was not tested.

### Reallocating the ACHR step budget

The 30,000 steps per chain of the default run (`thinning=100, n_samples=300`) were spread as `thinning=300, n_samples=100`. The runs used ACHR, 4 chains and yeast-GEM.

| Measure | t=100, n=300 (default thinning) | t=300, n=100 (reallocated) |
|---|---:|---:|
| wall time | 572.3 s | 612.4 s |
| R-hat median | 1.1020 | 1.1010 |
| R-hat p90 | 1.3793 | 1.3778 |
| R-hat max | 18.8976 | 21.9072 |
| R-hat > 1.01 | 95.2 % | 93.5 % |
| R-hat > 1.1 | 50.7 % | 50.5 % |
| worst reaction | `r_4562`, `r_4358` (18.90) | `r_4562`, `r_4358` (21.91) |

Both runs scored 3325 reactions. The reallocation moved the median R-hat from 1.1020 to 1.1010 and the shares above the two thresholds by at most 1.7 percentage points. The reactions with the highest R-hat were the same, and the run took 612.4 s against 572.3 s (1.07 times). That the disagreement comes from how ACHR moves through this polytope, and not from the split of the steps, is an inference from this result, and it was not tested on other models. At a fixed number of steps, moving steps from `n_samples` to `thinning` did not improve the agreement between chains, and a larger total number of steps was not tested with R-hat.

### CHRR on e_coli_core

The runs used 4 chains × 300 samples on e_coli_core, with `method='achr'` and `method='chrr'`.

| Measure | ACHR | CHRR |
|---|---:|---:|
| wall time | 10.9 s | 716.9 s |
| reactions scored | 87 | 95 (0 excluded as constant) |
| R-hat median | 1.0027 | 1.0039 |
| R-hat p90 | 1.0171 | 1.0137 |
| R-hat max | 1.0276 | 1.0377 |
| R-hat > 1.01 | 13.8 % (12) | 14.7 % (14) |
| R-hat > 1.1 | 0.0 % | 0.0 % |

With either method, no reaction exceeded 1.1. CHRR did not agree better than ACHR on e_coli_core: its highest R-hat was `EX_succ_e` at 1.0377 against 1.0276 for ACHR, and 14.7 % of its reactions exceeded 1.01 against 13.8 %. CHRR took 66 times the wall time of ACHR (133 times that of the 5.4 s repeat), with one run each. The percentages have different denominators, 87 and 95 scored reactions. The 8 reactions that ACHR left constant (all exactly 0.0) were scored with CHRR. CHRR computes every flux of a sample from the nullspace basis (`v0 + N x`), and these 8 reactions vary within a chain by at most 1.6e-13, with means of the order of 1e-14, which is the size of the floating-point rounding error in that product.

On a 95-reaction model, ACHR and CHRR with the default `thinning` and 300 samples per chain both gave agreement at 1.1 for every reaction, and CHRR cost 66 times as much time (133 times against the repeat) without lowering the share above 1.01.

### CHRR at genome scale

CHRR was not run on yeast-GEM with 4 chains × 300 samples. A probe with 2 chains × 20 samples (`thinning=100`) took 8147.9 s (about 136 min), 14.2 times the 572.3 s of the full ACHR run, with a peak memory of about 31 GB of the 32 GB allocated. Each chain runs an FVA with its own worker pool, and that the pools cause the memory use was not tested. The model yeast-GEM has 43 times the reactions of e_coli_core.

Each CHRR chain ran an FVA, a nullspace computation and the MVE rounding before its first step, and then 1,000 warmup steps and 2,000 sampling steps. The probe does not separate these parts. That the cost before the first step dominates, and that most of it is the MVE rounding, is an inference from the small number of steps, and the parts were not timed. The function `random_sampling` computes this transform anew in every call, so each chain pays it.

The R-hat of the probe (median 5.7274, p90 165.18, max 1.899e9 for `r_4782`; all 4105 reactions scored, 97.3 % above 1.01 and 93.6 % above 1.1) does not show that CHRR converges worse than ACHR at genome scale. With 20 samples per chain, the within-chain variance `W` is estimated from too few samples to be stable. A reaction that shows almost no variance in 20 draws by chance, combined with any difference between the chain means (`B/n`), gives a large R-hat whatever its distribution. The probe cannot distinguish a CHRR that does not converge on yeast-GEM from an R-hat that needs more samples, and a run with enough samples for a stable R-hat has the cost problem of the full run.

Twenty samples per chain are too few for R-hat on yeast-GEM, and whether CHRR converges on yeast-GEM with 300 samples per chain is open.

## Choice of `thinning` and `n_samples`

The defaults are `method='achr'`, `thinning=100` and `n_samples=1000` ([Tuned parameter defaults](../../tuned-parameters.md)). ACHR is the default because on e_coli_core CHRR differed from ACHR by +0.0012 in median R-hat (1.0027 and 1.0039), by −0.0034 in p90 (1.0171 and 1.0137) and by +0.0101 in maximum (1.0276 and 1.0377), with one run each and no measured spread between sets of seeds, and CHRR took 66 to 133 times as long.

On a model the size of e_coli_core, the default `thinning` with 300 samples per chain gave chains that agree at R-hat 1.1 for every scored reaction. On yeast-GEM, no setting measured with R-hat or `ρ` gave converged samples. A `thinning` up to 500 left `ρ` at 0.825 for seed 0 (0.644 to 0.825 over four seeds), and moving the same 30,000 steps from `n_samples` to `thinning` moved the median R-hat from 1.1020 to 1.1010 and the shares above 1.01 and 1.1 by at most 1.7 percentage points. With `n_samples=300` and `thinning=100`, 50.7 % of the 3325 scored reactions had R-hat above 1.1.

The docstring of `random_sampling` recommends, for genome-scale models, a `thinning` of at least 1000 or a larger `n_samples`, `method='chrr'`, or an ESS or R-hat check. A `thinning` of 1000 or more was not measured. The driver script runs the R-hat check: it samples several chains with different seeds at given settings and reports the share of reactions above the R-hat thresholds, so a sampling result can be checked at the settings that produced it.

One change outside the parameters was identified and not pursued: CHRR recomputes its rounding transform in every call. The chains run in separate processes at the same time, so to save that cost the transform would have to be computed once per model and passed to every chain. The saving depends on the share of the rounding in the 136 min of the probe, which was not measured.

## Other sampling settings

Two settings of `method='random_objective'` differ from `randomSampling` of RAVEN in MATLAB on purpose.

The setting `replace_max_bound` (default `False`; `replaceBoundsWithInf` in MATLAB defaults to true) replaces the largest upper bound, the big-M value that stands for an unconstrained reaction, with infinity before sampling, and replaces the most negative lower bound, if it is below 0, with minus infinity. Models in the RAVEN convention use 1000 as the big-M for almost every reaction (4,083 of the 4,102 reactions of yeast-GEM). With `True`, the call fails after 9.6 s with `OptimizationError: Solver status is 'unbounded'`. A probe of 50 random objectives, drawn as the sampler draws them on the model with the bounds replaced, gave 49 optimal results and 1 unbounded result (one probe of 50 objectives). One unbounded objective stops all draws. The abort mechanism is read from the cobra code, where `Model.optimize` raises on the status `unbounded` (`raise_error=False` does not change this) and the retry loop of the sampler never sees the status. The sample at which the run aborted was not recorded.

With `False`, 200 samples completed (68.2 s with 12 processes, including the loopless FVA). Counting a flux as at the bound when `|v| ≥ 1000 × (1 − 1e-9)`, the 200 × 4102 sample matrix (820,400 entries) had 54 entries at the bound (0.0066 %) in one run, with 15 samples containing at least one such reaction and 23 reactions (0.56 % of 4102) at the bound in at least one sample. A second run had 269 entries (0.033 %), 16 samples (8.0 %) and 32 reactions (0.78 %). The share of reactions at the bound was 0.56 % in one run and 0.78 % in the other, and the share of entries is 0.0066 to 0.033 %.

The method `random_objective` with a fixed seed is not reproducible on yeast-GEM: the loopless FVA returned 2307 and 2308 eligible reactions in two runs with the same seed. That a different eligible set shifts every random draw is an inference from these two counts.

The setting `loopless_good_reactions` (default `True`) selects which reactions are eligible as random objectives. MATLAB excludes every reaction whose FVA maximum is infinite or above 0.999 times the largest upper bound (999 on a model capped at 1000), and, when the smallest lower bound is negative, every reaction whose FVA minimum is minus infinity or below 0.999 times that bound. It treats proximity to the big-M as a sign of a thermodynamic loop. It also excludes reactions that cannot carry a non-zero flux and, in an ecModel, the `usage_prot_` reactions. That rule also excludes reactions that reach the bound for metabolic reasons. A loopless FVA excludes only the reactions that take part in infeasible cycles, at a higher cost.

## Limits

- Each comparison between chains ran once, except the repeated e_coli_core ACHR run, with seeds 0 to `n_chains − 1`. The spread of R-hat between sets of seeds was not measured, so differences of the size seen in the reallocation (0.0010 in the median) are within an unknown spread. The spread of `ρ` between seeds was measured for the single chain and reaches 0.28.
- One small and one genome-scale model were tested. The single-chain runs and the comparisons between chains used two different yeast-GEM files (v9.1.0 and v9.1.1).
- The ACHR wall times and the e_coli_core R-hat values depend on the software versions and the load of the node.
- The wall times depend on the other jobs on the shared nodes and on the Gurobi thread count, which was left at its default and not logged.
- R-hat is computed in its basic form, without split chains or rank normalisation.
- The default `n_samples=1000`, a `thinning` above 500, and CHRR on yeast-GEM with more than 20 samples per chain were not tested.

## Reproduction

The driver for the comparisons between chains is `scripts/analyze_sampling_convergence.py` in raven-toolbox. The other scripts are in `scripts/parameter_tuning/sampling/`: `summarize_chains.py`, `single_chain_autocorr.py` (autocorrelation of one chain), `random_objective_bounds.py` (`replace_max_bound`) and `posthoc_checks.py`.

```bash
python scripts/analyze_sampling_convergence.py \
    --model /path/to/yeast-GEM.xml --out work/ \
    --n-chains 4 --n-samples 300 --thinning 100 --warmup 1000
python scripts/parameter_tuning/sampling/single_chain_autocorr.py \
    --model /path/to/yeast-GEM.xml --thinning 100 --n-samples 300 \
    --warmup 1000 --seed 0 --time-warmup --out results/
python scripts/parameter_tuning/sampling/random_objective_bounds.py \
    --model /path/to/yeast-GEM.xml --n-samples 200 --seed 0 \
    --n-proc 12 --n-probe 50 --out results/
```

The CHRR runs use the same command with `--method chrr`. The script caches the chains per model, method, `n_chains`, `n_samples`, `thinning` and `warmup` under `--out`, and a run with a cached configuration computes R-hat from the stored chains without sampling. Another `--thinning` or `--n-samples` samples again and is cached separately. On yeast-GEM, four ACHR chains in parallel on 12 cores took 2.8 times the wall time of one chain at the same settings. The two runs read different yeast-GEM files, and the cause of the difference was not measured (see [Agreement between chains on yeast-GEM](#agreement-between-chains-on-yeast-gem)). A sweep at genome scale can therefore take more time than one chain per configuration suggests.
