# Legacy tutorials

Five tutorials belonged to the original RAVEN 1 paper (Agren et al., 2013). The scripts run with the current version of RAVEN, and the exercises are otherwise unchanged from the original. They use the MATLAB toolbox and progress from a simulation with an existing model to the reconstruction of a genome-scale model from sequence data. The scripts and their data files are in the [`tutorials/`](https://github.com/CompMetEng/RAVEN/tree/develop/tutorials) folder of the RAVEN repository.

| # | Tutorial | Content |
|---|---|---|
| 1 | [Importing a GEM and running FBA](tutorial1.md) | Load a model, set constraints and an objective, run FBA and visualise fluxes |
| 2 | [Constructing a functional small model](tutorial2.md) | Build a model from scratch, with exchange reactions and the steady-state assumption |
| 3 | [Knockouts and omics data](tutorial3.md) | Gene deletions, and a GEM as a scaffold for microarray data |
| 4 | [Fixing an erroneous model](tutorial4.md) | Quality control: find and fix mass-balance and naming errors |
| 5 | [Reconstructing a GEM from KEGG](tutorial5.md) | De novo reconstruction from protein sequences with KEGG |

## Prerequisites

- The tutorials use the MATLAB toolbox. RAVEN is installed and `checkRaven` passes ([Installation](../installation/raven.md)).
- Tutorials 1 and 2 load their model with `importModel` (SBML), and Tutorials 3 and 4 load theirs with `readYAMLmodel` (YAML). `curateModelFromTables` curates an existing model from `.tsv` files ([Excel I/O](../raven3-migration/formats-and-reconstruction.md#excel-io)).
- A section of a script runs in MATLAB when it is highlighted and "Evaluate selection" is chosen from the context menu.
- Tutorials 2, 3 and 4 have a companion script `*_solutions.m` with the completed exercise.

The reconstruction concepts apply to raven-toolbox. The `snake_case` form of a RAVEN function name is the name of the raven-toolbox function for some functions. Some RAVEN functions map to cobrapy (`solveLP` to `model.optimize()`), and some have no Python counterpart (there is no Excel reader). The [API reference](../api/index.md) lists the functions, and [Comparison of RAVEN and raven-toolbox](../raven3-vs-raven-toolbox.md) shows what maps where.

```{toctree}
:hidden:

tutorial1
tutorial2
tutorial3
tutorial4
tutorial5
```
