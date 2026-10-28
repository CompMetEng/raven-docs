# File formats, reconstruction, and GPR parsing

(file-formats-and-model-io)=
## 1. File formats and model I/O

(sbml-io)=
### SBML I/O

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `exportModel` output format | SBML Level 3 Version 1, FBC v2 | unchanged |
| `importModel` accepted input | any SBML level/version; L2-style notes-based gene associations (`GENE_ASSOCIATION`/`PROTEIN_ASSOCIATION`) also read; FBC fields optional | only SBML **Level 3 Version 1, FBC v2**; anything else errors |
| MIRIAM prefixes read on import | `urn:miriam:`, `http://identifiers.org/`, `https://identifiers.org/` | unchanged |

Older SBML files must be converted first (e.g. re-exported from COBRApy/COBRA
Toolbox) before `importModel` will accept them.

(excel-io)=
### Excel I/O

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Excel engine | Apache POI (Java), bundled | dependency-free OOXML writer (`io/writeExcel.m`) |
| Full-model `.xlsx` import | `importExcelModel.m` (`RXNS`/`METS`/`COMPS`/`GENES`/`MODEL` sheets → complete model) | removed, no equivalent importer |
| Nearest replacement for curation | no equivalent | `curation/curateModelFromTables.m`: curates/extends an *existing* model from separate `.tsv` files (mets by name+compartment, reactions by stoichiometry, genes by name), not a from-scratch importer |
| `exportToExcelFormat` on a bare path (no `.xlsx`) | fell back to tab-delimited text export | errors, `.xlsx` only |

If your pipeline depends on the old Excel curation template, either convert it
to the `.tsv` shape `curateModelFromTables` expects, or build the model via
`importModel`/YAML and use `curateModelFromTables` for incremental edits.

### YAML I/O

`readYAMLmodel`/`writeYAMLmodel` are pure-MATLAB in both branches; model YAML
I/O has no Python dependency in RAVEN 2 or RAVEN 3. (`io/parseYAML.m` is an
unrelated, new, pure-MATLAB generic YAML parser used only by
`conditions/applyCondition.m` to read condition files; it doesn't affect
model I/O.) Output format changes, visible as diffs in version-controlled
model files:

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Quote style | single quotes | double quotes |
| Reaction EC codes | top-level `eccodes` field only | also written under `annotation: ec-code` |
| Gene-less model | `genes:` section omitted | `genes: []` written explicitly |
| Empty `gene_reaction_rule` | written as an empty string | omitted |
| `objective_coefficient` on import | ignored | honored |

(raven-cobra-interoperability)=
### RAVEN⇄COBRA interoperability

`conversion/ravenCobraWrapper.m` keeps its signature
(`newModel = ravenCobraWrapper(model)`) unchanged. Two correctness fixes change
output for affected models: a stale-variable bug that could reuse the wrong
MIRIAM data during gene-annotation conversion, and gene IDs containing regex
metacharacters (e.g. `ENSG00000141510.16`) that could be mis-matched during
annotation conversion; both fixed.

---

(kegg-reconstruction)=
## 2. Reconstruction: KEGG and homology pipelines

### KEGG-based reconstruction (`getModelFromKEGG`, `getKEGGModelForOrganism`)

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| Reaction/gene database source | local KEGG FTP dump (license required), parsed by `getGenesFromKEGG`/`getMetsFromKEGG`/`getRxnsFromKEGG` into a cached `keggModel.mat` | prebuilt artifacts (a gene-free reference model plus KO/reaction/organism tables) fetched on demand from the `raven-data` GitHub release, assembled by `buildGlobalKEGGModel`/`buildGlobalGPR`/`readKEGGTable` |
| `getModelFromKEGG`'s `keggPath` argument | required | removed, not needed |
| Ortholog HMM library | one `.hmm` file per KO (self-built via CD-HIT + MAFFT + `hmmbuild`, or downloaded); queried with one `hmmsearch` call per KO, via WSL on Windows | one concatenated per-domain library (`kegg118_eukaryotes.hmm` / `kegg118_prokaryotes.hmm`); one `hmmsearch` call against the whole proteome, no WSL |
| `dataDir` | arbitrary local folder | must be `kegg118_eukaryotes` or `kegg118_prokaryotes` |
| `nSequences`, `seqIdentity` (CD-HIT clustering controls) | configurable | removed, no local clustering step |
| `cutOff` default | `10^-50` | `10^-30` |
| `minScoreRatioG` default | `0.8` | `0.9` |
| Calling convention | positional | positional-or-named (`parseRAVENargs`); old positional order preserved |

### Homology-based reconstruction (`getModelFromHomology`)

| | RAVEN 2 | RAVEN 3 |
|---|---|---|
| `strictness` parameter | `1`/`2`/`3` | unchanged |
| Best-hit tie-break at `strictness=3` | E-value | bitscore by default (`"scoreBy","evalue"` restores the old criterion) |
| `minLen` default | `200` | `100` |
| GPR gene substitution when merging homology hits | regex/`strrep` substitution (could corrupt IDs that were substrings of one another, or contained regex metacharacters) | exact-token-based substitution |

### Shared infrastructure

External binaries (BLAST+, DIAMOND, HMMER) and the KEGG data artifacts
themselves are fetched on demand rather than bundled with the repository; see
[§11](#toolbox-deps).

**New:** `curation/downloadGenomeData.m`, `curation/getGeneData.m`, and
`curation/processProteinFastaFile.m` give a new on-ramp from a bare NCBI genome
accession (`GCF_`/`GCA_`) straight to a model-ready proteome and gene ID
mapping table.

---

(gpr-parsing)=
## 3. Gene-reaction-rule (GPR) parsing

RAVEN 3 adds a proper grRule tokenizer/parser: `utils/parseGrRule.m` builds a
parse tree (`type`: `'gene'|'and'|'or'`, with `children`); `utils/grRuleToDNF.m`
converts it to disjunctive normal form (RAVEN's canonical "OR of AND-clauses"
shape for enzyme-complex/isozyme structure); `utils/isDnfGrRule.m` checks
whether a rule is already in that form; `utils/grRuleToString.m` renders a tree
back to a canonical string. These are used internally by four functions,
they are **not** applied automatically to every loaded model; a grRule keeps
its original text unless one of these functions is called on it.

| Function | RAVEN 2 parsing | RAVEN 3 parsing |
|---|---|---|
| `removeGenes` | substring match on gene ID (`"10"` also matched `"100"`) | exact gene-token match |
| `expandModel` | naive split on `' or '` (could drop an `AND`-ed subunit inside a nested rule) | parse-tree-based isozyme expansion, preserves nested `AND`/`OR` |
| `findPotentialErrors` | string-pattern check for `") and ("` etc. (false positives on valid rules) | parse-tree-based non-DNF detection |
| `addRxns` (new gene IDs from a grRule) | split on the substrings "and"/"or" anywhere (could shred an ID like `"band1"`) | split only on space-bounded `' and '`/`' or '` tokens |
| `comparison/diffModels.m` | (function didn't exist) | grRules compared as logical DNF equality, not string equality |

The accepted grRule *syntax* itself is unchanged: `' and '`/`' or '`
(case-insensitive) still work exactly as before, and
`manipulation/standardizeGrRules.m` (which runs on import) uses the same
string-splitting logic it always did.
