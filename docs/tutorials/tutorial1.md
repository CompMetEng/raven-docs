# Tutorial 1: Import a GEM, set parameters and run FBA

The tutorial loads a genome-scale metabolic model (GEM), sets reaction constraints and an objective function, runs a flux balance analysis (FBA) and visualises the fluxes.

The example uses the GEM of the filamentous fungus *Penicillium chrysogenum* (`iAL1006`), which is the SBML file `iAL1006 v1.00.xml`.

The import performs structural checks. With this model there is one warning: the formula of the metabolite LPE cannot be parsed. The warning is expected and can be ignored.

## Step by step

### 1. Importing the model

`importModel` imports the model from SBML and performs structural checks, for example for incorrectly written equations and illegal characters. The `false` flag imports the exchange reactions in their closed form, which is not suitable for simulation and suits quality-control steps.

```matlab
model = importModel('iAL1006 v1.00.xml', false);
printModelStats(model, true, true);   % list dead-end reactions / unconnected mets
```

The model contains 1632 reactions, 1395 metabolites and 1006 genes.

### 2. Simplifying the model

Mass balancing is done around the internal metabolites. Remove the unconstrained (boundary) metabolites that let the system take up or excrete compounds before simulation. `simplifyModel` makes models smaller, for example by grouping linear reactions and by deleting reactions that cannot carry flux. The call below deletes the unconstrained metabolites, the reactions constrained to zero flux (mainly the uptake of non-standard carbon sources) and the dead-end reactions, and leaves linear reactions ungrouped.

```matlab
model = simplifyModel(model, true, false, true, true);
```

The simplified model contains 1305 reactions, 1037 metabolites and 1006 genes.

### 3. Setting constraints and an objective, and solving

The first validation is the theoretical yield of CO₂ from glucose. The supplied model allows the uptake of phosphate, sulfate, NH3, O2 and the cofactor precursors thiamin and pimelate. `setParam` limits glucose uptake to 1 `mmol/gDW/h`, blocks ethanol uptake and sets CO₂ production as the objective.

```matlab
model = setParam(model, 'ub', {'glcIN' 'etohIN'}, [1 0]);
model = setParam(model, 'obj', {'co2OUT'}, 1);
sol = solveLP(model);
printFluxes(model, sol.x, true, 10^-7);   % exchange fluxes only
```

The solution structure contains `.f` (the objective value), `.stat` (1 on success) and `.x` (the flux through each reaction). The system takes up 1 glucose and 6 O₂ and produces 6 CO₂ and 6 H₂O.

### 4. Removing loops

Printing all fluxes (the third argument is `false`) shows many reactions at ±1000 because of loops in the solution. `1` as the second argument of `solveLP` minimises the sum of fluxes and gives a result that is easier to interpret.

```matlab
printFluxes(model, sol.x, false, 10^-7);   % all fluxes
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, 10^-7);
```

The solution that minimises the sum of fluxes has far fewer active reactions than the first solution.

### 5. Optimising for growth and comparing carbon sources

For growth, change the objective to biomass production (`bmOUT`). The growth rate on glucose is 0.084/h, and the system also requires sulfate, phosphate, NH3, thiamin and pimelate. Compare with growth on ethanol at a molar flux three times as large, because ethanol has 2 carbons and glucose has 6. The `eq` flag sets the lower and the upper bound to the same value.

```matlab
model = setParam(model, 'obj', {'bmOUT'}, 1);
sol = solveLP(model, 1);
printFluxes(model, sol.x, true, 10^-7);

% Growth on ethanol instead of glucose (3× the molar flux, 2 C vs 6 C)
modelETH = setParam(model, 'eq', {'glcIN' 'etohIN'}, [0 3]);
solETH = solveLP(modelETH, 1);
printFluxes(modelETH, solETH.x, true, 10^-7);
```

### 6. Investigating the changes

`compareFluxes` takes two flux distributions and reports every reaction whose flux changed, with the largest change first. It labels the reactions that were turned on, turned off or reversed in direction. The first call considers changes above 0.5 `mmol/gDW/h`, and the second restricts the view to ATP metabolism by naming the metabolites of interest.

```matlab
res = compareFluxes(modelETH, sol.x, solETH.x, 'cutoff', 0.5);
compareFluxes(modelETH, sol.x, solETH.x, 'cutoff', 0.4, 'metaboliteList', {'ATP'});
```

The printed table has at most 20 rows. `res.changed` holds every changed reaction, and `res.turnedOn`, `res.turnedOff` and `res.flipped` list the reactions that switched state.

The comparison shows the flux redistributions that produce different phenotypes. On glucose, ATP is generated in glycolysis, and on ethanol the generation involves acetate.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial1.m
:language: matlab
```
