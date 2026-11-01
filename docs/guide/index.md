# Guide

Each page of the guide covers one task, with MATLAB and Python examples side by side. The pages can be read in the order below or one at a time; [Getting started](getting-started.md) is the first.

The [reconstruction protocol](../protocol/index.md) for *H. polymorpha* and the [legacy tutorials](../tutorials/index.md) from the original RAVEN paper are separate from the task pages. Both are MATLAB only.

## Functions from cobrapy

A function that comes from cobrapy carries a {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` badge that links to the cobrapy documentation, and its import line shows where it lives (`from cobra.io import read_sbml_model`). The [function mapping](../matlab-vs-python.md) lists all of these functions.

## Executed examples

The [Guide examples](https://github.com/CompMetEng/raven-docs/actions/workflows/examples.yml) workflow runs the code on the task pages, MATLAB and Python separately. It starts when a guide page, the example data or the runner changes, and once a week against the latest RAVEN and raven-toolbox. A run fails when a block raises an error or prints output that differs from the output shown beneath it. The blocks of a page run in order in one session, so a block uses what the preceding blocks made. Reading a page starts at its Setup section.

Two pages are not executed. [Reconstruction from KEGG](kegg.md) downloads tens of megabytes and takes minutes, and the Human-GEM steps of [Context-specific models with ftINIT](init.md) take hours. Both pages quote the run that their numbers come from. A few further blocks are marked as not run on their own page, with the reason. The protocol and the legacy tutorials are not executed.

## Example data

| File | Content |
|---|---|
| [`smallYeast.yml`](../data/smallYeast.yml) | Central carbon metabolism of yeast; the default example |
| [`smallYeastBad.yml`](../data/smallYeastBad.yml) | The same model with deliberate errors, used on the curation pages |
| [`empty.xml`](../data/empty.xml) | An empty model with compartments, the start of a model built from scratch |
| [`yeast-GEM.yml`](../data/yeast-GEM.yml) | yeast-GEM v9.1.0, the consensus *S. cerevisiae* model, for pages that need a genome-scale model |
| [`yeast-GEM.xml`](../data/yeast-GEM.xml) | yeast-GEM v9.1.0 as SBML |
| [`anaerobic.yml`](../data/anaerobic.yml) | A condition file: yeast-GEM under anaerobic conditions |

## Pages

### Foundations

1. [Getting started](getting-started.md): load a model and inspect it.
2. [Model structure and identifiers](model-structure.md): how the RAVEN struct and `cobra.Model` correspond, field by field.
3. [Reading and writing models](io.md): SBML, RAVEN YAML, Excel and text, and the layout of a model repository.

### Simulation

4. [Simulating growth with FBA](fba.md): objective, bounds, solving and reading the fluxes.
5. [Growth media and conditions](media.md): defining a medium and keeping a condition as data.
6. [Solvers and configuration](solvers.md): selecting a solver and reading what it returns.

### Building and curating

7. [Building a model from scratch](building.md): metabolites, reactions, genes and exchange reactions.
8. [Editing an existing model](editing.md): stoichiometry, gene-reaction rules, bounds and deletions.
9. [Quality control](quality-control.md): structure, mass balance, blocked reactions and mass produced from nothing.
10. [Table-driven curation](curation.md): curation kept as reviewable tables.
11. [Biomass composition and annotation](biomass.md): the composition of the biomass reaction, rescaling it, and the annotation that the model keeps after the solve.

### Reconstruction

12. [Reconstruction from homology](homology.md): aligning a proteome against the genes of a template model, and the effect of the cut-offs.
13. [Reconstruction from KEGG](kegg.md): a draft without a template model, and what such a draft lacks.
14. [Context-specific models with ftINIT](init.md): integrating omics data and extracting a cell-line model from Human-GEM and RNA-seq data.

### Analysis and repair

15. [Metabolic tasks](tasks.md): defining what a model must be able to do and checking that it keeps that ability.
16. [Deletions and essentiality](deletions.md): knockouts, essential genes and reactions, and MOMA.
17. [Gap-filling](gap-filling.md): closing the gaps of a draft model.
18. [Flux variability and alternative optima](fva.md): the range of each flux and the predictions that the model fixes.
19. [Random sampling](sampling.md): the flux distribution behind those ranges and its conditioning on a state.

### Comparing and engineering

20. [Combining and simplifying models](combining.md): merging models on metabolite names and taking a model apart.
21. [Comparing models](comparing.md): the differences between two models and their effect on predictions.
22. [Engineering targets](engineering.md): FSEOF for over-production targets and reporter metabolites for the metabolites around a transcriptional response.

## Protocol and legacy tutorials

| Resource | Content |
|---|---|
| [GEM reconstruction protocol, *H. polymorpha*](../protocol/index.md) | Homology-based reconstruction of `hanpo-GEM`, from the template models to a draft that grows on methanol. MATLAB only; not executed. |
| [Legacy tutorials](../tutorials/index.md) | Five exercises from the original RAVEN paper (Agren et al., 2013), adapted to run with current RAVEN and otherwise unchanged. MATLAB only. |

The task pages are for looking up a single task. The protocol follows one reconstruction in order.

## Compartment localisation

No page covers it. The feature is in development and the two toolboxes differ in it.

```{toctree}
:hidden:
:caption: Start

../installation/index
../yaml-format
../data/README
```

```{toctree}
:hidden:
:caption: Task pages

getting-started
model-structure
io
fba
media
solvers
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
:caption: Legacy

../protocol/index
../tutorials/index
```
