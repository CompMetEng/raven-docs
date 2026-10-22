# Tutorial 3: Knockouts and omics data

This exercise shows how to run FBA simulations and gene deletion analysis, and
how a GEM can serve as a scaffold for interpreting microarray data. It uses a
simplified model of yeast metabolism (`smallYeast.yml`), imported with
`readYAMLmodel`.

It is assumed you have completed Tutorial 2.

:::{note} Skeleton and solutions
`tutorial3.m` is a skeleton script for you to work through. The completed
answers are in the companion script `tutorial3_solutions.m`. The code
excerpts below follow the solutions; try to derive them yourself before
looking.
:::

## Step by step

### 1. Import and check ATP yield

Import the model, restrict it to anaerobic glucose growth, and maximize ATP
hydrolysis (`ATPX`):

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN' 'o2IN'}, [1 0]);
model = setParam(model, 'obj', {'ATPX'}, 1);
sol = solveLP(model);
printFluxes(model, sol.x, false);
```

The ATP production rate should be 2.0. It was 4.0 in Tutorial 2, but there
sucrose was used instead of glucose.

### 2. Check product yields

Switch to fully aerobic conditions and check the yield of different products,
maximizing each in turn:

```matlab
model = setParam(model, 'ub', {'glcIN' 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', {'ethOUT'}, 1);
sol = solveLP(model);
fprintf(['Yield of ethanol is ' num2str(sol.f) ' mol/mol\n']);
```

The same is repeated for acetate (`acOUT`), glycerol (`glyOUT`) and biomass
(`biomassOUT`).

### 3. Aerobic vs. limited oxygen

Solve for biomass production under full aeration, then restrict the oxygen
uptake upper bound to 0.5 and solve again:

```matlab
solA = solveLP(model);
model = setParam(model, 'ub', {'o2IN'}, 0.5);
solB = solveLP(model);
```

### 4. Single gene deletions with FBA

Set the model to anaerobic growth maximizing biomass, then scan single gene
deletions. After running the deletion scan, keep only solutions that still grow
and look for the one giving the highest glycerol production:

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

The model predicts a glycerol production of 0.23 mmol/gDW/h for the unperturbed
anaerobic case. The best gene deletion corresponds to turning off the `ZWF`
reaction (`ZWF1`, `YNL241C`). Compare the deletion strain to wild type and
follow the changed fluxes around the redox metabolites:

```matlab
model2 = setParam(model, 'eq', {'ZWF'}, 0);
sol2 = solveLP(model2);
compareFluxes(model, sol.x, sol2.x, 'cutoff', 10^-2, ...
    'metaboliteList', {'NADPH' 'NADH' 'NAD' 'NADP'});
```

### 5. Reporter metabolites from microarray data

A GEM can highlight the metabolites around which significant transcriptional
changes cluster. Reload the model first (the steps above changed its bounds and
objective), then load the expression data and run the reporter-metabolites test:

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
