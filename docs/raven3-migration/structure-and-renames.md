# Structure, removals and renames

RAVEN 3 organises functions in folders named by function area, removes RAVEN 2 functions and subsystems, and renames or merges other functions.

## Repository reorganisation

RAVEN 3 replaces the top-level layout of RAVEN 2 (`core/`, `external/`, `hpa/`, `io/`, `legacy/`, `pathway/`, `plotting/`, `solver/`, `struct_conversion/`, `installation/`, `utils/`) with folders named by function area:

| RAVEN 3 folder | Contents | RAVEN 2 source |
|---|---|---|
| `INIT/` | `ftINIT`, `INIT/tINIT/` for `getINITModel` and `runINIT`, and HPA parsing, expression parsing and gene scoring (`parseHPA`, `parseHPArna`, `scoreModel`) | `INIT/`, `hpa/` |
| `analysis/` | Analyses related to flux balance analysis (FBA): flux variability analysis (FVA), sampling, FSEOF, OptKnock, robustness, production envelope, flux comparison and tracing | `core/` |
| `annotation/` | MIRIAM editing, SBO term assignment, ΔG CSV I/O | `struct_conversion/` (and new functions) |
| `biomass/` | Biomass composition fitting and scaling, growth-associated maintenance (GAM) | `core/` (and new functions) |
| `comparison/` | Multi-model comparison, structured model diffing | `core/` (and new functions) |
| `conditions/` | Applying a data-driven growth or media condition to a model | New folder |
| `conversion/` | RAVEN⇄COBRA conversion, identifier prefixing, field ordering | `struct_conversion/` |
| `curation/` | Genome-annotation-driven gene and model curation | New folder |
| `external/` | Bundled third-party code (GLPKmex, libSBML, SCIP and m2html) and the download target of the BLAST+, DIAMOND and HMMER binaries | `external/` |
| `gapfilling/` | `fillGaps` and its pluggable algorithms, task fitting, leak-metabolite and exchange checks | `core/` (and new functions) |
| `installation/` | Path setup, on-demand binary and data download | `installation/` |
| `io/` | Model import and export (SBML, YAML, Excel), FASTA I/O | `io/` |
| `localization/` | Subcellular localisation prediction and scoring, compartment assignment | `external/` (and new functions) |
| `manipulation/` | Structural edits: add, remove and change reactions, metabolites and genes; merge, sort, simplify | `core/` |
| `queries/` | Non-mutating lookups: indexes, exchange and transport reactions, stoichiometry construction, model checking | `core/` |
| `reconstruction/` | KEGG- and homology-based draft reconstruction | `external/` |
| `solver/` | LP and MILP solving | `solver/` |
| `tasks/` | Metabolic task list parsing and checking | `core/` |
| `tests/function_tests/` (repository root, outside `src/`) | `matlab.unittest` suite | `testing/` |
| `utils/` | Generic helpers, including the new argument-parsing and registry infrastructure | `utils/` |
| `deprecated/` | Wrappers for merged and renamed functions | New folder |

Removed without a successor folder: the subfolder `external/metacyc/` (MetaCyc reconstruction; `external/` itself remains), `pathway/` and `plotting/` (visualisation), `legacy/` (CellDesigner import and other pre-2.0 code), and the Excel-POI helpers of `struct_conversion/`.

A script that calls RAVEN functions by name keeps working when the whole RAVEN folder tree, including subfolders, is on the MATLAB path (through `addRavenToUserPath` or `addpath(genpath(...))`), except for calls to removed functions and to merged functions without a wrapper. MATLAB resolves functions by name across the whole path, so moving a file to a new subfolder does not break the call. The reorganisation affects a script that (a) uses a hard-coded path to a specific `.m` file, (b) calls a removed function or a merged function without a wrapper, or (c) shadows a RAVEN function name with its own function.

The full mapping of moved files (RAVEN 2 path to RAVEN 3 path) is not reproduced here because it is large and rarely something that needs action in a script.

---

(removed-functionality)=
## Removed functionality

RAVEN 3 removed the functions and subsystems in the table to make the codebase smaller. None of them has a call site left in RAVEN 3.

| Removed | Former purpose | Replacement |
|---|---|---|
| `pathway/*`, `plotting/*` (16 functions, such as `drawMap`, `drawPathway`, `colorPathway`, `colorSubsystem`, `markPathwayWithFluxes`, `markPathwayWithExpression`, `setOmicDataToRxns` and `plotAdditionalInfo`) | Metabolic map and pathway visualisation | None in RAVEN 3. Alternatives are the COBRA Toolbox, Escher and export of flux and omics data for external plotting. |
| `external/metacyc/*` (7 functions: `getModelFromMetaCyc`, `getRxnsFromMetaCyc`, `getMetsFromMetaCyc`, `getEnzymesFromMetaCyc`, `addSpontaneousRxns`, `linkMetaCycKEGGRxns`, `combineMetaCycKEGGModels`) | MetaCyc-based draft reconstruction | None; KEGG- and homology-based reconstruction remain the supported reconstruction methods. |
| `legacy/*` (CellDesigner import, `changeGeneAssoc`, the bundled `xml_toolbox`) | Pre-2.0 compatibility code | None; considered dead. |
| `io/importExcelModel.m`, `io/loadWorkbook.m`, `io/loadSheet.m`, `io/writeSheet.m`, `io/SBMLFromExcel.m`, `io/addJavaPaths.m`, `io/startup.m` | Apache-POI-based Excel model I/O | `io/writeExcel.m` (dependency-free OOXML writer) for export; `curation/curateModelFromTables.m` for tabular curation. No full Excel-template import remains; see [Excel I/O](#excel-io). |
| `io/exportModelToSIF.m`, `io/exportToTabDelimited.m` | SIF graph export; tab-delimited model export | Dead or orphaned code with no callers. |
| `io/getFullPath.m`, `io/getMD5Hash.m`, `io/getToolboxVersion.m` | Path canonicalisation; file MD5 hashing; toolbox git-version lookup | Inlined where still needed (for example MD5 via Java's `MessageDigest` inside `getBlast`), or merged into `exportForGit`. |
| `core/dispEM.m` | Universal error and warning display | Native `warning()` and `error()` plus new `utils/ravenList.m` for formatted item lists. See [Backward-incompatible changes](#backward-incompatible-changes). |
| `core/followFluxes.m`, `core/followChanged.m` | Flux-change reporting relative to a reference solution | `queries/printFluxes.m` covers the cutoff filtering; nothing directly replaces the reference-flux comparison. |
| `core/printModel.m` | Printed reactions to screen or file | `queries/printModelStats.m` and `queries/printFluxes.m` cover related summary and flux printing (see the note below the table). |
| `core/getMetsInComp.m` | Returned metabolite indices in a given compartment | Inline it as `model.metComps == compIndex`. |
| `core/mapCompartments.m` | Merged and split the score columns of a localisation-score structure by compartment rules | Superseded by the `compartmentMap` option of `parseScores` and `getUniProtScores` (default `defaultCompartmentMap`); merged columns take the maximum score, and splitting is not supported. |
| `core/getExpressionStructure.m` | Loaded an expression-experiment structure from an ad hoc Excel format | Superseded by `INIT/parseHPA.m` and `INIT/parseHPArna.m` for the supported expression-data workflow. |
| `core/checkRxn.m` | Per-reaction reactant and product synthesisability debugging | No direct successor; use `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` or `gapfilling/checkProduction.m`. |
| `external/getWoLFScores.m` | WoLF PSORT score parsing | None; see [Backward-incompatible changes](#backward-incompatible-changes). |
| `external/kegg/{getGenesFromKEGG,getMetsFromKEGG,getRxnsFromKEGG,constructMultiFasta,getWSLpath}.m`, `external/getBlastFromExcel.m` | Local-KEGG-FTP-dump parsing; per-KO multi-FASTA assembly; WSL path translation; Excel-based BLAST import | Superseded by the KEGG pipeline based on `toolbox-assets` artefacts. See [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction). |
| `solver/qMOMA.m`, `solver/solveQP.m` | MOMA-based analyses (quadratic programming) | Removed; RAVEN 3 has no replacement based on quadratic programming. See [Backward-incompatible changes](#backward-incompatible-changes) for the arguments removed from `findGeneDeletions`. |
| `testing/unit_tests/*.m` (script-based tests) | Ad hoc test scripts | `tests/function_tests/*.m` in the repository root, a `matlab.unittest`-class-based suite. Relevant to contributors only; `runRAVENtests` usage is unchanged for end users. |

`printFluxes` prints the reactions of a flux vector with an absolute flux at or above `cutOffFlux` (default `10^-8`), one line per reaction; it prints exchange reactions only unless `onlyExchange` is `false`. A dump of all reactions of a model without fluxes has no direct replacement.

---

(renamed-merged-and-consolidated-functions)=
## Renamed and merged functions

RAVEN 3 introduces the `deprecated/` folder convention. In `deprecated/`, `makeSomething`, `consumeSomething`, `canProduce` and `canConsume` stay callable under their old names as wrappers that issue a one-time `RAVEN:deprecated` warning ("will be removed in the next major release") and forward to the new function. The other functions in the table have no wrapper, except `checkInstallation`, which has its own row.

| RAVEN 2 functions | RAVEN 3 function | Notes |
|---|---|---|
| `makeSomething(model, ignoreMets, isNames, minNrFluxes, allowExcretion, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'produce', ...)` | Argument order maps 1:1; the wrapper forwards `varargin` unchanged. |
| `consumeSomething(model, ignoreMets, isNames, minNrFluxes, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'consume', ...)` | The old positional order of `consumeSomething` has no `allowExcretion` slot, so the wrapper remaps the arguments by name to keep `params` and `ignoreIntBounds` intact. |
| `canProduce(model, mets)` | `canExchange(model, 'produce', 'mets', mets)` | None. |
| `canConsume(model, mets)` | `canExchange(model, 'consume', 'mets', mets)` | None. |
| `compareRxnsGenesMetsComps` | Merged into `comparison/compareMultipleModels.m` | The reaction, gene, metabolite and compartment overlap output is one part of the output of `compareMultipleModels`; no separate function or wrapper remains. |
| `INIT/scoreComplexModel.m` | `INIT/scoreModel.m` | Merged; no wrapper remains. |
| `INIT/ftINITFillGapsMILP.m` | Merged into `solver/getMinNrFluxes.m` | Available through the `resolveTies` option of `getMinNrFluxes`; the `proveAbsGap` option belongs to `ftINIT`. |
| `INIT/ftINITFillGapsForAllTasks.m` | Merged into `gapfilling/ftINITFillGaps.m` and the `'preMerged'` gap-fill mode of `fitTasks` | None. |
| `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` | `reconstruction/kegg/readKEGGTable.m` and the `toolbox-assets` KEGG artefacts | The data source changed, so the signatures are not compatible; see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction). |
| `core/parallelPoolRAVEN.m` | `utils/parallelWorkersRAVEN.m` | Parallel Computing Toolbox pool setup, renamed and rewritten. `parallelWorkersRAVEN` returns a `parfor` worker count (`0` or `Inf`) and starts no pool; the old function returned `[ps, oldPoolAutoCreate]`. |
| `checkInstallation` | `checkRaven` | Moved from `installation/checkInstallation.m` to `checkRaven.m` in the repository root; the calling signature is identical. `checkInstallation` remains as a deprecated forwarding wrapper that issues a `RAVEN:deprecated` warning. |

RAVEN 2 had both `INIT/scoreComplexModel.m` and `hpa/scoreModel.m`; RAVEN 3 merged them into one `scoreModel`, called with different settings from tINIT than from ftINIT. A RAVEN 2 call to `scoreModel` (`hpa/scoreModel.m`, checked against v2.11.3) changes: RAVEN 2 scored a reaction by the best or average score over all its genes (`multipleGeneScoring`), while RAVEN 3 applies `isozymeScoring` (default `'max'`) to the `or` parts and `complexScoring` (default `'min'`) to the `and` parts of the rule. A reaction with an `and` rule therefore receives a different default score. The positional arguments after `noGeneScore` changed: the 7th to 9th arguments of a RAVEN 2 call (`multipleGeneScoring`, `multipleCellScoring`, `hpaLevelScores`) are read as `isozymeScoring`, `complexScoring` and `multipleCellScoring`, `multipleCellScoring` accepts `'max'` and `'average'` (RAVEN 2: `'best'` and `'average'`), and `hpaLevelScores` becomes the 10th positional argument. RAVEN 3 adds `dataPrecedence` (default `'gene'`); see [Backward-incompatible changes](#backward-incompatible-changes). A call to `scoreComplexModel` has to move to `scoreModel` and pass the settings that reproduce the old behaviour (a single operator for both `and` and `or`, `dataPrecedence` `'reaction'`).

`getINITModel` and `runINIT` (under `INIT/tINIT/`) are marked legacy but supported indefinitely; unlike the functions in `deprecated/`, they are not scheduled for removal. `utils/legacyMethodNotice.m` issues a one-time, silenceable `RAVEN:legacyMethod` warning that points to `ftINIT`. Use `ftINIT` for new work; keep `getINITModel` and `runINIT` only to reproduce models originally built with them.
