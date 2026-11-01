# RAVEN 2 to RAVEN 3

RAVEN 3 is a breaking release. A script written for RAVEN 2 can stop with an error, or run and return a different model. The sections below list what to check first, give the calling convention for optional arguments and provide a checklist for the upgrade. Four detail pages hold the lists.

All statements about RAVEN 2 refer to release 2.11.3. The last RAVEN 2 release, 2.11.4, differs from 2.11.3 by bug fixes in `ftINIT`, `mergeLinear`, `replaceMets`, `checkInstallation`, `importModel`, `readYAMLmodel` and `optimizeProb`. The changelog of RAVEN 3 states its changes relative to RAVEN 2.9.3, so an entry in it can describe a difference that does not exist against 2.11.3. The comparison with the Python package is in [Comparison of RAVEN and raven-toolbox](raven3-vs-raven-toolbox.md).

The codebase was reorganised, functions were removed (counts per folder are in [Structure, removals and renames](raven3-migration/structure-and-renames.md)), several external dependencies were dropped, and 112 functions read their optional arguments through `parseRAVENargs`. The rationale is in the [v3 development review](https://github.com/CompMetEng/RAVEN/blob/develop/docs/v3_review.md). Scripts that call reconstruction, KEGG, localisation or gene-deletion functions need a check. The changes that can affect any script are in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

:::{admonition} Changes to check first
:class: warning

- A homology-based or KEGG-based reconstruction call returns a different draft model without an error (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)).
- A script that uses WoLF PSORT localisation scores raises an error (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
:::

(calling-convention)=
## Calling convention

A RAVEN 2 function took its optional arguments by position, as in `f(model, a, b, c)`, and setting a later optional argument required every earlier one. A position N in these pages is the position among all arguments of the call, required ones included. In `f(model, a, b, c)` the model is position 1 and `a` is position 2.

In RAVEN 3 the function `utils/parseRAVENargs.m` reads the arguments of 112 functions. The required leading arguments are positional parameters. The optional arguments are collected in `varargin` and can be given by position, by name or by both:

```matlab
removeReactions(model, rxnList, true, true, true)                       % positional (RAVEN 2 style)
removeReactions(model, rxnList, "removeUnusedGenes", true)              % named
removeReactions(model, rxnList, true, "removeUnusedComps", true)        % hybrid
```

The first string argument that matches a parameter name, ignoring case, starts the name-value pairs. The arguments before it are positional and are assigned in the order of the `parseRAVENargs` specification of the function. When no argument matches, or the arguments from the first match on are not valid name-value pairs, all arguments are positional. More positional values than the specification has parameters raise `parseRAVENargs:tooManyArgs`. A positional argument whose value is a string equal to a parameter name has to be given in the name-value form.

A positional call keeps its meaning where the parameter order is unchanged. This holds for `importModel`, `exportModel`, `exportToExcelFormat`, `removeReactions`, `addIdentifierPrefix`, `removeIdentifierPrefix` and `exportForGit`. The functions `ftINIT`, `fillGaps`, `fitTasks` and `getModelFromHomology` append new optional parameters after the RAVEN 2 ones, so their old calls also keep their meaning. A comparison of all 112 specifications with the RAVEN 2.11.3 signatures found six functions in which a positional call changes meaning or fails: `getModelFromKEGG`, `getPhylDist`, `getKEGGModelForOrganism`, `scoreModel`, `writeYAMLmodel` and `findGeneDeletions`. Each has a row in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

(upgrade-checklist)=
## Upgrade checklist

1. Install RAVEN 3 and run `checkRaven`. It checks the installation type, the MATLAB release, the libSBML version, SBML import and export, the LP solvers, the BLAST+, DIAMOND and HMMER binaries, and function names that overlap with other toolboxes. Unless `checkBinaries` is false, `checkRaven` downloads any of the three binaries that is missing (see [Toolbox dependencies and installation](#toolbox-deps)). The function `checkInstallation` forwards to `checkRaven` and warns on every call.
2. Search the scripts for the functions in [Removed functionality](raven3-migration/structure-and-renames.md#removed-functionality) and in [Renamed and merged functions](#renamed-merged-and-consolidated-functions), and replace or delete those calls. The wrappers in `deprecated/` (`makeSomething`, `consumeSomething`, `canProduce`, `canConsume`) work and warn once per session, as do `getINITModel` and `runINIT`.
3. Rebuild and validate every draft model from `getModelFromKEGG`, `getKEGGModelForOrganism` or `getModelFromHomology`. The default cut-offs, the KEGG data source and the best-hit criterion differ, so an unchanged call gives a different draft (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)). Check the positional calls of the six functions in [Calling convention](#calling-convention).
4. Convert `.xlsx` curation templates to the `.tsv` format of `curateModelFromTables`. The function `importExcelModel` does not exist in RAVEN 3 (see [Excel I/O](raven3-migration/formats-and-reconstruction.md#excel-io)).
5. Replace WoLF PSORT scores (`getWoLFScores`, or `parseScores` with `'wolf'`) with DeepLoc 2, MULocDeep, COMPARTMENTS or UniProt. The default predictor of `parseScores` differs (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
6. Run task-based gap-filling and context-specific model extraction (`fitTasks`, `checkTasks`, `ftINIT`) with RAVEN 3 and compare the task results. `simplifyModel` keeps the boundary constraint of a task on a metabolite without reactions, which RAVEN 2 removed, so the task check can give a different result in RAVEN 2 and RAVEN 3. The difference in the task check was not run (see [Gap-filling and context-specific model extraction](#ftinit)). The function `fitTasks` returns a third output, `failedTasks`.
7. Expect differences in YAML and SBML files on the next export of a model under version control. The changelog of RAVEN 3 lists changes in quoting, EC-code annotation and ΔG fields. These differences were not compared file by file (see [File formats and model I/O](raven3-migration/formats-and-reconstruction.md#file-formats-and-model-io)).
8. Compare the output of the validation pipeline of the model (model size, growth rate and task results) between RAVEN 2 and RAVEN 3 before using RAVEN 3 results.

## Detail pages

| Page | Content |
|---|---|
| [Structure, removals and renames](raven3-migration/structure-and-renames.md) | The folder reorganisation, every removed function and folder, and every renamed or merged function. |
| [Backward-incompatible changes](raven3-migration/backward-incompatible.md) | Changes that raise errors, changes that alter results without an error, changes to error and warning identifiers, changes that raise warnings, and installation changes. |
| [File formats, reconstruction and GPR parsing](raven3-migration/formats-and-reconstruction.md) | SBML, Excel and YAML I/O, the KEGG and homology reconstruction pipelines, and the grRule parser. |
| [New functionality, dependencies and error handling](raven3-migration/new-and-environment.md) | Gap-filling and ftINIT changes, functions added in RAVEN 3, the toolbox dependency comparison, and error and warning handling. |

```{toctree}
:hidden:

raven3-migration/structure-and-renames
raven3-migration/backward-incompatible
raven3-migration/formats-and-reconstruction
raven3-migration/new-and-environment
```
