# Building a model from scratch

A hand-built model starts with metabolites, a reaction, a gene association and the exchanges that let material in and out, and ends with a model that carries flux. The same steps test an idea before an automated reconstruction is involved.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `addMets` | `Metabolite` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | add metabolites |
| `addRxns` | `add_reactions_from_equations` | add reactions from equation strings |
| `addGenesRaven` | auto-created from the GPR {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | add genes |
| `addExchangeRxns` | `Model.add_boundary` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | add exchange reactions |
| `constructEquations` | `Reaction.reaction` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read the equations back |

In both toolboxes, write a reaction as an equation string and let the toolbox derive the stoichiometry, not a column of the stoichiometric matrix by hand.

## Setup

[`empty.xml`](../data/empty.xml) is RAVEN's starter model: four metabolites (sucrose, glucose, fructose and water) and one reaction, invertase, which splits sucrose into glucose and fructose. Everything is in one compartment, `e`.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = importModel('empty.xml');
fprintf('%d reactions, %d metabolites\n', numel(model.rxns), numel(model.mets));
eqn = constructEquations(model);
fprintf('%s\n', eqn{1});
```

```text
The model contains 0 errors and 1 warnings.

[Warning: The following fields have prefixes removed from all entries. If this is undesired, run importModel with removePrefix as false. Example: importModel('filename.xml',[],false); model.rxns (R_ prefix) model.mets (M_ prefix)]
1 reactions, 4 metabolites
sucrose[e] + H2O[e] => glucose[e] + fructose[e]
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.io import read_sbml_model

model = read_sbml_model("empty.xml")
print(len(model.reactions), "reactions,", len(model.metabolites), "metabolites")
for reaction in model.reactions:
    print(f"  {reaction.id}: {reaction.reaction}")
```

```text
1 reactions, 4 metabolites
  r1: m1 + m4 --> m2 + m3
```
:::
::::

## Adding metabolites

Hexokinase is added next, so the model needs ATP, ADP and glucose-6-phosphate first.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
metsToAdd.mets = {'m5', 'm6', 'm7'};
metsToAdd.metNames = {'ATP', 'ADP', 'glucose-6-phosphate'};
metsToAdd.compartments = 'e';
metsToAdd.metFormulas = {'C10H12N5O13P3', 'C10H12N5O10P2', 'C6H11O9P'};
model = addMets(model, metsToAdd);
fprintf('%d metabolites\n', numel(model.mets));
```

```text
7 metabolites
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra import Metabolite

model.add_metabolites([
    Metabolite("m5", name="ATP", formula="C10H12N5O13P3", compartment="e"),
    Metabolite("m6", name="ADP", formula="C10H12N5O10P2", compartment="e"),
    Metabolite("m7", name="glucose-6-phosphate", formula="C6H11O9P", compartment="e"),
])
print(len(model.metabolites), "metabolites")
```

```text
7 metabolites
```

Give every metabolite a formula and a compartment when it is added. [Quality control](quality-control.md) checks against both, and adding them later means revisiting every reaction written in between.
:::
::::

## Adding a reaction

The equation string is the same in both toolboxes: `<=>` for a reversible reaction, `=>` for an irreversible one.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
rxnsToAdd.rxns = {'HEX1'};
rxnsToAdd.rxnNames = {'hexokinase'};
rxnsToAdd.equations = {'m2 + m5 => m7 + m6'};
rxnsToAdd.grRules = {'YFR053C'};
model = addRxns(model, rxnsToAdd, 'eqnType', 1, 'allowNewGenes', true);

idx = getIndexes(model, 'HEX1', 'rxns');
eqn = constructEquations(model, {'HEX1'});
fprintf('%s\n', eqn{1});
fprintf('bounds: [%g %g], genes: %s\n', model.lb(idx), model.ub(idx), ...
    model.grRules{idx});
```

```text
New genes added to the model:
YFR053C
glucose[e] + ATP[e] => ADP[e] + glucose-6-phosphate[e]
bounds: [0 Inf], genes: YFR053C
```

`eqnType` specifies how the equation is written: `1` or `"id"` matches metabolites against `model.mets`, `2` or `"name"` against `model.metNames` with `compartment` deciding where they go, and `3` or `"name[comp]"` reads the compartment from the token itself.

`allowNewGenes` is needed because `YFR053C` is not in the model. Both `allowNewGenes` and `allowNewMets` default to `false`, so `addRxns` refuses anything it does not recognise unless the option is set, and a mistyped identifier is an error, not a new entity. `allowNewMets` also accepts a string, used as the prefix for the ids it generates. Adding metabolites with `addMets` first carries more annotation than `addRxns` can infer.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.manipulation import add_reactions_from_equations

add_reactions_from_equations(model, [
    {
        "id": "HEX1",
        "name": "hexokinase",
        "equation": "m2 + m5 => m7 + m6",
        "gene_reaction_rule": "YFR053C",
    },
])

hex1 = model.reactions.get_by_id("HEX1")
print(hex1.reaction)
print("bounds:", hex1.bounds, "genes:", hex1.gene_reaction_rule)
```

```text
m2 + m5 --> m6 + m7
bounds: (0.0, 1000.0) genes: YFR053C
```

The arrow sets the bounds, so an irreversible reaction needs no `bounds` key; passing `bounds` overrides it. `<=>` is reversible, and `-->`, `->` and `=>` are accepted for an irreversible reaction.

`allow_new_genes` and `allow_new_mets` both default to `True` here, the opposite of the MATLAB defaults, so a gene named in the rule is created without a separate step and without a message. That removes the `addGenesRaven` call MATLAB needs, and a typo becomes a new gene without an error. Set them to `False` once the model's metabolites and genes are all defined.
:::
::::

## Adding exchanges

Without boundary reactions nothing can enter or leave, so there is no net uptake, secretion or growth. Internal cycles can carry flux even without boundary reactions (see [Flux variability and alternative optima](fva.md#loops-in-flux-ranges)), and under the steady-state assumption a metabolite that appears in only one reaction blocks that reaction. Exchange reactions are the boundary.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = addExchangeRxns(model, 'both', 'mets', model.mets);
fprintf('%d reactions\n', numel(model.rxns));
```

```text
NOTE: The exchange reactions are assigned to the first compartment
9 reactions
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
for metabolite in list(model.metabolites):
    model.add_boundary(metabolite, type="exchange")

print(len(model.reactions), "reactions")
print(sorted(rxn.id for rxn in model.exchanges))
```

```text
9 reactions
['EX_m1', 'EX_m2', 'EX_m3', 'EX_m4', 'EX_m5', 'EX_m6', 'EX_m7']
```

`add_boundary` works out that `e` is the external compartment. It refuses when nothing looks external, which is the usual reason it fails on a small hand-built model: give a compartment a recognisable name, or build the exchange as an ordinary reaction with a single metabolite. `type="demand"` and `type="sink"` add the other two kinds of boundary reaction, which cobrapy tracks in separate collections.
:::
::::

## Flux check

Solving the model shows whether the reactions assembled so far can carry flux at all.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = setParam(model, 'obj', 'HEX1', 1);
sol = solveLP(model);
fprintf('HEX1 flux: %.2f\n', sol.x(getIndexes(model, 'HEX1', 'rxns')));
```

```text
HEX1 flux: 1000.00
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
model.objective = "HEX1"
solution = model.optimize()
print(f"HEX1 flux: {solution.fluxes['HEX1']:.2f}")
```

```text
HEX1 flux: 1000.00
```
:::
::::

:::{admonition} Troubleshooting
:class: warning

- A typo creates a metabolite. The defaults differ: `add_reactions_from_equations` creates unrecognised metabolites and genes, while `addRxns` refuses them unless `allowNewMets` and `allowNewGenes` are set. So `m7` and `M7` become two different things in Python and an error in MATLAB. Set `allow_new_mets=False` and `allow_new_genes=False` once everything is defined.
- No exchange reactions. Nothing can be taken up or secreted, so growth is zero, with no error to explain why.
- A model with no external compartment. `add_boundary` cannot guess one, and RAVEN's `addExchangeRxns` adds exchanges for internal metabolites without warning, opening the model to uptake and secretion of intermediates.
:::

## See also

- [Editing an existing model](editing.md), changing the contents of a model.
- [Quality control](quality-control.md), checking a newly built model.
- [Reading and writing models](io.md), saving it.
