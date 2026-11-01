# Homology cut-off calibration

Scripts for the homology cut-off page of the parameter-tuning documentation. *S. cerevisiae* (`sce`) is the template against *K. lactis* (`kla`), *Y. lipolytica* (`yli`), *A. nidulans* (`ani`) and *E. coli* (`eco`). The gene-to-KO assignment is scored as F0.5 against the KEGG release 118 table, current KEGG and OMA orthologues over sequence identity, alignment length and E-value. BLAST and DIAMOND are compared, and the BLAST E-value and thread settings are tested on *H. polymorpha* against *S. cerevisiae*. The driver is `scripts/homology_cutoff_kegg.py` of raven-toolbox.

## Inputs and environment

| Input | Source |
| --- | --- |
| UniProt proteomes | UP000002311, UP000001300, UP000000560, UP000000625, UP000000598 (release 2026_03) |
| KEGG release 118 | `kegg118_core.tar.gz` of [CompMetEng/toolbox-assets](https://github.com/CompMetEng/toolbox-assets/releases/tag/kegg118), SHA-256 `520ba8bb09d6ca479ca1ab84ea70bf7c1d7f82d8f6406b717cee293b7c8609ca` |
| current KEGG | REST API (`link/ko`, restricted to KOs in `link/reaction/ko`, and all KOs) |
| OMA | `All.May2026`, `https://omabrowser.org/api/pairs/<target>/559292/` |
| SGD | `orf_trans_all.fasta.gz` of `sgd-archive.yeastgenome.org/sequence/S288C_reference/orf_protein` |
| *H. polymorpha* | `data/genomes/hanpo.faa` of the hanpo-GEM repository (5177 sequences) |

`job_fetch.sh` downloads the inputs into `homology-inputs.tar.zst` (proteomes, UniProt cache, reference tables); `job_align_score.sh` writes the hit tables to `homology-hits.tar.zst`. Download manifests with URLs, sizes and SHA-256 are in `results/inputs/`.

| Variable | Meaning |
| --- | --- |
| `STUDY` | this folder |
| `TOOLBOX_ROOT` | raven-toolbox checkout (`94f3940`) |
| `PY` | Python interpreter with pandas |
| `DATA` | folder of the two archives |
| `BINARIES_CACHE` | `raven_toolbox/binaries` cache with BLAST+ 2.17.0 and DIAMOND 2.1.17 |
| `HANPO_FAA` | `hanpo.faa` (aligner-settings job) |
| `HOMOLOGY_SCRIPT`, `HOMOLOGY_URL_CACHE`, `HOMOLOGY_OFFLINE` | read by `run_cached.py`: path of the driver, UniProt cache folder, offline switch (set by the jobs) |

The module names in the job files are site-specific; other systems need an equivalent environment.

## Commands

```bash
export STUDY=... TOOLBOX_ROOT=... PY=... DATA=... BINARIES_CACHE=... HANPO_FAA=...
sbatch -A <account> $STUDY/job_fetch.sh
sbatch -A <account> $STUDY/job_align_score.sh
sbatch -A <account> $STUDY/job_aligner_settings.sh
```

The jobs run the following, with `W` the extracted `homology-inputs/` folder, `REFS=$W/refs`, `K118=$REFS/kegg118_organism_gene_ko_5org.tsv.gz` and `RES` the results folder. `--out` goes before the subcommand. Each `score` run writes `hitlevel_results.json` into `$W`, which the job copies to `$RES/<name>.json` with the name in the comment.

```bash
python run_cached.py --out $W fetch
python run_cached.py prefetch --out $W                       # UniProt tables and OMA pairs
python fetch_references.py --out $REFS --kegg118-sha256 520ba8bb09d6ca479ca1ab84ea70bf7c1d7f82d8f6406b717cee293b7c8609ca
python run_cached.py --out $W align                          # BLAST, 4 threads, E-value 1e-4
python run_cached.py --out $W align --aligner diamond        # DIAMOND, 4 threads, E-value 1e-3, --more-sensitive
python run_cached.py --out $W score --beta 0.5 --gene-ko $K118                                  # kegg118_blast_b0.5
python run_cached.py --out $W score --beta 0.5 --gene-ko $K118 --aligner diamond                # kegg118_diamond_b0.5
python run_cached.py --out $W score --beta 1   --gene-ko $K118                                  # kegg118_blast_b1
python run_cached.py --out $W score --beta 1   --gene-ko $K118 --aligner diamond                # kegg118_diamond_b1
python run_cached.py --out $W score --beta 0.5 --gene-ko $K118 --reference oma                  # oma_blast_b0.5
python run_cached.py --out $W score --beta 0.5 --gene-ko $K118 --reference oma --aligner diamond  # oma_diamond_b0.5
python run_cached.py --out $W score --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_rxn.tsv.gz                    # keggrest_rxn_blast_b0.5
python run_cached.py --out $W score --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_rxn.tsv.gz --aligner diamond  # keggrest_rxn_diamond_b0.5
python run_cached.py --out $W score --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_all.tsv.gz                    # keggrest_all_blast_b0.5 (BLAST)
python agreement.py --work $W --gene-ko $K118 --out $RES/agreement.tsv
python aligner_settings.py --hanpo $HANPO_FAA --template <sgd_orf_trans_all.fasta> \
    --bindir $BINARIES_CACHE/blast-2.17.0-linux-x86_64 --work $TMPDIR/as --out $RES/aligner_settings.json --threads 4 --single-thread-full
python make_tables.py --res $RES > $RES/tables.md
```

## Outputs

| File | Content |
| --- | --- |
| `run_cached.py` | Runs the driver with its UniProt download function replaced by a disk cache, so that `score --reference oma` reads the UniProt tables offline. |
| `results/<name>.json` | Driver output of each score run (reference, aligner, beta). |
| `results/all_rows.tsv`, `results/tables.md` | Every scored setting of every score file, and all tables of the page including identity 20 and 60, DIAMOND length and E-value rows, current-KEGG and OMA sweeps (`make_tables.py`). |
| `results/agreement.tsv` | Jaccard index of the surviving (template gene, target gene) pairs of BLAST and DIAMOND (`agreement.py`). |
| `results/aligner_settings.json`, `results/align_blast.txt`, `results/align_diamond.txt` | *H. polymorpha* hits at BLAST E-value 1e-4 and 1e-5 with a row-level difference, thread test (first 500 sequences at 1 and 4 threads), single-thread timing of the full directions; hit counts of the alignments. |
| `results/inputs/` | Download manifests, KEGG REST info and OMA version. |
