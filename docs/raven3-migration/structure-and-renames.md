# Structure, removals and renames

RAVEN 3 organises functions in folders named by function area, removes 65 RAVEN 2 functions, merges or renames 8 functions, and keeps 5 RAVEN 2 names as wrappers.

## Repository reorganisation

The RAVEN 3 code is in `src/`. RAVEN 2 kept its functions in the top-level folders `core/`, `external/`, `INIT/`, `hpa/`, `io/`, `legacy/`, `pathway/`, `plotting/`, `solver/`, `struct_conversion/`, `installation/` and `utils/`, and its bundled third-party code in `software/`. Other top-level folders changed as well: `software/` third-party code is in `src/external/`, `tutorial/` is `tutorials/`, `doc/` is `docs/`, and `testing/` is `tests/function_tests/`.

| RAVEN 3 folder (under `src/`) | Contents | RAVEN 2 source |
|---|---|---|
| `INIT/` | `ftINIT`, `INIT/tINIT/` for `getINITModel` and `runINIT`, and HPA parsing, expression parsing and gene scoring (`parseHPA`, `parseHPArna`, `scoreModel`) | `INIT/`, `hpa/` |
| `analysis/` | Analyses related to flux balance analysis (FBA): flux variability analysis (FVA), sampling, FSEOF, OptKnock, robustness, production envelope, flux comparison and tracing | `core/` |
| `annotation/` | MIRIAM editing, SBO term assignment, ΔG CSV I/O | `struct_conversion/` (and new functions) |
| `biomass/` | Biomass composition fitting and scaling, growth-associated maintenance (GAM) | `core/` (and new functions) |
| `comparison/` | Multi-model comparison, structured model diffing | `core/` (and new functions) |
| `conditions/` | Applying a data-driven growth or media condition to a model | New folder |
| `conversion/` | RAVEN⇄COBRA conversion, identifier prefixing, field ordering | `struct_conversion/` |
| `curation/` | Genome-annotation-driven gene and model curation | New folder |
| `external/` | Bundled third-party code (GLPKmex, libSBML and m2html) and the download target of the BLAST+, DIAMOND and HMMER binaries (`src/external/<tool>`). `src/external/scip/` holds no files; `setRavenSolver('scip')` downloads the SCIP MEX file there on Windows (see [Toolbox dependencies and installation](#toolbox-deps)) | `software/` |
| `gapfilling/` | `fillGaps` and its pluggable algorithms, task fitting, leak-metabolite and exchange checks | `core/`, `INIT/` (and new functions) |
| `installation/` | Path setup, on-demand binary and data download | `installation/`, `core/` (`findRAVENroot`), `external/` (`updateDocumentation`) |
| `io/` | Model import and export (SBML, YAML, Excel), FASTA I/O | `io/` (and new functions) |
| `localization/` | Subcellular localisation prediction and scoring, compartment assignment | `external/`, `core/` (`predictLocalization`) (and new functions) |
| `manipulation/` | Structural edits: add, remove and change reactions, metabolites and genes; merge, sort, simplify | `core/`, `io/` (`closeModel`, `sortIdentifiers`), `INIT/` (`removeLowScoreGenes`, `reverseRxns`) |
| `queries/` | Non-mutating lookups: indexes, exchange and transport reactions, stoichiometry construction, model checking | `core/` (and new functions) |
| `reconstruction/` | KEGG- and homology-based draft reconstruction | `external/`, `core/` (`getModelFromHomology`, `guessComposition`) |
| `solver/` | LP and MILP solving | `solver/`, `core/` (`getMinNrFluxes`) (and new functions) |
| `tasks/` | Metabolic task list parsing and checking | `core/` |
| `utils/` | Generic helpers, including the argument-parsing and registry infrastructure | `utils/`, `core/` (`convertCharArray`, `printOrange`) |
| `deprecated/` | Wrappers for merged and renamed functions | New folder |
| `tests/function_tests/` (repository root, outside `src/`) | Class-based `matlab.unittest` suite (23 of 25 classes derive from `RavenTestCase`; `tBinaries` and `tParseRAVENargs` derive from `matlab.unittest.TestCase`) | `testing/` (function-based tests built with `functiontests`) |

`checkRaven.m` and the wrapper `checkInstallation.m` are in the repository root.

Removed without a successor folder: the subfolder `external/metacyc/` and the MetaCyc function `external/combineMetaCycKEGGModels.m`, `pathway/` and `plotting/` (visualisation), `legacy/` (CellDesigner import and other pre-2.0 code), and the Excel-POI helpers of `io/` together with the Apache POI libraries of `software/apache-poi`.

A script that calls RAVEN functions by name works when the whole RAVEN folder tree, including subfolders, is on the MATLAB path (through `addRavenToUserPath` or `addpath(genpath(...))`), because MATLAB resolves functions by name across the path. The reorganisation affects a script that uses a hard-coded path to a specific `.m` file, calls a removed function or a merged function without a wrapper, or contains its own function with the same name as a RAVEN 3 function. `checkFunctionUniqueness` warns about the last case.

The mapping of every moved file is not listed.

---

(removed-functionality)=
## Removed functionality

The table lists all 65 RAVEN 2 functions that RAVEN 3 removes without a successor of the same name. The numbers per RAVEN 2 folder are: `pathway/` 6, `plotting/` 10, `external/` 12 (8 MetaCyc, 4 others), `legacy/` 11, `io/` 12, `core/` 8, `utils/` 3, `solver/` 2 and `INIT/` 1. A function of RAVEN 3 calls no removed function; the name `getToolboxVersion` remains as a local function `getToolboxVersion` in `exportForGit`.

| Removed | Former purpose | Replacement |
|---|---|---|
| `pathway/colorPathway`, `pathway/getPathwayDimensions`, `pathway/mapPathwayRxnNames`, `pathway/markPathwayWithExpression`, `pathway/markPathwayWithFluxes`, `pathway/trimPathway` (6 functions) | Metabolic pathway map handling and colouring | None in RAVEN 3. Alternatives are the COBRA Toolbox, Escher and export of flux and omics data for external plotting. |
| `plotting/colorSubsystem`, `plotting/drawMap`, `plotting/drawPathway`, `plotting/getColorCodes`, `plotting/getObjectiveString`, `plotting/plotAdditionalInfo`, `plotting/plotLabels`, `plotting/setColorToMapRxns`, `plotting/setOmicDataToRxns`, `plotting/setTitle` (10 functions) | Metabolic map drawing and omics colouring | None, as above. |
| `external/metacyc/{getModelFromMetaCyc,getRxnsFromMetaCyc,getMetsFromMetaCyc,getEnzymesFromMetaCyc,getMetaCycModelForOrganism,addSpontaneousRxns,linkMetaCycKEGGRxns}`, `external/combineMetaCycKEGGModels` (8 functions) | MetaCyc-based draft reconstruction | None; KEGG- and homology-based reconstruction are the reconstruction methods of RAVEN 3. |
| `legacy/core/changeGeneAssoc`, `legacy/external/constructPathwayFromCelldesigner`, and the nine functions of the bundled `xml_toolbox` (`xml_format`, `xml_formatany`, `xml_help`, `xml_load`, `xml_parse`, `xml_parseany`, `xml_save`, `xml_strsplit`, `xml_unblank`) (11 functions) | CellDesigner import and pre-2.0 compatibility code | None. |
| `io/importExcelModel`, `io/loadWorkbook`, `io/loadSheet`, `io/writeSheet`, `io/SBMLFromExcel`, `io/addJavaPaths`, `io/startup` (7 functions) | Apache-POI-based Excel model I/O | `io/writeExcel.m` (dependency-free OOXML writer) for export; `curation/curateModelFromTables.m` for tabular curation. There is no full Excel-template import; see [Excel I/O](#excel-io). |
| `io/exportModelToSIF`, `io/exportToTabDelimited` | SIF graph export; tab-delimited model export | None. The sole caller of `exportToTabDelimited` was the bare-path fallback of `exportToExcelFormat`, which is removed. |
| `io/getFullPath`, `io/getMD5Hash`, `io/getToolboxVersion` | Path canonicalisation; file MD5 hashing; toolbox git-version lookup | Inlined where needed: the MD5 hash through Java `MessageDigest` in `getBlast`, the version lookup as a local function of `exportForGit`. |
| `core/dispEM` | Error and warning display (388 lines call it in RAVEN 2, counted outside `doc/` and `testing/`) | Native `warning()` and `error()`, and `utils/ravenList.m` for formatted item lists. See [Backward-incompatible changes](#backward-incompatible-changes). |
| `core/followFluxes`, `core/followChanged` | Flux-change reporting relative to a reference solution | `analysis/compareFluxes.m` compares two flux vectors of one model (reactions turned on or off, flipped and changed, with `cutoff` and `metaboliteList`), which replaces `core/followChanged`; `queries/printFluxes.m` prints the fluxes of one vector above a cutoff. |
| `core/printModel` | Printed reactions to screen or file | `queries/printModelStats.m` and `queries/printFluxes.m` cover model summaries and flux printing (see below the table). |
| `core/getMetsInComp` | Metabolite indices in a compartment | `model.metComps == compIndex` |
| `core/mapCompartments` | Merged and split the score columns of a localisation-score structure by compartment rules | The `compartmentMap` option of `parseScores` and `getUniProtScores`. The default map `defaultCompartmentMap` applies to `getUniProtScores` and to `parseScores` with the `'uniprot'` predictor; elsewhere, without a map, every label stays unchanged. With a map, a label that the map does not contain is dropped together with its score column. Merged columns take the maximum score; splitting is not supported. |
| `core/getExpressionStructure` | Loaded an expression structure from an ad hoc Excel format | `INIT/parseHPA.m` and `INIT/parseHPArna.m` read Human Protein Atlas files. Expression tables from other sources have to be assembled by hand as the `arrayData` structure documented in `scoreModel`. |
| `core/checkRxn` | Per-reaction synthesisability debugging | No direct successor; `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` and `gapfilling/checkProduction.m` cover related checks. |
| `external/getWoLFScores` | WoLF PSORT score parsing | None; `parseScores` with `'wolf'` raises `RAVEN:badInput`. See [Backward-incompatible changes](#backward-incompatible-changes). |
| `external/kegg/constructMultiFasta`, `external/kegg/getWSLpath`, `external/getBlastFromExcel` | Per-KO multi-FASTA assembly; WSL path translation; Excel-based BLAST import | The KEGG pipeline based on `toolbox-assets` artefacts. See [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction). |
| `solver/qMOMA`, `solver/solveQP` | MOMA analyses and quadratic programming | None; RAVEN 3 has no quadratic programming. See [Backward-incompatible changes](#backward-incompatible-changes) for the arguments removed from `findGeneDeletions`. |
| `utils/emptyOrLogicalScalar`, `utils/emptyOrTextOrCellOfText`, `utils/emptyOrTextScalar` | Argument validators | `utils/parseRAVENargs.m` |
| `INIT/getExprForRxnScore` | Reaction scores from expression data | A private helper of the test suite in `tests/function_tests/private/` |

`printFluxes` prints the reactions of a flux vector with an absolute flux at or above `cutOffFlux` (default `10^-8`), one line per reaction; it prints exchange reactions unless `onlyExchange` is `false`. A listing of all reactions of a model without fluxes has no direct replacement.

---

(renamed-merged-and-consolidated-functions)=
## Renamed and merged functions

The `deprecated/` folder holds `makeSomething`, `consumeSomething`, `canProduce` and `canConsume`. These wrappers keep the RAVEN 2 names callable, issue a `RAVEN:deprecated` warning once ("will be removed in the next major release") and forward to the RAVEN 3 function. The other functions in the table have no wrapper, except `checkInstallation`, which has its own row.

| RAVEN 2 functions | RAVEN 3 function | Notes |
|---|---|---|
| `makeSomething(model, ignoreMets, isNames, minNrFluxes, allowExcretion, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'produce', ...)` | The argument order maps one to one; the wrapper forwards `varargin` unchanged. |
| `consumeSomething(model, ignoreMets, isNames, minNrFluxes, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'consume', ...)` | The RAVEN 2 argument order has no `allowExcretion` position, so the wrapper remaps the arguments by name to keep `params` and `ignoreIntBounds`. |
| `canProduce(model, mets)` | `canExchange(model, 'produce', 'mets', mets)` | None. |
| `canConsume(model, mets)` | `canExchange(model, 'consume', 'mets', mets)` | None. |
| `compareRxnsGenesMetsComps` | `comparison/compareMultipleModels.m` | The overlap output of RAVEN 2 (reactions, genes, metabolites, EC codes, metabolite names, equations and unique equations) is part of the output of `compareMultipleModels`. No wrapper. |
| `INIT/scoreComplexModel.m` | `INIT/scoreModel.m` | Merged; no wrapper. A call moves to `scoreModel` with the same positions and defaults for the first six optional arguments; `dataPrecedence` is added as the 7th optional argument. |
| `INIT/ftINITFillGapsMILP.m` | `solver/getMinNrFluxes.m` | Available through the `resolveTies` option of `getMinNrFluxes`, which is implemented for `formulation` `'reversible'` only (the default `'irrev'` raises an error with `resolveTies`); the `proveAbsGap` option belongs to `ftINIT`. |
| `INIT/ftINITFillGapsForAllTasks.m` | `gapfilling/ftINITFillGaps.m` and the `'preMerged'` gap-fill mode of `fitTasks` | None. `ftINITFillGaps` exists in RAVEN 2 as well. |
| `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` | `reconstruction/kegg/readKEGGTable.m` (with `buildGlobalKEGGModel` and `buildGlobalGPR`) and the `toolbox-assets` KEGG artefacts | The data source differs, so the signatures are not compatible; see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction). |
| `core/parallelPoolRAVEN.m` | `utils/parallelWorkersRAVEN.m` | `parallelWorkersRAVEN` returns a `parfor` worker count (`0` or `Inf`) and starts no pool; `parallelPoolRAVEN` returns `[ps, oldPoolAutoCreate]`. |
| `installation/checkInstallation.m` | `checkRaven.m` in the repository root | The calling signature is identical. `checkInstallation.m` in the repository root forwards to `checkRaven` and issues a `RAVEN:deprecated` warning on every call. |

### Gene scoring with `scoreModel`

RAVEN 2 has `INIT/scoreComplexModel.m` and `hpa/scoreModel.m`; RAVEN 3 has one `scoreModel`, which tINIT and ftINIT call with different settings. Differences for a call written for `hpa/scoreModel.m` (checked against v2.11.3):

- RAVEN 2 scored a reaction by the best or average score over all its genes (`multipleGeneScoring`, values `'best'` and `'average'`). RAVEN 3 applies `isozymeScoring` (default `'max'`) to the `or` parts and `complexScoring` (default `'min'`) to the `and` parts of the rule. A reaction with an `and` rule receives a different default score.
- Positions count all arguments of the call. The 7th to 9th arguments of a RAVEN 2 call (`multipleGeneScoring`, `multipleCellScoring`, `hpaLevelScores`) are read as `isozymeScoring`, `complexScoring` and `multipleCellScoring`; `hpaLevelScores` is the 10th argument.
- `multipleCellScoring` accepts `'max'` and `'average'` (RAVEN 2: `'best'` and `'average'`).
- `dataPrecedence` is an argument of RAVEN 3 with the default `'gene'`.
- Genes that are absent from the data receive `NaN` in `geneScores`; the RAVEN 2 documentation states `-Inf`. `getINITModel` converts `NaN` back to `-Inf`.

See [Backward-incompatible changes](#backward-incompatible-changes). `getINITModel` passes `'max'` for both `isozymeScoring` and `complexScoring` and `'reaction'` for `dataPrecedence`. Whether these settings reproduce the scores of the RAVEN 2 `hpa/scoreModel` was not checked; the RAVEN 2 value `'average'` for `multipleGeneScoring` has no equivalent among them.

### Legacy tINIT functions

`getINITModel` and `runINIT` (under `INIT/tINIT/`) are marked legacy and are not scheduled for removal. `utils/legacyMethodNotice.m` issues a `RAVEN:legacyMethod` warning once, which can be silenced, and points to `ftINIT`. `ftINIT` is the method for new work; `getINITModel` and `runINIT` reproduce models built with them.
