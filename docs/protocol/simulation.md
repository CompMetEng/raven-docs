# Saving to GitHub and simulating

## Saving to GitHub

The model is tracked and distributed through a GitHub repository. Before saving, add some metadata to the model structure:

```matlab
model.annotation.defaultLB    = -1000;
model.annotation.defaultUB    = +1000;
model.annotation.taxonomy     = 'taxonomy/460523';
model.annotation.givenName    = 'Eduard';
model.annotation.familyName   = 'Kerkhoven';
model.annotation.email        = 'eduardk@chalmers.se';
model.annotation.organization = 'Chalmers University of Technology';
model.id                      = 'hanpo';
model.name                    = 'Hansenula polymorpha-GEM';
```

Every significant curation should be committed to the repository. To standardise this, hanpo-GEM provides helper functions:

```matlab
newCommit(model);
```

`newCommit` automatically generates the XML, YAML and text files that help identify differences between model versions; run it whenever a curation is committed. After several curations, the current state can be designated as a numbered release:

```matlab
newRelease(model);
```

`newRelease` also generates MAT and XLSX files and records the changes between versions in the history file. Commits and releases become public only once pushed to the online repository.

hanpo-GEM follows a standardised layout: `model/` holds the latest model in several formats, while `code/` and `data/` contain everything needed to regenerate the model and run analyses.

## Performing simulations

After gap-filling, the draft model can simulate biomass production. Set biomass formation as the objective, run FBA with `solveLP`, and inspect the active fluxes with `printFluxes`:

```matlab
model = setParam(model, 'obj', 'r_4041', 1);
sol = solveLP(model, 1);
printFluxes(model, sol.x, false);
```

When available, constrain the model with measured uptake or excretion rates by setting the bounds of the relevant exchange reactions. This allows evaluation of the model against experimental data from the literature and identification of where further development is needed.

Next: [Manual curation](manual-curation.md).
