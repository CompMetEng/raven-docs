# Gap-filling

Homology-based draft models tend to have many gaps, which are missing reactions that break a pathway needed to produce the biomass macromolecules. The pathway is likely functional in the template, and `getBlast` and `getModelFromHomology` cannot find a homolog for every gene, which leaves the pathway incomplete. Gap-filling identifies and resolves the gaps, and the draft becomes a functional model.

`fillGaps` of RAVEN adds the smallest set of reactions from the template models that supports flux through the draft.

## Forcing biomass production

Gap-filling is set up for growth on glycerol as the carbon source with biomass production as the objective. The model is forced to carry a small non-zero biomass flux, and the glycerol uptake is raised so that the fluxes stay above the tolerance of the MILP solver:

```matlab
model = setParam(model, 'obj', 'r_4041', 1);
model = setParam(model, 'lb', 'r_4041', 0.01);   % force biomass production
model = setParam(model, 'lb', 'r_1808', -10);    % allow glycerol uptake
```

## Preparing the template models

Gaps are resolved with enzymatic and transport reactions. New exchange reactions are excluded because they could introduce other carbon sources. All exchange reactions are therefore removed from the copies of the templates that are the reaction source, and the script also removes the biomass pseudoreactions. Reactions that both templates share are also dropped, to reduce the MILP search space:

```matlab
modelSce2  = removeReactions(modelSce,  getExchangeRxns(modelSce, 'both'), true, true, true);
modelRhto2 = removeReactions(modelRhto, getExchangeRxns(modelRhto, 'both'), true, true, true);
rxns       = intersect(modelSce2.rxns, modelRhto2.rxns);
modelRhto2 = removeReactions(modelRhto2, rxns);
```

## Running `fillGaps`

```matlab
[~, ~, addedRxns, model] = fillGaps(model, {modelSce2, modelRhto2}, false, true);
```

`allowNetProduction` set to `false` prevents additional exchange reactions, and `useModelConstraints` set to `true` ensures that the flux from glycerol to biomass is gap-filled. The growth of the model is verified, then the lipids are scaled and the bounds of the carbon uptake are restored:

```matlab
sol = solveLP(model, 1);
printFluxes(model, sol.x);
model = scaleLipids(model, 'tails');

model = setParam(model, 'lb', 'r_1808', -1);   % carbon source back to 1 mmol/gDCW/h
model = setParam(model, 'lb', 'r_4041', 0);
model = deleteUnusedGenes(model);
```

The `solveLP` call verifies that the model grows after gap-filling.

## Semi-automatic gap analysis

RAVEN has functions that find gaps:

- `canExchange` finds the net synthesis or consumption of metabolites (`'produce'` or `'consume'`).
- `checkProduction` finds the smallest set of metabolites that need net synthesis.
- `getAllSubGraphs` finds disconnected subnetworks.
- `haveFlux` finds the reactions that can or cannot carry flux.

A biomass macromolecule that is absent from `canExchange(model, 'produce')` indicates a gap.

The next page is [Saving to GitHub and simulating](simulation.md).
