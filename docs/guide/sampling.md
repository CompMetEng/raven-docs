# Random sampling

Flux variability gives the extremes that a reaction can reach. Sampling draws many flux vectors from the feasible space and gives the distribution between the extremes, which is how the vectors are spread. A range of 0 to 10 does not show whether the flux is mostly 0, mostly 10 or evenly spread, and a sample does.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `randomSampling` | `random_sampling` | sample the flux space |
| `sampleACHR` | `random_sampling` (`method='achr'`) | hit-and-run Markov chain Monte Carlo (MCMC), the default |
| `sampleCHRR` | `random_sampling` (`method='chrr'`) | hit-and-run with rounding, for thin polytopes |
| no equivalent | `find_good_reactions` | reactions usable as random objectives |
| `getAllowedBounds` | `flux_variability_analysis` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | the ranges that sampling fills in |

## Setup

The model is the glucose-limited `smallYeast.yml` of [Flux variability](fva.md), so the two pages can be compared.

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

Both toolboxes take a `seed`. A seed is set in every run, because a chain without a seed differs in every run and a result cannot be reproduced.

A seed does not guarantee identical numbers. The default `achr` sampler starts from warmup points that come from LPs, two per reaction. A different solver, solver version or platform returns different warmup vertices, and so does a solve of the same model before the sampling when GLPK is used, because it leaves a different starting basis. The same seed then explores the same distribution along a different chain. With seed 1, MATLAB gives a sampled minimum of `FRDS2` of 18.8 with GLPK and of 4.5 with Gurobi. The sampled values in the examples are printed with few decimals, because the distribution is the result and the single draws are not.

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

RAVEN returns reactions by samples. raven-toolbox returns a DataFrame of samples by reactions, which is the layout of `cobra.sampling`. Every mean, histogram and correlation must use the correct axis, because a wrong axis raises no error and gives other numbers than intended.
:::

## Distribution and range

[Flux variability](fva.md) showed that `FRDS2` and `SDH` have the widest range in this model, 1000 units, and that all of it comes from a thermodynamically infeasible cycle. Sampling does not remove the cycle and shows the share of the space that it occupies.

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

The two implementations are separate and use separate random number generators, so their numbers do not match draw by draw. They describe the same distribution, and the agreement of the distributions is the check.

`FRDS2` is sampled across nearly its whole range of 1000 units, so the loop forms most of the space and most draws fall in it. Growth shows the opposite. Its range runs from 0 to 0.1222, and the samples fall between about 0.01 and 0.1 with a mean of about 0.05. Near-uniform sampling almost never reaches a vertex, and the optimum is a corner without volume around it.

A sampled mean describes the shape of the feasible space and does not predict anything. The mean sampled growth of this model is less than half of its optimum, and biology does not cause the difference.

## Choosing a method

`achr` and `chrr` both draw the near-uniform interior distribution. `randomObjective` (`random_objective` in Python) maximises a small random objective each time, so it returns vertices, while the samples of `achr` and `chrr` are interior points. FBA also gives vertices, so this method surveys alternative optima and does not describe the space.

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

The dimension is a property of the polytope. It is the number of degrees of freedom of the network after the implicitly determined reactions are eliminated. A model with 53 reactions has far fewer than 53, and the two toolboxes, which implement CHRR separately, both compute 9.

`MVE converged: False` is a warning. MVE is the maximum-volume ellipsoid that is used for the rounding. The rounding stopped before it reached its tolerance. The last ellipsoid is a valid rounding and the samples are usable. On a polytope this elongated, mixing is slower than the defaults assume, and more thinning helps when the distribution is uneven.

## Sampling a constrained state

Sampling an unconstrained model answers what the network could do, which is rarely the question. The model should be constrained first, by holding growth near its optimum or by fixing a measured flux, and the remaining space is sampled.

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
ethanol: free 0.73, growth >= 90% 0.03
```
:::
::::

## Reactions to sample over

The `randomObjective` method needs reactions that carry flux outside loops, as objectives. Reactions that carry flux through a loop alone are unsuitable, and the two toolboxes screen them out differently. raven-toolbox runs a loopless FVA, the test that [Flux variability](fva.md) applied by hand. RAVEN runs a plain FVA (`getAllowedBounds`) and drops the reactions that reach 0.999 times the upper bound of the loop (1000 in this model), which is where loop flux ends up. Both keep the same 50 reactions here.

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

The list passed back as `good_reactions=` on a later call skips the FVA, which is the expensive part of the run on a genome-scale model.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- No seed is set. The numbers change in every run. Set a seed and report it together with the solver, because the warmup points come from LPs and another solver gives another chain, as does a solve of the same model before the sampling with GLPK ([First sample](#first-sample)). The distribution is reported.
- Thinning is too small. Consecutive MCMC steps are correlated, so every 100th step is recorded. This suffices for this model and falls short for a genome-scale model. On yeast-GEM, samples 100 steps apart have a correlation of 0.93, and independent chains disagree on most reactions ([Flux sampling convergence and settings](../parameter-tuning/studies/sampling-convergence-calibration.md)). Reported results need chains with different seeds that agree.
- A mean is read as a prediction. The mean of a sample describes the feasible space and the sampler. It is a feasible state located where most of the volume is, which puts the mean growth below half of the optimum in [Distribution and range](#distribution-and-range). With `randomObjective` the samples are vertices, and a reaction can average 5 while every sample has it at 0 or 10.
- A model with a wide-open medium is sampled. With an unconstrained medium the space is enormous and the distribution says nothing, so constrain the model first.
- Loops are present. They inflate the sampled space, and every sample drawn inside a cycle is wasted ([Flux variability](fva.md)).
- The runtime on a genome-scale model is long. `achr` starts with two LPs per reaction for its warmup points, and `chrr` starts with an FVA and a rounding step. The sampling steps after that solve no LP. `randomObjective` solves one LP per sample. A few hundred samples show the shape, and tens of thousands are not needed for that.
:::

## See also

- [Flux variability](fva.md): the ranges that sampling fills in.
- [Simulating growth with FBA](fba.md): the single point that sampling surrounds.
- [Deletions and essentiality](deletions.md): the other way to ask what the model depends on.
