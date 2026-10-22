# 6. Solvers and configuration

Most simulations on this site solve a linear program (LP); gap-filling,
minimum-component media, `solveLP` with `minFlux` 3 and ftINIT solve
mixed-integer linear programs (MILPs), and the quadratic MOMA in
[16.5](deletions.md) solves a quadratic program (QP). Something has to solve each
of them, and which solver can do which depends on the solver and the toolbox.
This page is about which solver is in use, how to change it, and how to read
what it gives back.

### Functions on this page

| MATLAB | Python | |
|---|---|---|
| `setRavenSolver` | `Configuration` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | choose the solver |
| `checkRaven` | `Configuration` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | check the solver works |
| `solveLP` | `Model.optimize` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve, and get a solution object |
| `optimizeProb` | `Model.solver` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | solve a problem the toolbox built for you |

## Setup

`smallYeast.yml` from [`docs/data/`](../data/README.md), with glucose and oxygen
opened so there is something to solve.

In this model the uptake reactions are written as `=> metabolite` and shipped
shut at `[0 0]`, so uptake is a **positive** flux and opening one means raising
its *upper* bound. Reverse that and you get a model that solves, reports success,
and grows at exactly zero.

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

The sign convention here is the opposite of yeast-GEM's, where uptake is a
negative flux through an exchange reaction. Neither is more correct; a model
carries whichever its author chose, and the direction the equation is written in
decides which bound opens it. [5. Growth media and conditions](media.md) works
through the other convention.

## 6.1 Which solver is in use

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
fprintf('RAVEN solver preference: %s\n', getpref('RAVEN', 'solver'));
```

```text
RAVEN solver preference: ...
```

RAVEN keeps the choice in MATLAB's preferences, so it survives restarts, and
the answer is whatever *this* installation was last told, which is why the
output above is elided. The preference is global to the installation, not a
property of the model, so a script that changes it changes it for everything
that follows. `checkRaven` prints it along with a test solve.
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

cobrapy has two levels: `Configuration()` is the default applied to models
created from then on, and `model.solver` is the interface this model is
actually using. Because the choice travels with the model, two models in one
session can use different solvers.
:::
::::

## 6.2 Change it

Both toolboxes ship with **GLPK**, which solves LPs and MILPs, so it runs
every example on this site except the quadratic MOMA. RAVEN prints a warning
when it sends a MILP to GLPK, recommending Gurobi: GLPK is fine for problems the
size of these examples, but on a genome-scale model gap-filling and ftINIT can
take far longer than with **Gurobi**, which is free for academic use. A QP needs
a QP-capable solver, such as Gurobi or CPLEX; RAVEN has no functions that solve
one.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
setRavenSolver('glpk');     % 'gurobi', 'scip', or 'cobra' to hand over to the COBRA Toolbox
```

The accepted values are `'glpk'`, `'gurobi'`, `'scip'` and `'cobra'`. `'glpk'`
uses the binaries RAVEN ships, so it works with no further installation.
`'gurobi'` needs Gurobi on the MATLAB path, and `'scip'` the SCIP MATLAB
interface. `'cobra'` translates the problem into COBRA Toolbox form and
uses whatever `changeCobraSolver` last selected, which requires the COBRA
Toolbox to be initialised first; `setRavenSolver` checks that and errors
rather than storing a preference that cannot work.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.solver = "glpk"       # or "gurobi", "cplex", "osqp", ...

from cobra import Configuration
Configuration().solver = "glpk"     # the default for models loaded later
```

Assigning to `model.solver` rebuilds this model's problem; assigning to
`Configuration().solver` changes the default for models created afterwards
and leaves existing ones alone. The available names are whichever optlang
interfaces are installed.
:::
::::

## 6.3 What comes back

The two solution objects carry the same information under different names.

| MATLAB `solveLP` | cobrapy `Solution` | |
|---|---|---|
| `sol.f` | `solution.objective_value` | objective value, same sign in both |
| `sol.x` | `solution.fluxes` | fluxes: a vector in `model.rxns` order, or a Series by id |
| `sol.stat` | `solution.status` | how the solve ended |
| `sol.msg` | `solution.status` | what the solver said |
| `sol.sPrice`, `sol.rCost` | `solution.shadow_prices`, `solution.reduced_costs` | duals |

`sol.stat` takes four values: `1` solved to optimality, `0` feasible but not
proven optimal, `-1` infeasible, and `-2` solved but with the flux minimisation
of parsimonious FBA failing afterwards. Only `1` means the fluxes are the answer
to the question that was asked.

The duals are the exception to the correspondence: RAVEN reports `sPrice` and
`rCost` only when `solveLP` runs without flux minimisation, because the second
optimisation replaces the problem whose duals they describe.

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

`solveLP` builds a COBRA-style problem struct and hands it to `optimizeProb`,
which is where the selected solver is actually called. Calling `optimizeProb`
directly is the way to solve a problem the toolbox built for you, such as the
MILPs inside gap-filling. It takes two name-value arguments: `'params'`, a
struct forwarded to the solver, and `'verbose'`, which shows MILP progress.
One field of `params` is handled by RAVEN rather than passed on: `maxRatio`,
which splits badly-scaled columns through auxiliary metabolites before solving
and leaves the feasible region unchanged.
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

`model.solver` is the optlang problem itself, so the underlying solver is
reachable for anything cobrapy does not expose: `model.solver.problem` is the
native object, and `model.solver.configuration` carries tolerances,
time limits and thread counts.
:::
::::

## 6.4 When the solve fails

An infeasible problem is the most common outcome of a bad edit, and the two
toolboxes report it differently: RAVEN sets `sol.stat` to `-1` and returns an
empty flux vector, while cobrapy raises nothing at all; `optimize` returns a
solution with status `infeasible`, and `slim_optimize` returns `nan`.

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

`sol.f` and `sol.x` are empty here, not zero, so arithmetic on them produces
an empty result rather than an error. That is how an unchecked infeasible
solve turns into a blank in a report.
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

Check the status before using a number. `slim_optimize` skips building a full
solution, so it is the fast option inside a loop, but it returns `nan` instead
of a reason.
:::
::::

An infeasible model is over-constrained: the constraints as written have no
solution at all. That is different from a feasible model whose optimum is zero,
which is a statement about biology rather than about the constraints.

:::{warning} What can go wrong
- **A solver that is set but not installed.** `setRavenSolver('gurobi')`
  stores the preference whether or not Gurobi is there; the failure appears
  at the next solve. `checkRaven` tests it directly.
- **A large MILP on GLPK.** Both toolboxes send MILPs to GLPK, and RAVEN
  warns when it does. On a genome-scale model, gap-filling and ftINIT can run
  for hours on GLPK where Gurobi takes minutes; use Gurobi for those.
- **Reading fluxes after a non-optimal solve.** `sol.stat` of `0` means a
  feasible point was found but not proven optimal, and `-2` means the
  parsimonious step failed after an optimal first solve. Both return numbers.
- **Tiny differences between solvers.** Alternative optima mean two solvers
  can return different flux distributions for the same objective value. Pin
  one solver for anything you intend to compare.
:::

## See also

- [4. Simulating growth with FBA](fba.md), the solve itself.
- [5. Growth media and conditions](media.md), the constraints that decide
  whether a problem is feasible at all.
- [Installation](../installation/index.md), installing and testing a solver.
