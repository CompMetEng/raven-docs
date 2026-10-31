# New functionality, dependencies and error handling

Gap-filling, context-specific model extraction with `ftINIT`, new functions, MATLAB toolbox dependencies and error handling differ between RAVEN 2 and RAVEN 3.

(ftinit)=
## Gap-filling and context-specific model extraction

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `fillGaps` algorithm | One built-in mixed-integer linear programming (MILP) connectivity-maximisation strategy | The same strategy remains the default; the `algorithm` option adds `'fastLP'`, `'swiftLP'`, `'gapfillMILP'` and `'topological'` |
| `fillGaps` positional arguments | `allowNetProduction, useModelConstraints, supressWarnings, rxnScores` | Unchanged; new options are name-value-only |
| `ftINIT` tie-breaking | Depended on the solver seed | Optional `resolveTies` makes the answer less dependent on the solver seed |
| `ftINIT` MILP optimality proof | Escalating relative-gap search only | Optional `proveAbsGap` proves each stage to a fixed absolute gap in one solve |
| `ftINITInternalAlg` tie-break arguments | (not present) | `rankKeys` (14th argument) and `pinFluxes` (15th argument) |
| `getINITModel` and `runINIT` | Supported, no runtime notice | Supported, under `INIT/tINIT/`; one-time "legacy, use `ftINIT`" notice (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |
| `fitTasks` gap-fill mode | One behaviour (equivalent to `'merge'`) | `gapFillMode`: `'merge'` (default, same as in RAVEN 2) or `'preMerged'` |
| `fitTasks` outputs | `[outModel, addedRxns]` | `[outModel, addedRxns, failedTasks]` |
| Task requiring net production of a metabolite with no reactions | Boundary constraint dropped before gap-filling without a message; the task could be reported as passing incorrectly | Constraint preserved; the task is reported as failing if the reference model cannot produce the metabolite |

With `gapFillMode` set to `'preMerged'`, `fitTasks` expects a reference model that already contains the model's own reactions, so no merge is needed for each task, and `ftINITFillGaps` fills the gaps.

The `algorithm` option of `fillGaps` selects among the following:

- `'fastLP'` and `'swiftLP'`: FASTCORE-style and SWIFTCORE-style linear programming (LP) relaxation.
- `'gapfillMILP'`: growth-floor MILP with directionality repair.
- `'topological'`: breadth-first search producibility pre-screen, without model modification.

`fillGaps` calls `gapFillTopological` with the defaults of that function: the seeds are the metabolites of every reaction that has only substrates and a negative lower bound or only products and a positive upper bound, and the targets are the metabolites of the first objective reaction, substrates and products. `fillGaps` passes neither seeds nor targets, so a model without an objective reaction always raises `RAVEN:badInput` there.

With `resolveTies`, each `ftINIT` MILP step keeps the score optimum and then picks among the tied solutions in phases: the fewest kept removable reactions, the lowest summed ID rank of those (a merged reaction is ranked by the smallest original ID of its group), the fluxes with the least total absolute flux, and the fluxes with the least ID-rank-weighted backward flux. The arguments `resolveTies` and `proveAbsGap` are name-value-only and default to off; the positional arguments of `ftINIT` are unchanged.

In `ftINITInternalAlg`, `rankKeys` (default `model.rxns`) gives the key each reaction is ranked by in the ID-rank phases of `resolveTies`. Setting `pinFluxes` (default `true`) to `false` skips the two flux phases of `resolveTies`. `ftINIT` passes `false` in its last step.

---

(new-functionality)=
## New functionality

RAVEN 3 adds the functions in the table; except where noted they do not change RAVEN 2 functions.

| Area | New functions | Added capability |
|---|---|---|
| Flux sampling (`analysis/`) | `sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`, `sampleWarmupPoints` | ACHR (hit-and-run) and CHRR (hit-and-run with rounding), two near-uniform Markov chain Monte Carlo (MCMC) samplers |
| Flux sampling (`analysis/`) | `randomSampling` (changed) | Becomes a dispatcher (`'method'` option) over the RAVEN 2 random-objective method (now `'randomObjective'`) and the two new samplers |
| Flux analysis and quality control (QC) | `compareFluxes` | Diffs flux vectors |
| Flux analysis and QC | `getMinimalMedium` | Searches a minimal medium with a MILP |
| Flux analysis and QC | `traceFluxPath` | Traces the path of highest flux fraction between two reactions |
| Flux analysis and QC | `walkFluxes` | Navigates the flux neighbourhood interactively |
| Flux analysis and QC | `modelSummary` | Prints a model and flux summary |
| Model comparison (`comparison/`) | `diffModels` | Diffs two models by ID: stoichiometry, bounds, objective, `grRules` (logical equality in disjunctive normal form, DNF), EC codes, metabolite properties |
| Manipulation | `findDuplicateRxns` | Standalone duplicate-stoichiometry query |
| Manipulation | `findPotentialErrors` | Function of its own (a local function of `core/standardizeGrRules.m` in RAVEN 2); parse-tree-based detection of `grRules` that are not in DNF and of rules that cannot be parsed (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| Genome-based curation (`curation/`, new folder) | `downloadGenomeData`, `getGeneData`, `processProteinFastaFile` | Pipeline from an NCBI genome accession to a gene ID mapping table |
| Genome-based curation (`curation/`, new folder) | `renameModelGenes` | Bulk gene renaming in a model |
| Genome-based curation (`curation/`, new folder) | `curateModelFromTables` | Bulk curation of metabolites, reactions and genes from `.tsv` files against an existing model |
| Biomass composition (`biomass/`) | `getBiomassFractions`, `scaleBiomassFraction`, `scaleBiomassPseudoreaction`, `setGAM` | Organism-agnostic biomass-composition and growth-associated-maintenance (GAM) calibration; `tutorials/tutorial7.m` demonstrates the workflow |
| Localisation (`localization/`) | `assignCompartments`, `defaultCompartmentMap`, `getUniProtScores` | Deterministic MILP compartment assignment (alternative to the heuristic `predictLocalization`) |
| Localisation (`localization/`) | `parseScores` (changed) | Gains `'mulocdeep'`, `'compartments'` and `'uniprot'`; `'deeploc'` reads DeepLoc 2 output; the default predictor is `'deeploc'` (RAVEN 2: `'wolf'`); WoLF PSORT is removed (see [Backward-incompatible changes](#backward-incompatible-changes)) |
| Annotation (`annotation/`) | `assignSBOterms`, `loadDeltaGCSV`, `saveDeltaGCSV` | Organism-agnostic SBO term assignment; ΔG thermodynamic data CSV round-trip |
| Conditions (`conditions/`, new folder) | `applyCondition` | Applies a data-driven growth or media condition, given as a YAML file, to a model |
| Internal infrastructure | `ravenModelFields` | Central registry of every 1-D model field (entity type, default value), used internally by `permuteModel`, `removeReactions` and `curateModelFromTables` |

`sampleCHRR` rounds the polytope before sampling, so mixing stays fast on strongly elongated polytopes, such as enzyme-constrained models, unlike `sampleACHR`.

`diffModels` is separate from `compareMultipleModels`, the existing overlap-style comparison. `applyCondition` applies the parts of a condition in a fixed sequence: exchange bounds, optional cofactor-pseudoreaction edits, optional biomass-stoichiometry deltas and per-reaction bound overrides.

---

(toolbox-deps)=
## Toolbox dependencies and installation

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| MATLAB version | No pinned or documented minimum (guidance: avoid very new MATLAB syntax, to accommodate older installs) | Tested in continuous integration with R2024b |
| Statistics Toolbox | Required (`combnk`) | Not required (`nchoosek`, base MATLAB) |
| Bioinformatics Toolbox | Required (`fastaread` and `fastawrite`) | Not required (`io/readFasta.m` and `io/writeFasta.m`) |
| Optimization Toolbox | Required for `qMOMA` and `solveQP` | Not required (both removed) |
| Excel I/O | Bundled Apache POI (Java) | Dependency-free OOXML writer |
| LP and MILP solver | Required (bundled `glpk`, or Gurobi, SCIP or COBRA) | Unchanged, still required |
| External binaries | Committed to the repository, available offline immediately after clone | BLAST+, DIAMOND and HMMER are fetched on demand on first use (per-platform ZIPs); an offline `*-binaries` release bundle is available for air-gapped installs |
| KEGG HMM libraries and reference data | Manual download or local build required | Fetched on demand, cached locally after first use |
| Installation self-check | `installation/checkInstallation.m` ran the full test suite to populate its pass/fail table | `checkRaven` in the repository root runs targeted checks and downloads missing binaries without a prompt (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |

All downloads come from releases of `toolbox-assets`. KEGG data comes from the release tag that `keggDataVersion()` returns (`src/reconstruction/kegg/KEGG_VERSION.md`, tag `kegg118`). The binaries come from fixed tags set in `src/installation/downloadRavenBinaries.m`: `blast-2.17.0`, `diamond-2.1.17`, `hmmer-3.4.0` and, on Windows, `hmmer-3.3.2`. The checksums of downloaded files come from `manifest.json` of the `manifest-v3` release, read at download time.

`checkRaven` runs a small import and export round-trip and a two-reaction LP per solver, without invoking the full test classes.

A RAVEN 3 clone fetches binaries and data on demand, which requires network access.

---

## Error and warning handling

RAVEN 3 raises errors and issues warnings with native `error()` and `warning()` calls that carry identifiers, mostly `RAVEN:*`. The identifiers are additive, and message text is preserved for most existing checks, so `try/catch` blocks that match on message text keep working for those checks. [Backward-incompatible changes](#backward-incompatible-changes) gives the details of the `dispEM` replacement, and [Removed functionality](#removed-functionality) names the new `utils/ravenList.m` helper.

RAVEN 3 adds an output argument to `queries/checkModelStruct.m`: `issues = checkModelStruct(model)` returns a structured array of the problems (`category`, `target` and `message`) for programmatic model QC and raises no error. Without an output argument it raises errors or issues warnings directly, as in RAVEN 2.
