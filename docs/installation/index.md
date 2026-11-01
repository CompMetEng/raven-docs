# Installation

RAVEN is available as a MATLAB toolbox and as the Python package raven-toolbox. Both build the same models with the same algorithms, and the workflow decides which to use.

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

Both versions need a linear-programming solver. The options are the same for either language:

| Solver | Licence | Suited to |
|---|---|---|
| Gurobi | Free academic | Genome-scale models, ftINIT, the legacy tINIT method and gap-filling (recommended) |
| GLPK   | Open source   | Small and medium models, and getting started |
| SCIP   | Open source   | MILP problems (MATLAB); `setRavenSolver('scip')` downloads the binary on Windows only |

In MATLAB, `setRavenSolver('gurobi')` selects the active solver. In raven-toolbox, the solver is configured through cobrapy (`cobra.Configuration`).

```{toctree}
:hidden:

raven
python
data-and-binaries
```
