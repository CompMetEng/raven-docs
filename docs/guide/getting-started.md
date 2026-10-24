# 1. Getting started

Load a model, see how large it is, and inspect a single reaction, metabolite and
gene. Every later page assumes these operations.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `readYAMLmodel` | `read_yaml_model` | read a RAVEN YAML model |
| `importModel` | `read_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read an SBML model |
| `printModelStats` | model attributes {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | how big the model is |
| `getIndexes` | `get_by_id` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | look something up by identifier |
| `constructEquations` | `Reaction.reaction` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | a reaction as a readable string |
| `getElementalBalance` | `check_mass_balance` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | is a reaction balanced |

## Setup

The examples use `smallYeast.yml`, a model of central carbon metabolism in yeast
that ships with RAVEN. Download it from
[`docs/data/smallYeast.yml`](../data/smallYeast.yml) and run everything from the
directory you put it in.

Install one of the toolboxes first ([Installation](../installation/index.md)).
Every page lists the files it needs under *Setup*; they are all in
[`docs/data/`](../data/README.md), or clone the repository and work in
`raven-docs/docs/data`. The blocks on a page build on each other: run them in
order in one MATLAB or Python session.

## 1.1 Load the model

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

A RAVEN model is a MATLAB struct of parallel arrays. `model.rxns`,
`model.mets` and `model.genes` hold the identifiers, and every other field
lines up with one of them by position: `model.lb(4)` is the lower bound of
the reaction named in `model.rxns{4}`. The stoichiometric matrix `model.S`
has one row per metabolite and one column per reaction, in those same orders.
Working with the model means working with indices into these arrays, which is
why looking an identifier up comes first.
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

In Python a RAVEN model **is** a `cobra.Model`. raven-toolbox defines no
model class of its own, so every cobrapy tool, and anything else in the
Python COBRA ecosystem, operates on it directly. Reactions, metabolites and
genes are objects held in collections rather than parallel arrays, and each
knows what it is connected to, so there are no indices to keep aligned.
:::
::::

For SBML use `importModel` in MATLAB and cobrapy's `read_sbml_model` in Python;
[3. Reading and writing models](io.md) covers every supported format.

## 1.2 How big is it?

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

Two things in that output are easy to misread. The per-compartment counts do
not sum to the total, because a reaction or gene is counted in every
compartment its metabolites touch; a transport reaction appears under both.
And *unique* means biochemically unique, ignoring compartments: 52
metabolites collapse to 45 because seven of them exist in both the cytosol
and the mitochondrion. The same 45 is what
[20. Combining and simplifying](combining.md) arrives at when it flattens the
compartments away.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(len(model.reactions), len(model.metabolites), len(model.genes))
```

```text
53 52 61
```

There is no equivalent of `printModelStats`. The collections are attributes,
so their lengths are the totals, and per-compartment counts come from
filtering them. After a solve, `model.summary()` prints the exchange fluxes
and the objective.
:::
::::

## 1.3 Look at a reaction

Glucose-6-phosphate isomerase, `PGI`, exercises most of what a reaction carries:
it is reversible, it has a gene association, and it should be mass balanced.

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

`getIndexes` turns an identifier into the position used by every other
field. `constructEquations` builds the readable equation from the
stoichiometric column, substituting metabolite *names* rather than
identifiers, which is why the equation reads in words.
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

`Reaction.reaction` substitutes metabolite *identifiers*, so the same
reaction reads differently from the MATLAB equation above. Both describe the
same stoichiometry.
:::
::::

The bounds carry the direction. A lower bound of −1000 means the reaction may
run backwards; a lower bound of zero means it may not. cobrapy derives
`reversibility` from the bounds each time it is asked, so the two can never
disagree. RAVEN stores an explicit `model.rev` field alongside the bounds, which
means it is possible to set one without the other;
[2. Model structure and identifiers](model-structure.md) covers what to do about
that.

## 1.4 Look at a metabolite

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

The reaction count comes from counting non-zero entries in the metabolite's
row of `model.S`. `model.metComps` holds an index into `model.comps` rather
than the compartment letter itself, which is why the compartment needs two
lookups.
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

`Metabolite.reactions` is maintained by the model as reactions are added and
removed, so it needs no matrix lookup.
:::
::::

The formula is what makes a mass-balance check possible at all. A metabolite
without one leaves every reaction it appears in undecidable, which is the
distinction 1.6 turns on.

## 1.5 Look at a gene

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

`model.rxnGeneMat` is a reactions-by-genes incidence matrix; a non-zero entry
means that gene appears in that reaction's rule. It records *which* genes are
involved, not how they combine; the `and`/`or` structure lives only in
`model.grRules` as text.
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

Both toolboxes distinguish the identifier from the name. `YBR196C` is the
systematic identifier and `PGI1` the standard gene name; the model is keyed on
the former.

## 1.6 Is the reaction balanced?

Draft models routinely contain reactions that do not balance. Checking one is the
same operation in both toolboxes; doing it for a whole model is
[9. Quality control](quality-control.md).

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

The two statuses are reported separately, and they use three values, not two:
`1` balanced, `0` unbalanced, `-1` undecidable. `PGI` balances elementally
and its charge is undecidable: the metabolites in this model carry formulas
but no charges, so there is nothing to sum. That is a different statement
from "the charges do not balance": one says the check could not run, the
other says it failed.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(pgi.check_mass_balance())
```

```text
{}
```

An empty dictionary means the reaction balances. Anything listed is an
element, or `charge`, mapped to the amount by which the two sides differ, so
the result says both whether and by how much. cobrapy folds charge into the
same dictionary rather than reporting it separately, and omits what it cannot
decide, so an empty result covers both "balanced" and "nothing to check".
:::
::::

:::{warning} What can go wrong
- **A lookup fails.** Identifiers are case-sensitive and carry the
  compartment suffix (`G6P_c`, not `G6P`). Neither toolbox returns a
  sentinel for a name it cannot find: `getIndexes` errors with
  `Could not find object 'X' in the model` and `get_by_id` raises
  `KeyError`, so a typo stops the script rather than indexing something else
  without warning.
- **The model loads but nothing grows.** In `smallYeast.yml` every uptake
  reaction is closed (`glcIN` has bounds `[0 0]`). Opening a medium is
  [5. Growth media and conditions](media.md).
- **Gene identifiers differ between model and FASTA.** Systematic names
  (`YBR196C`) and standard names (`PGI1`) are not interchangeable; RAVEN
  stores the systematic name as the identifier and the standard name as the
  gene name.
:::

## See also

- [Guide overview](index.md), the other pages, and what is still planned.
- [MATLAB vs Python](../raven3-vs-raven-toolbox.md), what each toolbox has, and where
  cobrapy takes over.
- [API reference](../api/index.md), every function in both toolboxes.
