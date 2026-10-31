# Combining and simplifying models

Merging and simplifying are two operations that look like simple bookkeeping but carry real risk. **Merging** puts models together: a draft and a template, two organisms, a curated core and an extension. The result is only as sound as the assumption that a metabolite in one model is the same molecule as in the other. **Simplifying** takes a model apart, dropping what cannot carry flux, and the risk is deleting something that was needed.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `mergeModels` | `merge_models` | combine models into one |
| `contractModel` | `remove_duplicate_reactions` | collapse identical reactions |
| `simplifyModel` | `simplify_model` | drop what cannot carry flux |
| `expandModel` | `expand_model` | split reactions with `or` in the GPR |
| `mergeCompartments` | `merge_compartments` | collapse the model to one compartment |

## Setup

`smallYeast.yml`, and a second model to merge it with. Taking a copy and giving it a new id makes the comparison unambiguous: whatever the merge does to two identical models shows what it matches on.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
second = model;
second.id = 'second';
fprintf('%d rxns, %d mets, %d genes\n', ...
    numel(model.rxns), numel(model.mets), numel(model.genes));
```

```text
53 rxns, 52 mets, 61 genes
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from raven_toolbox.io import read_yaml_model

cobra.Configuration().processes = 1

model = read_yaml_model("smallYeast.yml")
second = model.copy()
second.id = "second"
print(f"{len(model.reactions)} rxns, {len(model.metabolites)} mets, "
      f"{len(model.genes)} genes")
```

```text
53 rxns, 52 mets, 61 genes
```
:::
::::

## Merging

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
merged = mergeModels({model, second});
fprintf('merged: %d rxns, %d mets, %d genes\n', ...
    numel(merged.rxns), numel(merged.mets), numel(merged.genes));
```

```text
[Warning: The following reaction IDs in second are already present in the model and were renamed: Old: acOUT New: acOUT_second Old: biomassOUT New: biomassOUT_second Old: co2OUT New: co2OUT_second Old: ethOUT New: ethOUT_second Old: glyOUT New: glyOUT_second Old: glcIN New: glcIN_second Old: o2IN New: o2IN_second Old: ethIN New: ethIN_second Old: HXK New: HXK_second ...and 44 more]

merged: 106 rxns, 52 mets, 61 genes
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import merge_models

merged = merge_models([model, second])
print(f"merged: {len(merged.reactions)} rxns, "
      f"{len(merged.metabolites)} mets, {len(merged.genes)} genes")
```

```text
merged: 106 rxns, 52 mets, 61 genes
```
:::
::::

The reactions double and the metabolites do not: two models that describe the same 52 metabolites end up sharing them, while every reaction is carried over from both sources and kept.

The asymmetry follows from the matching rules. Metabolites are matched on name and compartment (`metaboliteName[comp]`, not the identifier) and genes on name, so anything the two models call by the same name becomes one entity. Reactions are matched on nothing: every one is carried over, and the warning reports this. An id that exists in both models gets the source model's id appended (`HXK` and `HXK_second`), which keeps the identifiers unique; the two reactions are not reconciled. Python renames the same way, without a warning.

`mergeModels` takes `metParam` to choose what metabolites are matched on: `"metNames"`, the default used in the example, or `"mets"` to match on identifier. Matching on id is the right choice when both models come from the same database, where the ids mean the same thing and the names may not.

:::{admonition} Merging matches on names, not identifiers
:class: warning

Two models built from different databases usually share almost no metabolite names either, in which case merging produces a model with two disconnected halves in the same struct. Merging assumes that the naming is consistent; check the naming before merging.
:::

## Contraction and simplification

Merging does not de-duplicate. Every reaction from both models is kept, so the merged model describes each conversion twice. Collapsing those is a separate step.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
contracted = contractModel(merged);
fprintf('after contracting: %d rxns\n', numel(contracted.rxns));
```

```text
after contracting: 53 rxns
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import remove_duplicate_reactions

remove_duplicate_reactions(merged)
print(f"after contracting: {len(merged.reactions)} rxns")
```

```text
after contracting: 53 rxns
```
:::
::::

`simplifyModel` does little unless the flags say what to remove: every flag is off by default except `deleteUnconstrained`. `deleteMinMax` is the expensive one used in the example, minimising and maximising each reaction to find out whether it can carry flux; `deleteInaccessible` drops dead ends structurally, `deleteZeroInterval` drops reactions pinned to zero, and `deleteDuplicates` does what `contractModel` does. `reservedRxns` protects reactions from all of them. In Python the same choices are `delete_no_flux` and its siblings, with `open_exchanges` deciding whether the test runs on the medium as it stands or with the boundary opened first.

:::{admonition} Which functions mutate
:class: warning

Every RAVEN function here returns a new model struct and leaves its input unchanged. The Python functions differ:

| Python | Behaviour |
|---|---|
| `remove_duplicate_reactions`, `simplify_model` | change the model in place, return `None` |
| `merge_models`, `merge_compartments` | return a new model |

`model = simplify_model(model)` is correct MATLAB and sets `model` to `None` in Python. Copy the model first to keep the original.
:::

## Dropping what cannot carry flux

`smallYeast` ships with its medium shut, so almost nothing in it can carry flux, the state [Quality control](quality-control.md) measures. That makes it a subject for simplification and an illustration of its hazard.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
shut = readYAMLmodel('smallYeast.yml');
fprintf('%d of %d reactions can carry flux\n', ...
    sum(haveFlux(shut)), numel(shut.rxns));
reduced = simplifyModel(shut, 'deleteMinMax', true);   % test each reaction by LP
fprintf('simplified: %d rxns, %d mets\n', numel(reduced.rxns), numel(reduced.mets));
```

```text
2 of 53 reactions can carry flux
simplified: 2 rxns, 4 mets
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import simplify_model

shut = read_yaml_model("smallYeast.yml")
reduced = shut.copy()
simplify_model(reduced, delete_no_flux=True, open_exchanges=False)
print(f"simplified: {len(reduced.reactions)} rxns, "
      f"{len(reduced.metabolites)} mets")
```

```text
simplified: 2 rxns, 4 mets
```
:::
::::

A model that has been simplified against a shut medium is a model of that medium, not of the organism. Open the conditions to be simulated before simplifying, otherwise the pathways to be studied are deleted; see [Growth media and conditions](media.md).

## Collapsing compartments

Sometimes the compartments are the problem: a draft with unreliable localisation, or a comparison against a model that has none.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[flat, deletedRxns] = mergeCompartments(model);
fprintf('%d compartments -> %d, %d -> %d mets, %d -> %d rxns\n', ...
    numel(model.comps), numel(flat.comps), ...
    numel(model.mets), numel(flat.mets), numel(model.rxns), numel(flat.rxns));
fprintf('%d transport reactions dropped\n', numel(deletedRxns));
```

```text
2 compartments -> 1, 52 -> 45 mets, 53 -> 50 rxns
0 transport reactions dropped
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import merge_compartments

flat, dropped, _ = merge_compartments(model)
print(f"{len(model.compartments)} compartments -> {len(flat.compartments)}, "
      f"{len(model.metabolites)} -> {len(flat.metabolites)} mets, "
      f"{len(model.reactions)} -> {len(flat.reactions)} rxns")
print(f"{len(dropped)} transport reactions dropped")
```

```text
2 compartments -> 1, 52 -> 45 mets, 53 -> 50 rxns
3 transport reactions dropped
```
:::
::::

Seven metabolites in this model exist in both compartments, so 52 collapse to 45; the three reactions that moved something across the mitochondrial membrane become `A -> A`, carry no information, and are dropped.

The merged metabolite is one of its copies, with every field of that copy (id, name, formula, charge, annotation); raven-toolbox also adds `notes["merged_base_id"]`. The copy is the one in the merged compartment if there is one, otherwise the copy whose id sorts first (`ACCOA_c` before `ACCOA_m`). The id can therefore name a compartment that is not in the merged model.

The two toolboxes count the removals differently. Both end at 50 reactions, but the second line disagrees: RAVEN reports 0 dropped where raven-toolbox reports 3 (`CAT2`, `CO2TRANS`, `ShuttleX`). The same three reactions go in both cases. RAVEN clears them when it removes reactions the merge left empty, and its `deletedRxns` counts only what the `deleteRxnsWithOneMet` path deleted, which is nothing, since that flag is `false` by default.

A reaction that holds a single metabolite after merging is kept or removed by the `deleteRxnsWithOneMet` flag in MATLAB and by `drop_single_metabolite_reactions` in Python, which is `false` or `False` by default in both. An exchange has one metabolite by design (`=> glucose`) and is kept whatever the flag is, so the boundary reactions and the objective survive.

Collapsing compartments discards information. A model that distinguishes mitochondrial from cytosolic acetyl-CoA cannot be recovered from the flattened one, and the flattened model permits a pathway to run on a pool that no membrane separates. Flatten a copy, for a specific question, and keep the original.

:::{admonition} Troubleshooting
:class: warning

- Merging on inconsistent names. The match is on name and compartment. Different naming conventions give two disconnected networks in one model, and the merge raises no error; MATLAB only warns about the metabolite ids it renames.
- Expecting de-duplication. Merging keeps every reaction from every source. Contract afterwards, and check what got collapsed.
- Simplifying against the wrong condition. Reactions are removed because they cannot carry flux under the current bounds. Change the medium first.
- In place or a copy. The Python functions mutate; the MATLAB ones return. Mixing the conventions discards either the original or the result.
- `deleteUnconstrained` has no Python counterpart. RAVEN models mark boundary metabolites with an `unconstrained` field; cobra models use explicit boundary reactions, and that flag has nothing to act on.
:::

## See also

- [Quality control](quality-control.md), deciding what should be removed.
- [Gap-filling](gap-filling.md), the opposite operation, and the usual reason for having a template model to merge from.
- [Context-specific models](init.md), cutting a model down by evidence, not by connectivity.
