# Benchmarks of `fseof`, `remove_genes` and other defaults

These benchmarks record parameters whose defaults were measured or checked without a study of their own. All were run with raven-toolbox commit `94f39407` on 2026-11-01: the effect of `flux_eps` on the targets of `fseof`, the handling of reactions without an enzyme in `remove_genes`, a sweep of three `fseof` parameters and a test of `connect_blocked_reactions.threshold`. A table lists literature and convention values with what supports each of them.

The parameters with a measurement campaign of their own have studies listed under [Parameter tuning](index.md). [Tuned parameter defaults](../tuned-parameters.md) gives the current value and a one-line reason for every parameter of both implementations.

## Set-up

The `fseof` benchmarks ran on iJO1366 (2,583 reactions) with the biomass reaction of the model as objective and `EX_succ_e` (succinate exchange) as target. In the `flux_eps` table the enforced flux ran from 1.5387 to 15.387 in 10 levels, and the unconstrained growth rate was 0.98237 h⁻¹. The other arguments were `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 and the default `equality=False`, which sets each enforced flux as the lower bound of the target reaction.

`fseof` solves each enforced level in two steps, as RAVEN's `FSEOF` does: it maximises the objective, then minimises the sum of fluxes with the objective held at 0.999999 of that optimum. A reaction is a target when its absolute flux exceeds `1e-10` at some level, the standard deviation of its absolute flux is above 0, the absolute correlation between its absolute flux and the enforced flux reaches `correlation_threshold`, and the slope of the linear fit of its absolute flux against the enforced flux is not 0. A target with a positive slope is an amplify target. A target with a negative slope is a knockout target when its last absolute flux is at most `1e-8`, and a knockdown target otherwise. `fseof` and RAVEN's `FSEOF` use these thresholds as fixed values.

The `remove_genes` benchmark ran on e_coli_core (95 reactions) from the cobrapy distribution, with bounds as shipped, raven-toolbox commit `94f39407` and RAVEN commit `2d0630e3`. It deleted `b1779`, the only gene of GAPD (glyceraldehyde-3-phosphate dehydrogenase), with each setting of `blocked_reactions` in `remove_genes` and of `removeBlockedRxns` in RAVEN's `removeGenes`. The predicted growth is the optimal flux through the biomass reaction of the model, in h⁻¹. The unmodified model has 95 reactions and predicts a growth rate of 0.874 h⁻¹. Each call ran once.

The Python runs used Python 3.14.2, cobra 0.32.1, optlang 1.9.1 and Gurobi 13.0.3 (gurobipy wheel); MATLAB R2024b ran RAVEN with Gurobi 13.0.1 selected through `setRavenSolver('gurobi')`. The `flux_eps` runs were repeated three times per value, each on a freshly read model, and gave the same target set and labels every time.

The sweep of `fseof` ran on iJO1366 with the settings above and Gurobi 13.0.3, changing one of `n_steps`, `max_fraction` and `correlation_threshold` at a time, with three runs per value on freshly read models. All three runs of every configuration gave the same counts and the same added and dropped targets. Two categories of target are reported, and neither measures error:

1. **Added:** the target appears at the swept value and not in the default run (the set difference from the default). An added target is no evidence of error.
2. **Noise:** the standard deviation of its absolute flux across the scan is below `1e-6`.

The default run contains 19 noise tracks, all knockdown targets with a standard deviation of 5.08e-7, a slope of -1.15e-7 and a correlation of -1: `EGMEACPR`, `OGMEACPD`, `OPMEACPR`, `OPMEACPS`, `MALCOAMT`, `OGMEACPR`, `OGMEACPS`, `DM_amob_c`, `EX_meoh_e`, `AMAOTr`, `AOXSr2`, `BTS5`, `DBTS`, `EPMEACPR`, `I2FE2SR`, `MEOHtex`, `MEOHtrpp`, `OPMEACPD` and `PMEACPE` (biotin synthesis and methanol export). The classification rule above keeps them, because it requires a standard deviation above 0.

The test of `connect_blocked_reactions.threshold` used a synthetic network: a draft with an import of A of at most 0.5, the reaction A to B, and B as a dead end, and a template with the exchange `EX_B`. The other arguments were at their defaults (`min_flux` 0.1). Each value ran once, with Gurobi 13.0.3.

## Results

### `fseof` targets at three values of `flux_eps`

| `flux_eps` | Amplify targets | Knockdown and knockout targets |
|---|---|---|
| `1e-8` | 18 | 408 |
| `1e-7` | 18 | 408 |
| `1e-6` (default) | 18 | 408 |

Of the 408 reactions, 406 are knockdown targets and 2 are knockout targets. Three runs per value gave the same set of targets.

### `fseof` targets at other values of three parameters

iJO1366, target `EX_succ_e`. The last two columns list the targets that the swept value adds to the default set and drops from it.

| Parameter | Value | Amplify targets | Knockdown and knockout targets | Added (amplify / knockdown and knockout) | Dropped (amplify / knockdown and knockout) |
|---|---|---|---|---|---|
| (defaults) | `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 | 18 | 408 | - | - |
| `n_steps` | 5 | 18 | 410 | 0 / 3 (`PGI`, `ACt2rpp`, `ACt4pp`) | 0 / 1 (`PDH`) |
| `n_steps` | 20 | 16 | 412 | 0 / 4 (`EX_co2_e`, `CO2tex`, `CO2tpp`, `GLYCTO2`) | 2 / 0 (`FUM`, `MDH`) |
| `max_fraction` | 0.5 | 15 | 414 | 1 / 6 (`SUCOAS`; `EX_co2_e`, `CO2tex`, `CO2tpp`, `ICDHyr`, `TKT2`, `AKGDH`) | 4 / 0 (`FUM`, `MDH`, `HEX7`, `XYLI2`) |
| `max_fraction` | 0.99 | 18 | 408 | 0 / 1 (`PGI`) | 0 / 1 (`PDH`) |
| `correlation_threshold` | 0.7 | 22 | 416 | 4 / 8 (`FRD3`, `NADH18pp`, `ICL`, `MALS`; `EX_co2_e`, `CO2tex`, `CO2tpp`, `ICDHyr`, `AKGDH`, `PGI`, `TKT2`, `GLYCTO2`) | 0 / 0 |
| `correlation_threshold` | 0.95 | 16 | 406 | 0 / 0 | 2 / 2 (`FUM`, `MDH`; `PDH`, `RPE`) |

Every swept value changes the target set. None of the added targets is a noise track: they are added, and the noise category does not apply to them. The four added amplify targets at `correlation_threshold` 0.7 have an absolute correlation of 0.71 to 0.72 in the default scan and a standard deviation of 0.62 to 4.4. Whether any added target is biologically wrong was not assessed. At `max_fraction` 0.5, `FBA3` and `PFK_3` change from knockout to knockdown targets; at 0.99, the 19 noise targets change from knockdown to knockout targets.

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

### `connect_blocked_reactions` at four values of `threshold`

Synthetic network described in [Set-up](#set-up).

| `threshold` | Gap filled | Reactions added | Maximum flux of the reaction A to B afterwards |
|---|---|---|---|
| 0.01 | yes | `EX_B` | 0.5 |
| 0.1 | yes | `EX_B` | 0.5 |
| 0.5 | no | none | 0 |
| 1.0 (default) | no | none | 0 |

At every value, `cannot_connect` also lists the reversible `EX_A`, which is blocked in the draft and is never a candidate.

### Checked literature and convention values

Both implementations have the same value or behaviour for each of these parameters, and none was changed. The third column gives what supports the value; the three `fseof` rows and the `connect_blocked_reactions.threshold` row record a measurement.

| Parameter | Value | Basis |
|---|---|---|
| `fseof.n_steps` | `10` | Value of [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper); on iJO1366, 5 steps gave 18 amplify and 410 knockdown and knockout targets and 20 steps gave 16 and 412, so the target set changes with `n_steps` |
| `fseof.max_fraction` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper); on iJO1366, 0.5 added 7 targets and dropped 4, and 0.99 gave the same counts as 0.9 with one target added and one dropped |
| `fseof.correlation_threshold` | `0.9` | [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (value not checked against the paper); on iJO1366, 0.7 added 4 amplify and 8 knockdown and knockout targets, and 0.95 dropped 2 and 2 |
| `connect_blocked_reactions.threshold` | `1.0` | Suited to models in the RAVEN convention, where exchange reactions have bounds of ±1000; on one synthetic network with a maximum flux of 0.5, values of 0.01 and 0.1 filled the gap and values of 0.5 and 1.0 did not (one run per value; the test shows that a reaction must carry more than the threshold, and no correctness comparison was made) |
| `connect_blocked_reactions.allow_net_production` | `False` | Keeps the steady-state balance `S @ v == 0`, the stricter test; `True` relaxes it to `S @ v >= 0` |
| `fill_gaps_fast_lp.epsilon` | `1e-4` | Value of the fastGapFill paper, [Thiele et al. 2014](https://doi.org/10.1093/bioinformatics/btu321) |
| `fill_gaps_milp.big_m` | `1000.0` | Matches the ±1000 bounds of the RAVEN convention |
| `check_tasks.close_boundaries` | `False` | Matches RAVEN's `checkTasks`, against which published task lists were curated; `True` closes the exchange reactions of the model so that the task defines the whole boundary |

The three `fseof` rows and the `connect_blocked_reactions.threshold` row ran with commit `94f39407`. The other rows were not run.

## `flux_eps` in `fseof`

`flux_eps` is the floor below which `fseof` treats the theoretical maximum of the target flux as zero; the scan then raises an error. The classification of targets does not read `flux_eps`, and RAVEN's `FSEOF` has no such parameter. On iJO1366 with target `EX_succ_e`, the three values gave 18 amplify targets and 408 knockdown and knockout targets each. From the code, two values of `flux_eps` give different results only when the theoretical maximum of the target lies between them: `fseof` then raises at the larger value and runs at the smaller.

## Reactions without an enzyme in `remove_genes`

`blocked_reactions` in `remove_genes`, and `removeBlockedRxns` in RAVEN's `removeGenes`, decide what happens to a reaction whose gene rule is emptied by a deletion. By default both keep such a reaction with bounds of zero, and the two defaults gave the same model. After deletion of `b1779`, that model predicts no growth, because GAPD stays in the network with no capacity to carry flux. `"remove"` and `removeBlockedRxns` true also predicted no growth; they delete GAPD, which changes the number of reactions and the set of reaction identifiers. `"keep"` leaves GAPD with an empty gene rule and unchanged bounds, so the model predicted the growth of the unmodified model, 0.874 h⁻¹, although the only gene of GAPD was deleted. GAPD is essential for aerobic growth on glucose in e_coli_core, so the growth predicted with `"keep"` is a false positive. The docstring of `remove_genes` states no use for `"keep"`. Editing gene annotations without changing the network is a use given for it in the documentation, without a source in the code.

## Choice of defaults

The measurement gives no reason to change `flux_eps` from `1e-6`. The sweep of `fseof` does not select the other three defaults: the target set changes with each swept value, by 2 to 12 targets, and no tested value leaves it unchanged. The defaults follow [Choi et al. 2010](https://doi.org/10.1128/AEM.00115-10) (not checked against the paper). The 19 noise tracks are in the target set at every setting. `blocked_reactions="constrain"` is the default of `remove_genes`; it gives the model that RAVEN's `removeGenes` gives by default. `"remove"` and `"keep"` are available on request.

## Limits

Each benchmark used one model: iJO1366 with one target for `fseof`, e_coli_core with one deleted gene for `remove_genes`, and a synthetic network for `connect_blocked_reactions`. Criterion 1 of the [evaluation methodology](index.md#evaluation-methodology) asks for a large and a small model. Gurobi was the sole solver. Whether the targets added by a swept value are biologically wrong was not assessed, and neither was the literature basis of the cited values. The rows `connect_blocked_reactions.allow_net_production`, `fill_gaps_fast_lp.epsilon`, `fill_gaps_milp.big_m` and `check_tasks.close_boundaries` rest on the literature or on a convention; no test was run for them.

## Source

The scripts are in raven-toolbox under `scripts/parameter_tuning/benchmarks/`: `small.py` (`flux_eps` and `remove_genes`), `fseof_sweep.py` (the sweep of three parameters), `gapfill_threshold.py` (the test of `threshold`) and `mat_small.m` (`removeGenes` in RAVEN). For example:

```bash
python scripts/parameter_tuning/benchmarks/small.py --repeats 3
python scripts/parameter_tuning/benchmarks/fseof_sweep.py --repeats 3
python scripts/parameter_tuning/benchmarks/gapfill_threshold.py
```

The unit tests `tests/test_analysis_fseof.py` and `tests/test_manipulation_remove.py` of raven-toolbox check, on small test networks, the classification thresholds of `fseof` and the three settings of `blocked_reactions`.
