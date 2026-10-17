# Parameter benchmarks

Parameters whose defaults were measured but did not need a study of their own.
Everything here was run on 2026-06-20 unless a row says otherwise, on yeast-GEM
(4,102 reactions), iJO1366 (2,583) and e_coli_core (95).

The parameters that did get a dedicated campaign are in the studies listed
under [Parameter tuning](index.md); the current value and one-line reason for every
parameter on either side is in
[Tuned parameter defaults](../tuned-parameters.md).

## Two measurements that show MATLAB's default should change

### `fseof`: MATLAB classifies targets with no tolerance at all

`flux_eps` is the floor below which a reaction's flux trend is treated as noise
rather than signal. It does three jobs inside the classifier: skip a reaction
whose flux is flat across the scan, skip one whose regression slope is
indistinguishable from zero, and call a reaction a knockout when its flux at
maximum enforcement is effectively zero.

On iJO1366:

| `flux_eps` | Amplified | Knocked down or out |
|---|---|---|
| `1e-8` | 18 | 414 |
| `1e-7` | 18 | 414 |
| **`1e-6`** *(default)* | 18 | **393** |

The 21 extra targets admitted below `1e-6` all have a flux standard deviation
around `5e-7` across the ten scan steps, Gurobi's primal feasibility tolerance
accumulated across 2,583 reactions, which is floating-point summation noise
rather than a metabolic trend. Reporting them would send a user to engineer
reactions that are functionally zero throughout.

MATLAB's `FSEOF.m` compares each step against the previous one as bare floats,
with no threshold of any kind. That is stricter than the `1e-8` row here, so 21
is a lower bound on what the MATLAB side would flag, not a measurement of it.
Giving MATLAB a floor means adding one rather than exposing a value it already
has.

### `remove_genes`: the MATLAB default predicts growth after deleting an essential gene

`blocked_reactions` decides what happens to a reaction whose gene rule is emptied
by a deletion. Deleting `b1779` from e_coli_core removes the only gene for GAPD,
which is essential for aerobic growth on glucose:

| `blocked_reactions` | Reactions left | Predicted growth | |
|---|---|---|---|
| `'keep'` *(MATLAB)* | 95 | 0.874 | GAPD survives with an empty rule and runs unconstrained |
| **`'remove'`** *(Python)* | 94 | **0.000** | GAPD is deleted, glycolysis breaks |

Both behaviours are defensible, for different jobs. Keeping the reaction is right
when editing gene annotations, where the network should not change as a result.
Removing it is right for essentiality and engineering work, where a reaction with
no enzyme should not carry flux. The defaults disagree about which job is the
common one, and the MATLAB default silently produces a false negative in
essentiality screens.

## Literature and convention values, checked

These were swept and confirmed rather than changed. Both implementations agree on
each, so there is nothing to reconcile; the value of the check is that the number
is no longer taken on trust.

| Parameter | Value | What the sweep showed |
|---|---|---|
| `fseof.n_steps` | `10` | Choi et al. 2010's value; 5 and 20 give the same target set on iJO1366 |
| `fseof.max_fraction` | `0.9` | Choi et al. 2010; below 0.9 admits spurious targets, 0.99 finds nothing extra |
| `fseof.correlation_threshold` | `0.9` | Choi et al. 2010; 0.7 adds four spurious amplification targets |
| `connect_blocked_reactions.eps` | `1.0` | Correct for RAVEN-convention models, where exchanges carry ±1000 bounds |
| `connect_blocked_reactions.allow_net_production` | `False` | The stricter question, and the one the function exists to ask |
| `fill_gaps_fast_lp.epsilon` | `1e-4` | The fastGapFill paper's value |
| `fill_gaps_kumar_milp.big_m` | `1000.0` | Matches RAVEN-convention bounds |
| `check_tasks.close_boundaries` | `False` | Matches RAVEN's `checkTasks`, which published task lists were curated against; `True` closes the model's own exchanges so that the task is the whole boundary |
