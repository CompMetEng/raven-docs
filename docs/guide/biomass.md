# Biomass composition and annotation

The biomass pseudoreaction states the composition of a cell and sets the units of every growth rate that the model reports. The composition can be read, one component can be changed without unbalancing the rest, and annotation makes a model interpretable for software other than a solver.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getBiomassFractions` | `sum_biomass` | mass fraction of each biomass component |
| `scaleBiomassFraction` | `scale_biomass` | rescale one component to a target |
| `scaleBiomassPseudoreaction` | `rescale_pseudoreaction` | rescale a pseudoreaction and rebalance it |
| `assignSBOterms` | `add_sbo_terms` | label reactions and metabolites with SBO terms |
| `loadDeltaGCSV`, `saveDeltaGCSV` | `load_delta_g_csv`, `save_delta_g_csv` | thermodynamic data in CSV files |
| `extractMiriam`, `editMiriam` | `Object.annotation` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read and edit database cross-references |

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

Nothing is inferred beyond what the stoichiometry supports. On a model with wrong compartments, the assignment propagates the error and does not detect it.

## Cross-reference and thermodynamic annotation

Database cross-references are stored in MIRIAM form as a namespace and an identifier, for example `chebi/CHEBI:15589`. RAVEN keeps them in `metMiriams` and `rxnMiriams`. `extractMiriam` reads them, and `editMiriam` changes one without affecting the others. cobrapy keeps the same information in the `annotation` dictionary of each object, which is read and written as an ordinary dictionary. [Reading and writing models](io.md) covers how both forms survive a round trip.

Thermodynamic data is kept in a separate file. `loadDeltaGCSV` and `load_delta_g_csv` read CSV files of standard Gibbs free energies onto the metabolites and reactions, and `saveDeltaGCSV` and `save_delta_g_csv` write them. Keeping the data in a CSV file lets a thermodynamics run be versioned and reviewed apart from the model and be applied again after the model changes.

:::{admonition} Troubleshooting
:class: warning

- The configuration does not match the model. Components are matched by the name of the pseudoreaction. A component whose pseudoreaction is missing contributes zero without an error, and a mistyped name appears as a total that is too small.
- The mass strategy is wrong. `mw` where the convention is `mw_minus_2h` or `mw_minus_water` increases the mass of every polymer by the mass of the bonds, and the total is then not close to 1.
- A component is rescaled without balancing. Setting the protein content to a measured value and leaving the rest unchanged alters the total and rescales every growth rate of the model.
- A lipid is counted twice. A representation with a backbone and a chain states the same mass in two ways, and one of them is included.
- SBO terms are used as a validation. They record what the model already implies. Downstream software uses them, and they do not check the model.
:::

## See also

- [Simulating growth with FBA](fba.md): the source of the growth rate that these units belong to.
- [Editing an existing model](editing.md): changing a pseudoreaction by hand.
- [GEM reconstruction protocol: biomass composition](../protocol/biomass.md): building the pseudoreactions from measurements for a new organism.
