# RAVEN (MATLAB)

The RAVEN Toolbox runs in MATLAB and works independently. It does not require the COBRA Toolbox, although it can interoperate with it.

## Requirements

- MATLAB R2016b or later. R2016b is the oldest release that the code guards for. Continuous integration tests R2024b only. No additional MathWorks toolboxes are required.
- A linear-programming solver: [Gurobi](https://www.gurobi.com/) (free academic licence, recommended) or GLPK, bundled with RAVEN itself and needing no separate install. See [Choosing and configuring a solver](#choosing-a-solver-matlab).
- RAVEN bundles `libSBML` and the GLPK mex files for Windows, macOS and Linux. `BLAST+`, `DIAMOND` and `HMMER` are not bundled: RAVEN fetches the build for the platform on first use, so the reconstruction functions need internet access the first time they run. `downloadRavenBinaries` fetches them ahead of time. [Download data and binaries](data-and-binaries.md) lists the full set, where it is cached and how to prepare an offline machine.

---

(choosing-a-solver-matlab)=
## Choosing and configuring a solver

| Solver | LP | MILP | Relative speed | Licence |
|---|---|---|---|---|
| GLPK | yes | yes (RAVEN warns; slow on large problems) | 1x (baseline) | open source, bundled with RAVEN |
| SCIP | yes | yes | 0.33x | open source; bundled on Windows, a separate install on macOS or Linux |
| Gurobi | yes | yes | 4.2x | free academic licence |
| COBRA Toolbox | yes | depends on the COBRA solver configured | depends on the COBRA solver configured | depends on the COBRA solver configured |

MILP-solving functions (`getMinimalMedium`, ftINIT, some gap-filling algorithms) also run on the bundled GLPK, with a warning that recommends Gurobi. On genome-scale models GLPK can be slower than Gurobi, which runs at 4.2 times the speed of GLPK in the table.

`setRavenSolver` sets the active solver and takes `'gurobi'`, `'glpk'`, `'scip'` or `'cobra'`:

```matlab
setRavenSolver('gurobi');
```

### Gurobi

1. Install Gurobi 7.5 or later.
2. Request and download a licence (a free academic licence covers most research use).
3. Place the licence file where Gurobi's own installer says to.
4. Follow Gurobi's MATLAB integration instructions, then run `savepath` to keep the change after a restart.
5. Run `setRavenSolver('gurobi')`.

### Solving through the COBRA Toolbox

RAVEN can solve through the solver that the COBRA Toolbox has configured, in place of its own bundled options:

```matlab
changeCobraSolver('glpk');   % or any solver the COBRA Toolbox supports
setRavenSolver('cobra');
```

`ravenCobraWrapper` converts a model between the RAVEN struct and the COBRA Toolbox structure; see [COBRA Toolbox conversion](../raven3-vs-raven-toolbox/what-each-has.md#cobra-toolbox-conversion).

---

## Installation

:::{warning} Installing 3.0.0b1
This site documents RAVEN 3.0.0b1, a pre-release. The Add-Ons manager and the normal releases page of the Release download offer only the latest stable release (RAVEN 2.x), so neither method installs 3.0.0b1. Use the Clone with git tab, or the direct archive link in the Release download tab.
:::

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

The installation runs from within MATLAB with no separate download. The installed version is the latest stable release (RAVEN 2.x), not 3.0.0b1; see the warning at the start of the [Installation](#installation) section.

1. Open the **Home** tab and click **Add-Ons → Get Add-Ons**.
2. Search for **RAVEN Toolbox** and click **Add → Add to MATLAB**.
3. [Verify the installation](#verification).

If MATLAB does not pick up the toolbox after step 2, `matlab.addons.enableAddon("RAVEN")` enables it.
:::
:::{tab-item} {octicon}`download;1em` Release download

This method suits offline or managed environments. The [RAVEN releases page](https://github.com/CompMetEng/RAVEN/releases) lists only stable releases, and 3.0.0b1 is a git tag with no packaged release, so the archive is downloaded directly:

1. Download [the 3.0.0b1 archive](https://github.com/CompMetEng/RAVEN/archive/refs/tags/3.0.0b1.zip). This works without git.
2. Extract it to any location.
3. In MATLAB, add the RAVEN folder to the path (`pathtool`), then [verify](#verification).
:::
:::{tab-item} {octicon}`git-branch;1em` Clone with git

The commands clone the repository and check out the `3.0.0b1` tag. A plain `git clone` tracks the `develop` branch, which can contain changes made after this site's pre-release.

```bash
git clone --depth=1 https://github.com/CompMetEng/RAVEN.git
cd RAVEN
git fetch --depth=1 origin tag 3.0.0b1
git checkout 3.0.0b1
```

Add the folder to the MATLAB path and [verify](#verification).
:::
::::

---

(verify)=
## Verification

From the MATLAB command window:

```matlab
checkRaven
```

The output of a successful run has the form:

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

MATLAB can report that it could not save the path, which is common on shared or managed installations without write access to MATLAB's own `pathdef.m`. In that case, run `addRavenToUserPath`, which writes a `startup.m` that adds RAVEN to the path on every MATLAB start and leaves the shared path file unchanged. `addRavenToUserPath('overwrite', false)` appends to an existing `startup.m`, which is replaced otherwise.

---

## Upgrading

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

In MATLAB, open **Help → Check for Updates**, click **Update** for RAVEN and run `checkRaven` again.
:::
:::{tab-item} {octicon}`download;1em` Release download

Close MATLAB, delete the old RAVEN folder, download and extract the new release and run `checkRaven`.
:::
:::{tab-item} {octicon}`git-branch;1em` Clone with git

The `3.0.0b1` tag does not move, so a checkout of it has nothing to pull. The development branch is followed with:

```bash
git checkout develop
git pull origin develop
```

`develop` can contain unreleased changes. Afterwards, run `checkRaven`.
:::
::::

---

## Removal

::::{tab-set}
:::{tab-item} {octicon}`plug;1em` Add-Ons manager

Open **Add-Ons → Manage Add-Ons** and remove RAVEN from the list. A following call of `removeRavenFromPath` should report an unrecognised-function error, which confirms that RAVEN is off the path.
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

Installation problems are reported as an issue on [GitHub](https://github.com/CompMetEng/RAVEN/issues).
