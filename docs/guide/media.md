# Growth media and conditions

A flux balance analysis (FBA) result is a statement about a medium. The medium is set deliberately by choosing which exchange reactions are open and how wide, and a condition keeps a medium as reviewable data and not as a paragraph of bound-setting code.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getExchangeRxns` | `Model.exchanges` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | find the exchange reactions |
| `setExchangeBounds` | `Model.medium` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | set a whole medium, closing the rest |
| `setParam` | `set_reaction_bounds` | set one reaction's bounds |
| `getMinimalMedium` | `minimal_medium` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the smallest medium that still supports growth |
| `applyCondition` | `apply_condition`, `load_condition` | apply a condition file |

## Setup

The model is `yeast-GEM.yml` from [`docs/data/`](../data/README.md), which has an aerobic minimal glucose medium applied.

## Open exchanges

An exchange reaction connects a boundary metabolite to nothing, so its flux is the rate at which that metabolite enters or leaves the system. yeast-GEM writes its exchanges as `metabolite <=>`, so entering is a negative flux and leaving a positive one, and the medium is the set of exchanges with a negative lower bound. A model that writes uptake as `=> metabolite` has the opposite sign; see [Solvers](solvers.md).

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

`getExchangeRxns` identifies an exchange by its stoichiometry, as a reaction with no substrates or no products, so it does not depend on a naming convention. Its `reactionType` argument can return a subset chosen by bounds: `'uptake'`, `'excrete'`, `'reverse'` and `'blocked'` classify a reaction by what its bounds permit, while `'in'` and `'out'` classify by which side the boundary metabolite is on and ignore the bounds.

The hand-written filter in the code and `'uptake'` ask different questions. `'uptake'` returns reactions that can only take up; every open exchange in yeast-GEM also has an upper bound of 1000, so it can secrete as well and is classified `'reverse'`. Selecting on `model.lb < 0` is what "the medium" means here.
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

`model.medium` is a dict of `{exchange id: maximum uptake rate}`, given as a positive number; cobrapy flips the sign, so a medium entry of `1.0` means a lower bound of `-1.0`. It lists only the exchanges that are open, so the loop prints 16 rows out of 270 reactions.
:::
::::

The two toolboxes count exchange reactions differently, and both counts are correct. cobrapy sorts single-metabolite reactions into `exchanges`, `demands` and `sinks`; `getExchangeRxns` returns all of them together. In yeast-GEM the difference is three reactions: `r_2111` (growth) and the sinks `r_4062` and `r_4064`, so MATLAB reports 273 where `model.exchanges` reports 270.

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

`setParam` takes a reaction id, a list of ids, or indices, and applies one value to all of them or one value each. `'lb'`, `'ub'` and `'eq'` set bounds; `'obj'` sets the objective coefficient.
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

`reaction.bounds = (-10.0, 1000.0)` does the same thing for ordinary edits. `set_reaction_bounds` covers the case that cobrapy refuses: it writes the underlying attributes directly, so a condition can reach `lb > ub`, which cobrapy's own setter rejects as invalid. Conditions use that to force flux through a reaction with a sentinel bound.

`slim_optimize` returns the objective value alone, without building a full `Solution`, which is the cheaper call inside a loop over many bound settings.
:::
::::

## Defining a whole medium

Assigning to the medium replaces the whole medium: everything not in the dict is closed. That makes it the right tool for "this exact recipe and nothing else", and the wrong one for "the shipped medium, but with more glucose".

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

The first line prints no number. With every uptake closed the linear programme (LP) is infeasible, and `solveLP` returns `sol.f` as an empty array with `sol.stat` set to `-1`; `fprintf` prints nothing for an empty argument. Check `sol.stat`, not the value, as in [Simulating growth with FBA](fba.md).

`setExchangeBounds` is the closer counterpart to assigning `model.medium`. It addresses metabolites and not reaction ids, sets their exchange bounds, and with its default `closeOthers` shuts every other uptake, which is the replace-the-whole-recipe behaviour. `mediaOnly` restricts it to the extracellular compartment, so intracellular sink reactions are left alone.
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

Glucose and oxygen alone are not enough; yeast-GEM also needs nitrogen, phosphate, sulphate and a handful of ions. Building a medium from `dict(model.medium)` and editing individual entries therefore leaves the rest of the recipe intact, which writing it out in full does not.

The three results are three different states. `nan` means the LP had no solution; `0.0000` means it solved and the optimum is zero; `0.8370` means it solved and the model grows. `slim_optimize` returns `nan` for the first case and does not raise, so check `model.optimize().status` when a number is unexpected.
:::
::::

## Anaerobic growth and conditions

Switching yeast-GEM to anaerobic conditions takes more than closing the oxygen exchange. Without oxygen the model cannot make sterols or unsaturated fatty acids, so those have to be supplied; heme a leaves the cofactor pseudoreaction; the biomass gains an FADH2 term; and two reactions that are repressed on glucose are blocked. Those edits belong together, so both toolboxes read them from one YAML file (a **condition**), which can be reviewed as data and is not buried in a script.

[`anaerobic.yml`](../data/anaerobic.yml) is that file, transcribed from yeast-GEM's own `anaerobicModel.m`:

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

The schema is narrow on purpose: an optional `prelude` that resets the exchanges, an optional cofactor-pseudoreaction edit, an optional biomass-stoichiometry delta, a list of per-reaction `bounds`, and an `expected_uptake_count` that triggers a warning when the condition does not match the model.

Removing a metabolite from the cofactor pseudoreaction leaves it charge imbalanced, so `charge_balance_met` names the metabolite whose coefficient absorbs the difference. Both toolboxes recompute it and do not store the new value, so the file is readable as a statement of intent.

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

`apply_condition` edits the model in place and returns it, so pass a copy to keep the aerobic model as well. It also takes the path directly: `apply_condition(model, "anaerobic.yml")`. `load_condition` is the parse step on its own, for inspecting or editing a condition before applying it.

Compare 0.1615 /h with the 0.8370 /h that the same model reached aerobically in [Defining a whole medium](#defining-a-whole-medium): both are on 10 mmol glucose, because the condition is applied to the model as that section left it. Fermentation yields far less ATP per glucose than respiration; the ratio of the two growth rates is what the comparison is for.
:::
::::

## Minimal medium

A medium copied from a paper usually contains more than the model needs. `getMinimalMedium` and cobrapy's `minimal_medium` search for the smallest set of uptakes that supports a given growth rate, which identifies which component is necessary for growth, and finds a nutrient the model does not need because a gap-filled reaction produces it internally.

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

Candidates are the exchanges that have `lb < 0`; a nutrient the model cannot take up is never proposed. `minGrowth` defaults to 10 % of the optimum under the current bounds, which is loose enough that most components drop out, so state it explicitly, as here, when the question is about a particular growth rate. `verbose` set to `false` suppresses the table and returns the ids alone.

Of the 16 open uptakes, 14 are kept: water and H+ are dropped because other reactions supply them. `getMinimalMedium` solves a mixed-integer linear programme (MILP) that minimises the number of open uptakes. RAVEN's bundled GLPK solves it too, with a warning that recommends Gurobi. cobrapy's `minimal_medium` by default solves an LP that minimises the summed uptake flux (in mmol/gDW/h, all metabolites weighted equally), so it returns rates.
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

The values are uptake rates and not bounds, and the zeros are components that the solution needs at a rate below the printed precision, not components the solution does without. `minimize_components=True` solves the component-count MILP (it runs on GLPK too). It returns the import fluxes of one feasible solution, whose index is the medium; the rates are not minimal. Treat values near the solver tolerance as zero: with Gurobi, a heme a uptake of 1e-6 appears in this model's answer. An integer value returns alternative media as columns.
:::
::::

:::{warning} Troubleshooting
- `infeasible` right after setting a medium: something essential is closed. Reopen the medium one component at a time, or start from `minimal_medium` on the working model and compare.
- A sign error from mixing conventions: for an exchange written `metabolite <=>`, as in yeast-GEM, uptake is a negative flux, but `model.medium` takes positive numbers. Both are correct; mixing them is not.
- The model grows without a carbon source: usually a leak, where some reaction produces carbon from nothing. [Quality control](quality-control.md) covers the diagnosis, with `canExchange` and `analyse_topology`.
- Results that cannot be reproduced: if a medium is defined inside a script, the next person runs a different one. A condition file is data, and a diff shows its changes.
:::

## See also

- [Simulating growth with FBA](fba.md), the solve that uses the medium.
- [Reading and writing models](io.md), keeping a model and its conditions in a
  repository.
- [MATLAB vs Python](../raven3-vs-raven-toolbox.md), the full function mapping.
