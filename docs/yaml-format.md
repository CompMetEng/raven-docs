# YAML file format

Three tools produce and read the YAML format:

- cobrapy ([`cobra.io.{load,save}_yaml_model`](https://github.com/opencobra/cobrapy))
- raven-toolbox (`raven_toolbox.io.yaml.{read,write}_yaml_model`, [API](api/index.md))
- RAVEN MATLAB (`readYAMLmodel.m` and `writeYAMLmodel.m` in [`src/io`](https://github.com/CompMetEng/RAVEN/tree/develop/src/io) of the RAVEN repository)

The same file can be round-tripped through any of the three. cobrapy defines the core shape. raven-toolbox and RAVEN MATLAB add namespaced extensions that leave the shape known to cobra intact: RAVEN curation fields, MIRIAM cross-references that the `annotation` of cobrapy already covers, and the GECKO `ec-*` sections.

---

## Overview

```yaml
!!omap
- metaData: !!omap
    - id: yeastGEM_develop
    - name: The Consensus Genome-Scale Metabolic Model of Yeast
    - version: 9.0.0
    - date: 2026-05-27
    - taxonomy: taxonomy/559292
- metabolites:
    - !!omap
      - id: s_0001
      - name: ATP
      - compartment: c
      - charge: -4
      - formula: C10H16N5O13P3
      - annotation: !!omap
          - kegg.compound: C00002
          - smiles: "[O-]P(=O)([O-])OP(=O)([O-])O..."
      - inchis: InChI=1S/C10H16N5O13P3/...
      - deltaG: -2768.1
- reactions:
    - !!omap
      - id: r_0001
      - name: hexokinase
      - metabolites: !!omap
          - s_0001: -1.0
          - s_0568: -1.0
          - s_0394: 1.0
          - s_0423: 1.0
      - lower_bound: 0.0
      - upper_bound: 1000.0
      - gene_reaction_rule: YGL253W or YCL040W or YFR053C
      - subsystem: Glycolysis / Gluconeogenesis
      - notes: "MetaNetX ID curated (PR #220)"
      - annotation: !!omap
          - kegg.reaction: R00299
          - sbo: SBO:0000176
      - eccodes: 2.7.1.1
      - deltaG: -17.39
      - confidence_score: 2.0
- genes:
    - !!omap
      - id: YGL253W
      - name: HXK2
      - annotation: !!omap
          - uniprot: P04807
- compartments: !!omap
    - c: cytoplasm
    - e: extracellular
```

Three structural rules apply to the field-by-field description:

1. The whole document is one ordered mapping (`!!omap`) at the root. Every nested mapping that preserves key order is also an `!!omap`: `metaData`, each metabolite, reaction and gene entry, `annotation`, `metabolites`, `compartments` and the ec sections.
2. Each metabolite, reaction and gene is one `- !!omap` element of a list. Inside the mapping, every field is written as `- key: value`. This is the native shape of cobrapy, and the reader of RAVEN MATLAB depends on it.
3. Strings are unquoted by default. Quotes appear only when YAML would otherwise misparse the value: an empty string, a leading indicator character, `-`, `?` or `:` followed by whitespace, an embedded `: ` or ` #`, and values that read as `true`, `false`, `y`, `n`, `yes`, `no`, `on`, `off`, `null`, a number or a date. The section on numbers, strings and quoting lists the cases.

---

## Top-level layout

```
!!omap
- metaData: !!omap    # optional; RAVEN extension
- metabolites:        # required
- reactions:          # required
- genes:              # required (may be `genes: []`)
- compartments: !!omap # required
- gecko_light: <bool> # optional; GECKO extension
- ec-rxns:            # optional; GECKO extension
- ec-enzymes:         # optional; GECKO extension
```

| Key | Required | Source | Notes |
|-----|----------|--------|-------|
| `metaData` | optional | RAVEN | Provenance block with `id`, `name`, `version`, `date`, `taxonomy`, optionally `givenName`, `familyName`, `email`, `organization`, `note` and `sourceUrl`, and `defaultLB` and `defaultUB`. cobrapy ignores the block, which carries no semantics of the core model. |
| `metabolites` | yes | cobra core | Ordered list of `- !!omap` entries. |
| `reactions` | yes | cobra core | Ordered list of `- !!omap` entries. |
| `genes` | yes | cobra core | Ordered list; `genes: []` for a model without genes. |
| `compartments` | yes | cobra core | `!!omap` of `<code>: <full name>`. |
| `gecko_light` | optional | GECKO | Scalar boolean. cobrapy and raven-toolbox write it at the top level, and the spelling `geckoLight` inside `metaData` is accepted on reading. |
| `ec-rxns` | optional | GECKO | Table per reaction with kcat, source and enzymes. |
| `ec-enzymes` | optional | GECKO | Table per enzyme with MW, sequence and concentration. |

cobrapy writes `id`, `name` and `version` at the root level and not inside `metaData`. The RAVEN readers accept both placements, and the RAVEN writers write the `metaData` form.

---

## Metabolite entry

The field order has the cobra-core fields first and the RAVEN extensions after them:

```yaml
- !!omap
  - id: s_0001               # required
  - name: ATP                # cobra
  - compartment: c           # cobra
  - charge: -4               # cobra (number)
  - formula: C10H16N5O13P3   # cobra
  - notes: "free-text"       # cobra
  - annotation: !!omap       # cobra (MIRIAM + smiles)
      - kegg.compound: C00002
      - chebi:
          - CHEBI:15422
          - CHEBI:30616
      - sbo: SBO:0000247
      - smiles: "OC1=NC..."  # quoted when it contains [ ] : etc.
  - inchis: "InChI=1S/..."   # RAVEN extension
  - deltaG: -2768.1          # RAVEN extension
  - metFrom: KEGG            # RAVEN extension
```

cobrapy writes the first seven keys only, which are the cobra-core block. raven-toolbox and RAVEN MATLAB also write `inchis`, `deltaG` and `metFrom` when those fields are populated. On reading, cobrapy keeps the RAVEN extensions on the metabolite as attributes (attribute fall-through), raven-toolbox captures them in `metabolite.notes` under their YAML name, and RAVEN MATLAB stores them in `model.inchis`, `model.metDeltaG` and `model.metFrom`.

An annotation entry with several values is written as a YAML list (`chebi:` followed by several `-` items), and a single value is written inline (`kegg.compound: C00002`). SMILES strings are stored in the annotation block under the key `smiles`. A `smiles` field at the top level of a metabolite entry is also accepted on reading.

---

## Reaction entry

```yaml
- !!omap
  - id: r_0001                                    # required
  - name: hexokinase                              # cobra
  - metabolites: !!omap                           # cobra (sorted by met id)
      - s_0001: -1.0
      - s_0394: 1.0
  - lower_bound: 0.0                              # cobra (number)
  - upper_bound: 1000.0                           # cobra (number)
  - gene_reaction_rule: YGL253W or YCL040W        # cobra
  - objective_coefficient: 1                      # cobra; omitted when 0
  - subsystem: Glycolysis / Gluconeogenesis       # cobra
  - notes: "MetaNetX ID curated (PR #220)"        # cobra
  - annotation: !!omap                            # cobra
      - kegg.reaction: R00299
      - sbo: SBO:0000176
  - eccodes:                                      # RAVEN extension
      - 2.7.1.1
      - 2.7.1.2
  - references: "PMID:12345"                      # RAVEN extension
  - rxnFrom: KEGG                                 # RAVEN extension
  - deltaG: -17.39                                # RAVEN extension
  - confidence_score: 2.0                         # RAVEN extension
```

Some fields are conditional:

- `objective_coefficient` is written only when it is not zero (cobrapy convention).
- The `metabolites` block is `!!omap []` (a flow-style empty omap) when the reaction has no metabolites, which keeps the file a valid YAML 1.2 document.
- `eccodes` is written inline (`eccodes: 2.7.1.1`) for one code and as a list for several codes. The same applies to `references`.

cobrapy and the writers of raven-toolbox and RAVEN MATLAB use the key `notes`. Some yeast-GEM files use `rxnNotes`, a legacy alias that both readers accept.

A `notes` entry is a string or a mapping. raven-toolbox writes a mapping for notes that have no RAVEN field, for example the base identifier that `merge_compartments` stores on each merged metabolite, with the free-text note under the key `note`. raven-toolbox reads such a mapping back into `notes`. RAVEN shows it in `metNotes`, and a round trip through RAVEN YAML or a `.mat` file does not retain it.

raven-toolbox reads `gene_reaction_rule` with the grammar of `parseGrRule` of RAVEN. The reader of RAVEN splits rules with `getGenesFromGrRules`, which needs a space on each side of a lowercase `and`, `or`, `&` or `|` unless the operator touches a bracket. `G1&G2` is therefore one gene identifier, and `G1 & G2` is two genes joined by `and`. A bracket next to an operator makes no difference, because `getGenesFromGrRules` inserts a space in `)and`, `and(`, `)or`, `or(`, `)&`, `&(`, `)|` and `|(`. raven-toolbox also accepts the spellings `AND`, `OR`, `&&` and `||`, which the reader of RAVEN leaves inside a gene identifier.

Bounds are written as floats with an explicit decimal point (`1000.0`, `-1000.0`), which matches the float representation of Python and the output of cobrapy.

---

## Gene entry

```yaml
- !!omap
  - id: YGL253W              # required
  - name: HXK2               # cobra; omitted when empty
  - annotation: !!omap       # cobra
      - uniprot: P04807
      - ncbigene: 856421
  - protein: P04807          # RAVEN extension
```

Empty names (`name: ''`) are not written, as in RAVEN MATLAB.

---

## Compartments

```yaml
- compartments: !!omap
    - c: cytoplasm
    - e: extracellular
    - m: mitochondrion
```

The block is an `!!omap` of `<short code>: <human-readable name>` pairs. Compartments carry no MIRIAM annotations of their own in the format.

---

## metaData (RAVEN extension)

```yaml
- metaData: !!omap
    - id: yeastGEM_develop
    - name: The Consensus Genome-Scale Metabolic Model of Yeast
    - version: 9.0.0
    - date: 2026-05-27
    - defaultLB: -1000.0
    - defaultUB: 1000.0
    - givenName: Eduard
    - familyName: Kerkhoven
    - email: eduardk@chalmers.se
    - organization: Chalmers University of Technology
    - taxonomy: taxonomy/559292
    - note: "Saccharomyces cerevisiae - strain S288C"
    - sourceUrl: https://github.com/SysBioChalmers/yeast-GEM
```

The block holds provenance. cobrapy ignores it. raven-toolbox keeps the verbatim dictionary in `model.notes['metaData']` and lifts `id`, `name` and `version` to `model.id`, `model.name` and `model.notes['version']`, where the accessors of cobra find them. RAVEN MATLAB fills `model.id`, `model.name`, `model.version` and `model.annotation.*` from the same fields.

`date` is preserved across round trips when the model has it. Otherwise the writer fills in the current date as `YYYY-MM-DD`.

---

## GECKO sections

Enzyme-constrained models carry the EC layer in three additional top-level keys:

```yaml
- gecko_light: false        # true for the "light" formulation
- ec-rxns:
    - !!omap
      - id: r_0001
      - kcat: 25.3
      - source: brenda
      - notes: ""
      - eccodes: 2.7.1.1
      - enzymes: !!omap
          - P04807: 1.0
- ec-enzymes:
    - !!omap
      - genes: YGL253W
      - enzymes: P04807
      - mw: 53942
      - sequence: "MVHLGPK..."
      - concs: .nan
```

The sections map to `model.ec` in RAVEN MATLAB and to `raven_toolbox.io.ec_data.EcData` (attached as `model.ec`) in raven-toolbox. cobrapy ignores them.

An `- enzymes: !!omap` line with nothing under the tag is read as a reaction without enzymes.

The spelling `geckoLight` inside `metaData` is also accepted on reading.

---

## Annotations

The `annotation` block uses MIRIAM-style namespace keys. cobrapy treats the block as a free-form dictionary. raven-toolbox preserves it verbatim in `cobra.Metabolite.annotation`, `Reaction.annotation` and `Gene.annotation`, and RAVEN MATLAB maps it to `model.metMiriams`, `rxnMiriams` and `geneMiriams`.

- A single value is written inline: `kegg.compound: C00002`.
- Several values are written as a YAML list:

  ```yaml
  - chebi:
      - CHEBI:15422
      - CHEBI:30616
  ```

- The `smiles` key in the `annotation` of a metabolite holds the SMILES string (convention of cobrapy). Both readers also accept `smiles` as a top-level field of a metabolite, and the writers use the annotation block.
- The `sbo` key holds the Systems Biology Ontology term that `assignSBOterms` or `add_sbo_terms` assigns.

---

## Numbers, strings and quoting

Floats with a whole-number value are written with an explicit `.0` (`1000.0`, `-1000.0`, `0.0`). Other floats use up to 15 significant digits (`-17.39`, `-2768.1`). `NaN` is encoded as `.nan`, and `+Inf` and `-Inf` as `.inf` and `-.inf` (YAML 1.2 conventions).

The default string style is bare, without quotes. raven-toolbox and RAVEN MATLAB apply the same rules and use the double-quoted style when the value:

- is empty;
- starts with one of `#`, `,`, `[`, `]`, `{`, `}`, `&`, `*`, `!`, `|`, `>`, `'`, `"`, `%`, `@` or `` ` ``;
- is `-`, `?` or `:` alone, or starts with one of them followed by whitespace;
- contains `:` followed by whitespace or at the end of the value, or `#` after whitespace;
- has leading or trailing whitespace or contains a line break;
- would be read as a non-string: `true` or `false` in lower, capitalised or upper case, `y`, `n`, `yes`, `no`, `on` or `off` in any case (the YAML 1.1 booleans), `null`, `Null`, `NULL`, `~`, an integer or float (including hexadecimal, octal, binary, `.inf` and `.nan` forms) or a date in the form `YYYY-MM-DD`.

The characters `[`, `]`, `{` and `}` inside a value do not trigger quoting.

In a double-quoted string, only `\` and `"` are escaped. Other characters, including Unicode and newlines where the model permits them, are passed through.

The reader of raven-toolbox repairs three quoted shapes that are not valid YAML: `""text""`, a double-quoted scalar with an unescaped inner quote (`"a "b" c"`), and a single-quoted scalar with an inner apostrophe (`'it's'`). The values are `"text"`, `a "b" c` and `it's`, as `readYAMLmodel` reads them. The repair runs when the strict parse fails, and it does not handle a comment after the closing quote.

---

## Tool interoperability

| File written by (rows) and reader (columns) | cobrapy | raven-toolbox | RAVEN MATLAB |
|---|---|---|---|
| cobrapy (`save_yaml_model`) | full | full, with extras in `notes` through attribute fall-through | full, including root-level `id`, `name` and `version` |
| raven-toolbox (`write_yaml_model`) | core (no `metaData`-derived `id`); RAVEN extras are unknown top-level keys that do not break parsing | full | full |
| RAVEN MATLAB (`writeYAMLmodel`) | core (no `metaData`-derived `id`); RAVEN extras through attribute fall-through | full | full |

"Full" means that every field is read back into its canonical position on the model object. "Core" means that the fields known to cobrapy are read, and the RAVEN extensions are ignored or kept on the object as attributes (for example `reaction.eccodes`, which is not written again on saving). A round trip through cobrapy is therefore lossy for the RAVEN extensions: only the core fields survive `cobrapy.load` followed by `cobrapy.save`. Round trips through raven-toolbox or RAVEN MATLAB are lossless.

Neither writer reproduces the default layout of `ruamel` in cobrapy byte for byte (indentation, quoting style, line folding). RAVEN and raven-toolbox share a layout with each other. The shared layout follows the structure of a cobrapy file and differs from it in details such as indentation and quoting. The [reconciliation record of raven-gecko-parity](https://github.com/CompMetEng/raven-gecko-parity/blob/develop/docs/yaml-reconciliation.md) gives the reason and the one scenario (`yaml_roundtrip_smallyeast`) that continuously checks that the two writers agree.

---

## Round-trip content counts

`yeast-GEM.yml` (2748 metabolites, 4102 reactions, 1143 genes) is loaded and written again through any of the three tools. Every documented piece of content is preserved:

| Count | After round trip |
|---|---|
| metabolites | 2748 / 2748 |
| reactions | 4102 / 4102 |
| genes | 1143 / 1143 |
| reactions with eccodes | 2411 |
| reactions with deltaG | 3984 |
| metabolites with deltaG | 2696 |
| metabolites with SMILES | 1788 |
| reactions with notes (rxnNotes) | 1443 |

Round trips through cobrapy give 2748 / 4102 / 1143 for the core and drop the RAVEN extensions in the rightmost column, which is the documented loss.
