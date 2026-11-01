# Comparison of RAVEN and raven-toolbox

RAVEN exists as two implementations: the MATLAB toolbox RAVEN 3 and the Python package raven-toolbox. The pages below help a reader who chooses between them or ports a workflow from one to the other.

- RAVEN is a MATLAB toolbox that runs without the COBRA Toolbox.
- raven-toolbox is a Python package built on [cobrapy](https://cobrapy.readthedocs.io/). A model is a `cobra.Model`.

The implementations differ in function names, in functions that exist in one implementation only, in the form of returned results and in the results of certain functions. Two detail pages cover these differences: [Features specific to each implementation](raven3-vs-raven-toolbox/what-each-has.md) and [Differences in results between functions](raven3-vs-raven-toolbox/same-function-different-answer.md).

## Choosing an implementation

The first three rows of the table list conditions that favour raven-toolbox, the next four favour RAVEN, and the last row names the functions that both implementations have.

| Implementation | Condition |
|---|---|
| raven-toolbox | The surrounding code is Python. |
| raven-toolbox | The model is used with cobrapy tools as a `cobra.Model`. |
| raven-toolbox | The KEGG artefacts are built from a specified KEGG release (requires a KEGG FTP subscription). |
| RAVEN | The surrounding code is MATLAB. |
| RAVEN | A model built with tINIT is reproduced. |
| RAVEN | Dynamic flux balance analysis (FBA) is run with `runDynamicFBA`. |
| RAVEN | A model is converted in memory to the COBRA Toolbox structure with `ravenCobraWrapper`. |
| Either | Homology and KEGG reconstruction, metabolic tasks, gap-filling, ftINIT, compartment assignment and model comparison. |

`read_matlab_model` of raven-toolbox reads a COBRA Toolbox `.mat` file as well as a RAVEN `.mat` file, and `write_matlab_model` writes the RAVEN layout, so a model can be exchanged by file between the implementations.

## Name differences

RAVEN uses `camelCase` and raven-toolbox uses `snake_case`. The generated mapping pairs 103 RAVEN functions with a raven-toolbox function (rule: rows of the mapping with a raven-toolbox function in the second column, cobrapy entries excluded). Of these, 48 have a name whose letters differ from the RAVEN name when case and the separator character `_` are ignored. Examples:

| RAVEN | raven-toolbox |
|---|---|
| `getBlast` | `run_blast` |
| `addRxns` | `add_reactions_from_equations` |
| `addRxnsGenesMets` | `add_reactions_from_model` |
| `fillGaps` | several functions (see [Gap-filling functions](raven3-vs-raven-toolbox/same-function-different-answer.md#gap-filling-functions)) |

`add_reactions_from_equations` takes a sequence of mappings with the keys `id`, `equation`, `name`, `bounds`, `gene_reaction_rule` and `subsystem`, which corresponds to the `equations` form of the `rxnsToAdd` struct of `addRxns`. The form of `addRxns` with `mets` and `stoichCoeffs` has no counterpart, and the metadata fields of the struct (such as `eccodes`, `rxnMiriams` and `rxnNotes`) are not keys of the mapping.

The [MATLAB vs Python](matlab-vs-python.md) page is generated from the sources of both implementations at build time. It has 132 rows for 130 documented RAVEN functions (`parseGrRule` and `setExchangeBounds` have two rows each): 55 matched automatically by name, 48 from a curated list and 29 covered by cobrapy. A further 42 RAVEN functions are listed as deliberately not ported and have no counterpart, so the page accounts for 172 RAVEN functions.

## Form of results

RAVEN functions return structs or several output arguments. Many raven-toolbox functions return dataclasses, for example `GapFillResult`, `TaskResult` and `ElementalBalance`; others return a model or a list, for example `ftinit` and `add_reactions_from_equations`. Porting a call requires changing how the result is read, in addition to the name.

## Solvers

The solver is set differently in each implementation.

| Aspect | RAVEN | raven-toolbox |
|---|---|---|
| Configuration | `setRavenSolver('gurobi')` | `cobra.Configuration().solver = 'gurobi'` |
| Solvers | GLPK, Gurobi, SCIP and the COBRA Toolbox solvers (`setRavenSolver` downloads the SCIP binary for Windows only) | Any solver that cobrapy supports through optlang |
| Free licence | Gurobi (academic) | Gurobi (academic) |
| Bundled open-source solver | GLPK (bundled with RAVEN) | GLPK (installed with cobrapy) |

[Choosing a solver](installation/index.md#choosing-a-solver) gives the recommendation by model size. The ftINIT extraction of raven-toolbox returned different reaction sets for different solvers, seeds and thread counts in the measurements of the parameter-tuning studies; [Alternative optima of mixed-integer problems](raven3-vs-raven-toolbox/same-function-different-answer.md#alternative-optima-of-mixed-integer-problems) gives the figures. Whether the solutions are of equal quality was not measured across solvers.

```{toctree}
:hidden:

raven3-vs-raven-toolbox/what-each-has
raven3-vs-raven-toolbox/same-function-different-answer
```
