---
icon: material/folder-open
---

# Legacy tutorials

These five hands-on tutorials were part of the original **RAVEN 1** paper
(Agren et al., 2013). The code has been updated to run with current RAVEN, but
the exercises themselves are otherwise unchanged. They use the **MATLAB**
toolbox and build up from running a simulation on an existing model to
reconstructing a genome-scale model from sequence data. The scripts and all the
data files they use live in the
[`tutorials/`](https://github.com/CompMetEng/RAVEN/tree/develop/tutorials)
folder of the RAVEN repository.

| # | Tutorial | What you learn |
|---|---|---|
| 1 | [Import a GEM and run FBA](tutorial1.md) | Load a model, set constraints and an objective, run FBA, visualise fluxes |
| 2 | [Construct a functional small model](tutorial2.md) | Build a model from scratch in Excel; exchange reactions and the steady-state assumption |
| 3 | [Knockouts and omics data](tutorial3.md) | Gene deletions, and using a GEM as a scaffold for microarray data |
| 4 | [Fix an erroneous model](tutorial4.md) | Systematic quality control: find and fix mass-balance and naming errors |
| 5 | [Reconstruct a GEM from KEGG](tutorial5.md) | *De novo* reconstruction from protein sequences using KEGG |

## Before you start

- These tutorials use the **MATLAB** toolbox. Make sure RAVEN is installed and
  `checkRaven` passes; see [Installation](../installation/raven.md).
- Tutorials 2–4 involve editing models in **RAVEN-compatible Excel format**,
  using `importExcelModel`. RAVEN 3 removed `importExcelModel`, so this step
  does not run as written on RAVEN 3; see [Excel I/O](../raven3-migration/formats-and-reconstruction.md#excel-io)
  for the replacement, `curateModelFromTables`, which curates an existing
  model from `.tsv` files rather than importing a full model from `.xlsx`.
- To run a section of a script in MATLAB, highlight it, right-click, and choose
  *"Evaluate selection"*.
- Tutorials 2, 3 and 4 ship with a `*_solutions.m` companion script containing
  the completed exercise.

:::{tip} Python users
The reconstruction concepts carry over directly to raven-toolbox, but
converting the name to `snake_case` does not always give the matching
raven-toolbox function name; some RAVEN functions map to cobrapy instead
(`solveLP` → `model.optimize()`), and some have no Python counterpart at all
(there is no Excel reader). Look each one up in the
[API reference](../api/index.md), and see
[RAVEN vs. raven-toolbox](../raven3-vs-raven-toolbox.md) for what maps where.
:::

```{toctree}
:hidden:

tutorial1
tutorial2
tutorial3
tutorial4
tutorial5
```
