<!-- run-examples: skip-file -->

# 13. Reconstruction from KEGG

[12. Reconstruction from homology](homology.md) needs a template model of a
related organism. KEGG needs none: its orthology groups (KOs) are already tied to
reactions, so annotating a genome with KOs gives you a draft directly. Which
route you take depends on one thing: whether your organism is already in KEGG.

:::{note} These examples are not run by the documentation build
A KEGG reconstruction downloads tens of megabytes and takes minutes, so this
page is not executed with the others. The Python numbers below come from
raven-toolbox 3.0.0b1 with the `kegg118` artefacts (about 2.5 minutes per call
on a recent workstation, with or without the cache).
:::

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `getKEGGModelForOrganism` | `get_kegg_model_for_organism_from_artefacts` | draft from an organism's KEGG annotation |
| `getKEGGModelForOrganism` (with `fastaFile`) | `get_kegg_model_from_sequences` | draft from an HMM search of your proteins |
| `getModelFromKEGG` | `build_reference_model` | assemble and cache the global KEGG model |
| `getPhylDist` | `PhylDist` | phylogenetic distance, used to weight the search |

## 13.1 When the organism is already in KEGG

If KEGG has your species (`sce` for *S. cerevisiae*), its gene-to-KO assignments
are already made, and no sequence search is needed. This is the fast route, and
the one to prefer when it applies.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = getKEGGModelForOrganism('sce', ...
    'dataDir', fullfile(tempdir, 'kegg118_eukaryotes'));
```

Without a `fastaFile`, the reconstruction runs from the organism
abbreviation alone and no sequence search happens, so the HMM library is not
fetched; the download is guarded on a FASTA being supplied. What it does need
is the global KEGG model, which `getModelFromKEGG` supplies. On first use
there is no `keggModel.mat` to load, so it downloads the published artefacts,
the gene-free reference model plus the KO, reaction and organism-gene tables,
assembles them, and caches the result. That first build takes a while and
needs a few hundred MB of disk; later calls load the cached file directly.

This route ignores every setting except `keepSpontaneous`,
`keepUndefinedStoich`, `keepIncomplete` and `keepGeneral`, since the cut-offs
and phylogenetic weighting only apply to a sequence search.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.reconstruction.kegg import (
    get_kegg_model_for_organism_from_artefacts,
)

model = get_kegg_model_for_organism_from_artefacts("sce")
print(f"{len(model.reactions)} rxns, {len(model.metabolites)} mets, "
      f"{len(model.genes)} genes")
```

```text
1357 rxns, 1502 mets, 838 genes
```

The artefacts (a reference model and three tables, about 47 MB) are fetched
from the `kegg118` raven-data release on first use and cached; see
[Download data and binaries](../installation/data-and-binaries.md) for
where, and how to fetch them ahead of a batch run. Expect a few minutes for
the first run and much the same afterwards: the download is not the slow part,
assembling the draft from the tables is.
:::
::::

## 13.2 When it is not

For an organism KEGG has never seen, the KO assignments have to be made from
sequence. Both toolboxes search your proteins against a library of profile HMMs,
one per KO, trained on either prokaryotic or eukaryotic sequences.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = getKEGGModelForOrganism('hpo', ...
    'fastaFile', 'hanpo.faa', ...
    'dataDir', fullfile(tempdir, 'kegg118_eukaryotes'), ...
    'outDir', fullfile(tempdir, 'hanpo_hmm'));
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.reconstruction.kegg import get_kegg_model_from_sequences

model = get_kegg_model_from_sequences("hanpo.faa", domain="eukaryotes")
```
:::
::::

This is the expensive route. The eukaryotic HMM library alone is **129 MB
compressed**, and `hmmsearch` against every KO takes tens of minutes to hours for
a full proteome, which is why `outDir` exists in the MATLAB version: results are
kept per-KO so an interrupted run can resume rather than start again. It also
needs HMMER, which has no bundle for every platform;
[Download data and binaries](../installation/data-and-binaries.md) has the
matrix.

The organism id still matters even here. It sets the phylogenetic distance used
to weight the KO assignments, so pick the closest relative KEGG does have.
`maxPhylDist` decides how far the search may reach: `-1` restricts it to the
same domain, and a positive value admits organisms out to that distance.

Three cut-offs shape the assignment. `cutOff` is the HMMER significance a hit
needs at all. `minScoreRatioKO` drops genes that fit a KO far worse than the
best gene in it, and `minScoreRatioG` drops KOs that fit a gene far worse than
that gene's best KO; the two prune the same matrix from opposite sides. Their
defaults were measured rather than inherited, and the
[KEGG HMM cut-off study](../parameter-tuning/studies/kegg-hmm-cutoff-calibration.md)
records which of them actually moves the result.

## 13.3 What a KEGG draft is

A KEGG draft is genome-scale in size, and unlike a working model in every other
respect.

```text title="the sce draft, measured"
reactions:     1357
metabolites:   1502
genes:          838
compartments:  1 (everything is in 's')
exchange rxns:   0
objective:       none
```

**There are no compartments.** KEGG describes reactions, not cell biology, so
every metabolite lands in one undifferentiated space. A KEGG draft cannot
distinguish mitochondrial from cytosolic anything until you localise it;
see [20. Combining and simplifying](combining.md) for the reverse operation, and
what is lost by it.

The flags decide how inclusive the draft is. `keepIncomplete` /
`keep_incomplete` keeps reactions whose KO assignment is only partial;
`keepUndefinedStoich` / `keep_undefined_stoich` keeps reactions with `n` or `x`
in their stoichiometry, which cannot be balanced as written. Turning both off:

```python
strict = get_kegg_model_for_organism_from_artefacts(
    "sce", keep_incomplete=False, keep_undefined_stoich=False)
print(f"{len(strict.reactions)} rxns, {len(strict.genes)} genes "
      f"(from {len(model.reactions)} and {len(model.genes)})")
```

```text
1348 rxns, 827 genes (from 1357 and 838)
```

That is a change of nine reactions on this organism. The size of the effect
depends on the organism, so measure it rather than assuming it. `keepGeneral` /
`keep_general` is off by default for a better reason: general reactions are placeholders like "an alcohol
+ NAD+", and admitting them produces a network that appears to do far more than
it can.

:::{warning} What can go wrong
- **Expecting a model.** No biomass reaction, no exchanges, no compartments,
  no medium. What you have is a reaction inventory with gene associations.
- **Trusting the KO assignment.** A KO is an orthology group, not a
  demonstrated activity in your organism, and a partial HMM hit is weaker
  still.
- **Undefined stoichiometry.** Reactions with `n` or `x` coefficients cannot
  be mass-balanced. They are kept by default because dropping them loses real
  chemistry, but they will trip up
  [9. Quality control](quality-control.md) later.
- **Version drift.** The artefacts are built from a specific KEGG release,
  `kegg118` here. Rebuilding a year later with a different release gives a
  different model, so record which one you used.
:::

## See also

- [12. Reconstruction from homology](homology.md), the same goal from a template
  model instead of an orthology database.
- [17. Gap-filling](gap-filling.md), what to do with 1357 reactions that cannot
  yet carry flux.
- [Legacy tutorial 5](../tutorials/tutorial5.md), the original KEGG
  reconstruction exercise from the RAVEN paper.
