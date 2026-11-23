# API reference

RAVEN ships in two implementations that build genome-scale metabolic models for
the same workflows. Some algorithms differ between them ([Tuned parameter
defaults](../tuned-parameters.md)):

- **RAVEN**: the original **MATLAB** toolbox, which runs independently of the
  COBRA Toolbox and reads and writes SBML through `libSBML`. Functions use
  `camelCase` names.
- **raven-toolbox**: the **Python** port, built on cobrapy. Functions use
  `snake_case` names.

The function help on these pages is extracted directly from the source of each
toolbox on the branch tracked by this site, so it stays in sync with the code.

## How these pages are organised

The reference is split into **two parallel trees**, one per language, each
organised by the toolbox's own module layout and each function shown with its
signature, parameters and returns:

- **MATLAB API (RAVEN)**: one page per category (`Reconstruction`,
  `Manipulation`, `Input / output`, …).
- **Python API (raven-toolbox)**: one page per package, mirroring the same
  categories.
- **[MATLAB vs Python](../matlab-vs-python.md)**: a third page pairing every
  function that exists in both, generated at build time from both toolboxes'
  sources.

Every page opens with a *Functions* table, followed by the full
help for each function.

To move between the two implementations, use the **[MATLAB vs Python](../matlab-vs-python.md)**
table, which pairs every function that exists in both (`camelCase` ↔ `snake_case`) and
links to both references.

## How the two compare

The implementations are kept aligned. The main differences are in calling
convention; where a function computes a different result, the
[comparison](../raven3-vs-raven-toolbox.md) states how:

| | RAVEN (MATLAB) | raven-toolbox (Python) |
|---|---|---|
| Naming | `camelCase` (`getModelFromHomology`) | `snake_case` (`get_model_from_homology`) |
| Returns | multiple outputs `[a,b] = f(...)` | one return value; objects often mutated in place |
| Indexing | 1-based | 0-based |
| Model object | RAVEN `model` struct | `cobra.Model` with RAVEN extensions |

:::{admonition} A note on the two docstring styles
:class: note

raven-toolbox's docstrings are NumPy-style, so they render as structured
parameter/return tables. RAVEN's MATLAB help blocks use the toolbox's own
indented convention, so they render as faithful help text rather than typed
tables. The content is the same; the formatting differs.
:::

Use the navigation to browse either tree, or start from the
[MATLAB vs Python](../matlab-vs-python.md) table.

```{toctree}
:hidden:

matlab/index
python/index
../matlab-vs-python
```
