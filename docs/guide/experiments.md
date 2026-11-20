# Comparing a model with measured conditions

A model is tested against an experiment by setting what the experiment controlled, solving the model, and comparing what it predicts with what was measured. The experiments functions do this for a set of conditions, each with a measured growth rate and measured exchange fluxes, and reduce the comparison to one number. That number is what a calibration minimises, for example the tuning of kcats in an enzyme-constrained model.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `loadFluxData` | `load_flux_data` | read one file of measured conditions |
| `loadExperimentData` | `load_experiment_data` | read the three data files of a folder |
| `applyFluxDataConstraints` | `apply_flux_data_constraints` | constrain a model to one condition |
| `simulateConditions` | `simulate_conditions` | solve the model for every condition |
| `computeCarbonWeights` | `compute_carbon_weights` | put growth and exchange fluxes on one carbon scale |
| `datasetRmse` | `dataset_rmse` | the distance of one dataset |
| `experimentDistance` | `experiment_distance` | the distance of all datasets of a folder |

## Setup

The model is `yeast-GEM.yml` from [`docs/data/`](../data/README.md). `fluxData.tsv` and `zeroFlux.tsv` are in the same directory, and the examples read the folder `.`, the current directory.

A data folder holds up to three files, and each is optional:

| File | Content |
|---|---|
| `fluxData.tsv` | conditions with a measured growth rate and measured exchange fluxes |
| `maxGrowth.tsv` | conditions with one carbon source each, simulated with the uptake fully open |
| `zeroFlux.tsv` | reactions that carry no flux in any condition, one reaction id per line below the header `Rxns` |

`fluxData.tsv` and `maxGrowth.tsv` have the same layout, a tab-delimited file with one row per condition:

- `Condition` is the name of the carbon source. The exchange column with the same metabolite name is the carbon source of the row, and a name can occur in several rows.
- `Ptot` is the total protein content in g/gDW and `grRate` the growth rate in 1/h. `Ptot` is empty (`NaN`) when it was not measured.
- One column per exchange reaction, with the header `<metabolite> (<reaction id>)`, holds the flux in mmol/gDW/h. The sign follows the model, so in yeast-GEM an uptake is negative. `NaN` means that the flux was not measured, and `-1000` or `1000` means an uptake or an excretion that is not limited.
- `weight` is optional and is the weight of the condition in the distance. A condition with the weight 0 is left out of the simulation and of the distance, and its `Condition` need not match an exchange column, so a row that another step reads, such as a standard condition, can stay in the file. Without the column every condition has the weight 1.
- `source` is optional and is a free text that says where the row comes from.

The conditions of `maxGrowth.tsv` are simulated with the uptake of the carbon source opened to `-1000`, and only the growth rate is compared. In a model where nothing besides the uptake limits growth, that gives a growth rate without biological meaning, so the file is for models in which something else limits growth, such as the enzyme capacity of an enzyme-constrained model. The examples on this page use `fluxData.tsv` and `zeroFlux.tsv`.

The example file has three conditions:

```text title="fluxData.tsv"
Condition	Ptot	grRate	glucose (r_1714)	oxygen (r_1992)	carbon dioxide (r_1672)	ethanol (r_1761)	weight	source
glucose	NaN	0.80	-10.0	-24.0	26.0	0.0	1	written for this guide
glucose	NaN	0.30	-10.0	0.0	18.0	17.0	1	written for this guide
ethanol	NaN	0.55	NaN	-35.0	16.0	-20.0	1	written for this guide
```

The values are written for this guide and are not measurements. The second row has an oxygen flux of exactly 0, which marks an anaerobic condition. `zeroFlux.tsv` lists the acetate exchange `r_1634` and the glycerol exchange `r_1808`.

## Load the data

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('yeast-GEM.yml');
experimentData = loadExperimentData('.');
fluxData = experimentData.fluxData;
for i = 1:numel(fluxData.conds)
    fprintf('%-8s growth %.2f /h, weight %d\n', fluxData.conds{i}, ...
        fluxData.grRate(i), fluxData.weight(i));
end
fprintf('zero-flux reactions: %s\n', strjoin(experimentData.zeroFlux, ', '));
if isempty(experimentData.maxGrowth)
    disp('maximum growth data: none');
end
```

```text
glucose  growth 0.80 /h, weight 1
glucose  growth 0.30 /h, weight 1
ethanol  growth 0.55 /h, weight 1
zero-flux reactions: r_1634, r_1808
maximum growth data: none
```

`loadExperimentData` returns a struct. A file that is not in the folder gives `[]`, or an empty cell array for `zeroFlux`, and no error. `loadFluxData` reads one file and returns the struct of its conditions: `conds`, `Ptot`, `grRate`, `exchFluxes` (conditions in rows), `exchMets` and `exchRxnIDs`, and `weight` and `source` when the file has the columns.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.experiments import (
    apply_flux_data_constraints, compute_carbon_weights, experiment_distance,
    load_experiment_data, simulate_conditions,
)
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("yeast-GEM.yml")
data = load_experiment_data(".")
flux = data.flux_data
for name, growth, weight in zip(flux.conds, flux.gr_rate, flux.weight):
    print(f"{name:<8} growth {growth:.2f} /h, weight {weight:.0f}")
print("zero-flux reactions:", ", ".join(data.zero_flux))
print("maximum growth data:", data.max_growth)
```

```text
glucose  growth 0.80 /h, weight 1
glucose  growth 0.30 /h, weight 1
ethanol  growth 0.55 /h, weight 1
zero-flux reactions: r_1634, r_1808
maximum growth data: None
```

`load_experiment_data` returns an `ExperimentData` with the attributes `flux_data`, `max_growth` and `zero_flux`. A file that is not in the folder gives `None`, or an empty list for `zero_flux`, and no error. `load_flux_data` reads one file and returns a `FluxData`: `conds`, `p_tot`, `gr_rate`, `exch_fluxes` (conditions in rows), `exch_mets` and `exch_rxn_ids`, and `weight` and `source`, which are `None` when the file lacks the columns.
:::
::::

## Constrain the model to one condition

`applyFluxDataConstraints` and `apply_flux_data_constraints` set the bounds of the biomass reaction and of the measured exchange reactions to one condition, chosen by its number or its name. The biomass reaction gets the measured growth rate as its upper bound. An exchange reaction gets the measured flux as one bound and 0 as the other, so it may carry less than the measured flux. A percentage between 0 and 100 instead sets both bounds around the measured flux, with that percentage in total: 10 gives 0.95 and 1.05 times the flux. The preferred carbon source of the model is closed first, so that the data alone decides which carbon source is used, and its reaction id is the argument `cSource` or `c_source`.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
constrained = applyFluxDataConstraints(model, fluxData, 'r_2111', ...
    'condition', 'ethanol', 'cSource', 'r_1714');
ethanolIdx = getIndexes(constrained, 'r_1761', 'rxns');
fprintf('ethanol bounds: [%g %g]\n', constrained.lb(ethanolIdx), constrained.ub(ethanolIdx));
sol = solveLP(constrained);
fprintf('growth: %.2f /h\n', sol.f);

strict = applyFluxDataConstraints(model, fluxData, 'r_2111', ...
    'condition', 'ethanol', 'looseStrictFlux', 10);
fprintf('ethanol bounds at 10%%: [%g %g]\n', strict.lb(ethanolIdx), strict.ub(ethanolIdx));
```

```text
ethanol bounds: [-20 0]
growth: 0.55 /h
ethanol bounds at 10%: [-21 -19]
```

The function returns the constrained model and leaves the input unchanged. `'condition'` counts from 1 when it is a number.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
with model:
    apply_flux_data_constraints(
        model, flux, bio_rxn_id="r_2111", condition="ethanol", c_source="r_1714",
    )
    ethanol = model.reactions.get_by_id("r_1761")
    print(f"ethanol bounds: {ethanol.bounds}")
    print(f"growth: {model.slim_optimize():.2f} /h")

with model:
    apply_flux_data_constraints(
        model, flux, bio_rxn_id="r_2111", condition="ethanol", loose_strict_flux=10,
    )
    print(f"ethanol bounds at 10%: {ethanol.bounds}")
```

```text
ethanol bounds: (-20.0, 0.0)
growth: 0.55 /h
ethanol bounds at 10%: (-21.0, -19.0)
```

The function changes the model in place, so the call is made inside `with model:` and the bounds are restored when the block ends. `condition` counts from 0 when it is a number.
:::
::::

In both blocks, the measured growth rate is a bound and not a target. The solve returns the highest growth rate that the model reaches within the bounds, which is the measured rate when the model can reach it and lower when it cannot. A model that cannot reach the measured rate within the measured uptake is the finding of the comparison.

## Solve every condition

`simulateConditions` and `simulate_conditions` solve the model once for each condition of a dataset, and record the growth rate and the fluxes that are compared with the measurements. For each condition with a weight other than 0 they:

1. close the uptake of every carbon source that occurs in a condition with a weight other than 0, so that the carbon source of one condition cannot carry flux in another;
2. open the carbon source of the condition: its lower bound becomes the measured uptake when the argument `constrain` is true (a flux dataset), or `-1000` when it is false (a maximum growth dataset, which asks for the best growth on the carbon source);
3. make the model anaerobic when the oxygen flux of the condition is exactly 0 and a function for it is given, and change the protein content of the model when `Ptot` is given and not 0 and a function for it is given;
4. solve, and record the growth rate, the flux of every measured exchange and the flux of every reaction in the zero-flux list, except the carbon source of the condition.

The changes are made on a model that is restored afterwards. What makes a model anaerobic, and how the protein content is changed, depend on the organism, so the functions that do it have no default and are passed as arguments. Here the anaerobic condition file of [Growth media and conditions](media.md) is applied. A third function, the argument `optimize`, replaces the solve. It defaults to `solveLP` in MATLAB and to `model.optimize()` in Python.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
makeAnaerobic = @(m) applyCondition(m, 'anaerobic.yml');
sims = simulateConditions(model, fluxData, true, experimentData.zeroFlux, 'r_2111', ...
    'makeAnaerobic', makeAnaerobic);
for i = 1:numel(sims)
    fprintf('%-8s growth %.3f /h, glycerol %.2f\n', fluxData.conds{i}, ...
        sims(i).growth, sims(i).blockFluxes(strcmp(sims(i).blockRxnIDs, 'r_1808')));
end
```

```text
glucose  growth 0.837 /h, glycerol 0.00
glucose  growth 0.161 /h, glycerol 1.86
ethanol  growth 0.583 /h, glycerol 0.00
```

`sims` is a struct array with one element per condition. Its fields are `feasible`, `skipped`, `growth`, `exchRxnIDs` and `exchFluxes` (the measured exchanges), and `blockRxnIDs` and `blockFluxes` (the zero-flux reactions). The functions that make the model anaerobic and change its protein content take a model and return a model.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.conditions import apply_condition

def make_anaerobic(m):
    apply_condition(m, "anaerobic.yml")

sims = simulate_conditions(
    model, flux, constrain=True, zero_flux_rxns=data.zero_flux,
    bio_rxn_id="r_2111", make_anaerobic=make_anaerobic,
)
for name, sim in zip(flux.conds, sims):
    print(f"{name:<8} growth {sim.growth:.3f} /h, glycerol {sim.block_fluxes['r_1808']:.2f}")
```

```text
glucose  growth 0.837 /h, glycerol 0.00
glucose  growth 0.161 /h, glycerol 1.86
ethanol  growth 0.583 /h, glycerol 0.00
```

`sims` is a list of `ConditionSimResult`, one per condition, with the attributes `feasible`, `skipped`, `growth`, `exch_fluxes` and `block_fluxes` (dictionaries keyed by reaction id). The functions that make the model anaerobic and change its protein content take a model and change it in place.
:::
::::

The second condition has no oxygen uptake and grows slower than the first. It also secretes glycerol, which is in the zero-flux list, so the distance counts that flux as a deviation from 0. A flux in that list that is simulated at exactly 0 is left out of the distance, so that a correct prediction does not lower the error.

## The distance

The growth rate is in 1/h and the exchange fluxes are in mmol/gDW/h, so they cannot be added as they are. `computeCarbonWeights` and `compute_carbon_weights` give each exchange reaction the number of carbon atoms of the metabolite that it exchanges, which turns the flux into Cmmol/gDW/h. The biomass reaction gets 41, the assumed carbon content of biomass in Cmmol/gDW. A metabolite without carbon (oxygen, water) or without a formula gets 1, so that its deviation still counts.

For each condition the distance is the root mean square of the carbon-weighted differences between measured and simulated values: the growth rate, each measured exchange flux, and each zero-flux reaction with a flux other than 0. A condition that the model cannot solve gets the penalty 99, which is meant to be larger than any distance of a solved condition. The distance of a dataset is the mean, over the conditions with a weight other than 0, of the condition values, each multiplied by its weight. A condition with the weight 0 has the value `NaN` and is not in the mean, and a dataset in which every condition has the weight 0 has the distance `NaN` and is left out of the combination. `experimentDistance` and `experiment_distance` combine the flux dataset and the maximum growth dataset as `(flux + w * maxGrowth) / (1 + w)`, where `w` is the argument `maxGrowthWeight` or `max_growth_weight` (default 1). A dataset that the folder lacks does not contribute, and the maximum growth dataset compares the growth rate alone.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
rxnIds = [fluxData.exchRxnIDs(:); experimentData.zeroFlux(:); {'r_2111'}];
carbonWeights = computeCarbonWeights(model, rxnIds, 'r_2111');
fprintf('glucose %g, oxygen %g, growth %g\n', carbonWeights('r_1714'), ...
    carbonWeights('r_1992'), carbonWeights('r_2111'));
[distance, detail] = experimentDistance(experimentData, sims, [], carbonWeights, 'r_2111');
fprintf('distance: %.3f\n', distance);
fprintf('per condition: %s\n', mat2str(detail.fluxData', 3));
```

```text
glucose 6, oxygen 1, growth 41
distance: 1.808
per condition: [1.03 3.47 0.926]
```

`computeCarbonWeights` returns a `containers.Map` from reaction id to weight. `experimentDistance` takes the simulation of the flux dataset and the simulation of the maximum growth dataset, with `[]` for a dataset that the folder lacks, and returns the distance and a struct with the value of each condition.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
rxn_ids = [*flux.exch_rxn_ids, *data.zero_flux, "r_2111"]
carbon_weights = compute_carbon_weights(model, rxn_ids, "r_2111")
print(f"glucose {carbon_weights['r_1714']:g}, oxygen {carbon_weights['r_1992']:g}, "
      f"growth {carbon_weights['r_2111']:g}")
distance, detail = experiment_distance(
    data, flux_sims=sims, max_growth_sims=None,
    carbon_weights=carbon_weights, bio_rxn_id="r_2111",
)
print(f"distance: {distance:.3f}")
print("per condition:", ", ".join(f"{x:.3f}" for x in detail["flux_data"]))
```

```text
glucose 6, oxygen 1, growth 41
distance: 1.808
per condition: 1.030, 3.469, 0.926
```

`compute_carbon_weights` returns a dictionary from reaction id to weight. `experiment_distance` takes the simulation of each dataset as a keyword, `None` for a dataset that the folder lacks, and returns the distance and a dictionary with the value of each condition under `"flux_data"` and `"max_growth"`.
:::
::::

A condition with the weight 0 is neither simulated nor part of the distance. Here the first condition gets the weight 0:

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
experimentData.fluxData.weight(1) = 0;
fluxData = experimentData.fluxData;
sims = simulateConditions(model, fluxData, true, experimentData.zeroFlux, 'r_2111', ...
    'makeAnaerobic', makeAnaerobic);
fprintf('skipped: %s\n', mat2str([sims.skipped]));
[distance, detail] = experimentDistance(experimentData, sims, [], carbonWeights, 'r_2111');
fprintf('distance: %.3f\n', distance);
fprintf('per condition: %s\n', mat2str(detail.fluxData', 3));
```

```text
skipped: [true false false]
distance: 2.197
per condition: [NaN 3.47 0.926]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
flux.weight[0] = 0
sims = simulate_conditions(
    model, flux, constrain=True, zero_flux_rxns=data.zero_flux,
    bio_rxn_id="r_2111", make_anaerobic=make_anaerobic,
)
print("skipped:", [sim.skipped for sim in sims])
distance, detail = experiment_distance(
    data, flux_sims=sims, max_growth_sims=None,
    carbon_weights=carbon_weights, bio_rxn_id="r_2111",
)
print(f"distance: {distance:.3f}")
print("per condition:", ", ".join(f"{x:.3f}" for x in detail["flux_data"]))
```

```text
skipped: [True, False, False]
distance: 2.197
per condition: nan, 3.469, 0.926
```
:::
::::

The first condition has `skipped` true and `feasible` false, and its value is `NaN`. The distance is the mean of the values of the other two conditions.

A calibration changes a parameter of the model, repeats the simulation and the distance, and keeps the change when the distance falls. `dataset_rmse` and `datasetRmse` give the value of a single dataset when the folder holds only one.

## Differences between the toolboxes

| | MATLAB | Python |
|---|---|---|
| Data | struct with the fields `conds`, `Ptot`, `grRate`, `exchFluxes`, `exchMets`, `exchRxnIDs` | `FluxData` with the attributes `conds`, `p_tot`, `gr_rate`, `exch_fluxes`, `exch_mets`, `exch_rxn_ids` |
| Condition by number | from 1 | from 0 |
| Constraining a model | returns the constrained model | changes the model in place |
| Biomass reaction | required argument, an error when it is not in the model | keyword, read as flux 0 in the result when it is not in the model |
| Carbon weights | `containers.Map` | dictionary |
| Simulation result | struct array | list of `ConditionSimResult` |
| Condition with the weight 0 | `sims(i).skipped` is true and its value in `detail` is `NaN` | `ConditionSimResult.skipped` is `True` and its value in `detail` is `NaN` |
| Solver | `optimize` is a function handle that returns `x`, `f` and `stat`, default `solveLP` | `optimize` is a function that returns a cobrapy solution, default `model.optimize()` |

:::{admonition} Troubleshooting
:class: warning

- A condition name has no matching exchange column. The error is `simulateConditions:unmatchedCondition` in MATLAB and a `ValueError` in Python. The name of a condition is the metabolite name in a column header, so a condition `glucose` needs a column `glucose (r_1714)`. Only conditions with a weight other than 0 are matched, so a row that is not part of the distance can have the weight 0.
- A condition has the value `NaN`. Its weight is 0, and it is left out of the simulation and of the distance.
- An anaerobic row grows on oxygen. A row with an oxygen flux of exactly 0 is made anaerobic only when a function for it is given. Without one the row is solved with the oxygen exchange of the model as it is.
- Every condition has the distance 99. The model is infeasible for the condition, often because a measured flux does not fit the model, such as an uptake that is higher than the model can use or an excretion that it cannot make. Constrain the model to the condition and solve to see which bound conflicts.
- A measured zero and a missing value look alike. A flux of `0.0` is a measurement and is compared with the simulated flux. `NaN`, and an empty cell in the file, is not compared.
- An exchange fixes the sign of its flux. The data follows the sign convention of the model. A model that writes uptake as `=> metabolite` has the opposite sign of yeast-GEM ([Solvers](solvers.md)).
:::

## See also

- [Simulating growth with FBA](fba.md): the solve that each condition runs.
- [Growth media and conditions](media.md): the condition file that makes the model anaerobic.
- [Solvers and configuration](solvers.md): the solver of a repeated simulation.
