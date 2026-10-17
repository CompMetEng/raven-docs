# Download data and binaries

Neither toolbox ships the large files it needs. The KEGG reference data, the
profile-HMM libraries, and the BLAST+, DIAMOND and HMMER executables are all
fetched on first use from a shared, checksummed release and cached locally. This
page covers what is fetched, where it is kept, and how to override each step.

Both toolboxes read from the same
[`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository, so the
files RAVEN downloads and the files raven-toolbox downloads are the same files.

## What gets downloaded

| Artefact | Size | Needed for |
|---|---|---|
| KEGG core bundle (reference model plus the KO, reaction and organism-gene tables) | about 47 MB | [13. Reconstruction from KEGG](../guide/kegg.md), either route |
| KEGG HMM library, one per domain | 129 MB compressed, eukaryotes | a KEGG draft for an organism KEGG has never seen |
| KEGG taxonomy | small | phylogenetic weighting of KO assignments |
| BLAST+ (`blastp`, `makeblastdb`) | small | [12. Reconstruction from homology](../guide/homology.md) |
| DIAMOND | small | the faster homology route |
| HMMER (`hmmsearch`) | small | searching the KEGG HMM library |

Nothing is downloaded until something needs it. Loading, editing, simulating and
comparing models require none of it.

## Where it goes

raven-toolbox caches under `$XDG_CACHE_HOME`, or `~/.cache` when that is
unset, using the same rule on every platform:

::::{tab-set}
:::{tab-item} Linux

| | Path |
|---|---|
| Data artefacts | `/home/<user>/.cache/raven_toolbox/data/<dataset>-<version>/` |
| Binaries | `/home/<user>/.cache/raven_toolbox/binaries/` |
:::
:::{tab-item} macOS

| | Path |
|---|---|
| Data artefacts | `/Users/<user>/.cache/raven_toolbox/data/<dataset>-<version>/` |
| Binaries | `/Users/<user>/.cache/raven_toolbox/binaries/` |
:::
:::{tab-item} Windows

| | Path |
|---|---|
| Data artefacts | `C:\Users\<user>\.cache\raven_toolbox\data\<dataset>-<version>\` |
| Binaries | `C:\Users\<user>\.cache\raven_toolbox\binaries\` |
:::
::::

raven-toolbox does not use each platform's own convention (`%LOCALAPPDATA%`
on Windows, `~/Library/Caches` on macOS); `~/.cache` is literal everywhere.

The version is part of the path, so two KEGG releases coexist and a pinned run
keeps fetching the release it was pinned to.

In MATLAB the KEGG artefacts go wherever `dataDir` points, which
`getKEGGModelForOrganism` requires you to pass, and the executables live in
`software/` inside wherever RAVEN itself is installed, the same on every
platform.

## How a tool is found

raven-toolbox resolves an executable in a fixed order and only reaches the
network at the end:

```text
explicit binary= argument
  → environment variable (RAVEN_PYTHON_BLASTP, RAVEN_PYTHON_DIAMOND, …)
  → the PATH (a conda, apt, brew or system install)
  → download the pinned bundle, verify its SHA256, cache it
  → an error naming the conda package and the manual alternative
```

An existing installation therefore takes precedence, and the bundled copy is
reached only on a machine that has none. The environment variable per tool is
`RAVEN_PYTHON_` followed by the tool name: `RAVEN_PYTHON_BLASTP`,
`RAVEN_PYTHON_MAKEBLASTDB`, `RAVEN_PYTHON_DIAMOND`, `RAVEN_PYTHON_HMMSEARCH`,
`RAVEN_PYTHON_HMMBUILD`, `RAVEN_PYTHON_HMMPRESS`, `RAVEN_PYTHON_HMMSCAN`,
`RAVEN_PYTHON_MAFFT`, `RAVEN_PYTHON_CDHIT`.

## Fetching ahead of time

Downloading on first use puts the download inside the first run, which is not
always where it should be. Both toolboxes can fetch ahead of that.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
downloadRavenBinaries
```

Fetches the executables RAVEN needs into its `software/` directory. The KEGG
artefacts arrive separately, on the first `getKEGGModelForOrganism` call, into
the `dataDir` given there.
:::
:::{tab-item} 🐍 Python
:sync: python

```bash
raven-toolbox-binaries --list           # what this platform has bundles for
raven-toolbox-binaries --set runtime    # blastp, makeblastdb, diamond, hmmsearch
raven-toolbox-binaries --set build      # hmmbuild, mafft, cd-hit
```

The `runtime` set is what an ordinary reconstruction needs. The `build` set is
for rebuilding the KEGG HMM libraries, which end users do not do.

The command skips anything already on the `PATH`, verifies every download
against its checksum, and reports tools with no bundle for this platform
rather than failing.
:::
::::

## Working offline

Setting `RAVEN_PYTHON_AUTOFETCH` to `0`, `false`, `no` or `off` stops
raven-toolbox reaching the network at all. Resolution then stops at the `PATH`
and raises an error naming what is missing, instead of downloading it. The
explicit `raven-toolbox-binaries` command still fetches when run, so an
air-gapped setup is: fetch once on a connected machine, copy the cache, and set
the variable.

For data artefacts, pass an explicit directory instead of relying on the cache:
`get_kegg_model_for_organism_from_artefacts` and its siblings take an
`artefact_dir=`, and MATLAB's `dataDir` is already explicit.

## What runs where

Every tool is invoked as a subprocess, so what matters is whether a native build
exists for the platform.

| Tool | Linux | macOS | Windows |
|---|---|---|---|
| BLAST+ | yes | yes | yes |
| DIAMOND | yes | yes | yes |
| HMMER `hmmsearch` | yes | yes | yes |
| HMMER `hmmbuild` | yes | yes | partly |
| MAFFT | yes | yes | no |
| CD-HIT | yes | yes | no |

On Windows this means homology reconstruction and the KEGG query path both run
natively, since they need only the first three. **Building** an HMM library does
not, because that needs MAFFT and CD-HIT, which have no Windows builds. Use WSL2 for that, keeping the whole stack inside it, since raven-toolbox
calls the resolved executable directly and does not translate paths between
Windows and WSL.

:::{warning} What can go wrong
- **A machine with no network.** The first reconstruction fails at the
  download. Fetch on a connected machine, copy `~/.cache/raven_toolbox`, and
  set `RAVEN_PYTHON_AUTOFETCH=0`.
- **An unexpected version of a tool.** The `PATH` takes precedence over the
  pinned bundle, so a conda environment carrying an old BLAST+ supplies it
  with no message. Point the `RAVEN_PYTHON_*` variable at the intended
  binary.
- **A read-only or unusual home directory.** The cache follows
  `XDG_CACHE_HOME`; set it somewhere writable on a shared or containerised
  machine.
- **Trying to build HMM libraries on Windows.** MAFFT and CD-HIT have no
  Windows builds. Use WSL2, and keep Python and the binaries both inside it.
- **Disk.** The HMM libraries are the large item, and the first KEGG model
  build needs a few hundred MB of working space beyond the download.
:::

## See also

- [13. Reconstruction from KEGG](../guide/kegg.md), the workflow that pulls the
  KEGG artefacts.
- [12. Reconstruction from homology](../guide/homology.md), the one that needs
  BLAST+ or DIAMOND.
- [Installing RAVEN](raven.md) and [Installing raven-toolbox](python.md).
