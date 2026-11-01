# New functionality, dependencies and error handling

RAVEN 3 changes gap-filling and the extraction of context-specific models with `ftINIT`, adds functions, depends on fewer MATLAB toolboxes, and handles errors in another way.

(ftinit)=
## Gap-filling and context-specific model extraction

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `fillGaps` algorithm | One built-in mixed-integer linear programming (MILP) strategy that maximises connectivity | The same strategy is the default (`algorithm` `'reference'`). The option `algorithm` adds `'fastLP'`, `'swiftLP'`, `'gapfillMILP'` and `'topological'` |
| `fillGaps` positional arguments | `allowNetProduction, useModelConstraints, supressWarnings, rxnScores` | The first four optional arguments are unchanged. `params` is the 7th and `algorithm` the 8th argument, followed by `epsilon`, `minGrowth` and `verbose`. All can also be given as name-value pairs |
| `ftINIT` tie-breaking | Depends on the solver seed, and the retries of the MILP set the seed to 1234. The dependence was not measured | The option `resolveTies` adds a best-effort selection among tied solutions. The resulting dependence on the seed was not measured |
| `ftINIT` proof of optimality | Retries with an increasing relative gap, which is derived from an absolute-gap setting and the last objective value | The option `proveAbsGap` proves each stage to a fixed absolute gap in one solve (`MIPGap` 0) |
| `ftINIT` positional arguments | `transcrData` to `verbose` are the 5th to 11th arguments | Unchanged. `resolveTies` and `proveAbsGap` follow `verbose` as the 12th and 13th arguments and are off by default |
| `fitTasks` gap-fill mode | One behaviour, equivalent to `'merge'` | `gapFillMode` is `'merge'` (default, as in RAVEN 2) or `'preMerged'` |
| `fitTasks` outputs | `[outModel, addedRxns]` | `[outModel, addedRxns, failedTasks]` |

Positions in the migration pages count all arguments of the call, required ones included. The functions `getINITModel` and `runINIT` are described in [Renamed and merged functions](#renamed-merged-and-consolidated-functions).

### Algorithms of `fillGaps`

The option `algorithm` of `fillGaps` selects one of these algorithms. A value that is none of them runs the algorithm `'reference'`.

- `'fastLP'` and `'swiftLP'` relax the problem to a linear program (LP) in the manner of FASTCORE and SWIFTCORE.
- `'gapfillMILP'` is a MILP with a growth floor. Reactions that are already in the draft model keep their bounds, so a reaction with the wrong direction is not changed.
- `'topological'` is a pre-screen of producibility by breadth-first search. It does not modify the model, requires a reference model and uses only the first one.

The function `fillGaps` calls `gapFillTopological` with the defaults of that function. The seeds are the metabolites of the exchange reactions that `getExchangeRxns` classes as `'uptake'` or `'reverse'`. The targets are the metabolites of the first objective reaction, and a model without an objective reaction raises `RAVEN:badInput`.

### Gap-filling in `fitTasks`

With `gapFillMode` set to `'preMerged'`, `fitTasks` expects a reference model that already contains the reactions of the model. No merge is then needed for each task, and `ftINITFillGaps` fills the gaps. How `fitTasks` treats a task that requires net production of a metabolite without reactions was not checked.

### Tie-breaking in `ftINIT`

With `resolveTies`, each MILP step of `ftINIT` holds the score at its optimum and then chooses among the tied solutions in phases, each with a time limit. The phases select, in this order:

1. the fewest kept removable reactions;
2. the lowest summed ID rank of those reactions, where a merged reaction is ranked by the smallest original ID of its group;
3. the least total absolute flux;
4. the least backward flux, weighted by ID rank.

The function `ftINITInternalAlg` has the arguments `resolveTies` (13th), `rankKeys` (14th, default `model.rxns`) and `pinFluxes` (15th, default `true`). With `pinFluxes` set to `false` the two flux phases are skipped, and `ftINIT` passes `false` in its last step. A step whose first solve stops at the time limit keeps that solution without the phases. The count phase and the rank phase get half of the step time limit each, and a phase that fails issues a warning.

---

(new-functionality)=
## New functionality

The table lists the functions that RAVEN 3 adds. The functions `randomSampling` and `parseScores` exist in RAVEN 2 and behave differently.

| Area | Functions | Capability |
|---|---|---|
| Flux sampling (`analysis/`) | `sampleACHR`, `sampleCHRR`, `sampleMaxVolEllipse`, `sampleChebyshevCenter`, `sampleWarmupPoints` | ACHR (hit-and-run) and CHRR (hit-and-run with rounding), two near-uniform Markov chain Monte Carlo (MCMC) samplers |
| Flux sampling (`analysis/`) | `randomSampling` (changed) | Dispatcher with the option `'method'`: `'achr'` (default), `'chrr'` and `'randomObjective'` (the RAVEN 2 method) |
| Flux analysis and quality control (QC) | `compareFluxes` | Compares flux vectors |
| Flux analysis and QC | `getMinimalMedium` | Searches a minimal medium with a MILP |
| Flux analysis and QC | `traceFluxPath` | Traces the path of the highest flux fraction between two reactions |
| Flux analysis and QC | `walkFluxes` | Navigates the flux neighbourhood interactively |
| Flux analysis and QC | `modelSummary` (`queries/`) | Prints a summary of a model and its fluxes |
| Model comparison (`comparison/`) | `diffModels` | Compares two models by ID: stoichiometry, bounds, objective, `grRules`, EC codes and metabolite properties. It is separate from the overlap comparison of `compareMultipleModels` |
| Manipulation | `findDuplicateRxns` | Query for reactions with the same stoichiometry |
| Genome-based curation (`curation/`) | `downloadGenomeData`, `getGeneData`, `processProteinFastaFile` | Pipeline from an NCBI genome accession to a gene ID mapping table |
| Genome-based curation (`curation/`) | `renameModelGenes` | Renames genes in bulk |
| Genome-based curation (`curation/`) | `curateModelFromTables` | Curates metabolites, reactions and genes of an existing model in bulk from `.tsv` files |
| Biomass composition (`biomass/`) | `getBiomassFractions`, `scaleBiomassFraction`, `scaleBiomassPseudoreaction`, `setGAM` | Calibration of the biomass composition and of the growth-associated maintenance (GAM). `tutorials/tutorial7.m` demonstrates the workflow |
| Localisation (`localization/`) | `assignCompartments`, `defaultCompartmentMap`, `getUniProtScores` | Deterministic assignment of compartments by MILP, as an alternative to the heuristic `predictLocalization` |
| Localisation (`localization/`) | `parseScores` (changed) | Adds `'mulocdeep'`, `'compartments'` and `'uniprot'`. The predictor `'deeploc'` reads DeepLoc 2 output and is the default (RAVEN 2: `'wolf'`). WoLF PSORT is removed (see [Backward-incompatible changes](#backward-incompatible-changes)) |
| Annotation (`annotation/`) | `assignSBOterms`, `loadDeltaGCSV`, `saveDeltaGCSV` | Assignment of SBO terms; CSV I/O of ΔG data |
| Conditions (`conditions/`) | `applyCondition` | Applies a condition from a YAML file to a model in a fixed order: exchange bounds, edits of cofactor pseudoreactions, changes of the biomass stoichiometry, and bound overrides per reaction |
| Infrastructure | `ravenModelFields` | Registry of every one-dimensional model field (entity type, default value), used by `permuteModel`, `removeReactions` and `curateModelFromTables` |
| Infrastructure | `progressReport`, `setRavenProgress` | Progress reporting with a selectable backend, for example a log file on compute clusters |
| Infrastructure | `splitProbForConditioning` (`solver/`) | Splits an optimisation problem to improve its conditioning |

The call `randomSampling(model, n)` runs ACHR, where RAVEN 2 ran its own method. Adding `'method', 'randomObjective'` runs the RAVEN 2 method. The function also gains the outputs and options `info`, `seed`, `thinning` and `nBurnin`.

The function documentation of `sampleCHRR` states that the polytope is rounded before sampling and that mixing stays fast on strongly elongated polytopes such as enzyme-constrained models. It states that `sampleACHR` does not round. The mixing speed was not measured.

[Parsing of gene-reaction rules](#gpr-parsing) describes `findPotentialErrors`, the parser functions and the rule comparison of `diffModels`. [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction) describes the reconstruction and curation functions for KEGG, homology and genome data.

---

(toolbox-deps)=
## Toolbox dependencies and installation

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| MATLAB version | No minimum stated. `readYAMLmodel` has a fallback for releases before R2020b (`readlines`) | No minimum stated, and the code has no check that rejects an older release. `readYAMLmodel` keeps the fallback for releases before R2020b, `parseTaskList` calls `readcell` (R2019a) for Excel task lists, and `addIdentifierPrefix` calls `regexpPattern` (R2020b). Continuous integration uses R2024b only, and older releases were not tested |
| Statistics and Machine Learning Toolbox | Required by `compareMultipleModels` (`mdscale`, `pdist`, `squareform` and `tsne`, with an error without them) and by `compareRxnsGenesMetsComps` (`combnk`) | Optional in `compareMultipleModels`. Without it the projection and the clustering of the heatmap are skipped |
| Bioinformatics Toolbox | Required by `getKEGGModelForOrganism` when it builds missing per-KO alignments from a local KEGG dump (`fastaread` and `fastawrite`) | Not required (`io/readFasta.m` and `io/writeFasta.m`) |
| Optimization Toolbox | Required for `qMOMA` and `solveQP` (`quadprog`) | Not required, because both functions are removed |
| Parallel Computing Toolbox | Optional. The `parfor` loops, for example in `getAllowedBounds` and `randomSampling`, run serially without it | Optional. `parallelWorkersRAVEN` returns 0 workers when `runParallel` is false, which runs the `parfor` loops as plain loops |
| Excel I/O | Bundled Apache POI (Java) | OOXML writer without dependencies |
| LP and MILP solver | Required: bundled `glpk`, or Gurobi, SCIP or COBRA | Unchanged |
| External binaries | Committed to the repository (BLAST+, DIAMOND, HMMER) and available offline after cloning | Fetched on first use as ZIP files per platform into `src/external/<tool>`. For air-gapped installs the workflow `.github/workflows/release-bundle.yml` builds `RAVEN-<tag>-full.zip` with the binaries of all platforms and attaches it to a published release. Whether a given release carries it was not checked |
| KEGG HMM libraries and reference data | Manual download or local build | Fetched on first use and cached |
| Installation self-check | `installation/checkInstallation.m` runs `importExportTests`, `solverTests` and the test files of BLAST+, DIAMOND, HMMER, CD-HIT and MAFFT to fill its table of passed and failed tests | `checkRaven` in the repository root imports `empty.xml`, exports SBML, imports and exports YAML, exports Excel, solves a two-reaction LP per solver and downloads missing binaries without a prompt. `checkInstallation` forwards to it (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |

KEGG data, binaries and the checksum manifest come from releases of `toolbox-assets`. Other downloads have other sources.

- KEGG data comes from the release tag that `keggDataVersion()` returns (`src/reconstruction/kegg/KEGG_VERSION.md`, tag `kegg118`).
- The binaries come from the fixed tags in `src/installation/downloadRavenBinaries.m`: `blast-2.17.0`, `diamond-2.1.17`, `hmmer-3.4.0` and, on Windows, `hmmer-3.3.2`.
- The checksums of downloaded files come from `manifest.json` of the `manifest-v3` release, which is read at download time.
- `setRavenSolver('scip')` on Windows downloads `scip_mex_win.zip` from the RAVEN v2.8.6 release on GitHub into `src/external/scip`. The repository holds no SCIP files, and other platforms need a SCIP installation made by hand.
- `getUniProtScores` queries rest.uniprot.org, `downloadGenomeData` downloads from NCBI, and `checkRaven` reads the version file from GitHub.

A RAVEN 3 clone needs network access for these downloads.

---

## Error and warning handling

RAVEN 3 raises errors and issues warnings with `error()` and `warning()`. Outside `src/external` there are 411 `error` calls, counted as lines that contain `error(` and do not start with a comment. Of these, 301 carry an identifier, and 242 of those are in the `RAVEN:*` namespace. By the same rule there are 94 `warning` calls, of which 79 carry an identifier and 72 are in the `RAVEN:*` namespace. Whether the message texts of the RAVEN 2 checks are preserved was not checked. A `try/catch` block that matches message text can be replaced by a match on the identifier where one exists. [Backward-incompatible changes](#backward-incompatible-changes) describes the replacement of `dispEM`, and [Removed functionality](#removed-functionality) names the helper `utils/ravenList.m`.

The call `issues = checkModelStruct(model)` returns a structure array of the problems (`category`, `target` and `message`) for programmatic model QC and raises no error. Without an output argument the function raises errors or issues warnings as in RAVEN 2. The options `throwErrors` and `trimWarnings`, which are positional in RAVEN 2, can also be given as name-value pairs.
