# Parameter benchmarks

Parameters whose defaults were measured but did not need a study of their own.
The measurements were run on 2026-06-20 on yeast-GEM (4,102 reactions), iJO1366 (2,583) and e_coli_core (95); the `fseof` and `remove_genes` measurements in the next section were run on 2026-10-30.

The parameters that had a dedicated campaign are in the studies listed under [Parameter tuning](index.md); the current value and one-line reason for every parameter on either side is in [Tuned parameter defaults](../tuned-parameters.md).

## Measurements of `fseof` and `remove_genes` defaults

### `fseof` classifier thresholds and `flux_eps`

`fseof` and RAVEN's `FSEOF` classify a reaction from its fluxes across the scan with the same fixed thresholds: a reaction is a target when some absolute flux exceeds `1e-10`, the standard deviation of its absolute flux is above 0 and the correlation reaches `correlation_threshold`; it is a knockout when the slope is negative and the last absolute flux is at most `1e-8`. `flux_eps` is the floor below which the theoretical maximum of the target flux is treated as zero, in which case the scan raises an error. It takes no part in the classification, and RAVEN's `FSEOF` has no `flux_eps` parameter. On iJO1366 with target `EX_succ_e`, `flux_eps` does not change the counts.

Measured on iJO1366 (2,583 reactions) with the model's biomass reaction as objective, `EX_succ_e` as target, `n_steps` 10, `max_fraction` 0.9, `correlation_threshold` 0.9 and the default `equality=False`, with raven-toolbox commit `94f39407`, run on 2026-10-30:

| `flux_eps` | Amplified | Knocked down or out |
|---|---|---|
| `1e-8` | 18 | 408 |
| `1e-7` | 18 | 408 |
| **`1e-6`** *(default)* | 18 | **408** |

Of the 408 reactions, 406 are knockdown targets and 2 are knockout targets. The counts are the same at the three values on this model and target. Each level is solved in two steps with the objective held at 0.999999 of its optimum in the second.

### `remove_genes` handling of reactions without an enzyme

`blocked_reactions` in `remove_genes`, and `removeBlockedRxns` in RAVEN's `removeGenes`, decide what happens to a reaction whose gene rule is emptied by a deletion. Both tools constrain such a reaction by default. Deleting `b1779` from e_coli_core removes the only gene for GAPD, which is essential for aerobic growth on glucose. The unmodified model has 95 reactions and predicts a growth rate of 0.874.

| Call | Reactions left | Predicted growth | GAPD |
|---|---|---|---|
| `remove_genes(..., blocked_reactions="constrain")` *(default)* | 95 | 0.000 | kept, bounds `(0, 0)` |
| `remove_genes(..., blocked_reactions="remove")` | 94 | 0.000 | deleted |
| `remove_genes(..., blocked_reactions="keep")` | 95 | 0.874 | kept, bounds unchanged |
| `removeGenes(model, genes)` *(`removeBlockedRxns` false, default)* | 95 | 0.000 | kept, bounds `[0 0]` |
| `removeGenes(model, genes, 'removeBlockedRxns', true)` | 94 | 0.000 | deleted |

`"constrain"` and RAVEN's default give the same model. Both predict no growth after the deletion, because the reaction stays in the network with no capacity to carry flux. `"remove"` and `removeBlockedRxns` true also predict no growth and differ in that the reaction is deleted, which matters when the number of reactions or the reaction identifiers are used afterwards. `"keep"` leaves the reaction with an empty rule and unchanged bounds, so it runs unconstrained and the model predicts growth although the only enzyme of an essential step is gone; it is meant for editing gene annotations, where the network should not change as a result.

Measured on e_coli_core from the cobrapy distribution (bounds as shipped), Gurobi 13.0.1, raven-toolbox commit `94f39407` and RAVEN commit `2d0630e3`, run on 2026-10-30.

## Checked literature and convention values

These values were swept and confirmed, and none was changed. Both implementations agree on each, so there is nothing to reconcile; the value of the check is that each number rests on a measurement.

| Parameter | Value | What the sweep showed |
|---|---|---|
| `fseof.n_steps` | `10` | Choi et al. 2010's value; 5 and 20 give the same target set on iJO1366 |
| `fseof.max_fraction` | `0.9` | Choi et al. 2010; below 0.9 admits spurious targets, 0.99 finds nothing extra |
| `fseof.correlation_threshold` | `0.9` | Choi et al. 2010; 0.7 adds four spurious amplification targets |
| `connect_blocked_reactions.eps` | `1.0` | Correct for RAVEN-convention models, where exchanges carry ±1000 bounds |
| `connect_blocked_reactions.allow_net_production` | `False` | The stricter question, and the one the function exists to ask |
| `fill_gaps_fast_lp.epsilon` | `1e-4` | The fastGapFill paper's value |
| `fill_gaps_milp.big_m` | `1000.0` | Matches RAVEN-convention bounds |
| `check_tasks.close_boundaries` | `False` | Matches RAVEN's `checkTasks`, which published task lists were curated against; `True` closes the model's own exchanges so that the task is the whole boundary |

The `fseof.n_steps`, `fseof.max_fraction` and `fseof.correlation_threshold` rows were measured on 2026-06-20 and were not rerun for this page.
