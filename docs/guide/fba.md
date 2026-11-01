# Simulating growth with FBA

Flux balance analysis (FBA) sets an objective, limits the uptake rates, solves the linear program and reads the fluxes. The other analyses on this site repeat this sequence with changes.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `setParam` | `Reaction.bounds`, `Model.objective` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | set the bounds and the objective |
| `solveLP` | `Model.optimize` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve the linear program |
| `printFluxes` | `Model.summary` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | show the fluxes that carry material |
| `solveLP` (`minFlux`) | `pfba` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | select a parsimonious solution among the optima |

Every Python simulation step on this page comes from cobrapy and carries the {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` badge in the functions table. In MATLAB, `solveLP` does not need the COBRA Toolbox or any other package outside RAVEN.

## Setup

The model is `yeast-GEM.yml` from [`docs/data/`](../data/README.md), yeast-GEM v9.1.0, with a growth objective and an aerobic glucose medium.

## Solving

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('yeast-GEM.yml');
sol = solveLP(model);
fprintf('objective: %s\n', model.rxns{model.c == 1});
fprintf('status:    %d\n', sol.stat);
fprintf('growth:    %.4f /h\n', sol.f);
```

```text
objective: r_2111
status:    1
growth:    0.0809 /h
```

The objective is `model.c`, a vector with one entry per reaction, and `model.c == 1` finds the reaction that is maximised.

`sol` holds the result. `sol.f` is the objective value with its natural sign, because RAVEN minimises internally and negates the result before returning it. `sol.x` is the flux vector in the order of `model.rxns`. `sol.stat` reports how the solve ended:

| `stat` | Meaning |
|---|---|
| `1` | solved to optimality |
| `0` | a feasible solution was found without a proof of optimality |
| `-1` | no feasible solution exists |
| `-2` | solved, and the second optimisation requested by `minFlux` failed |

The fluxes are provisional for every value other than `1`, so `stat` should be checked before `x` is read. A solve with `minFlux` at its default also returns `sol.sPrice` and `sol.rCost`, the shadow prices and the reduced costs from the dual of the linear program.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("yeast-GEM.yml")
solution = model.optimize()

print(f"objective: {model.objective.expression}")
print(f"status:    {solution.status}")
print(f"growth:    {solution.objective_value:.4f} /h")
```

```text
objective: 1.0*r_2111 - 1.0*r_2111_reverse_58b69
status:    optimal
growth:    0.0809 /h
```

`optimize` maximises by default and returns a `Solution`, whose `fluxes` is a pandas Series indexed by reaction identifier.

The objective is printed as a difference of two terms, because cobrapy gives every reaction a forward and a reverse variable, both non-negative, and reports the net flux as forward minus reverse. The suffix of the reverse variable is a hash and differs between models. The expression is split, and the reaction is not. `r_2111` remains one reaction, and `solution.fluxes['r_2111']` is its net flux.
:::
::::

## Changing the objective

The objective is a reaction that is maximised, for example growth, a product exchange or an ATP demand.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = setParam(model, 'obj', 'r_2111', 1);   % growth
disp(model.rxnNames{getIndexes(model, 'r_2111', 'rxns')});
```

```text
growth
```

`setParam` writes the coefficient into `model.c` and sets every other entry to zero, so a new objective replaces the previous one. A negative coefficient minimises the reaction.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.objective = "r_2111"
print(model.reactions.get_by_id("r_2111").name)
```

```text
growth
```

Assigning a reaction or its identifier replaces the objective. `model.objective` also accepts an expression, which defines a weighted combination of reactions, and `model.objective_direction` switches between maximisation and minimisation.
:::
::::

## Limiting an uptake rate

yeast-GEM writes its exchange reactions as `metabolite <=>`, so uptake is a negative flux and the lower bound limits it. A model that writes uptake as `=> metabolite`, such as smallYeast in [Solvers](solvers.md), has the opposite sign. In yeast-GEM, glucose uptake is limited to 1 mmol/gDW/h, which sets the growth rate of the first solve. Ten times the glucose gives roughly ten times the growth.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, 'r_1714', 'rxns');     % D-glucose exchange
fprintf('shipped bounds: [%g %g]\n', model.lb(idx), model.ub(idx));

model = setParam(model, 'lb', 'r_1714', -10);
sol = solveLP(model);
fprintf('growth on 10 mmol glucose: %.4f /h\n', sol.f);

model = setParam(model, 'lb', 'r_1714', -1);   % back to the shipped medium
```

```text
shipped bounds: [-1 1000]
growth on 10 mmol glucose: 0.8370 /h
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
glucose = model.reactions.get_by_id("r_1714")
print("shipped bounds:", glucose.bounds)

glucose.lower_bound = -10.0
faster = model.optimize()
print(f"growth on 10 mmol glucose: {faster.objective_value:.4f} /h")

glucose.lower_bound = -1.0   # back to the shipped medium
```

```text
shipped bounds: (-1.0, 1000.0)
growth on 10 mmol glucose: 0.8370 /h
```
:::
::::

The upper bound of `1000` on the same reaction is the convention of the model for an unbounded flux, and it allows glucose secretion, which the model has no reason to use. A bound is one half of a pair, and the half that faces the direction of interest limits the result. [Growth media and conditions](media.md) sets all bounds of a medium at once and covers the opposite sign convention of `model.medium`.

## Temporary changes

A knockout or a tighter bound is usually tested and then discarded. The cobrapy model is a context manager, and the changes made inside `with model:` are undone when the block ends. MATLAB has no equivalent. The struct is copied, the copy is changed, and the copy is discarded.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
modelKO = setParam(model, 'eq', 'r_1992', 0);   % close oxygen uptake
solKO = solveLP(modelKO);
fprintf('anaerobic: %.4f /h\n', solKO.f);

% `model` itself is untouched -- MATLAB copied it on assignment
sol = solveLP(model);
fprintf('back to aerobic: %.4f /h\n', sol.f);
```

```text
anaerobic: 0.0000 /h
back to aerobic: 0.0809 /h
```

`'eq'` sets both bounds, so one call closes the reaction in both directions. MATLAB structs are value types, so `modelKO` is a copy from the assignment, and `model` cannot be reached through it.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
with model:
    model.reactions.get_by_id("r_1992").bounds = (0, 0)   # oxygen exchange
    print(f"anaerobic: {model.optimize().objective_value:.4f} /h")

print(f"back to aerobic: {model.optimize().objective_value:.4f} /h")
```

```text
anaerobic: -0.0000 /h
back to aerobic: 0.0809 /h
```

Without `with`, the bound change would remain, and every later result of the examples would be an anaerobic result. The block undoes the edits that cobrapy records: bounds, the objective, added or removed reactions and metabolites, stoichiometry changed with `add_metabolites`, gene rules and gene knockouts. Plain attribute edits are not recorded and remain after the block. These are names, formulas, charges, `subsystem`, the model identifier and the contents of `annotation` and `notes`. They are made on `model.copy()`.

The anaerobic growth rate is zero. A closed oxygen exchange does not make yeast-GEM grow by fermentation. Growth also needs the uptake of sterols and fatty acids and a different biomass composition, which a condition provides ([Growth media and conditions](media.md)). The minus sign on that zero is solver noise. A value is compared with a tolerance around `0`.
:::
::::

## Inspecting the fluxes

An FBA solution has thousands of fluxes, and most are zero. Both toolboxes show a filtered view.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
exchanges = {'r_1714', 'r_1992', 'r_1672', 'r_1761'};
labels = {'glucose', 'oxygen', 'CO2', 'ethanol'};
for i = 1:numel(exchanges)
    idx = getIndexes(model, exchanges{i}, 'rxns');
    fprintf('%8s: %9.4f\n', labels{i}, sol.x(idx));
end
```

```text
 glucose:   -1.0000
  oxygen:   -2.3592
     CO2:    2.6597
 ethanol:    0.0000
```

`printFluxes(model, sol.x)` filters without a list of identifiers. By default it prints every exchange reaction with an absolute flux of at least `1e-8`. `cutOffFlux` raises that limit, `onlyExchange` set to `false` includes internal reactions, and `metaboliteList` restricts the output to reactions with the named metabolites. `outputString` sets the columns, and `%eqn`, `%lower` and `%upper` are available next to `%flux`.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
solution = model.optimize()
exchanges = {
    "r_1714": "glucose",
    "r_1992": "oxygen",
    "r_1672": "CO2",
    "r_1761": "ethanol",
}
for rxn_id, label in exchanges.items():
    print(f"{label:>8}: {solution.fluxes[rxn_id]:9.4f}")
```

```text
 glucose:   -1.0000
  oxygen:   -2.3592
     CO2:    2.6597
 ethanol:    0.0000
```

`model.summary()` prints the same view of uptake, secretion and objective as a table. `solution.fluxes` is a pandas Series, so ordinary filtering applies: `solution.fluxes[solution.fluxes.abs() > 1e-6]`.
:::
::::

With the orientation of yeast-GEM, a negative flux through an exchange reaction is uptake and a positive flux is secretion. Glucose and oxygen enter and CO2 leaves. Ethanol is zero because the model has enough oxygen to respire all the glucose that it takes up.

## Parsimonious solution

An FBA optimum is rarely unique. Many flux distributions reach the same growth rate, and a plain solve returns an arbitrary one, which often contains internal loops that carry flux without contributing to the objective. Parsimonious FBA (pFBA) keeps the objective at its optimum and minimises the total flux, on the assumption that a cell does not run reactions that give it no gain.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
solPars = solveLP(model, 'minFlux', 1);   % minimise sum(abs(fluxes))
fprintf('growth:     %.4f /h\n', solPars.x(getIndexes(model, 'r_2111', 'rxns')));
fprintf('total flux: %.1f\n', sum(abs(solPars.x)));
```

```text
growth:     0.0809 /h
total flux: 100.6
```

`minFlux` selects the second optimisation. The value `1` minimises the sum of absolute fluxes and needs one further linear program. The value `3` minimises the number of active reactions, which is a mixed-integer problem. Its result is easier to read as a pathway, and the solve takes much longer. The value `0` skips the second solve and is the sole setting that reports shadow prices.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import pfba

parsimonious = pfba(model)
print(f"growth:     {parsimonious.fluxes['r_2111']:.4f} /h")
print(f"total flux: {parsimonious.fluxes.abs().sum():.1f}")
```

```text
growth:     0.0809 /h
total flux: 100.6
```

`pfba` corresponds to `minFlux` set to `1`. `fraction_of_optimum` relaxes the objective before the flux is minimised, so `0.95` gives the smallest total flux at 95 % of the optimum.

The growth rate does not change, and the total flux is the smallest that achieves it. The number of active reactions varies between solves, because pFBA fixes the total flux and leaves open which reactions carry it. A test on that number fails intermittently.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- The status is `infeasible`. A constraint is too tight, most often a closed uptake or a bound with the wrong sign. [Growth media and conditions](media.md) covers the media.
- The solve succeeds and growth is zero. The model is feasible and its optimum is zero, because a nutrient is missing or a gap blocks the biomass pseudoreaction.
- The same model gives different flux distributions. Alternative optima exist. pFBA selects one, and flux variability analysis (FVA) compares ranges of fluxes.
- `sol.f` is read as a negated objective. RAVEN minimises `-c'x` internally and negates the result before returning it, so `sol.f` is the growth rate itself.
- The coefficients of a model span many orders of magnitude. Badly scaled stoichiometry makes the optimum differ between solvers. `params.maxRatio` of `solveLP` splits every reaction whose coefficients span a larger ratio through auxiliary metabolites before solving, and the feasible region does not change.
:::

## See also

- [Getting started](getting-started.md): loading and inspecting a model.
- [Growth media and conditions](media.md): the meaning of the exchange bounds and the definition of a medium.
- [MATLAB vs Python](../matlab-vs-python.md): the full function mapping.
