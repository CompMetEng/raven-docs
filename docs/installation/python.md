# raven-toolbox (Python)

raven-toolbox is the Python implementation of RAVEN, built on [cobrapy](https://opencobra.github.io/cobrapy/). It is distributed on PyPI.

## Requirements

- Python 3.11 or later.
- cobrapy, which is installed as a dependency.
- A solver. GLPK, which is bundled with cobrapy, works for small and medium models, and [Gurobi](https://www.gurobi.com/) is recommended for genome-scale work ([Choosing a solver](index.md#choosing-a-solver)).

A virtual environment is recommended. It is created and activated with:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

raven-toolbox fetches KEGG data and the reconstruction binaries (BLAST+, DIAMOND and HMMER) on first use. [Download data and binaries](data-and-binaries.md) describes how to prepare a machine without network access in advance.

---

## Installation

The release documented on this site, 3.0.0b2, is a pre-release. PyPI also holds the stable release 0.4.0, and `pip` selects that release unless `--pre` is given.

::::{tab-set}
:::{tab-item} {octicon}`package;1em` From PyPI

```bash
pip install --pre raven-toolbox
```
:::
:::{tab-item} {octicon}`git-branch;1em` From source

The source installation provides the latest unreleased code and is the route for contributors:

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

The import package is `raven_toolbox` with an underscore, and the PyPI distribution is `raven-toolbox` with a hyphen.

---

## Upgrading

::::{tab-set}
:::{tab-item} {octicon}`package;1em` From PyPI

```bash
pip install --pre --upgrade raven-toolbox
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

raven-toolbox uses the solver interface of cobrapy:

```python
import cobra
cobra.Configuration().solver = "gurobi"   # or "glpk"
```
