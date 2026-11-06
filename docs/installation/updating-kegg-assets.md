<!-- run-examples: skip-file -->

# Update the KEGG assets

The KEGG reference data and the libraries of profile hidden Markov models (HMMs) are published as assets of one KEGG release in [`toolbox-assets`](https://github.com/CompMetEng/toolbox-assets). Both toolboxes download them, as described in [Download data and binaries](data-and-binaries.md). A new KEGG release needs a new set of assets. The package maintainers do this when they adopt a new KEGG release, and users of the toolboxes never do.

The documentation build does not run these commands. The download needs a KEGG subscription, and the build of the libraries takes hours.

## Assets of one release

A release has the name `kegg<N>`, with `N` the KEGG release number, and four assets that have the name as a prefix.

| Asset | Content |
|---|---|
| `kegg<N>_core.tar.gz` | the gene-free reference model as gzipped YAML and the relational tables as gzipped TSV, among them `organism_gene_ko` |
| `kegg<N>_eukaryotes.hmm.gz` | the profile HMM library of the eukaryotic organisms |
| `kegg<N>_prokaryotes.hmm.gz` | the profile HMM library of the prokaryotic organisms |
| `kegg<N>_taxonomy.gz` | the KEGG `taxonomy` file, which assigns each organism to a domain and which `PhylDist` reads |

Each library holds one profile per KO in ASCII HMMER format, compressed with gzip. It is not indexed with `hmmpress`: `hmmsearch` reads the decompressed file, the gzip file is roughly ten times smaller than a binary index, MATLAB and Python read the same file, and the file stays readable across HMMER versions. The native Windows build of `hmmsearch` is an older version (3.3.2) than the Linux and macOS builds.

Release tags are immutable. A release that is published under a name is not changed afterwards, and a correction becomes a new release.

## Requirements

- A subscription to the bulk download of KEGG (`ftp.kegg.net`), which comes with a user name and a password.
- raven-toolbox from a checkout of its repository, installed as described in [Installing RAVEN](python.md). The commands run from the root of that checkout.
- HMMER (`hmmbuild`), MAFFT and CD-HIT, on the `PATH` or pointed at with the environment variables `RAVEN_PYTHON_HMMBUILD`, `RAVEN_PYTHON_MAFFT` and `RAVEN_PYTHON_CDHIT`. MAFFT and CD-HIT have no native Windows build, so the build runs on Linux, macOS or inside WSL2. Keep the whole toolchain inside WSL2, because raven-toolbox calls the resolved executable directly and does not translate paths across the boundary.
- The GitHub CLI `gh`, authenticated with write access to `toolbox-assets`.
- Disk space for the dump and for the per-KO working files of the build, and enough memory for the largest alignments of MAFFT. MAFFT switches to a memory-light method for an alignment that is predicted to need more memory than the host has, and that method approximates the guide tree.

The downloader reads the KEGG credentials from `~/.netrc` and takes none on the command line, so they stay out of the shell history and the process list. Create the file with mode 600 and add one line with your own credentials:

```text
machine ftp.kegg.net login YOUR_KEGG_USER password YOUR_KEGG_PASSWORD
```

The host must be `ftp.kegg.net`, and Python's `netrc` parser refuses a file that others can read. To keep the credentials outside the home directory, pass `netrc_path=` to `download_kegg_dump`.

## Update procedure

The commands below use `kegg120`. Replace it with the name of the release.

### 1. Download the KEGG dump

```python
from raven_toolbox.reconstruction.kegg import download_kegg_dump

download_kegg_dump("keggdb", force=True, progress=False)
```

The function fetches the reaction, compound, glycan and KO archives, the proteomes and the taxonomy file, extracts them and arranges the flat layout that the parser expects. Without `force=True`, it skips files that exist, so use it for a new release in a directory that holds an older dump.

### 2. Build the assets

```bash
python scripts/build_kegg_artefacts.py --keggdb keggdb --out artefacts \
    --version kegg120 --hmms --threads 16
```

The script parses the dump into the reference model and the tables, builds the library of each domain from the sequences of the KOs, and arranges the four assets in `artefacts`. `--domains` restricts the libraries to one domain.

The build of the libraries is the slow step. The script resumes: it skips a stage whose output exists, and it skips every KO whose profile exists in the working directory `artefacts/_hmms-<domain>`. Run the same command again after a failure. `--force` rebuilds everything, and a changed gene-to-KO table needs it, because a resumed run assumes the inputs of the first run.

The working directory holds one FASTA file and one profile per KO. On a file system with a quota on the number of files, put `artefacts` on a file system without that quota.

### 3. Check the assets

- The four files of the table exist in `artefacts`, and their sizes are of the same order as the previous release (49 MB, 135 MB, 155 MB and 0.2 MB for `kegg118`).
- The number of profiles in a library is the number of lines that start with `NAME` in the decompressed file. Compare it with the previous release.
- Reconstruct a draft for an organism that KEGG contains, for example *S. cerevisiae*, with `get_kegg_model_for_organism_from_artefacts`, and search its proteome against the eukaryotic library with `get_kegg_model_from_sequences_with_artefacts`. The assignment of the search should resemble the KEGG assignment of the organism. Both functions are described in [Reconstruction from KEGG](../guide/kegg.md).
- Record the KEGG release and the versions of HMMER, MAFFT and CD-HIT of the build.

### 4. Publish the assets

```bash
python scripts/publish_to_toolbox_assets.py --dry-run release --tag kegg120 --dir artefacts
python scripts/publish_to_toolbox_assets.py release --tag kegg120 --dir artefacts
```

The first command prints the `gh` calls without running them. The second creates the release `kegg120` in `toolbox-assets` and uploads the four assets. A rerun uploads only the assets that are missing.

### 5. Update the manifest and the registry

The manifest `data/manifest.json` is the single source of truth for the checksums of the assets. Never edit the registry in `src/raven_toolbox/data.py` by hand.

```bash
python scripts/make_registry_snippet.py manifest --manifest data/manifest.json \
    --target data --dataset kegg --version kegg120 --dir artefacts --tag kegg120
python scripts/make_registry_snippet.py sync
python scripts/publish_to_toolbox_assets.py release --tag manifest-v4 data/manifest.json
```

The first command computes the URL, the SHA-256 sum and the size of each asset and writes them to the manifest. The second regenerates the registry that raven-toolbox includes from the manifest. The third publishes the manifest as a new snapshot. The number of the snapshot is the next number after the newest `manifest-v<M>` release in `toolbox-assets`.

### 6. Point the toolboxes to the new release

- **raven-toolbox:** commit the changes to `data/manifest.json` and `src/raven_toolbox/data.py`, and open a pull request. raven-toolbox pins the manifest of its release, so users receive the new KEGG release with the next raven-toolbox release. The environment variable `RAVEN_PYTHON_MANIFEST` points an installed raven-toolbox to a newer manifest.
- **RAVEN:** write the new release name in the first line of `src/reconstruction/kegg/KEGG_VERSION.md`, which `keggDataVersion` reads, and change the manifest URL in `fetchToolboxAsset` to the new snapshot. RAVEN reads the manifest on each call.
- **raven-docs:** update the sizes in [Download data and binaries](data-and-binaries.md), and rerun the examples of [Reconstruction from KEGG](../guide/kegg.md) with the new release. That page quotes the release, the counts of the drafts and the timings.

A new KEGG release changes the drafts. Adopt it in a release of the toolboxes after a review of the changes in the drafts of a few organisms against the previous release.

## Run the build on a cluster

A batch job runs the build script with a time limit that covers the longest expected run. A resubmission of the same job continues where the previous job stopped. An example for Slurm:

```bash
#!/bin/bash
#SBATCH -A <account>
#SBATCH -n 16
#SBATCH -t 7-00:00:00
#SBATCH -J kegg-assets

python scripts/build_kegg_artefacts.py --keggdb keggdb --out artefacts \
    --version kegg120 --hmms --threads 16
```

## See also

- [Download data and binaries](data-and-binaries.md): what a user downloads, and where the files are cached.
- [Publishing versioned artefacts](https://github.com/CompMetEng/raven-gecko-parity/blob/develop/docs/publishing_artefacts.md): the convention for tags, manifests and checksums.
