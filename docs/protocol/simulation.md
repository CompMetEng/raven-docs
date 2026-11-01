# Saving to GitHub and simulating

## Saving to GitHub

The model is tracked and distributed through a GitHub repository. Add metadata to the model structure before saving it:

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

Every significant curation should be committed to the repository. hanpo-GEM provides helper functions to standardise this:

```matlab
newCommit(model);
```

`newCommit` generates the XML, YAML and text files that show the differences between model versions, and it is run whenever a curation is committed. After several curations, the current state is designated as a numbered release:

```matlab
newRelease(model);
```

`newRelease` also generates MAT and XLSX files and records the changes between versions in the history file. Commits and releases become public when they are pushed to the online repository.

hanpo-GEM follows a standardised layout. `model/` holds the latest model in several formats, and `code/` and `data/` contain everything needed to regenerate the model and to run analyses.

## Performing simulations

After gap-filling, the draft model can simulate biomass production. Set biomass formation as the objective, run FBA with `solveLP` and show the active fluxes with `printFluxes`:

```matlab
model = setParam(model, 'obj', 'r_4041', 1);
sol = solveLP(model, 1);
printFluxes(model, sol.x, false);
```

Constrain the model with measured uptake or excretion rates when they are available, by setting the bounds of the relevant exchange reactions. The model can then be evaluated against experimental data from the literature, and the result shows where further development is needed.

The next page is [Manual curation](manual-curation.md).
