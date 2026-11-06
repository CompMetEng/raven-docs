# Reconstruction from homology

Homology-based reconstruction builds a draft model for an organism without one, with a curated model of a related organism as the source of reactions. Genes of the new organism are matched to genes of the template by sequence similarity, and a template reaction is copied when its genes have an accepted match.

The reconstruction has two steps. A sequence search produces a table of hits, and a transfer step selects the hits that are sufficient to support a reaction. The cut-offs of the transfer step determine the size and the reliability of the draft.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getBlast` | `run_blast` | bidirectional BLASTP between two proteomes |
| `getDiamond` | `run_diamond` | the same search with DIAMOND, which is faster and less sensitive |
| `getModelFromHomology` | `get_model_from_homology` | transfer reactions on the basis of the hits |
| `makeFakeBlastStructure` | `make_ortholog_hits` | supply orthologs that are available already |

## Setup

The setup uses two proteomes and a template model. The template is `smallYeast.yml` with 53 reactions and 61 genes, and `sce-template.faa` holds the sequences of these 61 *S. cerevisiae* genes. The organism to reconstruct is *Hansenula polymorpha*, whose proteome of 5177 proteins is in `hanpo.faa`. The three files are in [`docs/data/`](../data/README.md): [`smallYeast.yml`](../data/smallYeast.yml), [`sce-template.faa`](../data/sce-template.faa) and [`hanpo.faa`](../data/hanpo.faa).

The identifier of the template model must match the identifier used for the BLAST. The transfer step looks up the source organism of each hit by that identifier to find the template model of the reaction, and a mismatch leaves every hit without a source.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
template = readYAMLmodel('smallYeast.yml');
template.id = 'sce';
fprintf('template: %d rxns, %d genes\n', numel(template.rxns), numel(template.genes));
```

```text
template: 53 rxns, 61 genes
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from raven_toolbox.io import read_yaml_model

cobra.Configuration().processes = 1

template = read_yaml_model("smallYeast.yml")
template.id = "sce"
print(f"template: {len(template.reactions)} rxns, {len(template.genes)} genes")
```

```text
template: 53 rxns, 61 genes
```
:::
::::

## BLAST in both directions

Both toolboxes run BLASTP twice: the proteome of the new organism against the proteome of the template, and the proteome of the template against the proteome of the new organism.

The second direction makes orthology testable. A search in one direction gives for each new gene the template gene that it resembles most, and the most similar sequence is not always the corresponding gene. A gene duplicated in the template, or a conserved domain shared across a family, attracts hits from genes with a different function. With both directions, the transfer step tests whether two genes select each other, which supports orthology more strongly than a selection in one direction.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
blastStructure = getBlast('hanpo', 'hanpo.faa', {'sce'}, {'sce-template.faa'});
for i = 1:numel(blastStructure)
    fprintf('%s -> %s: %d hits\n', blastStructure(i).fromId, ...
        blastStructure(i).toId, numel(blastStructure(i).fromGenes));
end
```

```text
BLASTing "sce" against "hanpo"..
BLASTing "hanpo" against "sce"..
sce -> hanpo: 159 hits
hanpo -> sce: 178 hits
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.reconstruction.homology import run_blast

hits = run_blast("hanpo", "hanpo.faa", ["sce"], ["sce-template.faa"])
print(f"{len(hits)} hits total")
print(hits.groupby(["from_id", "to_id"]).size().to_string())
```

```text
337 hits total
from_id  to_id
hanpo    sce      178
sce      hanpo    159
```
:::
::::

The two directions return different counts because they answer different questions, and neither count is a count of genes, as each line of BLAST output is one alignment. The 159 alignments from the template to *H. polymorpha* come from 60 of the 61 template genes, and the 178 alignments in the other direction come from 106 *H. polymorpha* genes. Neither number is the number of orthologs. The next step determines that from the pairs that occur in both directions.

The result has a different shape in the two toolboxes. RAVEN returns a struct array with one entry per direction. Each entry has `fromId`, `toId`, `fromGenes`, `toGenes` and per-hit vectors `evalue`, `aligLen` and `identity`. raven-toolbox returns one `pandas` DataFrame with the columns `from_id` and `to_id`, which holds both directions and can be filtered with DataFrame operations before it is passed on.

Both call the same BLAST+ executables with the same parameters, so the hit counts agree. Neither toolbox includes the executables. RAVEN downloads them for the platform on first use and caches them. raven-toolbox uses `RAVEN_PYTHON_BLASTP` if it is set, then a `blastp` on the `PATH`, and downloads when neither exists. A first reconstruction that downloads needs network access.

Without `threads`, `run_blast`, `run_diamond` and `run_supporth` use every CPU that the process can run on. In MATLAB, `getBlast`, `getDiamond` and `runSuppOrth` use the cores that are assigned to MATLAB (`feature('numcores')`), and `runSuppOrth` is the sole function with a `threads` option.

`getDiamond` and `run_diamond` are alternatives that search with DIAMOND. With `--more-sensitive`, the default of `run_diamond`, DIAMOND was 11.7 and 14.3 times faster than BLASTP on two complete proteome pairs (12 s against 140 s, and 14 s against 200 s, in [Homology cut-off calibration](../parameter-tuning/studies/homology-cutoff-calibration.md)). DIAMOND returned fewer hits: 32,192 against 54,513 for *K. lactis* against *S. cerevisiae*. After the filters identity 40, length 200 and E-value 1e-30, the two aligners kept 87.9 to 92.3 % of the same pairs on four targets (Jaccard index).

`makeFakeBlastStructure` and `make_ortholog_hits` put orthology assignments from another source (OrthoFinder, OMA or a published table) into the structure that the transfer step expects, and no search is run.

## From hits to a draft

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
draft = getModelFromHomology({template}, blastStructure, 'hanpo');
fprintf('draft: %d rxns, %d mets, %d genes\n', ...
    numel(draft.rxns), numel(draft.mets), numel(draft.genes));
```

```text
Standardizing grRules of template model with ID "sce" ... done
draft: 37 rxns, 49 mets, 54 genes
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.reconstruction.homology import get_model_from_homology

result = get_model_from_homology([template], hits, "hanpo")
draft = result.model
print(f"draft: {len(draft.reactions)} rxns, {len(draft.metabolites)} mets, "
      f"{len(draft.genes)} genes")
```

```text
draft: 37 rxns, 49 mets, 54 genes
```
:::
::::

The transfer works reaction by reaction. For each reaction of the template, the genes in its gene rule are looked up in the hit table. A template gene is replaced by its accepted counterpart in the new organism, and the reaction is transferred when the rule can be satisfied after the substitution. A reaction that needs two subunits is kept with a placeholder gene (`OLD_<model>_<gene>`) for the missing subunit under the default `complexPolicy` (`complex_policy` in Python) of `flag`, and the policy `drop` removes it. A reaction with two isozymes is kept when either has a counterpart. The metabolites that a transferred reaction needs are transferred with it. The draft has 49 metabolites against 52 in the template, because the three metabolites that occur in dropped reactions alone are not created.

The line `Standardizing grRules` shows RAVEN rewriting the rules of the template in a canonical form before the substitution. One rule written in two ways is then handled identically.

`get_model_from_homology` returns a `HomologyResult`, which holds more than the model:

- `.model` is the draft.
- `.gene_map` maps, per template model, each template gene to the new genes that replace it (`{model_id: {template_gene: [new_gene, ...]}}`). It traces a reaction back to the evidence that placed it in the draft.
- `.candidates` is filled when `review_identity=` is given. It collects the reactions that failed the identity cut-off and came within the given value, so these are near misses that a threshold rejected, and they are not reactions without a hit.

RAVEN returns the draft and its hit genes as two separate outputs.

The draft is smaller than the template, because reactions whose genes have no accepted counterpart are not transferred. This is the intended behaviour and also the main source of error, as a reaction left out because no hit passed the cut-offs looks the same as a reaction that the organism lacks.

## Hit cut-offs

Three cut-offs select the accepted hits, and tightening any of them reduces the size of the draft.

`maxE` / `max_evalue` (`1e-30`) is the maximum BLAST E-value, the number of hits of at least this quality that is expected by chance in a database of this size. The default is strict for BLAST, where `1e-5` is a common threshold, and it keeps the value of RAVEN 2. In four organisms, the F0.5 score against KEGG was identical from `1e-4` to `1e-30`, up to 0.006 lower at `1e-50` and 0.020 to 0.063 lower at `1e-100` ([Homology cut-off calibration](../parameter-tuning/studies/homology-cutoff-calibration.md)).

`minLen` / `min_align_len` (`100`) is the minimum aligned length in residues. It rejects hits that align over a short conserved domain while the rest of the protein is unrelated. The value was measured against KEGG orthology assignments in four organisms ([Homology cut-off calibration](../parameter-tuning/studies/homology-cutoff-calibration.md)). The values 50 and 100 gave the same score, 150 gave a score that was at most 0.003 lower, and 200 and 300 gave lower scores. At 200 the loss came mainly from recall, and precision and recall were not reported for 300.

`minIde` / `min_identity` (`40`) is the minimum percentage of identical residues across the alignment.

A fourth parameter, `strictness`, sets how much agreement between the two BLAST directions is required. It has three levels. Level 1, the default, requires a hit that passes the cut-offs in both directions. Level 2 requires a hit in one direction, and level 3 keeps the best hit per gene in each direction. At the strictest setting, each gene keeps its best hits by bitscore in each direction, and all of them when several tie. The bitscore, unlike the E-value, does not depend on the size of the searched database, so the choice does not shift when a proteome is updated.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
strict = getModelFromHomology({template}, blastStructure, 'hanpo', ...
    'maxE', 1e-100, 'minLen', 250);
fprintf('strict draft: %d rxns, %d genes\n', numel(strict.rxns), numel(strict.genes));
```

```text
Standardizing grRules of template model with ID "sce" ... done
strict draft: 32 rxns, 46 genes
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
strict = get_model_from_homology([template], hits, "hanpo",
                                 max_evalue=1e-100, min_align_len=250).model
print(f"strict draft: {len(strict.reactions)} rxns, {len(strict.genes)} genes")
```

```text
strict draft: 32 rxns, 46 genes
```
:::
::::

The two stricter thresholds remove five reactions and eight genes. Whether this is an improvement depends on the purpose of the draft. A draft that is curated by hand benefits from the additional candidates, as a wrong reaction is easier to notice than a missing one. A draft that is used for prediction directly is better with fewer and better supported reactions.

:::{admonition} Reproducing a RAVEN 2 reconstruction
:class: note

Some of these defaults differ from the values of RAVEN 2, so the same script can give a different draft in RAVEN 3. The values should be set explicitly, or [Migrating from RAVEN 2](../raven3-migration.md) consulted.
:::

## Contents of a draft

The result of this step has reactions, metabolites and genes. It has no biomass reaction unless a template reaction contained one, no exchange reactions, and no guarantee that any reaction carries flux.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
exchangeRxns = getExchangeRxns(draft);
fprintf('objective set: %d\n', any(draft.c ~= 0));
fprintf('exchange reactions: %d\n', numel(exchangeRxns));
fprintf('reactions that can carry flux: %d of %d\n', ...
    sum(haveFlux(draft)), numel(draft.rxns));
```

```text
objective set: 0
exchange reactions: 0
reactions that can carry flux: 0 of 37
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import find_blocked_reactions

blocked = find_blocked_reactions(draft)
print(f"objective set: {str(draft.objective.expression) != '0'}")
print(f"exchange reactions: {len(draft.boundary)}")
print(f"reactions that can carry flux: {len(draft.reactions) - len(blocked)} "
      f"of {len(draft.reactions)}")
```

```text
objective set: False
exchange reactions: 0
reactions that can carry flux: 0 of 37
```
:::
::::

None of the 37 reactions carries flux. This does not indicate a defect of the draft. Without exchange reactions nothing enters or leaves the model, and the draft has no internal cycle, so no flux is possible. The number says nothing about the quality of the reconstruction, and it becomes informative after a medium is defined.

A homology draft is a set of claims about the reactions of the organism. Three steps turn it into a model: a medium ([Growth media and conditions](media.md)), gap-filling to fill the gaps that prevent biomass production ([Gap-filling](gap-filling.md)), and a check against the known behaviour of the organism ([Metabolic tasks](tasks.md)). The [GEM reconstruction protocol](../protocol/index.md) follows this path for *H. polymorpha* at full scale.

:::{admonition} Troubleshooting
:class: warning

- The identifiers do not match. The headers of the FASTA file contain the gene identifiers of the `genes` field of the template model. A mismatch gives a draft without reactions and without an error.
- One template has the bias of one organism. Every reaction of the draft comes from the template, so the draft cannot have anything that the template lacks. Several templates, ordered with `preferredOrder`, spread the risk.
- Absence is read as evidence. A missing reaction means that no acceptable hit was found, and it does not show that the organism lacks the capability. Sequencing gaps, divergent sequences and short proteins look the same.
- Complete proteomes are slow. The example finishes in seconds because the template proteome has 61 sequences. Two complete proteomes take minutes to hours with BLASTP, and `getDiamond` and `run_diamond` are faster.
:::

## See also

- [Gap-filling](gap-filling.md): the next step, which determines what the draft lacks.
- [Context-specific models](init.md): reducing a model by evidence, where homology builds a model up.
- [Comparing models](comparing.md): comparing a draft with a curated model of the same organism.
