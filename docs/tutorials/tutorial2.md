# Tutorial 2: Construct a functional small model

The exercise builds a small model of glycolysis in RAVEN format and covers the basic aspects of stoichiometric modelling: building a model from scratch, setting parameters and running basic simulations.

The start is `empty.xml`, an incomplete model with the first reaction of glycolysis, which is extended to a functional network. The companion script `tutorial2_solutions.m` reads the solution model `small.yml` directly with `readYAMLmodel`.

The task is to build a model of glycolysis and to determine how many units of ATP can be generated from one unit of sucrose.

## Step by step

### 1. Importing the starter model

```matlab
smallModel = importModel('empty.xml');
sol = solveLP(smallModel);
printFluxes(smallModel, sol.x, true);
```

The import of the incomplete model gives a RAVEN warning that some internal metabolites are used in one reaction, so the sole feasible solution is zero flux. When `sol.f` equals zero, the problem cannot be solved, and the uptake and excretion of all necessary metabolites must be added to the model before `solveLP` is run a second time.

### 2. Internal and external metabolites

Under the steady-state assumption, the production rate of each internal metabolite equals its consumption rate. A metabolite that takes part in one reaction can therefore carry no flux. Exchange reactions, which involve external (boundary) metabolites that do not need to be mass-balanced, remove this restriction.

### 3. Adding the glycolysis reactions and exchanges

Add the remaining reactions of glycolysis. Then add exchange and transport reactions, so that the cell can take up sucrose and excrete pyruvate and water.

Run `importModel` on the file again to check the structure during the build.

### 4. Handling cofactors and defining the objective

Two problems remain:

- NAD⁺ must be regenerated from NADH. Extend the model, for example with ethanol production through pyruvate decarboxylase and alcohol dehydrogenase, or add exchange reactions for NAD⁺ and NADH as an approximation.
- The ATP yield must be measured. Add a "fake" ATP hydrolysis reaction and maximise its flux. Production must match consumption, so the flux reports how much ATP the network can make. Check the direction, because a wrong direction allows free ATP synthesis.

Limit the sucrose uptake to one unit, and set the ATP-hydrolysis reaction as the objective to maximise.

### 5. Solving

When the model is complete, solve the linear programming problem and print the fluxes. The completed model is `small.yml`, which the solutions script reads directly:

```matlab
smallModel = readYAMLmodel('small.yml');
sol = solveLP(smallModel);
printFluxes(smallModel, sol.x, true);                                          % exchange fluxes
printFluxes(smallModel, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n');  % all fluxes
```

The worked answer is `tutorial2_solutions.m` in the `tutorials` folder of RAVEN.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial2.m
:language: matlab
```
