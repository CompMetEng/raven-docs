# Biomass composition and annotation

The biomass pseudoreaction states the composition of a cell and sets the units of every growth rate that the model reports. The composition can be read, one component can be changed without unbalancing the rest, and annotation makes a model interpretable for software other than a solver.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getBiomassFractions` | `sum_biomass` | mass fraction of each biomass component |
| `scaleBiomassFraction` | `scale_biomass` | rescale one component to a target |
| `scaleBiomassPseudoreaction` | `rescale_pseudoreaction` | rescale a pseudoreaction and rebalance it |
| `setGAM` | `set_gam` | set the growth-associated maintenance and the non-growth-associated maintenance |
| no equivalent | `get_gam` | read the growth-associated maintenance |
| no equivalent | `fit_maintenance` | fit both maintenance values to chemostat and retentostat data |
| `assignSBOterms` | `add_sbo_terms` | label reactions and metabolites with SBO terms |
| `loadDeltaGCSV`, `saveDeltaGCSV` | `load_delta_g_csv`, `save_delta_g_csv` | thermodynamic data in CSV files |
| `extractMiriam`, `editMiriam` | `Object.annotation` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read and edit database cross-references |
| no equivalent | `find_met_smiles`, `met_smiles` | SMILES of the metabolites from their names |
| no equivalent | `calculate_mw` | molecular weight of a protein from its sequence |

## Setup

The model is `yeast-GEM.yml` from [`docs/data/`](../data/README.md). Its biomass is split over one pseudoreaction per class of macromolecules, and both toolboxes need that layout as a configuration.

The layout differs between organisms, so neither toolbox infers it. Each component names the metabolite that its pseudoreaction produces, the name of the reaction and the way in which the substrates of the reaction are converted to a mass.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('yeast-GEM.yml');

names      = {'protein', 'carbohydrate', 'RNA', 'DNA', ...
              'lipidBackbone', 'cofactor', 'ion'};
pseudoRxns = {'protein pseudoreaction', 'carbohydrate pseudoreaction', ...
              'RNA pseudoreaction', 'DNA pseudoreaction', ...
              'lipid backbone pseudoreaction', 'cofactor pseudoreaction', ...
              'ion pseudoreaction'};
strategies = {'mw_minus_2h', 'mw_minus_2h', 'mw_minus_water', 'mw_minus_water', ...
              'grams', 'mw_minus_2h', 'mw_minus_2h'};

components = cell(1, numel(names));
for i = 1:numel(names)
    components{i} = struct('name', names{i}, ...
        'pseudoreaction_name', pseudoRxns{i}, ...
        'mass_strategy', strategies{i});
end

biomassConfig = struct('biomass_rxn', 'r_4041', ...
    'proton_met', 's_0794', 'components', {components});
fprintf('%d components configured\n', numel(biomassConfig.components));
```

```text
7 components configured
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.biomass import BiomassComponent, BiomassConfig
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("yeast-GEM.yml")

strategies = {
    "protein": "mw_minus_2h",
    "carbohydrate": "mw_minus_2h",
    "RNA": "mw_minus_water",
    "DNA": "mw_minus_water",
    "lipid backbone": "grams",
    "cofactor": "mw_minus_2h",
    "ion": "mw_minus_2h",
}

config = BiomassConfig(
    biomass_rxn="r_4041",
    proton_met="s_0794",
    components=tuple(
        BiomassComponent(
            name=name,
            pseudoreaction_name=f"{name} pseudoreaction",
            mass_strategy=strategy,
        )
        for name, strategy in strategies.items()
    ),
)
print(len(config.components), "components configured")
```

```text
7 components configured
```
:::
::::

The component `name` has different roles in the two toolboxes. MATLAB returns the fractions as a struct keyed by the name, so the name is a valid field name and contains no space, and the lipid backbone is `lipidBackbone` in the configuration. `scaleBiomassPseudoreaction` and `rescale_pseudoreaction` use the name to identify the metabolite that the pseudoreaction produces and leave it unscaled, so the name matches the wording of the model. In MATLAB, a name that differs from the metabolite name, such as `lipidBackbone`, leaves the product unprotected. `pseudoreaction_name` locates the reaction in both toolboxes, with the same string.

`mass_strategy` defines how the substrates of a pseudoreaction become grams:

- `mw` multiplies each coefficient by the molecular weight of the metabolite.
- `mw_minus_2h` reduces the molecular weight of each substrate by two hydrogens (2.016 g/mol), the protons that a charged tRNA releases in the protein pseudoreaction. A protein therefore weighs less than the sum of its amino acids.
- `mw_minus_water` reduces it by one water (18.015 g/mol), the mass lost in each polymerisation step of RNA and DNA.
- `grams` takes the coefficients as g/gDW already, the form of the lipid backbone.

## Composition of the biomass

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
fractions = getBiomassFractions(model, biomassConfig);
names = fieldnames(fractions);
for i = 1:numel(names)
    fprintf('  %-16s %.4f\n', names{i}, fractions.(names{i}));
end
```

```text
  protein          0.4648
  carbohydrate     0.3787
  RNA              0.0541
  DNA              0.0033
  lipidBackbone    0.0873
  cofactor         0.0048
  ion              0.0024
  total            0.9954
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.biomass import sum_biomass

fractions = sum_biomass(model, config)
for name, value in fractions.items():
    print(f"  {name:<16} {value:.4f}")
```

```text
  protein          0.4648
  carbohydrate     0.3787
  RNA              0.0541
  DNA              0.0033
  lipid backbone   0.0873
  cofactor         0.0048
  ion              0.0024
  total            0.9954
```
:::
::::

The total is the value to check. One unit of flux through the biomass pseudoreaction consumes one gram of cell, which gives the growth rate the unit `/h`, so the fractions sum to about 1 g/gDW. A total far from 1 points to a component that was edited without rebalancing or to a wrong mass strategy, and every growth rate of the model is off by the same factor. The unedited yeast-GEM total is 0.9954.

The lipid chain pseudoreaction is not in the configuration. yeast-GEM represents lipids with a backbone and a chain, which are two views of the same mass, and counting both would double it. The step [lipid curation](../protocol/lipid-curation.md) of the protocol explains the representation.

## Changing one component

A different measured protein content is applied by setting it and naming the component that absorbs the change. A biomass that does not sum to 1 is worse than one with the old number, so both functions can balance a second component.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
rescaled = scaleBiomassFraction(model, biomassConfig, 'protein', 0.5, ...
    'balanceOut', 'carbohydrate');
after = getBiomassFractions(rescaled, biomassConfig);
fprintf('protein %.4f, carbohydrate %.4f, total %.4f\n', ...
    after.protein, after.carbohydrate, after.total);
```

```text
protein 0.5000, carbohydrate 0.3481, total 1.0000
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.biomass import scale_biomass

rescaled = model.copy()
scale_biomass(rescaled, config, "protein", 0.5, balance_out="carbohydrate")
after = sum_biomass(rescaled, config)
print(f"protein {after['protein']:.4f}, "
      f"carbohydrate {after['carbohydrate']:.4f}, "
      f"total {after['total']:.4f}")
```

```text
protein 0.5000, carbohydrate 0.3481, total 1.0000
```
:::
::::

`scale_biomass` edits the model in place and returns `None`, and `scaleBiomassFraction` returns a new struct and leaves its input unchanged. The same split applies in [Combining and simplifying models](combining.md), and the Python example copies the model first.

`balanceOut` names the component that absorbs the change. That component is rescaled so that the components sum to `targetTotal` (`target_total` in Python), 1 g/gDW, whatever the total was before; here 0.9954 becomes 1.0000. The proton rebalance of a rescaled pseudoreaction can leave the total slightly above the target. The balancing component must be large enough to absorb the difference. When it would have to become negative, both functions raise an error, so the pseudoreaction does not turn around. Without `balanceOut`, the component is rescaled alone, which is correct when another step restores the total.

`scaleBiomassPseudoreaction` and `rescale_pseudoreaction` work on one pseudoreaction. They rebalance the protons afterwards with the `proton_met` of the configuration, so the charge of the reaction stays balanced when its coefficients change.

## Maintenance: GAM and NGAM

Two numbers set what keeping a cell alive costs in ATP. The growth-associated maintenance (GAM) is the ATP that is hydrolysed per gram of biomass formed, in mmol/gDW. It sits in the coefficients of ATP, ADP, water, phosphate and protons in the biomass pseudoreaction. The non-growth-associated maintenance (NGAM) is the ATP that is hydrolysed per hour and gram of biomass, in mmol/gDW/h, and it is the fixed flux of a maintenance reaction. Together they decide how much substrate a model needs for a given growth rate.

`setGAM` and `set_gam` set GAM, and NGAM when the maintenance reaction is given. The metabolites are matched by name, because the same name is used in every compartment.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
cofactors = {'ATP', 'ADP', 'H2O', 'H+', 'phosphate'};
maintained = setGAM(model, 40, 'r_4041', cofactors, ...
    'ngamRxn', 'r_4046', 'ngamValue', 1);
rxnIdx = getIndexes(maintained, 'r_4041', 'rxns');
metIdx = find(maintained.S(:, rxnIdx) ~= 0 & ismember(maintained.metNames, cofactors));
for i = metIdx'
    fprintf('%-10s %g\n', maintained.metNames{i}, full(maintained.S(i, rxnIdx)));
end
```

```text
ADP        40
ATP        -40
H+         40
H2O        -40
phosphate  40
```

`setGAM` gives every listed metabolite the same coefficient, with the sign that it has. A proton coefficient that differs from the ATP coefficient to balance the charge of the other biomass terms is therefore lost. `setGAM` returns a new struct.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.biomass import get_gam, set_gam

cofactors = ["ATP", "ADP", "H2O", "H+", "phosphate"]
maintained = model.copy()
print(f"GAM before: {get_gam(maintained, biomass_rxn='r_4041'):g}")
set_gam(
    maintained, 40.0, biomass_rxn="r_4041", cofactor_met_names=cofactors,
    ngam_rxn="r_4046", ngam_value=1.0, keep_offsets_of="ATP",
)
biomass = maintained.reactions.get_by_id("r_4041")
for metabolite, coefficient in biomass.metabolites.items():
    if metabolite.name in cofactors:
        print(f"{metabolite.name:<10} {coefficient:g}")
```

```text
GAM before: 55.3
ADP        40
ATP        -40
H+         37
H2O        -40
phosphate  40
```

`set_gam` changes the model in place. Without `keep_offsets_of` it behaves like `setGAM`. With `keep_offsets_of="ATP"` the ATP coefficient becomes the value and every other listed metabolite moves by the same amount, so a proton coefficient that balances the charge keeps its offset from ATP. `get_gam` returns the size of the ATP coefficient.
:::
::::

### Fitting maintenance to data

GAM and NGAM are measured by different experiments, so they are fitted one after the other. Retentostats, and chemostats at very low growth rates, give the maintenance coefficient: the substrate that a cell takes up per hour and gram at zero growth. A model needs a substrate uptake at zero growth that is proportional to NGAM, so the NGAM that reproduces the coefficient follows from one solve. The ATP that a substrate yields comes from the model. With NGAM fixed, chemostats at higher growth rates give GAM: the model is solved for the substrate uptake at each measured growth rate, for a grid of GAM values, and the GAM with the smallest loss is chosen.

The loss is the Huber loss of the logarithm of the ratio of modelled to measured uptake, so a ratio within about 15% counts quadratically and a larger deviation linearly. Data come from many studies, and a study with many rows would decide the result. Each row therefore counts `1 / sqrt(n)` of the number of rows `n` of its study, and a row can be discounted, for example because its value was read from a figure. Resampling the studies with replacement, and choosing the best GAM again each time, gives the 16th and 84th percentile of the estimate. The grid of uptakes is computed once, so the resampling needs no further solves. A model with several growth regimes, such as aerobic and anaerobic growth, is fitted once for each regime, with the model as it is used in that regime.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

RAVEN has no function that fits GAM and NGAM to chemostat data. `fitParameters` fits stoichiometric parameters, such as the maintenance ATP, to measured fluxes with a squared loss and the Nelder-Mead search, and the fitted value is then applied with `setGAM`.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import numpy as np
import pandas as pd
from raven_toolbox.biomass import MaintenanceConfig, fit_maintenance, min_uptake

config = MaintenanceConfig(
    biomass_rxn="r_4041", ngam_rxn="r_4046", growth_rxn="r_2111",
    substrate_exchange="r_1714", cofactor_met_names=tuple(cofactors),
)
studies = {"study A": 0.95, "study B": 1.00, "study C": 1.05}
data = pd.DataFrame(
    [
        {"study": study, "growth_rate": rate,
         "uptake": factor * min_uptake(maintained, rate, config)}
        for study, factor in studies.items()
        for rate in (0.1, 0.2, 0.3)
    ]
)
coefficient = min_uptake(maintained, 0.0, config)
fit = fit_maintenance(
    model, data, coefficient, config, gams=np.arange(30, 50.1, 2.5), bootstrap=100,
)
print(f"NGAM {fit.ngam:.2f} mmol/gDW/h")
print(f"GAM {fit.gam:.1f} mmol/gDW, 16th to 84th percentile {fit.gam_p16:.1f} to {fit.gam_p84:.1f}")
print(f"{fit.units} rows of {fit.studies} studies")
```

```text
NGAM 1.00 mmol/gDW/h
GAM 40.0 mmol/gDW, 16th to 84th percentile 35.0 to 47.5
9 rows of 3 studies
```

The data here are made by the model itself: the uptake of the model with GAM 40 and NGAM 1, scaled by 5% up and down in two of three studies. The fit starts from the original model and finds the values that the data were made with, which checks the procedure and shows how a fit is set up. The percentiles are far apart because each resample draws only three studies. Measured data replace the table in a real fit.

`MaintenanceConfig` names the biomass pseudoreaction, the maintenance reaction, the reaction whose flux is the growth rate, the exchange reaction of the substrate and the metabolites of the GAM term. `fit_maintenance` takes a table with one row per chemostat (`study`, `growth_rate` and `uptake`, the last as a positive number) and the maintenance coefficient of the substrate. The argument `condition_setup` takes a function of the model and a row, for example to set the protein content that was measured in that chemostat. The steps are also available separately: `ngam_from_maintenance_coefficient`, `uptake_grid`, `fit_gam`, `study_weights` and `bootstrap_gam`.
:::
::::

## SBO term annotation

An SBO term states what a reaction or metabolite is: a transport reaction, an exchange reaction, or a metabolite as opposed to a pseudo-species. Solvers ignore SBO terms, and the software that reads a model afterwards uses them.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
small = readYAMLmodel('smallYeast.yml');
annotated = assignSBOterms(small);
idx = getIndexes(annotated, {'glcIN', 'PGI'}, 'rxns');
sbo = extractMiriam(annotated.rxnMiriams(idx), 'sbo');
fprintf('%s: %s\n', annotated.rxns{idx(1)}, sbo{1});
fprintf('%s: %s\n', annotated.rxns{idx(2)}, sbo{2});
```

```text
glcIN: SBO:0000628
PGI: SBO:0000176
```

RAVEN stores the term as a MIRIAM entry with the namespace `sbo` in `rxnMiriams` and `metMiriams`. `extractMiriam` reads it, and `exportModel` writes it to SBML as the attribute `sboTerm`.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.annotation import add_sbo_terms

small = read_yaml_model("smallYeast.yml")
add_sbo_terms(small)
for rid in ("glcIN", "PGI"):
    print(f"{rid}: {small.reactions.get_by_id(rid).annotation['sbo']}")
```

```text
glcIN: SBO:0000628
PGI: SBO:0000176
```

cobrapy stores the term as a string in `annotation["sbo"]` of each object and writes it to SBML as `sboTerm`.
:::
::::

The terms are assigned from the content of the model:

- A reaction with a single metabolite is an exchange (SBO:0000627) when the metabolite is in an extracellular compartment (`e`, or a compartment named `extracellular`). Otherwise it is a sink (SBO:0000632) when it consumes the metabolite and a demand (SBO:0000628) when it produces it. smallYeast has no extracellular compartment, so its uptake reactions are demands and its output reactions are sinks.
- A reaction in which one metabolite name occurs in more than one compartment is a transport (SBO:0000655). `GROWTH`, which uses acetyl-CoA in `c` and `m`, is labelled as one.
- Every other reaction is a metabolic reaction (SBO:0000176), unless its name marks it as the biomass, maintenance or another pseudoreaction.

Nothing is inferred beyond what the stoichiometry supports. On a model with wrong compartments, the assignment carries the error forward and does not detect it.

## Cross-reference and thermodynamic annotation

Database cross-references are stored in MIRIAM form as a namespace and an identifier, for example `chebi/CHEBI:15589`. RAVEN keeps them in `metMiriams` and `rxnMiriams`. `extractMiriam` reads them, and `editMiriam` changes one without affecting the others. cobrapy keeps the same information in the `annotation` dictionary of each object, which is read and written as an ordinary dictionary. [Reading and writing models](io.md) covers how both forms survive a round trip.

Thermodynamic data is kept in a separate file. `loadDeltaGCSV` and `load_delta_g_csv` read CSV files of standard Gibbs free energies onto the metabolites and reactions, and `saveDeltaGCSV` and `save_delta_g_csv` write them. Keeping the data in a CSV file lets a thermodynamics run be versioned and reviewed apart from the model and be applied again after the model changes.

## Names and sequences

Two properties follow from what a model already holds. A metabolite name leads to a structure, and a protein sequence leads to a mass.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

RAVEN stores SMILES in the field `metSmiles` and has no function that looks them up. It has no function that computes the molecular weight of a protein either. `getBiomassFractions` converts the metabolites of the biomass pseudoreactions to grams with the molecular weights from their formulas.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
import cobra
from pathlib import Path
from raven_toolbox.annotation import find_met_smiles, met_smiles
from raven_toolbox.utils.protein import calculate_mw

small = cobra.Model("small")
small.add_metabolites([
    cobra.Metabolite("etoh_c", name="ethanol", compartment="c"),
    cobra.Metabolite("etoh_e", name="ethanol", compartment="e"),
])
Path("smiles-cache.tsv").write_text("ethanol\tCCO\n")
find_met_smiles(small, cache_path="smiles-cache.tsv")
print([met_smiles(m) for m in small.metabolites])

ubiquitin = ("MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG")
print(f"ubiquitin: {calculate_mw(ubiquitin):.1f} g/mol")
```

```text
['CCO', 'CCO']
ubiquitin: 8564.7 g/mol
```

`find_met_smiles` looks each metabolite name up once, in a cache file that is a table of name and SMILES, and applies the SMILES to every metabolite with that name. A name that is not in the cache is searched in [PubChem](https://pubchem.ncbi.nlm.nih.gov/) and the result is appended to the file, so the next call does not send the request again. The example has the name in the cache and sends no request. `met_smiles` reads the SMILES of a metabolite, which is a string for a metabolite that was annotated in memory and a list for a model that was read back from a file. A metabolite that has a SMILES is skipped.

`calculate_mw` adds the average mass of each residue and one water, in g/mol. It reads the 20 standard residues and the codes B, J, O, U, X and Z, ignores whitespace and digits, and returns `nan` for an empty sequence.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- The configuration does not match the model. Components are matched by the name of the pseudoreaction. A component whose pseudoreaction is missing contributes zero without an error, and a mistyped name appears as a total that is too small.
- The mass strategy is wrong. `mw` where the convention is `mw_minus_2h` or `mw_minus_water` increases the mass of every polymer by the mass of the bonds, and the total is then not close to 1.
- A component is rescaled without balancing. Setting the protein content to a measured value and leaving the rest unchanged alters the total and rescales every growth rate of the model.
- A lipid is counted twice. A representation with a backbone and a chain states the same mass in two ways, and one of them is included.
- The fitted GAM is at an end of the grid. `fit_maintenance` searches 25 to 70 mmol/gDW in steps of 1.25 by default. A best value at either end means that the value that fits the data is outside the grid, and the argument `gams` widens it.
- SBO terms are used as a validation. They record what the model already implies. Downstream software uses them, and they do not check the model.
:::

## See also

- [Simulating growth with FBA](fba.md): the source of the growth rate that these units belong to.
- [Editing an existing model](editing.md): changing a pseudoreaction by hand.
- [GEM reconstruction protocol: biomass composition](../protocol/biomass.md): building the pseudoreactions from measurements for a new organism.
