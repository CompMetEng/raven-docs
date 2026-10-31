# Tutorial 4: Fix an erroneous model

A GEM is powerful because of its size, and the same size makes errors almost inevitable, in a self-built model and in a model from another source. This exercise is a systematic round of quality control on a deliberately broken version of the small yeast model, `smallYeastBad.yml`.

Model validation is iterative: some errors only appear once others are fixed. The RAVEN philosophy is that trying to make a model do something it should not (for example create mass from nothing) is more valuable than testing only for what it should do.

`tutorial4.m` leaves several gaps to fill; the completed version is in `tutorial4_solutions.m`. Many of these checks are also wrapped by the `gapReport` function, but doing them step by step is far more instructive.

The changes are made here in code, which avoids having several model files. It is assumed that Tutorials 2–3 are completed and that the reader is familiar with linear programming.

## Step by step

### 1. Detecting production from nothing

Import the broken model, close all uptake, and maximise the sum of the producing exchange reactions. Any non-zero solution is a problem.

```matlab
model = readYAMLmodel('smallYeastBad.yml');
model = setParam(model, 'eq', {'glcIN', 'o2IN'}, [0 0]);
model = setParam(model, 'obj', {'acOUT' 'biomassOUT' 'co2OUT' 'ethOUT' 'glyOUT'}, [1 1 1 1 1]);
sol = solveLP(model);
printFluxes(model, sol.x, true); %Nothing produced, good
```

### 2. Provoking hidden errors

An error may be masked because it costs energy or redox power. Add temporary "free" cofactor reactions (ATP ⇌ ADP + Pᵢ, and similar for NADH and NADPH) to provoke the model, then minimise the sum of fluxes for an interpretable solution:

```matlab
rxns.rxns = {'FREE_ATP'; 'FREE_NADH'; 'FREE_NADPH'};
rxns.equations = {'ATP <=> ADP + phosphate'; 'NAD(+) <=> NADH'; 'NADP(+) <=> NADPH'};
model = addRxns(model, rxns, 2, 'c');
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, [], [], '%rxnID (%rxnName):%flux\n\t%eqn\n');
```

??? success "Answer to Question 2: production of ethanol from nothing"
    A large amount of ethanol is produced. `ADH1` should only produce one unit of ethanol. Change its equation with `model = changeRxns(model, 'ADH1', 'acetaldehyde[c] + NADH[c] => ethanol[c] + NAD(+)[c]', 3);`

### 3. Allowing every metabolite to be excreted

Add a second column to `model.b` so that RAVEN treats it as lower and upper bounds on the equality constraints and any metabolite can be excreted. This exposes errors that need a partner metabolite to be dumped.

```matlab
model.b = [model.b inf(numel(model.b), 1)];
sol = solveLP(model, 1);
printFluxes(model, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n');
```

??? success "Answer to Question 3: two unbalanced reactions"
    The unbalanced reactions in the flux list show that two reactions should each result in only one unit of product:

    - `FBP` should give one unit of F6P: change it to `beta-D-fructofuranose 1,6-bisphosphate[c] => beta-D-fructofuranose 6-phosphate[c] + phosphate[c]`.
    - `PFK` should give one unit of F16P: change it to `ATP[c] + beta-D-fructofuranose 6-phosphate[c] => ADP[c] + beta-D-fructofuranose 1,6-bisphosphate[c]`.

    Apply each with `changeRxns(model, …, 3)`.

### 4. `canExchange`

Set all uptakes and production to 0, drop the excretion column again, and check which metabolites can be consumed without any production:

```matlab
model = setParam(model, 'eq', getExchangeRxns(model), 0);
model.b = model.b(:, 1);
I = canExchange(model, 'consume');
disp(model.mets(I)); %These 12 metabolites can be consumed without any production
```

`canExchange` with `'consume'` reports the metabolites the model can consume even when no production is allowed; `'produce'` asks the opposite. Allow all uptake again, then force the uptake of one of them (here CO2), and study the fluxes (a negative output means input):

```matlab
model.b = [ones(numel(model.b), 1) * -1000 model.b];
model = setParam(model, 'eq', {'co2OUT'}, -1);
sol = solveLP(model);
printFluxes(model, sol.x, false, 10^-5, [], '%rxnID (%rxnName):\n\t%eqn\n\t%flux\n'); %Now it works
```

??? success "Answer to Question 4: `PDC` is missing a product"
    `PDC` converts pyruvate (3 carbons) to acetaldehyde (2 carbons) without any other products: CO2 is missing. The change can be made with `changeRxns`; as an exercise, add the cytosolic CO2 coefficient directly to the stoichiometric matrix:

    ```matlab
    Irxn = ismember(model.rxns, 'PDC');
    Imet = ismember(model.mets, 'CO2_c');
    model.S(Imet, Irxn) = 1; %The coefficient is 1.0
    constructEquations(model, Irxn)
    ```

    The solution is infeasible after the change, meaning that forcing uptake of CO2 without any output is not possible.

### 5. Gap-filling against a reference model

`tutorial4.m` also imports a reference model to draw reactions from, allows all excretion, and reports gaps before filling them:

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

`gapReport` automates this whole quality-control workflow, while `fillGaps` adds reactions from the reference model (here the Tutorial 3 small yeast model) to connect the remaining gaps.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial4.m
:language: matlab
```
