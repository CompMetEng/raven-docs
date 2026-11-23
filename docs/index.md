# RAVEN

<div class="site-hero">
  <div class="site-logo-row">
    <img class="site-logo-light" src="_static/raven-logo.png" alt="RAVEN">
    <img class="site-logo-dark" src="_static/raven-logo-white.png" alt="RAVEN">
    <p class="site-tag">MATLAB &amp; Python</p>
  </div>
  <p class="site-tagline">A toolkit for building, curating, and simulating genome-scale metabolic models, available as the MATLAB toolbox RAVEN and the Python package raven-toolbox, which is built on cobrapy. This site documents both.</p>
</div>

## Installation

::::{tab-set}
:::{tab-item} MATLAB (git)

The clone is the development version. The [tags page](https://github.com/CompMetEng/RAVEN/tags) lists the releases.

```bash
git clone --depth=1 https://github.com/CompMetEng/RAVEN.git
```

Add the folder to the MATLAB path and run `checkRaven`, which reports whether the installation and the solver work.
:::
:::{tab-item} MATLAB (Add-Ons)

The Add-Ons manager installs the latest stable release, RAVEN 2.x. RAVEN 3 is installed from git or from a source archive; see [RAVEN (MATLAB)](installation/raven.md).
:::
:::{tab-item} Python (pip)

```bash
pip install --pre raven-toolbox
```

PyPI also holds the stable release 0.4.0, which `pip` selects unless `--pre` is given. The option `--pre` selects the pre-release that this site documents.
:::
:::{tab-item} Python (git)

The clone is the development version. The [tags page](https://github.com/CompMetEng/raven-toolbox/tags) lists the releases.

```bash
git clone --depth=1 https://github.com/CompMetEng/raven-toolbox.git
pip install -e raven-toolbox/
```
:::
::::

[Installation](installation/index.md) lists the requirements, the solvers and how to verify an installation.

## Key features

::::{grid} 1 2 3 3

:::{grid-item-card} Homology reconstruction
:link: guide/homology
:link-type: doc

Transfers reactions from template models to a new genome, using BLAST+, DIAMOND or HMMER to find the homologous genes.
:::

:::{grid-item-card} KEGG-based reconstruction
:link: guide/kegg
:link-type: doc

Builds a draft network from the KEGG annotation of an organism or from KEGG pathway and reaction entries.
:::

:::{grid-item-card} Flux analysis
:link: guide/fba
:link-type: doc

Runs flux balance analysis (FBA), flux variability analysis (FVA), gene and reaction deletions and flux sampling. The MATLAB toolbox solves with GLPK, Gurobi, SCIP or a COBRA Toolbox solver; raven-toolbox uses the solvers of cobrapy.
:::

:::{grid-item-card} ftINIT
:link: guide/init
:link-type: doc

Extracts a context-specific model from gene expression data. ftINIT is the successor of the legacy tINIT method.
:::

:::{grid-item-card} Gap-filling
:link: guide/gap-filling
:link-type: doc

Adds reactions from a template model so that blocked reactions carry flux, a metabolic task passes or the model grows.
:::

:::{grid-item-card} Model curation
:link: guide/quality-control
:link-type: doc

Checks the structure, the mass and charge balance, the connectivity and the metabolic tasks of a model.
:::

::::

## Quick start

The example loads yeast-GEM from [`yeast-GEM.yml`](data/yeast-GEM.yml), sets growth as the objective, limits glucose uptake to 1 mmol/gDW/h and runs FBA. The commands run in the folder that contains the file.

::::{tab-set}
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
print(f"Growth rate: {sol.objective_value:.4f} h-1")
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

The help of every MATLAB function and every Python function, generated from the source.
:::

:::{grid-item-card} Installation
:link: installation/index
:link-type: doc

The requirements, installation, upgrade and removal of RAVEN and raven-toolbox, and the choice of a solver.
:::

:::{grid-item-card} MATLAB and Python
:link: matlab-vs-python
:link-type: doc

The pairing of each RAVEN function with its raven-toolbox function or its cobrapy equivalent.
:::

:::{grid-item-card} Migration
:link: migrate
:link-type: doc

What changes from RAVEN 2 to RAVEN 3, and from the MATLAB toolbox to the Python package.
:::

:::{grid-item-card} Comparison of RAVEN and raven-toolbox
:link: raven3-vs-raven-toolbox
:link-type: doc

The features that exist in one implementation alone, and the functions that return a different result in each.
:::

:::{grid-item-card} Release notes
:link: release-notes/index
:link-type: doc

The changes of each release of RAVEN and raven-toolbox.
:::

::::

## Help

::::{grid} 1 2 2 2

:::{grid-item-card} {octicon}`bug` Report a bug or request a feature
Open an issue in the repository of the implementation that it concerns.

- [RAVEN (MATLAB) issues](https://github.com/CompMetEng/RAVEN/issues)
- [raven-toolbox (Python) issues](https://github.com/CompMetEng/raven-toolbox/issues)
:::

:::{grid-item-card} {octicon}`comment-discussion` Ask a usage question
Start a discussion in the repository of the implementation that it concerns.

- [RAVEN (MATLAB) discussions](https://github.com/CompMetEng/RAVEN/discussions)
- [raven-toolbox (Python) discussions](https://github.com/CompMetEng/raven-toolbox/discussions)
:::

::::

```{toctree}
:hidden:

installation/index
guide/index
api/index
migrate
references
parameter-tuning/index
release-notes/index
maintenance
```
