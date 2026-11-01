# Table-driven curation

Curation by single function calls is hard to review and to repeat. Both toolboxes accept curation as tables, with one row per metabolite, gene or reaction, in tab-separated files that a spreadsheet edits and a pull request shows as a difference.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `curateModelFromTables` | `batch_curate_from_tsv` | apply curation tables from files |
| `curateModelFromTables` | `batch_curate` | apply curation tables from DataFrames in memory |

## The tables

There are four tables. Each is optional, except that the two reaction tables are used together.

| Table | Columns |
|---|---|
| metabolites | `metNames`, `comps`, `formula`, `charge`, `inchi`, `metNotes`, then one column per MIRIAM namespace |
| genes | `genes`, `geneShortNames`, then MIRIAM |
| reactions | `rxnIdx`, `rxnNames`, `grRules`, `lb`, `ub`, `rev`, `subSystems`, `eccodes`, `rxnNotes`, `rxnReferences`, `rxnConfidenceScores`, then MIRIAM |
| reaction coefficients | `rxnIdx`, `rxnNames`, `metNames`, `comps`, `coefficient`, one row per reaction and metabolite |

Columns are found by their header, so the order does not matter and the optional columns can be omitted. Both toolboxes read a `grRules` cell with the grammar of `parseGrRule`, so `G1&G2` is one gene identifier and `G1 & G2` is two genes joined by `and`. Entities are matched by name and not by identifier: metabolites by `metaboliteName[comp]`, genes by gene name, and reactions by the stoichiometry of their reactants and products. A row that matches nothing adds a new entity, and a row that matches an existing entity overwrites it. `rxnIdx` links the two reaction tables and is local to the files, without meaning in the model.

## Setup

The files are `smallYeast.yml` and [`curation-mets.tsv`](../data/curation-mets.tsv) from [`docs/data/`](../data/README.md). The model has formulas and no charges, which leaves the charge balance undecidable in [Getting started](getting-started.md). The table supplies four charges, together with formulas of the charged species, because a formula and a charge must describe the same species for the charge balance to work. The other metabolites of `smallYeast` keep their neutral formulas, so the reactions of these four metabolites balance again only after their partners are curated in the same way. [Quality control](quality-control.md) finds them.

```text title="curation-mets.tsv"
metNames	comps	formula	charge	metNotes
(S)-malate	m	C4H4O5	-2	charge assigned at pH 7.3
2-oxoglutarate	m	C5H4O5	-2	charge assigned at pH 7.3
2-phospho-D-glycerate	c	C3H4O7P	-3	charge assigned at pH 7.3
3-phospho-D-glycerate	c	C3H4O7P	-3	charge assigned at pH 7.3
```

## Applying a table

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
fprintf('charges before: %d\n', isfield(model, 'metCharges'));

curated = curateModelFromTables(model, 'curation-mets.tsv');
idx = getIndexes(curated, 'MAL_m', 'mets');
fprintf('%s charge %d, note: %s\n', curated.metNames{idx}, ...
    curated.metCharges(idx), curated.metNotes{idx});
```

```text
charges before: 0
[Warning: The following metabolites are already present in the model, their annotation will be overwritten to match the metsInfo file. If you do not particularly want to curate their annotations, it would be better to remove these metabolites from metsInfo: (S)-malate[m]
		2-oxoglutarate[m]
		2-phospho-D-glycerate[c]
		3-phospho-D-glycerate[c]]
(S)-malate charge -2, note: charge assigned at pH 7.3
```

A model without charges has no `metCharges` field, and no field filled with `NaN`. The optional fields of RAVEN work this way throughout, and code that reads one checks with `isfield` first. `curateModelFromTables` creates a field that the table supplies and the model lacks, and gives every metabolite that the table does not name the default of the field (`NaN` for a charge, an empty string for a note). The warning lists the four metabolites whose values were overwritten.

`curateModelFromTables` returns a new struct and leaves its input unchanged.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.curation import batch_curate_from_tsv
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
print("charges before:", sum(1 for m in model.metabolites if m.charge is not None))

result = batch_curate_from_tsv(model, mets_tsv="curation-mets.tsv")
print("charges after: ", sum(1 for m in model.metabolites if m.charge is not None))
print("updated:", result.updated_metabolites)

mal = model.metabolites.get_by_id("MAL_m")
print(f"{mal.name} charge {mal.charge}, note: {mal.notes['note']}")
```

```text
charges before: 0
charges after:  4
updated: ['MAL_m', 'AKG_m', 'P2G_c', 'P3G_c']
(S)-malate charge -2, note: charge assigned at pH 7.3
```

`batch_curate_from_tsv` edits the model in place and returns a `CurationResult` that lists the added and the updated entities per entity type. It warns when a row overwrites an existing entity and names the identifiers, so an addition and a replacement can be told apart without inspecting the model.

`batch_curate` takes the same four tables as DataFrames, for a pipeline that builds the tables and does not read them from disk.
:::
::::

## Adding entities and overwriting values

A row whose name matches nothing in the model adds a new entity. The identifier is generated and not taken from the file. Both toolboxes find the largest zero-padded number that carries the prefix and continue from it, so the new identifiers continue the scheme of the model.

The prefixes are arguments: `metPrefix` and `rxnPrefix` in MATLAB, `met_id_prefix` and `rxn_id_prefix` in Python. The defaults are `M_` and `R_`, the convention of cobrapy and BiGG. A model derived from yeast-GEM uses `s_` and `r_`, and other prefixes give a model with two identifier schemes.

Adding a reaction needs both reaction tables. The row in the reactions table holds the bounds, the gene rule and the annotation. The rows in the coefficients table hold the stoichiometry, one row per metabolite, negative for substrates and positive for products, linked by `rxnIdx`. A metabolite named there that the model lacks is created, so the metabolite table is usually applied in the same pass.

:::{admonition} Blank cells overwrite values
:class: warning

An empty cell is an instruction and not an omission. By default, it overwrites the existing value of the model, so a table written to correct one charge erases the text annotations in every column that is present and blank in that row. `overwriteWithEmpty` set to false, or `overwrite_with_empty=False` in Python, keeps the existing values.

Some cells never overwrite: an empty `grRules` cell, and empty bounds. An empty charge or confidence score becomes 0 when another row has a value. A charge, confidence-score or annotation (MIRIAM) column without any value is not written. In Python, a text column that is present and blank in every row also clears the stored values.

The table includes the columns that are curated, and every value that must survive is written in the file. A blank cell keeps the existing value only when `overwriteWithEmpty` is false.
:::

:::{admonition} Troubleshooting
:class: warning

- The names do not match. A trailing space, a different capitalisation or `name[comp]` with the wrong compartment makes the row add a duplicate entity and leaves the intended entity uncurated.
- Reactions are matched by stoichiometry. Two reactions with the same reactants and products that differ only in direction or bounds are one reaction to the matcher.
- The identifier prefix is wrong. The default is `M_` and `R_`. On a model with `s_` and `r_`, the additions are correct and their identifiers differ from all others in the model.
- Changes are not recorded. The tables are the record. They are committed together with the model, as the curation is otherwise as difficult to review as the function calls it replaced.
:::

## See also

- [Editing an existing model](editing.md): the same changes, one call at a time.
- [Quality control](quality-control.md): checking the result of a curation pass.
- [Reading and writing models](io.md): the Excel format, the other tabular format for models.
