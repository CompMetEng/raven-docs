# File formats, reconstruction and GPR parsing

Three areas differ between RAVEN 2 and RAVEN 3: the model file formats, the draft reconstruction from KEGG and from homology, and the parsing of gene-reaction rules (`grRules`, abbreviated GPR). Each section gives the changes that affect a script and the differences that show up as diffs in version-controlled model files.

(file-formats-and-model-io)=
## File formats and model I/O

(sbml-io)=
### SBML I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `exportModel` output format | SBML Level 3 Version 1, FBC package version 2 | Unchanged |
| `importModel` accepted input | Any SBML level and version. The notes-based gene association `GENE_ASSOCIATION` of Level 2 files is read, and `SHORT NAME` is read for gene names. FBC fields are optional | SBML Level 3 Version 1 with FBC package version 2. Any other file raises the error `RAVEN:badInput` |
| MIRIAM prefixes read on import | `urn:miriam:`, `http://identifiers.org/` and `https://identifiers.org/` | `http://identifiers.org/` and `https://identifiers.org/` |

`importModel` of RAVEN 3 reads MIRIAM annotations (reaction EC codes, model and species annotations) with the prefixes `http://identifiers.org/` and `https://identifiers.org/`, and ignores `urn:miriam:` annotations.

:::{admonition} Cross-references in older SBML files
:class: warning
An SBML file with `urn:miriam:` annotations is imported without an error, and its cross-references (for example `metMiriams`) are absent from the imported model. The `exportModel` function of RAVEN 2 writes `https://identifiers.org/` prefixes, so files written by RAVEN 2 are not affected. Files from other tools that use `urn:miriam:` can be converted to the `identifiers.org` form before the import.
:::

A file in an older SBML level or version has to be converted before `importModel` accepts it. The error message suggests another tool or an older RAVEN version for the conversion.

(excel-io)=
### Excel I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Excel engine | Apache POI (Java), bundled with RAVEN | Dependency-free OOXML writer (`io/writeExcel.m`) |
| Import of a full model from `.xlsx` | `importExcelModel.m` builds a complete model from the sheets `RXNS`, `METS`, `COMPS`, `GENES` and `MODEL` | Removed |
| Tabular curation of an existing model | No equivalent | `curation/curateModelFromTables.m` curates or extends a loaded model from `.tsv` files: metabolites by name and compartment, reactions by stoichiometry, genes by name |
| `exportToExcelFormat` with a path that has no file name or extension | Falls back to tab-delimited text | Raises an error. The output is `.xlsx` |

A pipeline that depends on the RAVEN 2 Excel curation template has two options. The template can be converted to the `.tsv` format that `curateModelFromTables` expects. Alternatively the model is built with `importModel` or `readYAMLmodel`, and `curateModelFromTables` makes the later edits.

(yaml-io)=
### YAML I/O

`readYAMLmodel` and `writeYAMLmodel` are written in MATLAB in both versions, so the YAML I/O of a model has no Python dependency in either. The function `io/parseYAML.m` is a general YAML parser in MATLAB, which `conditions/applyCondition.m` uses to read condition files.

`writeYAMLmodel` of RAVEN 3 takes name-value arguments and quotes strings by a fixed rule, in place of the RAVEN 2 option `preserveQuotes`. The output differs from the output of RAVEN 2 in the points below, and each of them appears as a diff in a version-controlled model file.

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Quoting | Every string has double quotes (default `preserveQuotes` true) | A string has double quotes where YAML needs them (reserved words, numbers, leading indicators, `: `). Other strings are bare |
| Indentation | List entries `    - !!omap` (four spaces), keys indented by six spaces | List entries `  - !!omap` (two spaces), keys indented by four spaces |
| Reaction EC codes | Top-level field `eccodes` | Under `annotation: ec-code`. The top-level key is not written |
| Metabolite SMILES | Top-level field | Under `annotation` as `smiles` |
| Reaction notes key | `rxnNotes` | `notes` |
| Gene-less model | `genes:` is omitted when `model.genes` is absent, and an empty field gives a bare `- genes:` | The line `- genes: []` |
| Document start | A `---` line, then `!!omap` | `!!omap` alone |
| Field order, metabolites | `formula`, then `charge` | `charge`, then `formula` |
| Field order, reactions | `rxnFrom` directly after `gene_reaction_rule`, and `references` before `subsystem` and `annotation` | `subsystem` and `annotation` first, then `references` and `rxnFrom` among the RAVEN-specific extras |
| Field order, genes | `protein` before `annotation` | `protein` after `annotation` |
| `objective_coefficient` on import | Sets the coefficient to 1 for any value | Reads the value |

`readYAMLmodel` of RAVEN 3 accepts the top-level keys `eccodes`, `smiles` and `rxnNotes` as well as the forms `annotation` and `notes`.

(raven-cobra-interoperability)=
### RAVEN⇄COBRA interoperability

The function `conversion/ravenCobraWrapper.m` keeps its signature, `newModel = ravenCobraWrapper(model)`. RAVEN 3 fixes two bugs that change its output. One is a stale variable that could reuse the wrong MIRIAM data in the conversion of gene annotations. The other is a mismatch of gene IDs that contain regular-expression metacharacters, for example `ENSG00000141510.16`, when the `rules` field is built from `grRules`.

---

(kegg-reconstruction)=
## Reconstruction: KEGG and homology pipelines

### KEGG-based reconstruction (`getModelFromKEGG`, `getKEGGModelForOrganism`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Source of the reaction and gene database | Local KEGG FTP dump (licence required), read when the cached files `keggGenes.mat`, `keggMets.mat` and `keggRxns.mat` are absent | Prebuilt artefacts fetched on demand from releases of `toolbox-assets` |
| Functions that build the database | `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` | `buildGlobalKEGGModel`, `buildGlobalGPR` and `readKEGGTable` |
| Argument `keggPath` of `getModelFromKEGG` | Optional, default `external/kegg` | Removed |
| Ortholog HMM library | One `.hmm` file per KEGG Orthology (KO) entry and one `hmmsearch` call per KO, through the Windows Subsystem for Linux (WSL) on Windows | One concatenated library per domain (`kegg118_eukaryotes.hmm` and `kegg118_prokaryotes.hmm`), one `hmmsearch` call against the whole proteome, and no WSL |
| `dataDir` | Any local folder | For the homology method, which takes a FASTA file, the folder name must end in `kegg118_eukaryotes` or `kegg118_prokaryotes`. The annotation method ignores `dataDir` |
| `nSequences`, `seqIdentity` (CD-HIT clustering controls) | Configurable | Removed; there is no local clustering step |
| Default of `cutOff` | `10^-50` | `10^-30` |
| Default of `minScoreRatioG` | `0.8` | `0.9` |
| Calling convention | Positional | Positional or name-value (`parseRAVENargs`). A call with more positional arguments than the function defines raises `parseRAVENargs:tooManyArgs` |

The first call of `getModelFromKEGG` downloads the data, builds the global KEGG model and saves it as `src/reconstruction/kegg/keggModel.mat`. The source header states that the first build needs a few hundred MB of disk, and the size of the cached file was not checked. The function `getKEGGModelForOrganism` loads the global model, the KO model and the five flag vectors from the same file. The external binaries and the KEGG data come from pinned `toolbox-assets` tags and are not bundled (see [Toolbox dependencies and installation](#toolbox-deps)).

The three functions take their optional arguments through `varargin`, in the RAVEN 2 order without the removed arguments. A position counts all arguments of the call, required ones included. Positional calls written for RAVEN 2 (checked against 2.11.3) change as follows.

- `getModelFromKEGG(keggPath, keepSpontaneous, ...)` becomes `getModelFromKEGG(keepSpontaneous, ...)`. An unchanged RAVEN 2 call shifts every later argument: the argument at position 2 is read as the parameter that RAVEN 2 has at position 3, and so on.
- `getKEGGModelForOrganism` has no `nSequences` and no `seqIdentity`, so `globalModel` moves from the 15th to the 13th argument.
- `getPhylDist(keggPath, onlyInKingdom)` becomes `getPhylDist(onlyInKingdom)`.

### Homology-based reconstruction (`getModelFromHomology`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Parameter `strictness` | `1`, `2` or `3` | Unchanged |
| Best-hit criterion at `strictness=3` | E-value | Bitscore. No option restores the E-value criterion |
| Default of `minLen` | `200` | `100` |
| Gene substitution in GPRs when homology hits are merged | Substitution by regular expression or `strrep`, which corrupts IDs that are substrings of other IDs or contain regular-expression metacharacters | Substitution by exact token |
| Complexes, gene-free reactions and notes | A reaction with an incompletely mapped complex is flagged with the prefix `OLD_` | The options `complexPolicy` (default `'flag'`, the RAVEN 2 behaviour), `keepGeneFree` and `preserveNotes` |
| Gene IDs of the new organism | No restriction | Must not contain whitespace, parentheses, `\|` or `&` |

The functions `reconstruction/homology/runSuppOrth.m` and `reconstruction/homology/hitsFromSuppOrth.m` supply reconstruction input and have no RAVEN 2 counterpart. The homology method takes its hits from BLAST, DIAMOND or SuppOrth.

### Genome data

The functions `curation/downloadGenomeData.m`, `curation/getGeneData.m` and `curation/processProteinFastaFile.m` turn an NCBI genome accession (`GCF_` or `GCA_`) into a proteome that is ready for modelling and a gene ID mapping table. RAVEN 2 has no counterpart.

The content of the KEGG artefacts, a gene-free reference model plus KO, reaction and organism tables, was not checked against the `toolbox-assets` release.

---

(gpr-parsing)=
## Parsing of gene-reaction rules

RAVEN 3 parses gene-reaction rules into a tree. Five functions use the parser: `removeGenes`, `expandModel`, `findPotentialErrors`, `diffModels` and `curateModelFromTables`. The parser is not applied to a loaded model, so a rule keeps its text unless one of these functions changes it.

| Function | RAVEN 2 parsing | RAVEN 3 parsing |
|---|---|---|
| `removeGenes` | Substring match on the gene ID (`"10"` also matches `"100"`) | Match on the exact gene token |
| `expandModel` | Split on `' or '` after the parentheses are removed. An `AND`-ed subunit in a nested rule can be dropped | Isozyme expansion from the parse tree, which keeps nested `AND` and `OR` |
| `findPotentialErrors` | Local function of `core/standardizeGrRules.m`. A string-pattern check for `") and ("` and similar patterns, with false positives on valid rules. Returns indices | A function of its own. Parse-tree detection of rules that are not in disjunctive normal form (DNF). `issues = findPotentialErrors(model)` returns a structure array with the fields `index`, `rxn`, `grRule` and `reason` |
| `diffModels` | Not present | Compares grRules. Two rules are equal when their DNF forms are equal after sorting of genes and clauses, without absorption: `A or (A and B)` differs from `A` |
| `curateModelFromTables` | Not present | Parses the rules of the table input |

`addRxns` does not use the parser. It takes the new gene IDs of a grRule from `getGenesFromGrRules`, which splits at the space-bounded tokens `and`, `or`, `&` and `|`. RAVEN 2 split at the substrings "and" and "or" anywhere, so an ID such as `band1` was cut at "and".

The parser functions are in `utils/`. `parseGrRule` builds a tree with `type` (`'gene'`, `'and'` or `'or'`) and `children`. `grRuleToDNF` converts the tree to DNF, an OR of AND clauses. `isDnfGrRule` checks whether a rule has that form, and `grRuleToString` renders a tree as a canonical string.

`parseGrRule` accepts `and` and `or` in any case and the symbols `&`, `&&`, `|` and `||`. It recognises operators as whole words, so `G1&G2` is one gene ID. A malformed rule raises `RAVEN:badGrRule`.

The function `manipulation/standardizeGrRules.m`, which `importModel` calls, builds no parse tree. It converts ` AND ` and ` OR ` to lowercase and splits the rule at the space-bounded strings ` and ` and ` or `. It calls `findPotentialErrors` and returns the indices of rules that cannot be parsed or are not in DNF (`indexes2check`). A direct call lists these rules in one warning, and `importModel` passes `embedded` as `true`, which suppresses the warning. The function does not raise `RAVEN:badGrRule`.
