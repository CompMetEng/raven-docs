# Draft from homology

The protein FASTA files of the target and the template organisms are compared to build a draft *H. polymorpha* model on the basis of homology. Two RAVEN functions do the work: `getBlast` aligns the protein sequences, and `getModelFromHomology` assembles the first draft from the results.

## Cleaning and matching protein identifiers

The gene identifiers in each template model must match those in its protein FASTA file, for example `YML001W` for *S. cerevisiae*. For the target organism, the identifiers can be shortened to a standard format such as `Hanpo2_12345`. The *H. polymorpha* FASTA file from JGI needs editing to remove annotations ([Note 2](#notes)).

## Determining homology by BLAST

Evidence of homology comes from a bidirectional BLAST of the target proteome against both template proteomes, which can take some minutes:

```matlab
blast = getBlast('hanpo', 'hanpo.faa', {'sce', 'rhto'}, {'sce.faa', 'rhto.faa'});
```

`getBlast` takes the identifier of the target organism, the protein FASTA file of the target, a cell array of template identifiers and a cell array of the corresponding template FASTA files.

## Building the first draft

The BLAST results drive `getModelFromHomology`:

```matlab
model = getModelFromHomology({modelSce, modelRhto}, blast, 'hanpo', ...
    {'sce', 'rhto'}, 1, false, 10^-30, 150, 35);
model = contractModel(model);   % merge identical reactions with different grRules
```

The cut-offs select the BLAST hits that count as homology. The maximum E-value is `1e-30` (the default), the minimum alignment length is 150 (default 100; in the [calibration study](../parameter-tuning/studies/homology-cutoff-calibration.md), 150 scored at most 0.003 lower than 100) and the minimum identity is 35 % (default 40 %) ([Note 6](#notes)).

## Adding exchange reactions for the growth medium

The homology approach adds only reactions that have gene annotations. Exchange reactions simulate the flow of metabolites in and out of the system and have no gene association, so they are added explicitly. The exchanges of the growth-medium components are added:

```matlab
mediumComps = {'r_1654', 'r_1672', 'r_1808', 'r_1832', 'r_1861', ...
               'r_1992', 'r_2005', 'r_2060', 'r_2100', 'r_2111'};
model = addRxnsGenesMets(model, modelSce, mediumComps);
```

They represent ammonium, CO₂, glycerol, H⁺, iron, O₂, phosphate, sulfate, water and biomass, which are everything that must enter or leave the system to support growth. The first draft is inspected:

```matlab
exportToExcelFormat(model, 'scrap/hanpo_step3.3.xlsx');
```

The next page is [Biomass composition](biomass.md).

## Notes

- **Note 2: matching identifiers.** The protein identifiers of the model and the FASTA file of each organism must match. A common fix discards everything after the first whitespace in each FASTA header with `sed -i 's/ .*$//' sce.faa`, which turns a long annotated header into a bare identifier such as `>YAL001C`.
- **Note 6: `getModelFromHomology` arguments.** Up to thirteen input arguments can be given, three of them required. The optional arguments are passed by position or as name-value pairs. The first four are the template models, the BLAST structure, the identifier of the target organism (which must match the one given to `getBlast`) and the preferred order of templates (here *S. cerevisiae* is preferred). The next arguments adjust the inclusion criteria, and the seventh to ninth are the BLAST cut-offs (maximum E-value, minimum alignment length and minimum identity). The defaults balance sensitivity and specificity.
