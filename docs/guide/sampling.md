# Random sampling

Flux variability gives the extremes a reaction can reach. Sampling draws many flux vectors from the feasible space and gives the **distribution** in between: how the vectors are spread. A range of 0–10 does not say whether the flux is usually 0, usually 10 or evenly spread; a sample does.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `randomSampling` | `random_sampling` | sample the flux space |
| `sampleACHR` | `random_sampling` (`method='achr'`) | hit-and-run Markov chain Monte Carlo (MCMC), the default |
| `sampleCHRR` | `random_sampling` (`method='chrr'`) | hit-and-run with rounding, for thin polytopes |
| no equivalent | `find_good_reactions` | reactions usable as random objectives |
| `getAllowedBounds` | `flux_variability_analysis` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the ranges sampling fills in |

## Setup

The model is the glucose-limited `smallYeast.yml` of [Flux variability](fva.md), so the two pages can be read against each other.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', 'biomassOUT', 1);
```

```text
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from raven_toolbox.io import read_yaml_model

cobra.Configuration().processes = 1

model = read_yaml_model("smallYeast.yml")
model.reactions.get_by_id("glcIN").upper_bound = 1.0
model.reactions.get_by_id("o2IN").upper_bound = 1000.0
model.objective = "biomassOUT"
```

```text
```
:::
::::

## First sample

Both toolboxes take a `seed`. A seed should always be set: without it a chain differs in every run and no reported result can be reproduced.

A seed does not guarantee identical numbers. The default `achr` sampler starts from warmup points, and those come from LPs: two per reaction. A different solver, solver version or platform, and with GLPK even a solve of the same model before the sampling (which leaves a different starting basis), returns different warmup vertices, so the same seed explores the same distribution along a different chain. With seed 1, MATLAB gives `FRDS2`'s sampled minimum as 18.8 with GLPK and as 4.5 with Gurobi. The sampled values in the examples are printed to few decimals, because the distribution is the result and the individual draws are not.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
solutions = randomSampling(model, 200, 'seed', 1);
fprintf('%d reactions x %d samples\n', size(solutions, 1), size(solutions, 2));
```

```text
53 reactions x 200 samples
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.analysis import random_sampling

result = random_sampling(model, 200, seed=1)
print(f"{result.samples.shape[0]} samples x {result.samples.shape[1]} reactions")
print(f"method: {result.method}")
```

```text
200 samples x 53 reactions
method: achr
```
:::
::::

:::{admonition} Transposed layouts
:class: warning

RAVEN returns reactions × samples; raven-toolbox returns a DataFrame of samples × reactions, the `cobra.sampling` layout. Every mean, histogram and correlation has to use the right axis, and a wrong axis gives no error, only numbers other than the intended ones.
:::

## Distribution and range

[Flux variability](fva.md) found that `FRDS2` and `SDH` have the widest range in this model, 1000 units, and that all of it is a thermodynamically infeasible cycle. Sampling does not remove the cycle; it shows the share of the space that the cycle occupies.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, {'FRDS2', 'biomassOUT'}, 'rxns');
fprintf('FRDS2  sampled %.0f to %.0f\n', ...
    min(solutions(idx(1), :)), max(solutions(idx(1), :)));
fprintf('growth sampled %.2f to %.2f, mean %.2f\n', ...
    min(solutions(idx(2), :)), max(solutions(idx(2), :)), mean(solutions(idx(2), :)));
```

```text
FRDS2  sampled 19 to 1000
growth sampled 0.01 to 0.10, mean 0.05
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
frds2 = result.samples["FRDS2"]
growth = result.samples["biomassOUT"]
print(f"FRDS2  sampled {frds2.min():.0f} to {frds2.max():.0f}")
print(f"growth sampled {growth.min():.2f} to {growth.max():.2f}, "
      f"mean {growth.mean():.2f}")
```

```text
FRDS2  sampled 1 to 998
growth sampled 0.01 to 0.09, mean 0.05
```
:::
::::

The two tabs are separate implementations with separate random number generators, so their numbers are not expected to match draw for draw. They describe the same distribution, and the agreement of the distributions is the check to make.

`FRDS2` is sampled across nearly its whole 1000-unit range, so the loop is most of the space, and most of the draws fall in it. Growth is the opposite. Its range runs from 0 to 0.1222, while the samples fall between about 0.01 and 0.1 and average about 0.05, because near-uniform sampling almost never reaches a vertex and the optimum is a corner with no volume around it.

A sampled mean describes the shape of the feasible space and is no prediction: the mean sampled growth of this model is less than half its optimum, and biology does not cause the difference.

## Choosing a method

`achr` and `chrr` both draw the near-uniform interior distribution. `randomObjective` (`random_objective` in Python) maximises a small random objective each time, so it returns vertices; the samples of `achr` and `chrr` are interior points. Vertices are what FBA gives, which makes that method a way to survey alternative optima, not to describe the space.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[chrrSolutions, ~, info] = randomSampling(model, 200, 'method', 'chrr', 'seed', 1);
fprintf('chrr: %d dimensions, MVE converged: %d, %d fixed\n', ...
    info.nDimensions, info.mveConverged, numel(info.fixedRxns));
```

```text
[Warning: The maximum-volume ellipsoid rounding did not converge; the samples may be poorly mixed. Inspect the mveConverged field of the second output.]
chrr: 9 dimensions, MVE converged: 0, 1 fixed
```

:::
:::{tab-item} 🐍 Python
:sync: python

```python
chrr = random_sampling(model, 200, method="chrr", seed=1)
print(f"chrr: {chrr.n_dimensions} dimensions, "
      f"MVE converged: {chrr.mve_converged}, "
      f"{len(chrr.fixed_reactions)} fixed")
```

```text
chrr: 9 dimensions, MVE converged: False, 1 fixed
```
:::
::::

The dimension is a property of the polytope, not of the sampler: it is how many degrees of freedom the network has once the implicitly determined reactions are eliminated. A model with 53 reactions has far fewer than 53, and the two toolboxes, which implement CHRR separately, both compute 9.

`MVE converged: False` is a warning, not a failure. MVE is the maximum-volume ellipsoid used for rounding. The rounding step stopped before reaching its tolerance, so the last ellipsoid is a valid rounding and the samples are usable, but on a polytope this elongated mixing is slower than the defaults assume, and more thinning helps if the distribution is uneven.

## Sampling a constrained state

Sampling an unconstrained model answers "what could this network do?", which is rarely the question of interest. Constrain first (hold growth near its optimum, fix a measured flux) and sample the space that is left.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
sol = solveLP(model);
floored = setParam(model, 'lb', 'biomassOUT', 0.9 * sol.f);
constrained = randomSampling(floored, 200, 'seed', 1);
ethIdx = getIndexes(model, 'ethOUT', 'rxns');
fprintf('ethanol: free %.2f, growth >= 90%% %.2f\n', ...
    mean(solutions(ethIdx, :)), mean(constrained(ethIdx, :)));
```

```text
ethanol: free 0.80, growth >= 90% 0.04
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
floored = model.copy()
floored.reactions.get_by_id("biomassOUT").lower_bound = 0.9 * model.slim_optimize()
constrained = random_sampling(floored, 200, seed=1)
print(f"ethanol: free {result.samples['ethOUT'].mean():.2f}, "
      f"growth >= 90% {constrained.samples['ethOUT'].mean():.2f}")
```

```text
ethanol: free 0.72, growth >= 90% 0.04
```
:::
::::

## Reactions to sample over

The `randomObjective` method needs reactions that can carry flux outside loops to use as objectives. Reactions that carry flux only through a loop are of no use as objectives, and the two toolboxes screen them out differently. raven-toolbox runs a loopless FVA, the test that [Flux variability](fva.md) applied manually. RAVEN runs a plain FVA (`getAllowedBounds`) and drops the reactions that reach 0.999 of the model's largest bound, which is where loop flux ends up. Here both keep the same 50.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[~, goodRxns] = randomSampling(model, 20, 'method', 'randomObjective', 'seed', 1);
fprintf('%d of %d reactions usable as objectives\n', numel(goodRxns), numel(model.rxns));
```

```text
50 of 53 reactions usable as objectives
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.analysis import find_good_reactions

good = find_good_reactions(model)
print(f"{len(good)} of {len(model.reactions)} reactions usable as objectives")
```

```text
50 of 53 reactions usable as objectives
```

Passing the list back as `good_reactions=` on a later call skips the FVA, the expensive part of the run on a genome-scale model.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- No seed. The numbers change in every run. Set one, and report it with the solver: the warmup points come from LPs, so another solver (or, with GLPK, a solve of the same model before the sampling) gives another chain (see [First sample](#first-sample)). Report the distribution, not the draws.
- Too little thinning. Consecutive MCMC steps are correlated, so only every 100th is recorded. That is enough for this model, not for a genome-scale one: on yeast-GEM, samples 100 steps apart are 0.93 correlated and independent chains disagree on most reactions (see the [sampling convergence study](../parameter-tuning/studies/sampling-convergence-calibration.md)). For results that are reported, run chains with different seeds and check that they agree.
- Reading a mean as a prediction. The mean of a sample describes the feasible space and the sampler, not the cell. It is a feasible state, but it is located where most of the volume is: in [Distribution and range](#distribution-and-range) that puts mean growth below half the optimum. With `randomObjective` the samples are vertices, so a reaction can average 5 while every sample has it at 0 or 10.
- Sampling a model that is wide open. With an unconstrained medium the space is enormous and the distribution says nothing. Constrain first.
- Loops. They inflate the space being sampled, and every sample drawn inside a cycle is wasted. See [Flux variability](fva.md).
- Genome-scale runtime. `achr` starts with two LPs per reaction for its warmup points and `chrr` with an FVA and a rounding step; the sampling steps after that solve no LP. `randomObjective` solves one LP per sample. Start with a few hundred samples to see the shape, not tens of thousands.
:::

## See also

- [Flux variability](fva.md), the ranges that sampling fills in.
- [Simulating growth with FBA](fba.md), the single point that sampling surrounds.
- [Deletions and essentiality](deletions.md), the other way to ask what the model depends on.
