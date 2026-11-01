# Metabolic tasks

A metabolic task is a statement of something the model must be able to do: "given glucose and oxygen, produce biomass", "make ATP", "do not produce something from nothing". Tasks test a reconstruction against biology and not against the reconstruction itself, and ftINIT repairs against them after cutting a model down.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `parseTaskList` | `parse_task_list` | read a task-list file |
| `checkTasks` | `check_tasks` | run the tasks against a model |
| `checkTasks` (`getEssential`) | `find_task_essential_reactions` | reactions a task requires |
| `fitTasks` | `fill_tasks` | add reactions until the tasks pass |

## The file format

A task list is a tab-separated table, one row per task, with columns for the inputs, the outputs, any equations that must carry flux, and the bounds on each. [`tasks.txt`](../data/tasks.txt) holds two tasks for `smallYeast.yml`:

```text title="tasks.txt, abridged; the real file keeps every column"
	ID	DESCRIPTION	SHOULD FAIL	IN	IN LB	IN UB	OUT	OUT LB	OUT UB	…
	GROWTH	Growth on glucose		alpha-D-glucose[c];O2[c]	0	1000	biomass[c]	0.01	1000	…
							CO2[c]	0	1000	…
							acetate[c]	0	1000	…
	LEAK	Biomass from nothing	1				biomass[c]	0.01	1000	…
```

Two things about the format have to be right the first time, because both fail in MATLAB with the same error `Index in position 2 is invalid`:

- Every row starts with an empty cell: `parseTaskList` discards any row whose first cell is non-empty (that is how it skips comments and section headers), so in a file without the leading tab every row is discarded.
- Keep the full column set, even where the columns are empty: `parseTaskList` matches all seventeen known headers and then indexes the numeric ones positionally, so omitting `EQU LB` or `CHANGED LB` leaves an index of zero.

raven-toolbox's `parse_task_list` accepts the file with or without either, so both are easy to miss until the MATLAB tab runs. The file `tasks.txt` has the full set; the columns after `OUT UB` are blank.

Metabolites are named `name[compartment]`, matching the metabolite names and not the identifiers. Several go in one cell, separated by `;`, and the bounds columns apply to all of them. To give a metabolite bounds of its own, put it on a continuation row: a row with no `ID` adds its inputs and outputs to the task above it. `GROWTH` uses that to ask for at least 0.01 units of biomass while leaving CO₂ and acetate free; with a lower bound of 0 on biomass, the all-zero flux would pass the task. The 0.01 is illustrative; any positive floor has the same effect.

`SHOULD FAIL` marks a task the model must fail: the second asks for biomass with nothing supplied, which a correct model cannot do, so failing it is a pass.

Once the model's own exchanges are closed (see [Task-defined medium](#task-defined-medium)), `GROWTH` has to list glucose and oxygen as inputs, and biomass, CO₂ and acetate as outputs, because growth has to release its carbon: as CO₂ and, in this small model, some acetate. A task without CO₂ is infeasible, which looks like a broken model and is a broken task.

## Reading and running tasks

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
tasks = parseTaskList('tasks.txt');
fprintf('%d tasks\n', numel(tasks));

closed = closeModel(model);   % the task is the whole boundary, see Task-defined medium
report = checkTasks(closed, [], 'printOutput', false, 'taskStructure', tasks);
for i = 1:numel(report.id)
    verdicts = {'FAIL', 'pass'};
    fprintf('  %-8s %s\n', report.id{i}, verdicts{report.ok(i) + 1});
end
```

```text
2 tasks
  GROWTH   pass
  LEAK     pass
```

`report.ok` is true for both, and for opposite reasons: `GROWTH` was required to pass and did, `LEAK` was required to fail and did.

`checkTasks` prints its own verdicts unless `printOutput` is off, as here, and `printOnlyFailed` narrows that to the failures. Reading the verdicts from `report` gives a structure to test against, not text to read.

Passing the parsed tasks as `taskStructure` makes the second argument, the task file, redundant. `runParallel` evaluates the tasks in parallel workers, and defaults to `false`, because starting a pool takes longer than the time it saves on a short task list; on a genome-scale list it is the setting that matters.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model
from raven_toolbox.tasks import check_tasks, parse_task_list

model = read_yaml_model("smallYeast.yml")
tasks = parse_task_list("tasks.txt")
print(len(tasks), "tasks")

for result in check_tasks(model, tasks, close_boundaries=True):   # see Task-defined medium
    verdict = "pass" if result.passed else "FAIL"
    print(f"  {result.id:<8} {verdict}  (feasible: {result.feasible})")
```

```text
2 tasks
  GROWTH   pass  (feasible: True)
  LEAK     pass  (feasible: False)
```

`close_boundaries=True` closes the model's own exchange, sink and demand reactions first, so the inputs and outputs are what the task says they are. A task list is therefore portable between models, which a script full of `setParam` calls is not.
:::
::::

## Task-defined medium

By default neither `checkTasks` nor `check_tasks` closes the model's own exchange reactions: a task's inputs and outputs are added to whatever the model allows. To make the task the whole boundary, close the model first: `closeModel` in RAVEN (what ftINIT does before collecting task-essential reactions), `close_boundaries=True` in raven-toolbox. The task's inputs and outputs are then the only way anything enters or leaves, which makes a task list portable between models and makes an incomplete task look like a broken model.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
noCO2 = tasks(1);
noCO2.id = 'GROWTH-NO-CO2';
keep = ~strcmp(noCO2.outputs, 'CO2[c]');
noCO2.outputs = noCO2.outputs(keep);
noCO2.LBout = noCO2.LBout(keep);
noCO2.UBout = noCO2.UBout(keep);
pair = [tasks(1); noCO2];

boundaries = {'open', 'closed'};
models = {model, closed};
for k = 1:2
    report = checkTasks(models{k}, [], 'printOutput', false, 'taskStructure', pair);
    for i = 1:numel(report.id)
        fprintf('  %-6s  %-14s feasible=%d\n', boundaries{k}, report.id{i}, report.ok(i));
    end
end
```

```text
[Warning: Exchange metabolites should normally not be removed from the model when using checkTasks. Inputs and outputs are defined in the task file instead. Use importModel(file,false) to import a model with exchange metabolites remaining]
  open    GROWTH         feasible=1
  open    GROWTH-NO-CO2  feasible=1
  closed  GROWTH         feasible=1
  closed  GROWTH-NO-CO2  feasible=0
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.tasks import Task

growth = tasks[0]
no_co2 = Task(
    id="GROWTH-NO-CO2",
    description="the same task, without somewhere to put the CO2",
    inputs=growth.inputs,
    outputs=[o for o in growth.outputs if o[0] != "CO2[c]"],
)

for close in (False, True):
    for result in check_tasks(model, [growth, no_co2], close_boundaries=close):
        boundary = "closed" if close else "open"
        print(f"  {boundary:<6}  {result.id:<14} feasible={result.feasible}")
```

```text
  open    GROWTH         feasible=True
  open    GROWTH-NO-CO2  feasible=True
  closed  GROWTH         feasible=True
  closed  GROWTH-NO-CO2  feasible=False
```
:::
::::

The only difference between the two tasks is the CO₂ output. With the model's own exchanges open, both are feasible: the carbon leaves through the model's `co2OUT`, whatever the task says. With them closed, the task without CO₂ is infeasible. A task list written for one reading gives different answers under the other, so check which one it was curated against.

## Task-essential reactions

Essentiality here is defined with respect to a task, not to the objective: remove each candidate reaction and see whether the task passes. ftINIT uses it to decide which reactions must survive an extraction regardless of their expression score.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[~, essentialRxns] = checkTasks(closed, [], 'printOutput', false, ...
    'getEssential', true, 'taskStructure', tasks(1));
fprintf('%d reactions essential for the task\n', sum(essentialRxns));
```

```text
28 reactions essential for the task
```

Task-essential reactions come from `checkTasks` with its `getEssential` flag, returned as a reactions-by-tasks logical matrix and not as a list. Failed tasks and `SHOULD FAIL` tasks are left out of it, since a task that does not pass has no reactions it depends on. `getEssentialRxns` answers for the model's own objective and takes no task.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.tasks import find_task_essential_reactions

result = find_task_essential_reactions(model, tasks[:1], close_boundaries=True)
print(len(result.reactions), "reactions essential for the task")
print(sorted(result.reactions)[:5])
```

```text
28 reactions essential for the task
['ACO', 'ACS', 'ALD6', 'CIT', 'CO2TRANS']
```
:::
::::

## Failing tasks

A failing task is a gap: something the model should be able to do and cannot. Both toolboxes can add reactions from a template until the task passes, which is [Gap-filling](gap-filling.md) applied to tasks.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

<!-- run-examples: skip -->

```matlab
template = readYAMLmodel('smallYeast.yml');   % where the reactions come from
[outModel, addedRxns] = fitTasks(model, template, [], 'taskStructure', tasks);
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.init import fill_tasks
```

`fill_tasks` is the same operation inside the ftINIT pipeline: given the tasks and a source of reactions, it adds back the minimum needed to make every task feasible again.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- A metabolite given by its identifier: task files address metabolites by name, not by identifier, as `name[compartment]`. A task that matches nothing without an error is a task that passes for the wrong reason.
- Missing `SHOULD FAIL` tasks: the tasks that matter most are often the ones the model must not satisfy; without them, a leaking model passes everything.
- The boundary a task ran against is unknown: with the model closed, a task defines its own inputs and does not inherit the model's medium, so a task passing says nothing about whether the model grows on the medium it has. Left open (the default in both toolboxes), the model's own exchanges take part, and a task can pass because of an uptake or secretion it never lists.
:::

## See also

- [Gap-filling](gap-filling.md), which makes a failing task pass.
- [Context-specific models](init.md), tasks that an extraction must preserve.
- [Quality control](quality-control.md), the checks that do not need a task list.
