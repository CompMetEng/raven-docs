# Tutorial 4: Fix an erroneous model

A GEM covers metabolism at a large scale, and the size makes errors almost inevitable, in a self-built model and in a model from another source. The exercise is a systematic round of quality control on a deliberately broken version of the small yeast model, `smallYeastBad.yml`.

Model validation is iterative, as some errors appear after others are fixed. In the RAVEN approach, the user tries to make a model do something that it should not do, for example create mass from nothing. This finds errors that a check of the intended behaviour misses.

`tutorial4.m` leaves several gaps to fill, and the completed version is `tutorial4_solutions.m`. The `gapReport` function wraps many of these checks, and doing them step by step shows how they work.

The changes are made in code, which avoids several model files. Tutorials 2 and 3 must be completed first, and the exercise assumes familiarity with linear programming.

## Step by step

### 1. Detecting production from nothing

Import the broken model, close all uptake and maximise the sum of the producing exchange reactions. Any non-zero solution is a problem.

```matlab
model = readYAMLmodel('smallYeastBad.yml');
model = setParam(model, 'eq', {'glcIN', 'o2IN'}, [0 0]);
model = setParam(model, 'obj', {'acOUT' 'biomassOUT' 'co2OUT' 'ethOUT' 'glyOUT'}, [1 1 1 1 1]);
sol = solveLP(model);
printFluxes(model, sol.x, true); %Nothing produced, good
```

### 2. Provoking hidden errors

An error can be masked because it costs energy or redox power. Add temporary "free" cofactor reactions (ATP ⇌ ADP + Pᵢ, and similar reactions for NADH and NADPH) to provoke the model, and minimise the sum of fluxes for an interpretable solution:

```matlab
rxns.rxns = {'FREE_ATP'; 'FREE_NADH'; 'FREE_NADPH'};
rxns.equations = {'ATP <=> ADP + phosphate'; 'NAD(+) <=> NADH'; 'NADP(+) <=> NADPH'};
model = addRxns(model, rxns, 2, 'c');
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, [], [], '%rxnID (%rxnName):%flux\n\t%eqn\n');
```

:::{dropdown} Answer to step 2: production of ethanol from nothing
A large amount of ethanol is produced. `ADH1` should produce one unit of ethanol. Change its equation with `model = changeRxns(model, 'ADH1', 'acetaldehyde[c] + NADH[c] => ethanol[c] + NAD(+)[c]', 3);`
:::

### 3. Allowing every metabolite to be excreted

Add a second column to `model.b`, and RAVEN then treats the columns as lower and upper bounds on the equality constraints and any metabolite can be excreted. This exposes errors that need a partner metabolite to be dumped.

```matlab
model.b = [model.b inf(numel(model.b), 1)];
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n');
```

:::{dropdown} Answer to step 3: two unbalanced reactions
The unbalanced reactions in the flux list show that two reactions should each give one unit of product:

- `FBP` should give one unit of F6P. Change its equation to `beta-D-fructofuranose 1,6-bisphosphate[c] => beta-D-fructofuranose 6-phosphate[c] + phosphate[c]`.
- `PFK` should give one unit of F16P. Change its equation to `ATP[c] + beta-D-fructofuranose 6-phosphate[c] => ADP[c] + beta-D-fructofuranose 1,6-bisphosphate[c]`.

Apply each with `changeRxns(model, …, 3)`.
:::

### 4. `canExchange`

Set all uptake and production to 0, drop the excretion column and determine the metabolites that can be consumed without any production:

```matlab
model = setParam(model, 'eq', getExchangeRxns(model), 0);
model.b = model.b(:, 1);
I = canExchange(model, 'consume');
disp(model.mets(I)); %These 12 metabolites can be consumed without any production
```

`canExchange` with `'consume'` reports the metabolites that the model can consume when no production is allowed, and `'produce'` asks the opposite. Allow all uptake, force the uptake of one of the metabolites (here CO2) and study the fluxes (a negative output means input):

```matlab
model.b = [ones(numel(model.b), 1) * -1000 model.b];
model = setParam(model, 'eq', {'co2OUT'}, -1);
sol = solveLP(model);
printFluxes(model, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n'); %Now it works
```

:::{dropdown} Answer to step 4: `PDC` lacks a product
`PDC` converts pyruvate (3 carbons) to acetaldehyde (2 carbons) without another product, and CO2 is missing. `changeRxns` makes the change. As an exercise, add the coefficient of cytosolic CO2 directly to the stoichiometric matrix:

```matlab
Irxn = ismember(model.rxns, 'PDC');
Imet = ismember(model.mets, 'CO2_c');
model.S(Imet, Irxn) = 1; %The coefficient is 1.0
constructEquations(model, Irxn)
```

The solution is infeasible after the change, because the forced uptake of CO2 without any output is not possible.
:::

### 5. Gap-filling against a reference model

`tutorial4.m` also imports a reference model from which reactions are drawn, allows all excretion, and reports the gaps before filling them:

```matlab
model = readYAMLmodel('smallYeastBad.yml');
refModel = readYAMLmodel('smallYeast.yml');
model.b = [model.b inf(numel(model.b), 1)];
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n');
I = canExchange(model, 'consume');
disp(model.mets(I));
gapReport(model, {refModel});

[newConnected, cannotConnect, addedRxns, newModel] = fillGaps(model, {refModel}, false);
disp(addedRxns);
disp(newConnected);
disp(cannotConnect);
```

`gapReport` automates this quality-control workflow, and `fillGaps` adds reactions from the reference model (here the small yeast model of Tutorial 3) to connect the remaining gaps.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial4.m
:language: matlab
```
