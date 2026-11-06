# Benchmarks of `fseof`, `remove_genes` and other defaults

Six defaults of raven-toolbox were measured without a study of their own: `flux_eps` of `fseof`; `n_steps`, `max_fraction` and `correlation_threshold` of `fseof`; `blocked_reactions` of `remove_genes`; and `threshold` of `connect_blocked_reactions`. A table lists further defaults that rest on the literature or on a convention. All runs used raven-toolbox commit `94f39407` and were made on 2026-11-01.

The measurements give no reason to change `flux_eps` from `1e-6`. The sweep does not select the other three `fseof` defaults, which follow [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (not checked against the paper), and the default of `blocked_reactions` gives the model that `removeGenes` of RAVEN gives by default.

Parameters with a measurement campaign of their own have a study listed under [Parameter tuning](index.md). [Tuned parameter defaults](../tuned-parameters.md) gives the current value of every parameter of both implementations with a one-line reason.

## Set-up

### `fseof`

The `fseof` benchmarks ran on iJO1366 (2,583 reactions) with the biomass reaction of the model as the objective and `EX_succ_e` (succinate exchange) as the target. In the `flux_eps` runs the enforced flux ran from 1.5387 to 15.387 in 10 levels, and the unconstrained growth rate was 0.98237 h⁻¹. The other arguments were `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 and the default `equality=False`, which sets each enforced flux as the lower bound of the target reaction.

At each enforced level `fseof` solves two problems, as `FSEOF` of RAVEN does. It first maximises the objective and then minimises the sum of fluxes with the objective held at 0.999999 of that optimum. A reaction is a target when four conditions hold:

- its absolute flux exceeds `1e-10` at some level;
- the standard deviation of its absolute flux is above 0;
- the absolute correlation between its absolute flux and the enforced flux reaches `correlation_threshold`;
- the slope of the linear fit of its absolute flux against the enforced flux is not 0.

A target with a positive slope is an amplify target. A target with a negative slope is a knockout target when its last absolute flux is at most `1e-8`, and a knockdown target otherwise. `fseof` and `FSEOF` of RAVEN use these thresholds as fixed values.

The sweep changed one of `n_steps`, `max_fraction` and `correlation_threshold` at a time, with three runs per value on freshly read models. Every configuration gave the same counts and the same added and dropped targets in all three runs. The sweep reports two categories of target, and neither measures error:

1. **Added:** the target appears at the swept value and not in the default run, which is the set difference from the default. An added target is no evidence of error.
2. **Noise:** the standard deviation of the absolute flux of the target across the scan is below `1e-6`.

The default run contains 19 noise tracks. All are knockdown targets with a standard deviation of 5.08e-7, a slope of -1.15e-7 and a correlation of -1: `EGMEACPR`, `OGMEACPD`, `OPMEACPR`, `OPMEACPS`, `MALCOAMT`, `OGMEACPR`, `OGMEACPS`, `DM_amob_c`, `EX_meoh_e`, `AMAOTr`, `AOXSr2`, `BTS5`, `DBTS`, `EPMEACPR`, `I2FE2SR`, `MEOHtex`, `MEOHtrpp`, `OPMEACPD` and `PMEACPE` (biotin synthesis and methanol export). The classification keeps them, because it requires a standard deviation above 0.

### `remove_genes`

The `remove_genes` benchmark ran on e_coli_core (95 reactions) from the cobrapy distribution, with the bounds of the distribution, raven-toolbox commit `94f39407` and RAVEN commit `2d0630e3`. It deleted `b1779`, the only gene of GAPD (glyceraldehyde-3-phosphate dehydrogenase), with each setting of `blocked_reactions` in `remove_genes` and of `removeBlockedRxns` in `removeGenes` of RAVEN. The predicted growth is the optimal flux through the biomass reaction of the model, in h⁻¹. The unmodified model has 95 reactions and predicts a growth rate of 0.874 h⁻¹. Each call ran once.

### `connect_blocked_reactions`

The test of `threshold` used a synthetic network. The draft has an import of A of at most 0.5, the reaction A to B, and B as a dead end, and the template has the exchange `EX_B`. The other arguments were at their defaults (`min_flux` 0.1). Each value ran once.

### Software

The Python runs used Python 3.14.2, cobra 0.32.1, optlang 1.9.1 and Gurobi 13.0.3 (gurobipy wheel). The MATLAB run used R2024b with RAVEN and Gurobi 13.0.1, selected through `setRavenSolver('gurobi')`. The `flux_eps` runs were repeated three times per value, each on a freshly read model.

## Results

### `fseof` targets at three values of `flux_eps`

| `flux_eps` | Amplify targets | Knockdown and knockout targets |
|---|---|---|
| `1e-8` | 18 | 408 |
| `1e-7` | 18 | 408 |
| `1e-6` (default) | 18 | 408 |

Of the 408 reactions, 406 are knockdown targets and 2 are knockout targets. Three runs per value gave the same set of targets.

`flux_eps` is the floor below which `fseof` treats the theoretical maximum of the target flux as zero, and the scan then raises an error. The classification of targets does not read `flux_eps`, and `FSEOF` of RAVEN has no such parameter. From the code, two values of `flux_eps` give different results if and only if the theoretical maximum of the target lies between them: `fseof` raises at the larger value and runs at the smaller.

### `fseof` targets at other values of three parameters

The table lists iJO1366 with the target `EX_succ_e`. The last two columns give the targets that the swept value adds to the default set and drops from it.

| Parameter | Value | Amplify targets | Knockdown and knockout targets | Added (amplify / knockdown and knockout) | Dropped (amplify / knockdown and knockout) |
|---|---|---|---|---|---|
| (defaults) | `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 | 18 | 408 | - | - |
| `n_steps` | 5 | 18 | 410 | 0 / 3 (`PGI`, `ACt2rpp`, `ACt4pp`) | 0 / 1 (`PDH`) |
| `n_steps` | 20 | 16 | 412 | 0 / 4 (`EX_co2_e`, `CO2tex`, `CO2tpp`, `GLYCTO2`) | 2 / 0 (`FUM`, `MDH`) |
| `max_fraction` | 0.5 | 15 | 414 | 1 / 6 (`SUCOAS`; `EX_co2_e`, `CO2tex`, `CO2tpp`, `ICDHyr`, `TKT2`, `AKGDH`) | 4 / 0 (`FUM`, `MDH`, `HEX7`, `XYLI2`) |
| `max_fraction` | 0.99 | 18 | 408 | 0 / 1 (`PGI`) | 0 / 1 (`PDH`) |
| `correlation_threshold` | 0.7 | 22 | 416 | 4 / 8 (`FRD3`, `NADH18pp`, `ICL`, `MALS`; `EX_co2_e`, `CO2tex`, `CO2tpp`, `ICDHyr`, `AKGDH`, `PGI`, `TKT2`, `GLYCTO2`) | 0 / 0 |
| `correlation_threshold` | 0.95 | 16 | 406 | 0 / 0 | 2 / 2 (`FUM`, `MDH`; `PDH`, `RPE`) |

Every swept value changes the target set. None of the added targets is a noise track, because they are added relative to the default and the noise category does not apply to them. The four added amplify targets at `correlation_threshold` 0.7 have an absolute correlation of 0.71 to 0.72 in the default scan and a standard deviation of 0.62 to 4.4. At `max_fraction` 0.5, `FBA3` and `PFK_3` change from knockout to knockdown targets. At 0.99 the 19 noise targets change from knockdown to knockout targets. Whether any added target is biologically wrong was not assessed.

### `remove_genes` after deletion of `b1779` from e_coli_core

| Call | Reactions left | Predicted growth (h⁻¹) | GAPD |
|---|---|---|---|
| `remove_genes(..., blocked_reactions="constrain")` | 95 | 0.000 | kept, bounds `(0, 0)` |
| `remove_genes(...)` without the keyword (default) | 95 | 0.000 | kept, bounds `(0, 0)` |
| `remove_genes(..., blocked_reactions="remove")` | 94 | 0.000 | deleted |
| `remove_genes(..., blocked_reactions="keep")` | 95 | 0.874 | kept, bounds `(-1000, 1000)`, empty gene rule |
| `removeGenes(model, genes)` (`removeBlockedRxns` false, default) | 95 | 0.000 | kept, bounds `[0 0]` |
| `removeGenes(model, genes, 'removeBlockedRxns', true)` | 94 | 0.000 | deleted |
| unmodified model | 95 | 0.874 (MATLAB biomass flux 0.8739) | present |

`blocked_reactions` of `remove_genes` and `removeBlockedRxns` of `removeGenes` determine what happens to a reaction whose gene rule is emptied by a deletion. Both default settings keep such a reaction with bounds of zero, and the two gave the same model. After the deletion of `b1779` that model predicts no growth, because GAPD stays in the network without capacity to carry flux. With `"remove"` and with `removeBlockedRxns` true the model also predicted no growth. Both delete GAPD, which changes the number of reactions and the set of reaction identifiers.

The setting `"keep"` leaves GAPD with an empty gene rule and unchanged bounds, so the model predicted the growth of the unmodified model, 0.874 h⁻¹, although the only gene of GAPD was deleted. The default setting predicted no growth after the same deletion, so the growth predicted with `"keep"` is probably a false positive in this model (the bounds are those included with e_coli_core). The docstring of `remove_genes` states no use for `"keep"`. The documentation names the editing of gene annotations without changing the network as a use, and the code gives no source for that use.

### `connect_blocked_reactions` at four values of `threshold`

The draft network has an import of A, the reaction A to B and no exit for B, and the template supplies `EX_B`.

| `threshold` | Gap filled | Reactions added | Maximum flux of the reaction A to B afterwards |
|---|---|---|---|
| 0.01 | yes | `EX_B` | 0.5 |
| 0.1 | yes | `EX_B` | 0.5 |
| 0.5 | no | none | 0 |
| 1.0 (default) | no | none | 0 |

At every value `cannot_connect` also lists the reversible `EX_A`, which is blocked in the draft and is never a candidate.

### Checked literature and convention values

Both implementations have the same value or behaviour for each of these parameters, and none was changed. The third column gives what supports the value. The three `fseof` rows and the `connect_blocked_reactions.threshold` row record a measurement, and the other rows were not run.

| Parameter | Value | Basis |
|---|---|---|
| `fseof.n_steps` | `10` | Value of [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper). On iJO1366, 5 steps gave 18 amplify and 410 knockdown and knockout targets and 20 steps gave 16 and 412, so the target set changes with `n_steps` |
| `fseof.max_fraction` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper). On iJO1366, 0.5 added 7 targets and dropped 4, and 0.99 gave the same counts as 0.9 with one target added and one dropped |
| `fseof.correlation_threshold` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper). On iJO1366, 0.7 added 4 amplify and 8 knockdown and knockout targets, and 0.95 dropped 2 and 2 |
| `connect_blocked_reactions.threshold` | `1.0` | Suited to models in the RAVEN convention, where exchange reactions have bounds of ±1000. On one synthetic network with a maximum flux of 0.5, values of 0.01 and 0.1 filled the gap and values of 0.5 and 1.0 did not (one run per value). The test shows that a reaction must carry more than the threshold, and no comparison of correctness was made |
| `connect_blocked_reactions.allow_net_production` | `False` | Keeps the steady-state balance `S @ v == 0`, the stricter test. `True` relaxes it to `S @ v >= 0` |
| `fill_gaps_fast_lp.epsilon` | `1e-4` | Value of the fastGapFill paper, [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) |
| `fill_gaps_milp.big_m` | `1000.0` | Matches the ±1000 bounds of the RAVEN convention |
| `check_tasks.close_boundaries` | `False` | Matches `checkTasks` of RAVEN, against which published task lists were curated. `True` closes the exchange reactions of the model, which makes the task define the whole boundary |

## Choice of defaults

The measurements give no reason to change `flux_eps` from `1e-6`. The sweep does not select the other three `fseof` defaults: the target set changes with each swept value by 2 to 12 targets, and no tested value leaves it unchanged. The defaults follow [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (not checked against the paper). The 19 noise tracks are in the target set at every setting.

The default `blocked_reactions="constrain"` of `remove_genes` gives the model that `removeGenes` of RAVEN gives by default. The settings `"remove"` and `"keep"` are selected with the `blocked_reactions` argument.

## Limits

Each benchmark used one model: iJO1366 with one target for `fseof`, e_coli_core with one deleted gene for `remove_genes`, and a synthetic network for `connect_blocked_reactions`. Criterion 1 of the [evaluation methodology](index.md#evaluation-methodology) asks for a large and a small model. Gurobi was the sole solver. Neither the biological correctness of the targets added by a swept value nor the literature basis of the cited values was assessed. The rows `connect_blocked_reactions.allow_net_production`, `fill_gaps_fast_lp.epsilon`, `fill_gaps_milp.big_m` and `check_tasks.close_boundaries` rest on the literature or on a convention, and no test was run for them.

## Source

The scripts are in the raven-docs repository under `scripts/parameter_tuning/benchmarks/`: `small.py` (`flux_eps` and `remove_genes`), `fseof_sweep.py` (the sweep of three parameters), `gapfill_threshold.py` (the test of `threshold`) and `mat_small.m` (`removeGenes` in RAVEN). For example:

```bash
python scripts/parameter_tuning/benchmarks/small.py --repeats 3
python scripts/parameter_tuning/benchmarks/fseof_sweep.py --repeats 3
python scripts/parameter_tuning/benchmarks/gapfill_threshold.py
```

The unit tests `tests/test_analysis_fseof.py` and `tests/test_manipulation_remove.py` of raven-toolbox check, on small test networks, the classification thresholds of `fseof` and the three settings of `blocked_reactions`.
