# File formats, reconstruction and GPR parsing

Model file formats, draft reconstruction and the parsing of gene-reaction rules (`grRules`, abbreviated GPR) differ between RAVEN 2 and RAVEN 3.

(file-formats-and-model-io)=
## File formats and model I/O

(sbml-io)=
### SBML I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `exportModel` output format | SBML Level 3 Version 1, FBC package version 2 | Unchanged |
| `importModel` accepted input | Any SBML level and version; L2-style notes-based gene associations (`GENE_ASSOCIATION` and `PROTEIN_ASSOCIATION`) also read; FBC fields optional | Only SBML Level 3 Version 1, FBC package version 2; anything else raises an error |
| MIRIAM prefixes read on import | `urn:miriam:`, `http://identifiers.org/`, `https://identifiers.org/` | Unchanged |

Older SBML files have to be converted before `importModel` accepts them, for example by re-exporting them from cobrapy or the COBRA Toolbox.

(excel-io)=
### Excel I/O

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Excel engine | Apache POI (Java), bundled | Dependency-free OOXML writer (`io/writeExcel.m`) |
| Full-model `.xlsx` import | `importExcelModel.m` (`RXNS`, `METS`, `COMPS`, `GENES` and `MODEL` sheets → complete model) | Removed, no equivalent importer |
| Tabular curation of an existing model | No equivalent | `curation/curateModelFromTables.m` curates or extends a loaded model from separate `.tsv` files (metabolites by name and compartment, reactions by stoichiometry, genes by name); it is not an importer |
| `exportToExcelFormat` on a bare path (no `.xlsx`) | Fell back to tab-delimited text export | Raises an error, `.xlsx` only |

A pipeline that depends on the RAVEN 2 Excel curation template can convert the template to the `.tsv` format that `curateModelFromTables` expects, or build the model with `importModel` or YAML and use `curateModelFromTables` for incremental edits.

### YAML I/O

`readYAMLmodel` and `writeYAMLmodel` are pure MATLAB in RAVEN 3 and were in RAVEN 2, so model YAML I/O has no Python dependency in either version. `io/parseYAML.m` is a new pure-MATLAB generic YAML parser, used only by `conditions/applyCondition.m` to read condition files. RAVEN 3 writes model YAML with the following differences, which appear as diffs in version-controlled model files:

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Quote style | Single quotes | Double quotes |
| Reaction EC codes | Top-level `eccodes` field only | Also written under `annotation: ec-code` |
| Gene-less model | `genes:` section omitted | `genes: []` written explicitly |
| Empty `gene_reaction_rule` | Written as an empty string | Omitted |
| `objective_coefficient` on import | Ignored | Honoured |

(raven-cobra-interoperability)=
### RAVEN⇄COBRA interoperability

`conversion/ravenCobraWrapper.m` keeps its signature (`newModel = ravenCobraWrapper(model)`). RAVEN 3 fixes two bugs that change the output: a stale variable that could reuse the wrong MIRIAM data during gene-annotation conversion, and a mis-match of gene IDs containing regex metacharacters (for example `ENSG00000141510.16`) during annotation conversion.

---

(kegg-reconstruction)=
## Reconstruction: KEGG and homology pipelines

### KEGG-based reconstruction (`getModelFromKEGG`, `getKEGGModelForOrganism`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Reaction and gene database source | Local KEGG FTP dump (licence required) | Prebuilt artefacts fetched on demand from releases of `toolbox-assets` |
| Functions that build the database | `getGenesFromKEGG`, `getMetsFromKEGG` and `getRxnsFromKEGG` parsed the dump into a cached `keggModel.mat` | `buildGlobalKEGGModel`, `buildGlobalGPR` and `readKEGGTable` assemble the artefacts |
| `getModelFromKEGG`'s `keggPath` argument | Required | Removed, not needed |
| Ortholog HMM library | One `.hmm` file per KEGG Orthology (KO) entry; one `hmmsearch` call per KO, via WSL on Windows | One concatenated per-domain library (`kegg118_eukaryotes.hmm` and `kegg118_prokaryotes.hmm`); one `hmmsearch` call against the whole proteome, no WSL |
| `dataDir` | Arbitrary local folder | Must be `kegg118_eukaryotes` or `kegg118_prokaryotes` |
| `nSequences`, `seqIdentity` (CD-HIT clustering controls) | Configurable | Removed, no local clustering step |
| `cutOff` default | `10^-50` | `10^-30` |
| `minScoreRatioG` default | `0.8` | `0.9` |
| Calling convention | Positional | Positional or named (`parseRAVENargs`); positions shift in `getModelFromKEGG`, `getKEGGModelForOrganism` and `getPhylDist` (see below the table) |

The RAVEN 3 artefacts are a gene-free reference model plus KO, reaction and organism tables. In RAVEN 2 the per-KO `.hmm` files were either self-built with CD-HIT, MAFFT and `hmmbuild`, or downloaded.

In RAVEN 3 the three functions take their optional arguments through `varargin`, in the order of RAVEN 2 minus the removed arguments. Positional calls written for RAVEN 2 (checked against v2.11.3) change as follows:

- `getModelFromKEGG(keggPath, keepSpontaneous, ...)` became `getModelFromKEGG(keepSpontaneous, ...)`. Each old positional argument is read as the parameter one position earlier.
- `getKEGGModelForOrganism` no longer has `nSequences` and `seqIdentity`, so `globalModel` moves from the 15th to the 13th argument.
- `getPhylDist(keggPath, onlyInKingdom)` became `getPhylDist(onlyInKingdom)`, because `keggPath` was removed.

### Homology-based reconstruction (`getModelFromHomology`)

| Aspect | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `strictness` parameter | `1`, `2` or `3` | Unchanged |
| Best-hit tie-break at `strictness=3` | E-value | Bitscore; no option restores the E-value criterion of RAVEN 2 |
| `minLen` default | `200` | `100` |
| GPR gene substitution when merging homology hits | Regex or `strrep` substitution (could corrupt IDs that were substrings of one another, or contained regex metacharacters) | Exact-token-based substitution |

### Binaries and genome data

External binaries (BLAST+, DIAMOND, HMMER) and the KEGG data artefacts are fetched on demand from pinned `toolbox-assets` release tags and are not bundled with the repository; see [Toolbox dependencies and installation](#toolbox-deps).

`curation/downloadGenomeData.m`, `curation/getGeneData.m` and `curation/processProteinFastaFile.m` are new in RAVEN 3 and turn an NCBI genome accession (`GCF_` or `GCA_`) into a model-ready proteome and a gene ID mapping table.

---

(gpr-parsing)=
## Parsing of gene-reaction rules

RAVEN 3 adds a gene-reaction rule tokeniser and parser. `utils/parseGrRule.m` builds a parse tree (`type`: `'gene'|'and'|'or'`, with `children`). `utils/grRuleToDNF.m` converts the tree to disjunctive normal form (DNF), RAVEN's canonical "OR of AND-clauses" shape for enzyme-complex and isozyme structure. `utils/isDnfGrRule.m` checks whether a rule is already in that form. `utils/grRuleToString.m` renders a tree back to a canonical string. Five functions use the parser and converters internally: `removeGenes`, `expandModel`, `findPotentialErrors`, `diffModels` and `curateModelFromTables`. The parser and converters are not applied automatically to a loaded model: a rule keeps its original text unless one of these functions is called on it.

| Function | RAVEN 2 parsing | RAVEN 3 parsing |
|---|---|---|
| `removeGenes` | Substring match on gene ID (`"10"` also matched `"100"`) | Exact gene-token match |
| `expandModel` | Split on `' or '` (could drop an `AND`-ed subunit inside a nested rule) | Parse-tree-based isozyme expansion, preserves nested `AND` and `OR` |
| `findPotentialErrors` | Local function of `core/standardizeGrRules.m` (not callable); string-pattern check for `") and ("` and similar patterns (false positives on valid rules) | Function of its own; parse-tree-based non-DNF detection |
| `addRxns` (new gene IDs from a grRule) | Split on the substrings "and" and "or" anywhere (could split an ID such as `"band1"` at its "and") | Split only on space-bounded `' and '` and `' or '` tokens |
| `comparison/diffModels.m` | (not present) | grRules compared by logical DNF equality |

`parseGrRule` accepts `and` and `or` in any case and the symbols `&`, `&&`, `|` and `||`. Operators are recognised as whole words, so `G1&G2` is one gene ID. A malformed rule raises `RAVEN:badGrRule`.

`manipulation/standardizeGrRules.m` (which runs on import) does not build a parse tree. It converts ` AND ` and ` OR ` to lowercase and splits the rule on the space-bounded strings ` and ` and ` or `, so those are the two spellings of the operators it recognises. It calls `findPotentialErrors`, which parses the rules, and returns the indices of rules that cannot be parsed or are not in DNF (`indexes2check`). A direct call lists these rules in one warning; `importModel` calls the function with `embedded` set to `true`, which suppresses the warning. The function does not raise `RAVEN:badGrRule`.
