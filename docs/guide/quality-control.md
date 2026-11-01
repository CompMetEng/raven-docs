# Quality control

A model that loads and solves can be wrong. Four checks come before a result is trusted: the structure is sound, the reactions balance, no part of the network is disconnected, and the model cannot make mass from nothing.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `checkModelStruct` | `check_model` | structural problems |
| `getElementalBalance` | `get_elemental_balance` | mass balance of each reaction |
| `haveFlux` | `find_blocked_reactions` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | reactions that cannot carry flux under the current bounds |
| `canExchange` | `gap_report` | metabolites that the model can make or consume with its medium |
| `findLeakMetabolite` | `find_leak_metabolite`, `gap_report` | mass produced from nothing |
| `gapReport` | `gap_report` | one summary of the gaps |

## Setup

`smallYeastBad.yml` is the small yeast model of this guide with deliberate errors, which the checks detect.

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

The first pass checks the model as a data structure: metabolites that no reaction uses, reactions without metabolites, genes that nothing refers to and a missing objective. The two validators check different lists, so their counts differ. [Model structure and identifiers](model-structure.md) describes what each covers.

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

The two findings are a missing objective, reported as `invalid_id` because a model without an objective cannot be written as FBC version 2 SBML, and a `cross_reference` finding: one InChI string matches two metabolite names. The second finding follows from the corrupted formula of `F6P_c`, which [Comparison with a trusted model](#comparison-with-a-trusted-model) finds by comparison, and which appears in the annotations.
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

An unbalanced reaction can create matter. A reaction that creates ATP or a redox carrier inflates every prediction of the model.

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

Exchange reactions are unbalanced by design, because they are where mass enters and leaves. They are filtered out before the number is judged.

`getElementalBalance` returns a struct and prints nothing by default. `printUnbalanced` and `printUnparsable` add warnings for the two failure kinds separately, which separates a wrong reaction from an undecidable one. `rxns` restricts the check to a subset.
:::
::::

## Reactions that cannot carry flux

A reaction that cannot carry flux under the current bounds is a gap, an error, or a reaction that waits for a medium that is not open. Both functions test the bounds as they are and do not explore other media. This is the cheapest of the checks.

`haveFlux` counts a reaction as active when its flux exceeds `cutOff`, which is `1e-6` by default and keeps solver noise from counting as flux. It tests the reactions in shuffled order, and `seed` makes the order reproducible.

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

`smallYeastBad` has glucose and oxygen uptake open. The same test on `smallYeast` with that medium finds 52 of 53 reactions active, and the 52 blocked reactions here are blocked by the errors that the other checks find. The two reactions that carry flux, `SDH` and `FRDS2`, are the reverse of each other and form a cycle ([Loops in flux ranges](fva.md#loops-in-flux-ranges)).

## Mass from nothing

A correct model with every uptake closed produces nothing. When it makes a metabolite, a reaction is unbalanced or a loop creates mass. This is the most damaging class of error, because such a model grows without a carbon source.

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

`getExchangeRxns` returns every reaction with metabolites on one side, so the sinks and demands are closed together with the exchange reactions. A model that is infeasible when closed, for instance because of a forced maintenance flux, cannot show a leak. The feasibility of the closed model should be checked before the leak test. `canExchange` counts the leaks. `findLeakMetabolite` finds one leak with the smallest total flux, and `minNrFluxes` minimises the number of reactions instead. The leak is a starting point. Both take the direction as the second argument, and `'consume'` asks the reverse question: which metabolites the model can take up without limit.
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

`gap_report` closes every boundary reaction, adds an output reaction for every metabolite, and lists in `can_produce_without_input` the metabolites whose output can carry flux, as `canExchange` does. When the model is infeasible with its own bounds or with the closed boundary, the function stops with an error that names the reactions with a forced flux. ATP maintenance should be set to zero before the call. `gapReport` behaves the same way.

`find_leak_metabolite` is the port of `findLeakMetabolite` and closes nothing, so it receives the closed copy. It returns a list, and more than one identifier means that the metabolites can be exchanged together. A manual closure closes `model.boundary`. `model.exchanges` omits sinks and demands, because cobrapy does not count them as exchanges, and an open sink is an input.

`analyse_topology` answers the connectivity part of the question without solving a linear program, and it requires a `templates` argument. Without `seeds`, the seeds are the metabolites of every reaction that has substrates alone and a negative lower bound or products alone and a positive upper bound. Without `targets`, the targets are the metabolites of the first objective reaction. A model without an objective reaction and without `targets` raises `ValueError`.
:::
::::

:::{admonition} Outlets for by-products in leak tests
:class: note

The leak-test functions assume that every metabolite can be excreted during the test. `canExchange` and `gap_report` add an output reaction for each metabolite that they check, and `findLeakMetabolite` and `find_leak_metabolite` take `allowExcretion` (`allow_excretion` in Python), which is true by default. A hand-written loop adds the outlets explicitly. Testing one demand reaction at a time without outlets for the by-products reports zero leaks in this model where 33 are present, because the stoichiometry of a leaking reaction blocks it.
:::

## Comparison with a trusted model

When a check reports a finding, a comparison with the last version that passed shows whether the finding is new.

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

`diffModels` compares two models entry by entry. It reports the reactions that are unique to each model and the shared reactions that differ in stoichiometry, bounds, objective coefficient, gene rule or metabolite properties. [Comparing models](comparing.md) uses the same function, and here it compares a model with its last good version.

:::{admonition} Troubleshooting
:class: warning

- A model is judged by whether it solves. An unbalanced reaction can improve the solve. Check the balance first, and trust the growth rate afterwards.
- Every unbalanced reaction is treated as an error. Exchange, demand, sink and biomass pseudoreactions are unbalanced by design.
- The result is `unknown`. A metabolite without a formula, or a polymer formula that cobrapy cannot parse, makes the balance undecidable. Add the formula and repeat the check.
:::

## See also

- [Editing an existing model](editing.md): fixing what the checks find.
- [Model structure and identifiers](model-structure.md): what the structural checks cover.
- [Growth media and conditions](media.md): closing the medium, as in [Mass from nothing](#mass-from-nothing).
