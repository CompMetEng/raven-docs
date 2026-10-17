# raven-docs

Documentation site for **RAVEN** (the MATLAB toolbox) and **raven-toolbox** (the
Python port) for genome-scale metabolic model reconstruction, analysis and
visualization. Built with [MkDocs](https://www.mkdocs.org/) +
[Material](https://squidfunk.github.io/mkdocs-material/) and published on Read
the Docs.

The site combines:

- a side-by-side **API reference** auto-generated from the function comments of
  both toolboxes (via [mkdocstrings](https://mkdocstrings.github.io/) with its
  Python and MATLAB handlers);
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
git clone --recurse-submodules https://github.com/edkerk/raven-docs.git
cd raven-docs
# (if already cloned: git submodule update --init --recursive)

python -m venv .venv
source .venv/Scripts/activate      # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

mkdocs serve     # live preview at http://127.0.0.1:8000
mkdocs build     # static site into ./site
```

The API reference pages are generated at build time by
[`scripts/gen_api_pages.py`](scripts/gen_api_pages.py), which walks the two
toolbox submodules and pairs their functions. No MATLAB runtime or installed
Python package is required; docstrings are collected statically from source.
