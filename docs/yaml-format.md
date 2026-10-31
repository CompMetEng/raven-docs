# YAML file format

The YAML format is produced and consumed by three tools:

- cobrapy ([`cobra.io.{load,save}_yaml_model`](https://github.com/opencobra/cobrapy))
- raven-toolbox (`raven_toolbox.io.yaml.{read,write}_yaml_model`, see [API](api/index.md))
- RAVEN MATLAB (`readYAMLmodel.m` and `writeYAMLmodel.m` in the [RAVEN repo](https://github.com/CompMetEng/RAVEN/tree/develop/io))

The same file can be round-tripped through any of the three. cobrapy defines the core shape. raven-toolbox and RAVEN MATLAB add namespaced extensions (RAVEN curation fields, MIRIAM cross-references already covered by cobrapy's `annotation`, and the GECKO `ec-*` sections) that leave the cobra-known shape intact.

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

Three structural rules apply throughout the field-by-field description:

1. The whole document is one ordered mapping (`!!omap`) at the root. Every nested map that preserves key order is also `!!omap` (metaData, each metabolite, reaction and gene entry, `annotation`, `metabolites`, `compartments`, and the ec sections).
2. Each metabolite, reaction, and gene is one `- !!omap` element of a list. Inside that mapping, every field is written as `- key: value`. This is cobrapy's native shape, and RAVEN MATLAB's reader depends on it.
3. Strings are unquoted by default. Quotes appear only when YAML would otherwise misparse the value (an empty string; a leading indicator character; `-`, `?` or `:` followed by whitespace; embedded `: ` or ` #`; values that read as `true`, `false`, `y`, `n`, `yes`, `no`, `on`, `off`, `null`, a number or a date). The section on numbers, strings and quoting lists the cases.

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
| `metaData` | optional | RAVEN | Provenance block. Holds `id`, `name`, `version`, `date`, `taxonomy`, optionally `givenName`, `familyName`, `email`, `organization`, `note` and `sourceUrl`, plus `defaultLB` and `defaultUB`. Cobrapy ignores this block, which carries no semantics of the core model. |
| `metabolites` | yes | cobra core | Ordered list of `- !!omap` entries. |
| `reactions` | yes | cobra core | Ordered list of `- !!omap` entries. |
| `genes` | yes | cobra core | Ordered list; may be `genes: []` for a model with no genes. |
| `compartments` | yes | cobra core | `!!omap` of `<code>: <full name>`. |
| `gecko_light` | optional | GECKO | Scalar boolean. Cobrapy and raven-toolbox emit this at the top level; the spelling `geckoLight` inside `metaData` is accepted on read. |
| `ec-rxns` | optional | GECKO | Per-reaction coupling table of kcat, source and enzymes. |
| `ec-enzymes` | optional | GECKO | Per-enzyme table of MW, sequence and concentration. |

Cobrapy writes `id`, `name` and `version` at the root level and not inside `metaData`. The RAVEN readers accept both placements, and the RAVEN writers write the `metaData` form.

---

## Metabolite entry

Field order (cobra-core first, then RAVEN extensions):

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

Cobrapy emits exactly the first seven keys (the cobra-core block). raven-toolbox and RAVEN MATLAB additionally emit `inchis`, `deltaG`, and `metFrom` when those fields are populated. On read, cobrapy puts the RAVEN extensions on the metabolite as attribute fall-through, raven-toolbox captures them into `metabolite.notes` (keyed by their YAML name), and RAVEN MATLAB stores them on `model.inchis`, `model.metDeltaG` and `model.metFrom`.

Annotation entries with multiple values are emitted as a YAML list (`chebi:` then several `-` items). Single-value entries are emitted inline (`kegg.compound: C00002`). SMILES strings are stored inside the annotation block under the `smiles` key. A `smiles` field at the top level of a metabolite entry is also accepted on read.

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

- `objective_coefficient` is only written when non-zero (cobrapy convention).
- The `metabolites` block uses `!!omap []` (flow-style empty omap) when the reaction has no metabolites, which keeps the file a valid YAML 1.2 document.
- `eccodes` is written inline (`eccodes: 2.7.1.1`) when there is one code, and as a list when there are several. The same applies to `references`.

Cobrapy and the raven-toolbox and RAVEN MATLAB writers use the key `notes`. Some yeast-GEM files use `rxnNotes`, a legacy alias that both readers accept.

A `notes` entry can be a string or a mapping. raven-toolbox writes one for notes that have no RAVEN field, for example the base id that `merge_compartments` stores on each merged metabolite, with the free-text note under the key `note`. raven-toolbox reads such a mapping back into `notes`. RAVEN shows it in `metNotes`, and a round trip through RAVEN YAML or a `.mat` file does not retain it.

raven-toolbox reads `gene_reaction_rule` with the grammar of RAVEN's `parseGrRule`. RAVEN's reader splits rules with `getGenesFromGrRules`, which needs a space on each side of a lowercase `and`, `or`, `&` or `|` unless the operator touches a bracket, so `G1&G2` is one gene id and `G1 & G2` is two genes joined by `and`. Brackets next to an operator make no difference, because `getGenesFromGrRules` inserts a space in `)and`, `and(`, `)or`, `or(`, `)&`, `&(`, `)|` and `|(`. raven-toolbox also accepts the spellings `AND`, `OR`, `&&` and `||`, which RAVEN's reader leaves inside a gene id.

Bounds are emitted as floats with an explicit decimal point (`1000.0`, `-1000.0`), matching Python's float repr and cobrapy's output.

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

Empty names (`name: ''`) are not emitted (matches RAVEN MATLAB's behaviour).

---

## Compartments

```yaml
- compartments: !!omap
    - c: cytoplasm
    - e: extracellular
    - m: mitochondrion
```

An `!!omap` of `<short code>: <human-readable name>` pairs. Compartments carry no MIRIAM annotations of their own in the format.

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

The block holds provenance. Cobrapy ignores the block. raven-toolbox keeps the verbatim dictionary on `model.notes['metaData']` and lifts `id`, `name` and `version` to `model.id`, `model.name` and `model.notes['version']`, where cobra-shape accessors find them. RAVEN MATLAB populates `model.id`, `model.name`, `model.version` and `model.annotation.*` from the same fields.

`date` is preserved across round-trips when present on the model. Otherwise the writer fills in `YYYY-MM-DD` of the current date.

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

The sections map onto `model.ec` in RAVEN MATLAB and `raven_toolbox.io.ec_data.EcData` (attached as `model.ec`) in raven-toolbox. Cobrapy ignores the sections.

An `- enzymes: !!omap` line with nothing under the tag is read as a reaction with no enzymes.

The spelling `geckoLight` inside `metaData` is also accepted on read.

---

## Annotations

The `annotation` block uses MIRIAM-style namespace keys. Cobrapy treats the block as a free-form dictionary, raven-toolbox preserves it verbatim through `cobra.Metabolite.annotation`, `Reaction.annotation` and `Gene.annotation`, and RAVEN MATLAB maps it to `model.metMiriams`, `rxnMiriams` and `geneMiriams`.

- A single value is written inline: `kegg.compound: C00002`.
- Multiple values are written as a YAML list:

  ```yaml
  - chebi:
      - CHEBI:15422
      - CHEBI:30616
  ```

- The `smiles` key inside a metabolite's `annotation` carries the SMILES string (cobrapy convention). Both readers also accept `smiles` as a metabolite top-level field, and the writers use the annotation block.
- The `sbo` key carries the Systems Biology Ontology term assigned by `assignSBOterms` / `add_sbo_terms`.

---

## Numbers, strings and quoting

Whole-number floats are written with an explicit `.0` (`1000.0`, `-1000.0`, `0.0`). Other floats use up to 15 significant digits (`-17.39`, `-2768.1`). `NaN` is encoded as `.nan`, and `+Inf` and `-Inf` as `.inf` and `-.inf` (YAML 1.2 conventions).

The default string style is bare (no quotes). raven-toolbox and RAVEN MATLAB apply the same rules and use double-quoted style when the value:

- is empty;
- starts with one of `#`, `,`, `[`, `]`, `{`, `}`, `&`, `*`, `!`, `|`, `>`, `'`, `"`, `%`, `@` or `` ` ``;
- is `-`, `?` or `:` alone, or starts with one of them followed by whitespace;
- contains `:` followed by whitespace or at the end of the value, or `#` after whitespace;
- has leading or trailing whitespace or contains a line break;
- would be read as a non-string: `true` or `false` in lower, capitalised or upper case, `y`, `n`, `yes`, `no`, `on` or `off` in any case (the YAML 1.1 booleans), `null`, `Null`, `NULL`, `~`, an integer or float (including hexadecimal, octal, binary, `.inf` and `.nan` forms) or a date in the form `YYYY-MM-DD`.

The characters `[`, `]`, `{` and `}` inside a value do not trigger quoting.

In a double-quoted string, only `\` and `"` are escaped. Other characters (including Unicode, and newlines if the underlying model permits them) are passed through.

The raven-toolbox reader repairs three quoted shapes that are not valid YAML: `""text""`, a double-quoted scalar with an unescaped inner quote (`"a "b" c"`), and a single-quoted scalar with an inner apostrophe (`'it's'`). The values are `"text"`, `a "b" c` and `it's`, as `readYAMLmodel` reads them. The repair runs when the strict parse fails and does not handle a comment after the closing quote.

---

## Tool interoperability

| File written by (rows) and reader (columns) | cobrapy | raven-toolbox | RAVEN MATLAB |
|---|---|---|---|
| cobrapy (`save_yaml_model`) | full | full, with extras in `notes` via attribute fall-through | full, including root-level `id` / `name` / `version` |
| raven-toolbox (`write_yaml_model`) | core (no `metaData`-derived `id`); RAVEN extras are unknown top-level keys that do not break parsing | full | full |
| RAVEN MATLAB (`writeYAMLmodel`) | core (no `metaData`-derived `id`); RAVEN extras via attribute fall-through | full | full |

"Full" means that every field is read back into its canonical position on the model object. "Core" means that cobrapy-known fields are read and RAVEN extensions are ignored or kept on the object as attribute fall-through (for example `reaction.eccodes`, not re-emitted on save). A round-trip through cobrapy is therefore lossy for RAVEN extensions: only the core fields survive `cobrapy.load → cobrapy.save`. Round-trips through raven-toolbox or RAVEN MATLAB are lossless.

Neither writer reproduces cobrapy's own `ruamel`-default layout byte-for-byte (indentation, quoting style, line folding). RAVEN and raven-toolbox share a layout with each other. The shared layout follows the structure of a cobrapy file and differs from it in details such as indentation and quoting. [raven-gecko-parity's reconciliation record](https://github.com/CompMetEng/raven-gecko-parity/blob/develop/docs/yaml-reconciliation.md) gives the reason and the one scenario (`yaml_roundtrip_smallyeast`) that continuously checks that the two writers agree.

---

## Round-trip content counts

Loading `yeast-GEM.yml` (2748 metabolites, 4102 reactions, 1143 genes) and re-writing it through any of the three tools preserves every documented piece of content:

| Count | After round-trip |
|---|---|
| metabolites | 2748 / 2748 |
| reactions | 4102 / 4102 |
| genes | 1143 / 1143 |
| reactions with eccodes | 2411 |
| reactions with deltaG | 3984 |
| metabolites with deltaG | 2696 |
| metabolites with SMILES | 1788 |
| reactions with notes (rxnNotes) | 1443 |

Cobrapy round-trips give 2748 / 4102 / 1143 for the core and drop the RAVEN extensions in the rightmost column, which is the documented loss.
