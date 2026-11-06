<!-- run-examples: skip-file -->

# Update the binary bundles

The BLAST+, DIAMOND and HMMER executables are published as one ZIP file per platform in [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets), and raven-toolbox resolves them at run time through `raven_toolbox.binaries`. [Download data and binaries](data-and-binaries.md) describes the resolution order, the `RAVEN_PYTHON_*` overrides and the `raven-toolbox-binaries` command for users. The sections below describe what a bundle contains and how the package maintainers publish a new one. Release tags are immutable, so a new version of a tool becomes a new tag, and every other tag stays as it is.

The documentation build does not run these commands.

## Contents of a bundle

| Bundle | Included | Left out |
|---|---|---|
| `diamond` | `diamond` | nothing; it is one static binary |
| `blast` | `blastp`, `makeblastdb` | `blastn`, `tblastn`, `psiblast`, `rpsblast`, `blast_formatter`, the `*_vdb` tools, `doc/`, `ChangeLog`, `README` and the other tools of the suite |
| `hmmer` | `hmmsearch` | the rest of the suite |

Both toolboxes invoke `makeblastdb`, `blastp`, and the `makedb` and `blastp` subcommands of DIAMOND, and no other tool, so the same minimal set serves both. For BLAST+ the minimal set reduces the size of the bundle from hundreds of megabytes to a few.

## File name and layout

A ZIP file is named `<bundle>-<version>-<os>-<arch>.zip`. It is flat: the executables lie at the root beside the upstream `LICENSE`, without a nested `bin/` folder. A Windows ZIP carries the `.exe` files and the runtime DLLs that the build needs at the root, `nghttp2.dll` for BLAST+ and `cygwin1.dll` for HMMER, because the extraction is flat and the executable is looked up as `<name>.exe`.

## Platforms and licences

The bundles are built for `linux-x86_64` first, then for `macos-arm64`, `macos-x86_64`, `linux-arm64` and `windows-x86_64`. A platform without a bundle is a supported state: `ensure_binary` raises an error that names the conda package to install.

| Tool | Licence | Requirement for the ZIP |
|---|---|---|
| BLAST+ | produced by NCBI, public domain | the upstream `LICENSE`, for provenance |
| DIAMOND | GPL-3.0 | the licence text, the unmodified binary, and a separate asset outside the wheel |
| HMMER | BSD-3-Clause | the upstream `LICENSE` |

The release body or a provenance file records, for each asset, the upstream URL, the upstream version, the upstream checksum and the published SHA-256 sum.

## HMMER on Windows

No native Windows build of HMMER 3.4 exists, because upstream targets POSIX systems. The published `windows-x86_64` asset is HMMER 3.3.2, repackaged from RAVEN v2.10.5, the last release that bundles a Cygwin-compiled Windows build. The file `cygwin1.dll` ships beside the `.exe`.

Searching profiles that HMMER 3.4 built with HMMER 3.3.2 is sound for the published libraries. They are concatenated ASCII files in the `HMMER3/f` format, which is unchanged from HMMER 3.1 to 3.4, and HMMER 3.4 is a maintenance release over 3.3.2 without a change of the protein scoring model. The bit scores and the calibrated KEGG cut-offs therefore carry over. This holds while the libraries stay in ASCII format.

## Publish a bundle

Run the commands from the root of a checkout of raven-toolbox.

```bash
python scripts/build_binary_bundles.py
python scripts/publish_to_toolbox_assets.py binaries --dir dist/binaries
python scripts/make_registry_snippet.py manifest --manifest data/manifest.json \
    --target binary --bundle blast --version 2.17.0 --provides blastp makeblastdb \
    --dir dist/binaries --tag blast-2.17.0
python scripts/make_registry_snippet.py sync
```

The first command builds the ZIP files from the vetted binaries in the `software/` folder of RAVEN into `dist/binaries`, with checksums and provenance. The second creates the release tags in `toolbox-assets` and skips the assets that exist. The third computes the checksums with the helper that `ensure_binary` verifies with, and writes the entry of the bundle to `data/manifest.json`. A bundle with a licence that needs a statement takes `--license`, for example `--license GPL-3.0-only` for DIAMOND. The fourth regenerates the baked registries of raven-toolbox from the manifest.

`data/manifest.json` is the single source of truth, and the registries `_DATA_REGISTRY` in `src/raven_toolbox/data.py` and `_REGISTRY` in `src/raven_toolbox/binaries.py` are never edited by hand. The manifest is published as the next `manifest-v<N>` snapshot, as step 5 of [Update the KEGG assets](updating-kegg-assets.md) describes.

A new tool needs no new provisioning code. A bundle entry with the right `provides` list and ZIP files that follow the layout above are enough for the wrappers to resolve the tool through `ensure_binary`.

## See also

- [Download data and binaries](data-and-binaries.md): what a user downloads, and where the files are cached.
- [Update the KEGG assets](updating-kegg-assets.md): the same publication steps for the KEGG release.
