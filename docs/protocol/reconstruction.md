# GEM reconstruction protocol

This protocol is a complete, worked example of reconstructing a genome-scale metabolic model (GEM) from homology, using RAVEN. It follows the published protocol:

> Zorrilla F, Kerkhoven EJ (2022). *Reconstruction of Genome-Scale Metabolic Model for* Hansenula polymorpha *Using RAVEN.* In: *Yeast Metabolic Engineering: Methods and Protocols*, Methods in Molecular Biology vol. 2513, pp. 271–290. <https://doi.org/10.1007/978-1-0716-2399-2_16>

All scripts and data are hosted in the [hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) repository, where `hanpo-GEM` is a short name for the model. The complete, runnable version of every command on these pages is in [`code/reconstructionProtocol.m`](https://github.com/SysBioChalmers/hanpo-GEM/blob/main/code/reconstructionProtocol.m); sections 3.1 to 3.9 of the script correspond to the pages in the order of the stages below, with sections 3.7 and 3.8 on the page Saving to GitHub and simulating. The commands shown in these pages are occasionally more concise than in the script (mainly around file locations).

The original, published protocol was written for RAVEN 2. This site applies minor modifications to the commands shown so the same protocol also works with RAVEN 3.

## Genome-scale metabolic models

Cellular metabolism is a complex network of hundreds to thousands of reactions and metabolites. A GEM is a mathematical description of that network. At its core is the **stoichiometric matrix** (*S*-matrix) of dimensions *M* × *N*, where *M* is the number of metabolites and *N* the number of reactions. Each reaction is bounded by a lower (LB) and upper (UB) bound reflecting thermodynamics and reversibility, and gene–reaction associations are stored in `grRules`.

Constraining the model with measurable rates (such as carbon uptake) allows estimation of all intracellular fluxes by **flux balance analysis (FBA)**, and so prediction of phenotypes. This supports applications from strain engineering to antibiotic discovery and microbial-community analysis.

## The homology-based approach

RAVEN can create a draft GEM for an organism of interest by using well-curated models of phylogenetically related organisms as templates. Whether a given reaction from a template is included in the new model is decided by homology between the protein sequences of the two organisms (determined by bidirectional BLAST).

In this protocol a draft model is reconstructed for the industrially relevant methylotrophic yeast *Hansenula polymorpha* (also known as *Ogataea polymorpha*), which lacks a published high-quality GEM. Two highly curated yeast models are used as templates:

| Template | Organism | Role |
|---|---|---|
| [yeast-GEM](https://github.com/SysBioChalmers/yeast-GEM) | *Saccharomyces cerevisiae* (ascomycete) | Primary template |
| [rhto-GEM](https://github.com/SysBioChalmers/rhto-GEM) | *Rhodotorula toruloides* (basidiomycete) | Complementary template |

:::{admonition} Same identifier namespace
:class: warning

Multiple template models must use the same identifiers for metabolites, reactions and compartments. The yeast-GEM and rhto-GEM models used here share the same identifier style.
:::

## Reconstruction stages

The reconstruction proceeds through these stages, each a page of the protocol:

1. [Materials and installation](materials.md), software, files and verifying RAVEN.
2. [Importing template models](template-models.md), load the yeast-GEM and rhto-GEM templates.
3. [Draft from homology](homology.md), BLAST and `getModelFromHomology`.
4. [Biomass composition](biomass.md), DNA, RNA, protein, carbohydrate and lipid pseudoreactions.
5. [Curation of lipid reactions](lipid-curation.md), the SLIME formalism.
6. [Gap-filling](gap-filling.md), make the draft able to produce biomass.
7. [Saving to GitHub and simulating](simulation.md), version control and FBA.
8. [Manual curation](manual-curation.md), fix gene associations, add methanol metabolism.
