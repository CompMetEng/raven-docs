# 12. Reconstruction from homology

Homology-based reconstruction builds a draft model for an organism that has none,
using a curated model of a related organism as the source of reactions. Genes in
the new organism are matched to genes in the template by sequence similarity, and
each template reaction whose genes have an accepted match is copied across.

The work happens in two steps: a sequence search that produces a table of hits,
and a transfer step that decides which of those hits are good enough to carry a
reaction. The cut-offs used by the second step determine the size and the
reliability of the draft, and they are what encode the method's assumptions.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `getBlast` | `run_blast` | bidirectional BLASTP between two proteomes |
| `getDiamond` | `run_diamond` | the same, with DIAMOND: faster, less sensitive |
| `getModelFromHomology` | `get_model_from_homology` | carry reactions across on the hits |
| `makeFakeBlastStructure` | `make_ortholog_hits` | feed in orthologs you already have |

## Setup

Two proteomes and a template model. The template is `smallYeast.yml` (53
reactions, 61 genes), and `sce-template.faa` holds the sequences of exactly those
61 *S. cerevisiae* genes. The organism being reconstructed is *Hansenula
polymorpha*, whose full 5177-protein proteome is in `hanpo.faa`. All three files
are in [`docs/data/`](../data/README.md):
[`smallYeast.yml`](../data/smallYeast.yml),
[`sce-template.faa`](../data/sce-template.faa) and
[`hanpo.faa`](../data/hanpo.faa).

The template model's id must match the id used for the BLAST. The transfer step
looks up each hit's source organism by that id to find which template model the
reaction should come from, so a mismatch leaves every hit unattributable.

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

## 12.1 BLAST, in both directions

Both toolboxes run BLASTP twice: the new organism's proteome against the
template's, and the template's against the new organism's.

The second direction is what makes orthology testable. A one-directional search
gives, for each new gene, the template gene it resembles most, but the most
similar sequence is not necessarily the corresponding one. A gene that has been
duplicated in the template, or a conserved domain shared across a family, will
attract hits from genes that do a different job. Searching both ways lets the
transfer step ask whether two genes pick *each other*, which is a much stronger
claim than either picking the other alone.

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

The two directions return different counts because they ask different
questions, and neither count is of genes: each line of BLAST output is one
alignment. The 159 alignments in the template-to-*H. polymorpha* direction come
from 60 of the 61 template genes, and the 178 in the other direction from 106
*H. polymorpha* genes. Neither number is the number of orthologs; that is decided
in the next step, from the pairs that appear in both directions.

The shape of the result differs between the toolboxes. RAVEN returns a struct
array with one entry per direction, each carrying `fromId`, `toId`, `fromGenes`,
`toGenes` and per-hit `evalue`, `aligLen` and `identity` vectors. raven-toolbox
returns a single `pandas` DataFrame with `from_id` and `to_id` columns, so both
directions are in one table and can be filtered with ordinary DataFrame
operations before being passed on.

Both call the same BLAST+ executables with the same parameters, which is why the
hit counts agree. Neither ships those executables: both download them per
platform on first use and cache them, so the first reconstruction on a new
machine needs network access. raven-toolbox will use the copies on your `PATH`
instead if `RAVEN_PYTHON_BLASTP` points at them.

Without `threads`, `run_blast`, `run_diamond` and `run_supporth` use every CPU the process may run on. In MATLAB, `getBlast`, `getDiamond` and `runSuppOrth` use the cores assigned to MATLAB (`feature('numcores')`); `runSuppOrth` is the one of the three with a `threads` option.

`getDiamond` and `run_diamond` are drop-in alternatives that search with DIAMOND
instead. DIAMOND indexes the database and searches in reduced amino-acid
alphabets, which makes it one to two orders of magnitude faster on a full
proteome pair (minutes rather than hours), and less sensitive for
distant homologs, where the seeds it uses are less likely to match. For a
template within the same genus the difference is small; for a template several
hundred million years away, BLASTP finds pairs DIAMOND misses.

If you already have orthology assignments from another source (OrthoFinder,
OMA, a published table), `makeFakeBlastStructure` and `make_ortholog_hits` wrap
them in the structure the transfer step expects, so no search is run.

## 12.2 From hits to a draft

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

The transfer works reaction by reaction. For each reaction in the template, the
genes named in its gene-reaction rule are looked up in the hit table; a template
gene is replaced by its accepted counterpart in the new organism, and the
reaction is carried over if the rule still resolves to something satisfiable
after the substitution. A reaction requiring two subunits is dropped when only
one of them has a counterpart; a reaction with two isozymes survives on either.
The metabolites a carried reaction needs come with it, which is why the draft has
49 metabolites rather than the template's 52: the three that appear only in
dropped reactions are not created.

The `Standardizing grRules` line is RAVEN rewriting the template's rules into a
canonical form before substituting into them, so that the same rule written two
ways is handled identically.

`get_model_from_homology` returns a `HomologyResult` rather than a bare model.
`.model` is the draft; `.gene_map` records which template gene each new gene was
derived from, which is what you need to trace a reaction back to the evidence
that put it there; and `.candidates`, populated when `review_identity=` is given,
collects reactions that failed the identity cut-off but came within the value
given. Those are near-misses that a threshold rejected, rather than absences.
RAVEN returns the draft and its hit genes as two separate outputs.

The draft is smaller than the template because reactions whose genes have no
accepted counterpart are not carried over. That is the intended behaviour, and
also the main source of error: a reaction left out because no hit passed the
cut-offs looks exactly like a reaction the organism genuinely lacks.

## 12.3 The cut-offs decide the model

Three cut-offs control which hits are accepted, and tightening any of them
shrinks the draft.

`maxE` / `max_evalue` (`1e-30`) is the maximum BLAST E-value, the number of
hits of at least this quality expected by chance in a database this size. The
default is strict by BLAST standards, where `1e-5` is a common threshold, because
transferring a reaction on a marginal hit adds a claim about metabolism that
nothing downstream will question.

`minLen` / `min_align_len` (`100`) is the minimum aligned length in residues. It
exists to reject hits that align well over a short conserved domain while the
rest of the protein is unrelated. The value was measured against KEGG and OMA
orthology assignments across four organisms: anything at or below 150 gave the
same result, and higher values discarded genuine orthologs whose alignment was
interrupted.

`minIde` / `min_identity` (`40`) is the minimum percentage identity across the
alignment.

A fourth parameter, `strictness`, decides how much agreement between the two
BLAST directions is required, from accepting any hit that passes the cut-offs up
to requiring reciprocal best hits. At its strictest setting, ties between
candidate hits are broken on bitscore, which unlike the E-value does not depend
on the size of the database searched, so the choice does not shift when a
proteome is updated.

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

Raising the two thresholds removes five reactions and eight genes. Whether that is
an improvement depends on what the draft is for: a model that will be curated
by hand benefits from the extra candidates, since a wrong reaction is easier to
spot than a missing one, while a model used directly for prediction is better
with fewer and better-supported reactions.

:::{note} Reproducing an older reconstruction
Some of these defaults are not the values RAVEN 2 used, so the same script
can produce a different draft under RAVEN 3. Set them explicitly, or see
[Migrating from RAVEN 2](../raven3-migration.md).
:::

## 12.4 A draft is not a model

What comes out of this step has reactions, metabolites and genes, and nothing
else. There is no biomass reaction unless a template reaction happened to carry
one, no exchange reactions, and no guarantee that anything can carry flux.

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

None of the 37 reactions can carry flux. This is not a defect in the draft: with
no exchange reactions nothing can enter or leave, so the only flux left is
internal cycling, and this draft has none. The number says nothing yet about the quality of
the reconstruction, and will only become informative once a medium is defined.

A homology draft is a set of claims about which reactions the organism has. Turning
it into a model means giving it a medium
([5. Growth media and conditions](media.md)), closing the gaps that stop it
producing biomass ([17. Gap-filling](gap-filling.md)), and checking it against
what the organism is known to do ([15. Metabolic tasks](tasks.md)). The
[GEM reconstruction protocol](../protocol/index.md) follows that path for
*H. polymorpha* at full scale.

:::{warning} What can go wrong
- **Identifiers that do not match.** The FASTA headers must carry the same
  gene ids as the template model's `genes`. A mismatch produces a draft with
  no reactions and no error.
- **One template, one organism's biases.** Every reaction in the draft comes
  from the template, so anything the template lacks the draft cannot have.
  Several templates, with `preferredOrder`, spread that risk.
- **Reading absence as evidence.** A reaction left out means no acceptable
  hit was found, not that the organism lacks the capability. Sequencing
  gaps, divergent sequences and short proteins all look the same here.
- **Full proteomes are slow.** The example on this page finishes in seconds
  because the template proteome is 61 sequences. Two complete proteomes take
  minutes to hours with BLASTP; that is what `getDiamond` and `run_diamond`
  are for.
:::

## See also

- [17. Gap-filling](gap-filling.md), the usual next step, and the one that
  decides what the draft is missing.
- [14. Context-specific models](init.md), cutting a model down by evidence
  instead of building one up from homology.
- [21. Comparing models](comparing.md), checking a draft against a curated
  model of the same organism.
