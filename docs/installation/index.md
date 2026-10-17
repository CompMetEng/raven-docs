# Installation

RAVEN is available as a **MATLAB toolbox** and as the **Python package
raven-toolbox**. Both build the same models with the same algorithms, so pick
whichever fits your workflow:

::::{grid} 1 2 2 2

:::{grid-item-card} RAVEN (MATLAB)
:link: raven
:link-type: doc

Install the MATLAB toolbox: via the MATLAB Add-Ons manager, a release
download, or `git`. Includes upgrading and removal.
:::

:::{grid-item-card} raven-toolbox (Python)
:link: python
:link-type: doc

`pip install raven-toolbox`, plus development installs, upgrading and
removal.
:::

::::

## Choosing a solver

Both versions need a linear-programming solver. The choice is the same for
either language:

| Solver | License | Good for |
|---|---|---|
| Gurobi | Free academic | Genome-scale models, tINIT/ftINIT, gap-filling (recommended) |
| GLPK   | Open source   | Small to medium models, getting started |
| SCIP   | Open source   | MILP problems (MATLAB) |

In **MATLAB**, select the active solver with `setRavenSolver('gurobi')`. In
**raven-toolbox**, the solver is configured through cobrapy
(`cobra.Configuration`).

```{toctree}
:hidden:

raven
python
data-and-binaries
```
