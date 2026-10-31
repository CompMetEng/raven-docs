# Guide

Short, task-focused pages: one job per page, three to eight functions, in
**MATLAB and Python side by side**. Start at
[Getting started](getting-started.md) and read on, or jump to whichever task you
are working on.

Two older sets of material appear at the end of this section: a complete
[reconstruction protocol](../protocol/index.md) for *H. polymorpha*, followed
start to finish, and the [hands-on tutorials](../tutorials/index.md) from the
original RAVEN paper. Both are MATLAB only.

:::{admonition} cobrapy
:class: info
Functions that come from cobrapy rather than raven-toolbox carry a
{bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` badge, their import line shows where
they live (`from cobra.io import read_sbml_model`), and the badge links to
the cobrapy documentation. The
[function mapping](../matlab-vs-python.md) lists every such function.
:::

:::{admonition} Executed examples
:class: info
The code on the numbered pages is run, MATLAB and Python separately, by the
[Guide examples](https://github.com/CompMetEng/raven-docs/actions/workflows/examples.yml)
workflow whenever a guide page, the example data or the runner changes, and once
a week against the latest RAVEN and raven-toolbox. A run fails when a block errors
or prints something other than the output shown beneath it. The blocks on a page
run in order in one session, so later blocks use what earlier ones made: start
from the page's *Setup*.

Not executed: [13. Reconstruction from KEGG](kegg.md), which downloads tens of
megabytes and takes minutes, and the Human-GEM steps of
[14. Context-specific models](init.md), which take hours. A few other blocks are
marked on their page as not run, with the reason. Both pages quote the run their
numbers came from. The protocol and the hands-on tutorials at the end of this
section are MATLAB-only and are not executed.
:::

## Example data

| File | What it is |
|---|---|
| [`smallYeast.yml`](../data/smallYeast.yml) | central carbon metabolism in yeast; the default example |
| [`smallYeastBad.yml`](../data/smallYeastBad.yml) | the same model with deliberate errors, for the curation pages |
| [`empty.xml`](../data/empty.xml) | an empty model with compartments, for building one from scratch |
| [`yeast-GEM.yml`](../data/yeast-GEM.yml) | yeast-GEM v9.1.0, the consensus *S. cerevisiae* model, for pages that need a genome-scale one |
| [`yeast-GEM.xml`](../data/yeast-GEM.xml) | the same model as SBML |
| [`anaerobic.yml`](../data/anaerobic.yml) | a condition file: yeast-GEM under anaerobic conditions |

## Pages

**Foundations**

1. [Getting started](getting-started.md), load a model and inspect it.
2. [Model structure and identifiers](model-structure.md), how the RAVEN struct
   and `cobra.Model` correspond, field by field.
3. [Reading and writing models](io.md), SBML, RAVEN YAML, Excel, text, and the
   layout a model repository expects.

**Simulation**

4. [Simulating growth with FBA](fba.md), objective, bounds, solve, read the
   fluxes.
5. [Growth media and conditions](media.md), define a medium, keep a condition as
   data.
6. [Solvers and configuration](solvers.md), which solver, and how to read what
   it returns.

**Building and curating**

7. [Building a model from scratch](building.md), metabolites, reactions, genes,
   exchanges.
8. [Editing an existing model](editing.md), stoichiometry, GPRs, bounds,
   deletions.
9. [Quality control](quality-control.md), structure, mass balance, blocked
   reactions, mass from nothing.
10. [Table-driven curation](curation.md), applying curation as reviewable
    tables rather than a script of function calls.
11. [Biomass composition and annotation](biomass.md), what the cell is made
    of, rescaling it, and the annotation that stays useful after the solve.

**Reconstruction**

12. [Reconstruction from homology](homology.md), BLAST a proteome against a
    template model's genes, and what the cut-offs decide for you.
13. [Reconstruction from KEGG](kegg.md), a draft with no template model at all,
    and what such a draft is missing.
14. [Context-specific models (ftINIT)](init.md), omics integration and
    extracting a cell-line
    model from Human-GEM and RNA-seq, end to end.

**Analysis and repair**

15. [Metabolic tasks](tasks.md), saying what a model must be able to do, and
    checking that it still can.
16. [Deletions and essentiality](deletions.md), knockouts, essential genes and
    reactions, MOMA.
17. [Gap-filling](gap-filling.md), closing the holes a draft model has.
18. [Flux variability](fva.md), how much each flux can still move, and
    which predictions the model has no choice about.
19. [Random sampling](sampling.md), the distribution behind those ranges, and
    how to condition it on a particular state.

**Comparing and engineering**

20. [Combining and simplifying models](combining.md), merging models on
    metabolite names, and taking one apart again.
21. [Comparing models](comparing.md), what changed between two models, and what
    effect that difference has.
22. [Engineering targets](engineering.md), FSEOF for over-production targets
    and reporter metabolites for the metabolites a transcriptional response
    surrounds.

## Also in this section

| | |
|---|---|
| [GEM reconstruction protocol, *H. polymorpha*](../protocol/index.md) | homology-based reconstruction of `hanpo-GEM`, end to end, from template models to a growing methylotrophic draft. A published pipeline followed from start to finish. MATLAB only, not executed here. |
| [Hands-on tutorials](../tutorials/index.md) | five exercises from the original RAVEN paper (Agren et al., 2013), updated to run with current RAVEN but otherwise unchanged. MATLAB only. |

Use the numbered pages to look something up; use the protocol to see a whole
reconstruction in order.

**Not yet written**: compartment localisation, which is still in development and
not yet at parity between the two toolboxes.

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
