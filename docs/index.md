# RAVEN

<div class="site-hero">
  <div class="site-logo-row">
    <img class="site-logo-light" src="_static/raven-logo.png" alt="RAVEN">
    <img class="site-logo-dark" src="_static/raven-logo-white.png" alt="RAVEN">
    <p class="site-tag">MATLAB &amp; Python</p>
  </div>
  <p class="site-tagline">A toolkit for building, curating, and simulating genome-scale metabolic models, available as a MATLAB toolbox and a Python package built on cobrapy.</p>
</div>

## Install

::::{tab-set}
:::{tab-item} Python (pip)

```bash
pip install --pre raven-toolbox
```
:::
:::{tab-item} MATLAB (Add-Ons)

Home → Add-Ons → Get Add-Ons → search "RAVEN Toolbox".

Then run `checkRaven` to verify.
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

Add the folder to the MATLAB path, then run `checkRaven` to verify.
:::
::::

## Key features

::::{grid} 1 2 3 3

:::{grid-item-card} Homology reconstruction
Build draft models by transferring reactions from template models using
BLAST+, DIAMOND, or HMMER.
:::

:::{grid-item-card} KEGG-based reconstruction
Reconstruct metabolic networks directly from KEGG organism annotations and
pathway databases.
:::

:::{grid-item-card} Flux analysis
FBA, FVA, gene knockouts, and flux sampling with Gurobi or GLPK solvers.
:::

:::{grid-item-card} ftINIT
Fast task-and-data-driven INIT for extracting context-specific models from
transcriptomics data.
:::

:::{grid-item-card} Gap-filling
Identify and fill stoichiometric gaps by LP to restore connectivity or
enable predicted growth.
:::

:::{grid-item-card} Model curation
Check mass and charge balance, dead-end metabolites, and metabolic task
fulfilment.
:::

::::

## Quick start

::::{tab-set}
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

# load yeast-GEM from RAVEN YAML -- returns a plain cobra.Model
model = read_yaml_model("yeast-GEM.yml")

# set growth as the objective
model.objective = "r_2111"

# constrain glucose uptake to 1 mmol/gDW/h
model.reactions.get_by_id("r_1714").lower_bound = -1.0

# run FBA -- simulation comes from cobrapy, unchanged
sol = model.optimize()
print(f"Growth rate: {sol.objective_value:.4f} h⁻¹")
```
:::
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
% load yeast-GEM from RAVEN YAML
model = readYAMLmodel('yeast-GEM.yml');

% set growth as the objective
model = setParam(model, 'obj', 'r_2111', 1);

% constrain glucose uptake to 1 mmol/gDW/h
model = setParam(model, 'lb', 'r_1714', -1);

% run FBA
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

Twenty-two task-focused pages, MATLAB and Python side by side, with the
examples executed and their output checked.
:::

:::{grid-item-card} API reference
:link: api/index
:link-type: doc

Complete function reference for both MATLAB and Python.
:::

:::{grid-item-card} Installation
:link: installation/index
:link-type: doc

Set up RAVEN in MATLAB or raven-toolbox in Python with a solver.
:::

:::{grid-item-card} Comparison of RAVEN and raven-toolbox
:link: raven3-vs-raven-toolbox
:link-type: doc

Which to use for what, what only one of them has, and where the same
function gives a different answer.
:::

::::

## Citing RAVEN

If you use RAVEN in your research, please cite:

> Wang H, Marcišauskas S, Sánchez BJ, Domenzain I, Hermansson D, Agren R,
> Nielsen J, Kerkhoven EJ (2018). **RAVEN 2.0: A versatile toolbox for
> metabolic network reconstruction and a case study on *Streptomyces
> coelicolor*.** *PLoS Computational Biology* 14(10): e1006541.
> <https://doi.org/10.1371/journal.pcbi.1006541>

See [Citations](references.md) for the full list, including the earlier
RAVEN paper and the GEM reconstruction protocol.

## Source code

RAVEN is publicly available under the GPLv3 license at
[CompMetEng/RAVEN](https://github.com/CompMetEng/RAVEN){.github},
archived at
[https://doi.org/10.5281/zenodo.3689518](https://doi.org/10.5281/zenodo.3689518).
raven-toolbox, the Python port, is under the MIT license at
[CompMetEng/raven-toolbox](https://github.com/CompMetEng/raven-toolbox){.github}.

## Issues and discussions

Report a bug or request a feature on the tracker for the toolbox it concerns:
[RAVEN issues](https://github.com/CompMetEng/RAVEN/issues){.github} for the
MATLAB toolbox, [raven-toolbox issues](https://github.com/CompMetEng/raven-toolbox/issues){.github}
for the Python package. For questions and general discussion, use
[RAVEN discussions](https://github.com/CompMetEng/RAVEN/discussions){.github}
or [raven-toolbox discussions](https://github.com/CompMetEng/raven-toolbox/discussions){.github}.

```{toctree}
:hidden:

migrate
guide/index
api/index
parameter-tuning/index
references
```
