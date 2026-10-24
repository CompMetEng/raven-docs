# New functionality, dependencies, and error handling

(ftinit)=
## 1. Gap-filling and context-specific model extraction

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `fillGaps` algorithm | one built-in MILP connectivity-maximization strategy | same strategy is still the default; `algorithm` option adds `'fastLP'`/`'swiftLP'` (FASTCORE/SWIFTCORE-style LP relaxation), `'gapfillMILP'` (growth-floor MILP with directionality repair), `'topological'` (BFS producibility pre-screen, no model modification) |
| `fillGaps` positional arguments | `allowNetProduction, useModelConstraints, supressWarnings, rxnScores` | unchanged; new options are name-value-only |
| `ftINIT` tie-breaking | depends on solver seed | optional `resolveTies` pins degenerate MILP optima to a deterministic answer |
| `ftINIT` MILP optimality proof | escalating relative-gap search only | optional `proveAbsGap` proves each stage to a fixed absolute gap in one solve |
| `ftINIT` positional arguments | preserved | unchanged; `resolveTies`/`proveAbsGap` are name-value-only, default off |
| `getINITModel`/`runINIT` | supported, no runtime notice | supported, now under `INIT/tINIT/`; one-time "legacy, use `ftINIT`" notice (see [§5](#renamed-merged-and-consolidated-functions)) |
| `fitTasks` gap-fill mode | one behavior (equivalent to today's `'merge'`) | `gapFillMode`: `'merge'` (default, same as before) or `'preMerged'` (faster, ftINIT-style) |
| `fitTasks` outputs | `[outModel, addedRxns]` | `[outModel, addedRxns, failedTasks]` |
| Task requiring net production of a metabolite with no reactions | boundary constraint silently dropped before gap-filling; task could incorrectly report as passing | constraint preserved; task correctly reports failing if the reference model can't produce it |

---

(new-functionality)=
## 2. New functionality

All additive; none of this replaces or changes behavior of existing RAVEN 2
functions, except where noted.

| Area | New function(s) | What it adds |
|---|---|---|
| Flux sampling (`analysis/`) | `sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`, `sampleWarmupPoints` | `randomSampling` becomes a dispatcher (`'method'` option) across RAVEN 2's original random-objective method (now `'randomObjective'`) plus two new near-uniform MCMC samplers: ACHR (hit-and-run) and CHRR (hit-and-run with rounding, better mixing on ill-conditioned polytopes) |
| Flux analysis / QC | `compareFluxes`, `getMinimalMedium`, `traceFluxPath`, `walkFluxes`, `modelSummary` | structured flux-vector diffing; MILP-based minimal-medium search; highest-flux-fraction path tracing between two reactions; interactive flux-neighborhood navigation; model/flux summary printing |
| Model comparison (`comparison/`) | `diffModels` | structured, ID-keyed diff between two models: stoichiometry, bounds, objective, grRule (as logical DNF equality), EC codes, metabolite properties; distinct from the existing overlap-style `compareMultipleModels` |
| Manipulation | `findDuplicateRxns`, `findPotentialErrors` | standalone duplicate-stoichiometry query; parse-tree-based non-DNF grRule detection (see [§8](#gpr-parsing)) |
| Genome-based curation (`curation/`, new folder) | `downloadGenomeData`, `getGeneData`, `processProteinFastaFile`, `renameModelGenes`, `curateModelFromTables` | pipeline from an NCBI genome accession to a gene ID mapping table to bulk gene renaming in a model; `curateModelFromTables` bulk-curates mets/rxns/genes from `.tsv` files against an existing model |
| Biomass composition (`biomass/`) | `getBiomassFractions`, `scaleBiomassFraction`, `scaleBiomassPseudoreaction`, `setGAM` | organism-agnostic biomass-composition and growth-associated-maintenance (GAM) calibration; `tutorial/tutorial7.m` demonstrates the workflow |
| Localization (`localization/`) | `assignCompartments`, `defaultCompartmentMap`, `getUniProtScores` | deterministic MILP compartment assignment (alternative to the heuristic `predictLocalization`); `parseScores` gains `'deeploc'`/`'cello'`/`'mulocdeep'`/`'compartments'`/`'uniprot'` predictors (replacing WoLF PSORT; see [§3](../raven3-migration/backward-incompatible.md#backward-incompatible-changes)) |
| Annotation (`annotation/`) | `assignSBOterms`, `loadDeltaGCSV`/`saveDeltaGCSV` | organism-agnostic SBO term assignment; ΔG thermodynamic data CSV round-trip |
| Conditions (`conditions/`, new folder) | `applyCondition` | applies a data-driven growth/media condition (a YAML file, not code) to a model in a fixed sequence: exchange bounds, optional cofactor-pseudoreaction edits, optional biomass-stoichiometry deltas, per-reaction bound overrides |
| Internal infrastructure | `ravenModelFields` | central registry of every 1-D model field (entity type, default value), backing `permuteModel`/`removeReactions` internally |

---

(toolbox-deps)=
## 3. Toolbox dependencies and installation

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| MATLAB version | no pinned/documented minimum (guidance: avoid very new MATLAB syntax, to accommodate older installs) | CI is tested against **R2024b** |
| Statistics Toolbox | required (`combnk`) | not required (`nchoosek`, base MATLAB) |
| Bioinformatics Toolbox | required (`fastaread`/`fastawrite`) | not required (`io/readFasta.m`/`io/writeFasta.m`) |
| Optimization Toolbox | required for `qMOMA`/`solveQP` | not required (both removed) |
| Excel I/O | bundled Apache POI (Java) | dependency-free OOXML writer |
| LP/MILP solver | required (bundled `glpk`, or Gurobi/SCIP/COBRA) | unchanged, still required |
| External binaries (BLAST+, DIAMOND, HMMER, cd-hit, MAFFT) | committed to the repository, available offline immediately after clone | fetched on demand from the `raven-data` GitHub release on first use (per-platform ZIPs); an offline `*-full`/`*-binaries` release bundle is available for air-gapped installs |
| KEGG HMM libraries / reference data | manual download or local build required | fetched on demand from `raven-data`, cached locally after first use |
| Installation self-check | `installation/checkInstallation.m`; ran the full test suite to populate its pass/fail table | renamed `checkRaven`, moved to the repo root; does fast, targeted checks (a small import/export round-trip, a trivial LP per solver) instead of invoking the full test classes, and proactively offers to download missing binaries |

Net effect: a bare RAVEN 3 clone is far smaller and installs with fewer MATLAB
toolbox prerequisites. The trade-off: it needs network access the first time
KEGG- or homology-based reconstruction functions actually run.

---

## 4. Error and warning handling

RAVEN 2's `dispEM` always raised errors with an empty identifier, so no RAVEN 2
`try/catch` could have matched on `err.identifier`; RAVEN 3's move to native
`error()`/`warning()` with real (mostly `RAVEN:*`) identifiers is additive from
that angle, not breaking. Message text is preserved for most existing checks,
so text-matching `try/catch` blocks are unaffected either way. See
[§3](../raven3-migration/backward-incompatible.md#backward-incompatible-changes) for the details and the new
`utils/ravenList.m` message-formatting helper.

One related, purely additive change: `queries/checkModelStruct.m`, called *with*
an output argument (`issues = checkModelStruct(model)`), now returns a
structured array of findings (`category`/`target`/`message`) instead of only
throwing or printing, useful for programmatic model QC. The no-output-argument
calling convention (throws/warns directly) is unchanged.
