# Importing template models

RAVEN creates a draft GEM with models of phylogenetically related organisms as templates. For *H. polymorpha*, the *S. cerevisiae* model (yeast-GEM) is the primary template and the *R. toruloides* model (rhto-GEM) is the complementary template.

## Loading the primary template

`importModel` loads an SBML file into a RAVEN-format MATLAB structure:

```matlab
modelSce = importModel('yeastGEM.xml');
```

The COBRA Toolbox wrote yeast-GEM and appends the compartment to each metabolite identifier. RAVEN keeps the compartment in a separate field (`.metComps`), so the redundant suffix is removed. The model receives the identifier `sce`, which `getModelFromHomology` later uses to match the model with its protein FASTA file:

```matlab
modelSce.mets = regexprep(modelSce.mets, '\[[a-z]+\]$', '');
modelSce.id = 'sce';
```

## Inspecting the model

A spreadsheet is often easier for browsing a model. `exportToExcelFormat` writes an `.xlsx` file with five sheets: `RXNS`, `METS`, `COMPS`, `GENES` and `MODEL`:

```matlab
exportToExcelFormat(modelSce, 'modelSce.xlsx');
```

Reconstruction often writes files that are not meant to be tracked in git. The hanpo-GEM repository keeps them in a `scrap/` folder that is excluded from version control.

Changes are made in MATLAB, and the model is exported to SBML when needed:

```matlab
exportModel(modelSce, 'modelSce.xml');
```

## Loading the complementary template

The *R. toruloides* model is loaded in the same way. RAVEN wrote it, so it has no redundant compartment suffix to remove:

```matlab
modelRhto = importModel('rhto.xml', true);
modelRhto.id = 'rhto';
```

Intermediate states of the MATLAB workspace can be stored to resume later:

```matlab
save('scrap/importModels.mat')
% load('scrap/importModels.mat')
```

The next page is [Draft from homology](homology.md).
