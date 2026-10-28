# What moved, what's gone, and what's renamed

## 1. Repository reorganization

RAVEN 2's top-level layout (`core/`, `external/`, `hpa/`, `io/`, `legacy/`,
`pathway/`, `plotting/`, `solver/`, `struct_conversion/`, `installation/`,
`utils/`) has been replaced with functional folders that group functions by what
they do rather than by legacy history:

| RAVEN 3 folder | Contents | Mostly came from (RAVEN 2) |
|---|---|---|
| `INIT/` | `ftINIT`, `INIT/tINIT/` for `getINITModel`/`runINIT`, and HPA/expression parsing + gene scoring (`parseHPA`, `parseHPArna`, `scoreModel`) | `INIT/`, `hpa/` |
| `analysis/` | FBA-adjacent analyses: FVA, sampling, FSEOF, OptKnock, robustness, production envelope, flux comparison/tracing | `core/` |
| `annotation/` | MIRIAM editing, SBO term assignment, ΔG CSV I/O | `struct_conversion/` (+ new) |
| `biomass/` | Biomass composition fitting/scaling, GAM | `core/` (+ new) |
| `comparison/` | Multi-model comparison, structured model diffing | `core/` (+ new) |
| `conditions/` | Applying a data-driven growth/media condition to a model | *new folder* |
| `conversion/` | RAVEN⇄COBRA conversion, identifier prefixing, field ordering | `struct_conversion/` |
| `curation/` | Genome-annotation-driven gene/model curation | *new folder* |
| `gapfilling/` | `fillGaps` and its pluggable algorithms, task fitting, leak-metabolite/exchange checks | `core/` (+ new) |
| `installation/` | Path setup, on-demand binary/data download | `installation/` |
| `io/` | Model import/export (SBML, YAML, Excel), FASTA I/O | `io/` |
| `localization/` | Subcellular localization prediction/scoring, compartment assignment | `external/` (+ new) |
| `manipulation/` | Structural edits: add/remove/change rxns, mets, genes; merge, sort, simplify | `core/` |
| `queries/` | Non-mutating lookups: indexes, exchange/transport reactions, stoichiometry construction, model checking | `core/` |
| `reconstruction/` | KEGG- and homology-based draft reconstruction | `external/` |
| `solver/` | LP/MILP solving | `solver/` |
| `tasks/` | Metabolic task list parsing/checking | `core/` |
| `testing/` | `matlab.unittest` suite (`function_tests/`) | `testing/` |
| `utils/` | Generic helpers, including the new argument-parsing/registry infrastructure | `utils/` |
| `deprecated/` | Thin backward-compatible wrappers for merged/renamed functions | *new folder* |

Entirely removed (no successor folder): `external/metacyc/` (MetaCyc
reconstruction), `pathway/` and `plotting/` (visualization), `legacy/`
(CellDesigner import and other pre-2.0 code), `struct_conversion/`'s Excel-POI
helpers.

**The reorganization affects fewer scripts than the change list suggests.**
If your scripts call RAVEN
functions by name (the normal usage pattern, with the whole RAVEN folder tree,
including subfolders, added to the MATLAB path via `addRavenToUserPath` or
`addpath(genpath(...))`), moving a file to a new subfolder does not break the
call: MATLAB resolves functions by name across the whole path, not by a
hard-coded relative location. The reorganization only matters if you (a)
hard-coded a path to a specific `.m` file, (b) called one of the functions that
was actually removed or merged (see below), or (c) shadowed a RAVEN function
name with your own; folder names are irrelevant otherwise.

The full moved-file mapping (RAVEN 2 path → RAVEN 3 path) is not reproduced
here because it is large and, as the point above explains, rarely something
you need to act on.

---

(removed-functionality)=
## 2. Removed functionality

Beyond the items already listed as backward-incompatible above, RAVEN 3 removed
a number of functions and whole subsystems as part of a deliberate effort to
make the codebase smaller. None of these have call sites left in RAVEN 3 itself.

| Removed | What it did | Replacement / notes |
|---|---|---|
| `pathway/*`, `plotting/*` (16 functions: `drawMap`, `drawPathway`, `colorPathway`, `colorSubsystem`, `markPathwayWithFluxes`, `markPathwayWithExpression`, `setOmicDataToRxns`, `plotAdditionalInfo`, etc.) | Metabolic map/pathway visualization | None in RAVEN core. Use COBRA Toolbox, Escher, or export flux/omics data for external plotting. |
| `external/metacyc/*` (7 functions: `getModelFromMetaCyc`, `getRxnsFromMetaCyc`, `getMetsFromMetaCyc`, `getEnzymesFromMetaCyc`, `addSpontaneousRxns`, `linkMetaCycKEGGRxns`, `combineMetaCycKEGGModels`) | MetaCyc-based draft reconstruction | None; KEGG- and homology-based reconstruction remain the supported paths. |
| `legacy/*` (CellDesigner import, `changeGeneAssoc`, the bundled `xml_toolbox`) | Pre-2.0 compatibility code | None; considered dead. |
| `io/importExcelModel.m`, `io/loadWorkbook.m`, `io/loadSheet.m`, `io/writeSheet.m`, `io/SBMLFromExcel.m`, `io/addJavaPaths.m`, `io/startup.m` | Apache-POI-based Excel model I/O | `io/writeExcel.m` (dependency-free OOXML writer) for export; `curation/curateModelFromTables.m` for tabular curation. No full Excel-template *import* path remains; see [§6](../raven3-migration/formats-and-reconstruction.md#excel-io). |
| `io/exportModelToSIF.m`, `io/exportToTabDelimited.m` | SIF graph export; tab-delimited model export | Dead/orphaned code with no callers; removed outright. |
| `io/getFullPath.m`, `io/getMD5Hash.m`, `io/getToolboxVersion.m` | Path canonicalization; file MD5 hashing; toolbox git-version lookup | Inlined where still needed (e.g. MD5 via Java's `MessageDigest` directly inside `getBlast`), or folded into `exportForGit`. |
| `core/dispEM.m` | Universal error/warning display | Native `warning()`/`error()` + new `utils/ravenList.m` for formatted item lists. See [§3](../raven3-migration/backward-incompatible.md#backward-incompatible-changes). |
| `core/followFluxes.m`, `core/followChanged.m` | Flux-change reporting relative to a reference solution | `queries/printFluxes.m` covers the cutoff-filtering half; nothing replaces the reference-flux comparison directly. |
| `core/printModel.m` | Printed reactions to screen/file | `queries/printModelStats.m` / `queries/printFluxes.m` cover related summary/flux printing; no direct one-line-per-reaction dump remains. |
| `core/getMetsInComp.m` | Returned metabolite indices in a given compartment | Inline it as `model.metComps == compIndex`. |
| `core/mapCompartments.m` | Remapped compartment labels in a localization-score structure | Superseded by the new predictor-based localization workflow and `localization/defaultCompartmentMap.m`. |
| `core/getExpressionStructure.m` | Loaded an expression-experiment structure from an ad hoc Excel format | Superseded by `INIT/parseHPA.m`/`INIT/parseHPArna.m` for the supported expression-data workflow. |
| `core/checkRxn.m` | Per-reaction reactant/product synthesizability debugging | No direct successor; use `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m`, or `gapfilling/checkProduction.m`. |
| `core/parallelPoolRAVEN.m` | Parallel Computing Toolbox pool setup | Renamed/rewritten as `utils/parallelWorkersRAVEN.m`. |
| `external/getWoLFScores.m` | WoLF PSORT score parsing | None; see [§3](../raven3-migration/backward-incompatible.md#backward-incompatible-changes). |
| `external/kegg/{getGenesFromKEGG,getMetsFromKEGG,getRxnsFromKEGG,constructMultiFasta,getWSLpath}.m`, `external/getBlastFromExcel.m` | Local-KEGG-FTP-dump parsing; per-KO multi-FASTA assembly; WSL path translation; Excel-based BLAST import | Superseded by the raven-data-artifact-based KEGG pipeline. See [§7](#kegg-reconstruction). |
| `solver/qMOMA.m`, `solver/solveQP.m` | MOMA-based analyses (quadratic programming) | Removed; no in-toolbox QP-based replacement. See [§3](../raven3-migration/backward-incompatible.md#backward-incompatible-changes) for `findGeneDeletions` impact. |
| `testing/unit_tests/*.m` (script-based tests) | Ad hoc test scripts | `testing/function_tests/*.m`, a `matlab.unittest`-class-based suite. Contributor-facing only; `runRAVENtests` usage is unchanged for end users. |

---

(renamed-merged-and-consolidated-functions)=
## 3. Renamed, merged, and consolidated functions

RAVEN 3 introduces a formal **`deprecated/` folder convention**: functions that
were merged into a more general replacement stay callable under their old name,
as a thin wrapper that emits a one-time `RAVEN:deprecated` warning ("will be
removed in the next major release") and forwards to the new function.

| Old function(s) | New function | Notes |
|---|---|---|
| `makeSomething(model, ignoreMets, isNames, minNrFluxes, allowExcretion, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'produce', ...)` | Argument order maps 1:1; the wrapper forwards `varargin` unchanged. |
| `consumeSomething(model, ignoreMets, isNames, minNrFluxes, params, ignoreIntBounds)` | `findLeakMetabolite(model, 'consume', ...)` | **Not** a verbatim forward: `consumeSomething`'s old positional order has no `allowExcretion` slot, so the wrapper explicitly remaps arguments by name to avoid corrupting `params`/`ignoreIntBounds`. |
| `canProduce(model, mets)` | `canExchange(model, 'produce', 'mets', mets)` | |
| `canConsume(model, mets)` | `canExchange(model, 'consume', 'mets', mets)` | |
| `compareRxnsGenesMetsComps` | folded into `comparison/compareMultipleModels.m` | Its rxn/gene/met/comp overlap output is now one part of `compareMultipleModels`'s output; no separate function remains. |
| `INIT/scoreComplexModel.m` | `INIT/scoreModel.m` | **Merged, not renamed.** RAVEN 2 had *both* `INIT/scoreComplexModel.m` and `hpa/scoreModel.m`; RAVEN 3 folded them into one `scoreModel`, called with different settings from tINIT than from ftINIT. A RAVEN 2 call to `scoreModel` is unaffected; a call to `scoreComplexModel` has to move to `scoreModel` *and* pass the settings that reproduce the old behaviour (a single operator for both `and`/`or`, `dataPrecedence` `'reaction'`). |
| `INIT/ftINITFillGapsMILP.m` | folded into `solver/getMinNrFluxes.m` | Exposed now via `getMinNrFluxes`'s `resolveTies`/`proveAbsGap` options. |
| `INIT/ftINITFillGapsForAllTasks.m` | folded into `gapfilling/ftINITFillGaps.m` and `fitTasks`'s `'preMerged'` gap-fill mode | |
| `getGenesFromKEGG`/`getMetsFromKEGG`/`getRxnsFromKEGG` | `reconstruction/kegg/readKEGGTable.m` + the raven-data KEGG artifacts | Not a direct signature-compatible rename: the whole data source changed; see [§7](#kegg-reconstruction). |
| `checkInstallation` | `checkRaven` | Moved from `installation/checkInstallation.m` to repo-root `checkRaven.m`; identical calling signature. `checkInstallation` remains as a deprecated forwarding wrapper, so old calls keep working with a `RAVEN:deprecated` warning. |

Separately, `getINITModel` and `runINIT` (now under `INIT/tINIT/`) are marked
**legacy but indefinitely supported** (not on the `deprecated/` removal track)
via `utils/legacyMethodNotice.m`, which fires a one-time, silenceable
`RAVEN:legacyMethod` warning pointing at `ftINIT`. Use `ftINIT` for new work;
keep `getINITModel`/`runINIT` only to reproduce models originally built with
them.
