# Combining and simplifying models

Merging and simplifying look like bookkeeping and carry risk. Merging puts models together, such as a draft and a template, two organisms, or a curated core and an extension. The result is sound if a metabolite in one model is the same molecule as the metabolite of that name in the other. Simplifying takes a model apart and drops what cannot carry flux, and its risk is the deletion of something that is needed.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `mergeModels` | `merge_models` | combine models into one |
| `contractModel` | `remove_duplicate_reactions` | collapse identical reactions |
| `simplifyModel` | `simplify_model` | drop what cannot carry flux |
| `expandModel` | `expand_model` | split reactions with `or` in the gene rule |
| `mergeCompartments` | `merge_compartments` | collapse the model to one compartment |

## Setup

The examples use `smallYeast.yml` and a second model to merge it with. The second model is a copy with a new identifier. The merge of two identical models then shows what the merge matches on.

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

The number of reactions doubles and the number of metabolites does not. The two models describe the same 52 metabolites, which the merged model shares, and every reaction of both sources is carried over.

The asymmetry follows from the matching rules. Metabolites are matched by name and compartment (`metaboliteName[comp]`) and genes by name, so anything that the two models call by the same name becomes one entity. Reactions are matched on nothing, and the warning reports this. An identifier that exists in both models receives the identifier of the source model as a suffix (`HXK` and `HXK_second`), which keeps the identifiers unique, and the two reactions are not reconciled. Python renames in the same way and gives no warning.

`mergeModels` takes `metParam`, which selects what metabolites are matched on. The value `"metNames"` is the default and is used in the example, and `"mets"` matches on identifier. Matching on identifier suits two models from the same database, where the identifiers have the same meaning and the names may differ.

:::{admonition} Name-based merging
:class: warning

Two models built from different databases usually share almost no metabolite names either. The merge then gives a model with two disconnected halves in one struct. Merging assumes consistent naming, and the naming should be checked before the merge.
:::

## Contraction and simplification

Merging does not remove duplicates. Every reaction of both models is kept, so the merged model describes each conversion twice. Collapsing them is a separate step.

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

`simplifyModel` removes nothing unless the flags say what to remove, as every flag is off by default except `deleteUnconstrained`. `deleteMinMax` is the expensive flag used in the example. It minimises and maximises each reaction to find out whether the reaction can carry flux. `deleteInaccessible` drops dead ends structurally, `deleteZeroInterval` drops reactions that are fixed at zero, and `deleteDuplicates` does what `contractModel` does. `reservedRxns` protects reactions from `deleteZeroInterval`, `deleteInaccessible` and `deleteMinMax`. In Python, the same choices are `delete_no_flux` and its related arguments. `open_exchanges` decides whether the test runs on the medium as it is or with the boundary opened first.

:::{admonition} Functions that change the model in place
:class: warning

Every RAVEN function here returns a new model struct and leaves its input unchanged. The Python functions differ:

| Python | Behaviour |
|---|---|
| `remove_duplicate_reactions`, `simplify_model` | change the model in place and return `None` |
| `merge_models`, `merge_compartments` | return a new model |

`model = simplify_model(model)` is correct in MATLAB and sets `model` to `None` in Python. The model should be copied first when the original is needed.
:::

## Dropping what cannot carry flux

`smallYeast` ships with a shut medium, so almost nothing in it can carry flux, which is the state that [Quality control](quality-control.md) measures. This makes it a subject for simplification and shows its hazard.

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

A model that is simplified against a shut medium describes that medium. The conditions to be simulated should be opened before simplifying, because the pathways of interest are otherwise deleted ([Growth media and conditions](media.md)).

## Collapsing compartments

Collapsing compartments applies to a draft with unreliable localisation and to a comparison with a model that has no compartments.

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

Seven metabolites of this model exist in both compartments, so 52 metabolites collapse to 45. The three reactions that moved a metabolite across the mitochondrial membrane become `A -> A`, carry no information and are dropped.

The merged metabolite is one of its copies, with all fields of that copy (identifier, name, formula, charge, annotation), and raven-toolbox also adds `notes["merged_base_id"]`. The copy is the one in the merged compartment if there is one, and otherwise the copy whose identifier sorts first (`ACCOA_c` before `ACCOA_m`). The identifier can therefore name a compartment that the merged model does not contain.

The two toolboxes count the removals differently. Both end at 50 reactions, and the second line differs: RAVEN reports 0 dropped reactions and raven-toolbox reports 3 (`CAT2`, `CO2TRANS`, `ShuttleX`). The same three reactions go in both cases. RAVEN clears them when it removes the reactions that the merge left empty, and its `deletedRxns` counts the deletions of the `deleteRxnsWithOneMet` path alone, which are none because that flag is `false` by default.

A reaction with a single metabolite after the merge is kept or removed by the flag `deleteRxnsWithOneMet` in MATLAB and by `drop_single_metabolite_reactions` in Python, which is `false` or `False` by default in both. An exchange reaction has one metabolite by design (`=> glucose`) and is kept whatever the flag is, so the boundary reactions and the objective remain.

Collapsing compartments discards information. A model that distinguishes mitochondrial from cytosolic acetyl-CoA cannot be recovered from the flattened model, and the flattened model allows a pathway to run on a pool that no membrane separates. A copy is flattened for a specific question, and the original is kept.

:::{admonition} Troubleshooting
:class: warning

- The names are inconsistent. The match uses name and compartment. Different naming conventions give two disconnected networks in one model without an error, and MATLAB warns about the metabolite identifiers that it renames.
- Duplicates are expected to disappear. Merging keeps every reaction of every source. Contract the model afterwards and check the collapsed reactions.
- The model is simplified against the wrong condition. Reactions are removed because they cannot carry flux under the current bounds, so the medium is changed first.
- The function works in place or returns a copy. The Python functions mutate, and the MATLAB functions return a new struct. Mixing the conventions discards either the original or the result.
- `deleteUnconstrained` has no Python counterpart. RAVEN models mark boundary metabolites with an `unconstrained` field, and cobra models use explicit boundary reactions, so the flag has nothing to act on.
:::

## See also

- [Quality control](quality-control.md): deciding what should be removed.
- [Gap-filling](gap-filling.md): the opposite operation, and the usual reason for a template model to merge from.
- [Context-specific models](init.md): reducing a model by evidence.
