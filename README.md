# raven-docs

Documentation site for **RAVEN** (the MATLAB toolbox) and **raven-toolbox** (the
Python port) for genome-scale metabolic model reconstruction, analysis and
visualization. Built with [Sphinx](https://www.sphinx-doc.org/),
[MyST](https://myst-parser.readthedocs.io/) Markdown and the
[PyData theme](https://pydata-sphinx-theme.readthedocs.io/), and published on
Read the Docs.

The site combines:

- a side-by-side **API reference** generated from the function comments of
  both toolboxes;
- a **guide** of task pages with MATLAB and Python side by side, whose examples
  are executed and checked against their printed output;
- the **RAVEN tutorials**; and
- a complete, worked **GEM reconstruction protocol** (the *Hansenula
  polymorpha* `hanpo-GEM` example).

The source repositories are tracked as git submodules that follow the branches
set in `.gitmodules`: [`RAVEN`](https://github.com/CompMetEng/RAVEN) and
[`raven-toolbox`](https://github.com/CompMetEng/raven-toolbox) at `develop`, and
[`hanpo-GEM`](https://github.com/SysBioChalmers/hanpo-GEM) at `main`.

## Building locally

```bash
# clone with submodules
git clone --recurse-submodules https://github.com/CompMetEng/raven-docs.git
cd raven-docs
# (if already cloned: git submodule update --init --recursive)

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

sphinx-build -b html docs docs/_build/html
```

The API reference pages are generated at the start of each build by
[`scripts/gen_api_pages.py`](scripts/gen_api_pages.py), called
from `docs/conf.py`, which walks the two toolbox submodules and pairs their
functions. No MATLAB runtime or installed Python package is required;
docstrings are collected statically from source.
[`scripts/autolink.py`](scripts/autolink.py) then links the function names on
the guide pages to those reference pages, and cobrapy names to cobrapy's
documentation through its intersphinx inventory.

## Checking the guide examples

[`scripts/run_examples.py`](scripts/run_examples.py) runs the code blocks on the
guide pages, MATLAB and Python, and compares what each prints with the `text`
block below it; `--update` rewrites those blocks. The
[Guide examples](.github/workflows/examples.yml) workflow runs it in CI.
