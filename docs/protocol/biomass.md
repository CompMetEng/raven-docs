# Biomass composition

Metabolism must be able to synthesise the macromolecules that make up the biomass. GEMs encode this in biomass pseudoreactions, which specify the required macromolecules (DNA, RNA, protein, lipid and carbohydrate) and their amounts. Defining the biomass composition early states what the model must be able to synthesise.

In the template models the biomass is split over several pseudoreactions, for example the DNA pseudoreaction:

$$ x\;\text{dAMP} + y\;\text{dCMP} + y\;\text{dGMP} + x\;\text{dTMP} \rightarrow \text{DNA} $$

The pseudoreactions combine into biomass:

$$ \text{DNA} + \text{RNA} + \text{protein} + \text{lipids} + \text{carbohydrate} \rightarrow \text{biomass} $$

## Taking the pseudoreactions from a template

*H. polymorpha* has poly-unsaturated fatty acids, as does *R. toruloides*, so the biomass pseudoreactions of rhto-GEM are the starting point. Their reaction names end in `pseudoreaction`:

```matlab
biomassRxns = modelRhto.rxns(endsWith(modelRhto.rxnNames, 'pseudoreaction'));
model = addRxnsGenesMets(model, modelRhto, biomassRxns);
```

## Updating the stoichiometric coefficients

A spreadsheet in the `data/biomass/` folder of the repository documents the calculations behind the coefficients. The script loads the coefficients and applies each group with `changeRxns`. The DNA pseudoreaction (`r_4050`) is an example:

```matlab
DNA.mets        = {'s_0584', 's_0589', 's_0615', 's_0649', 's_3720'};
DNA.stoichCoeffs = [-0.00189, -0.00174, -0.00174, -0.00189, 1];
model = changeRxns(model, 'r_4050', DNA, 1);
```

The same pattern updates RNA (`r_4049`), protein (`r_4047`), carbohydrate (`r_4048`) and the pseudoreactions of the lipid backbone and chain (`r_4063`, `r_4065`).

## Origin of the coefficients

A coefficient combines the measured total fraction of a macromolecule with the ratio of its constituents:

| Component | Total fraction from | Constituent ratio from |
|---|---|---|
| DNA | scaled from yeast-GEM (0.24 % for the smaller genome) | nucleotide frequencies in the DNA FASTA file |
| RNA | 6 % of biomass (as in yeast-GEM) | nucleotide frequencies of the coding sequences (from the GenBank file) |
| Protein | measured total protein content | amino-acid frequencies in the protein FASTA file |
| Carbohydrate | measured glucan, mannan, trehalose and glycogen | reported levels for *H. polymorpha* |
| Lipids | measured lipid classes and acyl chains | the SLIME approach (next page) |

For nucleotides, the frequency of each base is counted in the DNA FASTA file with `sed` and `grep`:

```bash
sed 's/>.*$//' hpo.fna > hanpo_modified.fa
for i in {A,T,G,C}; do
    echo -n "$i "; grep -oi $i hanpo_modified.fa | wc -l;
done
```

The frequencies, the pairing of A·T and C·G and the molecular weights of the nucleotides give the amount of each deoxyribonucleotide per gram of biomass. The ribonucleotide ratios and the amino-acid ratios are derived in the same way from the coding sequences and the protein FASTA file.

The lipid representation depends on two types of measurements: lipid classes (for example triacylglycerol and phosphatidylinositol) and acyl chains (for example 16:0 and 18:1). The model uses the SLIME formalism (Split Lipids Into Measurable Entities), which the next page sets up.

The next page is [Curation of lipid reactions](lipid-curation.md).
