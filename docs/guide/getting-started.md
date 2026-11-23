# Getting started

The page covers loading a model, reporting its size and inspecting one reaction, one metabolite and one gene. The later pages use these operations.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `readYAMLmodel` | `read_yaml_model` | read a RAVEN YAML model |
| `importModel` | `read_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read an SBML model |
| `printModelStats` | model attributes {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | size of the model |
| `getIndexes` | `get_by_id` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | find an object by identifier |
| `constructEquations` | `Reaction.reaction` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | reaction equation as a string |
| `getElementalBalance` | `check_mass_balance` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | mass balance of a reaction |

## Setup

The examples use `smallYeast.yml`, a model of the central carbon metabolism of yeast that is included with RAVEN. The file is [`docs/data/smallYeast.yml`](../data/smallYeast.yml), and the examples run in the directory that contains it.

One of the toolboxes must be installed first ([Installation](../installation/index.md)). The Setup section of most pages names the files that the page needs. All of them are in [`docs/data/`](../data/README.md), which is also the working directory when the `raven-docs` repository is cloned. The blocks of a page build on each other and run in order in one MATLAB or Python session.

## Loading the model

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
disp(model.id);
```

```text
smallYeast
```

A RAVEN model is a MATLAB struct of parallel arrays. `model.rxns`, `model.mets` and `model.genes` hold the identifiers, and every other field is aligned with one of them by position: `model.lb(4)` is the lower bound of the reaction in `model.rxns{4}`. The stoichiometric matrix `model.S` has one row per metabolite and one column per reaction, in the order of `model.mets` and `model.rxns`. Most operations work on indices into these arrays, so an identifier is first converted to an index.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
print(model.id)
```

```text
smallYeast
```

A RAVEN model in Python is a `cobra.Model`. raven-toolbox defines no model class, so cobrapy and the other tools of the Python COBRA ecosystem operate on the model directly. Reactions, metabolites and genes are objects in collections, and each object holds references to the objects it is connected to. No indices need to be kept aligned.
:::
::::

SBML models are read with `importModel` in MATLAB and with `read_sbml_model` of cobrapy in Python. [Reading and writing models](io.md) covers all supported formats.

## Model size

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
printModelStats(model);
```

```text
Network statistics for smallYeast: Central carbon metabolism for yeast
Genes*				61
	cytosol	52
	mitochondria	17

Reactions*			53
	cytosol	45
	mitochondria	19
Unique reactions**	53

Metabolites			52
	cytosol	35
	mitochondria	17
Unique metabolites	45

* Genes and reactions are counted for each compartment if any of the corresponding metabolites are in that compartment. The sum may therefore not add up to the total number.
** Unique reactions are defined as being biochemically unique (no compartmentalization)
```

A reaction or gene is counted in every compartment in which one of its metabolites is located, and a transport reaction is therefore counted under two compartments. The per-compartment counts do not add up to the total for this reason. A unique metabolite is counted once across compartments: 52 metabolites reduce to 45, because 7 of them exist in both the cytosol and the mitochondrion. [Combining and simplifying models](combining.md) arrives at the same 45 when it merges the compartments.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(len(model.reactions), len(model.metabolites), len(model.genes))
```

```text
53 52 61
```

Python has no equivalent of `printModelStats`. The collections are attributes, so their lengths are the totals, and the counts per compartment are obtained by filtering the collections. After a solve, `model.summary()` prints the exchange fluxes and the objective.
:::
::::

## Inspecting a reaction

Glucose-6-phosphate isomerase (`PGI`) is reversible, has a gene association and is expected to be mass balanced, which covers most of what a reaction contains.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, 'PGI', 'rxns');
disp(model.rxnNames{idx});
eqn = constructEquations(model, model.rxns(idx));
fprintf('%s\n', eqn{1});
fprintf('bounds: [%g %g]\n', model.lb(idx), model.ub(idx));
disp(model.grRules{idx});
```

```text
Glucose-6-phosphate isomerase
alpha-D-glucose 6-phosphate[c] <=> beta-D-fructofuranose 6-phosphate[c]
bounds: [-1000 1000]
YBR196C
```

`getIndexes` converts an identifier to the position used by every other field. `constructEquations` builds the equation from the stoichiometric column of that reaction and replaces the metabolite identifiers by metabolite names.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
pgi = model.reactions.get_by_id("PGI")
print(pgi.name)
print(pgi.reaction)
print("bounds:", pgi.bounds, "reversible:", pgi.reversibility)
print(pgi.gene_reaction_rule)
```

```text
Glucose-6-phosphate isomerase
G6P_c <=> F6P_c
bounds: (-1000.0, 1000.0) reversible: True
YBR196C
```

`Reaction.reaction` writes metabolite identifiers with their compartment suffix, where the MATLAB equation above uses metabolite names. Both describe the same stoichiometry.
:::
::::

The bounds define the direction. A lower bound of −1000 allows the reaction to run backwards, and a lower bound of zero does not. cobrapy derives `reversibility` from the bounds whenever it is read, so the two cannot disagree. RAVEN stores a separate `model.rev` field next to the bounds, and one can be changed without the other. [Model structure and identifiers](model-structure.md) describes how to keep the two fields consistent.

## Inspecting a metabolite

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = getIndexes(model, 'G6P_c', 'mets');
fprintf('%s (%s) in compartment %s\n', model.metNames{idx}, ...
    model.metFormulas{idx}, model.comps{model.metComps(idx)});
fprintf('takes part in %d reactions\n', nnz(model.S(idx, :)));
```

```text
alpha-D-glucose 6-phosphate (C6H13O9P) in compartment c
takes part in 4 reactions
```

The number of reactions is the number of non-zero entries in the row of the metabolite in `model.S`. `model.metComps` holds an index into `model.comps`, so the compartment takes two lookups.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
g6p = model.metabolites.get_by_id("G6P_c")
print(f"{g6p.name} ({g6p.formula}) in compartment {g6p.compartment}")
print(f"takes part in {len(g6p.reactions)} reactions")
```

```text
alpha-D-glucose 6-phosphate (C6H13O9P) in compartment c
takes part in 4 reactions
```

The model updates `Metabolite.reactions` when reactions are added or removed, so no matrix lookup is needed.
:::
::::

The formula of a metabolite is required for a mass-balance check. A reaction that contains a metabolite without a formula cannot be decided, and it is a different case from an unbalanced reaction ([Mass balance of a reaction](#mass-balance-of-a-reaction)).

## Inspecting a gene

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
gi = find(strcmp(model.genes, 'YBR196C'));
rxnIds = model.rxns(model.rxnGeneMat(:, gi) ~= 0);
fprintf('%s -> %s\n', model.geneShortNames{gi}, strjoin(rxnIds, ', '));
```

```text
PGI1 -> PGI
```

`model.rxnGeneMat` is an incidence matrix of reactions by genes. A non-zero entry means that the gene appears in the rule of the reaction. The matrix does not record how the genes combine; `model.grRules` is the sole field that records that, as `and` and `or` in text.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
gene = model.genes.get_by_id("YBR196C")
print(gene.name, "->", [rxn.id for rxn in gene.reactions])
```

```text
PGI1 -> ['PGI']
```
:::
::::

Both toolboxes distinguish the identifier of a gene from its name. `YBR196C` is the systematic identifier and `PGI1` is the standard gene name. The model is keyed on the identifier.

## Mass balance of a reaction

Draft models contain reactions that do not balance. The check of one reaction is the same in both toolboxes. [Quality control](quality-control.md) checks a whole model.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
balance = getElementalBalance(model, 'rxns', {'PGI'});
fprintf('elemental %d, charge %d\n', balance.balanceStatus, balance.chargeStatus);
```

```text
elemental 1, charge -1
```

The element balance and the charge balance are reported separately, each as `1` (balanced), `0` (unbalanced), `-1` (undecidable) or `-2` (formula that cannot be parsed). `PGI` is balanced elementally, and its charge balance is undecidable because the metabolites of this model have formulas but no charges, so there is nothing to sum. An undecidable balance means that the check could not run, and a failed charge balance means that the charges differ.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(pgi.check_mass_balance())
```

```text
{}
```

An empty dictionary means that the reaction balances. Each entry maps an element, or `charge`, to the difference between the two sides, so the result gives the size of an imbalance as well as its presence. cobrapy reports the charge in the same dictionary and omits what it cannot determine. An empty dictionary therefore covers both a balanced reaction and a reaction with nothing to check.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- A lookup fails. Identifiers are case-sensitive and have the compartment suffix (`G6P_c`). Neither toolbox returns a placeholder for an identifier that is absent: `getIndexes` raises the error `Could not find object 'X' in the model`, and `get_by_id` raises `KeyError`.
- The model loads and does not grow. In `smallYeast.yml` every uptake reaction is closed (`glcIN` has bounds `[0 0]`). [Growth media and conditions](media.md) opens a medium.
- Gene identifiers differ between the model and a FASTA file. RAVEN stores the systematic name (`YBR196C`) as the identifier and the standard name (`PGI1`) as the gene name, and the two are not interchangeable.
:::

## See also

- [Guide overview](index.md): the other pages.
- [Comparison of RAVEN and raven-toolbox](../raven3-vs-raven-toolbox.md): the features of each toolbox and the functions that cobrapy provides.
- [API reference](../api/index.md): all functions of both toolboxes.
