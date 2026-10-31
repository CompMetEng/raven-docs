# Model structure and identifiers

The same model is a struct of parallel arrays in MATLAB and a graph of objects in Python. Knowing which field corresponds to which attribute is most of what translating a script between the two requires.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `checkModelStruct` | `check_model` | report problems in a model |
| `sortIdentifiers` | `sort_identifiers` | sort reactions, metabolites and genes by id |
| `getIndexes` | `DictList.get_by_id` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | look up a reaction, metabolite or gene by id |
| `getIndexes` (`'metcomps'`) | `parse_name_comp`, then a name and compartment filter | resolve a `name[comp]` token |
| no equivalent | `subsystem_to_str` | one subsystem string, whatever the source stored |
| `addIdentifierPrefix`, `removeIdentifierPrefix` | handled on read and write {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | SBML identifier prefixes |
| `ravenCobraWrapper` | not needed | convert between RAVEN and COBRA structs |

## The correspondence

| RAVEN field | cobrapy | Note |
|---|---|---|
| `model.rxns` | `model.reactions` (ids) | a `DictList`, indexable by id or position |
| `model.rxnNames` | `reaction.name` | |
| `model.mets`, `model.metNames` | `model.metabolites`, `metabolite.name` | |
| `model.metFormulas` | `metabolite.formula` | |
| `model.genes` | `model.genes` | |
| `model.grRules` | `reaction.gene_reaction_rule` | same Boolean syntax |
| `model.rxnGeneMat` | `reaction.genes`, `gene.reactions` | the mapping is navigable from either side |
| `model.lb`, `model.ub` | `reaction.bounds` | |
| `model.rev` | derived from the bounds | `reaction.reversibility` is read-only |
| `model.S` | `create_stoichiometric_matrix(model)` | built on demand, not stored |
| `model.comps`, `model.metComps` | `metabolite.compartment`, `model.compartments` | |
| `model.subSystems` | `reaction.subsystem` | RAVEN allows several per reaction |
| `model.c` | `model.objective` | an expression, not a coefficient vector |

In MATLAB the caller keeps parallel arrays aligned, and in Python the objects hold their own references. Deleting a reaction in RAVEN means removing the same row from every reaction-length field, and the matching column of `model.S`; `removeReactions` exists for this, so a deletion is not a one-line edit. In cobrapy the object holds its own links, so `model.remove_reactions([...])` is enough and there is no state left behind to go stale.

That difference also decides where mistakes become visible. A RAVEN model can be left in a state no function rejects but later functions misread, and RAVEN ships a validator for this ([Checking a model](#checking-a-model)). A `cobra.Model` cannot reach most of those states, because the class maintains the structure.

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

## Lookup by identifier

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, 'PGI', 'rxns');
fprintf('%s: %s\n', model.rxns{idx}, model.rxnNames{idx});
fprintf('genes: %s\n', model.grRules{idx});
```

```text
PGI: Glucose-6-phosphate isomerase
genes: YBR196C
```

Most RAVEN functions take or return indices, and `getIndexes` converts between identifiers and indices. The third argument names the field to search, because the same string can be a reaction id in one field and nothing in another. It takes `'rxns'`, `'mets'`, `'genes'`, `'metnames'` or `'metcomps'`, plus `'ecrxns'`, `'ecenzymes'` and `'ecgenes'` on a GECKO model that carries a `model.ec` structure.

A miss is an error, not a zero: `getIndexes` raises `Could not find object 'X' in the model` in every mode except `'metnames'`, which returns an empty vector. That exception exists because a metabolite name can occur in several compartments, so `'metnames'` returns every matching index. In `'metcomps'` mode a token that matches more than one metabolite (the same name twice in one compartment) is an error as well, naming the ids of the metabolites it matched. Asking for several names at once gives back a cell array with one index vector per name; asking for exactly one name unwraps that to a plain vector.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
rxn = model.reactions.get_by_id("PGI")
print(f"{rxn.id}: {rxn.name}")
print("genes:", rxn.gene_reaction_rule)
print("also reachable as:", model.reactions.PGI.id)
```

```text
PGI: Glucose-6-phosphate isomerase
genes: YBR196C
also reachable as: PGI
```

There is no index to carry around: `DictList` looks up by id, and the object is the handle. `get_by_id` raises `KeyError` on a miss. The attribute form `model.reactions.PGI` is the same lookup, and works only for ids that are valid Python names, so `model.reactions.r_0001` resolves but an id containing a dot or a hyphen has to go through `get_by_id`. Both forms return the same object, and keeping a reference to it stays valid across edits elsewhere in the model.
:::
::::

## Compartments

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
disp(model.comps);                       % compartment ids
i = getIndexes(model, 'G6P_c', 'mets');
disp(model.comps{model.metComps(i)});    % the compartment of one metabolite
```

```text
    {'c'}
    {'m'}

c
```

`model.metComps` holds an index into `model.comps`, not the compartment letter, so reading a metabolite's compartment always takes the two steps above. The indirection keeps compartment names editable in one place: renaming a compartment is a single edit to `model.compNames`, with nothing to update per metabolite.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(model.compartments)
print(model.metabolites.get_by_id("G6P_c").compartment)
```

```text
{'m': 'mitochondria', 'c': 'cytosol'}
c
```

`model.compartments` maps id to name and is derived from the metabolites, so a compartment exists exactly as long as something is in it.
:::
::::

RAVEN also writes metabolite names as `name[comp]` in Excel and text exports, and accepts that form on input. Both toolboxes split the token on the last bracketed group, so a name that itself contains brackets resolves.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
% 'metcomps' resolves the name[comp] form; 'metnames' matches names alone
i = getIndexes(model, 'alpha-D-glucose 6-phosphate[c]', 'metcomps');
fprintf('%d %s\n', i, model.mets{i});
```

```text
14 G6P_c
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils.parse import parse_name_comp

print(parse_name_comp("alpha-D-glucose 6-phosphate[c]"))
print(parse_name_comp("ATP"))

name, comp = parse_name_comp("alpha-D-glucose 6-phosphate[c]")
matches = model.metabolites.query(lambda m: m.name == name and m.compartment == comp, None)
print([m.id for m in matches])
```

```text
('alpha-D-glucose 6-phosphate', 'c')
('ATP', None)
['G6P_c']
```

`parse_name_comp` returns the compartment as `None` when there is no trailing bracket, so one call handles both forms and the caller decides what a missing compartment means. It splits the string and never sees a model; the `query` after it is the lookup that `getIndexes` performs. An empty list is a miss, and more than one entry means the name is duplicated in that compartment. The function is imported from `raven_toolbox.utils.parse`; the `raven_toolbox.utils` package namespace does not re-export it.
:::
::::

## Subsystems

RAVEN lets a reaction belong to several subsystems, so an entry of `model.subSystems` is either a single string or a cell array of them. The field as a whole must have one of the two shapes; `checkModelStruct` reports mixing them ([Checking a model](#checking-a-model)). cobrapy stores one string per reaction, and `subsystem_to_str` normalises whichever form a model arrived with.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, 'PGI', 'rxns');
% nest every entry before nesting one, so the field keeps a single shape
model.subSystems = cellfun(@cellstr, model.subSystems, 'UniformOutput', false);
model.subSystems{idx} = {'Glycolysis', 'Pentose phosphate pathway'};
fprintf('%s\n', strjoin(model.subSystems{idx}, '; '));
```

```text
Glycolysis; Pentose phosphate pathway
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils.parse import subsystem_to_str

rxn = model.reactions.get_by_id("PGI")
rxn.subsystem = ["Glycolysis", "Pentose phosphate pathway"]
print(subsystem_to_str(rxn.subsystem))
print(subsystem_to_str("Glycolysis"))
```

```text
Glycolysis;Pentose phosphate pathway
Glycolysis
```

cobrapy declares `Reaction.subsystem` a plain string but does not enforce it, so a model that came through RAVEN, or through hand-written YAML, can hold a list there, and no error is raised until something tries to concatenate it. `subsystem_to_str` joins the parts with `;` and does not take only the first, so no name is dropped, and returns `""` for an empty or absent subsystem. Use it wherever a subsystem is printed, compared or written out.
:::
::::

## Checking a model

Both toolboxes provide a validator, and they check different things, because the two representations fail in different ways.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
issues = checkModelStruct(model, 'throwErrors', false);
fprintf('%d issue(s)\n', numel(issues));

mixed = model;
mixed.subSystems{idx} = 'Glycolysis';   % a plain string among cell arrays
issues = checkModelStruct(mixed, 'throwErrors', false);
fprintf('%d issue(s), category %s\n', numel(issues), issues(1).category);
fprintf('%s\n', issues(1).message);
```

```text
0 issue(s)
1 issue(s), category wrong_type
The "subSystems" field must be a cell array of chars, *or* a cell array of cell arrays of chars
```

`checkModelStruct` validates the struct itself: that required fields are present, that each holds the type and length it should, and that identifiers are non-empty, unique and legal. On top of that it reports advisory findings: metabolites and genes nothing uses, bounds that contradict each other, a missing or ambiguous objective, malformed gene rules and formulas, and cross-references that point nowhere. Every finding carries a `category` (`missing_field`, `wrong_type`, `empty_id`, `duplicate`, `invalid_id`, `invalid_bounds`, `unused`, `objective`, `gpr`, `invalid_formula`, `cross_reference` or `other`), a `target` naming the field or identifier involved, and the full `message`.

Asking for an output argument returns the findings and neither prints nor throws. Called without one it reports as it goes, and `throwErrors` decides whether a structural problem stops the script; advisory findings are warnings either way.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils import check_model

issues = check_model(model)
print(len(issues), "issue(s)")
for issue in issues[:5]:
    print(f"  {issue.category}: {issue.message}")
```

```text
0 issue(s)
```

`check_model` has no field types to check, because a `cobra.Model` cannot hold a misshapen field. It checks the curation layer that cobrapy leaves to the caller: metabolites and genes no reaction uses, reactions with no metabolites, metabolites without a name, two metabolites sharing a name inside one compartment, and an objective that is missing or spread over several reactions. Each `ModelIssue` carries `category`, `object_id` and `message`, and the function returns a list and does not raise, so a script can filter by category and decide for itself what is fatal.

A `0` here means no curation problem was found; it does not imply that the model satisfies `checkModelStruct`. The two lists overlap only on the unused-element and objective checks.
:::
::::

## Sorting identifiers before a commit

Sorting makes the diff between two versions of a model readable, and `exportForGit` and `export_for_git` offer it too. Without it, adding one reaction can shift everything after it and turn a one-line change into a whole-file diff.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
sortedModel = sortIdentifiers(model);
fprintf('%s\n', strjoin(sortedModel.rxns(1:5)', ', '));
```

```text
ACO, ACS, ADH1, ALD6, ATPX
```

`sortIdentifiers` returns a new struct and leaves the original alone. It permutes reactions, metabolites, genes and compartments together with every field indexed by them, `model.S` and `model.rxnGeneMat` included, so the model stays internally consistent.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils import sort_identifiers

sorted_model = sort_identifiers(model)
print([r.id for r in sorted_model.reactions[:5]])
print("same object:", sorted_model is model)
```

```text
['ACO', 'ACS', 'ADH1', 'ALD6', 'ATPX']
same object: True
```

`sort_identifiers` sorts in place and returns the model it was given, so the name on the left is not a second copy. Pass `model.copy()` when the original order matters. Compartments are a plain dict and are left alone here; the writers emit them in order where it is relevant.
:::
::::

## Converting to and from the COBRA Toolbox

RAVEN and the COBRA Toolbox use different field names for the same model. In MATLAB, `ravenCobraWrapper` converts a struct in either direction, inferring which direction from the fields it finds. There is no Python equivalent because there is nothing to convert: a raven-toolbox model is a `cobra.Model`, which every Python COBRA tool takes.

:::{admonition} Troubleshooting
:class: warning

- Fields drift out of alignment. In MATLAB, editing one reaction-length field by hand without editing the others leaves a model that looks fine and fails later, often far from the edit. `checkModelStruct` detects it.
- A field ends up with mixed contents. `model.subSystems` takes strings or cell arrays of strings, but not both in the same model. Convert the whole field, not one entry.
- `model.rev` disagrees with the bounds. RAVEN stores reversibility explicitly, so it can contradict `lb` and `ub` after a manual edit, and different functions consult different ones. Python cannot get into that state, because `reaction.reversibility` is computed from the bounds on every read.
- Subsystems come back as a list. Code that assumes `reaction.subsystem` is a string breaks on a model imported from RAVEN. Use `subsystem_to_str`.
- A name lookup returns several indices. `getIndexes` with `'metnames'` matches a name in every compartment it occurs in. Use `'metcomps'` and the `name[comp]` form when one specific metabolite is meant.
:::

## See also

- [Getting started](getting-started.md), loading a model and inspecting it.
- [Reading and writing models](io.md), where identifier prefixes come from.
- [MATLAB vs Python](../raven3-vs-raven-toolbox.md), the full function mapping.
