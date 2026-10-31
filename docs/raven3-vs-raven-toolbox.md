# Comparison of RAVEN and raven-toolbox

RAVEN exists as two implementations: the MATLAB toolbox RAVEN and the Python package raven-toolbox.

- RAVEN is a MATLAB toolbox that runs without the COBRA Toolbox.
- raven-toolbox is a Python package built on [cobrapy](https://cobrapy.readthedocs.io/). A model is a `cobra.Model`.

The implementations differ in function names, in functions that exist in one implementation only and in the results of certain functions (see [Differences in results between functions](raven3-vs-raven-toolbox/same-function-different-answer.md)).

## Choosing an implementation

The choice of an implementation depends on the conditions below. Each condition points to one implementation.

| Implementation | Condition |
|---|---|
| raven-toolbox | The surrounding code is Python. |
| raven-toolbox | The model should be a `cobra.Model` for use with cobrapy tools. |
| raven-toolbox | Reproducible environments and continuous integration (CI) are required. |
| raven-toolbox | The KEGG artefacts must be built from a specified KEGG release. |
| RAVEN | The surrounding code is MATLAB. |
| RAVEN | A model built with tINIT must be reproduced. |
| RAVEN | Dynamic flux balance analysis (FBA) is required. |
| RAVEN | Conversion to the COBRA Toolbox structure is required. |
| Either | The functions both implementations share are needed: homology and KEGG reconstruction, metabolic tasks, gap-filling, ftINIT, compartment assignment and model comparison. |

## Name differences

The implementations differ in naming: RAVEN uses `camelCase` and raven-toolbox uses `snake_case`; many names are not the `snake_case` form of the RAVEN name. Examples:

| RAVEN | raven-toolbox |
|---|---|
| `getBlast` | `run_blast` |
| `addRxns` | `add_reactions_from_equations` |
| `fillGaps` | several functions (see [Gap-filling functions](raven3-vs-raven-toolbox/same-function-different-answer.md#gap-filling-functions)) |

The [MATLAB vs Python](matlab-vs-python.md) page, generated from the sources of both implementations at build time, lists the name in the other implementation. Some functions have no counterpart or map to cobrapy; the table records which functions cobrapy covers in place of raven-toolbox, and which are deliberately absent.

## Detail pages

| Page | Content |
|---|---|
| [Features specific to each implementation](raven3-vs-raven-toolbox/what-each-has.md) | Features of raven-toolbox (model type, KEGG artefact generation, checksum registry) and of RAVEN (tINIT, COBRA Toolbox conversion, dynamic FBA, MATLAB-specific functions). |
| [Differences in results between functions](raven3-vs-raven-toolbox/same-function-different-answer.md) | Task-checking runtime, gap-filling functions, alternative optima of mixed-integer problems, elemental balance results and parsing of gene-reaction rules. |

## Solvers

The solver is set differently in each implementation.

| Aspect | RAVEN | raven-toolbox |
|---|---|---|
| Configuration | `setRavenSolver('gurobi')` | `cobra.Configuration().solver = 'gurobi'` |
| Recommended solver | Gurobi (free academic licence) | Gurobi (free academic licence) |
| Open-source option | GLPK (bundled with RAVEN) | GLPK (bundled with cobrapy) |

The mixed-integer linear programming (MILP) problems of ftINIT extraction can have several optima of equal objective value. For genome-scale MILP, the choice of solver changes which optimum is returned, and the seed, the thread count and wall-clock limits influence it as well (see [Alternative optima of mixed-integer problems](raven3-vs-raven-toolbox/same-function-different-answer.md#alternative-optima-of-mixed-integer-problems)). The solver matrix under [Choosing a solver](installation/index.md#choosing-a-solver) lists Gurobi for genome-scale models and GLPK for small to medium models.

```{toctree}
:hidden:

raven3-vs-raven-toolbox/what-each-has
raven3-vs-raven-toolbox/same-function-different-answer
```
