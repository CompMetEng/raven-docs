# 18. Flux variability and alternative optima

An FBA solution is one point in a space of equally optimal answers. Flux
variability asks the more accurate question: **given the objective, how much can
each reaction's flux still vary?** It is how you distinguish a flux the model
requires from one it merely happened to report.

### Functions on this page

| MATLAB | Python | |
|---|---|---|
| `getAllowedBounds` | `flux_variability_analysis` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the range each reaction can take |
| `haveFlux` | `find_blocked_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | reactions that can carry no flux at all |
| `solveLP` (`minFlux`) | `pfba` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | one representative optimum |
| no equivalent | `loopless_solution` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | an optimum without thermodynamically infeasible loops |
| no equivalent | `add_loopless` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the constraints behind `loopless="fastSNP"` |
| no equivalent | `find_good_reactions` | reactions whose range is real rather than a loop |

## Setup

`smallYeast.yml`, growing on glucose and oxygen. Uptake here is a **positive**
flux through a `=> metabolite` reaction, so it is the upper bound that opens it.

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

## 18.1 The range of every reaction

With no further constraint, this asks how far each flux can move anywhere in the
feasible space; the objective is free.

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

`getAllowedBounds` solves two LPs per reaction, one minimising and one
maximising, and runs them in parallel, so the first call in a session opens
a parallel pool and reports how many workers it got. Pass
`'runParallel', false` to keep it in the one process, which is quicker on a
model this size and the only option without the Parallel Computing Toolbox.
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

`fraction_of_optimum=0.0` is what makes this the same question
`getAllowedBounds` asks. Leave it out and cobrapy defaults to **1.0**, which
asks a different question; see the next section.
:::
::::

## 18.2 The range *at* the optimum

The useful question for interpreting a result: holding growth at its maximum,
which fluxes are still free to move, and how many come free again if growth only
has to reach 90 % of it?

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

RAVEN has no `fraction_of_optimum` argument: constrain the objective
reaction yourself, then ask for the bounds. A lower bound is a floor, not a
fixed value, so `0.9 * sol.f` lets growth sit anywhere from 90 % of the optimum
up to the optimum itself.
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

At the optimum only `FRDS2` and `SDH` can still move (18.3 shows why); everything
else is determined. Let growth drop to 90 % and only `ethIN`, which is closed,
stays fixed: a 10 % margin frees nearly every flux.

Reactions whose span collapses to zero at the optimum are the ones the model has
no choice about. Those are the predictions the model determines; a flux with a
wide range at the optimum is an artefact of which vertex the solver happened to
land on.

## 18.3 A wide range is not always a real one

A reaction can show a wide range purely because it is part of a thermodynamically
infeasible cycle, flux going round a loop with no net driving force. The widest
span in 18.1 was 1000, the model's default bound. That span is such a cycle.

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

**RAVEN has no loopless FVA.** The practical check is the one above: shut one
reaction of a suspected cycle and see whether anything downstream moves.
Growth is untouched, so those 1000 units of flux were never doing any work.
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

Both tabs reach the same number by different routes: shutting one arm of the
cycle, and adding loopless constraints, each cut the widest range in the model
from 1000 to **4**. `FRDS2` and `SDH` catalyse the same interconversion in
opposite directions.
Together they form a cycle that can carry arbitrary flux while consuming and
producing nothing, which is why the pair reaches the default bound of 1000 and
why the model's largest reported range is an artefact of stoichiometry rather
than a statement about the organism.

The `loopless` argument names the algorithm that forbids the cycle. `"fastSNP"`
adds loopless constraints to the model and gives optimal bounds;
`"cycleFreeFlux"` removes loops from each solution instead, which is quicker but
is not guaranteed to find the tightest bounds. `loopless=True` still works and
means `"cycleFreeFlux"`, but it is deprecated; name the algorithm.
`find_good_reactions` uses the same idea to decide which reactions are worth
sampling over, keeping a reaction only if its **loopless** range is non-trivial.

## 18.4 One representative solution

When a single flux distribution is needed (for a figure, or to compare two
conditions), take a parsimonious one rather than whatever the solver returns
first. It carries no loop flux and is less arbitrary than the first vertex
found, but it need not be unique either: where two routes cost the same total
flux, pFBA can return either. Report any single flux together with its range.

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

`minFlux` minimises total absolute flux subject to the objective, which is
parsimonious FBA. It is also the closest RAVEN gets to excluding loops: a
cycle adds flux, so a parsimonious solution has no reason to carry one.
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

All three agree here: this particular optimum happens to carry no loop flux,
even though 18.3 showed the cycle is there. Nothing guaranteed that: the
solver could as easily have returned a vertex with 1000 units going round
`FRDS2` and `SDH`, which is exactly the failure `loopless_solution` exists to
prevent.
:::
::::

:::{warning} What can go wrong
- **Forgetting `fraction_of_optimum`.** cobrapy defaults to `1.0`, ranges at
  the optimum. `getAllowedBounds` has no such notion and answers for the whole
  feasible space. The same call in the two toolboxes therefore asks different
  questions unless you say which one you mean.
- **Reporting a flux with a wide range.** If the range at the optimum is wide,
  the number in your table is one of many equally good answers.
- **Mistaking a loop for capacity.** Wide ranges on internal cycles are a
  property of the stoichiometry, not of the organism; see 18.3.
- **Loopless FVA is a MILP.** `loopless="fastSNP"` adds binary variables, so it is
  far slower than plain FVA and wants a good solver on anything larger than
  a toy model.
- **FVA on a genome-scale model.** Two LPs per reaction. cobrapy parallelises
  it, which is why `processes` matters; where spawning is blocked, set
  `Configuration().processes = 1` and expect it to take longer.
:::

## See also

- [4. Simulating growth with FBA](fba.md), the single solve this qualifies.
- [16. Deletions and essentiality](deletions.md), the other way to ask what the
  model depends on.
- [9. Quality control](quality-control.md), blocked reactions, the degenerate
  case of a zero range.
