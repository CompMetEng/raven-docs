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

The import of the incomplete model gives a RAVEN warning that some internal metabolites are used in one reaction, so the sole feasible solution is zero flux. When `sol.f` equals zero, the problem cannot be solved, and the uptake and excretion of all necessary metabolites are added to the model before `solveLP` is run again.

### 2. Internal and external metabolites

Under the steady-state assumption, the production rate of each internal metabolite equals its consumption rate. A metabolite that takes part in one reaction can therefore carry no flux. Exchange reactions, which involve external (boundary) metabolites that do not need to be mass-balanced, remove this restriction.

### 3. Adding the glycolysis reactions and exchanges

The remaining reactions of glycolysis are added. Exchange and transport reactions are then added, and the cell can take up sucrose and excrete pyruvate and water.

`importModel` is run again to check the structure during the build.

### 4. Handling cofactors and defining the objective

Two problems remain:

- NAD⁺ must be regenerated from NADH. The model is extended, for example with ethanol production through pyruvate decarboxylase and alcohol dehydrogenase, or exchange reactions for NAD⁺ and NADH are added as an approximation.
- The ATP yield must be measured. A "fake" ATP hydrolysis reaction is added and its flux is maximised. Production must match consumption, so the flux reports how much ATP the network can make. The direction is checked, because a wrong direction allows free ATP synthesis.

The sucrose uptake is limited to one unit, and the ATP-hydrolysis reaction is set as the objective to maximise.

### 5. Solving

When the model is complete, the linear programming problem is solved and the fluxes are printed. The completed model is `small.yml`, which the solutions script reads directly:

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
