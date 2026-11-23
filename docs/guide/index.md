# Guide

Each page of the guide covers one task, with MATLAB and Python examples side by side. The pages can be read in the order below or one at a time; [Getting started](getting-started.md) is the first. [Functions from cobrapy](cobrapy.md) explains the badge on functions that come from cobrapy, and [Executed examples](executed-examples.md) describes how the examples are checked.

## Pages

### Foundations

1. [Getting started](getting-started.md): load a model and inspect it.
2. [Model structure and identifiers](model-structure.md): how the RAVEN struct and `cobra.Model` correspond, field by field.
3. [Reading and writing models](io.md): SBML, RAVEN YAML, Excel and text, and the layout of a model repository.

### Simulation

4. [Simulating growth with FBA](fba.md): objective, bounds, solving and reading the fluxes.
5. [Growth media and conditions](media.md): defining a medium and keeping a condition as data.
6. [Solvers and configuration](solvers.md): selecting a solver and reading what it returns.
7. [Comparing a model with measured conditions](experiments.md): measured growth rates and fluxes, one condition applied to a model, and the distance between a simulation and the data.

### Building and curating

8. [Building a model from scratch](building.md): metabolites, reactions, genes and exchange reactions.
9. [Editing an existing model](editing.md): stoichiometry, gene-reaction rules, bounds and deletions.
10. [Quality control](quality-control.md): structure, mass balance, blocked reactions and mass produced from nothing.
11. [Table-driven curation](curation.md): curation kept as reviewable tables.
12. [Biomass composition and annotation](biomass.md): the composition of the biomass reaction, rescaling it, and the annotation that the model keeps after the solve.

### Reconstruction

13. [Reconstruction from homology](homology.md): aligning a proteome against the genes of a template model, and the effect of the cut-offs.
14. [Reconstruction from KEGG](kegg.md): a draft without a template model, and what such a draft lacks.
15. [Context-specific models with ftINIT](init.md): integrating omics data and extracting a cell-line model from Human-GEM and RNA-seq data.

### Analysis and repair

16. [Metabolic tasks](tasks.md): defining what a model must be able to do and checking that it keeps that ability.
17. [Deletions and essentiality](deletions.md): knockouts, essential genes and reactions, and MOMA.
18. [Gap-filling](gap-filling.md): closing the gaps of a draft model.
19. [Flux variability and alternative optima](fva.md): the range of each flux and the predictions that the model fixes.
20. [Random sampling](sampling.md): the flux distribution behind those ranges and its conditioning on a state.

### Comparing and engineering

21. [Combining and simplifying models](combining.md): merging models on metabolite names and taking a model apart.
22. [Comparing models](comparing.md): the differences between two models and their effect on predictions.
23. [Engineering targets](engineering.md): FSEOF for over-production targets and reporter metabolites for the metabolites around a transcriptional response.

## Example data

| File | Content |
|---|---|
| [`smallYeast.yml`](../data/smallYeast.yml) | Central carbon metabolism of yeast; the default example |
| [`smallYeastBad.yml`](../data/smallYeastBad.yml) | The same model with deliberate errors, used on the curation pages |
| [`empty.xml`](../data/empty.xml) | A starter model with four metabolites and one reaction, the start of a model built from scratch |
| [`yeast-GEM.yml`](../data/yeast-GEM.yml) | yeast-GEM v9.1.0, the consensus *S. cerevisiae* model, for pages that need a genome-scale model |
| [`yeast-GEM.xml`](../data/yeast-GEM.xml) | yeast-GEM v9.1.0 as SBML |
| [`anaerobic.yml`](../data/anaerobic.yml) | A condition file: yeast-GEM under anaerobic conditions |
| [`fluxData.tsv`](../data/fluxData.tsv) | Three conditions with a measured growth rate and exchange fluxes, for yeast-GEM |
| [`zeroFlux.tsv`](../data/zeroFlux.tsv) | The reactions that carry no flux in those conditions |

## Protocol and legacy tutorials

| Resource | Content |
|---|---|
| [GEM reconstruction protocol, *H. polymorpha*](../protocol/index.md) | Homology-based reconstruction of `hanpo-GEM`, from the template models to a draft that grows on methanol. MATLAB; not executed. |
| [Legacy tutorials](../tutorials/index.md) | Five exercises from the original RAVEN paper (Agren et al., 2013), adapted to run with current RAVEN and otherwise unchanged. MATLAB. |

The task pages are for looking up a single task. The protocol follows one reconstruction in order.

```{toctree}
:hidden:
:caption: Task pages

getting-started
model-structure
io
fba
media
solvers
experiments
building
editing
quality-control
curation
biomass
homology
kegg
init
tasks
deletions
gap-filling
fva
sampling
combining
comparing
engineering
```

```{toctree}
:hidden:
:caption: Background

../yaml-format
../data/README
cobrapy
executed-examples
```

```{toctree}
:hidden:
:caption: Legacy

../protocol/index
../tutorials/index
```
