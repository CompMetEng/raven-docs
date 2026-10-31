# Draft from homology

The protein FASTA files of the target and template organisms are compared to build a draft *H. polymorpha* model based on homology. Two RAVEN functions do the work: `getBlast` aligns the protein sequences, and `getModelFromHomology` uses those results to assemble the first draft.

## Cleaning and matching protein identifiers

The gene identifiers in each template model must match those in its protein FASTA (compare against, for example, *S. cerevisiae* `YML001W`). For the target organism it is also convenient to shorten the identifiers to a standard format such as `Hanpo2_12345`. The *H. polymorpha* FASTA from JGI needs some editing to strip annotations; see [Note 2](#notes).

## Determining homology by BLAST

Evidence of homology is determined by bidirectional BLAST of the target proteome against both template proteomes (this can take some minutes):

```matlab
blast = getBlast('hanpo', 'hanpo.faa', {'sce', 'rhto'}, {'sce.faa', 'rhto.faa'});
```

`getBlast` takes the target organism id, the target protein FASTA, a cell array of template ids, and a cell array of the corresponding template FASTA files.

## Building the first draft

The BLAST results then drive `getModelFromHomology`:

```matlab
model = getModelFromHomology({modelSce, modelRhto}, blast, 'hanpo', ...
    {'sce', 'rhto'}, 1, false, 10^-30, 150, 35);
model = contractModel(model);   % merge identical reactions with different grRules
```

The cutoffs control which BLAST hits count as homology. The maximum E-value is `1e-30` (the default), the minimum alignment length 150 (default 100; values up to 150 give the same result) and the minimum identity 35 % (default 40 %) (see [Note 6](#notes)).

## Adding exchange reactions for the growth medium

The homology approach can only add gene-annotated reactions. Exchange reactions are not gene-associated (they simulate flow of metabolites in and out of the system), so they must be added explicitly. Add the exchanges that correspond to the growth-medium components:

```matlab
mediumComps = {'r_1654', 'r_1672', 'r_1808', 'r_1832', 'r_1861', ...
               'r_1992', 'r_2005', 'r_2060', 'r_2100', 'r_2111'};
model = addRxnsGenesMets(model, modelSce, mediumComps);
```

These represent ammonium, CO₂, glycerol, H⁺, iron, O₂, phosphate, sulfate, water and biomass, everything that must be able to enter or leave the system to support growth. Inspect the first draft:

```matlab
exportToExcelFormat(model, 'scrap/hanpo_step3.3.xlsx');
```

Next: [Biomass composition](biomass.md).

## Notes

- **Note 2: matching identifiers.** Protein identifiers must match between the model and FASTA of each organism. One common fix is to discard everything after the first whitespace in each FASTA header with `sed -i 's/ .*$//' sce.faa`, turning a long annotated header into a bare identifier such as `>YAL001C`.
- **Note 6: `getModelFromHomology` arguments.** Up to thirteen input arguments can be given (three required; the optional ones by position or as name-value pairs). The first four are the template model(s), the BLAST structure, the target organism id (which must match the one given to `getBlast`), and the preferred order of templates (here *S. cerevisiae* is preferred). The next arguments tweak the inclusion criteria; the seventh to ninth are the BLAST cutoffs (maximum E-value, minimum alignment length, minimum identity). The defaults balance sensitivity and specificity.
