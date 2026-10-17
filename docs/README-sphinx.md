# Sphinx / pydata-sphinx-theme exploration

Not part of the site. This note records the migration from MkDocs to Sphinx
(#78, #80). Sphinx is the live build: `.readthedocs.yaml` builds from
`docs/conf.py`. `mkdocs.yml`, `requirements.txt`, `scripts/gen_api_pages.py`
and `scripts/build_hooks.py` belong to the retired MkDocs build and are no
longer used. The sections below describe the state at the time of the
migration.

## Building it

```bash
python -m venv .venv-sphinx
.venv-sphinx/Scripts/pip install -r requirements-sphinx.txt
.venv-sphinx/Scripts/sphinx-build -b html docs docs/_build/html
```

## What's converted

- **Admonitions, content tabs, snippet includes.** Mechanical, via
  `scripts/migrate_to_myst.py`, run once across every page. `!!! note "…"` ->
  `:::{note} …`; `=== "MATLAB"` -> a `tab-set`/`tab-item` pair;
  `--8<-- "path"` -> `{literalinclude}`. Re-running it is a no-op (nothing
  left to match).
- **Navigation.** `mkdocs.yml`'s single `nav:` tree is now a `{toctree}` per
  section, living in that section's own `index.md` (or `migrate.md`, a new
  landing page). Top level, in order: Migrate, User guide, API reference,
  Methods, References; API promoted out from under a "Reference" tab that
  otherwise would have held only citations once MATLAB-vs-Python and tuned
  parameter defaults moved to Migrate and Methods respectively, so that page
  was dropped rather than kept half-empty. `collapse_navigation: True`
  (pydata-sphinx-theme's own default, overridden to `False` in an earlier
  pass of this branch) keeps only the active tab's own subtree expanded.
- **The generated API reference and MATLAB vs Python table.** New
  `scripts/gen_api_pages_sphinx.py`, run from `conf.py`'s `setup()` before
  Sphinx reads the source tree. Reuses `api_index.py`'s collection constants
  and file-walking, extended to keep the *whole* help text instead of only
  the first line, and writes fully static pages: see "Not converted" below
  for why.
- **The home page.** Hand-converted, not mechanical: MkDocs Material's grid
  cards and the custom pip-install JS widget have no equivalent to translate,
  so it's rebuilt with `sphinx-design` grids and a plain tab-set instead. The
  wordmark image (light/dark swap via a small CSS rule) replaces the badge
  row and the "# RAVEN" heading; the heading itself stays in the source for
  document structure but is visually hidden, since a raw `<h1>` never
  registers with MyST's own heading-level check.
- **Missing icons.** MkDocs Material's `:material-*:`/`:octicons-*:`
  shorthand inside tab labels (`installation/raven.md`,
  `installation/python.md`) rendered as literal text; swapped for
  sphinx-design's built-in `{octicon}` role (`plug`, `download`,
  `git-branch`, `package`). Every MATLAB/Python code-example tab site-wide
  also gained a small marker (Ⓜ️ / 🐍) and a `:sync:` key, via
  `scripts/add_tab_icons_sync.py`, so switching the language in one code
  block switches every other tab-set on the page.
- **Announcement banner, "Show Source" links.** `html_theme_options`'
  `announcement` (RAVEN 3.0.0b1, pre-release) and `html_show_sourcelink =
  False`, both single-setting changes.
- **References.** Trimmed to the RAVEN 1/RAVEN 2/Hansenula-protocol/
  INIT/ftINIT/random-sampling papers only, each verified against its DOI
  (Crossref/PLOS) rather than typed from memory; tINIT has no citation of
  its own separate from the INIT paper, RAVEN's MATLAB implementation of it.
- **Link underlines.** `docs/_static/custom.css`, wired in via
  `html_css_files`.
- **`<span class="cobrapy-tag">` inline badges.** 39 occurrences across 14
  guide pages, rendered as inert literal text (the CSS class is
  Material-specific and not defined here). Swapped for sphinx-design's
  built-in `{bdg-secondary}` role, the same mechanical single-string
  find/replace as the icon shorthand fix above.

## Not converted

- **Per-function docstring rendering.** The MkDocs build defers this to two
  live plugins at render time: mkdocstrings' Python handler (griffe) and a
  separate mkdocstrings-matlab handler (tree-sitter). Neither has a verified
  drop-in Sphinx equivalent, the MATLAB one especially, which is a bespoke
  handler with no autodoc-family counterpart. `gen_api_pages_sphinx.py`
  sidesteps this by extracting the full help text itself and writing static
  pages, which keeps the same no-install, no-MATLAB-runtime constraint the
  MkDocs build has, but by a different route. Worth a closer look before
  treating this as done: real docstring structure (numpydoc parameter
  tables, cross-references) is flattened to a plain text block here, where
  mkdocstrings renders it properly.
- **`scripts/build_hooks.py`, `scripts/check_names.py`.** Both are MkDocs
  plugin hooks (`on_config`, `on_page_markdown`, `on_page_content`), a
  different event API than Sphinx's `app.connect(...)`. `build_hooks.py`'s
  matlab-path pruning and mkdocstrings-matlab output cleanup are moot here,
  since this branch doesn't use mkdocstrings-matlab at all.
  `check_names.py`'s identifier validation is still valuable and doesn't
  need to be a live hook; it can run as a standalone pre-build check either
  way, but re-wiring it wasn't done as part of this exploration.
- **`scripts/run_examples.py`.** Treats a bare ` ```text ` fence directly
  below a code block as that block's expected output, and `--update` writes
  that fence shape.
- **`.readthedocs.yaml`.** Still points at the `mkdocs:` build. The target
  block for a real switch:

  ```yaml
  build:
    os: ubuntu-24.04
    tools:
      python: "3.12"
  sphinx:
    configuration: docs/conf.py
  python:
    install:
      - requirements: requirements-sphinx.txt
  ```

  Left unset here since flipping it would make this branch's incomplete
  build the one Read the Docs actually serves.
- **RST cross-reference roles inside docstrings.** raven-toolbox's
  docstrings use Sphinx's own `:func:`name`` role syntax, expected by a
  proper `sphinx.ext.autodoc` pipeline. Rendered as static text here (see
  above), `:func:` shows as a literal prefix next to a correctly-formatted
  inline code span, rather than becoming a cross-reference link. Cosmetic,
  not a build warning.

## Verified

`sphinx-build -E -b html docs docs/_build/html` (`-E` forces a clean
re-read; an incremental rebuild under-reports the cross-reference count
below, since Sphinx does not always revalidate a link when only the *target*
document changed): **0 errors, 67 warnings.**

Two real fixes got the API-reference-generator's own share of that down to
zero, not just noise-suppression:

- Its Python function headings embedded the full signature
  (`### merge_linear(model, no_merge=())`), so MyST's auto-generated heading
  anchor did not match the plain `#merge_linear` the summary table and
  `matlab-vs-python.md` link to. Moved the signature to its own line below
  the heading instead of inside it.
- `## Title {#custom-id}` (MkDocs' attr_list heading-ID syntax) needed
  converting to an explicit `(custom-id)=` MyST target, added as the
  converter's fifth transform.

What's left, all in hand-authored pages rather than generated ones:

- **21 `myst.header`** ("Non-consecutive header level increase; H1 to H3"),
  across most of `docs/guide/*.md`. Predates this branch: every one of these
  pages goes straight from its H1 title to an H3 "Functions on this page"
  aside, which Python-Markdown never enforced and MyST does. A heading-level
  fix, not a migration one; left alone here.
- **42 `myst.xref_missing`**, almost all in `raven3-migration.md`
  (`installation/raven.md` and `guide/io.md` have a few more): hand-placed
  `<a name="…"></a>` HTML anchors, which work as plain browser URL fragments
  but aren't in MyST's own validated-target registry, so every markdown link
  pointing at one warns without actually being broken.
- **4 `toc.not_included`**: `docs/data/README.md` (the same page the MkDocs
  build also excludes from its nav), plus three pages this pass deliberately
  de-listed from Methods rather than deleted, since other pages still link
  to them inline: `parameter-tuning/studies/init-solver-benchmark.md` and
  `.../sampling-convergence-calibration.md` (cross-solver benchmark and one
  of the two sampling pages removed from the Methods listing),
  `parameter-tuning/flux-sampling-algorithms.md` (the other).
