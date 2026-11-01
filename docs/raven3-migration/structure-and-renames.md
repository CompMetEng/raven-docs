# Structure, removals and renames

RAVEN 3 sorts its functions into folders by function area. It removes 65 functions of RAVEN 2, merges or renames 8, and keeps 5 RAVEN 2 names as wrappers.

## Repository reorganisation

The code of RAVEN 3 is in `src/`. RAVEN 2 kept its functions in the top-level folders `core/`, `external/`, `INIT/`, `hpa/`, `io/`, `legacy/`, `pathway/`, `plotting/`, `solver/`, `struct_conversion/`, `installation/` and `utils/`, and its bundled third-party code in `software/`. Other top-level folders moved as well: the third-party code of `software/` is in `src/external/`, `tutorial/` is `tutorials/`, `doc/` is `docs/`, and `testing/` is `tests/function_tests/`.

| RAVEN 3 folder (under `src/`) | Contents | RAVEN 2 source |
|---|---|---|
| `INIT/` | `ftINIT`, `INIT/tINIT/` with `getINITModel` and `runINIT` (the legacy tINIT method), and the parsing of HPA and expression data and the scoring of genes (`parseHPA`, `parseHPArna`, `scoreModel`) | `INIT/`, `hpa/` |
| `analysis/` | Analyses based on flux balance analysis (FBA): flux variability analysis (FVA), sampling, FSEOF, OptKnock, robustness, production envelope, flux comparison and flux tracing | `core/` |
| `annotation/` | MIRIAM editing, SBO term assignment, ΔG CSV I/O | `struct_conversion/` (and new functions) |
| `biomass/` | Fitting and scaling of the biomass composition, growth-associated maintenance (GAM) | `core/` (and new functions) |
| `comparison/` | Comparison of several models, structured model diffing | `core/` (and new functions) |
| `conditions/` | Applying a growth or media condition from data to a model | New folder |
| `conversion/` | RAVEN⇄COBRA conversion, identifier prefixing, field ordering | `struct_conversion/` |
| `curation/` | Gene and model curation driven by a genome annotation | New folder |
| `external/` | Bundled third-party code (GLPKmex, libSBML and m2html) and the target folder `src/external/<tool>` for the downloaded BLAST+, DIAMOND and HMMER binaries. `src/external/scip/` holds no files, and `setRavenSolver('scip')` downloads the SCIP MEX file into it on Windows (see [Toolbox dependencies and installation](#toolbox-deps)) | `software/` |
| `gapfilling/` | `fillGaps` and its algorithms, task fitting, checks for leak metabolites and exchange | `core/`, `INIT/` (and new functions) |
| `installation/` | Path setup, download of binaries and data on demand | `installation/`, `core/` (`findRAVENroot`), `external/` (`updateDocumentation`) |
| `io/` | Model import and export (SBML, YAML, Excel), FASTA I/O | `io/` (and new functions) |
| `localization/` | Prediction and scoring of subcellular localisation, compartment assignment | `external/`, `core/` (`predictLocalization`) (and new functions) |
| `manipulation/` | Structural edits: adding, removing and changing reactions, metabolites and genes; merging, sorting and simplifying | `core/`, `io/` (`closeModel`, `sortIdentifiers`), `INIT/` (`removeLowScoreGenes`, `reverseRxns`) |
| `queries/` | Lookups that do not change the model: indexes, exchange and transport reactions, construction of stoichiometry, model checking | `core/` (and new functions) |
| `reconstruction/` | Draft reconstruction from KEGG and from homology | `external/`, `core/` (`getModelFromHomology`, `guessComposition`) |
| `solver/` | LP and MILP solving | `solver/`, `core/` (`getMinNrFluxes`) (and new functions) |
| `tasks/` | Parsing and checking of metabolic task lists | `core/` |
| `utils/` | General helpers, among them the argument parsing and the registry | `utils/`, `core/` (`convertCharArray`, `printOrange`) |
| `deprecated/` | Wrappers for merged and renamed functions | New folder |
| `tests/function_tests/` (repository root, outside `src/`) | Class-based `matlab.unittest` suite. 23 of 25 classes derive from `RavenTestCase`, and `tBinaries` and `tParseRAVENargs` derive from `matlab.unittest.TestCase` | `testing/` (function-based tests built with `functiontests`) |

The files `checkRaven.m` and `checkInstallation.m` (a wrapper) are in the repository root.

Some code has no successor folder: the subfolder `external/metacyc/` with the MetaCyc function `external/combineMetaCycKEGGModels.m`, `pathway/` and `plotting/` (visualisation), `legacy/` (CellDesigner import and other pre-2.0 code), and the Excel-POI helpers of `io/` together with the Apache POI libraries in `software/apache-poi`.

A script that calls RAVEN functions by name keeps working when the whole RAVEN folder tree, subfolders included, is on the MATLAB path (through `addRavenToUserPath` or `addpath(genpath(...))`), because MATLAB resolves functions by name across the path. The reorganisation affects a script in three cases: it uses a hard-coded path to a specific `.m` file, it calls a removed function or a merged function that has no wrapper, or it contains a function with the name of a RAVEN 3 function. `checkFunctionUniqueness` warns about the last case. Individual moved files are not mapped.

---

(removed-functionality)=
## Removed functionality

The table lists all 65 functions of RAVEN 2 that RAVEN 3 removes without a successor of the same name. The counts per RAVEN 2 folder are `pathway/` 6, `plotting/` 10, `external/` 12 (8 for MetaCyc, 4 others), `legacy/` 11, `io/` 12, `core/` 8, `utils/` 3, `solver/` 2 and `INIT/` 1. No function of RAVEN 3 calls a removed function. The name `getToolboxVersion` exists in RAVEN 3 as a local function of `exportForGit`.

| Removed | Former purpose | Replacement |
|---|---|---|
| `pathway/colorPathway`, `pathway/getPathwayDimensions`, `pathway/mapPathwayRxnNames`, `pathway/markPathwayWithExpression`, `pathway/markPathwayWithFluxes`, `pathway/trimPathway` (6 functions) | Handling and colouring of metabolic pathway maps | None in RAVEN 3. Alternatives are the COBRA Toolbox, Escher, and the export of flux and omics data for plotting elsewhere |
| `plotting/colorSubsystem`, `plotting/drawMap`, `plotting/drawPathway`, `plotting/getColorCodes`, `plotting/getObjectiveString`, `plotting/plotAdditionalInfo`, `plotting/plotLabels`, `plotting/setColorToMapRxns`, `plotting/setOmicDataToRxns`, `plotting/setTitle` (10 functions) | Drawing of metabolic maps and colouring with omics data | None, as above |
| `external/metacyc/{getModelFromMetaCyc,getRxnsFromMetaCyc,getMetsFromMetaCyc,getEnzymesFromMetaCyc,getMetaCycModelForOrganism,addSpontaneousRxns,linkMetaCycKEGGRxns}`, `external/combineMetaCycKEGGModels` (8 functions) | Draft reconstruction from MetaCyc | None. The reconstruction methods of RAVEN 3 are the KEGG-based and the homology-based method |
| `legacy/core/changeGeneAssoc`, `legacy/external/constructPathwayFromCelldesigner`, and the nine functions of the bundled `xml_toolbox` (`xml_format`, `xml_formatany`, `xml_help`, `xml_load`, `xml_parse`, `xml_parseany`, `xml_save`, `xml_strsplit`, `xml_unblank`) (11 functions) | CellDesigner import and pre-2.0 compatibility code | None |
| `io/importExcelModel`, `io/loadWorkbook`, `io/loadSheet`, `io/writeSheet`, `io/SBMLFromExcel`, `io/addJavaPaths`, `io/startup` (7 functions) | Excel model I/O through Apache POI | `io/writeExcel.m` (OOXML writer without dependencies) for export and `curation/curateModelFromTables.m` for tabular curation. RAVEN 3 cannot import a full Excel template (see [Excel I/O](#excel-io)) |
| `io/exportModelToSIF`, `io/exportToTabDelimited` | Export of a SIF graph; tab-delimited export of a model | None. The sole caller of `exportToTabDelimited` was the fallback of `exportToExcelFormat` for a path without file name, which is removed |
| `io/getFullPath`, `io/getMD5Hash`, `io/getToolboxVersion` | Canonical file path; MD5 hash of a file; git version of the toolbox | Inlined where needed: the MD5 hash through Java `MessageDigest` in `getBlast`, and the version as a local function of `exportForGit` |
| `core/dispEM` | Display of errors and warnings (388 lines call it in RAVEN 2, counted outside `doc/` and `testing/`) | `warning()` and `error()`, and `utils/ravenList.m` for formatted lists of items (see [Backward-incompatible changes](#backward-incompatible-changes)) |
| `core/followFluxes`, `core/followChanged` | Report of flux changes relative to a reference solution | `analysis/compareFluxes.m` compares two flux vectors of one model (reactions turned on or off, flipped and changed, with `cutoff` and `metaboliteList`) and replaces `core/followChanged`. `queries/printFluxes.m` prints the fluxes of one vector above a cut-off |
| `core/printModel` | Printing of reactions to the screen or to a file | `queries/printModelStats.m` and `queries/printFluxes.m` cover model summaries and the printing of fluxes (see below the table) |
| `core/getMetsInComp` | Indices of the metabolites in a compartment | `model.metComps == compIndex` |
| `core/mapCompartments` | Merging and splitting of the score columns of a localisation-score structure by compartment rules | The `compartmentMap` option of `parseScores` and `getUniProtScores`. The default map `defaultCompartmentMap` applies to `getUniProtScores` and to `parseScores` with the `'uniprot'` predictor. Elsewhere, without a map, every label stays unchanged. With a map, a label that the map does not contain is dropped together with its score column. Merged columns take the maximum score, and splitting is not supported |
| `core/getExpressionStructure` | Loading of an expression structure from an ad hoc Excel format | `INIT/parseHPA.m` and `INIT/parseHPArna.m` read Human Protein Atlas files. Expression tables from other sources have to be assembled by hand as the `arrayData` structure documented in `scoreModel` |
| `core/checkRxn` | Debugging of the synthesisability of one reaction | No direct successor. `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` and `gapfilling/checkProduction.m` cover related checks |
| `external/getWoLFScores` | Parsing of WoLF PSORT scores | None. `parseScores` with `'wolf'` raises `RAVEN:badInput` (see [Backward-incompatible changes](#backward-incompatible-changes)) |
| `external/kegg/constructMultiFasta`, `external/kegg/getWSLpath`, `external/getBlastFromExcel` | Assembly of a multi-FASTA file per KO; translation of WSL paths; import of BLAST results from Excel | The KEGG pipeline based on the artefacts of `toolbox-assets` (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `solver/qMOMA`, `solver/solveQP` | MOMA analyses and quadratic programming | None. RAVEN 3 has no quadratic programming. The arguments removed from `findGeneDeletions` are in [Backward-incompatible changes](#backward-incompatible-changes) |
| `utils/emptyOrLogicalScalar`, `utils/emptyOrTextOrCellOfText`, `utils/emptyOrTextScalar` | Validators of arguments | `utils/parseRAVENargs.m` |
| `INIT/getExprForRxnScore` | Reaction scores from expression data | A private helper of the test suite in `tests/function_tests/private/` |

The function `printFluxes` prints the reactions of a flux vector whose absolute flux is at least `cutOffFlux` (default `10^-8`), one line per reaction. It prints exchange reactions unless `onlyExchange` is `false`. A listing of all reactions of a model without fluxes has no direct replacement.

---

(renamed-merged-and-consolidated-functions)=
## Renamed and merged functions

The folder `deprecated/` holds `makeSomething`, `consumeSomething`, `canProduce` and `canConsume`. These wrappers keep the RAVEN 2 names callable, issue a `RAVEN:deprecated` warning once ("will be removed in the next major release") and forward to the RAVEN 3 function. The other functions in the table have no wrapper, except `checkInstallation`, which has a row of its own.

| RAVEN 2 functions | RAVEN 3 function | Notes |
|---|---|---|
| `makeSomething(model, ignoreMets, isNames, minNrFluxes, allowExcretion, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'produce', ...)` | The argument order maps one to one, and the wrapper forwards `varargin` unchanged |
| `consumeSomething(model, ignoreMets, isNames, minNrFluxes, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'consume', ...)` | The RAVEN 2 order has no position for `allowExcretion`, so the wrapper remaps the arguments by name to keep `params` and `ignoreIntBounds` |
| `canProduce(model, mets)` | `canExchange(model, 'produce', 'mets', mets)` | None |
| `canConsume(model, mets)` | `canExchange(model, 'consume', 'mets', mets)` | None |
| `compareRxnsGenesMetsComps` | `comparison/compareMultipleModels.m` | The overlap output of RAVEN 2 (reactions, genes, metabolites, EC codes, metabolite names, equations and unique equations) is part of the output of `compareMultipleModels`. No wrapper |
| `INIT/scoreComplexModel.m` | `INIT/scoreModel.m` | Merged, no wrapper. A call moves to `scoreModel` with the same positions and defaults for the first six optional arguments, and `dataPrecedence` is added as the 7th optional argument |
| `INIT/ftINITFillGapsMILP.m` | `solver/getMinNrFluxes.m` | Available through the option `resolveTies` of `getMinNrFluxes`, which exists for `formulation` `'reversible'`. The default `'irrev'` raises an error with `resolveTies`. The option `proveAbsGap` belongs to `ftINIT` |
| `INIT/ftINITFillGapsForAllTasks.m` | `gapfilling/ftINITFillGaps.m` and the gap-fill mode `'preMerged'` of `fitTasks` | None. `ftINITFillGaps` exists in RAVEN 2 as well |
| `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` | `reconstruction/kegg/readKEGGTable.m` (with `buildGlobalKEGGModel` and `buildGlobalGPR`) and the KEGG artefacts of `toolbox-assets` | The data source differs, so the signatures are not compatible (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `core/parallelPoolRAVEN.m` | `utils/parallelWorkersRAVEN.m` | `parallelWorkersRAVEN` returns a worker count for `parfor` (`0` or `Inf`) and starts no pool. `parallelPoolRAVEN` returns `[ps, oldPoolAutoCreate]` |
| `installation/checkInstallation.m` | `checkRaven.m` in the repository root | The signature is identical. `checkInstallation.m` in the repository root forwards to `checkRaven` and issues a `RAVEN:deprecated` warning on every call |

### Gene scoring with `scoreModel`

RAVEN 2 has `INIT/scoreComplexModel.m` and `hpa/scoreModel.m`. RAVEN 3 has one `scoreModel`, which the legacy method tINIT and its replacement ftINIT call with different settings. A call written for `hpa/scoreModel.m` differs in these points (checked against 2.11.3):

- RAVEN 2 scored a reaction by the best or the average score over all its genes (`multipleGeneScoring`, values `'best'` and `'average'`). RAVEN 3 applies `isozymeScoring` (default `'max'`) to the `or` parts and `complexScoring` (default `'min'`) to the `and` parts of the rule. A reaction with an `and` rule therefore gets a different default score.
- Positions count all arguments of the call. The 7th to 9th arguments of a RAVEN 2 call (`multipleGeneScoring`, `multipleCellScoring`, `hpaLevelScores`) are read as `isozymeScoring`, `complexScoring` and `multipleCellScoring`. `hpaLevelScores` is the 10th argument.
- `multipleCellScoring` accepts `'max'` and `'average'`. RAVEN 2 accepted `'best'` and `'average'`.
- `dataPrecedence` is an argument of RAVEN 3 with the default `'gene'`.
- A gene that is absent from the data receives `NaN` in `geneScores`, and the RAVEN 2 documentation states `-Inf`. `getINITModel` converts `NaN` back to `-Inf`.

[Backward-incompatible changes](#backward-incompatible-changes) lists these differences as table rows. The function `getINITModel` passes `'max'` for `isozymeScoring` and for `complexScoring`, and `'reaction'` for `dataPrecedence`. Whether these settings reproduce the scores of the RAVEN 2 `hpa/scoreModel` was not checked, and the RAVEN 2 value `'average'` of `multipleGeneScoring` has no equivalent among them.

### Legacy tINIT functions

The method ftINIT replaces the legacy method tINIT. The functions `getINITModel` and `runINIT` (in `INIT/tINIT/`) implement tINIT, are marked legacy and are not scheduled for removal. `utils/legacyMethodNotice.m` issues a `RAVEN:legacyMethod` warning once, which can be silenced, and points to `ftINIT`. The method `ftINIT` is meant for new work, and `getINITModel` and `runINIT` reproduce models that were built with them.
