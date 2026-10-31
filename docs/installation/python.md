# raven-toolbox (Python)

raven-toolbox is the Python implementation of RAVEN, built on [cobrapy](https://opencobra.github.io/cobrapy/). It is distributed on PyPI.

## Requirements

- Python ≥ 3.11
- cobrapy, installed automatically as a dependency
- A solver: GLPK (bundled with cobrapy) works for small and medium models, and [Gurobi](https://www.gurobi.com/) is recommended for genome-scale work. See [Choosing a solver](index.md#choosing-a-solver).

A virtual environment is recommended. Creation and activation:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

raven-toolbox fetches KEGG data and reconstruction binaries (BLAST+, DIAMOND, HMMER) on first use. [Download data and binaries](data-and-binaries.md) covers preparing a machine with no network access ahead of time.

---

## Installation

::::{tab-set}
:::{tab-item} {octicon}`package;1em` From PyPI

```bash
pip install raven-toolbox
```
:::
:::{tab-item} {octicon}`git-branch;1em` From source

For the latest unreleased code or to contribute:

```bash
git clone https://github.com/CompMetEng/raven-toolbox.git
cd raven-toolbox
pip install -e .
```
:::
::::

---

## Verification

```python
import raven_toolbox
print(raven_toolbox.__version__)
```

The import package is `raven_toolbox` (underscore) and the PyPI distribution name is `raven-toolbox` (hyphen).

---

## Upgrading

::::{tab-set}
:::{tab-item} {octicon}`package;1em` From PyPI

```bash
pip install --upgrade raven-toolbox
```
:::
:::{tab-item} {octicon}`git-branch;1em` From source

```bash
git pull origin develop
```
:::
::::

---

## Removal

```bash
pip uninstall raven-toolbox
```

---

## Solver configuration

raven-toolbox uses cobrapy's solver interface:

```python
import cobra
cobra.Configuration().solver = "gurobi"   # or "glpk"
```
