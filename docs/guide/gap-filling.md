# Gap-filling

A draft model always has holes: reactions that cannot carry flux because something upstream is missing, metabolites nothing produces, a biomass component the network cannot make. Gap-filling adds reactions from a template until the holes close. Deciding which holes are worth closing is a judgement.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `gapReport` | `check_model`, `analyse_topology` | find the holes first |
| `fillGaps` | `connect_blocked_reactions` | add template reactions so blocked reactions can carry flux |
| `gapFillFastLP` | `fill_gaps_fast_lp` | the linear programming (LP) formulation (fastGapFill / swiftGapFill) |
| `gapFillMILP` | `fill_gaps_milp` | the mixed-integer linear programming (MILP) formulation, when the LP is not enough |
| `gapFillTopological` | `analyse_topology` | connectivity, without solving an LP |
| `fitTasks` | `fill_tasks` | fill until a task passes; see [Metabolic tasks](tasks.md) |

`gapFillTopological` and `analyse_topology` take their defaults from the model. The seeds are the metabolites of every reaction that has only substrates and a negative lower bound, or only products and a positive upper bound, whatever the number of metabolites; when the model has no such reaction, RAVEN and the toolbox warn that there is no seed. Reactions without substrates fire in the scope computation whatever their bounds, so closing an uptake reaction does not remove its metabolite from the scope. The targets are the metabolites of the first objective reaction, substrates and products. Without targets, a model with no objective reaction raises `RAVEN:badInput` in MATLAB and `ValueError` in Python.

## Setup

A gap-filling example needs a draft with holes and a template to fill them from. `smallYeast.yml` is both: its medium is opened, a copy is taken and one reaction is removed. The reaction that gap-filling adds back can be checked directly: it should be the reaction that was removed.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
template = readYAMLmodel('smallYeast.yml');
template = setParam(template, 'ub', {'glcIN', 'o2IN'}, [1 1000]);

draft = removeReactions(template, {'ADH1'});   % alcohol dehydrogenase
draft.id = 'draft';   % fillGaps refuses a template sharing the model's id
fprintf('draft %d rxns, template %d rxns\n', numel(draft.rxns), numel(template.rxns));
```

```text
draft 52 rxns, template 53 rxns
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from raven_toolbox.io import read_yaml_model

cobra.Configuration().processes = 1     # FVA below spawns workers otherwise

template = read_yaml_model("smallYeast.yml")
template.reactions.get_by_id("glcIN").upper_bound = 1.0
template.reactions.get_by_id("o2IN").upper_bound = 1000.0

draft = template.copy()
draft.remove_reactions([draft.reactions.get_by_id("ADH1")])   # alcohol dehydrogenase
print(f"draft {len(draft.reactions)} rxns, template {len(template.reactions)} rxns")
```

```text
draft 52 rxns, template 53 rxns
```

With the medium as shipped (closed), `smallYeast` has 51 of its 53 reactions blocked, because nothing can get in and not because of gaps. Gap-filling a model in that state asks the wrong question.
:::
::::

## Finding holes

A model acquires reactions that nobody can justify when gap-filling starts without a check of the holes. Start from the reactions that cannot carry flux.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
canCarry = haveFlux(draft);
fprintf('%d of %d reactions can carry flux\n', sum(canCarry), numel(draft.rxns));
```

```text
50 of 52 reactions can carry flux
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import find_blocked_reactions

blocked = find_blocked_reactions(draft)
print(f"{len(blocked)} of {len(draft.reactions)} reactions are blocked")
print(sorted(blocked)[:5])
```

```text
2 of 52 reactions are blocked
['ethIN', 'ethOUT']
```
:::
::::

## Connectivity gap-filling

Connectivity gap-filling is structural: it finds the template reactions that, added to the draft, let a blocked reaction carry flux. It uses no objective and no growth, only connectivity.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
% fillGaps solves a MILP: GLPK warns and solves it, setRavenSolver('gurobi') is faster
[newConnected, cannotConnect, addedRxns] = fillGaps(draft, {template}, ...
    'allowNetProduction', true, 'useModelConstraints', false);
fprintf('%d added: %s\n', numel(addedRxns), strjoin(addedRxns, ', '));
```

```text
[Warning: Solving a MILP with GLPK. This works for small problems, but for larger problems Gurobi is much faster and more reliable; select it with setRavenSolver('gurobi'). Silence this warning with warning('off','RAVEN:glpkMILP').]
1 added: ADH1
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.gapfilling import connect_blocked_reactions

result = connect_blocked_reactions(draft, template, allow_net_production=True)
print(f"{len(result.added_reactions)} added: "
      f"{', '.join(sorted(result.added_reactions))}")
```

```text
1 added: ADH1
```

The reaction that is returned is the one that was taken out, in both toolboxes. That identity is the result to report. `fillGaps` also returns the newly connected reactions and those that cannot be connected, and their numbers are not stable: it solves a MILP, several solutions are equally optimal, and which one is returned can change with the machine or the thread count. Two CI runs on identical input reported 11 and 9 newly connected.

Both are MILPs. `connect_blocked_reactions` runs on the GLPK that ships with cobrapy; `fillGaps` runs on RAVEN's bundled GLPK too, with a warning that recommends Gurobi (`setRavenSolver('gurobi')`).

`allow_net_production` decides how strict the test is. A reaction can be blocked because a substrate is unavailable or because a product has nowhere to go; with net production allowed, only the first counts. Turning it off asks the harder question and usually adds more reactions.
:::
::::

## LP formulation

`fillGaps` takes a cell array of template models or a model structure, while `gapFillFastLP` and `gapFillMILP` take a single struct. Passing a cell to these two fails with `Dot indexing is not supported for variables of this type`.

`fill_gaps_fast_lp` (fastGapFill, and its `swift` variant) solves one LP per blocked reaction: activate this reaction using as few template reactions as possible. It is the fast option, and the one that scales to a genome-scale draft.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[addedRxns, outModel] = gapFillFastLP(draft, template);   % LP, GLPK is enough
fprintf('%d reactions added\n', numel(addedRxns));
```

```text
gapFillFastLP: 2 blocked reaction(s) found in draft model.
[Warning: The following reaction IDs in smallYeast are already present in the model and were renamed: Old: acOUT New: acOUT_smallYeast Old: biomassOUT New: biomassOUT_smallYeast Old: co2OUT New: co2OUT_smallYeast Old: ethOUT New: ethOUT_smallYeast Old: glyOUT New: glyOUT_smallYeast Old: glcIN New: glcIN_smallYeast Old: o2IN New: o2IN_smallYeast Old: ethIN New: ethIN_smallYeast Old: HXK New: HXK_smallYeast ...and 43 more]

gapFillFastLP: 1 reaction(s) cannot be rescued by the universal database.
gapFillFastLP: 1/2 blocked reaction(s) are rescuable; running fast...
gapFillFastLP: added 5 reaction(s) from universal database.
5 reactions added
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.gapfilling import fill_gaps_fast_lp

result = fill_gaps_fast_lp(draft, template, verbose=False)
print(f"{len(result.added_reactions)} reactions added")
```

```text
1 reactions added
```

The two tabs add 5 and 1 (MATLAB adds 8 with Gurobi: the LP has alternative optima, and the solver picks one). They apply the same method to different inputs: the MATLAB call merges the whole template into the draft first, renaming every id it already has, which the rename warning in the MATLAB output lists. Its universal database therefore holds a second copy of the draft's own reactions, and the LP is free to rescue a blocked reaction through those duplicates. `fill_gaps_fast_lp` matches by id and treats the shared reactions as already present, so only the missing one is a candidate. On two models that differ, which is the real case, the gap between the counts closes.
:::
::::

## MILP formulation

When the LP formulation adds too much, or when the provably smallest set is wanted, the MILP formulation is the alternative. GLPK solves it at this size in both toolboxes (RAVEN warns and recommends Gurobi); on anything genome-scale it is slower by a wide margin, and Gurobi is the better choice.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[addedRxns, outModel] = gapFillMILP(draft, template);
fprintf('%d reactions added\n', numel(addedRxns));
```

```text
[Warning: The following reaction IDs in smallYeast are already present in the model and were renamed: Old: acOUT New: acOUT_smallYeast Old: biomassOUT New: biomassOUT_smallYeast Old: co2OUT New: co2OUT_smallYeast Old: ethOUT New: ethOUT_smallYeast Old: glyOUT New: glyOUT_smallYeast Old: glcIN New: glcIN_smallYeast Old: o2IN New: o2IN_smallYeast Old: ethIN New: ethIN_smallYeast Old: HXK New: HXK_smallYeast ...and 43 more]

gapFillMILP: merged model has 52 mets, 105 rxns (52 draft, 52 universal).
gapFillMILP: 52 database candidates.
gapFillMILP: setting minGrowth = 0.02443 (10% of max 0.2443).
gapFillMILP: solving MILP (157 vars, 52 binary, 157 constraints)...
[Warning: Solving a MILP with GLPK. This works for small problems, but for larger problems Gurobi is much faster and more reliable; select it with setRavenSolver('gurobi'). Silence this warning with warning('off','RAVEN:glpkMILP').]
gapFillMILP: added 0 universal reaction(s).
0 reactions added
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.gapfilling import fill_gaps_milp

result = fill_gaps_milp(draft, template)
print(f"{len(result.added_reactions)} reactions added")
```

```text
fill_gaps_milp: merged model has 105 reactions (52 draft, 53 template).
fill_gaps_milp: setting min_growth = 0.02443 (10% of FBA max 0.2443).
fill_gaps_milp: solving MILP (53 database candidates)...
fill_gaps_milp: added 0 template reaction(s).
0 reactions added
```
:::
::::

Zero is the right answer here: without `ADH1` the draft grows at 0.1222 /h, so it meets the default floor (10 % of the merged model's maximum, 0.02443 /h in both tools). The template repeats the draft's reactions, its uptake reactions included, so the merged model can take up twice the glucose and its maximum is 0.2443 /h. The MILP has nothing to add. To see a repair, remove a reaction that growth needs, such as hexokinase:

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
draft2 = removeReactions(template, {'HXK'});   % hexokinase
draft2.id = 'draft2';
sol = solveLP(draft2);
fprintf('draft growth %.4f\n', sol.f);
addedRxns = gapFillMILP(draft2, template);
fprintf('added: %s\n', strjoin(addedRxns, ', '));
```

```text
draft growth -0.0000
[Warning: The following reaction IDs in smallYeast are already present in the model and were renamed: Old: acOUT New: acOUT_smallYeast Old: biomassOUT New: biomassOUT_smallYeast Old: co2OUT New: co2OUT_smallYeast Old: ethOUT New: ethOUT_smallYeast Old: glyOUT New: glyOUT_smallYeast Old: glcIN New: glcIN_smallYeast Old: o2IN New: o2IN_smallYeast Old: ethIN New: ethIN_smallYeast Old: PGI New: PGI_smallYeast ...and 43 more]

gapFillMILP: merged model has 52 mets, 105 rxns (52 draft, 52 universal).
gapFillMILP: 52 database candidates.
gapFillMILP: setting minGrowth = 0.02443 (10% of max 0.2443).
gapFillMILP: solving MILP (157 vars, 52 binary, 157 constraints)...
[Warning: Solving a MILP with GLPK. This works for small problems, but for larger problems Gurobi is much faster and more reliable; select it with setRavenSolver('gurobi'). Silence this warning with warning('off','RAVEN:glpkMILP').]
gapFillMILP: added 1 universal reaction(s).
added: HXK
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
draft2 = template.copy()
draft2.remove_reactions([draft2.reactions.get_by_id("HXK")])   # hexokinase
print(f"draft growth {draft2.slim_optimize():.4f}")
result = fill_gaps_milp(draft2, template, verbose=False)
print(f"added: {result.added_reactions}")
print(f"filled growth {result.model.slim_optimize():.4f}")
```

```text
draft growth 0.0000
added: ['HXK']
filled growth 0.1222
```
:::
::::

Hexokinase is added back. Both functions only add template reactions: the draft's own reactions keep their bounds, forced fluxes such as ATP maintenance included. A draft reaction that runs in the wrong direction is therefore not reversed to close a gap; it is a curation finding, so correct its bounds in the draft (see [Editing an existing model](editing.md)) and fill again.

## Filling towards a task

Connectivity gap-filling asks whether a reaction can carry flux. The other question, whether the model can perform a given function, is answered by filling against a task list, which is the form the question usually takes: a model that grows, or that produces a particular compound.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
tasks = parseTaskList('tasks.txt');
[outModel, addedRxns] = fitTasks(draft, template, [], 'taskStructure', tasks);
```

```text
[Warning: Exchange metabolites should normally not be removed from the model when using checkTasks. Inputs and outputs are defined in the task file instead. Use importModel(file,false) to import a model with exchange metabolites remaining]
[GROWTH] Growth on glucose: Added 0 reaction(s), 0 reactions added in total
[Warning: "[LEAK] Biomass from nothing" is set as SHOULD FAIL. Such tasks cannot be modelled using this approach and the task is therefore ignored]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.init import fill_tasks
```

See [Metabolic tasks](tasks.md) for the task list itself, and [Context-specific models](init.md) for `fill_tasks` in its usual role, repairing a model that ftINIT has reduced.

`fitTasks` fills one task at a time, so the order of the task list can change the result. Its `rxnScores` weights the candidates, taking negative scores only and maximising their sum, so a reaction with a score closer to zero is cheaper to add; this is how ftINIT prefers reactions its expression data supports. `gapFillMode` selects the back-end: `'merge'` combines the reference model with the draft for every task, and `'preMerged'` expects a reference that already contains the draft, which is the form ftINIT passes.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- Identifiers that do not line up. Gap-filling can only add what it can match. Two models built from different databases share almost no metabolite ids, and the result is a gap-filler that adds nothing, or adds duplicates.
- Filling every gap. Some blocked reactions are blocked because the organism cannot perform them. Each addition is a claim about biology, and `fillGaps` makes hundreds of them in one call.
- Net production hiding the problem. `allowNetProduction` makes more reactions look connectable by ignoring where the products go. It helps in early stages and misleads in later ones.
- MILP on a genome-scale model. Expect it to be slow, on GLPK most of all, and give it a time limit; see [Solvers and configuration](solvers.md).
- A draft reaction in the wrong direction. `gapFillMILP` and `fill_gaps_milp` do not change the draft's own reactions, so a wrong direction shows up as a fill that fails or adds a detour around it.
- Comparing added-reaction counts across toolboxes. The two sides differ in what they treat as a candidate, so the counts are only comparable when the template holds reactions that the draft lacks.
:::

## See also

- [Quality control](quality-control.md), finding the holes, and deciding which matter.
- [Metabolic tasks](tasks.md), the other way to say what the model must do.
- [Reading and writing models](io.md), saving the filled model with a record of what was added.
