# RAVEN 2 to RAVEN 3

The calling convention and an upgrade checklist for users of RAVEN 2 follow. Four detail pages follow the checklist. All statements on RAVEN 2 refer to RAVEN 2.11.3. The changelog of RAVEN 3 states its changes relative to RAVEN 2.9.3, so changelog entries may describe differences that are absent from the comparison with 2.11.3. The last RAVEN 2 release, 2.11.4, differs from 2.11.3 by bug fixes in `ftINIT`, `mergeLinear`, `replaceMets`, `checkInstallation`, `importModel`, `readYAMLmodel` and `optimizeProb`. The comparison with the Python package is in [Comparison of RAVEN and raven-toolbox](raven3-vs-raven-toolbox.md).

RAVEN 3 is a breaking release. The codebase was reorganised, functions were removed (counts per subsystem are in [Structure, removals and renames](raven3-migration/structure-and-renames.md)), several external dependencies were dropped and the calling convention for optional arguments changed in the 112 functions that use `parseRAVENargs`. The rationale is in the [v3 development review](https://github.com/CompMetEng/RAVEN/blob/develop/docs/v3_review.md) of the project. Scripts that use reconstruction, KEGG, localisation or gene-deletion functions need a check. The changes that can affect a script are listed in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

:::{admonition} Changes to check first
:class: warning

- The same homology-based or KEGG-based reconstruction call returns a different draft model without an error (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)).
- Scripts that use WoLF PSORT localisation scores raise an error (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
:::

(calling-convention)=
## Calling convention

RAVEN 2 functions took optional arguments by position (`f(model, a, b, c)`). Setting a later optional argument required all earlier optional arguments to be given. In these pages a position N is the position among all arguments of the call, including the required ones: in `f(model, a, b, c)` the model is position 1 and `a` is position 2.

RAVEN 3 has the function `utils/parseRAVENargs.m`, which 112 functions call. The required leading arguments are explicit positional parameters. All optional arguments are collected in `varargin` and can be given by position, by name or in a mix of both:

```matlab
removeReactions(model, rxnList, true, true, true)                       % positional (RAVEN 2 style)
removeReactions(model, rxnList, "removeUnusedGenes", true)              % named
removeReactions(model, rxnList, true, "removeUnusedComps", true)        % hybrid
```

The first string argument that matches a parameter name (case-insensitive) starts the name-value pairs. The arguments before it are positional and are assigned in the order of the `parseRAVENargs` specification of the function. If no argument matches, or the arguments from the first match on are not valid name-value pairs, all arguments are positional. More positional values than the specification has parameters raise `parseRAVENargs:tooManyArgs`. A positional argument that is a string equal to a parameter name has to be given in the name-value form.

An old positional call keeps its meaning when the order of the parameters is unchanged. `importModel`, `exportModel`, `exportToExcelFormat`, `removeReactions`, `addIdentifierPrefix`, `removeIdentifierPrefix` and `exportForGit` have the same parameters in the same order in RAVEN 2 and RAVEN 3. `ftINIT`, `fillGaps`, `fitTasks` and `getModelFromHomology` append new optional parameters after the RAVEN 2 ones. A comparison of all 112 specifications with the RAVEN 2.11.3 signatures found six functions where positional calls change meaning or fail: `getModelFromKEGG`, `getPhylDist`, `getKEGGModelForOrganism`, `scoreModel`, `writeYAMLmodel` and `findGeneDeletions`. Each of them has a row in [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes).

(upgrade-checklist)=
## Upgrade checklist

1. Install RAVEN 3 and run `checkRaven`. It checks the installation type, the MATLAB release, the libSBML version, SBML import and export, the LP solvers, the BLAST+, DIAMOND and HMMER binaries and function names that overlap with other toolboxes. Unless `checkBinaries` is false, `checkRaven` downloads any of the three binaries that is missing (see [Toolbox dependencies and installation](#toolbox-deps)). `checkInstallation` forwards to `checkRaven` and warns on every call.
2. Search the scripts for the functions listed in [Removed functionality](raven3-migration/structure-and-renames.md#removed-functionality) and in [Renamed and merged functions](#renamed-merged-and-consolidated-functions), and replace or remove those calls. The wrappers in `deprecated/` (`makeSomething`, `consumeSomething`, `canProduce`, `canConsume`) and `getINITModel` and `runINIT` work and warn once per session.
3. Rebuild and validate any draft model from `getModelFromKEGG`, `getKEGGModelForOrganism` or `getModelFromHomology`. Default cutoffs, the KEGG data source and the best-hit criterion differ, so an unmodified call gives a different draft (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)). Check positional calls of the six functions listed under [Calling convention](#calling-convention).
4. Convert `.xlsx` curation templates to the `.tsv` format of `curateModelFromTables`. `importExcelModel` does not exist in RAVEN 3 (see [Excel I/O](raven3-migration/formats-and-reconstruction.md#excel-io)).
5. Replace WoLF PSORT scores (`getWoLFScores`, or `parseScores` with `'wolf'`) with DeepLoc 2, MULocDeep, COMPARTMENTS or UniProt. The default predictor of `parseScores` differs (see [Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
6. Re-run task-based gap-filling and context-specific model extraction (`fitTasks`, `checkTasks`, `ftINIT`) and compare the task results. `simplifyModel` keeps the boundary constraint of a task on a metabolite without reactions, which RAVEN 2 removed, so the task check can give a different result in RAVEN 2 and RAVEN 3 (not run; see [Gap-filling and context-specific model extraction](#ftinit)). `fitTasks` returns a third output, `failedTasks`.
7. Expect differences in YAML and SBML files on the next export of a model under version control. The changelog of RAVEN 3 lists changes in quoting, EC-code annotation and ΔG fields; these differences were not compared file by file (see [File formats and model I/O](raven3-migration/formats-and-reconstruction.md#file-formats-and-model-io)).
8. Compare the output of the validation pipeline used for the model (model size, growth rate and task results) with the RAVEN 2 output before using RAVEN 3 results.

## Detail pages

| Page | Content |
|---|---|
| [Structure, removals and renames](raven3-migration/structure-and-renames.md) | The folder reorganisation, every removed function and subsystem, and every renamed or merged function. |
| [Backward-incompatible changes](raven3-migration/backward-incompatible.md) | Changes that raise errors, changes that alter results without an error, changes to error and warning identifiers, changes that raise warnings and installation changes. |
| [File formats, reconstruction and GPR parsing](raven3-migration/formats-and-reconstruction.md) | SBML, Excel and YAML I/O; the KEGG and homology reconstruction pipelines; the grRule parser. |
| [New functionality, dependencies and error handling](raven3-migration/new-and-environment.md) | Gap-filling and ftINIT changes, functions added in RAVEN 3, the toolbox dependency comparison, and error and warning handling. |

```{toctree}
:hidden:

raven3-migration/structure-and-renames
raven3-migration/backward-incompatible
raven3-migration/formats-and-reconstruction
raven3-migration/new-and-environment
```
