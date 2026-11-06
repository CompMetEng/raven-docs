# Metabolic tasks

A metabolic task states something the model must be able to do: "given glucose and oxygen, produce biomass", "make ATP", or "do not produce something from nothing". Tasks test a reconstruction against biology. ftINIT repairs against them after it reduces a model.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `parseTaskList` | `parse_task_list` | read a task-list file |
| `checkTasks` | `check_tasks` | run the tasks against a model |
| `checkTasks` (`getEssential`) | `find_task_essential_reactions` | reactions that a task requires |
| `fitTasks` | `fill_tasks` | add reactions until the tasks pass |

## The file format

A task list is a tab-separated table with one row per task. The columns hold the inputs, the outputs, the equations that must carry flux, and the bounds of each. [`tasks.txt`](../data/tasks.txt) holds two tasks for `smallYeast.yml`:

```text title="tasks.txt, abridged; the real file keeps every column"
	ID	DESCRIPTION	SHOULD FAIL	IN	IN LB	IN UB	OUT	OUT LB	OUT UB	…
	GROWTH	Growth on glucose		alpha-D-glucose[c];O2[c]	0	1000	biomass[c]	0.01	1000	…
							CO2[c]	0	1000	…
							acetate[c]	0	1000	…
	LEAK	Biomass from nothing	1				biomass[c]	0.01	1000	…
```

Two requirements of the format apply to MATLAB:

- The header row starts with an empty cell. `parseTaskList` treats the leading rows whose first cell is not empty as comments and takes the first row with an empty first cell as the header, so a file without the leading tab has no header row.
- The header row has a column named `ID`, which is the sole required column. A file without a row that starts with an empty cell raises `RAVEN:badInput` with the message that the TASKS sheet must have a column named ID.

`parse_task_list` of raven-toolbox accepts the file with or without the leading empty cell, so a missing cell is noticed when the MATLAB example runs. `tasks.txt` has the full set of columns, and the columns after `OUT UB` are blank.

Metabolites are given as `name[compartment]` with the metabolite name. Several metabolites go in one cell, separated by `;`, and the bound columns apply to all of them. A metabolite with its own bounds goes on a continuation row, which is a row without an `ID` that adds its inputs and outputs to the task above it. `GROWTH` uses this to require at least 0.01 units of biomass while CO₂ and acetate are unrestricted. With a lower bound of 0 on biomass, the zero flux would pass the task. The value 0.01 is illustrative, and any positive lower bound has the same effect.

`SHOULD FAIL` marks a task that the model must fail. The second task asks for biomass with nothing supplied, which a correct model cannot do, so failing it is a pass.

When the exchange reactions of the model are closed ([Task-defined medium](#task-defined-medium)), `GROWTH` lists glucose and oxygen as inputs and biomass, CO₂ and acetate as outputs. Growth must release its carbon, as CO₂ and, in this small model, as acetate. A task without CO₂ is infeasible, which looks like a broken model and is a broken task.

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

`report.ok` is true for both tasks, for opposite reasons: `GROWTH` had to pass and did, and `LEAK` had to fail and did.

`checkTasks` prints its verdicts unless `printOutput` is off, as here, and `printOnlyFailed` limits the print-out to the failures. The verdicts in `report` form a structure that a test can use.

The parsed tasks passed as `taskStructure` make the second argument, the task file, unnecessary. `runParallel` evaluates the tasks in parallel workers. It defaults to `false`, because starting a pool takes longer than a short task list saves, and it matters for a genome-scale list.
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

`close_boundaries=True` first closes the exchange, sink and demand reactions of the model, so the inputs and outputs are those that the task defines. A task list is therefore portable between models, which a script of `setParam` calls is not.
:::
::::

## Task-defined medium

By default, neither `checkTasks` nor `check_tasks` closes the exchange reactions of the model, and the inputs and outputs of a task are added to what the model allows. The task becomes the whole boundary when the model is closed first, with `closeModel` in RAVEN (which ftINIT does before it collects the task-essential reactions) or with `close_boundaries=True` in raven-toolbox. The inputs and outputs of the task are then the sole way for anything to enter or leave. A task list is then portable between models, and an incomplete task looks like a broken model.

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

The tasks differ in the CO₂ output. With the exchange reactions of the model open, both are feasible, because the carbon leaves through `co2OUT` of the model whatever the task says. With them closed, the task without CO₂ is infeasible. A task list written for one reading gives different answers under the other, so the boundary that the list was curated against is checked.

## Task-essential reactions

Essentiality here refers to a task. Each candidate reaction is removed, and the task is tested again. ftINIT uses the result to determine which reactions must remain in an extraction regardless of their expression score.

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

`checkTasks` with its `getEssential` flag returns the task-essential reactions as a logical matrix of reactions by tasks. Failed tasks and `SHOULD FAIL` tasks are left out, because a task that does not pass has no reactions that it depends on. `getEssentialRxns` answers for the objective of the model and takes no task.
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

A failing task is a gap, something that the model should be able to do and cannot. Both toolboxes add reactions from a template until the task passes, which is [Gap-filling](gap-filling.md) applied to tasks.

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

`fill_tasks` is the same operation inside the ftINIT pipeline. Given the tasks and a source of reactions, it adds the reactions of lowest cost that make each task feasible again.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- A metabolite is given by its identifier. Task files address metabolites by name, as `name[compartment]`. A task that matches nothing and raises no error passes for the wrong reason.
- `SHOULD FAIL` tasks are missing. The tasks that matter most are often those that the model must not satisfy, and a leaking model passes every other task.
- The boundary of a task run is unknown. With the model closed, a task defines its own inputs and does not inherit the medium of the model, so a passed task does not show that the model grows on its medium. With the model open, which is the default in both toolboxes, the exchange reactions of the model take part, and a task can pass because of an uptake or secretion that it does not list.
:::

## See also

- [Gap-filling](gap-filling.md): making a failing task pass.
- [Context-specific models](init.md): the tasks that an extraction must preserve.
- [Quality control](quality-control.md): the checks that need no task list.
