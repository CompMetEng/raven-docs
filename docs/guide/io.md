# Reading and writing models

Get a model in and out of both toolboxes: SBML, RAVEN YAML, Excel, and the directory layout a Git-maintained model repository expects.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `importModel` | `read_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read SBML |
| `exportModel` | `write_sbml_model` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | write SBML |
| `readYAMLmodel` | `read_yaml_model` | read RAVEN YAML |
| `writeYAMLmodel` | `write_yaml_model` | write RAVEN YAML |
| `exportToExcelFormat` | `export_to_excel` | write the RAVEN Excel format |
| `exportForGit` | `export_for_git` | write a Standard-GEM repository layout |

The function needed depends on the file, not on the model; all of them produce the same in-memory model, and none of them is the canonical format. What differs is what survives a round trip and how readable the file is; [Identifier mangling](#identifier-mangling) and [Spreadsheets](#spreadsheets) show this with examples.

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

Both warnings are informational and neither stops the read. The first says `importModel` stripped the `R_`, `M_`, `G_` and `C_` prefixes SBML requires on identifiers, which it does only when every identifier of that type carries one; pass `removePrefix` as `false` to keep them, which is what a comparison against the file's own ids requires. The second reports that the model annotates several differently-named metabolites with the same database identifier. The duplication is in yeast-GEM itself, and it makes those annotations unusable as a key for matching metabolites across models.

`importModel` accepts SBML Level 3 Version 1 with FBC version 2 and errors on anything older; see the [RAVEN 3 migration guide](../raven3-migration/formats-and-reconstruction.md#sbml-io) if a file is rejected.
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

`read_sbml_model` is cobrapy's own reader and strips the same SBML prefixes. `read_yaml_model` is raven-toolbox's, and returns a plain `cobra.Model`, so the models the two readers return are interchangeable from this point. It reads gzipped files directly and accepts both the current YAML layout and the older RAVEN one, so an archived model does not need converting first.

The yeast-GEM id printed here differs from the one in the MATLAB output; [Identifier mangling](#identifier-mangling) covers the difference.
:::
::::

## Identifier mangling

SBML identifiers must be valid XML names, so they cannot contain a dot. Model, reaction and metabolite ids that do are encoded when the file is written, as `__` around the character's ASCII code: a `.` becomes `__46__`. The encoding is in the file, so what differs between the toolboxes is whether it is undone on the way back in.

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

`importModel` decodes every `__NN__` back to its character, across reactions, metabolites, compartments, genes, gene rules and the model id, so a round trip through SBML returns the original ids.
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

cobrapy decodes the reaction, metabolite and gene ids but leaves the model id encoded, so the same release read from the two formats reports two different model ids while being the same model. `model.name` and the annotations are unchanged.
:::
::::

## Read time by format

Each toolbox is fast in one format and slow in the other. Reading yeast-GEM takes about 17 s from SBML and 73 s from YAML in Python, and about 78 s from SBML and 17 s from YAML in MATLAB, so the ranking is reversed. RAVEN parses YAML itself and goes through libSBML for SBML; cobrapy has the opposite balance. The format therefore follows from what is needed from it, a readable diff or the RAVEN-specific fields YAML preserves, and a script whose run time is dominated by reading the file often runs faster in the other format.

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

The two warnings are the prefixing rule in both directions: `exportModel` adds a prefix to a whole field as soon as one id in it starts with something other than a letter or underscore, and `importModel` takes it off again. Pass `neverPrefix` as `true` to suppress the addition, but the resulting file is not valid SBML.

Both `writeYAMLmodel` and `exportModel` take `sortIds`, which sorts a copy before writing and leaves the caller's model untouched.
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

`write_yaml_model` and `export_to_excel` take `sort_ids`, which sorts what is written without touching the model. cobrapy's `write_sbml_model` has no such argument, so a stable SBML diff needs the sort applied first, on a copy: `write_sbml_model(sort_identifiers(small.copy()), path)`.
:::
::::

Both toolboxes write reactions in whatever order the model holds them, so inserting one reaction near the front shifts every line after it. Sorting first confines the diff of a one-reaction change to that reaction.

## Spreadsheets

The Excel format holds the model as five sheets, covering reactions, metabolites, compartments, genes and the model's own metadata, in a form that can be edited without a toolbox.

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

`exportToExcelFormat` writes `.xlsx` and errors on any other extension, so a bare directory path is rejected without being interpreted. The [RAVEN 3 migration guide](../raven3-migration/formats-and-reconstruction.md#excel-io) covers scripts that pass one. There is no matching importer: `curateModelFromTables` reads a curated spreadsheet back by applying tabular edits to an existing model; it does not build one from scratch.
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

`export_to_excel` needs the `excel` extra (`pip install raven-toolbox[excel]`) and writes the same five sheets, plus ENZYMES and ENZRXNS for an enzyme-constrained model. Neither toolbox exports a whole model as a set of tab-delimited files; the single reaction table that `exportForGit` writes as its `txt` format is the only such output, and pandas over the model's collections covers the rest.
:::
::::

## Exporting for a model repository

A Git-maintained model repository (yeast-GEM, Human-GEM, and the models built from `standard-GEM`) keeps the same model in several formats under `model/`, so that a release is usable without a toolbox and a diff is readable in a pull request. Both toolboxes write that layout directly, one subdirectory per format plus a `dependencies.txt` recording the versions the files were written with.

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

`dir` reports names, so the subdirectories that contain the files are not visible in the output: the layout written is `repo/model/yml/smallYeast.yml` and `repo/model/xml/smallYeast.xml`. Set `subDirs` to `false` to put everything in one folder. Identifiers are sorted before writing, with no option to skip it, so successive releases diff cleanly. By default `exportForGit` writes all five formats, `mat`, `txt`, `xlsx`, `xml` and `yml`; `formats` narrows that. `COBRAtext` switches the `txt` table from metabolite names to metabolite ids, and `mainBranchFlag` makes the export fail unless RAVEN itself (and GECKO, for an enzyme-constrained model) is on its main branch, which pins a release to a released toolbox version.
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

`export_for_git` returns the `model/` directory it wrote, and sorts a copy of the model first, so the files are diff-friendly and the model passed in is unchanged. Its default `formats` are all five, `yml`, `xml`, `mat`, `xlsx` and `txt`; `formats` narrows that. `sub_dirs=False` flattens the layout, and `varname` sets the variable name inside the `.mat` file for repositories that pin one.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- The SBML writer refuses an identifier. SBML ids must start with a letter or underscore. Both toolboxes add a prefix to a whole field when any id in it does not, so `importModel` and `read_sbml_model` strip prefixes on the way back.
- The model id differs between two copies of the same release. cobrapy decodes `__46__`-style escapes in reaction, metabolite and gene ids, but not in the model id, so yeast-GEM read from SBML reports `yeastGEM_v9__46__1__46__0`. Decode it with `re.sub(r"__(\d+)__", lambda m: chr(int(m.group(1))), model.id)`, or compare `model.name`. Do not match entities on annotations: some database ids are shared by differently named metabolites.
- Excel export fails with a missing module. The Python side needs `openpyxl`; install `raven-toolbox[excel]`.
- A YAML round trip loses a field neither format defines. RAVEN YAML carries the RAVEN model fields; anything a plugin added outside them is not guaranteed to survive. Check with a diff, not by eye.
- A release written with `write_sbml_model` diffs badly. `exportForGit` and `export_for_git` sort identifiers, but a direct `write_sbml_model` does not, so a file written that way reorders whenever the model does.
:::

## See also

- [Getting started](getting-started.md), what to do with the model once it is loaded.
- [Guide overview](index.md), the other pages and the planned pages.
- [MATLAB vs Python](../raven3-vs-raven-toolbox.md), the full function mapping, including everything that resolves to cobrapy.
