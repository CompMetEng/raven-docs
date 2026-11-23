# Reading and writing models

The page covers reading and writing of SBML, RAVEN YAML and Excel files, and writing of the directory layout of a Git-maintained model repository.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `importModel` | `read_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read SBML |
| `exportModel` | `write_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | write SBML |
| `readYAMLmodel` | `read_yaml_model` | read RAVEN YAML |
| `writeYAMLmodel` | `write_yaml_model` | write RAVEN YAML |
| `exportToExcelFormat` | `export_to_excel` | write the RAVEN Excel format |
| `exportForGit` | `export_for_git` | write a Standard-GEM repository layout |

The function is chosen by the file format. All readers produce the same content in memory, and no format is canonical. The formats differ in what survives a round trip and in how readable the file is, as [Identifier mangling](#identifier-mangling) and [Spreadsheets](#spreadsheets) show.

## Setup

The examples use two models from [`docs/data/`](../data/README.md): `smallYeast.yml` (RAVEN YAML, 45 kB) and `yeast-GEM.xml` (SBML, yeast-GEM v9.1.0).

## Reading a model

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
modelSmall = readYAMLmodel('smallYeast.yml');
modelYeast = importModel('yeast-GEM.xml');

fprintf('%s %d reactions\n', modelSmall.id, numel(modelSmall.rxns));
fprintf('%s %d reactions\n', modelYeast.id, numel(modelYeast.rxns));
```

```text
[Warning: The following fields have prefixes removed from all entries. If this is undesired, run importModel with removePrefix as false. Example: importModel('filename.xml',[],false);]
[Warning: The following MIRIAM strings are associated to more than one unique metabolite name: bigg.metabolite/ficytb5 bigg.metabolite/hdd2coa bigg.metabolite/pail_cho bigg.metabolite/pchol_cho bigg.metabolite/succ bigg.metabolite/tchola chebi/CHEBI:138108 chebi/CHEBI:17140 chebi/CHEBI:18097 ...and 23 more]
smallYeast 53 reactions
yeastGEM_v9.1.0 4102 reactions
```

Both warnings are informational, and the read continues. The first reports that `importModel` removed the prefixes `R_`, `M_`, `G_` and `C_` that SBML requires on identifiers. It removes them when every identifier of that type has one, and `removePrefix` set to `false` keeps them, which a comparison with the identifiers in the file requires. The second warning reports that the model gives the same database identifier to several metabolites with different names. The duplication is in yeast-GEM, and it makes these annotations unusable for matching metabolites across models.

`importModel` reads SBML Level 3 Version 1 with FBC version 2 and raises an error for older files. The [RAVEN 3 migration guide](../raven3-migration/formats-and-reconstruction.md#sbml-io) covers files that are rejected.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.io import read_sbml_model

from raven_toolbox.io import read_yaml_model

small = read_yaml_model("smallYeast.yml")
yeast = read_sbml_model("yeast-GEM.xml")

print(small.id, len(small.reactions), "reactions")
print(yeast.id, len(yeast.reactions), "reactions")
```

```text
smallYeast 53 reactions
yeastGEM_v9__46__1__46__0 4102 reactions
```

`read_sbml_model` is the reader of cobrapy and removes the same SBML prefixes. `read_yaml_model` is the reader of raven-toolbox. Both return a `cobra.Model`, and the models are interchangeable afterwards. `read_yaml_model` reads gzipped files directly and accepts the current YAML layout and the older RAVEN layout, so an archived model needs no conversion.

The yeast-GEM identifier in this output differs from the one in the MATLAB output; [Identifier mangling](#identifier-mangling) explains the difference.
:::
::::

## Identifier mangling

SBML identifiers are XML names and cannot contain a dot. When a file is written, every character in the identifiers other than a letter, digit or underscore is encoded as its ASCII code between double underscores, and a dot becomes `__46__`. The code is stored in the file, and the toolboxes differ in whether they decode it on reading.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
disp(modelYeast.id);        % from yeast-GEM.xml
modelFromYaml = readYAMLmodel('yeast-GEM.yml');
disp(modelFromYaml.id);     % same release, unencoded
```

```text
yeastGEM_v9.1.0
yeastGEM_v9.1.0
```

`importModel` decodes every `__NN__` in reactions, metabolites, compartments, genes, gene rules and the model identifier, so a round trip through SBML returns the original identifiers.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print("from SBML:", yeast.id)

from_yaml = read_yaml_model("yeast-GEM.yml")
print("from YAML:", from_yaml.id)
print("same size:", len(from_yaml.reactions) == len(yeast.reactions))
```

```text
from SBML: yeastGEM_v9__46__1__46__0
from YAML: yeastGEM_v9.1.0
same size: True
```

cobrapy decodes the identifiers of reactions, metabolites and genes and leaves the model identifier encoded. The same release read from SBML and from YAML therefore reports two model identifiers. `model.name` and the annotations are the same.
:::
::::

## Read time by format

Each toolbox reads one format quickly and the other slowly, and the ranking is reversed between them. Reading yeast-GEM takes about 17 s from SBML and 73 s from YAML in Python, and about 78 s from SBML and 17 s from YAML in MATLAB. The format follows from what the file is needed for: a readable difference between versions, or the RAVEN-specific fields that YAML preserves. A script that uses most of its time to read the file runs faster with the format that its toolbox reads quickly.

## Writing a model

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
writeYAMLmodel(modelSmall, 'smallYeast-copy.yml');
exportModel(modelSmall, 'smallYeast.xml');

roundtrip = importModel('smallYeast.xml');
fprintf('%d %d %d\n', numel(roundtrip.rxns), numel(roundtrip.mets), ...
    numel(roundtrip.genes));
```

```text
[Warning: The following fields have one or more entries that do not start with a letter or _ (conflicting with SBML specifications). Prefixes are added to all entries in those fields:]
Document written
[Warning: The following fields have prefixes removed from all entries. If this is undesired, run importModel with removePrefix as false. Example: importModel('filename.xml',[],false);]
53 52 61
```

The two warnings show the prefix rule in both directions. `exportModel` adds a prefix to a whole field when one identifier in it starts with a character other than a letter or an underscore, and `importModel` removes it again. `neverPrefix` set to `true` suppresses the prefix, and the file is then not valid SBML.

`writeYAMLmodel` and `exportModel` take `sortIds`, which sorts a copy before writing and leaves the model of the caller unchanged.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.io import write_sbml_model

from raven_toolbox.io import write_yaml_model

write_yaml_model(small, "smallYeast-copy.yml")
write_sbml_model(small, "smallYeast.xml")

roundtrip = read_sbml_model("smallYeast.xml")
print(len(roundtrip.reactions), len(roundtrip.metabolites), len(roundtrip.genes))
```

```text
53 52 61
```

`write_yaml_model` and `export_to_excel` take `sort_ids`, which sorts the written content and leaves the model unchanged. `write_sbml_model` of cobrapy has no such argument, so a stable SBML file needs the sort on a copy first: `write_sbml_model(sort_identifiers(small.copy()), path)`.
:::
::::

Both toolboxes write the reactions in the order of the model, so a reaction inserted near the start shifts every line after it. After sorting, the difference of a one-reaction change is confined to that reaction.

## Spreadsheets

The Excel format holds the model in five sheets (reactions, metabolites, compartments, genes and the metadata of the model), which can be edited without a toolbox.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
exportToExcelFormat(modelSmall, 'fileName', 'smallYeast.xlsx');
fprintf('%s\n', strjoin(sheetnames('smallYeast.xlsx'), ', '));
```

```text
RXNS, METS, COMPS, GENES, MODEL
```

`exportToExcelFormat` writes `.xlsx` files and raises an error for any other extension, including a bare directory path. The [RAVEN 3 migration guide](../raven3-migration/formats-and-reconstruction.md#excel-io) covers scripts that pass a directory. No importer exists for the format. `curateModelFromTables` reads a curated spreadsheet and applies the edits to an existing model, and it does not build a model from scratch.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import export_to_excel

export_to_excel(small, "smallYeast.xlsx")

from openpyxl import load_workbook

print(load_workbook("smallYeast.xlsx").sheetnames)
```

```text
['RXNS', 'METS', 'COMPS', 'GENES', 'MODEL']
```

`export_to_excel` needs the `excel` extra (`pip install --pre raven-toolbox[excel]`) and writes the same five sheets, with the sheets ENZYMES and ENZRXNS added for an enzyme-constrained model. Neither toolbox exports a whole model as tab-delimited files. The sole such output is the reaction table that `exportForGit` writes as its `txt` format, and pandas over the collections of the model covers other tables.
:::
::::

## Exporting for a model repository

A Git-maintained model repository (yeast-GEM, Human-GEM and the models built from `standard-GEM`) keeps the model in several formats under `model/`. A release is then usable without a toolbox, and a pull request shows a readable difference. Both toolboxes write that layout: one subdirectory per format and a `dependencies.txt` with the versions of the software that wrote the files.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
exportForGit(modelSmall, 'prefix', 'smallYeast', 'path', 'repo', ...
    'formats', {'yml', 'xml'});

written = dir(fullfile('repo', 'model', '**', '*'));
written = written(~[written.isdir]);
fprintf('%s\n', strjoin(sort({written.name}), ', '));
```

```text
[Warning: The following fields have one or more entries that do not start with a letter or _ (conflicting with SBML specifications). Prefixes are added to all entries in those fields:]
Document written
dependencies.txt, smallYeast.xml, smallYeast.yml
```

`dir` lists names, so the subdirectories with the files do not appear in the output. The files are `repo/model/yml/smallYeast.yml` and `repo/model/xml/smallYeast.xml`. `subDirs` set to `false` puts all files in one folder. The identifiers are always sorted before writing, and successive releases give a clean difference. `exportForGit` writes the five formats `mat`, `txt`, `xlsx`, `xml` and `yml` by default, and `formats` selects a subset. `COBRAtext` writes metabolite identifiers in the `txt` table, where the default is metabolite names. `mainBranchFlag` makes the export fail unless RAVEN, and GECKO for an enzyme-constrained model, is on its main branch, which ties a release to a released toolbox version.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from pathlib import Path

from raven_toolbox.io import export_for_git

root = export_for_git(small, "repo", prefix="smallYeast", formats=("yml", "xml"))
print(sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()))
```

```text
['dependencies.txt', 'xml/smallYeast.xml', 'yml/smallYeast.yml']
```

`export_for_git` returns the `model/` directory that it wrote. It sorts a copy of the model, so the files give a clean difference and the model that was passed in is unchanged. The default `formats` are `yml`, `xml`, `mat`, `xlsx` and `txt`, and `formats` selects a subset. `sub_dirs=False` writes a flat layout, and `varname` sets the variable name inside the `.mat` file for repositories that fix one.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- The SBML writer rejects an identifier. SBML identifiers start with a letter or an underscore. Both toolboxes add a prefix to a whole field when one identifier in it does not, and `importModel` and `read_sbml_model` remove the prefixes on reading.
- The model identifier differs between two copies of the same release. cobrapy decodes `__46__` in the identifiers of reactions, metabolites and genes and leaves the model identifier encoded, so yeast-GEM read from SBML reports `yeastGEM_v9__46__1__46__0`. The identifier is decoded with `re.sub(r"__(\d+)__", lambda m: chr(int(m.group(1))), model.id)`, or `model.name` is compared. Matching entities on annotations fails because some database identifiers are shared by metabolites with different names.
- The Excel export fails with a missing module. The Python export needs `openpyxl`, which `raven-toolbox[excel]` installs.
- A YAML round trip drops a field. RAVEN YAML holds the RAVEN model fields, and a field that a plugin added outside them is not guaranteed to survive. A text difference of the two files shows the loss.
- A release written with `write_sbml_model` shows large differences. `exportForGit` and `export_for_git` sort the identifiers, and `write_sbml_model` called directly does not, so the file is reordered whenever the model is.
:::

## See also

- [Getting started](getting-started.md): the next steps with a loaded model.
- [Guide overview](index.md): the other pages.
- [MATLAB vs Python](../matlab-vs-python.md): the full function mapping, including the functions that resolve to cobrapy.
