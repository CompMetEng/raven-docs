<!-- run-examples: skip-file -->

# Reconstruction from KEGG

[Reconstruction from homology](homology.md) needs a template model of a related organism. KEGG needs none, because its orthology groups (KOs) are linked to reactions, and annotating a genome with KOs gives a draft directly. The method depends on whether the organism is in KEGG.

The documentation build does not run these examples. A KEGG reconstruction downloads tens of megabytes and takes minutes. The Python numbers come from raven-toolbox 3.0.0b1 with the `kegg118` artefacts.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getKEGGModelForOrganism` | `get_kegg_model_for_organism_from_artefacts` | draft from the KEGG annotation of an organism |
| `getKEGGModelForOrganism` (with `fastaFile`) | `get_kegg_model_from_sequences_with_artefacts` | draft from an HMM search of the query proteins |
| `getModelFromKEGG` | `build_reference_model` | assemble and cache the global KEGG model |
| `getPhylDist` | `PhylDist` | phylogenetic distance between KEGG organisms; MATLAB uses it to select the genes of one domain |

## Organisms in KEGG

When KEGG has the species (`sce` for *S. cerevisiae*), the assignments of genes to KOs exist and no sequence search is needed. This method is faster, and it applies when the organism is in KEGG.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = getKEGGModelForOrganism('sce', ...
    'dataDir', fullfile(tempdir, 'kegg118_eukaryotes'));
```

Without a `fastaFile`, the reconstruction runs from the organism abbreviation alone. No sequence search takes place, and the HMM library is not fetched, because the download takes place when a FASTA file is supplied. The reconstruction needs the global KEGG model, which `getModelFromKEGG` supplies. On first use there is no `keggModel.mat` to load. The function downloads the published artefacts (the reference model without genes and the tables of KOs, reactions and organism genes), assembles them and caches the result. The first build takes a while and needs a few hundred MB of disk, and later calls load the cached file.

This method does not read `dataDir`, `cutOff`, `minScoreRatioKO`, `minScoreRatioG` and `outDir`, which apply to a sequence search. `maxPhylDist` applies to this method, with the organism identifier `eukaryotes` or `prokaryotes`: `-1` keeps the genes of that domain, and any other value keeps the genes of every organism. The settings `keepSpontaneous`, `keepUndefinedStoich`, `keepIncomplete` and `keepGeneral` apply.
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

The artefacts (a reference model and three tables, about 49 MB) are fetched from the `kegg118` release of `toolbox-assets` on first use and cached. [Download data and binaries](../installation/data-and-binaries.md) gives the location and describes how to fetch them before a batch run. The first run takes a few minutes, and later runs take about as long, because assembling the draft from the tables is slow and the download is not.
:::
::::

## Organisms absent from KEGG

For an organism that is not in KEGG, the KO assignments are made from sequence. Both toolboxes search the proteins of the organism against a library of profile HMMs, one per KO, trained on prokaryotic or on eukaryotic sequences.

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

hanpo_model = get_kegg_model_from_sequences_with_artefacts("hanpo.faa", domain="eukaryotes")
```
:::
::::

This method is expensive. The eukaryotic HMM library is 135 MB compressed. One timed `hmmsearch` of a proteome (*S. cerevisiae*, 6021 sequences) against the eukaryotic library (2698 profiles) took 89.7 s on 16 threads and 88.6 s on 12 threads (AMD EPYC 9354). The method also needs HMMER, which is not available as a bundle for every platform, and [Download data and binaries](../installation/data-and-binaries.md) has the matrix. Without `threads`, `run_hmmsearch`, `get_kegg_model_from_sequences`, `build_ko_hmm` and `build_hmm_library` use every CPU that the process can run on. `getKEGGModelForOrganism` runs `hmmsearch` on the cores assigned to MATLAB (`feature('numcores')`) and has no `threads` option.

With a `fastaFile`, the organism identifier names the model. The search uses no phylogenetic distance and ignores `maxPhylDist`.

Three cut-offs shape the assignment. `cutOff` is the HMMER significance that a hit needs. `minScoreRatioKO` removes genes that fit a KO worse than the best gene of that KO, and `minScoreRatioG` removes KOs that fit a gene worse than the best KO of that gene. The two prune the same matrix from opposite sides. [KEGG HMM cut-off calibration](../parameter-tuning/studies/kegg-hmm-cutoff-calibration.md) measured all three, and `cutOff` and `minScoreRatioG` differ from the RAVEN 2 values. At `minScoreRatioG` 0.8 and `cutOff` 1e-50, raising `minScoreRatioKO` from 0.0 to 0.5 raised the precision by 0.00 to 0.03 and lowered the recall by 0.00 to 0.01. The default keeps the RAVEN 2 value of 0.3.

## Contents of a KEGG draft

A KEGG draft has the size of a genome-scale model, and it differs from a working model in every other respect.

```text title="the sce draft, measured"
reactions:     1357
metabolites:   1502
genes:          838
compartments:  1 (everything is in 's')
exchange rxns:   0
objective:       none
```

The draft has no compartments. KEGG describes reactions, so every metabolite is in one undifferentiated space. A KEGG draft cannot distinguish mitochondrial and cytosolic reactions until it is localised. [Combining and simplifying models](combining.md) covers the reverse operation and what it discards.

The flags decide how inclusive the draft is. `keepIncomplete` / `keep_incomplete` keeps reactions that KEGG labels incomplete, erroneous or unclear. `keepUndefinedStoich` / `keep_undefined_stoich` keeps reactions with `n` or `x` in the stoichiometry, which cannot be balanced as written. With both turned off:

```python
strict = get_kegg_model_for_organism_from_artefacts(
    "sce", keep_incomplete=False, keep_undefined_stoich=False)
print(f"{len(strict.reactions)} rxns, {len(strict.genes)} genes "
      f"(from {len(model.reactions)} and {len(model.genes)})")
```

```text
1348 rxns, 827 genes (from 1357 and 838)
```

This removes nine reactions from this organism, and the effect differs between organisms and should be measured for each. `keepGeneral` / `keep_general` is off by default, unlike the other flags. General reactions are placeholders such as "an alcohol + NAD+", and admitting them produces a network that appears to do more than it can.

:::{admonition} Troubleshooting
:class: warning

- The draft is expected to be a model. It has no biomass reaction, no exchange reactions, no compartments and no medium. It is an inventory of reactions with gene associations.
- The KO assignment is trusted. A KO is an orthology group, which does not demonstrate an activity in the organism, and a partial HMM hit is weaker.
- The stoichiometry is undefined. Reactions with `n` or `x` coefficients cannot be mass-balanced. They are kept by default because removing them removes real chemistry, and they affect [Quality control](quality-control.md).
- The KEGG release changes. The artefacts are built from one KEGG release, `kegg118` here. A rebuild with another release gives a different model, so the release should be recorded.
:::

## See also

- [Reconstruction from homology](homology.md): the same goal with a template model in place of an orthology database.
- [Gap-filling](gap-filling.md): the step for the 1357 reactions of a draft without exchange reactions, none of which can carry flux.
- [Legacy tutorial 5](../tutorials/tutorial5.md): the original KEGG reconstruction exercise from the RAVEN paper.
