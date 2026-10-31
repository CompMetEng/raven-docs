# Download data and binaries

Neither toolbox ships the large files it needs. The KEGG reference data, the profile hidden Markov model (HMM) libraries and the BLAST+, DIAMOND and HMMER executables are fetched on first use from a shared, checksummed release and cached locally. This page covers what is fetched, where it is kept and how to override each step.

Both toolboxes read from the same [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository, so the files RAVEN downloads and the files raven-toolbox downloads are the same files.

## Downloaded artefacts

| Artefact | Size | Needed for |
|---|---|---|
| KEGG core bundle (reference model plus the KO, reaction and organism-gene tables) | about 47 MB | [Reconstruction from KEGG](../guide/kegg.md), either method |
| KEGG HMM library, one per domain | 129 MB compressed, eukaryotes | a KEGG draft for an organism KEGG has never seen |
| KEGG taxonomy | small | phylogenetic weighting of KO assignments |
| BLAST+ (`blastp`, `makeblastdb`) | small | [Reconstruction from homology](../guide/homology.md) |
| DIAMOND | small | the faster homology method |
| HMMER (`hmmsearch`) | small | searching the KEGG HMM library |

Nothing is downloaded until a function needs it. Loading, editing, simulating and comparing models require none of it.

## Cache locations

raven-toolbox caches under `$XDG_CACHE_HOME`, or `~/.cache` when that is unset, using the same rule on every platform:

::::{tab-set}
:::{tab-item} Linux

| Item | Path |
|---|---|
| Data artefacts | `/home/<user>/.cache/raven_toolbox/data/<dataset>-<version>/` |
| Binaries | `/home/<user>/.cache/raven_toolbox/binaries/` |
:::
:::{tab-item} macOS

| Item | Path |
|---|---|
| Data artefacts | `/Users/<user>/.cache/raven_toolbox/data/<dataset>-<version>/` |
| Binaries | `/Users/<user>/.cache/raven_toolbox/binaries/` |
:::
:::{tab-item} Windows

| Item | Path |
|---|---|
| Data artefacts | `C:\Users\<user>\.cache\raven_toolbox\data\<dataset>-<version>\` |
| Binaries | `C:\Users\<user>\.cache\raven_toolbox\binaries\` |
:::
::::

The path `~/.cache` is used literally on every platform, and the platform conventions (`%LOCALAPPDATA%` on Windows, `~/Library/Caches` on macOS) do not apply.

The version is part of the path, so two KEGG releases coexist and a pinned run fetches the release it was pinned to when that release is missing from the cache.

In MATLAB the KEGG artefacts go to the directory `dataDir`, which `getKEGGModelForOrganism` requires as an argument. The executables are stored in `software/` inside the RAVEN installation directory on every platform.

## Tool resolution

raven-toolbox resolves an executable in a fixed order and reaches the network only at the download step:

```text
explicit binary= argument
  → environment variable (RAVEN_PYTHON_BLASTP, RAVEN_PYTHON_DIAMOND, …)
  → the PATH (a conda, apt, brew or system install)
  → download the pinned bundle, verify its SHA256, cache it
  → an error naming the conda package and the manual alternative
```

An existing installation therefore takes precedence, and the bundled copy is used only on a machine without one. The environment variable per tool is `RAVEN_PYTHON_` followed by the tool name: `RAVEN_PYTHON_BLASTP`, `RAVEN_PYTHON_MAKEBLASTDB`, `RAVEN_PYTHON_DIAMOND`, `RAVEN_PYTHON_HMMSEARCH`, `RAVEN_PYTHON_HMMBUILD`, `RAVEN_PYTHON_HMMPRESS`, `RAVEN_PYTHON_HMMSCAN`, `RAVEN_PYTHON_MAFFT`, `RAVEN_PYTHON_CDHIT`.

## Fetching before first use

Downloading on first use puts the download inside the first run, which is not always where it should be. Both toolboxes can fetch the files before that run.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
downloadRavenBinaries
```

`downloadRavenBinaries` fetches the executables that RAVEN needs into its `software/` directory. The KEGG artefacts are fetched separately, on the first `getKEGGModelForOrganism` call, into the `dataDir` given there.
:::
:::{tab-item} 🐍 Python
:sync: python

```bash
raven-toolbox-binaries --list           # what this platform has bundles for
raven-toolbox-binaries --set runtime    # blastp, makeblastdb, diamond, hmmsearch
raven-toolbox-binaries --set build      # hmmbuild, mafft, cd-hit
```

The `runtime` set covers an ordinary reconstruction. The `build` set is for rebuilding the KEGG HMM libraries, which end users do not do.

The command skips anything already on the `PATH`, verifies every download against its checksum and reports tools with no bundle for the platform without failing.
:::
::::

## Working offline

Setting `RAVEN_PYTHON_AUTOFETCH` to `0`, `false`, `no` or `off` stops raven-toolbox from reaching the network. Resolution then stops at the `PATH` and raises an error that names the missing tool, without downloading it. The explicit `raven-toolbox-binaries` command fetches when run. An air-gapped setup fetches once on a connected machine, copies the cache and sets the variable.

For data artefacts, an explicit directory replaces the cache: `get_kegg_model_for_organism_from_artefacts` and its siblings take an `artefact_dir=` argument, and MATLAB's `dataDir` is already explicit.

## Platform support

Every tool is invoked as a subprocess, so the availability of a native build for the platform decides support.

| Tool | Linux | macOS | Windows |
|---|---|---|---|
| BLAST+ | yes | yes | yes |
| DIAMOND | yes | yes | yes |
| HMMER `hmmsearch` | yes | yes | yes |
| HMMER `hmmbuild` | yes | yes | partly |
| MAFFT | yes | yes | no |
| CD-HIT | yes | yes | no |

On Windows, homology reconstruction and the KEGG query path run natively, since they need only the first three tools. Building an HMM library needs MAFFT and CD-HIT, which have no Windows builds. Use Windows Subsystem for Linux 2 (WSL2) for that and keep the whole stack inside it, since raven-toolbox calls the resolved executable directly and does not translate paths between Windows and WSL.

:::{warning} Troubleshooting
| Problem | Possible reason | Solution |
|---|---|---|
| A machine with no network | The first reconstruction needs to download files, which fails without a network. | Fetch on a connected machine, copy `~/.cache/raven_toolbox` and set `RAVEN_PYTHON_AUTOFETCH=0`. |
| An unexpected version of a tool | The `PATH` takes precedence over the pinned bundle, so a conda environment carrying an old BLAST+ supplies it without a message. | Point the `RAVEN_PYTHON_*` variable at the intended binary. |
| A read-only or unusual home directory | The cache follows `XDG_CACHE_HOME`. | Set `XDG_CACHE_HOME` to a writable location on a shared or containerised machine. |
| Building HMM libraries on Windows | MAFFT and CD-HIT have no Windows builds. | Use WSL2 and keep Python and the binaries both inside it. |
| Disk space | The HMM libraries are the large item, and the first KEGG model build needs a few hundred MB of working space beyond the download. | |
:::

## See also

- [Reconstruction from KEGG](../guide/kegg.md), the workflow that fetches the KEGG artefacts.
- [Reconstruction from homology](../guide/homology.md), the workflow that needs BLAST+ or DIAMOND.
- [RAVEN (MATLAB)](raven.md) and [raven-toolbox (Python)](python.md).
