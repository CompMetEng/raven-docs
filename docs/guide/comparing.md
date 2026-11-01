# Comparing models

Curation produces several versions of one model, such as a draft and a curated version, the model before and after gap-filling, or a local build and a published one. Two questions follow. What changed is answered by an exact entry-by-entry difference, which serves review and continuous integration (CI). How alike the models are is answered by an overview over whole sets, which serves to decide whether two models describe the same organism.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `diffModels` | `diff_models` | every semantic difference between two models |
| `compareMultipleModels` | `compare_models` | overlap in reactions, metabolites and genes across two or more models |
| `compareFluxes` | `compare_fluxes` | fluxes that changed between two solutions of the same model |

## Setup

The examples compare `smallYeast.yml` and `smallYeastBad.yml`, where the second file is a copy of the first with deliberate errors.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
good = readYAMLmodel('smallYeast.yml');
bad = readYAMLmodel('smallYeastBad.yml');
fprintf('good %d rxns, bad %d rxns\n', numel(good.rxns), numel(bad.rxns));
```

```text
good 53 rxns, bad 54 rxns
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from raven_toolbox.io import read_yaml_model

cobra.Configuration().processes = 1

good = read_yaml_model("smallYeast.yml")
bad = read_yaml_model("smallYeastBad.yml")
print(f"good {len(good.reactions)} rxns, bad {len(bad.reactions)} rxns")
```

```text
good 53 rxns, bad 54 rxns
```
:::
::::

## Entry-by-entry differences

`diffModels` matches entries by identifier and compares stoichiometry, bounds, objective coefficients, gene rules, formulas and charges. It first reports whether the models are the same and then lists the differences.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
report = diffModels(good, bad);
fprintf('equal: %d, %d differences\n', report.equal, numel(report.differences));
for i = 1:min(4, numel(report.differences))
    fprintf('  - %s\n', report.differences{i});
end
```

```text
equal: 0, 11 differences
  - 1 reactions only in A: ethIN
  - 2 reactions only in B: ADH2, PDC_2
  - ADH1: coef[ETH_c] A=1 B=2
  - ADH1: bounds A=[-1000,1000] B=[0,1000]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.comparison import diff_models

report = diff_models(good, bad)
print(f"equal: {report.equal}, {len(report.differences)} differences")
for d in report.differences[:4]:
    print(f"  - {d}")
```

```text
equal: False, 11 differences
  - reactions only in A (1): ['ethIN']
  - reactions only in B (2): ['ADH2', 'PDC_2']
  - ADH1: coef[ETH_c] A=1 B=2
  - ADH1: bounds A=(-1000.0, 1000.0) B=(0.0, 1000.0)
```
:::
::::

This comparison suits a test. `DiffReport` is falsy when the models differ, so `assert diff_models(before, after)` is a regression test for a curation script, and in MATLAB `report.equal` serves the same purpose.

## Similarity across models

The second question is coarser and concerns the overlap of two models over the whole reaction set. `compare_models` builds a presence matrix with one row per identifier and one column per model and reduces it to a Jaccard similarity. `compareMultipleModels` takes two or twenty models and reports the overlap for seven notions of identity (reactions, metabolites, genes, EC numbers, metabolite names, and equations with and without compartments) and a similarity matrix. `'printResults', true` prints the complete breakdown.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
good.id = 'smallYeast';
bad.id = 'smallYeastBad';
% compareMultipleModels narrates each stage as it goes, and its structural
% projection needs the Statistics and Machine Learning Toolbox, so what it
% prints depends on the machine. The counts do not: capture and drop it.
[~, compStruct] = evalc('compareMultipleModels({good, bad})');
inBoth = all(compStruct.rxns.comparison, 2);
fprintf('%d reactions shared of %d in the union\n', ...
    compStruct.rxns.nElements(inBoth), sum(compStruct.rxns.nElements));
```

```text
52 reactions shared of 55 in the union
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.comparison import compare_models

good.id, bad.id = "smallYeast", "smallYeastBad"
comparison = compare_models([good, bad])
shared = int((comparison.reactions.sum(axis=1) == 2).sum())
print(f"{shared} reactions shared of {len(comparison.reactions)} in the union")
print(f"similarity: {comparison.similarity.iloc[0, 1]:.3f}")
```

```text
52 reactions shared of 55 in the union
similarity: 0.945
```
:::
::::

:::{admonition} A high similarity does not mean that the models agree
:class: warning

The two models have a similarity of 0.945 on the reaction set, and one of them is broken. The differences in [Entry-by-entry differences](#entry-by-entry-differences) are a doubled stoichiometric coefficient and a reaction made irreversible. These changes alter the predictions of the model and hardly move a set-overlap score. Similarity serves to group models and does not validate one.
:::

## Comparison by behaviour

Two models with the same reactions can behave differently, and two models with different reactions can behave identically. A simulation of both under the same constraints decides. Growth is compared first, then flux ranges or tasks, and a single flux vector is not compared, because it is one optimum among many ([Flux variability and alternative optima](fva.md)).

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
openGood = setParam(good, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
openGood = setParam(openGood, 'obj', 'biomassOUT', 1);
openBad = setParam(bad, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
openBad = setParam(openBad, 'obj', 'biomassOUT', 1);
solGood = solveLP(openGood);
solBad = solveLP(openBad);
fprintf('growth: good %.4f, bad %.4f\n', solGood.f, solBad.f);
```

```text
growth: good 0.1222, bad -0.0000
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
for model in (good, bad):
    model.reactions.get_by_id("glcIN").upper_bound = 1.0
    model.reactions.get_by_id("o2IN").upper_bound = 1000.0
    model.objective = "biomassOUT"
print(f"growth: good {good.slim_optimize():.4f}, bad {bad.slim_optimize():.4f}")
```

```text
growth: good 0.1222, bad 0.0000
```
:::
::::

The errors in `smallYeastBad` change the prediction. On the same medium and with the same objective, the good model grows and the bad model does not grow at all, although a set-overlap score called them 94.5 % similar. A difference shows that the models differ, and a simulation shows the effect of the difference on growth. MATLAB reports the zero as `-0.0000`, and the minus sign is a formatting artefact of a zero objective.

RAVEN can run this comparison as well. `compareMultipleModels` takes `funcCompare` and a `taskFile` and compares the models by the metabolic tasks that each passes. This is the shift from content to behaviour that the examples make by hand. The task file is described in [Metabolic tasks](tasks.md). `groupVector` labels the models, for example by tissue or by condition, and the similarity matrix is then reported per group.

The two examples also show what `compareMultipleModels` and `compare_models` count differently. The matrix of RAVEN has one row per combination of models (in the first, in the second, in both) with `nElements` counting each. The matrix of raven-toolbox has one row per identifier and one column per model. Both answer the same question and are indexed in opposite directions.

:::{admonition} Troubleshooting
:class: warning

- Models are compared by identifier alone. Both functions match by identifier. Two models from different databases share few identifiers and look unrelated although they describe the same metabolism. [Combining and simplifying models](combining.md) merges by name instead.
- Similarity is read as quality. It measures overlap.
- One flux vector per model is compared. An FBA solution is one of many optima, so two models, or two solvers on one model, can return different vectors with the same growth. Check that both solves succeeded, and compare growth first, then ranges or tasks. `compareFluxes` and `compare_fluxes` compare two solutions of one model, so every reaction must be in both.
- The medium is forgotten. A flux comparison compares conditions as much as models. Set the same bounds explicitly on both models before drawing a conclusion.
- A model is compared with a reloaded copy of itself. Writing and reading a model can change formatting, order and rounding, and differences after a round trip can come from the file format ([Reading and writing models](io.md)).
:::

## See also

- [Quality control](quality-control.md): checking one model.
- [Combining and simplifying models](combining.md): putting models together and what must line up first.
- [Simulating growth with FBA](fba.md): the simulation that a flux comparison depends on.
