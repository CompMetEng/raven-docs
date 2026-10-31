# Installation

RAVEN is available as a MATLAB toolbox and as the Python package raven-toolbox. Both build the same models with the same algorithms, and the choice depends on the workflow.

::::{grid} 1 2 2 2

:::{grid-item-card} RAVEN (MATLAB)
:link: raven
:link-type: doc

Installation of the MATLAB toolbox through the MATLAB Add-Ons manager, a release download or `git`, with upgrading and removal.
:::

:::{grid-item-card} raven-toolbox (Python)
:link: python
:link-type: doc

`pip install raven-toolbox`, development installs, upgrading and removal.
:::

::::

## Choosing a solver

Both versions need a linear-programming solver. The options are the same for either language:

| Solver | Licence | Suited to |
|---|---|---|
| Gurobi | Free academic | Genome-scale models, tINIT and ftINIT, gap-filling (recommended) |
| GLPK   | Open source   | Small to medium models, getting started |
| SCIP   | Open source   | MILP problems (MATLAB) |

In MATLAB, `setRavenSolver('gurobi')` selects the active solver. In raven-toolbox, the solver is configured through cobrapy (`cobra.Configuration`).

```{toctree}
:hidden:

raven
python
data-and-binaries
```
