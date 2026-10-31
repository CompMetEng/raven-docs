# RAVEN vs. raven-toolbox

:::{note} Looking for a specific function?
The [MATLAB vs Python](matlab-vs-python.md) table pairs every function that
exists in both, and links straight to the reference entry for each. This
page is the narrative comparison; that page is the lookup.
:::

RAVEN exists as two independent implementations:

- **RAVEN**: the original MATLAB toolbox, which works entirely on its own,
  including independently of the COBRA Toolbox.
- **raven-toolbox**: the Python package, built on
  [cobrapy](https://cobrapy.readthedocs.io/), so a model is a `cobra.Model` and
  the wider Python ecosystem works on it directly.

They do the same things (homology and KEGG reconstruction, metabolic tasks,
gap-filling, context-specific extraction with ftINIT, compartment assignment,
model comparison), but one is not a direct translation of the other. Names
differ, some capabilities exist on one side only, and a handful of functions
answer the same question differently.

This page is the whole comparison. The function-by-function view is the
[mapping table](matlab-vs-python.md), generated from both toolboxes' sources at
build time.

## Which one should you use?

Neither is a reduced version of the other, so the right choice usually depends
on the rest of your code, not on the toolbox itself.

**Use raven-toolbox** if the surrounding code is Python, if you want the model
to be a `cobra.Model` that every cobrapy tool accepts without conversion, if
you need reproducible environments and CI, or if you need KEGG artefacts built
against a stated release rather than whatever is distributed.

**Use RAVEN** if the surrounding code is MATLAB, if you need to reproduce a
model built with tINIT, or if you need dynamic FBA or conversion to the COBRA
Toolbox structure.

**Either** covers the core reconstruction and analysis path. Where both have a
function, the mapping table names the pair; where only one does, the sections
below say which and why.

## Changing the case does not give the matching name

MATLAB uses `camelCase` and Python uses `snake_case`, but changing only the
case usually produces a name that does not exist. Much of the API was
deliberately renamed as it was ported:

| MATLAB | Python |
|---|---|
| `getBlast` | `run_blast` |
| `addRxns` | `add_reactions_from_equations` |
| `fillGaps` | three functions with different algorithms |

Check the [mapping table](matlab-vs-python.md) rather than guessing. It also
records what cobrapy covers instead of raven-toolbox, and what is deliberately
absent.

## Detail pages

| | |
|---|---|
| [Features specific to each implementation](raven3-vs-raven-toolbox/what-each-has.md) | Capabilities that exist on only one side: cobrapy's foundation and KEGG artefact generation on the Python side; tINIT, COBRA Toolbox conversion, dynamic FBA, and MATLAB-specific plumbing on the MATLAB side. |
| [Same function, different answer](raven3-vs-raven-toolbox/same-function-different-answer.md) | Where both sides do the same job but hand back a different result: gene-association merging, task-checking runtime, gap-filling's three-way split, MILP alternate optima, and elemental balance. |

## Solvers

| | RAVEN (MATLAB) | raven-toolbox (Python) |
|---|---|---|
| Configuration | `setRavenSolver('gurobi')` | `cobra.Configuration().solver = 'gurobi'` |
| Recommended solver | Gurobi (free academic licence) | Gurobi (free academic licence) |
| Open-source option | GLPK (bundled with RAVEN) | GLPK (bundled with cobrapy) |

Genome-scale MILP work (ftINIT extraction in particular) is where the choice
matters most; see [Installation](installation/index.md) for the full solver
matrix.

```{toctree}
:hidden:

raven3-vs-raven-toolbox/what-each-has
raven3-vs-raven-toolbox/same-function-different-answer
```

