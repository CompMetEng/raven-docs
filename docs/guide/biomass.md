# 11. Biomass composition and annotation

The biomass pseudoreaction is where a model states what a cell is made of, and it
sets the units of every growth rate the model reports. This page is about reading
that composition, changing one part of it without breaking the rest, and the
annotation that makes a model interpretable to something other than a solver.

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `getBiomassFractions` | `sum_biomass` | mass fraction per biomass component |
| `scaleBiomassFraction` | `scale_biomass` | rescale one component to a target |
| `scaleBiomassPseudoreaction` | `rescale_pseudoreaction` | rescale a pseudoreaction and rebalance it |
| `assignSBOterms` | `add_sbo_terms` | label reactions and metabolites with SBO terms |
| `loadDeltaGCSV`, `saveDeltaGCSV` | `load_delta_g_csv`, `save_delta_g_csv` | thermodynamic data through CSV |
| `extractMiriam`, `editMiriam` | `Object.annotation` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | read and edit database cross-references |

## Setup

`yeast-GEM.yml` from [`docs/data/`](../data/README.md). Its biomass is split
across one pseudoreaction per macromolecule class, which is the layout both
toolboxes expect to be told about.

Neither toolbox guesses that layout: it differs per organism, so it is passed in
as a configuration. Each component names the metabolite its pseudoreaction
produces, the reaction's name, and how to turn the reaction's substrates into a
mass.

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

The component `name` is used differently on the two sides. MATLAB returns the
fractions as a struct keyed by that name, so it has to be a valid field name and
cannot contain a space, which is why the lipid backbone is `lipidBackbone` above.
Python uses the name to identify the metabolite the pseudoreaction produces as
well, so it matches the model's own wording. `pseudoreaction_name` is what
locates the reaction in both, and it is the same string either way.

The `mass_strategy` says how a pseudoreaction's substrates become grams.
`mw` multiplies each coefficient by the metabolite's molecular weight.
`mw_minus_2h` and `mw_minus_water` subtract the mass lost when a monomer is
polymerised, two hydrogens or a water, which is what makes a protein weigh less
than the sum of its amino acids. `grams` takes the coefficients as already being
in g/gDW, which is how the lipid backbone is written.

## 11.1 What is the cell made of?

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

The total is the number to check. A biomass pseudoreaction is written so that one
unit of flux consumes one gram of cell, which is what makes the growth rate a
`/h` rather than an arbitrary unit, so the fractions should sum to about 1 g/gDW.
A total that has drifted means a component was edited without rebalancing, and
every growth rate the model reports is off by that factor.

The lipid chain pseudoreaction is left out of the configuration above on purpose.
yeast-GEM represents lipids with a backbone and a chain that are two views of the
same mass, so counting both would double it; the
[lipid curation](../protocol/lipid-curation.md) step in the protocol explains the
representation.

## 11.2 Change one component

Measured a different protein content? Set it, and specify which other component
absorbs the change. A biomass that no longer sums to 1 is worse than one with the
old number in it, so both functions can balance a second component to absorb the
difference.

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

`scale_biomass` edits the model **in place** and returns `None`, while
`scaleBiomassFraction` returns a new struct and leaves its input alone. That is
the same split as in [20. Combining and simplifying](combining.md), and it is why
the Python tab copies the model first.

`balanceOut` names the component that absorbs the change: it is rescaled so the
components sum to exactly 1 g/gDW, whatever the total was before (1.0051 above
becomes 1.0000). The balancing component must be large enough to absorb the
difference; if it would have to go negative, both functions raise an error
rather than turn its pseudoreaction around. Omit `balanceOut` and the component
is rescaled on its own, which is correct only if some other step restores the
total.

`scaleBiomassPseudoreaction` and `rescale_pseudoreaction` work one level down, on
a single pseudoreaction rather than a named component, and rebalance the protons
afterwards using the `proton_met` from the configuration. That is what keeps the
reaction charge balanced when its coefficients move.

## 11.3 Annotation: SBO terms

An SBO term says what a reaction or metabolite *is*: a transport reaction, an
exchange, a metabolite rather than a pseudo-species. Solvers ignore them;
everything that reads a model afterwards does not.

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

RAVEN keeps the term as a MIRIAM entry with namespace `sbo` in `rxnMiriams`
and `metMiriams`, so `extractMiriam` reads it out, and `exportModel` writes it
to SBML as the `sboTerm` attribute.
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

cobrapy keeps the term in each object's `annotation["sbo"]`, as a string, and
writes it to SBML as `sboTerm` too.
:::
::::

The terms are assigned from what the model already says. A reaction with
metabolites on one side only is an exchange (SBO:0000627) when its metabolite is
in an extracellular compartment (`e`, or one named `extracellular`), and
otherwise a sink (SBO:0000632) when it consumes the metabolite or a demand
(SBO:0000628) when it produces it; smallYeast has no extracellular compartment,
so its uptakes are demands and its outputs sinks. A reaction in which one
metabolite name occurs in more than one compartment is a transport
(SBO:0000655), which is why `GROWTH`, which uses acetyl-CoA in both `c` and
`m`, is labelled one. Everything else is a metabolic reaction (SBO:0000176),
unless its name marks it as the biomass, maintenance or another
pseudoreaction. Nothing is inferred that the
stoichiometry does not already support, so running it on a model with mislabelled
compartments propagates that mistake rather than catching it.

## 11.4 Annotation: cross-references and thermodynamics

Database cross-references travel in MIRIAM form: a namespace and an identifier,
such as `chebi/CHEBI:15589`. RAVEN keeps them in `metMiriams` and `rxnMiriams`
and provides `extractMiriam` to read them out and `editMiriam` to change one
without disturbing the rest. cobrapy keeps the same information in each object's
`annotation` dictionary, so it is read and written as an ordinary dict, and
[3. Reading and writing models](io.md) covers how both survive a round trip.

Thermodynamic data is handled as a side file rather than a model field.
`loadDeltaGCSV` and `load_delta_g_csv` read a CSV of standard Gibbs free energies
onto the reactions, and `saveDeltaGCSV` and `save_delta_g_csv` write it back out.
Keeping it in CSV means a thermodynamics run can be versioned and reviewed
separately from the model, and re-applied after the model changes.

:::{warning} What can go wrong
- **A configuration that does not match the model.** Components are matched
  on the pseudoreaction's **name**, not its id. A component whose
  pseudoreaction is missing contributes zero rather than failing, so a
  mistyped name shows up as a total that is short.
- **The wrong mass strategy.** Using `mw` where the convention is
  `mw_minus_2h` inflates every polymer by the mass of the bonds, and the
  total tells you: it will not land near 1.
- **Rescaling without balancing.** Setting protein to a measured value and
  leaving the rest alone changes the total, and therefore rescales every
  growth rate the model produces.
- **Counting a lipid twice.** A backbone-and-chain representation states the
  same mass two ways. Include one.
- **Trusting SBO terms as validation.** They record what the model already
  implies. They are useful downstream, not a check on the model.
:::

## See also

- [4. Simulating growth with FBA](fba.md), where the growth rate these units
  belong to comes from.
- [8. Editing an existing model](editing.md), changing a pseudoreaction by hand.
- [GEM reconstruction protocol: biomass composition](../protocol/biomass.md),
  building the pseudoreactions from measurements for a new organism.
