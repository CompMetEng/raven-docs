<!-- run-examples: skip-file -->

# Reconstruction from KEGG

[Reconstruction from homology](homology.md) needs a template model of a related organism. KEGG needs none: its orthology groups (KOs) are already linked to reactions, so annotating a genome with KOs gives a draft directly. Which method applies depends on one thing: whether the organism is already in KEGG.

The documentation build does not run these examples. A KEGG reconstruction downloads tens of megabytes and takes minutes, so the page is not executed with the others. The Python numbers come from raven-toolbox 3.0.0b1 with the `kegg118` artefacts (about 2.5 minutes per call on a recent workstation, with or without the cache).

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getKEGGModelForOrganism` | `get_kegg_model_for_organism_from_artefacts` | draft from an organism's KEGG annotation |
| `getKEGGModelForOrganism` (with `fastaFile`) | `get_kegg_model_from_sequences_with_artefacts` | draft from an HMM search of the query proteins |
| `getModelFromKEGG` | `build_reference_model` | assemble and cache the global KEGG model |
| `getPhylDist` | `PhylDist` | phylogenetic distance between KEGG organisms; MATLAB uses it to select one domain's genes |

## Organisms in KEGG

If KEGG has the species (`sce` for *S. cerevisiae*), its gene-to-KO assignments are already made, and no sequence search is needed. This method is the faster one, and the one to prefer when it applies.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = getKEGGModelForOrganism('sce', ...
    'dataDir', fullfile(tempdir, 'kegg118_eukaryotes'));
```

Without a `fastaFile`, the reconstruction runs from the organism abbreviation alone and no sequence search happens, so the HMM library is not fetched; the download is guarded on a FASTA being supplied. The reconstruction needs the global KEGG model, which `getModelFromKEGG` supplies. On first use there is no `keggModel.mat` to load, so it downloads the published artefacts, the gene-free reference model plus the KO, reaction and organism-gene tables, assembles them, and caches the result. That first build takes a while and needs a few hundred MB of disk; later calls load the cached file directly.

This method does not read `dataDir`, `cutOff`, `minScoreRatioKO`, `minScoreRatioG` and `outDir`, which apply only to a sequence search. `maxPhylDist` applies only here, with the organism id `eukaryotes` or `prokaryotes`: `-1` keeps the genes of that domain, and any other value keeps the genes of every organism. The settings `keepSpontaneous`, `keepUndefinedStoich`, `keepIncomplete` and `keepGeneral` apply.
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

The artefacts (a reference model and three tables, about 47 MB) are fetched from the `kegg118` raven-data release on first use and cached; see [Download data and binaries](../installation/data-and-binaries.md) for where, and how to fetch them ahead of a batch run. The first run takes a few minutes and later runs take much the same time, because assembling the draft from the tables is the slow part and the download is not.
:::
::::

## Organisms absent from KEGG

For an organism KEGG has never seen, the KO assignments have to be made from sequence. Both toolboxes search the organism's proteins against a library of profile HMMs, one per KO, trained on either prokaryotic or eukaryotic sequences.

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
from raven_toolbox.reconstruction.kegg import (
    get_kegg_model_from_sequences_with_artefacts,
)

model = get_kegg_model_from_sequences_with_artefacts("hanpo.faa", domain="eukaryotes")
```
:::
::::

This method is expensive. The eukaryotic HMM library alone is 129 MB compressed, and one `hmmsearch` of a full proteome against all KO profiles takes tens of minutes to hours. It also needs HMMER, which has no bundle for every platform; [Download data and binaries](../installation/data-and-binaries.md) has the matrix. Without `threads`, `run_hmmsearch`, `get_kegg_model_from_sequences`, `build_ko_hmm` and `build_hmm_library` use every CPU the process may run on; `getKEGGModelForOrganism` runs `hmmsearch` on the cores assigned to MATLAB (`feature('numcores')`) and has no `threads` option.

With a `fastaFile`, the organism id only names the model; the search uses no phylogenetic distance and ignores `maxPhylDist`.

Three cut-offs shape the assignment. `cutOff` is the HMMER significance a hit needs at all. `minScoreRatioKO` drops genes that fit a KO far worse than the best gene in it, and `minScoreRatioG` drops KOs that fit a gene far worse than that gene's best KO; the two prune the same matrix from opposite sides. All three were measured in the [KEGG HMM cut-off study](../parameter-tuning/studies/kegg-hmm-cutoff-calibration.md); `cutOff` and `minScoreRatioG` changed from the RAVEN 2 values, while `minScoreRatioKO` proved inert and keeps its original value.

## Contents of a KEGG draft

A KEGG draft is genome-scale in size and differs from a working model in every other respect.

```text title="the sce draft, measured"
reactions:     1357
metabolites:   1502
genes:          838
compartments:  1 (everything is in 's')
exchange rxns:   0
objective:       none
```

There are no compartments. KEGG describes reactions and not cell biology, so every metabolite is placed in one undifferentiated space. A KEGG draft cannot distinguish mitochondrial from cytosolic anything until it is localised; [Combining and simplifying](combining.md) covers the reverse operation and what is lost by it.

The flags decide how inclusive the draft is. `keepIncomplete` / `keep_incomplete` keeps reactions that KEGG labels incomplete, erroneous or unclear; `keepUndefinedStoich` / `keep_undefined_stoich` keeps reactions with `n` or `x` in their stoichiometry, which cannot be balanced as written. With both turned off:

```python
strict = get_kegg_model_for_organism_from_artefacts(
    "sce", keep_incomplete=False, keep_undefined_stoich=False)
print(f"{len(strict.reactions)} rxns, {len(strict.genes)} genes "
      f"(from {len(model.reactions)} and {len(model.genes)})")
```

```text
1348 rxns, 827 genes (from 1357 and 838)
```

That is a change of nine reactions on this organism. The size of the effect differs per organism. Measure it for each organism. Unlike the other flags, `keepGeneral` / `keep_general` is off by default: general reactions are placeholders like "an alcohol + NAD+", and admitting them produces a network that appears to do far more than it can.

:::{warning} Troubleshooting
- Expecting a model. No biomass reaction, no exchanges, no compartments, no medium. The draft is a reaction inventory with gene associations.
- Trusting the KO assignment. A KO is an orthology group and not a demonstrated activity in the organism, and a partial HMM hit is weaker still.
- Undefined stoichiometry. Reactions with `n` or `x` coefficients cannot be mass-balanced. They are kept by default because dropping them removes real chemistry, but they interfere with [Quality control](quality-control.md) later.
- Version drift. The artefacts are built from a specific KEGG release, `kegg118` here. Rebuilding a year later with a different release gives a different model, so record the release used.
:::

## See also

- [Reconstruction from homology](homology.md), the same goal with a template model in place of an orthology database.
- [Gap-filling](gap-filling.md), what to do with 1357 reactions that cannot carry flux until the draft has exchange reactions.
- [Legacy tutorial 5](../tutorials/tutorial5.md), the original KEGG reconstruction exercise from the RAVEN paper.
