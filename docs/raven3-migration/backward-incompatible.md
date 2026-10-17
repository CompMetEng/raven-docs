(backward-incompatible-changes)=
# Backward-incompatible changes

This is the consolidated list of everything a RAVEN 2 script could plausibly
break on, or silently produce different output from, when run against RAVEN 3.
Items are grouped by how they manifest.

## Will error / undefined function

| RAVEN 2 usage | What happens in RAVEN 3 |
|---|---|
| `importExcelModel(...)` | Removed. Use `curation/curateModelFromTables.m` (different input format: `.tsv`, not `.xlsx`; see [§6](../raven3-migration/formats-and-reconstruction.md#excel-io)) or convert your template to YAML/SBML and use `importModel`. |
| `importModel(...)` on SBML Level < 3, Level 3 without FBC v2, or any non-FBC SBML | Errors. Only SBML **Level 3 Version 1, FBC package version 2** is accepted (see [§6](../raven3-migration/formats-and-reconstruction.md#sbml-io)). |
| `exportToExcelFormat(model, fileName)` where `fileName` is a bare path (no `.xlsx`) | No longer falls back to tab-delimited text export; errors with "only export to xlsx format is supported". |
| `exportToTabDelimited(...)` | Removed outright (was a dead-code path anyway). |
| `getWoLFScores(...)` / `parseScores(..., 'wolf', ...)` | WoLF PSORT support is fully removed. `parseScores` now errors on `'predictor','wolf'` with a message pointing to `'deeploc'`, `'mulocdeep'`, `'compartments'`, or `'uniprot'`. **No in-toolbox migration path for existing WoLF PSORT output files.** |
| `qMOMA(...)`, `solveQP(...)` | Removed (RAVEN's last `quadprog`/Optimization Toolbox dependency). `findGeneDeletions`'s `analysisType`/`refModel`/`oeFactor` arguments (MOMA-based over-expression analysis) were removed with them; only FBA-based single/double gene deletion (`sgd`/`dgd`) remains. |
| `checkRxn(...)` | Removed, no direct successor. For debugging why a reaction can't carry flux, use `gapfilling/findLeakMetabolite.m` / `gapfilling/canExchange.m`, or `gapfilling/checkProduction.m`. |
| `dispEM(...)`, `followFluxes(...)`, `followChanged(...)`, `printModel(...)`, `mapCompartments(...)`, `getExpressionStructure(...)`, `getMetsInComp(...)`, `parallelPoolRAVEN(...)` | All removed (see [§4](../raven3-migration/structure-and-renames.md#removed-functionality) for what replaces each, where anything does). |
| Anything under `external/metacyc/`, `pathway/`, `plotting/`, `legacy/` | Entire subsystems removed: MetaCyc-based reconstruction and all visualization/plotting functionality (`drawMap`, `drawPathway`, `markPathwayWithFluxes`, `setOmicDataToRxns`, etc.). No in-toolbox replacement; use COBRA Toolbox or Escher for visualization. |
| `getGenesFromKEGG`, `getMetsFromKEGG`, `getRxnsFromKEGG`, `constructMultiFasta`, `getWSLpath`, `getBlastFromExcel` | Removed along with the old local-KEGG-FTP-dump workflow (see [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction)). |
| `getToolboxVersion(...)` | Removed as a standalone function; folded into an internal helper of `exportForGit`. |

## Will silently produce different results

Same call, same input model, different output. Grouped by function; see the
linked section for the full explanation of each.

| Function | New behavior (default, unless noted) |
|---|---|
| `getModelFromHomology`, `strictness=3` | Best-hit tie-break now uses **bitscore** instead of E-value (`"scoreBy","evalue"` restores the old criterion); [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction) |
| `getModelFromHomology`, `minLen` | Default lowered from `200` to `100`; [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction) |
| `getModelFromHomology`, GPR merging | Gene substitution is exact-token-based instead of regex/`strrep`-based; [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction) |
| `getKEGGModelForOrganism`, `cutOff` | Default lowered from `10^-50` to `10^-30`; [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction) |
| `getKEGGModelForOrganism`, `minScoreRatioG` | Default raised from `0.8` to `0.9`; [§7](../raven3-migration/formats-and-reconstruction.md#kegg-reconstruction) |
| `removeGenes`, `expandModel`, `findPotentialErrors`, `addRxns` | grRules are now parsed correctly (exact gene-token matching, structure-aware isozyme/complex handling) instead of via substring/regex matching; [§8](../raven3-migration/formats-and-reconstruction.md#gpr-parsing) |
| `changeGrRules(..., 'replace', false)` onto a gene-less reaction | Produces a valid grRule instead of an unparseable one; [§8](../raven3-migration/formats-and-reconstruction.md#gpr-parsing) |
| `simplifyModel` (used by task-based gap-filling) | No longer drops a task's boundary constraint on a metabolite with no reactions: a task that used to silently pass may now correctly fail; [§9](../raven3-migration/new-and-environment.md#ftinit) |
| `ftINITInternalAlg` | `allowExcretion` constraint sign corrected |
| `ravenCobraWrapper` | Gene-ID-to-MIRIAM matching no longer breaks on gene IDs containing regex metacharacters; [§6](../raven3-migration/formats-and-reconstruction.md#raven-cobra-interoperability) |
| `permuteModel`, `randomSampling`, `optimizeProb`, `getFluxZ`, `mergeCompartments`, `convertToIrrev`, `replaceMets`, `setExchangeBounds`, `fitParameters`, `guessComposition` | Each had a pre-existing bug fixed; output differs only for models/inputs that triggered it |

None of these are API changes; the same call with the same arguments now
returns a different, corrected result.

## Will warn, but keep working

- **Error/warning identifiers changed.** `dispEM` (RAVEN 2's universal
  error/warning function) always raised errors with an **empty** identifier
  (`MException('', ...)`), so no RAVEN 2 script could have legitimately caught
  on `err.identifier`. RAVEN 3 replaces `dispEM` with native `error()`/
  `warning()` calls, most (not all) carrying real identifiers,
  predominantly `RAVEN:badInput`, plus a handful of specific ones
  (`RAVEN:modelError`, `RAVEN:badGrRule`, `RAVEN:sampling`, `RAVEN:infeasible`,
  `RAVEN:grRuleTooComplex`). Message text is largely unchanged (many messages
  are byte-identical to RAVEN 2's), so `try/catch` blocks that pattern-match on
  message text keep working; scripts can newly (optionally) match on
  `err.identifier` instead.
- **`getINITModel`/`runINIT` now emit a one-time "legacy" notice** pointing at
  `ftINIT`, silenceable with `warning('off','RAVEN:legacyMethod')`. This is
  explicitly *not* a deprecation; RAVEN's own documentation states these
  functions "remain supported" indefinitely, to reproduce previously published
  Human-GEM-derived models. See [§9](../raven3-migration/new-and-environment.md#ftinit).
- **`makeSomething`, `consumeSomething`, `canProduce`, `canConsume`** now live in
  a new `deprecated/` folder as thin wrappers around `findLeakMetabolite`/
  `canExchange`, and emit a one-time `RAVEN:deprecated` warning stating they
  "will be removed in the next major release." Unlike the legacy-notice
  functions above, these are on an actual removal track; migrate call sites
  before the next major release. See [§9](../raven3-migration/new-and-environment.md#ftinit).
- **`checkInstallation` is now `checkRaven`**, moved from `installation/` to the
  repository root, with an unchanged signature
  (`[currVer, installType] = checkRaven(developMode, checkBinaries)`). Existing
  calls do **not** break: `checkInstallation` survives as a forwarding wrapper
  that passes every argument and output straight through, after emitting a
  `RAVEN:deprecated` warning naming `checkRaven`. It is on the same removal
  track as the `deprecated/` functions above, so switch at the next opportunity.

## Environment / installation changes

KEGG HMM libraries and external command-line binaries (BLAST+, DIAMOND, HMMER,
cd-hit, MAFFT, WoLF PSORT) are no longer committed to the repository. RAVEN 3
fetches them on demand from the `raven-data` GitHub release the first time a
function needs one, which means **internet access is required on first use**,
not just at clone/install time. See [§11](../raven3-migration/new-and-environment.md#toolbox-deps) for what's needed for
an air-gapped install, and the full dependency comparison.
