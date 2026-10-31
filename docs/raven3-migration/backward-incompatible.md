(backward-incompatible-changes)=
# Backward-incompatible changes

The list covers the changes found by comparing RAVEN 2.11.3 with RAVEN 3. The changes are grouped into those that raise an error, those that give a different result without an error, those to error and warning identifiers, those that raise warnings and installation changes.

## Changes that raise errors

| RAVEN 2 usage | RAVEN 3 behaviour |
|---|---|
| `importExcelModel(...)` | Removed; use `curation/curateModelFromTables.m` (input format `.tsv`, not `.xlsx`) or convert the template to YAML or SBML and use `importModel` (see [Excel I/O](#excel-io)) |
| `importModel(...)` on SBML Level < 3, Level 3 without FBC v2, or any non-FBC SBML | Raises an error; only SBML Level 3 Version 1, FBC package version 2 is accepted (see [SBML I/O](#sbml-io)) |
| `exportToExcelFormat(model, fileName)` where `fileName` is a bare path (no `.xlsx`) | No fallback to tab-delimited text export; raises an error with the message "only export to xlsx format is supported" |
| `exportToTabDelimited(...)` | Removed (dead-code path) |
| `getWoLFScores(...)` | Removed; WoLF PSORT support is fully removed |
| `parseScores(..., 'wolf', ...)` | Raises an error on `'predictor','wolf'`, with a message pointing to `'deeploc'`, `'mulocdeep'`, `'compartments'` or `'uniprot'`; there is no in-toolbox migration path for existing WoLF PSORT output files |
| `qMOMA(...)`, `solveQP(...)` | Removed (the last dependency of RAVEN on `quadprog` from the Optimization Toolbox) |
| `findGeneDeletions(...)` with `analysisType`, `refModel` or `oeFactor` | Arguments removed together with `qMOMA` (MOMA-based over-expression analysis); only single and double gene deletion (`sgd`, `dgd`) by flux balance analysis (FBA) remains. More than the `'testType'` argument raises `parseRAVENargs:tooManyArgs` |
| `checkRxn(...)` | Removed, no direct successor; to debug why a reaction cannot carry flux, use `gapfilling/findLeakMetabolite.m`, `gapfilling/canExchange.m` or `gapfilling/checkProduction.m` |
| `dispEM(...)`, `followFluxes(...)`, `followChanged(...)`, `printModel(...)`, `mapCompartments(...)`, `getExpressionStructure(...)`, `getMetsInComp(...)` | All removed (see [Removed functionality](#removed-functionality) for the replacements, where one exists) |
| Anything under `external/metacyc/` | Subsystem removed: MetaCyc-based reconstruction; no in-toolbox replacement |
| Anything under `pathway/` or `plotting/` | Subsystems removed: all visualisation and plotting functionality (16 functions, such as `drawMap`, `drawPathway`, `markPathwayWithFluxes` and `setOmicDataToRxns`); no in-toolbox replacement, use the COBRA Toolbox or Escher |
| Anything under `legacy/` | Subsystem removed; no in-toolbox replacement (see [Removed functionality](#removed-functionality)) |
| `getGenesFromKEGG`, `getMetsFromKEGG`, `getRxnsFromKEGG`, `constructMultiFasta`, `getWSLpath`, `getBlastFromExcel` | Removed with the local KEGG FTP dump workflow (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getToolboxVersion(...)` | Removed as a standalone function; now part of an internal helper of `exportForGit` |
| `parallelPoolRAVEN(...)` | Renamed `parallelWorkersRAVEN`, with a different signature and output (see [Renamed and merged functions](#renamed-merged-and-consolidated-functions)) |
| `getModelFromKEGG(keggPath, keepSpontaneous, keepUndefinedStoich, keepIncomplete, keepGeneral)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed and the function accepts four optional arguments |
| `getKEGGModelForOrganism(...)` with 13 to 15 positional arguments | `nSequences` and `seqIdentity` are removed. 14 or 15 arguments raise `parseRAVENargs:tooManyArgs`; a non-empty `nSequences` (13th) is read as `globalModel` and raises an error |
| `getPhylDist(keggPath, onlyInKingdom)` | Raises `parseRAVENargs:tooManyArgs`, because `keggPath` is removed |
| `writeYAMLmodel(model, fileName, preserveQuotes, sortIds)` with four arguments | Raises `parseRAVENargs:tooManyArgs`; RAVEN 3 has `(model, fileName, sortIds)` |
| `scoreModel(...)` with `'best'` as the seventh or eighth argument, or `hpaLevelScores` as the ninth | Raises `RAVEN:badInput` for `'best'`, which is not a valid value of `isozymeScoring` or `complexScoring`; a structure as the ninth argument raises an error, because that position now holds `multipleCellScoring` |

## Changes that alter results without an error

The same call with the same input model gives different output.

| Function | RAVEN 3 behaviour (default, unless noted) |
|---|---|
| `getModelFromHomology`, `strictness=3` | Best-hit tie-break uses bitscore; RAVEN 2.11.3 used E-value, and no option restores that criterion (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getModelFromHomology`, `minLen` | Default lowered from `200` to `100` (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getModelFromHomology`, merging of gene-reaction rules (GPR) | Gene substitution is based on exact tokens; RAVEN 2 used regex or `strrep` (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getKEGGModelForOrganism`, `cutOff` | Default lowered from `10^-50` to `10^-30` (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `getKEGGModelForOrganism`, `minScoreRatioG` | Default raised from `0.8` to `0.9` (see [Reconstruction: KEGG and homology pipelines](#kegg-reconstruction)) |
| `removeGenes`, `expandModel`, `addRxns` | RAVEN 3 parses `grRules` by exact gene-token matching; RAVEN 2 used substring or regex matching (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `findPotentialErrors` | RAVEN 3 parses the rule into a tree; the RAVEN 2.11.3 check inside `standardizeGrRules` searched for string patterns (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `changeGrRules(..., 'replace', false)` onto a gene-less reaction | Produces a valid grRule; RAVEN 2 produced an unparseable one (see [Parsing of gene-reaction rules](#gpr-parsing)) |
| `simplifyModel` (used by task-based gap-filling) | Keeps the boundary constraint of a task on a metabolite without reactions (see [Gap-filling and context-specific model extraction](#ftinit)) |
| `ftINITInternalAlg` | With `allowExcretion` true, RAVEN 3 constrains the metabolite balance to `S*v >= 0`; RAVEN 2 had the sense of the constraint inverted |
| `ravenCobraWrapper` | Gene-ID-to-MIRIAM matching handles gene IDs that contain regex metacharacters; RAVEN 2 mis-matched them (see [RAVEN⇄COBRA interoperability](#raven-cobra-interoperability)) |
| `mergeCompartments` | The merged metabolite is the copy already in compartment `s`, otherwise the copy whose ID sorts first (character code order), with every field of that copy |
| `simplifyModel` with `constrainReversible` on a model without a reversible reaction | This step changes nothing; RAVEN 2 raised an error, because `getAllowedBounds` took the empty reaction list for all reactions |
| `getModelFromKEGG(keggPath)` and `getModelFromKEGG(keggPath, keepSpontaneous)` | `keggPath` is read as `keepSpontaneous` and has no effect; the second argument is read as `keepUndefinedStoich`, so the wrong class of reactions is removed |
| `getPhylDist(keggPath)` | `keggPath` is read as `'onlyInKingdom'` and has no effect; the full distance matrix is returned |
| `writeYAMLmodel(model, fileName, true)` | The third argument is read as `sortIds`, so IDs are sorted; RAVEN 2.11.3 read it as `'preserveQuotes'` |
| `scoreModel` | Reactions with an `and` rule get the minimum over the genes by default (`complexScoring`); RAVEN 2.11.3 scored every reaction with the maximum over all genes |
| `scoreModel(..., celltype, noGeneScore, 'average')` | `'average'` as the seventh argument is read as `isozymeScoring`, so it no longer applies to `and` rules, which use `complexScoring` |
| `parseScores(file)` | The default predictor is `'deeploc'`; RAVEN 2.11.3 used `'wolf'`. WoLF PSORT output is parsed as DeepLoc output |
| `permuteModel`, `randomSampling`, `optimizeProb`, `getFluxZ`, `convertToIrrev`, `replaceMets`, `setExchangeBounds`, `fitParameters`, `guessComposition` | Each function had a bug in RAVEN 2; output differs only for models and inputs that triggered it |

`removeGenes`, `expandModel` and `findPotentialErrors` parse the rule into a tree, which handles isozymes and complexes. `addRxns` only splits the rule on space-bounded `and` and `or` tokens and builds no tree.

`simplifyModel` in RAVEN 2.11.3 dropped the boundary constraint of a task on a metabolite without reactions, so a task that RAVEN 2.11.3 reported as passing can fail in RAVEN 3.

`mergeCompartments` in RAVEN 2.11.3 kept the copy that came first in `model.mets`.

The `scoreModel` of RAVEN 3 takes `celltype`, `noGeneScore`, `isozymeScoring`, `complexScoring`, `multipleCellScoring`, `hpaLevelScores` and `dataPrecedence` (default `'gene'`) in this order. `multipleCellScoring` accepts `'max'` and `'average'`.

None of the changes in this table is an API change.

## Changes to error and warning identifiers

- `dispEM`, the universal error and warning function of RAVEN 2, always raised errors with an empty identifier (`MException('', ...)`), so no RAVEN 2 script could legitimately have caught on `err.identifier`. RAVEN 3 replaces `dispEM` with native `error()` and `warning()` calls. Calls that carry an identifier predominantly use `RAVEN:badInput` (220 calls) and `RAVEN:warning` (63 calls), plus other identifiers, for example `RAVEN:modelError`, `RAVEN:badGrRule`, `RAVEN:infeasibleModel`, `RAVEN:infeasible`, `RAVEN:sampling` and `RAVEN:grRuleTooComplex`. Not every call carries an identifier.
- `try/catch` blocks that match on message text keep working for messages whose text is unchanged from RAVEN 2. Scripts can match on `err.identifier` for the calls that carry one.

## Changes that raise warnings

- `getINITModel` and `runINIT` issue a one-time "legacy" notice that points at `ftINIT`; `warning('off','RAVEN:legacyMethod')` silences it. The notice is not a deprecation: the RAVEN documentation states that these functions "remain supported" indefinitely, to reproduce previously published Human-GEM-derived models. See [Gap-filling and context-specific model extraction](#ftinit).
- `makeSomething`, `consumeSomething`, `canProduce` and `canConsume` are in a new `deprecated/` folder as wrappers around `findLeakMetabolite` and `canExchange`. They issue a one-time `RAVEN:deprecated` warning that states they "will be removed in the next major release." The wrappers are scheduled for removal in the next major release, so calls should be migrated before then. See [Gap-filling and context-specific model extraction](#ftinit).
- `checkInstallation` is now `checkRaven`, moved from `installation/` to the repository root, with an unchanged signature (`[currVer, installType] = checkRaven(developMode, checkBinaries)`). Existing calls keep working: `checkInstallation` remains as a forwarding wrapper that passes every argument and output through, after issuing a `RAVEN:deprecated` warning that names `checkRaven`. The wrapper is scheduled for removal in the next major release, like the functions in `deprecated/`, so calls should be migrated before then.

## Installation changes

The KEGG HMM libraries and the external command-line binaries (BLAST+, DIAMOND, HMMER, cd-hit, MAFFT and WoLF PSORT) are no longer committed to the repository. RAVEN 3 fetches the KEGG data and the BLAST+, DIAMOND and HMMER binaries from the [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository the first time a function needs them, so internet access is required on first use as well as at clone or install time. What is fetched and where it is cached is described in [Download data and binaries](../installation/data-and-binaries.md). The air-gapped install and the full dependency comparison are in [Toolbox dependencies and installation](#toolbox-deps).
