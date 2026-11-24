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
| HiGHS  | Open source   | LP in Python through the scipy interface of cobrapy, which ships with SciPy |
| SCIP   | Open source   | MILP problems (MATLAB); `setRavenSolver('scip')` downloads the binary on Windows |

GLPK is bundled with both toolboxes, so the guide examples run without a further installation. On a genome-scale model a MILP on GLPK is much slower than on Gurobi and warns in MATLAB (`RAVEN:glpkMILP`), so Gurobi is recommended for ftINIT and gap-filling ([Gap-filling](../guide/gap-filling.md)).

In MATLAB, `setRavenSolver('gurobi')` selects the active solver. In raven-toolbox, the solver is configured through cobrapy (`cobra.Configuration`).

```{toctree}
:hidden:

raven
python
```
