# RAVEN (MATLAB)

The RAVEN Toolbox runs in MATLAB and works completely independently; it does
not require the COBRA Toolbox, although it can interoperate with it.

## Requirements

- **MATLAB** R2016b or later, which is the oldest release the code still guards
  for. Continuous integration tests R2024b only, so a recent release is the
  better-covered choice. No additional MathWorks toolboxes required.
- A **linear-programming solver**: [Gurobi](https://www.gurobi.com/) (free
  academic license, recommended) or **GLPK**, bundled with RAVEN itself, no
  separate install needed. See
  [Choosing and configuring a solver](#choosing-a-solver-matlab) below.
- RAVEN **bundles** `libSBML` and the GLPK mex files for Windows, macOS and
  Linux. `BLAST+`, `DIAMOND` and `HMMER` are **not** bundled: RAVEN fetches the
  build for your platform on first use, so the reconstruction functions need
  internet access the first time they run. `downloadRavenBinaries` fetches them
  ahead of time. See
  [Download data and binaries](data-and-binaries.md) for the full set, where
  it is cached, and how to prepare an offline machine.

:::{note} Working offline
[Download data and binaries](data-and-binaries.md) covers preparing a machine
with no network access ahead of time.
:::

---

(choosing-a-solver-matlab)=
## Choosing and configuring a solver

| Solver | LP | MILP | Relative speed | License |
|---|---|---|---|---|
| GLPK | yes | yes (RAVEN warns; slow on large problems) | 1x (baseline) | open source, bundled with RAVEN |
| SCIP | yes | yes | 0.33x | open source; bundled on Windows, a separate install on macOS/Linux |
| Gurobi | yes | yes | 4.2x | free academic license |
| COBRA Toolbox | yes | depends on the COBRA solver configured | depends on the COBRA solver configured | depends on the COBRA solver configured |

MILP-solving functions (`getMinimalMedium`, ftINIT, some gap-filling
algorithms) also run on the bundled GLPK, with a warning that recommends
Gurobi: on genome-scale models GLPK can be much slower than Gurobi, SCIP, or
a MILP-capable solver through the COBRA Toolbox.

Set the active solver with `setRavenSolver`, which takes `'gurobi'`,
`'glpk'`, `'scip'`, or `'cobra'`:

```matlab
setRavenSolver('gurobi');
```

### Gurobi

1. Install Gurobi 7.5 or later.
2. Request and download a license (a free academic license covers most
   research use).
3. Place the license file where Gurobi's own installer says to.
4. Follow Gurobi's MATLAB integration instructions, then run `savepath` so
   MATLAB keeps the change after a restart.
5. `setRavenSolver('gurobi')`.

### Through the COBRA Toolbox

RAVEN can solve through whatever solver the COBRA Toolbox has configured,
instead of one of its own bundled options:

```matlab
changeCobraSolver('glpk');   % or any solver the COBRA Toolbox supports
setRavenSolver('cobra');
```

`ravenCobraWrapper` converts a model between the RAVEN struct and the COBRA
Toolbox structure; see
[RAVEN vs. raven-toolbox](../raven3-vs-raven-toolbox.md#solvers).

---

## Install

:::{warning} Getting 3.0.0b1 specifically
This site documents RAVEN **3.0.0b1**, a pre-release. Both the **Add-Ons
manager** and the **Release download**'s normal releases page only offer the
latest stable release (RAVEN 2.x), not 3.0.0b1: neither method can install
what this site documents. Use the **Clone with git** tab, or the direct
archive link in the **Release download** tab below.
:::

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

Installs from within MATLAB, with no separate download. **Installs the
latest stable release, not 3.0.0b1**; see the warning above.

1. Open the **Home** tab and click **Add-Ons → Get Add-Ons**.
2. Search for **RAVEN Toolbox** and click **Add → Add to MATLAB**.
3. [Verify the installation](#verify).

If MATLAB does not pick up the toolbox after step 2, run
`matlab.addons.enableAddon("RAVEN")` to enable it explicitly.
:::
:::{tab-item} {octicon}`download;1em` Release download

Good for offline or managed environments. **The
[RAVEN releases page](https://github.com/CompMetEng/RAVEN/releases)
itself only lists stable releases**; 3.0.0b1 is a git tag with no packaged
release, so download it directly instead:

1. Download
   [the 3.0.0b1 archive](https://github.com/CompMetEng/RAVEN/archive/refs/tags/3.0.0b1.zip)
   directly (this works without git).
2. Extract it to a location of your choice.
3. In MATLAB, add the RAVEN folder to the path (`pathtool`), then
   [verify](#verify).
:::
:::{tab-item} {octicon}`git-branch;1em` Clone with git

Clones the repository, then checks out the `3.0.0b1` tag specifically: a
plain `git clone` alone tracks the `develop` branch, which can contain changes
made after this site's pre-release.

```bash
git clone --depth=1 https://github.com/CompMetEng/RAVEN.git
cd RAVEN
git fetch --depth=1 origin tag 3.0.0b1
git checkout 3.0.0b1
```

Add the folder to the MATLAB path and [verify](#verify).
:::
::::

---

(verify)=
## Verify

From the MATLAB command window:

```matlab
checkRaven
```

A successful run looks like:

```text
*** THE RAVEN TOOLBOX ***

 > Installation type                    Advanced (via git)
 > Checking RAVEN release               3.0.0
 > Checking MATLAB release              R2024b
 > Set RAVEN in MATLAB path             Pass
 > Save MATLAB path                     Pass

=== Model import and export ===
 > Checking libSBML version             5.20.0
 > Checking model import and export
   > Import SBML format                Pass
   > Export SBML format                Pass
   > Import YAML format                Pass
   > Export YAML format                Pass
   > Export Excel format               Pass

=== Model solvers ===
 > Checking for LP solvers
   > glpk                               Pass
   > gurobi                             Pass
 > Set RAVEN solver                     gurobi

=== Essential binary executables ===
 > Checking BLAST+                      Pass
 > Checking DIAMOND                     Pass
 > Checking HMMER                       Pass

=== Compatibility ===
 > Checking function uniqueness

*** checkRaven complete ***
```

If MATLAB reports that it could not save the path (common on shared or
managed installations where you do not have write access to MATLAB's own
`pathdef.m`), run `addRavenToUserPath` instead: it writes a `startup.m` that
adds RAVEN to the path on every MATLAB start, without touching the shared
path file. `addRavenToUserPath('overwrite', false)` appends to an existing
`startup.m` instead of replacing it.

---

## Upgrade

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

In MATLAB go to **Help → Check for Updates**, click **Update** for RAVEN,
then run `checkRaven` again.
:::
:::{tab-item} {octicon}`download;1em` Release download

Close MATLAB, delete the old RAVEN folder, download and extract the new
release, and run `checkRaven`.
:::
:::{tab-item} {octicon}`git-branch;1em` Clone with git

The `3.0.0b1` tag does not move, so there is nothing to pull while staying on
it. To follow the development branch instead:

```bash
git checkout develop
git pull origin develop
```

`develop` can contain changes that are not yet released. Then run
`checkRaven`.
:::
::::

---

## Remove

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

Go to **Add-Ons → Manage Add-Ons** and remove RAVEN from the list. Running
`removeRavenFromPath` afterward should report an unrecognized-function error,
confirming RAVEN is off the path.
:::
:::{tab-item} {octicon}`download;1em` Release download

```matlab
which removeRavenFromPath   % locate the installation
removeRavenFromPath         % clear RAVEN from the MATLAB path
```

Then delete the RAVEN folder from disk.
:::
:::{tab-item} {octicon}`git-branch;1em` Clone with git

```matlab
which removeRavenFromPath   % locate the installation
removeRavenFromPath         % clear RAVEN from the MATLAB path
```

Then delete the cloned RAVEN folder from disk.
:::
::::

---

## Getting help

For installation problems, open an issue on
[GitHub](https://github.com/CompMetEng/RAVEN/issues).
