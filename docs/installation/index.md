# Installation

RAVEN is available as a MATLAB toolbox and as the Python package raven-toolbox. Both build models for the same workflows, some algorithms differ between them ([Tuned parameter defaults](../tuned-parameters.md)), and the workflow determines which to use.

::::{grid} 1 2 2 2

:::{grid-item-card} RAVEN (MATLAB)
:link: raven
:link-type: doc

Installation of the MATLAB toolbox with the Add-Ons manager, a release download or `git`, and its upgrade and removal.
:::

:::{grid-item-card} raven-toolbox (Python)
:link: python
:link-type: doc

`pip install --pre raven-toolbox`, a development installation, and the upgrade and removal of the package.
:::

::::

## Choosing a solver

Both versions need a linear-programming solver:

| Solver | Licence | Suited to |
|---|---|---|
| Gurobi | Free academic | Genome-scale models, ftINIT, gap-filling, and in MATLAB the legacy tINIT method (recommended) |
| GLPK   | Open source   | Small and medium models, and getting started |
| SCIP   | Open source   | MILP problems (MATLAB); `setRavenSolver('scip')` downloads the binary on Windows |

In MATLAB, `setRavenSolver('gurobi')` selects the active solver. In raven-toolbox, the solver is configured through cobrapy (`cobra.Configuration`).

```{toctree}
:hidden:

raven
python
data-and-binaries
updating-kegg-assets
updating-binaries
```
