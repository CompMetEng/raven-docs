# 4. Simulating growth with FBA

Set an objective, constrain the uptake rates, solve, and read the fluxes back.
This is the loop every other analysis on this site is built from.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `setParam` | `Reaction.bounds`, `Model.objective` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | set bounds and the objective |
| `solveLP` | `Model.optimize` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve the LP |
| `printFluxes` | `Model.summary` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | show the fluxes that carry material |
| `solveLP` (`minFlux`) | `pfba` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | pick a parsimonious solution among the optima |

:::{admonition} Where the Python functions come from
:class: info
Every simulation step on this page is cobrapy, marked
{bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` in the table above. In MATLAB,
`solveLP` needs neither the COBRA Toolbox nor anything else outside RAVEN.
:::

## Setup

`yeast-GEM.yml` from [`docs/data/`](../data/README.md), yeast-GEM v9.1.0, which
arrives with a growth objective and an aerobic glucose medium already set.

## 4.1 Solve

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

The objective is `model.c`, a vector with one entry per reaction, so
`model.c == 1` finds the reaction being maximised.

`sol` carries the whole answer. `sol.f` is the objective value with its
natural sign: RAVEN minimises internally and negates the result, so no sign
has to be undone by the caller. `sol.x` is the flux vector, in the order of
`model.rxns`, and `sol.stat` reports how the solve ended:

| `stat` | Meaning |
|---|---|
| `1` | solved to optimality |
| `0` | a feasible solution was found, but not proven optimal |
| `-1` | no feasible solution exists |
| `-2` | solved, but the flux minimisation in 4.6 failed |

Anything other than `1` makes the fluxes provisional at best, so check `stat`
before reading `x`. A plain solve (`minFlux` left at its default) also returns
`sol.sPrice` and `sol.rCost`, the shadow prices and reduced costs from the
LP dual.
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

`optimize` maximises by default and returns a `Solution` whose `fluxes` is a
pandas Series indexed by reaction id.

The objective prints as a difference of two terms because cobrapy gives every
reaction a forward and a reverse variable, both non-negative, and reports the
net flux as forward minus reverse. The suffix on the reverse variable is a
hash, so it differs between models. Only the expression is split; `r_2111`
remains one reaction, and `solution.fluxes['r_2111']` is the net value.
:::
::::

## 4.2 Change the objective

The objective is a reaction to maximise: growth, a product exchange, an ATP
demand.

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

`setParam` writes the coefficient into `model.c` and zeroes every other
entry, so setting an objective replaces the previous one rather than adding
to it. A negative coefficient minimises that reaction instead.
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

Assigning a reaction or its id replaces the objective. `model.objective` also
accepts an expression, so a weighted combination of reactions is written
directly, and `model.objective_direction` switches between maximising and
minimising.
:::
::::

## 4.3 Constrain an uptake rate

yeast-GEM writes its exchange reactions as `metabolite <=>`, so uptake is a
**negative** flux and the lower bound is what limits it. A model that writes
uptake as `=> metabolite`, like smallYeast in [6. Solvers](solvers.md), has the
opposite sign. yeast-GEM ships with glucose capped at 1 mmol/gDW/h, which is
where the growth rate above comes from; ten times the glucose gives roughly ten
times the growth.

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

The upper bound of `1000` on the same reaction is the model's convention for
"unbounded", and it allows secretion of glucose, which nothing in the model will
choose to do. Bounds are a pair, and only the one facing the direction of
interest constrains the answer. [5. Growth media and conditions](media.md) sets
all of them at once, and covers the opposite sign convention that
`model.medium` uses.

## 4.4 Try something without keeping it

A knockout or a tighter bound is usually a question, not a decision. cobrapy's
model is a context manager: changes made inside `with model:` are rolled back on
the way out. MATLAB has no equivalent; copy the struct, change the copy, and let
it go out of scope.

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

`'eq'` sets both bounds at once, so a single call closes the reaction in both
directions. MATLAB structs are value types, so `modelKO` is a copy from the
moment it is assigned and `model` cannot be reached through it.
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

Without `with`, the bound change would persist and every later result on this
page would be an anaerobic one. The block undoes the edits cobrapy records:
bounds, the objective, reactions and metabolites added or removed,
stoichiometry changed with `add_metabolites`, gene rules and gene knockouts.
Plain attribute edits are not recorded and survive the block: names, formulas,
charges, `subsystem`, the model id and anything written into `annotation` or
`notes`. Make those on `model.copy()`.

Two things in that output need care. The anaerobic growth rate is **zero**,
not a smaller positive number: closing the oxygen exchange is not enough to
make yeast-GEM grow fermentatively; it also needs sterol and fatty-acid
uptake and a different biomass composition, which is what a *condition* does.
See [Growth media and conditions](media.md). And the minus sign on that zero
is solver noise, not a negative growth rate; compare against a tolerance
rather than to `0`.
:::
::::

## 4.5 Look at the fluxes

An FBA solution has thousands of numbers, most of them zero and most of the rest
uninteresting. Both toolboxes offer a filtered view.

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

`printFluxes(model, sol.x)` does the same filtering without a list of ids:
by default it prints every exchange reaction carrying more than `1e-8`. Its
`cutOffFlux` raises that floor, `onlyExchange` set to `false` includes
internal reactions, `metaboliteList` restricts the print-out to reactions
touching named metabolites, and `outputString` controls the columns, with
`%eqn`, `%lower` and `%upper` available alongside `%flux`.
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

`model.summary()` prints the same picture (uptake, secretion and the
objective) as a table, and `solution.fluxes` is a pandas Series, so ordinary
filtering works: `solution.fluxes[solution.fluxes.abs() > 1e-6]`.
:::
::::

In yeast-GEM's orientation the signs say which way material moves: negative
through an exchange is uptake, positive is secretion. Glucose and oxygen enter, CO2 leaves, and ethanol is zero
because the model has enough oxygen to respire everything it takes up.

## 4.6 Pick a parsimonious solution

An FBA optimum is rarely unique: many flux distributions reach the same growth
rate, and a plain solve returns an arbitrary one, often with internal loops that
carry flux without contributing to the objective. Parsimonious FBA keeps the
objective at its optimum and then minimises the total flux, on the reasoning that
a cell does not run reactions it gains nothing from.

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

`minFlux` selects the second optimisation. `1` minimises the sum of absolute
fluxes, which requires one further LP. `3`
minimises the *number* of active reactions instead, which is a
mixed-integer problem: the result is easier to read as a pathway, and the
solve is far slower. Leaving `minFlux` at `0` skips the second solve
altogether and is the only setting that reports shadow prices.
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

`pfba` is the equivalent of `minFlux` set to `1`. It takes
`fraction_of_optimum`, which relaxes the objective before minimising flux, so
`0.95` asks for the leanest distribution that still reaches 95% of the
optimum.

The growth rate is unchanged and the total flux is now the smallest that
achieves it. The *number* of active reactions still varies between solves;
pFBA pins the total flux, not which reactions carry it, so a test on that
count will be flaky.
:::
::::

:::{warning} What can go wrong
- **The status is `infeasible`.** Something is over-constrained, most often
  an uptake that is closed, or a bound set to the wrong sign. See
  [Growth media and conditions](media.md).
- **Growth is zero but the solve succeeded.** The model is feasible and the
  optimum really is zero: a nutrient is missing, or a gap blocks the biomass
  pseudoreaction.
- **The same model gives different flux distributions.** Expected:
  alternative optima. Use pFBA, or compare ranges with FVA, rather than one
  solution.
- **Reading `sol.f` as a negated objective.** RAVEN minimises `-c'x`
  internally and negates the result before returning, so `sol.f` is the
  growth rate, not its negative.
- **A model whose coefficients span many orders of magnitude.** Ill-scaled
  stoichiometry makes the solver report an optimum that shifts between
  solvers. `solveLP` takes `params.maxRatio`, which splits any reaction whose
  coefficients span more than that ratio through auxiliary metabolites before
  solving, leaving the feasible region unchanged.
:::

## See also

- [Getting started](getting-started.md), loading and inspecting a model.
- [Growth media and conditions](media.md), what the exchange bounds mean and how
  to define a medium.
- [MATLAB vs Python](../raven3-vs-raven-toolbox.md), the full function mapping.
