# Growth media and conditions

A flux balance analysis (FBA) result applies to one medium. The medium is the set of open exchange reactions and the width of their bounds. A condition stores a medium as reviewable data, where a script of bound-setting calls hides it.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getExchangeRxns` | `Model.exchanges` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | find the exchange reactions |
| `setExchangeBounds` | `Model.medium` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | set a whole medium and close all other uptakes |
| `setParam` | `set_reaction_bounds` | set the bounds of one reaction |
| `getMinimalMedium` | `minimal_medium` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | find the smallest medium that supports growth |
| `applyCondition` | `apply_condition`, `load_condition` | apply a condition file |

## Setup

The model is `yeast-GEM.yml` from [`docs/data/`](../data/README.md), with an aerobic minimal glucose medium applied.

## Open exchanges

An exchange reaction connects a boundary metabolite to nothing, so its flux is the rate at which the metabolite enters or leaves the system. yeast-GEM writes its exchange reactions as `metabolite <=>`, so a negative flux is entry and a positive flux is exit. The medium is the set of exchange reactions with a negative lower bound. A model that writes uptake as `=> metabolite` has the opposite sign ([Solvers](solvers.md)).

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('yeast-GEM.yml');
[exchangeRxns, exchangeIdx] = getExchangeRxns(model);
fprintf('%d exchange reactions\n', numel(exchangeRxns));

open = sort(exchangeIdx(model.lb(exchangeIdx) < 0));
for i = 1:numel(open)
    fprintf('  %s  %-28s %8.1f\n', model.rxns{open(i)}, ...
        model.rxnNames{open(i)}, -model.lb(open(i)));
end
```

```text
273 exchange reactions
  r_1654  ammonium exchange              1000.0
  r_1714  D-glucose exchange                1.0
  r_1832  H+ exchange                    1000.0
  r_1861  iron(2+) exchange              1000.0
  r_1992  oxygen exchange                1000.0
  r_2005  phosphate exchange             1000.0
  r_2020  potassium exchange             1000.0
  r_2049  sodium exchange                1000.0
  r_2060  sulphate exchange              1000.0
  r_2100  water exchange                 1000.0
  r_4593  chloride exchange              1000.0
  r_4594  Cu2(+) exchange                1000.0
  r_4595  Mn(2+) exchange                1000.0
  r_4596  Zn(2+) exchange                1000.0
  r_4597  Mg(2+) exchange                1000.0
  r_4600  Ca(2+) exchange                1000.0
```

`getExchangeRxns` identifies an exchange reaction by its stoichiometry (a reaction without substrates or without products), so it does not depend on a naming convention. `reactionType` selects a subset. The values `'uptake'`, `'excrete'`, `'reverse'` and `'blocked'` classify a reaction by what its bounds permit. The values `'in'` and `'out'` classify by the side of the boundary metabolite and ignore the bounds.

The filter in the code and `'uptake'` answer different questions. `'uptake'` returns the reactions that can take up and cannot secrete. Every open exchange reaction in yeast-GEM also has an upper bound of 1000, so it can secrete and is classified `'reverse'`. The medium is the selection `model.lb < 0`.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("yeast-GEM.yml")
shipped = dict(model.medium)          # keep it; later steps restore from here
print(len(model.exchanges), "exchange reactions")

for rxn_id, uptake in sorted(model.medium.items()):
    print(f"  {rxn_id}  {model.reactions.get_by_id(rxn_id).name:<28} {uptake:>8}")
```

```text
270 exchange reactions
  r_1654  ammonium exchange              1000.0
  r_1714  D-glucose exchange                1.0
  r_1832  H+ exchange                    1000.0
  r_1861  iron(2+) exchange              1000.0
  r_1992  oxygen exchange                1000.0
  r_2005  phosphate exchange             1000.0
  r_2020  potassium exchange             1000.0
  r_2049  sodium exchange                1000.0
  r_2060  sulphate exchange              1000.0
  r_2100  water exchange                 1000.0
  r_4593  chloride exchange              1000.0
  r_4594  Cu2(+) exchange                1000.0
  r_4595  Mn(2+) exchange                1000.0
  r_4596  Zn(2+) exchange                1000.0
  r_4597  Mg(2+) exchange                1000.0
  r_4600  Ca(2+) exchange                1000.0
```

`model.medium` is a dictionary of `{exchange identifier: maximum uptake rate}`. The rate is a positive number, and cobrapy flips the sign, so an entry of `1.0` means a lower bound of `-1.0`. The dictionary lists the open exchange reactions, and the loop prints 16 of 270 reactions.
:::
::::

The toolboxes count the exchange reactions differently, and both counts are correct. cobrapy sorts reactions with a single metabolite into `exchanges`, `demands` and `sinks`, and `getExchangeRxns` returns all of them. In yeast-GEM the difference is three reactions, `r_2111` (growth) and the sinks `r_4062` and `r_4064`, so MATLAB reports 273 where `model.exchanges` reports 270.

## Changing one nutrient

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = setParam(model, 'lb', 'r_1714', -10);   % D-glucose exchange
sol = solveLP(model);
idx = getIndexes(model, 'r_1714', 'rxns');
fprintf('[%g %g] -> %.4f /h\n', model.lb(idx), model.ub(idx), sol.f);
```

```text
[-10 1000] -> 0.8370 /h
```

`setParam` takes a reaction identifier, a list of identifiers or indices, and applies one value to all of them or one value to each. `'lb'`, `'ub'` and `'eq'` set bounds, and `'obj'` sets the objective coefficient.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.conditions import set_reaction_bounds

glucose = model.reactions.get_by_id("r_1714")
set_reaction_bounds(glucose, -10.0, 1000.0)
print(glucose.bounds, "->", f"{model.slim_optimize():.4f} /h")
```

```text
(-10.0, 1000.0) -> 0.8370 /h
```

`reaction.bounds = (-10.0, 1000.0)` has the same effect for ordinary edits. `set_reaction_bounds` writes the underlying attributes directly, so it also accepts `lb > ub`, which the setter of cobrapy rejects as invalid. A condition uses this to force flux through a reaction with a sentinel bound.

`slim_optimize` returns the objective value without building a `Solution`, which is cheaper in a loop over many bound settings.
:::
::::

## Defining a whole medium

Assigning to the medium replaces it, and every exchange reaction that is not in the dictionary is closed. The assignment suits an exact recipe. A change to one entry edits a copy of `dict(model.medium)`.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
% every uptake closed
[~, exchIdx] = getExchangeRxns(model);
modelClosed = setParam(model, 'lb', model.rxns(exchIdx), 0);
sol = solveLP(modelClosed);
fprintf('growth with nothing to eat: %.4f /h\n', sol.f);

% the shipped recipe, with more glucose
model = setParam(model, 'lb', 'r_1714', -10);
sol = solveLP(model);
fprintf('complete medium:           %.4f /h\n', sol.f);
```

```text
growth with nothing to eat:  /h
complete medium:           0.8370 /h
```

The first line prints no number. With every uptake closed, the linear programme (LP) is infeasible, `solveLP` returns an empty array in `sol.f` and sets `sol.stat` to `-1`, and `fprintf` prints nothing for an empty argument. `sol.stat` is checked before the value is read ([Simulating growth with FBA](fba.md)).

`setExchangeBounds` corresponds to the assignment of `model.medium`. It takes metabolite names, sets their exchange bounds, and with the default `closeOthers` closes every other uptake. `mediaOnly` restricts it to the extracellular compartment, which leaves intracellular sink reactions unchanged.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
with model:
    model.medium = {}                             # every uptake closed
    print(f"growth with nothing to eat: {model.slim_optimize():.4f} /h")

with model:
    model.medium = {"r_1714": 10.0, "r_1992": 1000.0}   # only glucose and oxygen
    growth = round(model.slim_optimize(), 4) + 0.0      # + 0.0 turns solver noise -0.0 into 0.0
    print(f"glucose and oxygen alone:  {growth:.4f} /h")

model.medium = {**shipped, "r_1714": 10.0}        # the shipped recipe, more glucose
print(f"complete medium:           {model.slim_optimize():.4f} /h")
```

```text
growth with nothing to eat: nan /h
glucose and oxygen alone:  0.0000 /h
complete medium:           0.8370 /h
```

Glucose and oxygen are not sufficient. yeast-GEM also needs nitrogen, phosphate, sulphate and several ions. A medium built from `dict(model.medium)` with individual entries edited keeps the rest of the recipe, and a medium written out in full does not.

The three results are three different states. `nan` means that the LP had no solution, `0.0000` means that it was solved with an optimum of zero, and `0.8370` means that it was solved and the model grows. `slim_optimize` returns `nan` in the first case and does not raise. `model.optimize().status` shows the cause of an unexpected number.
:::
::::

## Anaerobic growth and conditions

An anaerobic yeast-GEM needs more than a closed oxygen exchange. Without oxygen the model cannot make sterols and unsaturated fatty acids, so they are supplied. Heme a leaves the cofactor pseudoreaction, the biomass gains an FADH2 term, and two reactions that glucose represses are blocked. These edits belong together, and both toolboxes read them from one YAML file, a condition, which is reviewed as data.

[`anaerobic.yml`](../data/anaerobic.yml) is that file, transcribed from `anaerobicModel.m` of yeast-GEM, without its step for the amino-acid ratios:

```yaml title="anaerobic.yml (abridged)"
cofactor_pseudoreaction:
  rxn_id: r_4598
  remove_mets:
    - { met: s_3714 }        # heme a
  charge_balance_met: s_0794 # H+

biomass_stoichiometry_delta:
  rxn_id: r_4041             # biomass pseudoreaction
  add:
    - { met: s_0689, coef:  0.08 }   # FADH2
    - { met: s_0687, coef: -0.08 }   # FAD
    - { met: s_0794, coef: -0.16 }   # H+

bounds:
  - { rxn: r_1992, lb: 0 }         # no oxygen
  - { rxn: r_1757, lb: -1000 }     # ergosterol, supplied
  - { rxn: r_2189, lb: -1000 }     # oleate, supplied
  - { rxn: r_1967, lb: -1000 }     # nicotinate
  - { rxn: r_0714, lb: 0, ub: 0 }  # MDH2, repressed on glucose
```

The schema has five parts: an optional `prelude` that resets the exchange reactions, an optional edit of the cofactor pseudoreaction, an optional change of the biomass stoichiometry, a list of `bounds` per reaction and an `expected_uptake_count`, which triggers a warning when it differs from the number of `bounds` entries with a lower bound of -1000.

Removing a metabolite from the cofactor pseudoreaction leaves its charge unbalanced, and `charge_balance_met` names the metabolite whose coefficient absorbs the difference. Both toolboxes recompute the coefficient and do not store it, so the file states the intent.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
modelAnaerobic = applyCondition(model, 'anaerobic.yml');
sol = solveLP(modelAnaerobic);
fprintf('anaerobic growth: %.4f /h\n', sol.f);
```

```text
anaerobic growth: 0.1615 /h
```

`applyCondition` reads the file with `parseYAML`, a YAML reader written in MATLAB.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.conditions import apply_condition, load_condition

condition = load_condition("anaerobic.yml")
print("bounds changed:", len(condition["bounds"]))

anaerobic = apply_condition(model.copy(), condition)
print(f"anaerobic growth: {anaerobic.slim_optimize():.4f} /h")
```

```text
bounds changed: 12
anaerobic growth: 0.1615 /h
```

`apply_condition` edits the model in place and returns it, so a copy should be passed when the aerobic model is needed. It also accepts the path: `apply_condition(model, "anaerobic.yml")`. `load_condition` parses the file without applying it, which allows a condition to be inspected or edited before it is applied.

The growth rate of 0.1615 /h compares with the 0.8370 /h that the same model reached aerobically in [Defining a whole medium](#defining-a-whole-medium). Both are on 10 mmol glucose, because the condition is applied to the model as that section left it. Fermentation yields much less ATP per glucose than respiration, and the ratio of the two growth rates is the comparison.
:::
::::

## Minimal medium

A medium copied from a paper often contains more than the model needs. `getMinimalMedium` and `minimal_medium` of cobrapy search for the smallest set of uptakes that supports a given growth rate. The result shows which components are necessary, and it shows a nutrient that the model does not need because a gap-filled reaction produces it internally.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
% getMinimalMedium solves a MILP: GLPK warns and solves it, setRavenSolver('gurobi') is faster
sol = solveLP(model);
medium = getMinimalMedium(model, 'minGrowth', 0.9 * sol.f);
```

```text
[Warning: Solving a MILP with GLPK. This works for small problems, but for larger problems Gurobi is much faster and more reliable; select it with setRavenSolver('gurobi'). Silence this warning with warning('off','RAVEN:glpkMILP').]

==============================================================
  Minimal medium  (14 of 16 candidate uptake reactions)
  Target growth: 0.7533
--------------------------------------------------------------
  r_1654                ammonium exchange
  r_1714                D-glucose exchange
  r_1861                iron(2+) exchange
  r_1992                oxygen exchange
  r_2005                phosphate exchange
  r_2020                potassium exchange
  r_2049                sodium exchange
  r_2060                sulphate exchange
  r_4593                chloride exchange
  r_4594                Cu2(+) exchange
  r_4595                Mn(2+) exchange
  r_4596                Zn(2+) exchange
  r_4597                Mg(2+) exchange
  r_4600                Ca(2+) exchange
==============================================================
```

The candidates are the exchange reactions with `lb < 0`, so a nutrient that the model cannot take up is never proposed. `minGrowth` defaults to 10 % of the optimum under the current bounds, a limit loose enough that most components drop out, and it is set explicitly when the question concerns a given growth rate. `verbose` set to `false` suppresses the table and returns the identifiers.

Of the 16 open uptakes, 14 are kept. Water and H+ are dropped because other reactions supply them. `getMinimalMedium` solves a mixed-integer linear programme (MILP) that minimises the number of open uptakes. The GLPK that ships with RAVEN solves it as well, with a warning that recommends Gurobi. `minimal_medium` of cobrapy solves by default an LP that minimises the summed uptake flux (in mmol/gDW/h, all metabolites weighted equally), so it returns rates.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.medium import minimal_medium

minimal = minimal_medium(model, model.slim_optimize() * 0.9)
print(minimal.round(3).to_string())
```

```text
r_1654     4.959
r_1714     9.004
r_1861     0.000
r_1992    20.139
r_2005     0.210
r_2020     0.003
r_2049     0.003
r_2060     0.105
r_4593     0.001
r_4594     0.000
r_4595     0.002
r_4596     0.001
r_4597     0.001
r_4600     0.000
```

The values are uptake rates. A zero is a component that the solution needs at a rate below the printed precision and is no component that the solution does without. `minimize_components=True` solves the MILP for the number of components, which also runs on GLPK. It returns the import fluxes of one feasible solution, which define the medium, and the rates are not minimal. Values close to the solver tolerance count as zero, and with Gurobi the answer for this model contains a heme a uptake of 1e-6. An integer value returns alternative media as columns.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- The model is infeasible after setting a medium. An essential nutrient is closed. The components should be reopened one at a time, or `minimal_medium` run on the working model and compared.
- The signs of two conventions are mixed. For an exchange written `metabolite <=>`, as in yeast-GEM, uptake is a negative flux, and `model.medium` takes positive numbers. Both are correct, and mixing them gives wrong bounds.
- The model grows without a carbon source. A reaction usually produces carbon from nothing. [Quality control](quality-control.md) describes the diagnosis with `canExchange` and `gap_report`.
- A result cannot be reproduced. A medium defined inside a script differs between users who edit the script. A condition file is data, and a text difference shows its changes.
:::

## See also

- [Simulating growth with FBA](fba.md): the solve that uses the medium.
- [Reading and writing models](io.md): keeping a model and its conditions in a repository.
- [MATLAB vs Python](../matlab-vs-python.md): the full function mapping.
