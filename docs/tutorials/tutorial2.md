# Tutorial 2: Construct a functional small model

This exercise deals with a small glycolysis model in RAVEN format and shows the
most basic aspects of stoichiometric modelling: building a model from scratch,
setting parameters and running simple simulations.

You start from `empty.xml` (an incomplete model containing the first reaction of
glycolysis) and extend it until it forms a functional network. The companion
script `tutorial2_solutions.m` reads the provided solution model `small.yml`
directly with `readYAMLmodel`.

:::{admonition} Goal
:class: question
Build a model of glycolysis and answer: **how many units of ATP can be
generated from one unit of sucrose?**
:::

## Step by step

### 1. Import the starter model

```matlab
smallModel = importModel('empty.xml');
sol = solveLP(smallModel);
printFluxes(smallModel, sol.x, true);
```

When you import the (incomplete) model, RAVEN warns that some internal
metabolites are used in only one reaction, so the only feasible solution is zero
flux. If `sol.f` equals zero the problem is not solvable, and you need to ensure
that uptake and excretion of all necessary metabolites are added to the model
before running `solveLP` again.

### 2. Understand internal vs. external metabolites

Under the steady-state assumption, the production rate of each *internal*
metabolite must equal its consumption rate. A metabolite that participates in
only one reaction can therefore carry no flux. The fix is to introduce
**external (boundary) metabolites**, which need not be mass-balanced. Reactions
involving them are **exchange reactions**.

### 3. Add the glycolysis reactions and exchanges

Add the remaining reactions of glycolysis, then add exchange and transport
reactions so that the cell can take up sucrose and excrete pyruvate and water.

Re-import the model with `importModel` to check the structure as you go.

### 4. Handle cofactors and define the objective

Two problems remain:

- **Regenerating NAD⁺ from NADH.** Either extend the model (e.g. ethanol
  production via pyruvate decarboxylase + alcohol dehydrogenase) or add "fake"
  exchange reactions for NAD⁺/NADH.
- **Measuring ATP yield.** Add a "fake" ATP hydrolysis reaction and maximise its
  flux: because production must match consumption, this reports how much ATP
  the network can make. Watch the directionality so you don't accidentally allow
  free ATP synthesis.

Constrain the sucrose uptake to one unit and set the ATP-hydrolysis reaction as
the objective to maximise.

### 5. Solve

Once the model is complete, solve the linear programming problem and print the
fluxes. The completed model is provided as `small.yml`, which the solutions
script reads directly:

```matlab
smallModel = readYAMLmodel('small.yml');
sol = solveLP(smallModel);
printFluxes(smallModel, sol.x, true);                                          % exchange fluxes
printFluxes(smallModel, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n');  % all fluxes
```

See [Tutorial 2 on the RAVEN wiki](https://github.com/SysBioChalmers/RAVEN/wiki/Tutorials)
for more details and the worked answer.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial2.m
:language: matlab
```
