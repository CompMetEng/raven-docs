# RAVEN 2 to RAVEN 3

RAVEN 3 changes the MATLAB toolbox in four areas: the folder structure with its removed and renamed functions, backward-incompatible behaviour, file formats and reconstruction pipelines, and new functionality with its dependencies. The calling convention and an upgrade checklist for users of RAVEN 2 follow. The page was compared with RAVEN 2.11.3. The comparison with the Python package is in [Comparison of RAVEN and raven-toolbox](raven3-vs-raven-toolbox.md).

RAVEN 3 is a deliberate breaking release. The codebase was reorganised, low-value and duplicate functions were removed, several external dependencies were dropped and the calling convention for optional arguments changed in the 112 functions that use `parseRAVENargs`. The rationale is in the [v3 development review](https://github.com/CompMetEng/RAVEN/blob/develop/docs/v3_review.md) of the project. Most non-trivial RAVEN 2 scripts need to be checked; the core reconstruction and analysis behaviour is mostly the same. The changes that can affect a script are listed in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

:::{admonition} Changes to check first
:class: important

Two changes are most likely to affect existing scripts:

- The same homology-based or KEGG-based reconstruction call returns a different draft model, without an error (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)).
- WoLF PSORT-based localisation scores raise an error and have no in-toolbox migration path (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
:::

---

(calling-convention)=
## Calling convention: positional or named arguments

RAVEN 2 functions took optional arguments strictly positionally (`f(model, a, b, c)`). A later optional argument could be set only by specifying all optional arguments before it.

RAVEN 3 introduces `utils/parseRAVENargs.m`, called by 112 functions. Required leading arguments stay explicit positional parameters; all optional arguments are collected into `varargin` and can be supplied in three interchangeable ways:

```matlab
removeReactions(model, rxnList, true, true, true)                       % positional (RAVEN 2 style, still works)
removeReactions(model, rxnList, "removeUnusedGenes", true)              % named
removeReactions(model, rxnList, true, "removeUnusedComps", true)        % hybrid
```

The first string argument that matches a parameter name starts the name-value pairs. The arguments before it are positional, assigned in the order declared in the `parseRAVENargs` specification, and everything from it on is read as name-value pairs. If no argument matches, or the arguments from the first match on are not valid name-value pairs, all arguments are positional.

Old positional calls keep working if the new parameter order still matches the old positional order. In 11 functions (`importModel`, `exportModel`, `exportToExcelFormat`, `removeReactions`, `ftINIT`, `fillGaps`, `fitTasks`, `getModelFromHomology`, `addIdentifierPrefix`, `removeIdentifierPrefix` and `exportForGit`) new optional parameters follow the RAVEN 2 ones, so old positional calls keep working unchanged. The old order is kept in the 11 functions checked above. A comparison of all 112 `parseRAVENargs` specifications with the RAVEN 2.11.3 signatures found these exceptions:

- `getModelFromKEGG` and `getPhylDist` lost the leading `keggPath`, and `getKEGGModelForOrganism` lost `nSequences` and `seqIdentity`, so later positional arguments shift.
- `scoreModel` has new `isozymeScoring`, `complexScoring` and `dataPrecedence` parameters in the middle of the list.
- `writeYAMLmodel` had `(model, fileName, preserveQuotes, sortIds)` and has `(model, fileName, sortIds)`.
- `findGeneDeletions` lost `analysisType`, `refModel` and `oeFactor`.

Each exception and its effect is a row in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

A positional argument that is itself a string matching a parameter name needs the name-value form to avoid ambiguity.

---

(upgrade-checklist)=
## Upgrade checklist

1. Update to RAVEN 3.0.0 (or later) and run `checkRaven` (replaces `checkInstallation`). The checks include the installation type, the MATLAB release, the libSBML version, the SBML import and export, the LP solvers, the BLAST+, DIAMOND and HMMER binaries and function names that overlap with other toolboxes. `checkRaven` downloads any of the three binaries that is missing (see [Toolbox dependencies and installation](#toolbox-deps)).
2. Search the scripts for the functions listed in [Removed functionality](raven3-migration/structure-and-renames.md#removed-functionality) and in [Renamed and merged functions](#renamed-merged-and-consolidated-functions), and update or remove those calls.
3. If scripts use `getModelFromKEGG`, `getKEGGModelForOrganism` or `getModelFromHomology`, the draft reconstruction can differ even from an unmodified call: default cutoffs, the KEGG data source and the homology best-hit criterion changed (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)). Rebuild and re-validate any KEGG-derived or homology-derived draft models. Positional calls of the KEGG functions also need a check, because the argument positions shifted (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
4. If `.xlsx` curation templates or `importExcelModel` are used, convert the curation data to the `.tsv` format that `curateModelFromTables` expects; there is no drop-in Excel importer (see [Excel I/O](raven3-migration/formats-and-reconstruction.md#excel-io)).
5. If scripts use WoLF PSORT localisation scores (`getWoLFScores(...)` or `parseScores` with `'wolf'` or without a predictor), switch to DeepLoc 2, MULocDeep, COMPARTMENTS or UniProt. There is no in-toolbox migration path for existing WoLF PSORT output files (see [New functionality](#new-functionality)).
6. If workflows include metabolic-task gap-filling (`fitTasks`, `checkTasks`, `ftINIT`), re-run them and check the task pass and fail results. A fixed bug means that a task previously reported as passing can now fail (see [Gap-filling and context-specific model extraction](#ftinit)).
7. If model files are under version control (YAML or SBML), diffs can appear on the next export even without content changes (quoting style, EC-code annotation and ΔG fields; see [File formats and model I/O](raven3-migration/formats-and-reconstruction.md#file-formats-and-model-io)).
8. Re-run the test suite or validation pipeline of the project and compare the outputs (model size, growth rate and task results) with the RAVEN 2 baseline before using RAVEN 3 results in production.

---

## Detail pages

| Page | Content |
|---|---|
| [Structure, removals and renames](raven3-migration/structure-and-renames.md) | The folder reorganisation, every removed function and subsystem, and every renamed or merged function. |
| [Backward-incompatible changes](raven3-migration/backward-incompatible.md) | Changes that raise errors, changes that alter results without an error, changes to error and warning identifiers, changes that raise warnings and installation changes. |
| [File formats, reconstruction and GPR parsing](raven3-migration/formats-and-reconstruction.md) | SBML, Excel and YAML I/O; the KEGG and homology reconstruction pipelines; the new grRule parser. |
| [New functionality, dependencies and error handling](raven3-migration/new-and-environment.md) | Gap-filling and ftINIT changes, functions added in RAVEN 3, the toolbox dependency comparison, and error and warning handling. |

```{toctree}
:hidden:

raven3-migration/structure-and-renames
raven3-migration/backward-incompatible
raven3-migration/formats-and-reconstruction
raven3-migration/new-and-environment
```
