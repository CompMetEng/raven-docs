<!-- run-examples: skip-file -->

# Update the binary bundles

The BLAST+, DIAMOND and HMMER executables are published as one ZIP file per platform in [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets), and raven-toolbox resolves them at run time through `raven_toolbox.binaries`. [Download data and binaries](data-and-binaries.md) describes the resolution order, the `RAVEN_PYTHON_*` overrides and the `raven-toolbox-binaries` command for users. A new version of a tool is a new release tag, and every other tag stays as it is.

The documentation build does not run the commands below.

## Contents of a bundle

| Bundle | Included | Left out |
|---|---|---|
| `diamond` | `diamond` | nothing; the bundle is one executable |
| `blast` | `blastp`, `makeblastdb` | the other executables and the documentation of the suite |
| `hmmer` | `hmmsearch` | the rest of the suite |

A bundle holds the executables that the toolboxes invoke for a user: `makeblastdb` and `blastp` of BLAST+, the `makedb` and `blastp` subcommands of DIAMOND, and `hmmsearch` of HMMER. The build of the KEGG libraries needs `hmmbuild`, MAFFT and CD-HIT as well; they are not bundled, and [Update the KEGG assets](updating-kegg-assets.md) lists them. The published BLAST+ ZIP files are 13 to 35 MB, depending on the platform.

## File name and layout

A ZIP file is named `<bundle>-<version>-<os>-<arch>.zip`. It is flat: the executables lie at the root beside the upstream `LICENSE`, without a nested `bin/` folder. A Windows ZIP carries the `.exe` files and the runtime DLLs of the executables at the root, `nghttp2.dll` for BLAST+ and `cygwin1.dll` for HMMER, because the extraction is flat and the executable is looked up as `<name>.exe`.

## Platforms and licences

`scripts/build_binary_bundles.py` builds the bundles for `linux-x86_64`, `macos-arm64` and `windows-x86_64`. The `macos-arm64` bundle serves Apple Silicon. On a platform without a bundle, `ensure_binary` raises an error that gives the `conda install -c bioconda` command for the executable.

| Tool | Licence | Requirement for the ZIP |
|---|---|---|
| BLAST+ | produced by NCBI, public domain | the upstream `LICENSE`, for provenance |
| DIAMOND | GPL-3.0 | the licence text, the unmodified binary, and a separate asset that is not part of the raven-toolbox package |
| HMMER | BSD-3-Clause | the upstream `LICENSE` |

`PROVENANCE-binaries.txt` in the repository `toolbox-assets` records the source of the executables. It holds the content of the `PROVENANCE.txt` that the build script writes, and the publish command does not upload it.

## HMMER on Windows

No native Windows build of HMMER 3.4 exists, because upstream targets POSIX systems. The published `windows-x86_64` asset is HMMER 3.3.2, repackaged from RAVEN v2.10.5, the last release that bundles a Cygwin-compiled Windows build. The file `cygwin1.dll` ships beside the `.exe`.

The libraries that HMMER 3.4 builds are concatenated ASCII files in the `HMMER3/f` format, which is unchanged from HMMER 3.1 to 3.4, and HMMER 3.4 is a maintenance release over 3.3.2 without a change of the protein scoring model. HMMER 3.3.2 therefore gives the same bit scores on these libraries, and the calibrated KEGG cut-offs carry over. This holds while the libraries stay in ASCII format.

## Publish a bundle

Run the commands from the root of a checkout of raven-toolbox.

```bash
python scripts/build_binary_bundles.py
python scripts/publish_to_toolbox_assets.py binaries --dir dist/binaries
python scripts/make_registry_snippet.py manifest --manifest data/manifest.json \
    --target binary --bundle blast --version 2.17.0 --provides blastp makeblastdb \
    --dir dist/binaries --tag blast-2.17.0 --description "<text>" --license "<licence>"
python scripts/make_registry_snippet.py sync
```

The first command downloads the executables from the RAVEN release v2.10.5 and from a pinned commit of RAVEN on GitHub, and builds the ZIP files in `dist/binaries` with checksums. The second creates the release tags in `toolbox-assets` and skips the assets that exist. The third computes the checksums with the helper that `ensure_binary` verifies with, and writes the entry of the bundle to `data/manifest.json`. It runs once for each bundle, and it replaces the whole entry of the bundle, so `--description` and `--license` repeat the values of the existing entry (`GPL-3.0-only` for DIAMOND). It takes the ZIP files whose names start with `<bundle>-<version>-`. The entry of `hmmer` in the published manifest lists the Windows file of version 3.3.2 beside the files of version 3.4.0. That platform is added to `data/manifest.json` by hand, with the URL and the checksum of the file. The fourth regenerates the baked registries of raven-toolbox from the manifest.

`data/manifest.json` is the source of truth, and the registries `_DATA_REGISTRY` in `src/raven_toolbox/data.py` and `_REGISTRY` in `src/raven_toolbox/binaries.py` are never edited by hand. The manifest is published as the next `manifest-v<N>` snapshot, as step 5 of [Update the KEGG assets](updating-kegg-assets.md) describes.

## A new version or a new tool

- **New version of a tool:** the versions, the source references and the `PROVIDES` table are values in `scripts/build_binary_bundles.py` (`SPECS`, `RAVEN3`, `V2105`, `PROVIDES`). `downloadRavenBinaries.m` of RAVEN names the tags and the asset names and needs the new tag.
- **New tool:** an entry in `_ENV_VARS` of `raven_toolbox.binaries` adds the environment variable that overrides the executable, and an entry in `BINARY_SETS` adds the executable to the downloads of the command `raven-toolbox-binaries`.
- **Both toolboxes** read the new manifest snapshot after the update: the manifest URL in `fetchToolboxAsset.m` and the baked registry of raven-toolbox.

## See also

- [Download data and binaries](data-and-binaries.md): what a user downloads, and where the files are cached.
- [Update the KEGG assets](updating-kegg-assets.md): the same publication steps for the KEGG release.
