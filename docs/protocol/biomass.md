# Biomass composition

Metabolism must be able to synthesise the macromolecules that make up biomass. GEMs encode this in **biomass pseudoreactions** that specify which macromolecules (DNA, RNA, protein, lipid, carbohydrate) are required and in what amounts. Defining the biomass composition early ensures that the model can biosynthesise everything it needs.

In the template models the biomass is split over several pseudoreactions, for example the DNA pseudoreaction:

$$ x\;\text{dAMP} + y\;\text{dCMP} + y\;\text{dGMP} + x\;\text{dTMP} \rightarrow \text{DNA} $$

which then combine into biomass:

$$ \text{DNA} + \text{RNA} + \text{protein} + \text{lipids} + \text{carbohydrate} \rightarrow \text{biomass} $$

## Taking the pseudoreactions from a template

*H. polymorpha* has poly-unsaturated fatty acids, similar to *R. toruloides*, so the rhto-GEM biomass pseudoreactions are used as the starting point. They are recognised by reaction names ending in `pseudoreaction`:

```matlab
biomassRxns = modelRhto.rxns(endsWith(modelRhto.rxnNames, 'pseudoreaction'));
model = addRxnsGenesMets(model, modelRhto, biomassRxns);
```

## Updating the stoichiometric coefficients

A spreadsheet in the repository's `data/biomass/` folder details the calculations behind the coefficients; the script loads them and applies each group with `changeRxns`. The DNA pseudoreaction (`r_4050`), for example:

```matlab
DNA.mets        = {'s_0584', 's_0589', 's_0615', 's_0649', 's_3720'};
DNA.stoichCoeffs = [-0.00189, -0.00174, -0.00174, -0.00189, 1];
model = changeRxns(model, 'r_4050', DNA, 1);
```

The same pattern updates RNA (`r_4049`), protein (`r_4047`), carbohydrate (`r_4048`) and the lipid backbone and chain pseudoreactions (`r_4063`, `r_4065`).

## Origin of the coefficients

Determining a coefficient combines a measured total fraction of a macromolecule with the ratio of its constituents:

| Component | Total fraction from | Constituent ratio from |
|---|---|---|
| DNA | scaled from yeast-GEM (0.24 % for the smaller genome) | DNA FASTA nucleotide frequencies |
| RNA | 6 % of biomass (as in yeast-GEM) | coding-sequence nucleotide frequencies (from the GenBank file) |
| Protein | measured total protein content | amino-acid frequencies in the protein FASTA |
| Carbohydrate | measured glucan, mannan, trehalose and glycogen | reported levels for *H. polymorpha* |
| Lipids | measured lipid classes and acyl chains | the SLIME approach (next section) |

For nucleotides, the DNA FASTA gives the frequency of each base, counted with `sed` and `grep`:

```bash
sed 's/>.*$//' hpo.fna > hanpo_modified.fa
for i in {A,T,G,C}; do
    echo -n "$i "; grep -oi $i hanpo_modified.fa | wc -l;
done
```

Together with the paired nature of A·T and C·G and the nucleotide molecular weights, this gives the amount of each deoxyribonucleotide needed per gram of biomass. Ribonucleotide and amino-acid ratios are derived analogously from the coding sequences and the protein FASTA.

Lipid representation depends on two measurement types: lipid classes (for example triacylglycerol, phosphatidylinositol) and acyl chains (for example 16:0, 18:1). This model uses the SLIME formalism (Split Lipids Into Measurable Entities), set up in the next section.

Next: [Curation of lipid reactions](lipid-curation.md).
