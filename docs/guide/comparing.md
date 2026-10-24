# 21. Comparing models

Curation produces several versions of one model: a draft and a curated
version, the model before and after gap-filling, a local build and a
published one. Two
different questions follow: **what changed** (an exact, entry-by-entry diff)
and **how alike are these** (an overview across whole sets). The first is for
review and for CI; the second is for deciding whether two models are describing
the same organism at all.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `diffModels` | `diff_models` | every semantic difference between two models |
| `compareMultipleModels` | `compare_models` | overlap in reactions, metabolites, genes, across two or more models |
| `compareFluxes` | `compare_fluxes` | which fluxes changed between two solutions of the same model |

## Setup

`smallYeast.yml` and `smallYeastBad.yml`: the same model, one of them carrying
deliberate errors. Comparing them is the exercise this page exists for.

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

## 21.1 What exactly is different?

`diffModels` matches by identifier and compares what it finds: stoichiometry,
bounds, objective coefficients, gene rules, formulas, charges. It answers a yes
or no question first (are these the same model?) and then says why not.

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

This is the comparison to put in a test. `DiffReport` is falsy when the models
differ, so `assert diff_models(before, after)` is a working regression test for a
curation script, and in MATLAB, `report.equal` does the same job.

## 21.2 How alike are they?

The other question is coarser: across the whole reaction set, how much do two
models overlap? `compare_models` builds a presence matrix, one row per
identifier, one column per model, and reduces it to a Jaccard similarity.
`compareMultipleModels` takes two models or twenty and reports the overlap on
seven identity notions at once (reactions, metabolites, genes, EC numbers,
metabolite names, equations with and without compartments), plus a similarity
matrix. Pass `'printResults', true` for the full breakdown on screen.

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

:::{warning} A high similarity does not mean the models agree
These two models are **0.945** alike on the reaction set, and one of them is
broken. The differences 21.1 lists are a doubled stoichiometric coefficient
and a reaction made irreversible, changes that alter what the model
*predicts* while barely moving a set-overlap score. Similarity is for
grouping models, not for validating one.
:::

## 21.3 Compare what they do, not what they contain

Two models with the same reactions can behave differently, and two models with
different reactions can behave identically. What settles it is a simulation of
both under the same constraints: growth first, then flux ranges or tasks, not a
single flux vector, which is one optimum among many (see
[18. Flux variability](fva.md)).

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

The errors in `smallYeastBad` are not cosmetic. On the same medium, with the same
objective, the good model grows and **the bad one does not grow at all**, from a
model that a set-overlap score called 94.5 % similar. A diff tells you the models
differ; only a simulation tells you what effect the difference has on growth.
(MATLAB reports
that zero as `-0.0000`; the minus sign is a formatting artefact of a zero
objective, not a negative growth rate.)

RAVEN can also run this comparison for you. `compareMultipleModels` takes
`funcCompare` and a `taskFile`, and then compares the models by which
metabolic tasks each one passes rather than by which reactions each one has.
That is the same shift from contents to behaviour made by hand above, and
[15. Metabolic tasks](tasks.md) is where the task file comes from.
`groupVector` labels the models, by tissue or by condition, so the similarity
matrix is reported per group.

The two tabs also show what `compareMultipleModels` and `compare_models`
count differently. RAVEN's matrix has one row per *combination of models*,
in-first-only, in-second-only, in-both, with `nElements` counting each;
raven-toolbox's has one row per *identifier* with a column per model. Both
answer the same question, but you index them in opposite directions.

:::{warning} What can go wrong
- **Comparing on identifiers alone.** Both functions match by id. Two models
  from different databases share few ids and will look unrelated even when
  they describe the same metabolism; see
  [20. Combining and simplifying](combining.md), where merging matches on
  names instead.
- **Reading similarity as quality.** It measures overlap, not correctness.
- **Comparing one flux vector per model.** An FBA solution is one of many
  optima, so two models, or two solvers on one model, can return different
  vectors with the same growth. Check that both solves succeeded and compare
  growth first, then ranges or tasks. `compareFluxes` and `compare_fluxes`
  compare two solutions of one model, so they need every reaction in both.
- **Forgetting the medium.** A flux comparison compares conditions as much as
  models. Set the same bounds on both, explicitly, before drawing any
  conclusion.
- **Diffing a model against a reloaded copy of itself.** Writing and reading
  a model can change formatting, ordering and rounding; a diff that reports
  differences after a round trip may be telling you about the file format;
  see [3. Reading and writing models](io.md).
:::

## See also

- [9. Quality control](quality-control.md), checking one model rather than two.
- [20. Combining and simplifying](combining.md), putting models together, and
  what has to line up first.
- [4. Simulating growth with FBA](fba.md), the simulation a flux comparison
  rests on.
