# Engineering targets

Two questions underlie most strain-design work: which reactions would have to change for the cell to make more of something, and which metabolites are most affected by a transcriptional response. FSEOF (flux scanning based on enforced objective flux) answers the first from stoichiometry alone; reporter metabolites answer the second from expression data.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `FSEOF` | `fseof` | reactions whose flux tracks enforced product formation |
| `reporterMetabolites` | `reporter_metabolites` | metabolites surrounded by transcriptional change |

## Setup

`smallYeast.yml` is used with glucose and oxygen open, so the model grows. Uptake in this model is a positive flux through a `=> metabolite` reaction, so the upper bound opens it.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', 'biomassOUT', 1);
sol = solveLP(model);
fprintf('growth %.4f /h\n', sol.f);
```

```text
growth 0.1222 /h
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
model.reactions.get_by_id("glcIN").upper_bound = 1.0
model.reactions.get_by_id("o2IN").upper_bound = 1000.0
model.objective = "biomassOUT"
print(f"growth {model.slim_optimize():.4f} /h")
```

```text
growth 0.1222 /h
```
:::
::::

## Reactions that track the product

FSEOF forces the product exchange to carry progressively more flux, maximising growth at each step, and records what every other reaction does. A reaction whose flux rises with the enforced product is an amplification candidate; one that falls is a knockdown candidate. Ethanol, `ethOUT`, is the product here.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
targets = FSEOF(model, 'biomassOUT', 'ethOUT', 'outputFile', tempname());
fprintf('%d amplification target(s) of %d reactions\n', ...
    sum(targets.logical), numel(model.rxns));
```

```text
14 amplification target(s) of 53 reactions
```

The scan runs `iterations` steps, ten by default, up to `coefficient` times the theoretical maximum product flux, `0.9` by default. Writing to `outputFile` keeps the per-reaction table out of the command window; without `outputFile` the table prints to the command window.

`corrThreshold` is the filter that decides what counts as a target: a reaction is kept only if the absolute Pearson correlation between its flux and the enforced product flux is at least this value, `0.9` by default. Alternative optima make individual fluxes change erratically between steps, and requiring a nearly linear response keeps that noise out of the target list.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.analysis import fseof

result = fseof(model, target_rxn="ethOUT", biomass_rxn="biomassOUT")
amplify = (result.targets.target_type == "amplify").sum()
print(f"{amplify} amplification target(s) of {len(model.reactions)} reactions")
print(f"{len(result.targets)} rows in total, both directions")
print(f"enforced flux from {result.enforced[0]:.3f} to {result.enforced[-1]:.3f}")
```

```text
14 amplification target(s) of 53 reactions
40 rows in total, both directions
enforced flux from 0.180 to 1.800
```

The two examples count different things. `targets.logical` in MATLAB flags amplification targets only (as `targets.amplify` does; `targets.knockdown` and `targets.knockout` hold the others), while `result.targets` holds every classified reaction, with a `target_type` column of `amplify`, `knockdown` or `knockout`; `result.amplification` selects the amplification targets. Both scans use the same defaults: ten steps, the top of the scan at 0.9 (`coefficient` in MATLAB, `max_fraction` in Python) of the target flux in the pFBA solution that maximises the target, correlation at least 0.9. Both impose the enforced flux as a lower bound on the target reaction by default; `equality=True` in Python fixes the flux at each level instead, as the GECKO function `ecFSEOF` does. In Python, targets of equal score are listed in model order.

Both tabs find 14 amplification targets here. `fseof` classifies the fluxes of a reaction by the same fixed thresholds as `FSEOF` (`1e-10` for a track above zero, `1e-8` for a final flux of zero).

`fseof` returns the whole scan rather than only its conclusion. `scan` is the reactions by enforced-flux-level matrix of fluxes, `enforced` the levels themselves, and `targets` the classified per-reaction table sorted by score. `gene_targets` aggregates the same result to genes, which is the form a strain-design list usually takes.

`correlation_threshold` matches MATLAB's `corrThreshold`, and `flux_eps` is the tolerance of the check against the theoretical maximum flux (on iJO1366 with target `EX_succ_e` the counts are the same at `1e-8`, `1e-7` and `1e-6`, see [Parameter benchmarks](../parameter-tuning/benchmarks.md)). `min_target` sets the floor of the enforced range, by default one step (the top of the scan divided by `n_steps`); passing the target reaction's flux at the growth optimum starts the scan at the level the cell already has.
:::
::::

## Reading the scan

A target's reliability depends on the trend behind it. The scan matrix distinguishes a reaction that rises steadily from one that changes once and then stops changing.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
idx = find(targets.logical);
[~, order] = sort(abs(targets.slope(idx)), 'descend');
for i = 1:min(5, numel(order))
    j = idx(order(i));
    fprintf('  %-10s slope %8.3f\n', model.rxns{j}, targets.slope(j));
end
```

```text
  ethOUT     slope    1.000
  ADH1       slope    1.000
  PDC        slope    0.864
  PYK        slope    0.503
  GPM        slope    0.467
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
print(result.targets.head(5).to_string())
```

```text
   reaction                    name subsystem             gene_reaction_rule                        genes target_type     slope  correlation  initial_flux  final_flux     score
0    ethOUT   Production of ethanol    [None]                                                          []     amplify  1.000000     1.000000      0.180000    1.799998  1.000000
1      ADH1   Alcohol dehydrogenase    [None]  YGL256W or YMR303C or YOL086C  [YGL256W, YMR303C, YOL086C]     amplify  1.000000     1.000000      0.180000    1.799998  1.000000
2       PDC  Pyruvate decarboxylase    [None]  YGR087C or YLR134W or YLR044C  [YGR087C, YLR044C, YLR134W]     amplify  0.864032     0.999817      0.452739    1.840190  0.863873
3      o2IN            Uptake of O2    [None]                                                          []   knockdown -0.680911    -0.980680      1.101854    0.049522  0.667756
4  ShuttleX          NAD(H) shuttle    [None]                                                          []   knockdown -0.659831    -0.999577      1.183608    0.120575  0.659551
```
:::
::::

The slope is the change in a reaction's flux per unit of enforced product. Its sign gives the direction of the change to apply, and its magnitude the strength. Neither shows that the change is achievable: FSEOF works on the stoichiometry and the bounds, and contains no information on regulation, enzyme capacity or toxicity.

## Reporter metabolites

Reporter metabolites start from expression data. Given a differential-expression result, the analysis identifies the metabolites with the most transcriptionally responsive neighbourhood. The algorithm scores each metabolite from the p-values of the genes catalysing the reactions it takes part in, and corrects for how many genes that is, so a metabolite in a large subsystem does not rank high by size alone.

Real p-values come from a differential-expression analysis. The p-values in the examples are derived from the gene identifiers to keep the results reproducible, so both tabs compute the same input.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
pvalues = zeros(numel(model.genes), 1);
for i = 1:numel(model.genes)
    pvalues(i) = mod(sum(double(model.genes{i})), 1000) / 1000;
end

repMets = reporterMetabolites(model, model.genes, pvalues);
for i = 1:5   % sorted by z-score, highest first
    fprintf('  %-8s z %6.3f  p %.4f  genes %d\n', repMets(1).mets{i}, ...
        repMets(1).metZScores(i), repMets(1).metPValues(i), ...
        repMets(1).metNGenes(i));
end
```

```text
  GA3P_c   z  1.496  p 0.0673  genes 8
  X5P_c    z  1.251  p 0.1054  genes 3
  F6P_c    z  1.196  p 0.1159  genes 7
  PI_c     z  1.180  p 0.1191  genes 12
  F16P_c   z  1.126  p 0.1301  genes 4
```

`printResults` prints the top 20, and `outputFile` writes them. Supplying `geneFoldChanges` adds two further results alongside the full test, one for the up-regulated genes and one for the down-regulated, so a metabolite that is only interesting in one direction can be told apart from one that responds either way.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.analysis import reporter_metabolites

pvalues = {
    gene.id: sum(ord(c) for c in gene.id) % 1000 / 1000
    for gene in model.genes
}

results = reporter_metabolites(model, pvalues)
print(results[0].table.head(5).to_string(index=False))
```

```text
metabolite                                   name  z_score  p_value  n_genes   mean_z    std_z
    GA3P_c           D-glyceraldehyde 3-phosphate 1.496154 0.067307        8 0.088175 0.020418
     X5P_c                 D-xylulose 5-phosphate 1.251241 0.105423        3 0.097096 0.025711
     F6P_c      beta-D-fructofuranose 6-phosphate 1.195594 0.115928        7 0.084621 0.017170
      PI_c                              phosphate 1.179586 0.119082       12 0.079485 0.026143
    F16P_c beta-D-fructofuranose 1,6-bisphosphate 1.126055 0.130071        4 0.089746 0.020478
```

`reporter_metabolites` returns one result per gene set. Without fold changes that is a single `"all"` result; with `gene_fold_changes` it is three, adding `"up"` and `"down"` for the two subsets. Each carries a `table` with the z-score, p-value and the number of genes behind each metabolite.

Genes the model does not have and missing (NaN) p-values are dropped; a p-value outside `[0, 1]` raises an error, because one invalid value would otherwise turn the whole result into `NaN`.
:::
::::

Both toolboxes compute the background correction in closed form and report the same z-scores and one-sided p-values, sorted by z-score. RAVEN returns them as parallel arrays in a struct, raven-toolbox as one table per gene set.

:::{warning} Troubleshooting
- Reading FSEOF as a prediction. It reports what the stoichiometry allows when product formation is forced, which is a hypothesis to test, not an expected yield.
- A target list full of noise. With a lowered correlation threshold, alternative optima appear as targets. If a reaction's flux is not close to linear in the enforced product, its slope is not meaningful.
- Forcing a product the model cannot make. If the target exchange cannot carry flux, every step of the scan is infeasible and there is nothing to correlate. Check it with a single solve first.
- Reporter metabolites on an unfiltered gene list. The correction handles neighbourhood size, not a p-value distribution that is uniform because nothing is differentially expressed. Look at the input distribution before trusting the ranking.
- Currency metabolites at the top. ATP, NADH and water take part in a large share of all reactions, so they tend to appear at the top. Excluding them, or reading past them, is usually necessary.
:::

## See also

- [Simulating growth with FBA](fba.md), the solve that each FSEOF step performs.
- [Random sampling](sampling.md), the other way to ask what a network can do, not what one optimum says.
- [Deletions and essentiality](deletions.md), which covers knockouts, not amplification.
