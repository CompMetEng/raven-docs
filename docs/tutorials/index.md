# Legacy tutorials

Five hands-on tutorials were part of the original RAVEN 1 paper (Agren et al., 2013). The scripts run with the current RAVEN version. The exercises are otherwise unchanged from the original. They use the MATLAB toolbox and build up from running a simulation on an existing model to reconstructing a genome-scale model from sequence data. The scripts and all the data files they use are in the [`tutorials/`](https://github.com/CompMetEng/RAVEN/tree/develop/tutorials) folder of the RAVEN repository.

| # | Tutorial | Content |
|---|---|---|
| 1 | [Importing a GEM and running FBA](tutorial1.md) | Load a model, set constraints and an objective, run FBA, visualise fluxes |
| 2 | [Constructing a functional small model](tutorial2.md) | Build a model from scratch; exchange reactions and the steady-state assumption |
| 3 | [Knockouts and omics data](tutorial3.md) | Gene deletions, and using a GEM as a scaffold for microarray data |
| 4 | [Fixing an erroneous model](tutorial4.md) | Systematic quality control: find and fix mass-balance and naming errors |
| 5 | [Reconstructing a GEM from KEGG](tutorial5.md) | De novo reconstruction from protein sequences using KEGG |

## Prerequisites

- The tutorials use the MATLAB toolbox. RAVEN must be installed and `checkRaven` must pass; see [Installation](../installation/raven.md).
- Tutorial 2 loads its model with `importModel` (SBML), and Tutorials 3 and 4 with `readYAMLmodel` (YAML). `curateModelFromTables` curates an existing model from `.tsv` files; see [Excel I/O](../raven3-migration/formats-and-reconstruction.md#excel-io).
- To run a section of a script in MATLAB, highlight it, right-click, and choose "Evaluate selection".
- Tutorials 2, 3 and 4 ship with a `*_solutions.m` companion script containing the completed exercise.

The reconstruction concepts carry over to raven-toolbox. The `snake_case` form of a RAVEN function name matches the raven-toolbox function name for some functions. Some RAVEN functions map to cobrapy (`solveLP` → `model.optimize()`), and some have no Python counterpart (there is no Excel reader). The [API reference](../api/index.md) lists the functions, and [Comparison of RAVEN and raven-toolbox](../raven3-vs-raven-toolbox.md) shows what maps where.

```{toctree}
:hidden:

tutorial1
tutorial2
tutorial3
tutorial4
tutorial5
```
