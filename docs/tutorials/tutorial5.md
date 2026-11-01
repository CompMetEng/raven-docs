# Tutorial 5: Reconstruct a GEM from KEGG

The exercise creates a model from KEGG on the basis of protein sequences in a FASTA file and runs functionality checks on the result. The example organism is *Saccharomyces cerevisiae*.

Unlike Tutorials 1 to 4, this tutorial is a demonstration. It provides a scaffold that can be adapted to reconstruct a GEM for any organism.

The de novo reconstruction searches large HMM databases. Building the model takes 20 to 35 minutes on macOS and Unix systems and 40 to 55 minutes on Windows, depending on the hardware and the size of the proteome of the target organism. `gapReport` can take several to many hours, depending on the number of gaps in the model.

## Step by step

### 1. Reconstructing from KEGG

`getKEGGModelForOrganism` needs trained hidden Markov models (HMMs) for eukaryotes. When the library file `<dataDir>.hmm` or its `.gz` archive exists, for example after a manual download, it is used. Otherwise it is downloaded from the matching release of [toolbox-assets](https://github.com/CompMetEng/toolbox-assets). Here the archive `kegg118_eukaryotes` is selected for automatic download.

The function then creates a model for *S. cerevisiae* from the FASTA file of the whole proteome (`sce.fa`). The parameters exclude general or unclear reactions and reactions with undefined stoichiometry. `help getKEGGModelForOrganism` describes the parameters.

```matlab
model=getKEGGModelForOrganism('sce','sce.fa','kegg118_eukaryotes','output',false,false,false,false,10^-30,0.8,0.3,-1);
disp(model);
```

The resulting model should contain around 1589 reactions, 1600 metabolites and 836 genes. Small variations are possible because the algorithm is heuristic, and different KEGG versions give slightly different results.

### 2. Removing reactions that make something from nothing

A first control is that the model cannot produce any metabolite without the uptake of some metabolites. A violation often arises when metabolites have a different meaning in different reactions. `removeBadRxns` finds and removes such reactions automatically, and `help removeBadRxns` gives the details.

```matlab
[newModel, removedRxns]=removeBadRxns(model);
```

The output reports that H⁺ can be made even when no reaction was unbalanced. Protons are problematic because the pH at which the formulas are written is arbitrary. For this analysis the protons can be ignored and corrected later, so the call is repeated with the production of H⁺ allowed.

```matlab
[newModel, removedRxns]=removeBadRxns(model,1,{'H+'},true);
disp(removedRxns);
```

One reaction was removed because it enabled the model to produce something from nothing. As it is a single reaction, it is examined in more detail.

### 3. Investigating the problematic reaction

According to KEGG, the removed reaction is a general polymer reaction. `findLeakMetabolite` shows the flux distributions in more detail and shows whether a better alternative exists for deletion.

```matlab
[fluxes, metabolite]=findLeakMetabolite(model,'produce',{'H+'},true);
model.metNames(metabolite)
printFluxes(model, fluxes, false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n')
```

The model could produce H₂O, and the output contains more fluxes than can be read at once. Excluding the elementally balanced reactions shortens the list. Water was produced, so the reactions that are unbalanced for oxygen (column 6 of the elemental balance) are of interest.

```matlab
balanceStructure=getElementalBalance(model);
goodOnes=balanceStructure.leftComp(:,6)==balanceStructure.rightComp(:,6);
printFluxes(removeReactions(model,goodOnes), fluxes(~goodOnes), false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n');
```

Many reactions remain. The reactions that involve amylose or starch are kept, as one of the problematic reactions from step 2 involves them.

```matlab
printFluxes(model, fluxes, false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n',{'Amylose';'Starch'});
```

Two elementally unbalanced reactions remain, including the reaction identified by `removeBadRxns`. They contradict each other: the first shows that amylose and starch are interconvertible, and the second shows that amylose contains one glucose unit fewer than starch. General reactions of this kind are fixed manually. The result of `removeBadRxns` is trusted, and `R02110` is deleted.

```matlab
model=removeReactions(model,'R02110');
```

### 4. Checking consumption and adding uptakes

After the removal of `R02110`, the model cannot make something from nothing. The next check is whether it can consume something without any output.

```matlab
[solution, metabolite]=findLeakMetabolite(model,'consume',{'H+'},true);
model.metNames(metabolite)
```

Nothing is consumed without output. Some uptakes are added, and the products of the model are checked.

```matlab
[~, J]=ismember({'D-Glucose';'H2O';'Orthophosphate';'Oxygen';'NH3';'Sulfate'},model.metNames);
[model, addedRxns]=addExchangeRxns(model,'in',J);
```

`canExchange` reports the metabolites that can be produced with these uptakes. It allows the output of all metabolites, which does not happen in a real cell, and it serves functionality testing.

```matlab
I=canExchange(model,'produce');
fprintf('%d%%\n', round(sum(I)/numel(model.mets)*100));
```

About 31 % of the metabolites can be synthesised. The result does not show whether this is high or low. Many metabolites are not expected to be synthesised from glucose, water, orthophosphate, oxygen, NH3 and sulfate alone.

### 5. Filling gaps with the full KEGG model

Gap-filling with the full KEGG model tests whether it gives a higher fraction of synthesisable metabolites. `getModelFromKEGG` retrieves the full KEGG model. It is associated with more than 6,400,000 genes that gap-filling does not use, and they are removed to speed up the step.

```matlab
keggModel=getModelFromKEGG(false,false,false,false);
keggModel=rmfield(keggModel,'genes');
keggModel=rmfield(keggModel,'rxnGeneMat');
```

Some reactions in KEGG are known to be unbalanced, and the balanced reactions are used for gap-filling.

```matlab
balanceStructure=getElementalBalance(keggModel);
keggModel=removeReactions(keggModel,balanceStructure.balanceStatus~=1,true,true);
```

With these settings, `fillGaps` tries to include reactions that give flux through all reactions in the model. The first flag allows the production of all metabolites.

```matlab
params.relGap=0.6; %Lower number for a more exhaustive search
params.printReport=true;
[newConnected, cannotConnect, addedRxns, newModel, exitFlag]=fillGaps(model,keggModel,true,false,false,[],params);
```

`fillGaps` connected around 29 reactions (`newConnected`) by including around 41 reactions from the KEGG model (`addedRxns`). These reactions should be checked manually to confirm that they exist in yeast, and here they are assumed to.

### 6. Reporting connectivity

The connectivity of the model is improved further by identifying metabolites that should be connected. `gapReport` summarises how connected the model is, together with the supporting detail.

```matlab
[noFluxRxns, noFluxRxnsRelaxed, subGraphs, notProducedMets, minToConnect,...
    neededForProductionMat]=gapReport(newModel);
```

532 of 1634 reactions cannot carry flux. Output is allowed for all metabolites, so the number is 532 in both cases. 543 of 1617 metabolites cannot be synthesised from the supplied precursors. The model has 6 subnetworks, and 1605 of 1617 metabolites belong to the first.

`gapReport` also prints the metabolites to connect. Net production of all metabolites requires the connection of 322 metabolites, and the top-ranked one is Acyl-CoA, which connects 162 metabolites. The top 10 of the list connect 271 of 543 (50 %) of them. The list shows where the gap-filling has the greatest effect.

### 7. Adding minimal-media uptakes and iterating

The list shows that yeast cannot grow on the substrates defined so far and requires other precursors for cofactor synthesis. Uptake reactions are added for the minimal-medium constituents that yeast needs to grow.

```matlab
[~, J]=ismember({'4-Aminobenzoate';'Riboflavin';'Thiamine';'Biotin';'Folate';'Nicotinate';'Zymosterol';'Choline'},newModel.metNames);
[newModel, addedRxns]=addExchangeRxns(newModel,'in',J);
```

`gapReport` is run again, and its output directs the gap-filling. `gapReport` prints part of the information, and the output structures hold the rest. The work is iterated until the model has sufficient quality.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial5.m
:language: matlab
```
