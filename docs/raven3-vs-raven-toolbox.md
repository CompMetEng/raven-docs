# Comparison of RAVEN and raven-toolbox

RAVEN exists in two implementations: the MATLAB toolbox RAVEN 3 and the Python package raven-toolbox. The text below and the two detail pages help a reader who chooses between them or ports a workflow from one to the other.

- RAVEN runs in MATLAB without the COBRA Toolbox.
- raven-toolbox is built on [cobrapy](https://cobrapy.readthedocs.io/), and a model is a `cobra.Model`.

The implementations differ in function names, in functions that a single one of them has, in the form of the results and in the results of some functions. [Features specific to each implementation](raven3-vs-raven-toolbox/what-each-has.md) covers the functions that exist in a single implementation. [Differences in results between functions](raven3-vs-raven-toolbox/same-function-different-answer.md) covers functions that exist in both and return different results.

## Choosing an implementation

Each condition below favours the implementation named next to it. Both implementations provide homology and KEGG reconstruction, metabolic tasks, gap-filling, ftINIT, compartment assignment and model comparison.

| Condition | Implementation |
|---|---|
| The surrounding code is Python | raven-toolbox |
| The model is used with cobrapy tools as a `cobra.Model` | raven-toolbox |
| The KEGG artefacts are built from a specified KEGG release (requires a KEGG FTP subscription) | raven-toolbox |
| The surrounding code is MATLAB | RAVEN |
| A model built with the legacy tINIT method, which ftINIT replaces, is reproduced | RAVEN |
| Dynamic flux balance analysis (FBA) is run with `runDynamicFBA` | RAVEN |
| A model is converted in memory to the COBRA Toolbox structure with `ravenCobraWrapper` | RAVEN |

A model can also be exchanged by file. The function `read_matlab_model` of raven-toolbox reads a COBRA Toolbox `.mat` file as well as a RAVEN `.mat` file, and `write_matlab_model` writes the RAVEN layout.

## Name differences

RAVEN uses `camelCase` and raven-toolbox uses `snake_case`. The generated mapping pairs 103 RAVEN functions with a raven-toolbox function. The rule is: rows of the mapping that have a raven-toolbox function in the second column, with the cobrapy entries excluded. Of these 103, 48 have a name whose letters differ from the RAVEN name when case and the separator `_` are ignored. Examples:

| RAVEN | raven-toolbox |
|---|---|
| `getBlast` | `run_blast` |
| `addRxns` | `add_reactions_from_equations` |
| `addRxnsGenesMets` | `add_reactions_from_model` |
| `fillGaps` | several functions (see [Gap-filling functions](raven3-vs-raven-toolbox/same-function-different-answer.md#gap-filling-functions)) |

The function `add_reactions_from_equations` takes a sequence of mappings with the keys `id`, `equation`, `name`, `bounds`, `gene_reaction_rule` and `subsystem`. This corresponds to the `equations` form of the `rxnsToAdd` struct of `addRxns`. The form of `addRxns` with `mets` and `stoichCoeffs` has no counterpart, and the metadata fields of the struct, such as `eccodes`, `rxnMiriams` and `rxnNotes`, are not keys of the mapping.

The page [MATLAB vs Python](matlab-vs-python.md) is generated at build time from the sources of both implementations. It has 132 rows for 130 documented RAVEN functions (`parseGrRule` and `setExchangeBounds` have two rows each): 55 matched automatically by name, 48 from a curated list and 29 covered by cobrapy. A further 42 RAVEN functions are listed as deliberately not ported and have no counterpart, so the page accounts for 172 RAVEN functions.

## Form of results

RAVEN functions return structs or several output arguments. Many raven-toolbox functions return dataclasses, for example `GapFillResult`, `TaskResult` and `ElementalBalance`, and others return a model or a list, for example `ftinit` and `add_reactions_from_equations`. Porting a call therefore changes how the result is read, in addition to the name.

## Solvers

The two implementations set the solver differently.

| Aspect | RAVEN | raven-toolbox |
|---|---|---|
| Configuration | `setRavenSolver('gurobi')` | `cobra.Configuration().solver = 'gurobi'` |
| Solvers | GLPK, Gurobi, SCIP and the COBRA Toolbox solvers. `setRavenSolver` downloads the SCIP binary for Windows alone | Any solver that cobrapy supports through optlang |
| Free licence | Gurobi (academic) | Gurobi (academic) |
| Bundled open-source solver | GLPK, bundled with RAVEN | GLPK, installed with cobrapy |

[Choosing a solver](installation/index.md#choosing-a-solver) gives a recommendation by model size. In the measurements of the parameter-tuning studies, the ftINIT extraction of raven-toolbox returned different reaction sets for different solvers, seeds and thread counts. [Alternative optima of mixed-integer problems](raven3-vs-raven-toolbox/same-function-different-answer.md#alternative-optima-of-mixed-integer-problems) gives the figures. Whether the solutions have equal quality was not measured across solvers.

```{toctree}
:hidden:

raven3-vs-raven-toolbox/what-each-has
raven3-vs-raven-toolbox/same-function-different-answer
```
