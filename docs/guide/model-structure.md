# Model structure and identifiers

A model is a struct of parallel arrays in MATLAB and a graph of objects in Python. A script is translated between the two by mapping each field to its attribute.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `checkModelStruct` | `check_model` | report problems in a model |
| `sortIdentifiers` | `sort_identifiers` | sort reactions, metabolites and genes by identifier |
| `getIndexes` | `DictList.get_by_id` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | find a reaction, metabolite or gene by identifier |
| `getIndexes` (`'metcomps'`) | `parse_name_comp`, then a filter on name and compartment | resolve a `name[comp]` token |
| no equivalent | `subsystem_to_str` | one subsystem string from any stored form |
| `addIdentifierPrefix`, `removeIdentifierPrefix` | handled on read and write {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | SBML identifier prefixes |
| `ravenCobraWrapper` | not needed | convert between RAVEN and COBRA structs |

## The correspondence

| RAVEN field | cobrapy | Note |
|---|---|---|
| `model.rxns` | `model.reactions` (identifiers) | a `DictList`, indexable by identifier or position |
| `model.rxnNames` | `reaction.name` | |
| `model.mets`, `model.metNames` | `model.metabolites`, `metabolite.name` | |
| `model.metFormulas` | `metabolite.formula` | |
| `model.genes` | `model.genes` | |
| `model.grRules` | `reaction.gene_reaction_rule` | same Boolean syntax |
| `model.rxnGeneMat` | `reaction.genes`, `gene.reactions` | navigable from both sides |
| `model.lb`, `model.ub` | `reaction.bounds` | |
| `model.rev` | derived from the bounds | `reaction.reversibility` is read-only |
| `model.S` | `create_stoichiometric_matrix(model)` | built on demand |
| `model.comps`, `model.metComps` | `metabolite.compartment`, `model.compartments` | |
| `model.subSystems` | `reaction.subsystem` | RAVEN allows several subsystems per reaction |
| `model.c` | `model.objective` | an expression |

In MATLAB the caller keeps the parallel arrays aligned. `removeReactions` removes the same position from every reaction-length field and the matching column of `model.S`, so a manual deletion takes more than one line. In cobrapy each object holds its own links, and `model.remove_reactions([...])` leaves no stale state.

The difference also determines where errors become visible. A RAVEN model can be left in a state that no function rejects and that later functions misread, which `checkModelStruct` detects ([Checking a model](#checking-a-model)). A `cobra.Model` cannot reach most of these states, because the class maintains the structure.

## Setup

The examples use `smallYeast.yml` from [`docs/data/`](../data/README.md).

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

Most RAVEN functions take or return indices, and `getIndexes` converts between identifiers and indices. The third argument names the field to search, because one string can be a reaction identifier in one field and absent from another. It takes `'rxns'`, `'mets'`, `'genes'`, `'metnames'` or `'metcomps'`, and on a GECKO model with a `model.ec` structure also `'ecrxns'`, `'ecenzymes'` and `'ecgenes'`.

An identifier that is not found raises the error `Could not find object 'X' in the model` in every mode except `'metnames'`, which returns an empty vector. A metabolite name can occur in several compartments, and `'metnames'` returns every matching index. In `'metcomps'` mode, a token that matches more than one metabolite (the same name twice in one compartment) raises an error that names the matched metabolites. A request for several names returns a cell array with one index vector per name, and a request for one name returns a plain vector.
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

`DictList` looks up an object by identifier and the object itself is the handle, so no index is kept. `get_by_id` raises `KeyError` when the identifier is absent. The attribute form `model.reactions.PGI` is the same lookup, and it works for identifiers that are valid Python names: `model.reactions.r_0001` resolves, and an identifier with a dot or a hyphen needs `get_by_id`. Both forms return the same object, and a reference to it stays valid across edits elsewhere in the model.
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

`model.metComps` holds an index into `model.comps`, so the compartment of a metabolite takes the two steps above. A compartment is renamed with one edit to `model.compNames`, and no metabolite needs to be updated.
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

`model.compartments` maps identifier to name and is derived from the metabolites, so a compartment exists while at least one metabolite is in it.
:::
::::

RAVEN writes metabolite names as `name[comp]` in Excel and text exports and accepts that form on input. Both toolboxes split the token at the last bracketed group, so a name that itself contains brackets resolves.

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

`parse_name_comp` splits the string without access to a model, and the `query` after it is the lookup that `getIndexes` performs. The compartment is `None` when the string has no trailing bracket, so one call accepts both forms and the caller determines what a missing compartment means. An empty list means that the name is absent, and more than one entry means that the name is duplicated in that compartment. The function is imported from `raven_toolbox.utils.parse`, and the namespace `raven_toolbox.utils` does not re-export it.
:::
::::

## Subsystems

RAVEN allows several subsystems per reaction, so an entry of `model.subSystems` is a string or a cell array of strings. The field as a whole has one of the two shapes, and `checkModelStruct` reports a mixture ([Checking a model](#checking-a-model)). cobrapy stores one string per reaction, and `subsystem_to_str` converts either form to a string.

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

cobrapy declares `Reaction.subsystem` as a string and does not enforce it. A model that came through RAVEN or through hand-written YAML can hold a list there, and the error appears when code concatenates it. `subsystem_to_str` joins the parts with `;`, so no name is dropped, and returns `""` for an empty or absent subsystem. `subsystem_to_str` is applied wherever a subsystem is printed, compared or written.
:::
::::

## Checking a model

Each toolbox has a validator, and the two check different things because the two representations fail in different ways.

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

`checkModelStruct` validates the struct: required fields are present, each field has the expected type and length, and identifiers are non-empty, unique and valid. It also reports advisory findings: metabolites and genes that nothing uses, contradicting bounds, a missing or ambiguous objective, malformed gene rules and formulas, and cross-references that point nowhere. A finding has a `category` (`missing_field`, `wrong_type`, `empty_id`, `duplicate`, `invalid_id`, `invalid_bounds`, `unused`, `objective`, `gpr`, `invalid_formula`, `cross_reference` or `other`), a `target` with the field or identifier concerned, and the full `message`.

With an output argument, the function returns the findings and neither prints nor throws. Without one, it reports while it checks, and `throwErrors` determines whether a structural problem stops the script. Advisory findings are warnings in both cases.
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

`check_model` does not check field types, because a `cobra.Model` cannot hold a misshapen field. It checks what cobrapy leaves to the caller: metabolites and genes that no reaction uses, reactions without metabolites, metabolites without a name, two metabolites with the same name in one compartment, and an objective that is missing or spread over several reactions. A `ModelIssue` has `category`, `object_id` and `message`. The function returns a list and does not raise, so a script filters by category and determines which findings are fatal.

A result of `0` means that no curation problem was found. It does not mean that the model satisfies `checkModelStruct`, because the two lists overlap in the checks for unused elements and for the objective.
:::
::::

## Sorting identifiers

A sorted model gives a readable difference between two versions, as adding one reaction otherwise shifts everything after it and turns a one-line change into a whole-file difference. `exportForGit` and `export_for_git` sort as well.

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

`sortIdentifiers` returns a new struct and leaves the original unchanged. It reorders reactions, metabolites, genes and compartments together with every field indexed by them, including `model.S` and `model.rxnGeneMat`, so the model stays consistent.
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

`sort_identifiers` sorts in place and returns the model it received, and the returned name refers to the same model. `model.copy()` should be passed when the original order is needed. Compartments are stored as a dictionary and are not sorted here; the writers emit them in order where it matters.
:::
::::

## Conversion to and from the COBRA Toolbox

RAVEN and the COBRA Toolbox use different field names for the same model. In MATLAB, `ravenCobraWrapper` converts a struct in either direction and infers the direction from the fields it finds. Python needs no conversion, because a raven-toolbox model is a `cobra.Model`, which every Python COBRA tool accepts.

:::{admonition} Troubleshooting
:class: warning

- Fields are out of alignment. In MATLAB, a hand edit of one reaction-length field without the others leaves a model that works and fails later, often far from the edit. `checkModelStruct` detects it.
- A field has mixed contents. `model.subSystems` holds strings or cell arrays of strings, one kind per model. The whole field is converted.
- `model.rev` disagrees with the bounds. RAVEN stores the reversibility explicitly, so it can contradict `lb` and `ub` after a manual edit, and different functions read different fields. Python cannot reach this state, because `reaction.reversibility` is computed from the bounds on every read.
- Subsystems are lists. Code that assumes a string in `reaction.subsystem` fails on a model imported from RAVEN. `subsystem_to_str` accepts both forms.
- A name lookup returns several indices. `getIndexes` with `'metnames'` matches the name in every compartment. `'metcomps'` with the `name[comp]` form selects one metabolite.
:::

## See also

- [Getting started](getting-started.md): loading and inspecting a model.
- [Reading and writing models](io.md): the origin of identifier prefixes.
- [MATLAB vs Python](../matlab-vs-python.md): the full function mapping.
