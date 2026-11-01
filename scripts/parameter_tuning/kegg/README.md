# KEGG HMM cut-off calibration

Scripts for the KEGG HMM cut-off page of the parameter-tuning documentation. The gene-to-KO assignment of the `kegg118` HMM libraries is scored against the gene-to-KO and KO-to-reaction tables of the `kegg118` release for *S. cerevisiae* (`sce`), *C. merolae* (`cme`), *E. coli* (`eco`) and *M. genitalium* (`mge`), over E-value, `min_score_ratio_ko` and `min_score_ratio_g`. The annotation path and the HMM path are compared for whole models.

## Inputs and environment

The reference tables and HMM libraries are the `kegg118` release of [CompMetEng/toolbox-assets](https://github.com/CompMetEng/toolbox-assets/releases/tag/kegg118). `ensure_kegg_data()` and `ensure_kegg_hmm_library("eukaryotes" | "prokaryotes")` fetch them and check the SHA-256. The libraries hold 2698 (eukaryotes, used for `sce` and `cme`) and 4205 (prokaryotes, used for `eco` and `mge`) profiles.

`fetch.sbatch` downloads the proteomes from the KEGG REST API (`list/<org>` and `get/<ids>/aaseq`) and UniProt, and packs them into `kegg_proteomes_<date>.tar.gz`. It yields 6021 (`sce`), 5010 (`cme`), 4288 (`eco`) and 476 (`mge`) KEGG sequences. The UniProt proteomes are downloaded and not searched. `run.sbatch` packs the `hmmsearch --tblout` files into `kegg_hmmsearch_tblout_<date>.tar.gz`, which `rescore.sbatch` and `timing.sbatch` read.

| Variable | Meaning |
| --- | --- |
| `STUDY` | this folder |
| `TOOLBOX_ROOT` | raven-toolbox checkout (`94f3940`); its `src` goes on `PYTHONPATH` |
| `PY` | Python interpreter with cobra, optlang, pandas and numpy |
| `DATA` | folder of the two archives |
| `BINARIES_CACHE` | `raven_toolbox/binaries` cache with the `hmmsearch` 3.4 bundle |

The module names in the job files are site-specific; other systems need an equivalent environment.

## Commands

```bash
export STUDY=... TOOLBOX_ROOT=... PY=... DATA=... BINARIES_CACHE=...
sbatch -A <account> $STUDY/jobs/fetch.sbatch
sbatch -A <account> $STUDY/jobs/run.sbatch        # 16 cores, 48 GB
sbatch -A <account> $STUDY/jobs/timing.sbatch     # exclusive node, 16 cores
sbatch -A <account> $STUDY/jobs/rescore.sbatch
```

For each organism `run.sbatch` calls the following, and `compare_kegg_paths.py` for `sce` and `mge`.

```bash
python analyze_hmm_cutoffs.py --artefacts $ART --org <org> --proteome kegg_rest/<org>.faa \
    --library <EUK|PROK> --threads 16 --save-tblout <org>.tbl --json results/sweep_<org>.json
python compare_kegg_paths.py --org <org> --proteome kegg_rest/<org>.faa --artefacts $ART \
    --library <lib> --domain <dom> --threads 16 --settings 1e-50,0.3,0.8 1e-30,0.3,0.9
```

`rescore.sbatch` scores the saved hit tables again with `--tblout`, which gives identical sweeps, and with `--restrict-to-reference`. `timing.sbatch` runs `check_true_reactions.py` and `time_hmmsearch.py --threads 16 12 4 1`.

## Outputs

| File | Content |
| --- | --- |
| `analyze_hmm_cutoffs.py` | E-value percentiles of matched and novel hits, cut-off sweep at (0.3, 0.8) and (0.3, 0.9), score-ratio sweep and defaults row, as printed tables and JSON. By default every `ko_reaction` link counts as a true reaction; `--restrict-to-reference` counts links to reactions of the reference model. |
| `results/sweep_<org>.json`, `results/sweep_<org>_refrxn.json` | Sweep output per organism, without and with `--restrict-to-reference`. |
| `compare_kegg_paths.py` to `results/wholemodel_<org>.json` | Reactions, metabolites and genes of the two paths at each setting, and their overlap. |
| `check_true_reactions.py` to `results/true_reactions.json` | True reactions per organism under several definitions. |
| `time_hmmsearch.py` to `results/timing_sce_eukaryotes.json` | `hmmsearch` wall time at the given thread counts and a comparison of the parsed hit tables. |
