# RAVEN documentation: design & content guide

> **This is a living document, and it is the source of intent.** It describes how
> the RAVEN documentation site *should* be designed and what it *should*
> contain; it is a set of instructions, not a description of the current state
> of `main`. When the site and this document disagree, treat this document as
> the target and bring the site in line (not the other way round). Keep it
> updated as decisions are made; record new decisions in the decisions log and
> move resolved items out of "open questions".

> **⚠️ Before doing any work in this repo, pull all remotes first**: the
> superproject *and* every submodule. The submodules are updated frequently
> (including automatically), so local state goes stale quickly; never build on a
> stale checkout:
>
> ```bash
> git fetch --all --prune
> git checkout main && git pull --ff-only
> git submodule sync --recursive
> git submodule update --init --recursive
> ```

## 1. Purpose

A single, dual-language documentation site for **RAVEN** that serves both the
**MATLAB** toolbox and the **Python** package (**raven-toolbox**) from one place,
so a user can learn a concept once and apply it in either language. The site is
built with [Sphinx](https://www.sphinx-doc.org/), [MyST](https://myst-parser.readthedocs.io/)
Markdown and the [PyData theme](https://pydata-sphinx-theme.readthedocs.io/), and
published on Read the Docs.

## 2. Guiding principles

- **Dual-language parity.** MATLAB and Python are presented side by side
  throughout: paired API entries, and code blocks with MATLAB/Python tabs.
- **Single source of truth.** API documentation is extracted directly from the
  function help in each toolbox's source, so it never
  drifts from the code. The source repos are tracked as **git submodules**.
- **Source of truth follows the active branch.** The RAVEN submodule tracks
  **`develop`** and raven-toolbox tracks **`develop`**. RAVEN's modular
  folder layout (`reconstruction`, `manipulation`, `analysis`, …) mirrors
  raven-toolbox's package structure, so the two line up by category.
- **Don't reinvent cobrapy.** Where the Python version intentionally relies on
  [cobrapy](https://cobrapy.readthedocs.io/) instead of providing its own
  function, the site links to the cobrapy equivalent rather than duplicating it.
- **Low maintenance.** Pages that can be generated (the API reference) are
  generated at build time; prose pages are hand-written and kept short.
- **Living, curated content.** Protocols and tutorials are a growing, curated
  set: quality over quantity.

## 3. Technical foundation

- Sphinx + MyST Markdown + PyData theme, with `sphinx-design` for tabs, grids
  and badges; Read the Docs build (`.readthedocs.yaml`, `docs/conf.py`,
  `requirements.txt`).
- Function help in both toolboxes uses **NumPy-style docstrings** so it renders
  as structured argument/return tables.
- The API reference is **generated at build time** by `scripts/gen_api_pages.py`,
  called from `docs/conf.py`. It reads the help statically from submodule source
  (no MATLAB runtime, no installed package) and writes a cobrapy-style autoapi,
  one page per category, with MATLAB and Python paired by name.
- Submodules: `RAVEN` (branch `develop`), **raven-toolbox** (branch
  `develop`), `hanpo-GEM` (branch `main`).
- The site follows the `docs-site` standard of
  [CompMetEng/skills](https://github.com/CompMetEng/skills). The scripts in
  `scripts/` are copies of `docs-site/scripts` there, and what is specific to
  this site is in `scripts/project.yml`, `scripts/curated_pairs.yml` and
  `scripts/known_names.txt`. A change to a script is made in the plugin first.
- Read the Docs and `.github/workflows/docs-build.yml` build with warnings as
  errors; `docs-build.yml` also runs `scripts/check_site.py` and
  `scripts/check_names.py`.

## 4. Site structure

### 4.1 Home (first page)

- **(a)** A very brief introduction to RAVEN: what it is (reconstruction,
  analysis and visualization of genome-scale metabolic models) and what it is
  for.
- **(b)** Make clear that **both a MATLAB and a Python version exist**, and that
  this site documents both.
- **(c)** Links to the key articles:
  - RAVEN 2.0: Wang et al. (2018), *PLoS Comput Biol* 14(10):e1006541.
  - RAVEN (1.0): Agren et al. (2013), *PLoS Comput Biol* 9(3):e1002980.
  - (Add the raven-toolbox reference once published.)

### 4.2 Installation

An **Installation** section with an overview page and a **separate page per
version**:

- **RAVEN (MATLAB).** Requirements, then the **three install methods**: the
  MATLAB Add-Ons manager, a release download, and `git clone`, plus
  verifying (`checkRaven`), **upgrading** (per method) and **removing**
  (`removeRavenFromPath`).
- **Python (raven-toolbox).** Requirements, `pip install raven-toolbox`,
  development install, verifying, **upgrading** and **removing**, and solver
  configuration via cobrapy.
- A shared **Choosing a solver** table lives on the overview page.

### 4.3 MATLAB vs Python versions

Explain the relationship between the two implementations:

- They have **large overlap**, but there are differences.
- The **MATLAB** version works **completely independently**, including
  independently of the COBRA Toolbox, although `ravenCobraWrapper` can translate
  between the RAVEN and COBRA model formats.
- The **Python** version (raven-toolbox) is built **on top of cobrapy**.
- As a result there are **MATLAB-only functions**, many of which are not ported
  because cobrapy already covers that functionality.

Then a **mapping table**: MATLAB function name (left) ↔ Python function name
(right). Conventions:

- Each function name links to its entry in the [API reference](#46-api-reference).
- Where no raven-toolbox function exists because cobrapy provides the
  equivalent, link to the **cobrapy** function instead and mark it with a small
  **cobrapy** indicator (icon/badge) to show it is an external cobrapy function.
  cobrapy API index: <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>.
- **Maintenance:** the RAVEN ↔ raven-toolbox pairs are **auto-generated** from
  the API data (by normalised name); the **cobrapy-alternative rows are
  hand-curated** (a maintained list of MATLAB-only functions → cobrapy links).

| MATLAB (RAVEN) | Python (raven-toolbox) |
|---|---|
| `importModel` | `import_model` |
| `solveLP` | `solve_lp` |
| … | … (cobrapy) |

### 4.4 Guides

Three sets of worked material, kept distinct because they serve different
readers. `docs/protocol/index.md` is the landing page and says which is which.

#### 4.4.1 User guide (`docs/guide/`)

Short, task-focused pages modelled on the cobrapy documentation: **one job per
page**, three to eight functions, numbered so they can be referred to. Both
languages live on **one page** in linked MATLAB/Python tabs; the prose is
identical, and side by side a reader sees where raven-toolbox has no counterpart
because cobrapy already covers it. Two parallel trees would double the
maintenance and drift.

Twenty-two numbered pages are written: getting started, model structure, I/O,
FBA, media and conditions, solvers, building, editing, quality control,
tINIT/ftINIT, deletions, tasks, gap-filling, flux variability, sampling,
combining and simplifying, comparison, homology reconstruction and KEGG
reconstruction, engineering targets, table-driven curation, and biomass and
annotation. Omics integration is part of the tINIT/ftINIT page. Not yet
written: localization.

Conventions:

- **Page anatomy.** Title and one-paragraph statement of the task; a
  "Functions on this page" table (MATLAB | Python | note) linking into the API
  reference (`scripts/autolink.py` adds the links at build time: every name in
  the table and the first mention per section in the prose); setup; two to five numbered steps, each with a tabbed code block and
  its real output; "What can go wrong"; "See also".
- **cobrapy is marked, three ways**: a badge in the function table linking to
  cobrapy's docs, an explicit import in the snippet
  (`from cobra.io import read_sbml_model`), and a line of prose wherever the
  MATLAB tab would make a cobrapy call look like RAVEN's. A reader who thinks
  `get_by_id` is raven-toolbox's searches the wrong reference.
- **Never fake a pairing.** Where nothing equivalent exists, the tab says so.
  `scripts/check_names.py` lists names that resolve to neither toolbox.
- **Differences are the content.** Where the two toolboxes genuinely disagree,
  `getExchangeRxns` counting 273 exchanges where `model.exchanges` counts 270,
  `fillGaps` being a MILP where `connect_blocked_reactions` is an LP, say so on
  the page.

#### 4.4.2 Protocols

Published pipelines followed end to end. Currently the homology-based
reconstruction of *H. polymorpha* (`hanpo-GEM`), MATLAB only.

#### 4.4.3 Legacy tutorials

See §4.5.

#### 4.4.4 Executed examples

Every snippet in the user guide is run on each commit and compared with the
output printed beneath it, in **both** languages (`scripts/run_examples.py`,
`.github/workflows/examples.yml`).

- Python runs in-process; MATLAB runs one session per page, driven by
  `matlab-actions/run-command` because that is what licenses MATLAB on a
  GitHub-hosted runner.
- **GLPK is the documented default**, since it ships with both toolboxes. Blocks
  needing a MILP carry `<!-- run-examples: needs-gurobi -->` and run where a
  Gurobi WLS licence is configured (`GUROBI_WLS*` secrets), skipped elsewhere.
- `<!-- run-examples: skip -->` and `skip-file` opt out, and the page states why:
  a missing toolbox, an hour-long preparation, a KEGG download.
- Output is normalised before comparison: MATLAB warnings are flattened (the
  runner's terminal is narrower than a developer's), and solver chatter is
  stripped; Gurobi's banner names the machine's licence.
- **The tabs are compared to each other.** A value printed under the same label
  with the opposite sign in the other tab is reported. This is the one thing the
  per-block check cannot see: a snippet that runs cleanly and prints a wrong
  number still matches the wrong number written beneath it, which is how
  `growth: -0.0809 /h` once shipped beside `0.0809`.
- **What none of it catches:** a page where both tabs are wrong the same way. The
  solvers page once opened an uptake in the wrong direction and both tabs agreed
  on zero growth. Only reading catches that.

Data lives in `docs/data/` with provenance in its README: the two small yeast
models from `RAVEN/tutorial`, yeast-GEM v9.1.0 pinned in both formats, RAVEN's
starter model, a condition file and a task list. Pages needing Human-GEM clone it
rather than vendoring 43 MB.

### 4.5 Legacy tutorials

Include **tutorials 1–5** only. State that these were part of the **RAVEN 1
paper** (Agren et al., 2013); the code has been updated to run with current
RAVEN, but **no further changes** have been made to the exercises.

> Tutorial 6 (de novo reconstruction of *Streptomyces coelicolor* from
> MetaCyc + KEGG) is **not** included; it is a RAVEN 2.0 showcase, not a RAVEN 1
> legacy tutorial.

### 4.6 API reference

Generated from source, organised so each function is shown for both languages.

- **Python (raven-toolbox)**: should look and feel like cobrapy's autoapi, e.g.
  <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html> and a
  function page like
  <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/flux_analysis/parsimonious/index.html#cobra.flux_analysis.parsimonious.pfba>.
- **MATLAB**: functions organised **by subfolder** (RAVEN's modular
  categories: `reconstruction`, `manipulation`, `analysis`, …).

## 5. Conventions

- **Code tabs.** `sphinx-design` tabs labelled "MATLAB" / "Python", **linked**
  through `:sync:`, defaulting to **MATLAB**.
- **cobrapy indicator.** Functions that resolve to cobrapy (not RAVEN) are
  marked with a consistent icon/badge and link out to the cobrapy docs.
- **Naming.** MATLAB `camelCase` ↔ Python `snake_case`; the two are paired by
  normalised name in the API generator. The Python package is **raven-toolbox**.
- **Citations / attribution.** Neutral; no AI-authorship attribution anywhere.

## 6. Open questions

*(To be resolved with the maintainer; record answers here and fold the decisions
into the relevant section above.)*

- **Custom domain**: whether to serve under a project domain in addition to the
  default Read the Docs URL (optional).
- **Link check.** `docs-build.yml` does not fail on the link check yet; the
  state of the external links was not known when the check was added.
- **Migration page labels.** The links to the migration pages are labelled with
  section numbers of an earlier single-page version (`§7`, `§9`). The targets are
  correct; the labels are not.

## 7. Decisions log

*(Append decisions here as they are made.)*

- Build stack: Sphinx + MyST + PyData theme; API pages generated by
  `scripts/gen_api_pages.py`.
- Source via git submodules: RAVEN tracks `develop`, **raven-toolbox tracks
  `develop`**, hanpo-GEM tracks `main`.
- The Python package is named **raven-toolbox**.
- Function help reformatted to NumPy-style docstrings (renders as tables).
- API reference is cobrapy-style, generated from source, paired by name.
- **Tutorial 6 is excluded**; legacy tutorials are 1–5 (RAVEN 1 paper).
- **Code tabs default to MATLAB and are persistent/linked** across the site.
- **MATLAB↔Python mapping table:** auto-generated pairs + hand-curated cobrapy
  alternatives.
- **Always pull all remotes (superproject + submodules) before starting work.**
- **Look & feel:** layout "direction B", a navy hero homepage with a
  left **sidebar** (dense, sectioned, nested), prominent search, and a segmented
  MATLAB/Python switch in the hero. Palette **navy** (the values were replaced by the
  entry on the docs-site standard below). Logo: the **RAVEN raven silhouette only** (no wordmark),
  white on the navy header/hero; navy version as favicon.
- **User guide:** a cobrapy-style set of short task pages, both languages on one
  page in linked tabs, replacing the earlier plan of protocol-only content. 13
  pages written; the numbering is stable and pages are appended, not renumbered.
- **Examples are executed in CI, in both languages**, and the two tabs are
  compared to each other. GLPK is the documented default; Gurobi-only examples
  are marked and skipped where no licence is configured.
- **The ftINIT page is a full Human-GEM walkthrough but is not re-executed** by
  the build: preparation takes ~2 hours and 159 MB. It states the versions its
  numbers came from.
- **Versioning:** versioned per release via Read the Docs' native version
  management (tag `raven-docs` releases and activate them in the RTD project;
  RTD shows the version selector). Not mike/gh-pages.
- **docs-site standard:** the site follows the shared standard. The brand colour
  is `#1A4888` in light mode and `#6aa6e8` in dark mode, the values in
  `custom.css`, set as `--site-accent`, `--pst-color-primary` and
  `--pst-color-link`. The logo is the wordmark, with a white version for dark
  mode. Logos and the favicon are in `docs/_static` only. The scripts are shared
  with the other sites. The guide page titles keep their numbers; the standard
  does not require them.
- **Warnings are errors:** Read the Docs and CI build with `-W`. Links to the
  explicit targets of the migration pages are written `[text](#label)`; the form
  `page.md#label` resolves heading slugs only. The example data page and two
  parameter-tuning studies, which were listed in no toctree, are in the
  navigation: the data page under *Start* of the guide, the INIT solver
  benchmark under the ftINIT studies and the sampling study under a new *Flux
  sampling* group.
