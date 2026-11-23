(backward-incompatible-changes)=
# Backward-incompatible changes

The changes below were found by comparing RAVEN 2.11.3 with RAVEN 3 in the code. They are grouped into changes that raise an error, changes that give a different result without an error, changes to error and warning identifiers, changes that raise warnings, and installation changes. The changelog of RAVEN 3 lists further bug fixes. Those whose effect was not checked are named after the table of corrected behaviour.

## Changes that raise errors

| RAVEN 2 usage | RAVEN 3 behaviour |
|---|---|
| `importExcelModel(...)` | Removed. Use `curation/curateModelFromTables.m` (input format `.tsv`). Alternatively convert the template to SBML and read it with `importModel`, or to YAML and read it with `readYAMLmodel` (see [Excel I/O](#excel-io)) |
| `importModel(...)` on SBML Level < 3, on Level 3 without FBC version 2, or on any SBML without FBC | Raises an error. The accepted format is SBML Level 3 Version 1 with FBC package version 2 (see [SBML I/O](#sbml-io)) |
| `exportToExcelFormat(model, fileName)` where `fileName` has no file name or no extension | RAVEN 2 exported tab-delimited text. RAVEN 3 raises the error "only export to xlsx format is supported" for every extension other than `.xlsx`, an empty one included. RAVEN 2 already raised this error for a file name with a different extension |
| `exportToTabDelimited(...)` | Removed |
| `getWoLFScores(...)` | Removed, with all WoLF PSORT support |
| `parseScores(..., 'wolf', ...)` | Raises an error whose message names `'deeploc'`, `'mulocdeep'`, `'compartments'` and `'uniprot'`. RAVEN 3 has no function that reads WoLF PSORT output files |
| `qMOMA(...)`, `solveQP(...)` | Removed. RAVEN 3 has no code that depends on `quadprog` of the Optimization Toolbox |
| `findGeneDeletions(...)` with `analysisType`, `refModel` or `oeFactor` | The arguments are removed together with `qMOMA` (MOMA-based over-expression analysis), and so are the test types `'sgo'` and `'dgo'`. Single and double gene deletion (`sgd`, `dgd`) by flux balance analysis (FBA) remain. More than the `'testType'` argument raises `parseRAVENargs:tooManyArgs` |
| `checkRxn(...)` | Removed without a direct successor. To find why a reaction cannot carry flux, use `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` or `gapfilling/checkProduction.m` |
| `dispEM(...)`, `followFluxes(...)`, `followChanged(...)`, `printModel(...)`, `mapCompartments(...)`, `getExpressionStructure(...)`, `getMetsInComp(...)` | Removed. [Removed functionality](#removed-functionality) gives the replacements where one exists |
| Any function in `external/metacyc/` | Folder removed, with the 7 functions of the MetaCyc-based reconstruction. RAVEN 3 has no replacement |
| Any function in `pathway/` or `plotting/` | Folders removed, with 16 functions for visualisation and plotting, such as `drawMap`, `drawPathway`, `markPathwayWithFluxes` and `setOmicDataToRxns`. RAVEN 3 has no replacement; the COBRA Toolbox and Escher provide plotting |
| Any function in `legacy/` | Folder removed. RAVEN 3 has no replacement (see [Removed functionality](#removed-functionality)) |
| `getGenesFromKEGG`, `getMetsFromKEGG`, `getRxnsFromKEGG`, `constructMultiFasta`, `getWSLpath`, `getBlastFromExcel` | Removed (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getToolboxVersion(...)` | Removed as a function of its own. It is a local function of `exportForGit` |
| `parallelPoolRAVEN(...)` | Renamed `parallelWorkersRAVEN`, with a different signature and output (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |
| `getModelFromKEGG(keggPath, keepSpontaneous, keepUndefinedStoich, keepIncomplete, keepGeneral)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed and the function has four optional parameters |
| `getKEGGModelForOrganism(...)` with 13 to 15 positional arguments | The parameters `nSequences` and `seqIdentity` are removed. A call with 14 or 15 arguments raises `parseRAVENargs:tooManyArgs`. A non-empty 13th argument, which is `nSequences` in RAVEN 2, is read as `globalModel` |
| `getPhylDist(keggPath, onlyInKingdom)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed |
| `writeYAMLmodel(model, fileName, preserveQuotes, sortIds)` with four arguments | Raises `parseRAVENargs:tooManyArgs`. The RAVEN 3 signature is `(model, fileName, sortIds)` |
| `scoreModel(...)` with `'best'` at position 7, 8 or 9 among all arguments | Raises `RAVEN:badInput`. Positions 7, 8 and 9 are `isozymeScoring`, `complexScoring` and `multipleCellScoring`. The first two accept `'min'`, `'max'`, `'median'` and `'average'`, and the third accepts `'max'` and `'average'` |
| `scoreModel(...)` with `hpaLevelScores` at position 9 among all arguments | Raises an error. Position 9 is `multipleCellScoring`, and `hpaLevelScores` is position 10 |

## Changes that alter results without an error

The same call on the same model gives a different output. Positions count all arguments of the call, required ones included: in `scoreModel(model, hpaData, arrayData, tissue, celltype, ...)` the model is position 1 and `celltype` is position 5.

### Argument positions and defaults that change meaning

| Function | RAVEN 3 behaviour |
|---|---|
| `getModelFromKEGG(keggPath)` to `getModelFromKEGG(keggPath, keepSpontaneous, keepUndefinedStoich[, keepIncomplete])` | A call with one to four positional arguments shifts. The first argument, `keggPath` in RAVEN 2, is read as `keepSpontaneous` and has no effect. Each later argument is read as the next parameter in the RAVEN 2 order, so a different class of reactions is removed |
| `getPhylDist(keggPath)` | `keggPath` is read as `'onlyInKingdom'` and has no effect. The function returns the full distance matrix |
| `writeYAMLmodel(model, fileName, true)` | The third argument is read as `sortIds`, so the IDs are sorted. RAVEN 2 read it as `'preserveQuotes'` |
| `scoreModel` | `isozymeScoring` and `complexScoring` replace the single `multipleGeneScoring` of RAVEN 2. By default (`complexScoring`) a reaction with an `and` rule gets the minimum over its genes. RAVEN 2 scored every reaction with the maximum over all its genes by default (`multipleGeneScoring` `'best'`) |
| `scoreModel(..., celltype, noGeneScore, 'average')` | `'average'` at position 7 among all arguments, which is `multipleGeneScoring` in RAVEN 2, is read as `isozymeScoring`. It does not apply to `and` rules, which use `complexScoring` |
| `scoreModel(..., celltype, noGeneScore, multipleGeneScoring, 'average')` | `'average'` at position 8 among all arguments, which is `multipleCellScoring` in RAVEN 2, is read as `complexScoring` without an error. The average runs over the genes of an `and` rule; RAVEN 2 averaged over the cell types |
| `scoreModel`, output `geneScores` | A gene that is absent from the data receives `NaN`. The RAVEN 2 documentation states `-Inf` |
| `scoreModel`, value names | RAVEN 2 accepted `'best'` for `multipleGeneScoring` and `multipleCellScoring`. RAVEN 3 uses `'max'` for `isozymeScoring`, `complexScoring` and `multipleCellScoring`. The parameter order is `celltype`, `noGeneScore`, `isozymeScoring`, `complexScoring`, `multipleCellScoring`, `hpaLevelScores` and `dataPrecedence` (default `'gene'`) |
| `parseScores(file)` | The default predictor is `'deeploc'`. RAVEN 2 used `'wolf'`. How a WoLF PSORT file is handled without a predictor was not run |
| `randomSampling(model, n)` | The default `method` is `'achr'`. RAVEN 2 ran the random-objective method, which `'randomObjective'` selects. The output `goodRxns` is empty for `'achr'` and `'chrr'`. The function has the parameters `nObjectives`, `seed`, `method`, `thinning` and `nBurnin` and a third output, `info` |
| `getModelFromHomology`, `strictness=3` | The best hit is the hit with the highest bitscore. RAVEN 2 selected the hit with the lowest E-value. No parameter selects the criterion (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getModelFromHomology`, `minLen` | The default is `100`. In RAVEN 2 it was `200` |
| `getKEGGModelForOrganism`, `cutOff` | The default is `10^-30`. In RAVEN 2 it was `10^-50` |
| `getKEGGModelForOrganism`, `minScoreRatioG` | The default is `0.9`. In RAVEN 2 it was `0.8` |

### Corrected behaviour

| Function | RAVEN 3 behaviour |
|---|---|
| `getModelFromHomology`, merging of gene-reaction rules (GPR) | Gene substitution uses exact tokens. RAVEN 2 used regular expressions or `strrep` |
| `removeGenes`, `addRxns` | `removeGenes` evaluates the rule as a tree, so isozymes and complexes are handled. `addRxns` splits a rule at the space-bounded tokens `and` and `or`, so a gene ID such as `band1` stays whole, and it builds no tree. RAVEN 2 matched substrings |
| `expandModel` | The rule is parsed with `grRuleToDNF`. A rule that cannot be parsed (`RAVEN:badGrRule`) stays unchanged and its reaction is listed in `rxnToCheck`. A rule that expands to more than 10000 isozymes raises `RAVEN:grRuleTooComplex`. RAVEN 2 split the rule string at `' or '` and `' and '` (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `findPotentialErrors` | The changelog of RAVEN 3 states that the check uses a parse tree. The effect on results was not compared (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `changeGrRules(..., 'replace', false)` onto a reaction without genes | Produces a valid grRule. RAVEN 2 wrapped the new rule as `() or (X)`, which RAVEN 3 cannot parse |
| `simplifyModel` | Keeps the boundary constraint (`b`) of a task on a metabolite without reactions. RAVEN 2.11.3 removed such metabolites, so the task check can give a different result in RAVEN 3 (not run; see [Gap-filling and context-specific model extraction](#ftinit)) |
| `simplifyModel` with `constrainReversible` on a model without a reversible reaction | The step changes nothing. RAVEN 2 raised an error, because `getAllowedBounds` takes an empty reaction list as all reactions (the error is taken from the changelog and was not reproduced) |
| `ftINITInternalAlg` | With `allowExcretion` true, the metabolite balance is constrained to `S*v >= 0`. RAVEN 2 had the sense of the constraint inverted |
| `ravenCobraWrapper` | The conversion of `grRules` to the COBRA `rules` field works on gene IDs that contain regular-expression metacharacters. RAVEN 2 did not escape them (see [RAVEN⇄COBRA interoperability](#raven-cobra-interoperability)) |
| `mergeCompartments` | The merged metabolite is the copy in compartment `s` or, failing that, the copy whose ID sorts first in character code order, with every field of that copy. RAVEN 2 kept the copy that came first in `model.mets` |

The changelog of RAVEN 3 lists a bug fix for each of `permuteModel`, `optimizeProb`, `getFluxZ`, `convertToIrrev`, `replaceMets`, `setExchangeBounds`, `fitParameters` and `guessComposition`. It lists further fixes that can change results, for example for `mergeLinear`, `mergeModels`, `closeModel`, `addTransport`, `getExchangeRxns`, `removeLowScoreGenes`, `getMinNrFluxes`, `reporterMetabolites`, `getElementalBalance`, `checkModelStruct` and `deleteUnusedGenes`. The effect of these fixes on results was not checked.

## Changes to error and warning identifiers

RAVEN 2 raised its errors through `dispEM` with an empty identifier (`MException('', ...)`), so no RAVEN 2 script could catch an error by `err.identifier`. RAVEN 3 replaces `dispEM` with `error()` and `warning()` calls. Not every call has an identifier, and a script can match on `err.identifier` for the calls that do. `RAVEN:badInput` appears in 220 lines and `RAVEN:warning` in 63 lines of `src/` and the root `.m` files (non-comment lines that contain the identifier). Further identifiers in the `RAVEN:` namespace are `RAVEN:modelError`, `RAVEN:badGrRule`, `RAVEN:infeasibleModel`, `RAVEN:infeasible`, `RAVEN:sampling`, `RAVEN:grRuleTooComplex`, `RAVEN:deprecated`, `RAVEN:legacyMethod`, `RAVEN:notMainBranch`, `RAVEN:glpkMILP`, `RAVEN:fetchToolboxAsset:unverified`, `RAVEN:fetchToolboxAsset:checksum`, `RAVEN:fetchToolboxAsset:manifest`, `RAVEN:runSuppOrth:supportLv`, `RAVEN:runSuppOrth:failed`, `RAVEN:runSuppOrth:notFound` and `RAVEN:hitsFromSuppOrth:unmappedProteins`. Identifiers in other namespaces include `parseRAVENargs:tooManyArgs`, `parseRAVENargs:noSpec`, `getPhylDist:noData`, `renameModelGenes:*`, `setGAM:*` and `parseYAML:*`. The list is not exhaustive.

Whether `try/catch` blocks that match on message text match was not compared message by message.

## Changes that raise warnings

- `getINITModel` and `runINIT`, the functions of the legacy tINIT method, issue a one-time notice with the identifier `RAVEN:legacyMethod` that points to `ftINIT`. `warning('off','RAVEN:legacyMethod')` silences it. The help text of both functions states that the function remains supported, although the changelog of RAVEN 3 marks both as deprecated (see [Gap-filling and context-specific model extraction](#ftinit)).
- `makeSomething`, `consumeSomething`, `canProduce` and `canConsume` are wrappers in the folder `deprecated/` around `findLeakMetabolite` and `canExchange`. They issue a one-time `RAVEN:deprecated` warning that they will be removed in the next major release.
- `checkInstallation` is `checkRaven` in RAVEN 3, moved from `installation/` to the repository root, with the same signature: `[currVer, installType] = checkRaven(developMode, checkBinaries)`. The wrapper `checkInstallation` forwards every argument and output to `checkRaven` and issues a `RAVEN:deprecated` warning that names `checkRaven` on every call. The wrapper will be removed in the next major release.

## Installation changes

The repository of RAVEN 3 does not contain the KEGG HMM libraries, the external binaries (BLAST+, DIAMOND, HMMER, cd-hit, MAFFT, WoLF PSORT and SCIP) or Apache POI. The first time a function needs them, RAVEN 3 fetches the KEGG HMM libraries and reference tables and the BLAST+, DIAMOND and HMMER binaries from the [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository, so the first use requires internet access. The binaries are stored in `src/external/<tool>`. The function `setRavenSolver` downloads SCIP for Windows from the RAVEN v2.8.6 GitHub release. An offline bundle of the binaries is available as a `*-binaries` RAVEN release. [Download data and binaries](../installation/data-and-binaries.md) describes what is fetched and where it is cached, and [Toolbox dependencies and installation](#toolbox-deps) covers the air-gapped install and the dependency comparison.
