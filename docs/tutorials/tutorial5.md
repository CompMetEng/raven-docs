# Tutorial 5: Reconstruct a GEM from KEGG

This exercise creates a model from KEGG, based on protein sequences in a FASTA file, and runs some functionality checks on the result. The example organism is *Saccharomyces cerevisiae*.

Unlike Tutorials 1–4, this tutorial is a demonstration. Its main purpose is to provide a scaffold that can be adapted to reconstruct a GEM for any organism.

De novo reconstruction performs sequence searches against large HMM databases. Building the model takes up to 20–35 minutes on macOS and Unix systems and 40–55 minutes on Windows, depending on the hardware and the size of the target organism's proteome. `gapReport` can take several to many hours, depending on the number of gaps in the model.

## Step by step

### 1. Reconstructing from KEGG

`getKEGGModelForOrganism` needs trained Hidden Markov Models (HMMs) for eukaryotes. If the library file `<dataDir>.hmm` (or its `.gz` archive) is already present, for example because it was downloaded manually, it is used. Otherwise it is downloaded from the matching release of [toolbox-assets](https://github.com/CompMetEng/toolbox-assets); here the archive `kegg118_eukaryotes` is picked for automatic download.

The function then creates a model for *S. cerevisiae* from the whole-proteome FASTA (`sce.fa`). The parameters are set to exclude general or unclear reactions and reactions with undefined stoichiometry. Type `help getKEGGModelForOrganism` to see what the different parameters are for.

```matlab
model=getKEGGModelForOrganism('sce','sce.fa','kegg118_eukaryotes','output',false,false,false,false,10^-30,0.8,0.3,-1);
disp(model);
```

The resulting model should contain around 1589 reactions, 1600 metabolites and 836 genes. Small variations are possible since it is a heuristic algorithm, and different KEGG versions give slightly different results.

### 2. Removing reactions that make something from nothing

A first control is that the model should not be able to produce any metabolites without uptake of some metabolites. This often happens when metabolites have a different meaning in different reactions. `removeBadRxns` tries to find and remove such reactions automatically; type `help removeBadRxns` for details.

```matlab
[newModel, removedRxns]=removeBadRxns(model);
```

This reports that H⁺ can be made even if no reactions were unbalanced. Protons are particularly problematic because the pH at which the formulas are written is rather arbitrary. For this analysis the protons can be ignored and fixed later, so rerun while allowing H⁺ to be produced.

```matlab
[newModel, removedRxns]=removeBadRxns(model,1,{'H+'},true);
disp(removedRxns);
```

One reaction was removed because it enabled the model to produce something from nothing. Because it is a single reaction, the reaction is examined in more detail.

### 3. Investigating the problematic reaction

According to KEGG, the removed reaction is a general polymer reaction. Use `findLeakMetabolite` to look at the flux distributions in more detail and find out if there is a better alternative to delete.

```matlab
[fluxes, metabolite]=findLeakMetabolite(model,'produce',{'H+'},true);
model.metNames(metabolite)
printFluxes(model, fluxes, false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n')
```

This shows the model could produce H₂O, and returns more fluxes than can be read at once. Excluding the elementally balanced reactions narrows the list. Since water was produced, only look at the reactions unbalanced for oxygen (column 6 of the elemental balance).

```matlab
balanceStructure=getElementalBalance(model);
goodOnes=balanceStructure.leftComp(:,6)==balanceStructure.rightComp(:,6);
printFluxes(removeReactions(model,goodOnes), fluxes(~goodOnes), false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n');
```

Many reactions remain. Leave only the reactions which involve amylose or starch, from one of the problematic reactions identified in step 2.

```matlab
printFluxes(model, fluxes, false, [], [],'%rxnID (%rxnName):\n\t%eqn: %flux\n',{'Amylose';'Starch'});
```

There are two elementally unbalanced reactions, including the one identified by `removeBadRxns`. They contradict each other: the first shows that amylose and starch are interconvertible, while the second shows that amylose contains one less glucose unit than starch. Such general reactions should be fixed manually. Trusting `removeBadRxns`, delete `R02110`.

```matlab
model=removeReactions(model,'R02110');
```

### 4. Checking consumption and adding uptakes

After removing `R02110` the model cannot make something from nothing. Check whether it can consume something without any output.

```matlab
[solution, metabolite]=findLeakMetabolite(model,'consume',{'H+'},true);
model.metNames(metabolite)
```

Nothing is consumed without output. Add some uptakes and check what the model can produce.

```matlab
[~, J]=ismember({'D-Glucose';'H2O';'Orthophosphate';'Oxygen';'NH3';'Sulfate'},model.metNames);
[model, addedRxns]=addExchangeRxns(model,'in',J);
```

`canExchange` reports which metabolites can be produced given these uptakes. It allows output of all metabolites, which does not happen in a real cell. This is useful for functionality testing.

```matlab
I=canExchange(model,'produce');
fprintf('%d%%\n', round(sum(I)/numel(model.mets)*100));
```

Around 31 % of the metabolites could be synthesised. The result does not show by itself whether this is high or low. Many metabolites are not expected to be synthesised from glucose, water, orthophosphate, oxygen, NH3 and sulfate alone.

### 5. Filling gaps using the full KEGG model

Gap-filling with the full KEGG model tests whether this gives a higher fraction of synthesisable metabolites. `getModelFromKEGG` retrieves the full KEGG model. It is associated with more than 6,400,000 genes that are not used for gap-filling, so they are removed to speed up the step.

```matlab
keggModel=getModelFromKEGG(false,false,false,false);
keggModel=rmfield(keggModel,'genes');
keggModel=rmfield(keggModel,'rxnGeneMat');
```

Some reactions in KEGG are known to be unbalanced. Only the balanced ones are used for gap-filling.

```matlab
balanceStructure=getElementalBalance(keggModel);
keggModel=removeReactions(keggModel,balanceStructure.balanceStatus~=1,true,true);
```

`fillGaps` with these settings tries to include reactions that give flux through all reactions in the model. The first flag says that production of all metabolites should be allowed.

```matlab
params.relGap=0.6; %Lower number for a more exhaustive search
params.printReport=true;
[newConnected, cannotConnect, addedRxns, newModel, exitFlag]=fillGaps(model,keggModel,true,false,false,[],params);
```

The results show that `fillGaps` could connect around 29 reactions (`newConnected`) by including around 41 reactions from the KEGG model (`addedRxns`). These should be checked manually to confirm that they exist in yeast; here they are assumed to.

### 6. Reporting connectivity

Continue improving the connectivity of the model by identifying metabolites that should be connected. `gapReport` summarises how connected the model is, along with the supporting detail.

```matlab
[noFluxRxns, noFluxRxnsRelaxed, subGraphs, notProducedMets, minToConnect,...
    neededForProductionMat]=gapReport(newModel);
```

The results show that 532 from 1634 reactions cannot carry flux. Because output is allowed for all metabolites, it calculates 532 in both cases. 543 from 1617 metabolites cannot be synthesised from the supplied precursors. There are 6 subnetworks in the model, of which 1605 from 1617 metabolites belong to the first one.

`gapReport` also prints the metabolites to connect: to enable net production of all metabolites, a total of 322 metabolites must be connected, with the top ranked one being Acyl-CoA (which connects 162 metabolites). Connecting only the top 10 in the list already connects 271/543 (50 %) of them. This is a useful way of directing the gap-filling tasks to where they are of greatest use.

### 7. Adding minimal-media uptakes and iterating

The list reveals that yeast cannot grow on only the substrates defined so far; it requires some other precursors for co-factor synthesis as well. Add uptake reactions for the minimal-media constituents needed for yeast to grow.

```matlab
[~, J]=ismember({'4-Aminobenzoate';'Riboflavin';'Thiamine';'Biotin';'Folate';'Nicotinate';'Zymosterol';'Choline'},newModel.metNames);
[newModel, addedRxns]=addExchangeRxns(newModel,'in',J);
```

Rerun `gapReport` and use the output for targeting the gap-filling efforts. `gapReport` prints part of the information; most of it is available in the output structures. Work iteratively until the model is of sufficient quality.

## Full script

```{literalinclude} ../../RAVEN/tutorials/tutorial5.m
:language: matlab
```
