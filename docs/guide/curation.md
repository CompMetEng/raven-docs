# Table-driven curation

Curation done one function call at a time is hard to review and harder to repeat. Both toolboxes can take the curation as tables: one row per metabolite, gene or reaction, in tab-separated files that a spreadsheet can edit and a pull request can diff.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `curateModelFromTables` | `batch_curate_from_tsv` | apply curation tables from files |
| `curateModelFromTables` | `batch_curate` | the same, from DataFrames already in memory |

## The tables

Four tables, each optional, except that the two reaction tables go together:

| Table | Columns |
|---|---|
| metabolites | `metNames`, `comps`, `formula`, `charge`, `inchi`, `metNotes`, then one column per MIRIAM namespace |
| genes | `genes`, `geneShortNames`, then MIRIAM |
| reactions | `rxnIdx`, `rxnNames`, `grRules`, `lb`, `ub`, `rev`, `subSystems`, `eccodes`, `rxnNotes`, `rxnReferences`, `rxnConfidenceScores`, then MIRIAM |
| reaction coefficients | `rxnIdx`, `rxnNames`, `metNames`, `comps`, `coefficient`, one row per reaction and metabolite |

Columns are found by their header, so their order does not matter and any of the optional ones can be left out. A `grRules` cell is read with the grammar of `parseGrRule` in both tools, so `G1&G2` is one gene id, while `G1 & G2` is two genes joined by `and`. Entities are matched by name, not by identifier: metabolites on `metaboliteName[comp]`, genes on the gene name, reactions on the stoichiometry of their reactants and products. A row that matches nothing adds a new entity; a row that matches an existing one overwrites it. `rxnIdx` links the two reaction tables and is local to the files, not an identifier in the model.

## Setup

`smallYeast.yml` and [`curation-mets.tsv`](../data/curation-mets.tsv) from [`docs/data/`](../data/README.md). The model carries formulas but no charges, so the charge half of a mass balance is undecidable in [Getting started](getting-started.md). The table supplies four of them, with the formulas of the charged species to match: a formula and a charge have to describe the same species, or the charge balance this is for cannot work. The rest of `smallYeast` keeps its neutral formulas, so the reactions that use these four metabolites balance again only once their partners are curated the same way; [Quality control](quality-control.md) finds them.

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

A model with no charges has no `metCharges` field, and no field full of `NaN`. RAVEN's optional fields work this way throughout, so code that reads one should check with `isfield` first. `curateModelFromTables` creates a field the table supplies and the model lacks, giving every metabolite the table does not name the field's default (`NaN` for a charge, an empty string for a note). The warning lists the four metabolites whose values were overwritten.

`curateModelFromTables` returns a new struct and leaves its input unchanged, as the rest of RAVEN does.
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

`batch_curate_from_tsv` edits the model in place and returns a `CurationResult` listing what was added and what was updated, split by entity type. It warns when a row overwrites an existing entity, naming the ids, so an addition and a replacement are distinguishable without inspecting the model afterwards.

`batch_curate` takes the same four tables as DataFrames, for a pipeline that builds them and does not read them from disk.
:::
::::

## Adding entities and overwriting values

A row whose name matches nothing in the model adds a new entity, and the identifier is generated and not taken from the file. Both toolboxes find the largest existing zero-padded number carrying the prefix and continue from it, so the new ids continue the model's own scheme.

The prefixes are arguments: `metPrefix` and `rxnPrefix` in MATLAB, `met_id_prefix` and `rxn_id_prefix` in Python. Their defaults are `M_` and `R_`, the cobrapy and BiGG convention. A yeast-GEM-derived model should use `s_` and `r_`, and passing the wrong prefixes gives a model with two id schemes in it.

Adding a reaction needs both reaction tables. The row in the reactions table carries the bounds, the gene rule and the annotation; the rows in the coefficients table carry the stoichiometry, one per metabolite, negative for substrates and positive for products, linked by `rxnIdx`. Any metabolite named there that the model does not have is created, so the metabolite table is usually applied in the same pass.

:::{warning} Blank cells overwrite values
In both toolboxes an empty cell is an instruction and not an omission: by default it overwrites the model's existing value, so a table written to fix one charge erases the text annotations in every column that is present but blank in that row. Setting `overwriteWithEmpty` to false, or `overwrite_with_empty=False`, keeps the existing values instead. Empty `grRules` and bounds never overwrite, an empty charge or confidence score becomes 0 when another row has a value, and a charge, confidence-score or annotation (MIRIAM) column with no value at all is not written. In Python, an all-blank text column that is present still clears the stored values. For both toolboxes, include only the columns being curated, and keep the values that should survive in the file and do not rely on the blank, which keeps the value only when `overwriteWithEmpty` is false.
:::

:::{warning} Troubleshooting
- Matching on names that do not match. A trailing space, a different capitalisation, or `name[comp]` written with the wrong compartment makes the row add a duplicate entity and not curate the intended one.
- Reactions matched on stoichiometry. Two reactions with the same reactants and products, differing only in direction or bounds, are one reaction to the matcher.
- The wrong id prefix. The default is `M_` and `R_`. On a model using `s_` and `r_` the additions are correct, but their ids do not look like anything else in the model.
- No record of what changed. The tables are the record. Commit them alongside the model, or the curation is as unreviewable as the function calls it replaced.
:::

## See also

- [Editing an existing model](editing.md), the same changes one call at a time.
- [Quality control](quality-control.md), checking what a curation pass did.
- [Reading and writing models](io.md), the Excel format, which is the other tabular format for reading and writing models.
