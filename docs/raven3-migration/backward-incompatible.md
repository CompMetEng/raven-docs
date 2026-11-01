(backward-incompatible-changes)=
# Backward-incompatible changes

The list covers the changes found by comparing RAVEN 2.11.3 with RAVEN 3 in the code. The changelog of RAVEN 3 lists further bug fixes, which are named in the last row of the table of corrected behaviour. The changes are grouped into those that raise an error, those that give a different result without an error, changes to error and warning identifiers, changes that raise warnings and installation changes.

## Changes that raise errors

| RAVEN 2 usage | RAVEN 3 behaviour |
|---|---|
| `importExcelModel(...)` | Removed. Use `curation/curateModelFromTables.m` (input format `.tsv`), or convert the template to SBML and use `importModel`, or to YAML and use `readYAMLmodel` (see [Excel I/O](#excel-io)) |
| `importModel(...)` on SBML Level < 3, Level 3 without FBC v2, or any non-FBC SBML | Raises an error. The accepted format is SBML Level 3 Version 1 with FBC package version 2 (see [SBML I/O](#sbml-io)) |
| `exportToExcelFormat(model, fileName)` where `fileName` has no file name or no extension | RAVEN 2 exported tab-delimited text. RAVEN 3 raises an error for every extension other than `.xlsx`, including an empty one, with the message "only export to xlsx format is supported". RAVEN 2 already raised this error for a file name with another extension |
| `exportToTabDelimited(...)` | Removed |
| `getWoLFScores(...)` | Removed. WoLF PSORT support is removed |
| `parseScores(..., 'wolf', ...)` | Raises an error with a message that names `'deeploc'`, `'mulocdeep'`, `'compartments'` and `'uniprot'`. RAVEN 3 has no function that reads WoLF PSORT output files |
| `qMOMA(...)`, `solveQP(...)` | Removed. RAVEN 3 has no code that depends on `quadprog` of the Optimization Toolbox |
| `findGeneDeletions(...)` with `analysisType`, `refModel` or `oeFactor` | The arguments are removed together with `qMOMA` (MOMA-based over-expression analysis). The test types `'sgo'` and `'dgo'` are removed. Single and double gene deletion (`sgd`, `dgd`) by flux balance analysis (FBA) remain. More than the `'testType'` argument raises `parseRAVENargs:tooManyArgs` |
| `checkRxn(...)` | Removed, no direct successor. To find why a reaction cannot carry flux, use `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` or `gapfilling/checkProduction.m` |
| `dispEM(...)`, `followFluxes(...)`, `followChanged(...)`, `printModel(...)`, `mapCompartments(...)`, `getExpressionStructure(...)`, `getMetsInComp(...)` | Removed (see [Removed functionality](#removed-functionality) for the replacements, where one exists) |
| Anything under `external/metacyc/` | Subsystem removed (MetaCyc-based reconstruction, 7 functions). No replacement in RAVEN 3 |
| Anything under `pathway/` or `plotting/` | Subsystems removed: 16 functions for visualisation and plotting, such as `drawMap`, `drawPathway`, `markPathwayWithFluxes` and `setOmicDataToRxns`. No replacement in RAVEN 3; the COBRA Toolbox and Escher provide plotting |
| Anything under `legacy/` | Subsystem removed. No replacement in RAVEN 3 (see [Removed functionality](#removed-functionality)) |
| `getGenesFromKEGG`, `getMetsFromKEGG`, `getRxnsFromKEGG`, `constructMultiFasta`, `getWSLpath`, `getBlastFromExcel` | Removed (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getToolboxVersion(...)` | Removed as a standalone function. It is a local function of `exportForGit` |
| `parallelPoolRAVEN(...)` | Renamed `parallelWorkersRAVEN`, with a different signature and output (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |
| `getModelFromKEGG(keggPath, keepSpontaneous, keepUndefinedStoich, keepIncomplete, keepGeneral)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed and the function has four optional parameters |
| `getKEGGModelForOrganism(...)` with 13 to 15 positional arguments | The parameters `nSequences` and `seqIdentity` are removed. 14 or 15 arguments raise `parseRAVENargs:tooManyArgs`. A non-empty 13th argument (`nSequences` in RAVEN 2) is read as `globalModel` |
| `getPhylDist(keggPath, onlyInKingdom)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed |
| `writeYAMLmodel(model, fileName, preserveQuotes, sortIds)` with four arguments | Raises `parseRAVENargs:tooManyArgs`. RAVEN 3 has `(model, fileName, sortIds)` |
| `scoreModel(...)` with `'best'` at position 7, 8 or 9 among all arguments | Raises `RAVEN:badInput`. Positions 7, 8 and 9 are `isozymeScoring`, `complexScoring` and `multipleCellScoring`. The first two accept `'min'`, `'max'`, `'median'` and `'average'`, the third accepts `'max'` and `'average'` |
| `scoreModel(...)` with `hpaLevelScores` at position 9 among all arguments | Raises an error. Position 9 is `multipleCellScoring`, and `hpaLevelScores` is position 10 |

## Changes that alter results without an error

The same call with the same input model gives a different output. The changes fall into two groups: argument positions and defaults that change meaning, and corrected behaviour. Argument positions count all arguments of the call, including the required ones: in `scoreModel(model, hpaData, arrayData, tissue, celltype, ...)` the model is position 1 and `celltype` is position 5.

### Argument positions and defaults that change meaning

| Function | RAVEN 3 behaviour |
|---|---|
| `getModelFromKEGG(keggPath)` to `getModelFromKEGG(keggPath, keepSpontaneous, keepUndefinedStoich[, keepIncomplete])` | Calls with one to four positional arguments shift. The first argument (`keggPath` in RAVEN 2) is read as `keepSpontaneous` and has no effect. Each later argument is read as the next parameter in the RAVEN 2 order, so a different class of reactions is removed |
| `getPhylDist(keggPath)` | `keggPath` is read as `'onlyInKingdom'` and has no effect. The full distance matrix is returned |
| `writeYAMLmodel(model, fileName, true)` | The third argument is read as `sortIds`, so IDs are sorted. RAVEN 2 read it as `'preserveQuotes'` |
| `scoreModel` | `isozymeScoring` and `complexScoring` replace the single `multipleGeneScoring` of RAVEN 2. Reactions with an `and` rule get the minimum over the genes by default (`complexScoring`). RAVEN 2 scored every reaction with the maximum over all genes by default (`multipleGeneScoring` `'best'`) |
| `scoreModel(..., celltype, noGeneScore, 'average')` | `'average'` at position 7 among all arguments (`multipleGeneScoring` in RAVEN 2) is read as `isozymeScoring`, so it does not apply to `and` rules, which use `complexScoring` |
| `scoreModel(..., celltype, noGeneScore, multipleGeneScoring, 'average')` | `'average'` at position 8 among all arguments (`multipleCellScoring` in RAVEN 2) is read as `complexScoring` without an error, so the average is taken over the genes of an `and` rule and no longer over cell types |
| `scoreModel` output `geneScores` | Genes that are absent from the data receive `NaN`. The RAVEN 2 documentation states `-Inf`. |
| `scoreModel`, value names | RAVEN 2 accepted `'best'` for `multipleGeneScoring` and `multipleCellScoring`. RAVEN 3 uses `'max'` for `isozymeScoring`, `complexScoring` and `multipleCellScoring`. The parameter order is `celltype`, `noGeneScore`, `isozymeScoring`, `complexScoring`, `multipleCellScoring`, `hpaLevelScores` and `dataPrecedence` (default `'gene'`) |
| `parseScores(file)` | The default predictor is `'deeploc'`. RAVEN 2 used `'wolf'`. How a WoLF PSORT file is handled without a predictor was not run |
| `getModelFromHomology`, `strictness=3` | The best hit is the hit with the highest bitscore. RAVEN 2 selected the hit with the lowest E-value. No parameter selects the criterion (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getModelFromHomology`, `minLen` | The default is `100`, in RAVEN 2 `200` |
| `getKEGGModelForOrganism`, `cutOff` | The default is `10^-30`, in RAVEN 2 `10^-50` |
| `getKEGGModelForOrganism`, `minScoreRatioG` | The default is `0.9`, in RAVEN 2 `0.8` |

### Corrected behaviour

| Function | RAVEN 3 behaviour |
|---|---|
| `getModelFromHomology`, merging of gene-reaction rules (GPR) | Gene substitution uses exact tokens. RAVEN 2 used regular expressions or `strrep` |
| `removeGenes`, `addRxns` | `removeGenes` evaluates the rule as a tree, so isozymes and complexes are handled. `addRxns` splits a rule at space-bounded `and` and `or` tokens, so a gene ID such as `band1` is not cut, and builds no tree. RAVEN 2 used substring matching. `expandModel` parses the rule with `grRuleToDNF`, leaves a rule that cannot be parsed (`RAVEN:badGrRule`) unchanged and lists the reaction in `rxnToCheck`, and raises `RAVEN:grRuleTooComplex` for a rule that expands to more than 10000 isozymes; RAVEN 2 split the rule string at `' or '` and `' and '` (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `findPotentialErrors` | The changelog of RAVEN 3 states that the check uses a parse tree. The effect on results was not compared (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `changeGrRules(..., 'replace', false)` onto a reaction without genes | Produces a valid grRule. RAVEN 2 wrapped the new rule as `() or (X)`, which RAVEN 3 cannot parse |
| `simplifyModel` | Keeps the boundary constraint (`b`) of a task on a metabolite without reactions. RAVEN 2.11.3 removed such metabolites, so the task check can give a different result in RAVEN 3 (not run; see [Gap-filling and context-specific model extraction](#ftinit)) |
| `simplifyModel` with `constrainReversible` on a model without a reversible reaction | The step changes nothing. RAVEN 2 raised an error, because `getAllowedBounds` takes an empty reaction list as all reactions (error taken from the changelog; not reproduced) |
| `ftINITInternalAlg` | With `allowExcretion` true, the metabolite balance is constrained to `S*v >= 0`. RAVEN 2 had the sense of the constraint inverted |
| `ravenCobraWrapper` | The conversion of `grRules` to the COBRA `rules` field handles gene IDs that contain regular-expression metacharacters. RAVEN 2 did not escape them (see [RAVEN⇄COBRA interoperability](#raven-cobra-interoperability)) |
| `mergeCompartments` | The merged metabolite is the copy in compartment `s`, otherwise the copy whose ID sorts first (character code order), with every field of that copy. RAVEN 2 kept the copy that came first in `model.mets` |
| `permuteModel`, `optimizeProb`, `getFluxZ`, `convertToIrrev`, `replaceMets`, `setExchangeBounds`, `fitParameters`, `guessComposition` | The changelog of RAVEN 3 lists a bug fix for each function. The effect on results was not checked. The default `method` of `randomSampling` is `'achr'`, so `randomSampling(model, n)` no longer runs the random-objective method of RAVEN 2 (`'randomObjective'` selects it); `goodRxns` is empty for `'achr'` and `'chrr'`; the function has the parameters `nObjectives`, `seed`, `method`, `thinning` and `nBurnin` and a third output `info`. The changelog lists further fixes that can change results, for example for `mergeLinear`, `mergeModels`, `closeModel`, `addTransport`, `getExchangeRxns`, `removeLowScoreGenes`, `getMinNrFluxes`, `reporterMetabolites`, `getElementalBalance`, `checkModelStruct` and `deleteUnusedGenes`; these were not checked |

## Changes to error and warning identifiers

- RAVEN 2 raised errors through `dispEM` with an empty identifier (`MException('', ...)`), so no RAVEN 2 script could catch on `err.identifier`. RAVEN 3 replaces `dispEM` with `error()` and `warning()` calls. `RAVEN:badInput` is used in 220 lines and `RAVEN:warning` in 63 lines of `src/` and the root `.m` files (non-comment lines that contain the identifier). Further identifiers are `RAVEN:modelError`, `RAVEN:badGrRule`, `RAVEN:infeasibleModel`, `RAVEN:infeasible`, `RAVEN:sampling`, `RAVEN:grRuleTooComplex`, `RAVEN:deprecated`, `RAVEN:legacyMethod`, `RAVEN:notMainBranch`, `RAVEN:glpkMILP`, `RAVEN:fetchToolboxAsset:unverified`, `RAVEN:fetchToolboxAsset:checksum`, `RAVEN:fetchToolboxAsset:manifest`, `RAVEN:runSuppOrth:supportLv`, `RAVEN:runSuppOrth:failed`, `RAVEN:runSuppOrth:notFound`, `RAVEN:hitsFromSuppOrth:unmappedProteins`, `parseRAVENargs:tooManyArgs`, `parseRAVENargs:noSpec` and `getPhylDist:noData`. The list is not exhaustive: identifiers in other namespaces, such as `renameModelGenes:*`, `setGAM:*` and `parseYAML:*`, also exist. Not every call carries an identifier. Scripts can match on `err.identifier` for the calls that carry one.
- Whether `try/catch` blocks that match on message text still match was not compared message by message.

## Changes that raise warnings

- `getINITModel` and `runINIT` issue a one-time notice with the identifier `RAVEN:legacyMethod` that points at `ftINIT`. `warning('off','RAVEN:legacyMethod')` silences it. The help text of both functions states that the function remains supported, although the changelog of RAVEN 3 marks both functions deprecated. See [Gap-filling and context-specific model extraction](#ftinit).
- `makeSomething`, `consumeSomething`, `canProduce` and `canConsume` are wrappers in the folder `deprecated/` around `findLeakMetabolite` and `canExchange`. They issue a one-time `RAVEN:deprecated` warning that states that they will be removed in the next major release.
- `checkInstallation` is `checkRaven` in RAVEN 3, moved from `installation/` to the repository root, with the same signature (`[currVer, installType] = checkRaven(developMode, checkBinaries)`). `checkInstallation` forwards every argument and output to `checkRaven` and issues a `RAVEN:deprecated` warning that names `checkRaven` on every call. The wrapper will be removed in the next major release.

## Installation changes

RAVEN 3 does not contain the KEGG HMM libraries and the external binaries (BLAST+, DIAMOND, HMMER, cd-hit, MAFFT, WoLF PSORT and SCIP) or Apache POI in the repository. It fetches the KEGG HMM libraries and reference tables and the BLAST+, DIAMOND and HMMER binaries from the [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository the first time a function needs them, so internet access is required on first use. The binaries are stored in `src/external/<tool>`. SCIP for Windows is downloaded by `setRavenSolver` from the RAVEN v2.8.6 GitHub release. An offline bundle of the binaries is available as a `*-binaries` RAVEN release. What is fetched and where it is cached is described in [Download data and binaries](../installation/data-and-binaries.md). The air-gapped install and the dependency comparison are in [Toolbox dependencies and installation](#toolbox-deps).
