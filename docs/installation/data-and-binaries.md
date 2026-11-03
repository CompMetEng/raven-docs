# Download data and binaries

Neither toolbox ships the large files that it needs. The KEGG reference data, the libraries of profile hidden Markov models (HMMs) and the executables of BLAST+, DIAMOND and HMMER are fetched on first use from a shared, checksummed release and cached locally. The sections below describe what is fetched, where it is kept and how each step is overridden.

Both toolboxes read from the same [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets) repository, so RAVEN and raven-toolbox download the same files.

## Downloaded artefacts

| Artefact | Download size | Needed for |
|---|---|---|
| KEGG core bundle (reference model and the tables of KOs, reactions and organism genes) | 51 MB | [Reconstruction from KEGG](../guide/kegg.md), both methods |
| KEGG HMM library, one per domain | 140 MB for eukaryotes, 159 MB for prokaryotes | a KEGG draft for an organism that is not in KEGG |
| KEGG taxonomy | 0.2 MB | phylogenetic weighting of KO assignments |
| BLAST+ (`blastp`, `makeblastdb`) | 13 to 35 MB per platform | [Reconstruction from homology](../guide/homology.md) |
| DIAMOND | 3 to 9 MB per platform | the faster homology method |
| HMMER (`hmmsearch`) | 0.2 to 1.8 MB per platform | searching the KEGG HMM library |

Nothing is downloaded until a function needs it. Loading, editing, simulating and comparing models need none of these files.

## Cache locations

raven-toolbox caches under `$XDG_CACHE_HOME`, or under `~/.cache` when that variable is not set, with the same rule on every platform:

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

The path `~/.cache` is used literally on every platform. The platform conventions (`%LOCALAPPDATA%` on Windows and `~/Library/Caches` on macOS) do not apply.

The version is part of the path, so two KEGG releases coexist. A pinned run fetches the pinned release when the cache lacks it.

In MATLAB the KEGG artefacts go to the directory `dataDir`, which `getKEGGModelForOrganism` requires as an argument. The executables are stored in `src/external/<tool>` (`blast+`, `diamond`, `hmmer`) in the RAVEN installation directory on every platform.

## Tool resolution

raven-toolbox resolves an executable in a fixed order and reaches the network at the download step:

```text
explicit binary= argument
  → environment variable (RAVEN_PYTHON_BLASTP, RAVEN_PYTHON_DIAMOND, …)
  → the PATH (a conda, apt, brew or system install)
  → download the pinned bundle, verify its SHA256, cache it
  → an error naming the conda package and the manual alternative
```

An existing installation therefore takes precedence, and the bundled copy is used on a machine without one. The environment variable of a tool is `RAVEN_PYTHON_` followed by the tool name: `RAVEN_PYTHON_BLASTP`, `RAVEN_PYTHON_MAKEBLASTDB`, `RAVEN_PYTHON_DIAMOND`, `RAVEN_PYTHON_HMMSEARCH`, `RAVEN_PYTHON_HMMBUILD`, `RAVEN_PYTHON_HMMPRESS`, `RAVEN_PYTHON_HMMSCAN`, `RAVEN_PYTHON_MAFFT` and `RAVEN_PYTHON_CDHIT`.

## Fetching before first use

A download on first use takes place inside the first run. Both toolboxes can fetch the files before that run.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
downloadRavenBinaries
```

`downloadRavenBinaries` fetches the executables that RAVEN needs into the `src/external/` directory of the RAVEN installation. The KEGG artefacts are fetched separately by the first call of `getKEGGModelForOrganism`, into the `dataDir` given there.
:::
:::{tab-item} 🐍 Python
:sync: python

```bash
raven-toolbox-binaries --list           # what this platform has bundles for
raven-toolbox-binaries --set runtime    # blastp, makeblastdb, diamond, hmmsearch
raven-toolbox-binaries --set build      # hmmbuild, mafft, cd-hit
```

The `runtime` set covers an ordinary reconstruction. The `build` set serves to rebuild the KEGG HMM libraries, which end users do not do.

The command skips anything that is on the `PATH` already, verifies every download against its checksum and reports tools without a bundle for the platform without failing.
:::
::::

## Working offline

`RAVEN_PYTHON_AUTOFETCH` set to `0`, `false`, `no` or `off` stops raven-toolbox from reaching the network. Resolution then stops at the `PATH` and raises an error that names the missing tool, without downloading it. The explicit command `raven-toolbox-binaries` fetches when it is run. An air-gapped setup fetches once on a connected machine, copies the cache and sets the variable.

For data artefacts, an explicit directory replaces the cache. `get_kegg_model_for_organism_from_artefacts` and the related functions take an `artefact_dir=` argument, and `dataDir` of MATLAB is explicit already.

## Platform support

Every tool is invoked as a subprocess, so the availability of a native build for the platform decides the support. The bundles in `toolbox-assets` are built for Linux on x86-64, macOS on Apple silicon (arm64) and Windows on x86-64. Intel Macs and Linux on arm64 have no bundle, and the table applies to the three bundle platforms.

| Tool | Linux | macOS | Windows |
|---|---|---|---|
| BLAST+ | yes | yes | yes |
| DIAMOND | yes | yes | yes |
| HMMER `hmmsearch` | yes | yes | yes |
| HMMER `hmmbuild` | yes | yes | partly |
| MAFFT | yes | yes | no |
| CD-HIT | yes | yes | no |

On Windows, homology reconstruction and the KEGG query path run natively, because they need the first three tools. Building an HMM library needs MAFFT and CD-HIT, which have no Windows builds. Building runs in Windows Subsystem for Linux 2 (WSL2), with Python and the binaries both inside it, because raven-toolbox calls the resolved executable directly and does not translate paths between Windows and WSL.

:::{admonition} Troubleshooting
:class: warning

| Problem | Possible reason | Solution |
|---|---|---|
| A machine without network | The first reconstruction needs to download files, which fails without a network. | Fetch on a connected machine, copy `~/.cache/raven_toolbox` and set `RAVEN_PYTHON_AUTOFETCH=0`. |
| An unexpected version of a tool | The `PATH` takes precedence over the pinned bundle, so a conda environment with an old BLAST+ supplies it without a message. | Point the `RAVEN_PYTHON_*` variable at the intended binary. |
| A read-only or unusual home directory | The cache follows `XDG_CACHE_HOME`. | Set `XDG_CACHE_HOME` to a writable location on a shared or containerised machine. |
| Building HMM libraries on Windows | MAFFT and CD-HIT have no Windows builds. | Use WSL2 with Python and the binaries both inside it. |
| Disk space | The HMM libraries are the largest item, and the first KEGG model build needs a few hundred MB of working space beyond the download. | |
:::

## See also

- [Reconstruction from KEGG](../guide/kegg.md): the workflow that fetches the KEGG artefacts.
- [Reconstruction from homology](../guide/homology.md): the workflow that needs BLAST+ or DIAMOND.
- [RAVEN (MATLAB)](raven.md) and [raven-toolbox (Python)](python.md).
