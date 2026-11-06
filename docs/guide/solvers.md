# Solvers and configuration

Most simulations on this site solve a linear program (LP). Gap-filling, minimal media with a minimum number of components, `solveLP` with `minFlux` set to 3, and ftINIT solve mixed-integer linear programs (MILPs). The quadratic MOMA in [Deletions and essentiality](deletions.md) solves a quadratic program (QP). The solvers that can solve each problem type depend on the solver and on the toolbox.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `setRavenSolver` | `Configuration` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | select the solver |
| `checkRaven` | no equivalent | test the solver |
| `solveLP` | `Model.optimize` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve and return a solution object |
| `optimizeProb` | `Model.solver` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve a problem that the toolbox built |

## Setup

The model is `smallYeast.yml` from [`docs/data/`](../data/README.md), with glucose and oxygen opened so that there is a problem to solve.

In this model, the uptake reactions are written as `=> metabolite` and are closed at `[0 0]`. Uptake is a positive flux, and an uptake reaction is opened by raising its upper bound. Lowering the lower bound instead gives a model that solves, reports success and grows at zero.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
model.reactions.get_by_id("glcIN").upper_bound = 1.0
model.reactions.get_by_id("o2IN").upper_bound = 1000.0
```
:::
::::

The sign convention is the opposite of the one in yeast-GEM, where uptake is a negative flux through an exchange reaction. A model uses the convention of its author, and the direction in which the equation is written determines which bound opens the reaction. [Growth media and conditions](media.md) works with the other convention.

## Solver in use

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
fprintf('RAVEN solver preference: %s\n', getpref('RAVEN', 'solver'));
```

```text
RAVEN solver preference: ...
```

RAVEN stores the choice in the MATLAB preferences, so it persists across sessions. The answer is the last setting of the installation, and the output is therefore elided. The preference belongs to the installation, so a script that changes it changes it for everything that runs afterwards. `checkRaven` prints the solver together with a test solve.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra import Configuration

print("default:", Configuration().solver.__name__)
print("this model:", model.solver.__class__.__module__)
```

```text
default: optlang.glpk_interface
this model: optlang.glpk_interface
```

cobrapy has two levels. `Configuration()` holds the default for models created afterwards, and `model.solver` is the interface that a model uses. The choice is stored on the model, so two models in one session can use different solvers.
:::
::::

## Changing the solver

Both toolboxes include GLPK, which solves LPs and MILPs and therefore runs every example on this site except the quadratic MOMA. RAVEN warns when it sends a MILP to GLPK and recommends Gurobi. GLPK solves problems of the size of these examples, but gap-filling and ftINIT on a genome-scale model take much longer than with Gurobi, which is free for academic use. A QP needs a solver that supports QPs, such as Gurobi or CPLEX. RAVEN has no function that solves a QP.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
setRavenSolver('glpk');     % 'gurobi', 'scip', or 'cobra' to hand over to the COBRA Toolbox
```

The accepted values are `'glpk'`, `'gurobi'`, `'scip'` and `'cobra'`. `'glpk'` uses the binaries that RAVEN includes and needs no further installation. `'gurobi'` needs Gurobi on the MATLAB path, and `'scip'` needs the SCIP MATLAB interface. `'cobra'` translates the problem to the format of the COBRA Toolbox and uses the solver last selected with `changeCobraSolver`. It requires an initialised COBRA Toolbox, which `setRavenSolver` checks, and it raises an error without storing a preference that cannot work.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.solver = "glpk"       # or "gurobi", "cplex", "osqp", ...

from cobra import Configuration
Configuration().solver = "glpk"     # the default for models loaded later
```

Assigning to `model.solver` rebuilds the problem of this model. Assigning to `Configuration().solver` changes the default for models created afterwards and leaves existing models unchanged. The available names are the optlang interfaces that are installed.
:::
::::

## Solution objects

The two solution objects contain the same information under different names.

| MATLAB `solveLP` | cobrapy `Solution` | Meaning |
|---|---|---|
| `sol.f` | `solution.objective_value` | objective value, with the same sign in both |
| `sol.x` | `solution.fluxes` | fluxes: a vector in the order of `model.rxns`, or a Series by identifier |
| `sol.stat` | `solution.status` | how the solve ended |
| `sol.msg` | `solution.status` | message of the solver |
| `sol.sPrice`, `sol.rCost` | `solution.shadow_prices`, `solution.reduced_costs` | dual values |

`sol.stat` takes four values: `1` for solved to optimality, `0` for feasible without a proof of optimality, `-1` for infeasible, and `-2` for solved with a failure of the flux minimisation (`minFlux`) afterwards. Only `1` means that the fluxes answer the question.

The dual values do not correspond in all cases. RAVEN reports `sPrice` and `rCost` when `solveLP` runs without flux minimisation, because the second optimisation replaces the problem that the duals describe.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = setParam(model, 'obj', 'biomassOUT', 1);
sol = solveLP(model);
fprintf('stat %d: %s\n', sol.stat, sol.msg);
fprintf('growth %.4f /h\n', sol.f);
```

```text
stat 1: Optimal solution found
growth 0.1222 /h
```

`solveLP` builds a problem struct in the COBRA format and passes it to `optimizeProb`, which calls the selected solver. `optimizeProb` is called directly to solve a problem that the toolbox built, such as the MILPs inside gap-filling. It takes two name-value arguments: `'params'`, a struct that is passed to the solver, and `'verbose'`, which shows the progress of a MILP. RAVEN uses one field of `params` itself and does not pass it on. `maxRatio` applies to LPs, splits badly scaled columns through auxiliary metabolites before solving and leaves the feasible region unchanged.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.objective = "biomassOUT"
solution = model.optimize()
print(f"status {solution.status}")
print(f"growth {solution.objective_value:.4f} /h")
```

```text
status optimal
growth 0.1222 /h
```

`model.solver` is the optlang problem itself, so the underlying solver is accessible for anything that cobrapy does not expose. `model.solver.problem` is the native object, and `model.solver.configuration` holds tolerances, time limits and the number of threads.
:::
::::

## Failed solves

An infeasible problem is the usual result of a bad edit, and the toolboxes report it differently. RAVEN sets `sol.stat` to `-1` and returns an empty flux vector. cobrapy raises no error: `optimize` returns a solution with the status `infeasible`, and `slim_optimize` returns `nan`.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
broken = setParam(model, 'lb', 'biomassOUT', 1);   % demand growth with no glucose
broken = setParam(broken, 'eq', 'glcIN', 0);
sol = solveLP(broken);
fprintf('stat %d: %s\n', sol.stat, sol.msg);
```

```text
stat -1: The problem is infeasible
```

`sol.f` and `sol.x` are empty, so arithmetic on them returns an empty result without an error. An infeasible solve that is not checked appears as a blank in a report.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
with model:
    model.reactions.get_by_id("biomassOUT").lower_bound = 1.0
    model.reactions.get_by_id("glcIN").bounds = (0, 0)
    print("status:", model.optimize().status)
    print("slim_optimize:", model.slim_optimize())
```

```text
status: infeasible
slim_optimize: nan
```

The status should be checked before a number is used. `slim_optimize` does not build a full solution, which makes it fast inside a loop, and it returns `nan` without a reason.
:::
::::

An infeasible model is over-constrained, and no solution satisfies the constraints as written. A feasible model with an optimum of zero is a different case, and it describes the biology.

:::{admonition} Troubleshooting
:class: warning

- A solver is set and missing. `setRavenSolver('gurobi')` stores the preference whether or not Gurobi is present, and the failure appears at the next solve. `checkRaven` tests the solver directly.
- A large MILP runs on GLPK. Both toolboxes send MILPs to GLPK, and RAVEN warns when it does. Gap-filling and ftINIT on a genome-scale model run for hours on GLPK where Gurobi takes minutes.
- Fluxes are read after a solve that is not optimal. `sol.stat` of `0` means that a feasible point was found without a proof of optimality, and `-2` means that the parsimonious step failed after an optimal first solve. Both return numbers.
- Solvers give slightly different results. Alternative optima allow two solvers to return different flux distributions with the same objective value. Fix one solver for any comparison.
:::

## See also

- [Simulating growth with FBA](fba.md): the solve.
- [Growth media and conditions](media.md): the constraints that determine whether a problem is feasible.
- [Installation](../installation/index.md): installation and test of a solver.
