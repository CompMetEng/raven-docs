# GEM reconstruction protocol

The protocol is a complete, worked example of the reconstruction of a genome-scale metabolic model (GEM) from homology with RAVEN. It follows the published protocol:

> Zorrilla F, Kerkhoven EJ (2022). *Reconstruction of Genome-Scale Metabolic Model for* Hansenula polymorpha *Using RAVEN.* In: *Yeast Metabolic Engineering: Methods and Protocols*, Methods in Molecular Biology vol. 2513, pp. 271–290. <https://doi.org/10.1007/978-1-0716-2399-2_16>

All scripts and data are in the [hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) repository, where `hanpo-GEM` is the short name of the model. [`code/reconstructionProtocol.m`](https://github.com/SysBioChalmers/hanpo-GEM/blob/main/code/reconstructionProtocol.m) holds the complete, runnable version of every command on these pages. Its sections 3.1 to 3.9 correspond to the pages in the order of the stages below, and sections 3.7 and 3.8 correspond to the page Saving to GitHub and simulating. The commands on these pages are in places more concise than in the script, mainly in the file locations.

The published protocol was written for RAVEN 2. This site applies minor modifications to the commands, and the protocol also works with RAVEN 3.

## Genome-scale metabolic models

Cellular metabolism is a network of hundreds to thousands of reactions and metabolites, and a GEM is a mathematical description of that network. Its core is the stoichiometric matrix (*S*-matrix) of dimensions *M* × *N*, where *M* is the number of metabolites and *N* the number of reactions. Each reaction has a lower (LB) and an upper (UB) bound that reflect thermodynamics and reversibility, and the gene–reaction associations are stored in `grRules`.

Measurable rates, such as the carbon uptake, constrain the model. Flux balance analysis (FBA) then estimates all intracellular fluxes and predicts phenotypes. This supports applications from strain engineering to antibiotic discovery and the analysis of microbial communities.

## The homology-based approach

RAVEN creates a draft GEM for an organism with well-curated models of phylogenetically related organisms as templates. The homology between the protein sequences of the two organisms, determined by bidirectional BLAST, decides whether a reaction of a template is included in the new model.

The protocol reconstructs a draft model for the industrially relevant methylotrophic yeast *Hansenula polymorpha* (also named *Ogataea polymorpha*), which has no published high-quality GEM. Two highly curated yeast models are the templates:

| Template | Organism | Role |
|---|---|---|
| [yeast-GEM](https://github.com/SysBioChalmers/yeast-GEM) | *Saccharomyces cerevisiae* (ascomycete) | primary template |
| [rhto-GEM](https://github.com/SysBioChalmers/rhto-GEM) | *Rhodotorula toruloides* (basidiomycete) | complementary template |

:::{admonition} Same identifier namespace
:class: warning

Multiple template models must use the same identifiers for metabolites, reactions and compartments. The yeast-GEM and rhto-GEM models used here share the identifier style.
:::

## Reconstruction stages

Each stage is a page of the protocol:

1. [Materials and installation](materials.md): software, files and verification of RAVEN.
2. [Importing template models](template-models.md): loading the yeast-GEM and rhto-GEM templates.
3. [Draft from homology](homology.md): BLAST and `getModelFromHomology`.
4. [Biomass composition](biomass.md): the pseudoreactions for DNA, RNA, protein, carbohydrate and lipid.
5. [Curation of lipid reactions](lipid-curation.md): the SLIME formalism.
6. [Gap-filling](gap-filling.md): making the draft able to produce biomass.
7. [Saving to GitHub and simulating](simulation.md): version control and FBA.
8. [Manual curation](manual-curation.md): correcting gene associations and adding methanol metabolism.
