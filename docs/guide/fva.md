# Flux variability and alternative optima

A flux balance analysis (FBA) solution is one point in a space of equally optimal solutions. Flux variability analysis (FVA) determines how far the flux of each reaction can vary within the feasible space, optionally with the objective held at a fraction of its optimum. It separates a flux that the model requires from a flux that the solver happened to return.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getAllowedBounds` | `flux_variability_analysis` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the range of each reaction |
| `haveFlux` | `find_blocked_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | reactions that cannot carry any flux |
| `solveLP` (`minFlux`) | `pfba` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | one representative optimum |
| no equivalent | `loopless_solution` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | an optimum without thermodynamically infeasible loops |
| no equivalent | `add_loopless` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the constraints behind `loopless="fastSNP"` |
| no equivalent | `find_good_reactions` | reactions whose range does not come from a loop |

## Setup

The model is `smallYeast.yml`, growing on glucose and oxygen. Uptake in this model is a positive flux through a `=> metabolite` reaction, and the upper bound opens it.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', 'biomassOUT', 1);
sol = solveLP(model);
fprintf('growth: %.4f /h\n', sol.f);
```

```text
growth: 0.1222 /h
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
model.reactions.get_by_id("glcIN").upper_bound = 1.0
model.reactions.get_by_id("o2IN").upper_bound = 1000.0
model.objective = "biomassOUT"
print(f"growth: {model.slim_optimize():.4f} /h")
```

```text
growth: 0.1222 /h
```
:::
::::

## Range of every reaction

Without further constraints, the analysis determines how far each flux can move anywhere in the feasible space, and the objective is free.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[minFluxes, maxFluxes] = getAllowedBounds(model);
span = full(maxFluxes - minFluxes);
fprintf('%d reactions, %d fixed, widest span %.1f\n', ...
    numel(span), sum(span < 1e-9), max(span));
```

```text
53 reactions, 1 fixed, widest span 1000.0
```

`getAllowedBounds` solves two linear programmes (LPs) per reaction, one that minimises and one that maximises, and runs them in parallel. The first call in a session therefore opens a parallel pool and reports the number of workers. `'runParallel', false` keeps the calculation in one process, which is quicker for a model of this size and the sole option without the Parallel Computing Toolbox.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import flux_variability_analysis

ranges = flux_variability_analysis(model, fraction_of_optimum=0.0)
span = ranges.maximum - ranges.minimum
print(f"{len(span)} reactions, {(span < 1e-9).sum()} fixed, "
      f"widest span {span.max():.1f}")
```

```text
53 reactions, 1 fixed, widest span 1000.0
```

`fraction_of_optimum=0.0` gives the question that `getAllowedBounds` answers. The default of cobrapy is 1.0, which asks a different question ([Range at the optimum](#range-at-the-optimum)).
:::
::::

## Range at the optimum

With the growth at its maximum, the analysis determines which fluxes can move. It also determines how many fluxes are free again when growth has to reach 90 % of the maximum.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
for fraction = [1 0.9]
    floored = setParam(model, 'lb', 'biomassOUT', fraction * sol.f);
    [minFluxes, maxFluxes] = getAllowedBounds(floored);
    span = full(maxFluxes - minFluxes);
    fprintf('growth >= %.0f%% of optimum: %d reactions fixed\n', 100 * fraction, sum(span < 1e-9));
end
```

```text
growth >= 100% of optimum: 51 reactions fixed
growth >= 90% of optimum: 1 reactions fixed
```

RAVEN has no `fraction_of_optimum` argument. The objective reaction is constrained first, and the bounds are requested afterwards. A lower bound is a floor, so `0.9 * sol.f` allows any growth from 90 % of the optimum up to the optimum.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
for fraction in (1.0, 0.9):
    ranges = flux_variability_analysis(model, fraction_of_optimum=fraction)
    span = ranges.maximum - ranges.minimum
    print(f"growth >= {fraction:.0%} of optimum: {(span < 1e-9).sum()} reactions fixed")
```

```text
growth >= 100% of optimum: 51 reactions fixed
growth >= 90% of optimum: 1 reactions fixed
```
:::
::::

At the optimum, `FRDS2` and `SDH` are the sole fluxes that can move ([Loops in flux ranges](#loops-in-flux-ranges)), and every other flux is determined. When growth may drop to 90 %, `ethIN` is the sole flux that stays fixed, and it is closed. A margin of 10 % frees nearly every flux.

A reaction with a span of zero at the optimum is a reaction for which the model has no choice, so these fluxes are the predictions that the model determines. A flux with a wide range at the optimum depends on the vertex that the solver returned.

## Loops in flux ranges

A reaction can show a wide range because it is part of a thermodynamically infeasible cycle, a flux that goes around a loop with no net driving force. The widest span in [Range of every reaction](#range-of-every-reaction) was 1000, the default bound of the model, and it is such a cycle.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[minFluxes, maxFluxes] = getAllowedBounds(model);
span = full(maxFluxes - minFluxes);
[~, order] = sort(span, 'descend');
fprintf('widest: %s (%.1f) and %s (%.1f)\n', ...
    model.rxns{order(1)}, span(order(1)), model.rxns{order(2)}, span(order(2)));

% break the cycle: hold one of the pair shut, then ask again
noLoop = setParam(model, 'eq', 'FRDS2', 0);
solNoLoop = solveLP(noLoop);
[minB, maxB] = getAllowedBounds(noLoop);
fprintf('with FRDS2 shut: growth %.4f /h, widest span %.1f\n', ...
    solNoLoop.f, max(full(maxB - minB)));
```

```text
widest: FRDS2 (1000.0) and SDH (1000.0)
with FRDS2 shut: growth 0.1222 /h, widest span 4.0
```

RAVEN has no loopless FVA. The check is to close one reaction of a suspected cycle and to see whether anything downstream moves. Growth does not change, so the 1000 units of flux do no work.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
plain_ranges = flux_variability_analysis(model, fraction_of_optimum=0.0)
loopless_ranges = flux_variability_analysis(
    model, fraction_of_optimum=0.0, loopless="fastSNP")

plain_span = plain_ranges.maximum - plain_ranges.minimum
loop_span = loopless_ranges.maximum - loopless_ranges.minimum
print(f"widest span: plain {plain_span.max():.1f}, "
      f"loopless {loop_span.max():.1f}")
print(f"inflated by loops: {sorted(plain_span[(plain_span - loop_span) > 1.0].index)}")
```

```text
widest span: plain 1000.0, loopless 4.0
inflated by loops: ['FRDS2', 'SDH']
```
:::
::::

The two methods give the same number. Closing one arm of the cycle and adding loopless constraints each reduce the widest range in the model from 1000 to 4. `FRDS2` and `SDH` catalyse the same interconversion in opposite directions. Together they form a cycle that carries any flux while it consumes and produces nothing. The pair therefore reaches the default bound of 1000, and the largest range of the model follows from the stoichiometry and does not describe the organism.

The `loopless` argument names the algorithm that forbids the cycle. `"fastSNP"` adds loopless constraints to the model and gives optimal bounds. `"cycleFreeFlux"` removes loops from each solution, which is faster and does not guarantee the tightest bounds. `loopless=True` works and means `"cycleFreeFlux"`, and it is deprecated, so the algorithm is named. `find_good_reactions` applies the same idea to select the reactions for sampling and keeps a reaction when its loopless range is not trivial.

## Representative solution

A single flux distribution is needed for a figure or for a comparison of two conditions. It is taken from parsimonious FBA (pFBA). The pFBA solution carries no loop flux and is less arbitrary than the first vertex that is found, and it need not be unique: when two pathways cost the same total flux, pFBA can return either. A single flux is reported together with its range.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
solPars = solveLP(model, 'minFlux', 1);
idx = getIndexes(model, 'biomassOUT', 'rxns');
fprintf('growth: %.4f /h, total flux: %.1f\n', solPars.x(idx), sum(abs(solPars.x)));
```

```text
growth: 0.1222 /h, total flux: 20.9
```

`minFlux` minimises the total absolute flux subject to the objective, which is parsimonious FBA. It is also the closest option in RAVEN to excluding loops, because a cycle adds flux and a parsimonious solution has no reason to carry one.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import loopless_solution, pfba

print(f"plain     {model.optimize().fluxes.abs().sum():.1f}")
print(f"loopless  {loopless_solution(model).fluxes.abs().sum():.1f}")
print(f"pFBA      {pfba(model).fluxes.abs().sum():.1f}")
```

```text
plain     20.9
loopless  20.9
pFBA      20.9
```

All three methods agree here, because this optimum carries no loop flux, although [Loops in flux ranges](#loops-in-flux-ranges) showed that the cycle exists. This was not guaranteed: the solver could have returned a vertex with 1000 units around `FRDS2` and `SDH`, which `loopless_solution` prevents.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- `fraction_of_optimum` is not set. cobrapy defaults to `1.0` and returns the ranges at the optimum, and `getAllowedBounds` answers for the whole feasible space. The same call in the two toolboxes asks different questions unless the call states which one is meant.
- A flux with a wide range is reported. When the range at the optimum is wide, the number in a results table is one of many equally good solutions.
- A loop is mistaken for capacity. Wide ranges on internal cycles follow from the stoichiometry and do not describe the organism ([Loops in flux ranges](#loops-in-flux-ranges)).
- Loopless FVA is a mixed-integer linear programme (MILP). `loopless="fastSNP"` adds binary variables, so it is much slower than plain FVA and needs a good solver for anything larger than a small model.
- FVA on a genome-scale model needs two LPs per reaction. cobrapy parallelises it, so `processes` matters. Where spawning processes is blocked, set `Configuration().processes = 1`, and the run takes longer.
:::

## See also

- [Simulating growth with FBA](fba.md): the single solve that FVA qualifies.
- [Deletions and essentiality](deletions.md): the other way to ask what the model depends on.
- [Quality control](quality-control.md): blocked reactions, the case of a range of zero.
