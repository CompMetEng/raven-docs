# 8. Editing an existing model

Curation is mostly editing: a stoichiometry that was wrong, a gene association
that has been superseded, a reaction that should never have been there. This
page is the safe way to do each of those.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `changeRxns` | `change_reaction_equations` | replace a reaction's stoichiometry |
| `changeGrRules` | `change_gene_reaction_rules` | set or extend gene associations |
| `standardizeGrRules` | `gpr_to_dnf` | normalise a GPR |
| `setParam` | `Reaction.bounds` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | change bounds, objective |
| `removeReactions` | `Model.remove_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | delete reactions |
| `removeMets` | `remove_metabolites` | delete metabolites |
| `removeGenes`, `deleteUnusedGenes` | `remove_genes` | delete genes |

## Setup

`smallYeast.yml` from [`docs/data/`](../data/README.md).

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

## 8.1 Fix a stoichiometry

Give the whole equation, not a coefficient: the toolbox rewrites the reaction's
column in the stoichiometric matrix, which is what keeps everything consistent.

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

Both take a **mapping of reaction to equation** so a batch of curated
reactions can be applied in one call, which is what a curation spreadsheet
turns into. Every id must already exist; these functions change reactions
rather than add them.

Bounds are left alone. Rewriting an equation from `=>` to `<=>` does not
make the reaction reversible, because the direction is set by `lb` and `ub`
rather than by the arrow; 8.4 sets those separately. Both functions also
take the `eqnType` and `allowNewMets` options of `addRxns`, and default to
matching metabolites by id.
:::
::::

## 8.2 Change a gene association

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

A gene that the model did not have is created for you. Pass `replace=False`
to **append** an isozyme instead of overwriting, giving `(old) or (new)`,
which records an additional catalyst rather than a correction. A reaction
with no rule yet gets the new rule alone, without empty brackets.
:::
::::

## 8.3 Normalise a GPR

Rules that mix `and` and `or` in nested brackets are hard to compare and hard to
score. Both toolboxes rewrite them into disjunctive normal form, a list of
alternative complexes. `is_dnf` takes a rule string; `gpr_to_dnf` takes cobrapy's
parsed `GPR` object and returns the complexes as lists.

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

`standardizeGrRules` returns the rules and a matching `rxnGeneMat`, not a
model, so the results have to be assigned back into the struct to persist.
Disjunctive normal form is a flat `or` of `and` groups, one group per
alternative complex, which is the form the scoring in
[14. Context-specific models](init.md) expects.
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

## 8.4 Change bounds and the objective

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

`setParam` takes `'lb'`, `'ub'`, `'eq'`, `'obj'` and `'rev'`, and accepts a
list of reactions with a list of values, applying them in one call.
:::
::::

## 8.5 Delete things

Deleting is where the two designs differ most. RAVEN has to remove the matching
row or column from **every** field, which is why deletion has its own functions;
cobrapy's objects know what they are attached to.

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

Both flags default to `false`, so a plain `removeReactions` leaves behind
metabolites and genes that nothing refers to any more, which later read as
gaps. `removeUnusedComps` does the same for compartments.
`deleteUnusedGenes` performs the gene half on its own.
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

`remove_orphans=True` is cobrapy's equivalent of those two flags. Note the
`with model:`, deletions inside it are rolled back on exit, so the effect of
a deletion can be measured without keeping it.
:::
::::

## 8.6 Delete a gene, not a reaction

Removing a gene is not the same as knocking it out: the reactions stay, and
their GPRs are rewritten without it.

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

`removeGenes` rewrites each affected GPR without the removed gene. Its
`removeBlockedRxns` flag, off by default, additionally deletes reactions that
lose their last catalyst, which turns a gene deletion into a reaction deletion;
[16. Deletions and essentiality](deletions.md) covers when that is the
question being asked. `standardizeRules`, on by default, normalises the
rewritten rules.

:::{warning} What can go wrong
- **Editing `model.S` by hand.** It leaves `model.rev`, the bounds and the
  gene matrix describing a different model than the matrix does. Use
  `changeRxns`.
- **Deleting a reaction and stranding its metabolites.** Without the orphan
  flags you keep metabolites nothing produces or consumes, which then show up
  as gaps. See [9. Quality control](quality-control.md).
- **Overwriting a GPR you meant to extend.** `changeGrRules` and
  `change_gene_reaction_rules` replace by default.
- **Forgetting that Python edits in place.** MATLAB copies the struct on
  assignment, so `modelB = removeReactions(modelA, ...)` leaves `modelA`
  alone. In Python, use `model.copy()` or `with model:`.
:::

## See also

- [7. Building a model from scratch](building.md), the same operations, in the
  other direction.
- [2. Model structure and identifiers](model-structure.md), why RAVEN needs
  dedicated deletion functions.
- [9. Quality control](quality-control.md), checking what an edit did.
