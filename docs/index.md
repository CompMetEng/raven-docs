# RAVEN

<div class="site-hero">
  <div class="site-logo-row">
    <img class="site-logo-light" src="_static/raven-logo.png" alt="RAVEN">
    <img class="site-logo-dark" src="_static/raven-logo-white.png" alt="RAVEN">
    <p class="site-tag">MATLAB &amp; Python</p>
  </div>
  <p class="site-tagline">A toolkit for building, curating, and simulating genome-scale metabolic models, available as a MATLAB toolbox and a Python package built on cobrapy.</p>
</div>

## Installation

::::{tab-set}
:::{tab-item} Python (pip)

```bash
pip install --pre raven-toolbox
```
:::
:::{tab-item} Python (git)

```bash
git clone --depth=1 https://github.com/CompMetEng/raven-toolbox.git
pip install -e raven-toolbox/
```
:::
:::{tab-item} MATLAB (git)

```bash
git clone --depth=1 https://github.com/CompMetEng/RAVEN.git
```

Add the folder to the MATLAB path and run `checkRaven`, which reports whether the installation and the solver work.
:::
:::{tab-item} MATLAB (Add-Ons)

The Add-Ons manager installs the latest stable release, RAVEN 2.x. RAVEN 3.0.0b2, which this site documents, is installed from git or from a source archive; see [RAVEN (MATLAB)](installation/raven.md).
:::
::::

## Features

::::{grid} 1 2 3 3

:::{grid-item-card} Homology reconstruction
Transfers reactions from template models to a new genome, using BLAST+, DIAMOND or HMMER to find the homologous genes.
:::

:::{grid-item-card} KEGG-based reconstruction
Builds a draft network from the KEGG annotation of an organism or from KEGG pathway and reaction entries.
:::

:::{grid-item-card} Flux analysis
Runs flux balance analysis (FBA), flux variability analysis (FVA), gene and reaction deletions and flux sampling. The MATLAB toolbox solves with GLPK, Gurobi, SCIP or a COBRA Toolbox solver; raven-toolbox uses the solvers of cobrapy.
:::

:::{grid-item-card} ftINIT
Extracts a context-specific model from gene expression data. ftINIT is the successor of the legacy tINIT method.
:::

:::{grid-item-card} Gap-filling
Adds reactions from a template model so that blocked reactions carry flux, a metabolic task passes or the model grows.
:::

:::{grid-item-card} Model curation
Checks the structure, the mass and charge balance, the connectivity and the metabolic tasks of a model.
:::

::::

## Quick start

The example loads yeast-GEM, sets growth as the objective, limits glucose uptake to 1 mmol/gDW/h and runs FBA.

::::{tab-set}
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

# read_yaml_model returns a cobra.Model
model = read_yaml_model("yeast-GEM.yml")

model.objective = "r_2111"
model.reactions.get_by_id("r_1714").lower_bound = -1.0

# optimize is the cobrapy method
sol = model.optimize()
print(f"Growth rate: {sol.objective_value:.4f} h⁻¹")
```
:::
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('yeast-GEM.yml');

model = setParam(model, 'obj', 'r_2111', 1);
model = setParam(model, 'lb', 'r_1714', -1);

sol = solveLP(model);
fprintf('Growth rate: %.4f h-1\n', sol.f);
```
:::
::::

## Documentation

::::{grid} 1 2 2 2

:::{grid-item-card} Guide
:link: guide/index
:link-type: doc

One page per task, with MATLAB and Python examples side by side. Most examples are executed, and their output is checked against the text.
:::

:::{grid-item-card} API reference
:link: api/index
:link-type: doc

Reference of the MATLAB functions and the Python functions.
:::

:::{grid-item-card} Installation
:link: installation/index
:link-type: doc

Installation of RAVEN or raven-toolbox, and the choice of a solver.
:::

:::{grid-item-card} Comparison of RAVEN and raven-toolbox
:link: raven3-vs-raven-toolbox
:link-type: doc

The features that exist in one implementation alone, and the functions that return a different result in each.
:::

::::

## Citing RAVEN

Cite the following publication when using RAVEN in research:

> Wang H, Marcišauskas S, Sánchez BJ, Domenzain I, Hermansson D, Agren R,
> Nielsen J, Kerkhoven EJ (2018). **RAVEN 2.0: A versatile toolbox for
> metabolic network reconstruction and a case study on *Streptomyces
> coelicolor*.** PLoS Computational Biology 14(10): e1006541.
> <https://doi.org/10.1371/journal.pcbi.1006541>

[Citations](references.md) lists further publications, among them the first RAVEN paper (2013) and the protocol for genome-scale model reconstruction.

## Source code

RAVEN is released under the GPLv3 licence at [CompMetEng/RAVEN](https://github.com/CompMetEng/RAVEN){.github}, archived at [https://doi.org/10.5281/zenodo.3689518](https://doi.org/10.5281/zenodo.3689518). raven-toolbox, the Python port, is released under the MIT licence at [CompMetEng/raven-toolbox](https://github.com/CompMetEng/raven-toolbox){.github}.

## Issues and discussions

Bug reports and feature requests go to the issue tracker of the toolbox concerned: [RAVEN issues](https://github.com/CompMetEng/RAVEN/issues){.github} for the MATLAB toolbox, [raven-toolbox issues](https://github.com/CompMetEng/raven-toolbox/issues){.github} for the Python package. Questions go to [RAVEN discussions](https://github.com/CompMetEng/RAVEN/discussions){.github} or [raven-toolbox discussions](https://github.com/CompMetEng/raven-toolbox/discussions){.github}.

```{toctree}
:hidden:

migrate
guide/index
api/index
parameter-tuning/index
references
```
