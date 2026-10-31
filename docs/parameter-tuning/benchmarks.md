# Benchmarks of `fseof`, `remove_genes` and other defaults

These benchmarks record parameters whose defaults were measured or checked without a study of their own. Two of them were run with raven-toolbox commit `94f39407` on 2026-10-30: the effect of `flux_eps` on the targets of `fseof`, and the handling of reactions without an enzyme in `remove_genes`. A table lists literature and convention values, checked on 2026-06-20, with what supports each of them.

The parameters with a measurement campaign of their own have studies listed under [Parameter tuning](index.md). [Tuned parameter defaults](../tuned-parameters.md) gives the current value and a one-line reason for every parameter of both implementations.

## Set-up

The `fseof` benchmark ran on iJO1366 (2,583 reactions) with the biomass reaction of the model as objective and `EX_succ_e` (succinate exchange) as target. The other arguments were `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 and the default `equality=False`, which sets each enforced flux as the lower bound of the target reaction.

`fseof` solves each enforced level in two steps, as RAVEN's `FSEOF` does: it maximises the objective, then minimises the sum of fluxes with the objective held at 0.999999 of that optimum. A reaction is a target when its absolute flux exceeds `1e-10` at some level, the standard deviation of its absolute flux is above 0, the absolute correlation between its absolute flux and the enforced flux reaches `correlation_threshold`, and the slope of the linear fit of its absolute flux against the enforced flux is not 0. A target with a positive slope is an amplify target. A target with a negative slope is a knockout target when its last absolute flux is at most `1e-8`, and a knockdown target otherwise. `fseof` and RAVEN's `FSEOF` use these thresholds as fixed values.

The `remove_genes` benchmark ran on e_coli_core (95 reactions) from the cobrapy distribution, with bounds as shipped, Gurobi 13.0.1, raven-toolbox commit `94f39407` and RAVEN commit `2d0630e3`. It deleted `b1779`, the only gene of GAPD (glyceraldehyde-3-phosphate dehydrogenase), with each setting of `blocked_reactions` in `remove_genes` and of `removeBlockedRxns` in RAVEN's `removeGenes`. The predicted growth is the optimal flux through the biomass reaction of the model, in h⁻¹. The unmodified model has 95 reactions and predicts a growth rate of 0.874 h⁻¹.

The checks of literature and convention values ran on 2026-06-20 with yeast-GEM (4,102 reactions), iJO1366 (2,583) and e_coli_core (95). The table names the model for the `fseof` rows only.

## Results

### `fseof` targets at three values of `flux_eps`

| `flux_eps` | Amplify targets | Knockdown and knockout targets |
|---|---|---|
| `1e-8` | 18 | 408 |
| `1e-7` | 18 | 408 |
| `1e-6` (default) | 18 | 408 |

Of the 408 reactions, 406 are knockdown targets and 2 are knockout targets.

### `remove_genes` after deletion of `b1779` from e_coli_core

| Call | Reactions left | Predicted growth (h⁻¹) | GAPD |
|---|---|---|---|
| `remove_genes(..., blocked_reactions="constrain")` (default) | 95 | 0.000 | kept, bounds `(0, 0)` |
| `remove_genes(..., blocked_reactions="remove")` | 94 | 0.000 | deleted |
| `remove_genes(..., blocked_reactions="keep")` | 95 | 0.874 | kept, bounds unchanged |
| `removeGenes(model, genes)` (`removeBlockedRxns` false, default) | 95 | 0.000 | kept, bounds `[0 0]` |
| `removeGenes(model, genes, 'removeBlockedRxns', true)` | 94 | 0.000 | deleted |

### Checked literature and convention values

Both implementations have the same value or behaviour for each of these parameters, and none was changed. The third column gives what supports the value; only the three `fseof` rows record a sweep.

| Parameter | Value | Basis |
|---|---|---|
| `fseof.n_steps` | `10` | Value of [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); 5 and 20 gave the same target set on iJO1366 |
| `fseof.max_fraction` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); values below 0.9 admitted spurious targets on iJO1366, and 0.99 found no further targets |
| `fseof.correlation_threshold` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10); 0.7 added four spurious amplify targets on iJO1366 |
| `connect_blocked_reactions.threshold` | `1.0` | Correct for models in the RAVEN convention, where exchange reactions have bounds of ±1000; RAVEN's `fillGaps` uses a fixed threshold of 1 |
| `connect_blocked_reactions.allow_net_production` | `False` | Keeps the steady-state balance `S @ v == 0`, the stricter test; `True` relaxes it to `S @ v >= 0` |
| `fill_gaps_fast_lp.epsilon` | `1e-4` | Value of the fastGapFill paper, [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) |
| `fill_gaps_milp.big_m` | `1000.0` | Matches the ±1000 bounds of the RAVEN convention |
| `check_tasks.close_boundaries` | `False` | Matches RAVEN's `checkTasks`, against which published task lists were curated; `True` closes the exchange reactions of the model so that the task defines the whole boundary |

The three `fseof` rows date from 2026-06-20 and were not repeated with commit `94f39407`.

## `flux_eps` in `fseof`

`flux_eps` is the floor below which `fseof` treats the theoretical maximum of the target flux as zero; the scan then raises an error. The classification of targets does not read `flux_eps`, and RAVEN's `FSEOF` has no such parameter. On iJO1366 with target `EX_succ_e`, the three values gave 18 amplify targets and 408 knockdown and knockout targets each. From the code, two values of `flux_eps` give different results only when the theoretical maximum of the target lies between them: `fseof` then raises at the larger value and runs at the smaller.

## Reactions without an enzyme in `remove_genes`

`blocked_reactions` in `remove_genes`, and `removeBlockedRxns` in RAVEN's `removeGenes`, decide what happens to a reaction whose gene rule is emptied by a deletion. By default both keep such a reaction with bounds of zero, and the two defaults gave the same model. After deletion of `b1779`, that model predicts no growth, because GAPD stays in the network with no capacity to carry flux. `"remove"` and `removeBlockedRxns` true also predicted no growth; they delete GAPD, which changes the number of reactions and the set of reaction identifiers. `"keep"` leaves GAPD with an empty gene rule and its original bounds, so the model predicted the growth of the unmodified model, 0.874 h⁻¹, although the only gene of GAPD was deleted. GAPD is essential for aerobic growth on glucose in e_coli_core, so the growth predicted with `"keep"` is a false positive. The docstring of `remove_genes` states no use for `"keep"`; a use suggested for it is editing gene annotations without changing the network (unverified, no source in the code).

## Choice of defaults

The measurement gives no reason to change `flux_eps` from `1e-6`. `blocked_reactions="constrain"` stays the default of `remove_genes`; it gives the model that RAVEN's `removeGenes` gives by default. `"remove"` and `"keep"` are available on request.

## Limits

Each benchmark used one model: iJO1366 with one target for `fseof`, and e_coli_core with one deleted gene for `remove_genes`. Criterion 1 of the [evaluation methodology](index.md#evaluation-methodology) asks for a large and a small model. The solver of the `fseof` runs and the number of runs per value are not recorded, and the criterion for a spurious target in the 2026-06-20 sweeps is not recorded. The rows of the checked values without a sweep rest on the literature or on a convention.

raven-toolbox contains no script for these benchmarks. The unit tests `tests/test_analysis_fseof.py` and `tests/test_manipulation_remove.py` of raven-toolbox check, on small test networks, the classification thresholds of `fseof` and the three settings of `blocked_reactions`.
