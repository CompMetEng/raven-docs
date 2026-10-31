# Biomass composition and annotation

The biomass pseudoreaction states what a cell is made of and sets the units of every growth rate the model reports. The composition can be read, one part of it can be changed without breaking the rest, and the annotation makes a model interpretable to something other than a solver.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `getBiomassFractions` | `sum_biomass` | mass fraction per biomass component |
| `scaleBiomassFraction` | `scale_biomass` | rescale one component to a target |
| `scaleBiomassPseudoreaction` | `rescale_pseudoreaction` | rescale a pseudoreaction and rebalance it |
| `assignSBOterms` | `add_sbo_terms` | label reactions and metabolites with SBO terms |
| `loadDeltaGCSV`, `saveDeltaGCSV` | `load_delta_g_csv`, `save_delta_g_csv` | thermodynamic data through CSV |
| `extractMiriam`, `editMiriam` | `Object.annotation` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read and edit database cross-references |

## Setup

The setup uses `yeast-GEM.yml` from [`docs/data/`](../data/README.md). Its biomass is split across one pseudoreaction per macromolecule class, which is the layout both toolboxes expect to be told about.

Neither toolbox guesses that layout: it differs per organism, so it is passed in as a configuration. Each component names the metabolite its pseudoreaction produces, the reaction's name, and how to turn the reaction's substrates into a mass.

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
strategies = {'mw_minus_2h', 'mw_minus_2h', 'mw_minus_2h', 'mw_minus_2h', ...
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
    "RNA": "mw_minus_2h",
    "DNA": "mw_minus_2h",
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

The component `name` is used differently on the two sides. MATLAB returns the fractions as a struct keyed by that name, so it has to be a valid field name and cannot contain a space; the lipid backbone is therefore `lipidBackbone` in the configuration. `scaleBiomassPseudoreaction` and `rescale_pseudoreaction` also use the name to identify the metabolite the pseudoreaction produces, which they leave unscaled, so it matches the model's own wording. In MATLAB a name that differs from the metabolite name, such as `lipidBackbone`, leaves the product unprotected. `pseudoreaction_name` locates the reaction in both, and it is the same string either way.

The `mass_strategy` says how a pseudoreaction's substrates become grams. `mw` multiplies each coefficient by the metabolite's molecular weight. `mw_minus_2h` reduces each substrate's molecular weight by two hydrogens (2.016 g/mol), the protons a charged tRNA releases in the protein pseudoreaction; `mw_minus_water` reduces it by one water (18.015 g/mol), the mass lost per polymerisation step in RNA and DNA. The example configuration sets `mw_minus_2h` for RNA and DNA. A protein therefore weighs less than the sum of its amino acids. `grams` takes the coefficients as already in g/gDW, the form in which the lipid backbone is written.

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
  RNA              0.0633
  DNA              0.0039
  lipidBackbone    0.0873
  cofactor         0.0048
  ion              0.0024
  total            1.0051
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
  RNA              0.0633
  DNA              0.0039
  lipid backbone   0.0873
  cofactor         0.0048
  ion              0.0024
  total            1.0051
```
:::
::::

The total is the number to check. A biomass pseudoreaction is written so that one unit of flux consumes one gram of cell, which gives the growth rate the unit `/h` rather than an arbitrary unit, so the fractions should sum to about 1 g/gDW. A total that deviates from 1 means a component was edited without rebalancing, and every growth rate the model reports is off by that factor.

The lipid chain pseudoreaction is left out of the configuration on purpose. yeast-GEM represents lipids with a backbone and a chain that are two views of the same mass, so counting both would double it; the [lipid curation](../protocol/lipid-curation.md) step in the protocol explains the representation.

## Changing one component

To apply a different measured protein content, set it and specify which other component absorbs the change. A biomass that does not sum to 1 is worse than one with the old number in it, so both functions can balance a second component to absorb the difference.

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
protein 0.5000, carbohydrate 0.3384, total 1.0000
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
protein 0.5000, carbohydrate 0.3384, total 1.0000
```
:::
::::

`scale_biomass` edits the model in place and returns `None`, while `scaleBiomassFraction` returns a new struct and leaves its input alone. That is the same split as in [Combining and simplifying](combining.md); the Python tab therefore copies the model first.

`balanceOut` names the component that absorbs the change: it is rescaled so the components sum to 1 g/gDW (`targetTotal` or `target_total`), whatever the total was before (1.0051 becomes 1.0000); the H+ rebalance of a rescaled pseudoreaction can leave the total slightly above it. The balancing component must be large enough to absorb the difference; if it would have to go negative, both functions raise an error, so its pseudoreaction is not turned around. Omit `balanceOut` and the component is rescaled on its own, which is correct only if some other step restores the total.

`scaleBiomassPseudoreaction` and `rescale_pseudoreaction` work one level down, on a single pseudoreaction, and rebalance the protons afterwards using the `proton_met` from the configuration. The reaction charge therefore stays balanced when its coefficients move.

## SBO term annotation

An SBO term states what a reaction or metabolite is: a transport reaction, an exchange or a metabolite as opposed to a pseudo-species. Solvers ignore SBO terms; everything that reads a model afterwards does not.

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

RAVEN keeps the term as a MIRIAM entry with namespace `sbo` in `rxnMiriams` and `metMiriams`, so `extractMiriam` reads it out, and `exportModel` writes it to SBML as the `sboTerm` attribute.
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

cobrapy keeps the term in each object's `annotation["sbo"]`, as a string, and writes it to SBML as `sboTerm` too.
:::
::::

The terms are assigned from what the model already says. A reaction with a single metabolite is an exchange (SBO:0000627) when that metabolite is in an extracellular compartment (`e`, or one named `extracellular`), and otherwise a sink (SBO:0000632) when it consumes the metabolite or a demand (SBO:0000628) when it produces it; smallYeast has no extracellular compartment, so its uptakes are demands and its outputs sinks. A reaction in which one metabolite name occurs in more than one compartment is a transport (SBO:0000655), so `GROWTH`, which uses acetyl-CoA in both `c` and `m`, is labelled one. Everything else is a metabolic reaction (SBO:0000176), unless its name marks it as the biomass, maintenance or another pseudoreaction. Nothing is inferred that the stoichiometry does not already support, so running it on a model with mislabelled compartments propagates that mistake and does not catch it.

## Cross-reference and thermodynamic annotation

Database cross-references are stored in MIRIAM form: a namespace and an identifier, such as `chebi/CHEBI:15589`. RAVEN keeps them in `metMiriams` and `rxnMiriams` and provides `extractMiriam` to read them out and `editMiriam` to change one without disturbing the rest. cobrapy keeps the same information in each object's `annotation` dictionary, so it is read and written as an ordinary dict, and [Reading and writing models](io.md) covers how both survive a round trip.

Thermodynamic data is handled in a separate file. `loadDeltaGCSV` and `load_delta_g_csv` read CSVs of standard Gibbs free energies onto the metabolites and reactions, and `saveDeltaGCSV` and `save_delta_g_csv` write it back out. Keeping it in CSV means a thermodynamics run can be versioned and reviewed separately from the model, and re-applied after the model changes.

:::{warning} Troubleshooting
- A configuration that does not match the model. Components are matched on the pseudoreaction's name and not its id. A component whose pseudoreaction is missing contributes zero without failing, so a mistyped name shows as a total that is short.
- The wrong mass strategy. Using `mw` where the convention is `mw_minus_2h` inflates every polymer by the mass of the bonds, and the total shows it: the total is not near 1.
- Rescaling without balancing. Setting protein to a measured value and leaving the rest alone changes the total, and therefore rescales every growth rate the model produces.
- Counting a lipid twice. A backbone-and-chain representation states the same mass two ways. Include one.
- Trusting SBO terms as validation. They record what the model already implies. They are useful downstream and are no check on the model.
:::

## See also

- [Simulating growth with FBA](fba.md), where the growth rate these units belong to comes from.
- [Editing an existing model](editing.md), changing a pseudoreaction by hand.
- [GEM reconstruction protocol: biomass composition](../protocol/biomass.md), building the pseudoreactions from measurements for a new organism.
