# Editing an existing model

Curation consists mostly of edits: a wrong stoichiometry, a superseded gene association or a reaction that does not belong in the model. Both toolboxes have a procedure for each of these edits.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `changeRxns` | `change_reaction_equations` | replace the stoichiometry of a reaction |
| `changeGrRules` | `change_gene_reaction_rules` | set or extend gene associations |
| `standardizeGrRules` | `gpr_to_dnf` | normalise a gene rule |
| `setParam` | `Reaction.bounds` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | change bounds and objective |
| `removeReactions` | `Model.remove_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | delete reactions |
| `removeMets` | `remove_metabolites` | delete metabolites |
| `removeGenes`, `deleteUnusedGenes` | `remove_genes` | delete genes |

## Setup

The model is `smallYeast.yml` from [`docs/data/`](../data/README.md).

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
```
:::
::::

## Fixing a stoichiometry

The whole equation is given. The toolbox rewrites the column of the reaction in the stoichiometric matrix, which keeps all fields consistent.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = changeRxns(model, {'PGI'}, {'G6P_c <=> F6P_c'});
idx = getIndexes(model, 'PGI', 'rxns');
eqn = constructEquations(model, model.rxns(idx));
fprintf('%s\n', eqn{1});
```

```text
alpha-D-glucose 6-phosphate[c] <=> beta-D-fructofuranose 6-phosphate[c]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import change_reaction_equations

change_reaction_equations(model, {"PGI": "G6P_c <=> F6P_c"})
print(model.reactions.get_by_id("PGI").reaction)
```

```text
G6P_c <=> F6P_c
```

`changeRxns` takes two matching lists of reactions and equations, and `change_reaction_equations` takes a mapping from reaction to equation. A batch of curated reactions, which is what a curation spreadsheet turns into, is therefore applied in one call. Every identifier must exist in the model, because these functions change reactions and do not add them.

The bounds are not changed. Rewriting an equation from `=>` to `<=>` does not make the reaction reversible, because `lb` and `ub` set the direction and the arrow does not. [Changing bounds and the objective](#changing-bounds-and-the-objective) sets them separately. `changeRxns` takes the options `eqnType`, `compartment` and `allowNewMets` of `addRxns`, and `change_reaction_equations` takes the options `mets_by`, `compartment`, `allow_new_mets` and `new_met_prefix` of `add_reactions_from_equations`. Both match metabolites by identifier by default. `allowNewMets` defaults to `false` and `allow_new_mets` to `True`.
:::
::::

## Changing a gene association

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = changeGrRules(model, {'PGI'}, {'YBR196C or YLR354C'});
disp(model.grRules{idx});
```

```text
YBR196C or YLR354C
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import change_gene_reaction_rules

change_gene_reaction_rules(model, {"PGI": "YBR196C or YLR354C"})
pgi = model.reactions.get_by_id("PGI")
print(pgi.gene_reaction_rule)
print("genes now:", sorted(gene.id for gene in pgi.genes))
```

```text
YBR196C or YLR354C
genes now: ['YBR196C', 'YLR354C']
```

A gene that is not in the model is created. `replace=False` appends an isozyme to the rule and gives `(old) or (new)`, which records an additional catalyst. The default overwrites the rule. A reaction without a rule receives the new rule alone, without empty brackets.
:::
::::

## Normalising a gene rule

Rules that mix `and` and `or` in nested brackets are difficult to compare and to score. Both toolboxes rewrite them in disjunctive normal form, a list of alternative complexes. `is_dnf` takes a rule string, and `gpr_to_dnf` takes the parsed `GPR` object of cobrapy and returns the complexes as lists.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
grRules = standardizeGrRules(model);
fprintf('%s\n', grRules{idx});
```

```text
YBR196C or YLR354C
```

`standardizeGrRules` returns the rules and a matching `rxnGeneMat` and no model, so the results are assigned back into the struct. Disjunctive normal form is a flat `or` of `and` groups, one group per alternative complex, which is the form that the scoring in [Context-specific models](init.md) expects.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.core.gene import GPR

from raven_toolbox.manipulation import gpr_to_dnf
from raven_toolbox.utils import is_dnf

rule = "YBR196C and (YLR354C or YGR192C)"
print("already DNF:", is_dnf(rule))
print(gpr_to_dnf(GPR.from_string(rule)))
```

```text
already DNF: False
[['YBR196C', 'YLR354C'], ['YBR196C', 'YGR192C']]
```
:::
::::

## Changing bounds and the objective

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = setParam(model, 'lb', 'PGI', 0);        % make it irreversible
model = setParam(model, 'obj', 'biomassOUT', 1);
fprintf('bounds: [%g %g]\n', model.lb(idx), model.ub(idx));
```

```text
bounds: [0 1000]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.reactions.get_by_id("PGI").bounds = (0, 1000)
model.objective = "biomassOUT"
print("bounds:", model.reactions.get_by_id("PGI").bounds)
```

```text
bounds: (0, 1000)
```

`setParam` takes `'lb'`, `'ub'`, `'eq'`, `'obj'`, `'rev'`, `'var'` and `'unc'`. It applies a list of values to a list of reactions, or one value to all, in a single call.
:::
::::

## Deleting metabolites, reactions and genes

The toolboxes differ most in deletion. RAVEN removes the matching row or column from every field, and deletion therefore has its own functions. The objects of cobrapy record what they are attached to.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
before = numel(model.rxns);
reduced = removeReactions(model, {'ACO'}, ...
    'removeUnusedMets', true, 'removeUnusedGenes', true);
fprintf('%d -> %d reactions, %d -> %d genes\n', before, numel(reduced.rxns), ...
    numel(model.genes), numel(reduced.genes));
```

```text
53 -> 52 reactions, 61 -> 60 genes
```

Both flags default to `false`, so `removeReactions` without flags leaves metabolites and genes that nothing refers to, and they appear later as gaps. `removeUnusedComps` does the same for compartments when `removeUnusedMets` is true, and `deleteUnusedGenes` performs the gene part alone.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
before = len(model.reactions), len(model.genes)

with model:
    model.remove_reactions([model.reactions.get_by_id("ACO")], remove_orphans=True)
    print(f"{before[0]} -> {len(model.reactions)} reactions, "
          f"{before[1]} -> {len(model.genes)} genes")
```

```text
53 -> 52 reactions, 61 -> 60 genes
```

`remove_orphans=True` corresponds to those two flags. A deletion inside `with model:` is undone when the block ends, so the effect of a deletion can be measured without keeping it.
:::
::::

## Deleting a gene

Deleting a gene differs from deleting its reactions. The gene and its occurrences in the reaction rules are removed, and the reactions stay with rewritten rules. With the default policy for a reaction that has no catalyst left, the flux state equals that of a knockout (bounds `(0, 0)`), and the model differs because the gene is gone.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
reduced = removeGenes(model, {'YBR196C'});
fprintf('%d -> %d genes\n', numel(model.genes), numel(reduced.genes));
disp(reduced.grRules{getIndexes(reduced, 'PGI', 'rxns')});
```

```text
61 -> 60 genes
YLR354C
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import remove_genes

with model:
    remove_genes(model, ["YBR196C"])
    print(len(model.genes), "genes")
    print("PGI rule:", repr(model.reactions.get_by_id("PGI").gene_reaction_rule))
```

```text
60 genes
PGI rule: 'YLR354C'
```
:::
::::

`removeGenes` and `remove_genes` rewrite each affected rule without the removed gene. A reaction that has no catalyst left stays in the model with its rule dropped and its bounds set to `(0, 0)`. This is the default of `remove_genes` (`blocked_reactions="constrain"`), the behaviour of `removeGenes` with `removeBlockedRxns` at its default of false, and the bound state that `knock_out_model_genes` leaves. With `blocked_reactions="keep"`, the blocked reactions keep their bounds. `removeBlockedRxns` set to true, or `blocked_reactions="remove"`, deletes them, which turns a gene deletion into a reaction deletion. [Deletions and essentiality](deletions.md) covers when that is the question.

When at least one requested gene is in the model, the genes that no remaining reaction uses are removed as well, including genes that were not requested. When no requested gene is in the model, no gene is removed. In `removeGenes`, `standardizeRules` is on by default and normalises the rewritten rules.

:::{admonition} Troubleshooting
:class: warning

- `model.S` is edited by hand. `model.rev`, the bounds and the gene matrix then describe a different model than the matrix does. `changeRxns` edits a reaction consistently.
- A deleted reaction leaves metabolites without a reaction. Without the orphan flags, metabolites that nothing produces or consumes remain in the model and appear as gaps ([Quality control](quality-control.md)).
- A gene rule that was meant to be extended is overwritten. `changeGrRules` and `change_gene_reaction_rules` replace the rule by default.
- Python edits the model in place. MATLAB copies the struct on assignment, so `modelB = removeReactions(modelA, ...)` leaves `modelA` unchanged. In Python, `model.copy()` or `with model:` keeps the original.
:::

## See also

- [Building a model from scratch](building.md): the same operations in the other direction.
- [Model structure and identifiers](model-structure.md): the reason RAVEN needs dedicated deletion functions.
- [Quality control](quality-control.md): checking the result of an edit.
