# File formats, reconstruction and GPR parsing

Model file formats, draft reconstruction and the parsing of gene-reaction rules (`grRules`, abbreviated GPR) differ between RAVEN 2 and RAVEN 3. The sections describe the changes that affect scripts and the differences that appear in version-controlled model files.

(file-formats-and-model-io)=
## File formats and model I/O

(sbml-io)=
### SBML I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `exportModel` output format | SBML Level 3 Version 1, FBC package version 2 | Unchanged |
| `importModel` accepted input | Any SBML level and version; the notes-based gene association `GENE_ASSOCIATION` of Level 2 files is read, and `SHORT NAME` is read for gene names; FBC fields are optional | SBML Level 3 Version 1 with FBC package version 2; any other file raises the error `RAVEN:badInput` |
| MIRIAM prefixes read on import | `urn:miriam:`, `http://identifiers.org/` and `https://identifiers.org/` | `http://identifiers.org/` and `https://identifiers.org/` |

`importModel` of RAVEN 3 reads MIRIAM annotations (reaction EC codes, model and species annotations) with the `http://identifiers.org/` and `https://identifiers.org/` prefixes and ignores `urn:miriam:` annotations.

:::{admonition} Cross-references in older SBML files
:class: warning
An SBML file that uses `urn:miriam:` annotations is imported without an error, and its cross-references (for example `metMiriams`) are absent from the imported model. RAVEN 2 writes `https://identifiers.org/` prefixes (`exportModel`), so its own files are not affected. Files from other tools that use `urn:miriam:` can be converted to the `identifiers.org` form before import.
:::

A file in an older SBML level or version has to be converted before `importModel` accepts it. The error message suggests another tool or an older RAVEN version for the conversion.

(excel-io)=
### Excel I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Excel engine | Apache POI (Java), bundled with RAVEN | Dependency-free OOXML writer (`io/writeExcel.m`) |
| Full-model `.xlsx` import | `importExcelModel.m` (sheets `RXNS`, `METS`, `COMPS`, `GENES` and `MODEL`) builds a complete model | Removed |
| Tabular curation of an existing model | No equivalent | `curation/curateModelFromTables.m` curates or extends a loaded model from `.tsv` files (metabolites by name and compartment, reactions by stoichiometry, genes by name) |
| `exportToExcelFormat` with a path that has no file name or extension | Falls back to tab-delimited text export | Raises an error; the output is `.xlsx` |

A pipeline that depends on the RAVEN 2 Excel curation template can convert the template to the `.tsv` format that `curateModelFromTables` expects, or build the model with `importModel` or `readYAMLmodel` and use `curateModelFromTables` for incremental edits.

(yaml-io)=
### YAML I/O

`readYAMLmodel` and `writeYAMLmodel` are pure MATLAB in both versions, so model YAML I/O has no Python dependency in either. `io/parseYAML.m` is a generic pure-MATLAB YAML parser that `conditions/applyCondition.m` uses to read condition files.

`writeYAMLmodel` of RAVEN 3 takes name-value arguments and quotes strings by a fixed rule in place of the RAVEN 2 option `preserveQuotes`. The output differs from RAVEN 2 in the following points, which appear as diffs in version-controlled model files.

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Quoting | Every string is quoted with double quotes (default `preserveQuotes` is true) | A string is quoted with double quotes where YAML needs it (reserved words, numbers, leading indicators, `: `); other strings are bare |
| Indentation | List entries `    - !!omap` (four spaces) with keys indented by six spaces | List entries `  - !!omap` (two spaces) with keys indented by four spaces |
| Reaction EC codes | Top-level `eccodes` field | Under `annotation: ec-code`; the top-level key is not written |
| Metabolite SMILES | Top-level field | Under `annotation` as `smiles` |
| Reaction notes key | `rxnNotes` | `notes` |
| Gene-less model | `genes:` is omitted when `model.genes` is absent; an empty field gives a bare `- genes:` | The line `- genes: []` |
| Document start | `---` line, then `!!omap` | `!!omap` only |
| Field order, metabolites | `formula`, then `charge` | `charge`, then `formula` |
| Field order, reactions | `rxnFrom` directly after `gene_reaction_rule`; `references` before `subsystem` and `annotation` | `subsystem` and `annotation` first; `references` and `rxnFrom` follow `annotation` among the RAVEN-specific extras |
| Field order, genes | `protein` before `annotation` | `protein` after `annotation` |
| `objective_coefficient` on import | Sets the coefficient to 1 for any value | The value is read |

`readYAMLmodel` of RAVEN 3 accepts both the top-level `eccodes`, `smiles` and `rxnNotes` keys and the `annotation` and `notes` forms.

(raven-cobra-interoperability)=
### RAVEN⇄COBRA interoperability

`conversion/ravenCobraWrapper.m` keeps its signature (`newModel = ravenCobraWrapper(model)`). RAVEN 3 fixes two bugs that change the output: a stale variable that could reuse the wrong MIRIAM data during gene-annotation conversion, and a mismatch of gene IDs that contain regular-expression metacharacters (for example `ENSG00000141510.16`) when the `rules` field is built from `grRules`.

---

(kegg-reconstruction)=
## Reconstruction: KEGG and homology pipelines

### KEGG-based reconstruction (`getModelFromKEGG`, `getKEGGModelForOrganism`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Reaction and gene database source | Local KEGG FTP dump (licence required), read when the cached files `keggGenes.mat`, `keggMets.mat` and `keggRxns.mat` are absent | Prebuilt artefacts fetched on demand from releases of `toolbox-assets` |
| Functions that build the database | `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` | `buildGlobalKEGGModel`, `buildGlobalGPR` and `readKEGGTable` |
| `getModelFromKEGG` `keggPath` argument | Optional (default `external/kegg`) | Removed |
| Ortholog HMM library | One `.hmm` file per KEGG Orthology (KO) entry; one `hmmsearch` call per KO, through the Windows Subsystem for Linux (WSL) on Windows | One concatenated library per domain (`kegg118_eukaryotes.hmm` and `kegg118_prokaryotes.hmm`); one `hmmsearch` call against the whole proteome; no WSL |
| `dataDir` | Arbitrary local folder | For the homology method (a FASTA file is given), the folder name must end in `kegg118_eukaryotes` or `kegg118_prokaryotes`; the annotation method ignores `dataDir` |
| `nSequences`, `seqIdentity` (CD-HIT clustering controls) | Configurable | Removed; there is no local clustering step |
| `cutOff` default | `10^-50` | `10^-30` |
| `minScoreRatioG` default | `0.8` | `0.9` |
| Calling convention | Positional | Positional or name-value (`parseRAVENargs`); a call with more positional arguments than the function defines raises `parseRAVENargs:tooManyArgs` |

The first call of `getModelFromKEGG` downloads the data, builds the global KEGG model and saves it as `src/reconstruction/kegg/keggModel.mat` (the source header states that the first build needs a few hundred MB of disk; the size of the cached file was not checked). `getKEGGModelForOrganism` loads the global model, the KO model and the five flag vectors from the same file. External binaries and the KEGG data are fetched from pinned `toolbox-assets` tags and are not bundled; see [Toolbox dependencies and installation](#toolbox-deps).

The three functions take their optional arguments through `varargin`, in the order of RAVEN 2 minus the removed arguments. Positional calls written for RAVEN 2 (checked against v2.11.3) change as follows.

- `getModelFromKEGG(keggPath, keepSpontaneous, ...)` becomes `getModelFromKEGG(keepSpontaneous, ...)`. An unchanged RAVEN 2 call shifts every later argument: the argument at position 2 is read as the parameter that RAVEN 2 takes at position 3, and so on.
- `getKEGGModelForOrganism` has no `nSequences` and `seqIdentity`, so `globalModel` moves from the 15th to the 13th argument among all arguments. In the migration pages, a position counts all arguments of the call, including the required ones.
- `getPhylDist(keggPath, onlyInKingdom)` becomes `getPhylDist(onlyInKingdom)`.

### Homology-based reconstruction (`getModelFromHomology`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `strictness` parameter | `1`, `2` or `3` | Unchanged |
| Best-hit tie-break at `strictness=3` | E-value | Bitscore; no option restores the E-value criterion |
| `minLen` default | `200` | `100` |
| GPR gene substitution when merging homology hits | Regular-expression or `strrep` substitution, which corrupts IDs that are substrings of other IDs or contain regular-expression metacharacters | Exact-token substitution |
| Complex handling, gene-free reactions and notes | Reactions with incompletely mapped complexes are flagged with an `OLD_` prefix | Options `complexPolicy` (default `'flag'`, the RAVEN 2 behaviour), `keepGeneFree` and `preserveNotes` |
| Gene IDs of the new organism | No restriction | Must not contain whitespace, parentheses, `\|` or `&` |

`reconstruction/homology/runSuppOrth.m` and `reconstruction/homology/hitsFromSuppOrth.m` are reconstruction inputs without a RAVEN 2 counterpart. The homology method takes its hits from BLAST, DIAMOND or SuppOrth.

### Genome data

`curation/downloadGenomeData.m`, `curation/getGeneData.m` and `curation/processProteinFastaFile.m` turn an NCBI genome accession (`GCF_` or `GCA_`) into a model-ready proteome and a gene ID mapping table. RAVEN 2 has no counterpart.

The content of the KEGG artefacts (a gene-free reference model plus KO, reaction and organism tables) was not checked against the `toolbox-assets` release.

---

(gpr-parsing)=
## Parsing of gene-reaction rules

RAVEN 3 parses gene-reaction rules into a tree, and the five functions in the table use the parser (`removeGenes`, `expandModel`, `findPotentialErrors`, `diffModels` and `curateModelFromTables`). The parser is not applied to a loaded model: a rule keeps its original text unless one of these functions changes it.

| Function | RAVEN 2 parsing | RAVEN 3 parsing |
|---|---|---|
| `removeGenes` | Substring match on gene ID (`"10"` also matches `"100"`) | Exact gene-token match |
| `expandModel` | Split on `' or '` after removing parentheses; an `AND`-ed subunit in a nested rule can be dropped | Parse-tree-based isozyme expansion that preserves nested `AND` and `OR` |
| `findPotentialErrors` | Local function of `core/standardizeGrRules.m`; string-pattern check for `") and ("` and similar patterns (false positives on valid rules); returns indices | Function of its own; parse-tree-based detection of rules that are not in disjunctive normal form (DNF); `issues = findPotentialErrors(model)` returns a structure array with the fields `index`, `rxn`, `grRule` and `reason` |
| `diffModels` | Not present | Compares grRules; two rules are equal when their DNF forms are equal after sorting of genes and clauses (no absorption: `A or (A and B)` differs from `A`) |
| `curateModelFromTables` | Not present | Parses rules of the table input |

`addRxns` does not use the parser. It takes the new gene IDs of a grRule from `getGenesFromGrRules`, which splits on space-bounded `and`, `or`, `&` and `|`. RAVEN 2 split on the substrings "and" and "or" anywhere, so an ID such as `band1` was split at "and".

The parser functions are in `utils/`. `parseGrRule` builds a tree with `type` (`'gene'`, `'and'` or `'or'`) and `children`. `grRuleToDNF` converts the tree to DNF, an OR of AND-clauses. `isDnfGrRule` checks whether a rule is in that form, and `grRuleToString` renders a tree as a canonical string.

`parseGrRule` accepts `and` and `or` in any case and the symbols `&`, `&&`, `|` and `||`. Operators are recognised as whole words, so `G1&G2` is one gene ID. A malformed rule raises `RAVEN:badGrRule`.

`manipulation/standardizeGrRules.m` (called by `importModel`) builds no parse tree. It converts ` AND ` and ` OR ` to lowercase and splits the rule on the space-bounded strings ` and ` and ` or `. It calls `findPotentialErrors` and returns the indices of rules that cannot be parsed or are not in DNF (`indexes2check`). A direct call lists these rules in one warning; `importModel` passes `embedded` as `true`, which suppresses the warning. The function does not raise `RAVEN:badGrRule`.
