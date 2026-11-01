# Quality control

A model that loads and solves can be wrong. The checks that apply before a result can be trusted are: whether the structure is sound, whether the reactions balance, whether anything is disconnected, and whether the model can make something out of nothing.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `checkModelStruct` | `check_model` | structural problems |
| `getElementalBalance` | `get_elemental_balance` | mass balance, reaction by reaction |
| `haveFlux` | `find_blocked_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | reactions that cannot carry flux under the current bounds |
| `canExchange` | `analyse_topology` | which metabolites the model can make, or consume, given its medium |
| `findLeakMetabolite` | `find_leak_metabolite`, `gap_report` | can the model make something from nothing |
| `gapReport` | `check_model` + `analyse_topology` | one summary of the gaps |

## Setup

`smallYeastBad.yml` is the small yeast model used throughout this guide, with deliberate errors, which are what these checks detect.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeastBad.yml');
good = readYAMLmodel('smallYeast.yml');
fprintf('%d reactions, %d metabolites\n', numel(model.rxns), numel(model.mets));
```

```text
54 reactions, 52 metabolites
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeastBad.yml")
good = read_yaml_model("smallYeast.yml")
print(len(model.reactions), "reactions,", len(model.metabolites), "metabolites")
```

```text
54 reactions, 52 metabolites
```
:::
::::

## Structural soundness

The first pass checks the model as a data structure: metabolites that no reaction uses, reactions with no metabolites, genes that nothing refers to and a missing objective. The two validators do not check the same list, so their counts differ; [Model structure and identifiers](model-structure.md) sets out what each one covers.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
issues = checkModelStruct(model, 'throwErrors', false);
fprintf('%d issue(s)\n', numel(issues));
```

```text
2 issue(s)
```

The two are a missing objective, reported as `invalid_id` because an objective-less model cannot be written as FBC v2 SBML, and a `cross_reference` finding: one InChI string matches two different metabolite names. The second finding is a consequence of the corrupted formula on `F6P_c` that [Comparison with a trusted model](#comparison-with-a-trusted-model) finds by comparison, as it appears in the annotations.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils import check_model

issues = check_model(model)
print(len(issues), "issue(s)")
for issue in issues[:5]:
    print(f"  {issue.category}: {issue.message}")
```

```text
1 issue(s)
  objective: No reaction has a nonzero objective coefficient.
```
:::
::::

## Reaction balance

An unbalanced reaction can create matter, and one that creates ATP or a redox carrier inflates every prediction the model makes.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
balance = getElementalBalance(model);
fprintf('balanced %d, unbalanced %d, undecidable %d\n', ...
    sum(balance.balanceStatus == 1), ...
    sum(balance.balanceStatus == 0), ...
    sum(balance.balanceStatus < 0));
```

```text
balanced 28, unbalanced 24, undecidable 2
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.utils import get_elemental_balance

balances = get_elemental_balance(model)
counts = {"balanced": 0, "unbalanced": 0, "unknown": 0}
for balance in balances:
    counts[balance.status] += 1
print(counts)

for balance in balances:
    if balance.status == "unbalanced":
        print(f"  {balance.reaction_id}: {balance.imbalance}")
```

```text
{'balanced': 28, 'unbalanced': 24, 'unknown': 2}
  acOUT: {'C': -2.0, 'H': -4.0, 'O': -2.0}
  co2OUT: {'C': -1.0, 'O': -2.0}
  ethOUT: {'C': -2.0, 'H': -6.0, 'O': -1.0}
  glyOUT: {'C': -3.0, 'H': -8.0, 'O': -3.0}
  glcIN: {'C': 6.0, 'H': 12.0, 'O': 6.0}
  o2IN: {'O': 2.0}
  PGI: {'H': 1.0, 'O': 3.0, 'P': 1.0}
  PFK: {'C': 6.0, 'H': 13.0, 'O': 9.0, 'P': 1.0}
  FBP: {'C': 6.0, 'H': 17.0, 'O': 16.0, 'P': 3.0}
  ENO: {'H': -2.0, 'O': -1.0}
  PGL: {'H': 2.0, 'O': 1.0}
  TAL1: {'H': 1.0, 'O': 3.0, 'P': 1.0}
  TKI1TKI2b: {'H': 1.0, 'O': 3.0, 'P': 1.0}
  GPP: {'H': 2.0, 'O': 1.0}
  PDC: {'C': -1.0, 'O': -2.0}
  ADH1: {'C': 2.0, 'H': 6.0, 'O': 1.0}
  ALD6: {'H': 2.0, 'O': 1.0}
  ACS: {'H': 2.0, 'O': 1.0}
  PYC: {'H': 2.0, 'O': 1.0}
  CIT: {'H': 2.0, 'O': 1.0}
  FUM1: {'H': 2.0, 'O': 1.0}
  NADHX: {'H': -8.8, 'O': -4.4}
  FADHX: {'H': -8.799999999999994, 'O': -4.4}
  ATPX: {'H': 2.0, 'O': 1.0}
```

Exchange reactions read as unbalanced by design: they are where mass enters and leaves, so filter them out before judging the number.

`getElementalBalance` returns a struct and prints nothing by default. Its `printUnbalanced` and `printUnparsable` options add warnings for the two failure kinds separately, which distinguishes a reaction that is wrong from one that is undecidable. `rxns` restricts the check to a subset.
:::
::::

## Reactions that cannot carry flux

A reaction that cannot carry flux under the model's current bounds is either a gap, a mistake, or waiting for a medium that is not open. Both functions test the bounds as they are; neither explores other media. It is also the cheapest of these checks to run.

`haveFlux` counts a reaction as active when it carries more than its `cutOff`, `1e-6` by default, which keeps solver noise from reading as flux. It shuffles the order in which reactions are tested, and takes a `seed` so that order is reproducible.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
canCarry = haveFlux(model);
fprintf('%d of %d reactions can carry flux\n', sum(canCarry), numel(model.rxns));
```

```text
2 of 54 reactions can carry flux
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import find_blocked_reactions

blocked = find_blocked_reactions(model)
print(f"{len(model.reactions) - len(blocked)} of {len(model.reactions)} "
      f"reactions can carry flux")
print("blocked:", sorted(blocked)[:5])
```

```text
2 of 54 reactions can carry flux
blocked: ['ACO', 'ACS', 'ADH1', 'ADH2', 'ALD6']
```
:::
::::

`smallYeastBad` has glucose and oxygen uptake open, and the same test on `smallYeast` with that medium finds 52 of 53 reactions active: the 52 blocked here are blocked by the errors that the other checks find. The two that do carry flux, `SDH` and `FRDS2`, are each other's reverse and only cycle (see [Loops in flux ranges](fva.md#loops-in-flux-ranges)).

## Making something from nothing

With every uptake closed, a correct model can produce nothing at all. If it makes a metabolite, some reaction is unbalanced or a loop is creating mass: the most damaging class of error, because such a model grows without a carbon source.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
exchangeRxns = getExchangeRxns(model);   % exchanges, sinks and demands
closed = setParam(model, 'eq', exchangeRxns, 0);
sol = solveLP(closed);
fprintf('closed model feasible: %d\n', ~isempty(sol.x));   % if not, it tests nothing

produced = canExchange(closed, 'produce');
fprintf('%d of %d metabolites producible from nothing\n', ...
    sum(produced), numel(produced));

[~, metabolite] = findLeakMetabolite(closed, 'produce');
fprintf('one leak: %s\n', strjoin(closed.mets(metabolite), ', '));
```

```text
closed model feasible: 1
33 of 52 metabolites producible from nothing
one leak: F6P_c
```

`getExchangeRxns` returns every reaction with metabolites on one side only, so sinks and demands are closed along with the exchanges. A model that is infeasible once closed, for instance because of a forced maintenance flux, cannot show a leak, so check that first. `canExchange` counts the leaks; `findLeakMetabolite` finds one, using as few reactions as possible, which gives a starting point. Both take the direction as their second argument, and `'consume'` asks the mirror-image question: what this model can take up without limit.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.gapfilling import find_leak_metabolite, gap_report

closed = model.copy()
for reaction in closed.boundary:      # exchanges, sinks and demands
    reaction.bounds = (0, 0)
closed.slim_optimize()
print("closed model:", closed.solver.status)   # if not optimal, it tests nothing

produced = gap_report(model).can_produce_without_input
print(f"{len(produced)} metabolite(s) producible from nothing: {sorted(produced)[:5]}")
print("one leak:", find_leak_metabolite(closed, "produce").metabolites)
```

```text
closed model: optimal
33 metabolite(s) producible from nothing: ['ACA_c', 'AC_c', 'AKG_m', 'BIOMASS_c', 'CI_m']
one leak: ['F6P_c', 'GP_c', 'PYR_c']
```

`gap_report` closes every boundary reaction itself, adds an output for every metabolite, and lists in `can_produce_without_input` the ones whose output can carry flux, as `canExchange` does. If the model is infeasible under its own bounds, or once its boundary is closed, it stops with an error that names the reactions with a forced flux; set ATP maintenance to zero first. `gapReport` does the same. `find_leak_metabolite` is the port of `findLeakMetabolite` and does not close anything, so give it the closed copy. It returns a list: more than one id means those metabolites could only be exchanged together. For a manual closure, close `model.boundary`; `model.exchanges` omits sinks and demands because cobrapy does not count them as exchanges, and an open sink is an input. `analyse_topology` answers the connectivity half of the same question without solving an LP. Without `seeds` it takes as seeds the metabolites of every reaction with only substrates and a negative lower bound or only products and a positive upper bound, and without `targets` the metabolites of the first objective reaction; a model with no objective reaction and no `targets` raises `ValueError`.
:::
::::

:::{admonition} Outlets for by-products in leak tests
:class: note

The leak-test functions assume every metabolite can be excreted while the test runs: `canExchange` and `gap_report` add an output reaction for each metabolite they check, and `findLeakMetabolite` and `find_leak_metabolite` take `allowExcretion` (`allow_excretion` in Python) as true by default. A hand-written loop has to add the outlets explicitly. Testing one demand reaction at a time, with no outlet for the by-products, reports zero leaks in this model instead of 33, because a leaking reaction is then blocked by its own stoichiometry.
:::

## Comparison with a trusted model

When a check reports something, comparing against the last version that passed shows whether the finding is new.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
report = diffModels(good, model);
fprintf('equal: %d, %d difference(s)\n', report.equal, numel(report.differences));
fprintf('only in the good model: %d reactions\n', numel(report.rxnsOnlyInA));
fprintf('only in this one:       %d reactions\n', numel(report.rxnsOnlyInB));
```

```text
equal: 0, 11 difference(s)
only in the good model: 1 reactions
only in this one:       2 reactions
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.comparison import diff_models

difference = diff_models(good, model)
print(difference)
```

```text
Models differ (11 differences):
  - reactions only in A (1): ['ethIN']
  - reactions only in B (2): ['ADH2', 'PDC_2']
  - ADH1: coef[ETH_c] A=1 B=2
  - ADH1: bounds A=(-1000.0, 1000.0) B=(0.0, 1000.0)
  - FBP: coef[F6P_c] A=1 B=2
  - PDC: stoichiometry has different mets
  - PFK: coef[F16P_c] A=1 B=2
  - biomassOUT: objective A=1.0 B=0.0
  - glcIN: bounds A=(0.0, 0.0) B=(0.0, 1000.0)
  - o2IN: bounds A=(0.0, 0.0) B=(0.0, 1000.0)
  - met F6P_c: formula A=C6H13O9P B=C6H14O12P2
```
:::
::::

`diffModels` compares two models entry by entry: which reactions are unique to each, and where a shared reaction differs in stoichiometry, bounds, objective coefficient, gene rule or metabolite properties. [Comparing models](comparing.md) uses the same function, here applied to a model and its last good version.

:::{admonition} Troubleshooting
:class: warning

- Judging a model by whether it solves. An unbalanced reaction makes it solve better. Balance first, then believe the growth rate.
- Treating every unbalanced reaction as a bug. Exchange, demand, sink and biomass pseudo-reactions are unbalanced on purpose.
- `unknown` instead of `unbalanced`. A metabolite with no formula, or a polymer formula cobrapy cannot parse, makes the balance undecidable, not wrong. Fill in the formula and check again.
:::

## See also

- [Editing an existing model](editing.md), fixing what these checks find.
- [Model structure and identifiers](model-structure.md), what the structural checks are checking.
- [Growth media and conditions](media.md), closing the medium, as in [Making something from nothing](#making-something-from-nothing).
