# New functionality, dependencies and error handling

Gap-filling, context-specific model extraction with `ftINIT`, added functions, MATLAB toolbox dependencies and error handling differ between RAVEN 2 and RAVEN 3.

(ftinit)=
## Gap-filling and context-specific model extraction

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `fillGaps` algorithm | One built-in mixed-integer linear programming (MILP) connectivity-maximisation strategy | The same strategy is the default (`algorithm` `'reference'`); the `algorithm` option adds `'fastLP'`, `'swiftLP'`, `'gapfillMILP'` and `'topological'` |
| `fillGaps` positional arguments | `allowNetProduction, useModelConstraints, supressWarnings, rxnScores` | The first four optional arguments are unchanged; `params` is the 7th and `algorithm` the 8th argument among all arguments, followed by `epsilon`, `minGrowth` and `verbose`; all can also be given as name-value pairs |
| `ftINIT` tie-breaking | Depends on the solver seed (the retries of the MILP set the seed to 1234); the dependence was not measured | The option `resolveTies` adds a best-effort selection among tied solutions (see below); the resulting dependence on the seed was not measured |
| `ftINIT` MILP optimality proof | Retries with an increasing relative gap, which is derived from an absolute-gap setting and the last objective value | The option `proveAbsGap` proves each stage to a fixed absolute gap in one solve (`MIPGap` 0) |
| `ftINIT` positional arguments | `transcrData` to `verbose` (5th to 11th argument among all arguments) | Unchanged; `resolveTies` and `proveAbsGap` follow `verbose` as the 12th and 13th argument among all arguments and are off by default |
| `fitTasks` gap-fill mode | One behaviour (equivalent to `'merge'`) | `gapFillMode`: `'merge'` (default, as in RAVEN 2) or `'preMerged'` |
| `fitTasks` outputs | `[outModel, addedRxns]` | `[outModel, addedRxns, failedTasks]` |

Argument positions in the migration pages count all arguments of the call, including the required ones. `getINITModel` and `runINIT` are described in [Renamed and merged functions](#renamed-merged-and-consolidated-functions).

With `gapFillMode` set to `'preMerged'`, `fitTasks` expects a reference model that already contains the model's own reactions, so no merge is needed for each task, and `ftINITFillGaps` fills the gaps.

How `fitTasks` treats a task that requires net production of a metabolite without reactions was not checked.

The `algorithm` option of `fillGaps` selects among the following.

- `'fastLP'` and `'swiftLP'`: FASTCORE-style and SWIFTCORE-style linear programming (LP) relaxation.
- `'gapfillMILP'`: growth-floor MILP. Reactions already in the draft model keep their bounds, so a reaction with the wrong direction is not changed.
- `'topological'`: breadth-first-search producibility pre-screen, without model modification. It requires a reference model and uses only the first one.

`fillGaps` calls `gapFillTopological` with the defaults of that function. The seeds are the metabolites of the exchange reactions that `getExchangeRxns` classes as `'uptake'` or `'reverse'`. The targets are the metabolites of the first objective reaction. A model without an objective reaction raises `RAVEN:badInput`. A value of `algorithm` that is none of the listed ones runs the `'reference'` algorithm.

With `resolveTies`, each `ftINIT` MILP step holds the score at its optimum and then chooses among the tied solutions in phases, each with a time limit: the fewest kept removable reactions, the lowest summed ID rank of those (a merged reaction is ranked by the smallest original ID of its group), the least total absolute flux, and the least ID-rank-weighted backward flux. `ftINITInternalAlg` has the arguments `resolveTies` (13th), `rankKeys` (14th, default `model.rxns`) and `pinFluxes` (15th, default `true`); `pinFluxes` set to `false` skips the two flux phases, and `ftINIT` passes `false` in its last step. A step whose first solve stops at the time limit keeps that solution without the phases, and the count and rank phases get half of the step time limit each; a phase that fails issues a warning.

---

(new-functionality)=
## New functionality

RAVEN 3 adds the functions in the table. `randomSampling` and `parseScores` are RAVEN 2 functions with changed behaviour.

| Area | Functions | Capability |
|---|---|---|
| Flux sampling (`analysis/`) | `sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`, `sampleWarmupPoints` | ACHR (hit-and-run) and CHRR (hit-and-run with rounding), two near-uniform Markov chain Monte Carlo (MCMC) samplers |
| Flux sampling (`analysis/`) | `randomSampling` (changed) | Dispatcher with the option `'method'`: `'achr'` (default), `'chrr'` and `'randomObjective'` (the RAVEN 2 method) |
| Flux analysis and quality control (QC) | `compareFluxes` | Compares flux vectors |
| Flux analysis and QC | `getMinimalMedium` | Searches a minimal medium with a MILP |
| Flux analysis and QC | `traceFluxPath` | Traces the path of highest flux fraction between two reactions |
| Flux analysis and QC | `walkFluxes` | Navigates the flux neighbourhood interactively |
| Flux analysis and QC | `modelSummary` (`queries/`) | Prints a model and flux summary |
| Model comparison (`comparison/`) | `diffModels` | Compares two models by ID: stoichiometry, bounds, objective, `grRules`, EC codes and metabolite properties; separate from the overlap comparison of `compareMultipleModels` |
| Manipulation | `findDuplicateRxns` | Duplicate-stoichiometry query |
| Genome-based curation (`curation/`) | `downloadGenomeData`, `getGeneData`, `processProteinFastaFile` | Pipeline from an NCBI genome accession to a gene ID mapping table |
| Genome-based curation (`curation/`) | `renameModelGenes` | Bulk gene renaming in a model |
| Genome-based curation (`curation/`) | `curateModelFromTables` | Bulk curation of metabolites, reactions and genes from `.tsv` files against an existing model |
| Biomass composition (`biomass/`) | `getBiomassFractions`, `scaleBiomassFraction`, `scaleBiomassPseudoreaction`, `setGAM` | Biomass-composition and growth-associated-maintenance (GAM) calibration; `tutorials/tutorial7.m` demonstrates the workflow |
| Localisation (`localization/`) | `assignCompartments`, `defaultCompartmentMap`, `getUniProtScores` | Deterministic MILP compartment assignment (alternative to the heuristic `predictLocalization`) |
| Localisation (`localization/`) | `parseScores` (changed) | Adds `'mulocdeep'`, `'compartments'` and `'uniprot'`; `'deeploc'` reads DeepLoc 2 output; the default predictor is `'deeploc'` (RAVEN 2: `'wolf'`); WoLF PSORT is removed (see [Backward-incompatible changes](#backward-incompatible-changes)) |
| Annotation (`annotation/`) | `assignSBOterms`, `loadDeltaGCSV`, `saveDeltaGCSV` | SBO term assignment; ΔG data CSV I/O |
| Conditions (`conditions/`) | `applyCondition` | Applies a condition given as a YAML file to a model, in a fixed order: exchange bounds, cofactor-pseudoreaction edits, biomass-stoichiometry deltas and per-reaction bound overrides |
| Infrastructure | `ravenModelFields` | Registry of every 1-D model field (entity type, default value), used by `permuteModel`, `removeReactions` and `curateModelFromTables` |
| Infrastructure | `progressReport`, `setRavenProgress` | Progress reporting with a selectable backend (for example a log for compute clusters) |
| Infrastructure | `splitProbForConditioning` (`solver/`) | Splitting of an optimisation problem for conditioning |

`randomSampling` changes the default: a RAVEN 2 call `randomSampling(model, n)` runs ACHR; adding `'method', 'randomObjective'` runs the RAVEN 2 method. `randomSampling` also gains the outputs and options `info`, `seed`, `thinning` and `nBurnin`.

The function documentation of `sampleCHRR` states that the polytope is rounded before sampling and mixing stays fast on strongly elongated polytopes such as enzyme-constrained models, and that `sampleACHR` does not round. The mixing speed was not measured.

`findPotentialErrors`, the parser functions and `diffModels` rule comparison are described in [Parsing of gene-reaction rules](#gpr-parsing). The reconstruction and curation functions for KEGG, homology and genome data are described in [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction).

---

(toolbox-deps)=
## Toolbox dependencies and installation

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| MATLAB version | No minimum stated; `readYAMLmodel` has a fallback for releases before R2020b (`readlines`) | No minimum stated; the code has no check that rejects an older release. `readYAMLmodel` keeps the fallback for releases before R2020b, `parseTaskList` calls `readcell` (R2019a) for Excel task lists and `addIdentifierPrefix` calls `regexpPattern` (R2020b). Continuous integration uses R2024b only. Older releases were not tested |
| Statistics and Machine Learning Toolbox | Required by `compareMultipleModels` (`mdscale`, `pdist`, `squareform` and `tsne`; an error without them) and by `compareRxnsGenesMetsComps` (`combnk`) | Optional in `compareMultipleModels`; without it the projection and heatmap clustering are skipped |
| Bioinformatics Toolbox | Required by `getKEGGModelForOrganism` when it builds missing per-KO alignments from a local KEGG dump (`fastaread` and `fastawrite`) | Not required (`io/readFasta.m` and `io/writeFasta.m`) |
| Optimization Toolbox | Required for `qMOMA` and `solveQP` (`quadprog`) | Not required (both removed) |
| Parallel Computing Toolbox | Optional; `parfor` loops (for example in `getAllowedBounds` and `randomSampling`) run serially without it | Optional; `parallelWorkersRAVEN` returns 0 workers when `runParallel` is false, which runs the `parfor` loops as plain loops |
| Excel I/O | Bundled Apache POI (Java) | Dependency-free OOXML writer |
| LP and MILP solver | Required (bundled `glpk`, or Gurobi, SCIP or COBRA) | Unchanged |
| External binaries | Committed to the repository (BLAST+, DIAMOND, HMMER); available offline after cloning | Fetched on first use as per-platform ZIPs into `src/external/<tool>`; for air-gapped installs the workflow `.github/workflows/release-bundle.yml` builds `RAVEN-<tag>-full.zip` with all platform binaries and attaches it to a published release (whether a given release carries it was not checked) |
| KEGG HMM libraries and reference data | Manual download or local build | Fetched on first use and cached |
| Installation self-check | `installation/checkInstallation.m` runs `importExportTests`, `solverTests` and the BLAST+, DIAMOND, HMMER, CD-HIT and MAFFT test files to fill its table of passed and failed tests | `checkRaven` in the repository root imports `empty.xml`, exports SBML, imports and exports YAML, exports Excel, solves a two-reaction LP per solver and downloads missing binaries without a prompt; `checkInstallation` forwards to it (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |

KEGG data, binaries and the checksum manifest come from releases of `toolbox-assets`; other downloads have other sources (listed below). KEGG data comes from the release tag that `keggDataVersion()` returns (`src/reconstruction/kegg/KEGG_VERSION.md`, tag `kegg118`). The binaries come from fixed tags set in `src/installation/downloadRavenBinaries.m`: `blast-2.17.0`, `diamond-2.1.17`, `hmmer-3.4.0` and, on Windows, `hmmer-3.3.2`. The checksums of downloaded files come from `manifest.json` of the `manifest-v3` release, read at download time. `setRavenSolver('scip')` on Windows downloads `scip_mex_win.zip` from the RAVEN v2.8.6 release on GitHub into `src/external/scip`; the repository holds no SCIP files, and other platforms need a manually installed SCIP. `getUniProtScores` queries rest.uniprot.org, `downloadGenomeData` downloads from NCBI and `checkRaven` reads the version file from GitHub. A RAVEN 3 clone needs network access for these downloads.

---

## Error and warning handling

RAVEN 3 raises errors and issues warnings with native `error()` and `warning()` calls. Of 411 `error` calls outside `src/external` (lines that contain `error(` and do not start with a comment), 301 carry an identifier, 242 of them in the `RAVEN:*` namespace. Of 94 `warning` calls counted by the same rule, 79 carry an identifier, 72 of them in the `RAVEN:*` namespace. Whether message texts of RAVEN 2 checks are preserved was not checked; a `try/catch` block that matches message text can be replaced by a match on the identifier where one exists. [Backward-incompatible changes](#backward-incompatible-changes) describes the `dispEM` replacement, and [Removed functionality](#removed-functionality) names the `utils/ravenList.m` helper.

`issues = checkModelStruct(model)` returns a structure array of the problems (`category`, `target` and `message`) for programmatic model QC and raises no error. Without an output argument the function raises errors or issues warnings as in RAVEN 2. The options `throwErrors` and `trimWarnings` (positional in RAVEN 2) can also be given as name-value pairs.
