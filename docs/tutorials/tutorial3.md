# Tutorial 3: Knockouts and omics data

The exercise runs FBA simulations and a gene deletion analysis, and it uses a GEM as a scaffold for the interpretation of microarray data. The model is a simplified model of yeast metabolism (`smallYeast.yml`), which `readYAMLmodel` imports.

Tutorial 2 must be completed first.

`tutorial3.m` is a skeleton script for the exercise. The completed answers are in the companion script `tutorial3_solutions.m`, and the code excerpts below follow the solutions. Write the code before reading the solutions.

## Step by step

### 1. Importing and checking the ATP yield

Import the model, restrict it to anaerobic growth on glucose and maximise the ATP hydrolysis (`ATPX`):

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN' 'o2IN'}, [1 0]);
model = setParam(model, 'obj', {'ATPX'}, 1);
sol = solveLP(model);
printFluxes(model, sol.x, false);
```

The ATP production rate is 2.0. In Tutorial 2, where sucrose was the substrate, it was 4.0.

### 2. Checking product yields

Switch the model to fully aerobic conditions and check the yield of each product by maximising it in turn:

```matlab
model = setParam(model, 'ub', {'glcIN' 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', {'ethOUT'}, 1);
sol = solveLP(model);
fprintf(['Yield of ethanol is ' num2str(sol.f) ' mol/mol\n']);
```

Repeat this for acetate (`acOUT`), glycerol (`glyOUT`) and biomass (`biomassOUT`).

### 3. Aerobic and limited oxygen conditions

Solve for biomass production with full aeration. Then restrict the upper bound of the oxygen uptake to 0.5 and solve a second time:

```matlab
solA = solveLP(model);
model = setParam(model, 'ub', {'o2IN'}, 0.5);
solB = solveLP(model);
```

### 4. Single gene deletions with FBA

Set the model to anaerobic growth with biomass as the objective, and scan single gene deletions. Keep the solutions that grow, and select the one with the highest glycerol production:

```matlab
model = setParam(model, 'eq', {'o2IN'}, 0);
model = setParam(model, 'obj', {'biomassOUT'}, 1);
sol = solveLP(model);
printFluxes(model, sol.x, true);

[genes, fluxes, originalGenes, details] = findGeneDeletions(model, 'sgd');

I = getIndexes(model, {'biomassOUT'}, 'rxns');
J = getIndexes(model, {'glyOUT'}, 'rxns');
okSolutions = find(fluxes(I,:) > 10^-2);          % still growing
[maxGlycerol, J] = max(fluxes(J, okSolutions));
fprintf(['Glycerol production is ' num2str(maxGlycerol) ...
    ' after deletion of ' originalGenes{genes(okSolutions(J),:)} '\n']);
```

The model predicts a glycerol production of 0.23 `mmol/gDW/h` for the unperturbed anaerobic case. The best gene deletion turns off the `ZWF` reaction (`ZWF1`, `YNL241C`). Compare the deletion strain with the wild type, and follow the changed fluxes around the redox metabolites:

```matlab
model2 = setParam(model, 'eq', {'ZWF'}, 0);
sol2 = solveLP(model2);
compareFluxes(model, sol.x, sol2.x, 'cutoff', 10^-2, ...
    'metaboliteList', {'NADPH' 'NADH' 'NAD' 'NADP'});
```

### 5. Reporter metabolites from microarray data

A GEM shows the metabolites around which significant transcriptional changes cluster. Reload the model first, because the preceding steps changed its bounds and objective. Then load the expression data and run the reporter-metabolites test:

```matlab
model = readYAMLmodel('smallYeast.yml');

[orfs, pvalues] = textread('expression.txt', '%s%f');
repMets = reporterMetabolites(model, orfs, pvalues);
[I, J] = sort(repMets.metPValues);

fprintf('TOP 10 REPORTER METABOLITES:\n');
for i = 1:min(numel(J), 10)
    fprintf([repMets.mets{J(i)} '\t' num2str(I(i)) '\n']);
end
```

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial3.m
:language: matlab
```
