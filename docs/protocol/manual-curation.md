# Manual curation

A draft GEM needs manual curation to become a high-quality model. Curation corrects gene associations, adds or removes reactions, and moves reactions between compartments, all to describe the in vivo network more accurately. For comparison, the *S. cerevisiae* model is curated continuously.

## Replacing template genes with target homologs

Gap-filling adds reactions from the templates without a homology search for the associated genes, so the draft contains *S. cerevisiae* and *R. toruloides* genes that should be replaced by *H. polymorpha* homologs. List the reactions that have an *R. toruloides* gene:

```matlab
rhtoRxns = find(contains(model.grRules, 'RHTO'));
model.rxnNames(rhtoRxns);
model.grRules(rhtoRxns);
```

BLAST identified that gene `RHTO_03911` (oleoyl-CoA desaturase, reaction `y300009`) has the homolog `Hanpo2_15704`. Curate the gene association:

```matlab
model = changeGrRules(model, 'y300009', 'Hanpo2_15704', true);
model = deleteUnusedGenes(model);
```

## Adding methanol assimilation

*H. polymorpha* is a methylotroph and assimilates methanol, and the draft lacks the required pathway. The pathway has five reactions. Reactions 3 to 5 (formate dehydrogenase, peroxisomal catalase and dihydroxyacetone kinase) are present already, so two reactions are added manually:

1. methanol oxidase: `methanol[p] + oxygen[p] => formaldehyde[p] + hydrogen peroxide[p]`
2. dihydroxyacetone synthase: `formaldehyde[p] + D-xylulose 5-phosphate[p] => glyceraldehyde 3-phosphate[p] + glycerone[p]`

A `rxnsToAdd` structure collects the information of the new reactions, and `addRxns` adds them:

```matlab
rxnsToAdd.rxns      = {'MOX', 'DAS'};
rxnsToAdd.equations = {'methanol[p] + oxygen[p] => formaldehyde[p] + hydrogen peroxide[p]', ...
                       'formaldehyde[p] + D-xylulose 5-phosphate[p] => glyceraldehyde 3-phosphate[p] + glycerone[p]'};
rxnsToAdd.rxnNames  = {'methanol oxidase', 'dihydroxyacetone synthase'};
rxnsToAdd.lb        = [0, 0];
rxnsToAdd.ub        = [1000, 1000];
rxnsToAdd.eccodes   = {'1.1.3.13', '2.2.1.3'};
rxnsToAdd.grRules   = {'Hanpo2_76277', 'Hanpo2_95557'};
rxnsToAdd.rxnNotes  = {'Methanol metabolism reaction added by manual curation', ...
                       'Methanol metabolism reaction added by manual curation'};
model = addRxns(model, rxnsToAdd, 3, '', true, true);
```

A few transport and exchange reactions complete the pathway: the exchange of methanol (and glucose), the peroxisomal diffusion of O₂ and H₂O, and the transport of the intermediates between cytoplasm and peroxisome:

```matlab
model = addRxnsGenesMets(model, modelSce, {'r_4494', 'r_4391', 'r_1714', 'r_1980', 'r_2098'});
model = addTransport(model, 'c', 'p', {'D-xylulose 5-phosphate' 'methanol' ...
    'glycerone' 'glyceraldehyde 3-phosphate'}, true, false, 't_');
```

## Confirming growth on methanol

Block the other carbon sources, allow methanol uptake and verify growth:

```matlab
model = setParam(model, 'eq', {'r_1808', 'r_1714'}, 0);   % no glycerol/glucose
model = setParam(model, 'lb', 'r_4494', -1);              % allow methanol uptake
sol = solveLP(model, 1);
printFluxes(model, sol.x);

newCommit(model);
```

After these additions the draft model is methylotrophic, in agreement with the literature.

[`code/reconstructionProtocol.m`](https://github.com/SysBioChalmers/hanpo-GEM/blob/main/code/reconstructionProtocol.m) is the complete runnable script of the protocol.
